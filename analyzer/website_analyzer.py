from __future__ import annotations

import logging
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


class WebsiteIssue(BaseModel):
    code: str
    label: str
    severity: str
    evidence: str


class WebsiteAnalysis(BaseModel):
    score: float
    issues: list[WebsiteIssue]
    load_time_seconds: float | None = None


class WebsiteAnalyzer:
    """Scores public websites using transparent checks agencies can explain to prospects."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.settings.public_source_user_agent})

    def analyze(self, website: str | None) -> WebsiteAnalysis:
        if not website:
            return WebsiteAnalysis(
                score=20,
                issues=[
                    WebsiteIssue(
                        code="no_public_website",
                        label="No public website listed",
                        severity="high",
                        evidence="Public source did not include a website URL.",
                    )
                ],
            )

        normalized = self._normalize_url(website)
        issues: list[WebsiteIssue] = []
        if not normalized.startswith("https://"):
            issues.append(
                WebsiteIssue(
                    code="missing_https",
                    label="Website does not use HTTPS by default",
                    severity="high",
                    evidence=f"URL begins with {urlparse(normalized).scheme or 'no scheme'}.",
                )
            )

        if not self._robots_allows(normalized):
            return WebsiteAnalysis(
                score=50,
                issues=[
                    WebsiteIssue(
                        code="robots_disallowed",
                        label="Robots.txt disallows automated review",
                        severity="medium",
                        evidence="LeadHive respected robots.txt and skipped page analysis.",
                    )
                ],
            )

        try:
            html, load_time = self._fetch_html(normalized)
        except requests.RequestException as exc:
            logger.warning("Requests analysis failed", extra={"url": normalized, "error": str(exc)})
            if self.settings.enable_playwright_analysis:
                try:
                    html, load_time = self._fetch_with_playwright(normalized)
                except Exception as playwright_exc:
                    return WebsiteAnalysis(
                        score=30,
                        issues=issues
                        + [
                            WebsiteIssue(
                                code="fetch_failed",
                                label="Website could not be loaded reliably",
                                severity="high",
                                evidence=str(playwright_exc)[:180],
                            )
                        ],
                    )
            else:
                return WebsiteAnalysis(
                    score=30,
                    issues=issues
                    + [
                        WebsiteIssue(
                            code="fetch_failed",
                            label="Website could not be loaded reliably",
                            severity="high",
                            evidence=str(exc)[:180],
                        )
                    ],
                )

        soup = BeautifulSoup(html, "html.parser")
        issues.extend(self._metadata_issues(soup))
        issues.extend(self._cta_issues(soup))
        issues.extend(self._structure_issues(soup))
        issues.extend(self._contact_issues(soup))
        if load_time and load_time > 3:
            issues.append(
                WebsiteIssue(
                    code="slow_load_speed",
                    label="Homepage loaded slowly",
                    severity="medium",
                    evidence=f"Initial HTML took {load_time:.2f}s to load.",
                )
            )

        score = self._score(issues)
        return WebsiteAnalysis(score=score, issues=issues, load_time_seconds=load_time)

    def _fetch_html(self, url: str) -> tuple[str, float]:
        start = time.perf_counter()
        response = self.session.get(url, timeout=self.settings.website_analysis_timeout, allow_redirects=True)
        elapsed = time.perf_counter() - start
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "<html" not in response.text[:500].lower():
            raise requests.RequestException(f"Expected HTML but received {content_type or 'unknown content'}")
        return response.text, elapsed

    def _fetch_with_playwright(self, url: str) -> tuple[str, float]:
        from playwright.sync_api import sync_playwright

        start = time.perf_counter()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.settings.website_analysis_timeout * 1000)
            html = page.content()
            browser.close()
        return html, time.perf_counter() - start

    def _metadata_issues(self, soup: BeautifulSoup) -> list[WebsiteIssue]:
        issues: list[WebsiteIssue] = []
        title = soup.find("title")
        description = soup.find("meta", attrs={"name": "description"})
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if not title or not title.get_text(strip=True):
            issues.append(
                WebsiteIssue(
                    code="missing_title",
                    label="Missing page title",
                    severity="medium",
                    evidence="No non-empty <title> tag found.",
                )
            )
        if not description or not description.get("content"):
            issues.append(
                WebsiteIssue(
                    code="missing_meta_description",
                    label="Missing meta description",
                    severity="medium",
                    evidence="No <meta name='description'> content found.",
                )
            )
        if not viewport or "width=device-width" not in (viewport.get("content") or "").lower():
            issues.append(
                WebsiteIssue(
                    code="no_mobile_viewport",
                    label="Missing mobile viewport configuration",
                    severity="high",
                    evidence="No responsive viewport meta tag found.",
                )
            )
        return issues

    def _cta_issues(self, soup: BeautifulSoup) -> list[WebsiteIssue]:
        cta_words = ("contact", "call", "quote", "book", "schedule", "reserve", "get started", "request")
        visible_actions = [
            tag.get_text(" ", strip=True).lower()
            for tag in soup.find_all(["a", "button"])
            if tag.get_text(strip=True)
        ]
        if not any(any(word in text for word in cta_words) for text in visible_actions[:80]):
            return [
                WebsiteIssue(
                    code="poor_cta_visibility",
                    label="No clear call-to-action found near primary links/buttons",
                    severity="medium",
                    evidence="Common CTA words were not found in visible links or buttons.",
                )
            ]
        return []

    def _structure_issues(self, soup: BeautifulSoup) -> list[WebsiteIssue]:
        issues: list[WebsiteIssue] = []
        semantic_count = sum(1 for tag in ("header", "nav", "main", "section", "footer") if soup.find(tag))
        table_layouts = len(soup.find_all("table"))
        h1_count = len(soup.find_all("h1"))
        stylesheet_count = len(soup.find_all("link", rel=lambda value: value and "stylesheet" in value))
        if semantic_count < 2 or h1_count == 0 or (table_layouts > 2 and stylesheet_count < 2):
            issues.append(
                WebsiteIssue(
                    code="outdated_basic_structure",
                    label="Homepage appears outdated or structurally basic",
                    severity="medium",
                    evidence=f"Semantic sections: {semantic_count}, H1 tags: {h1_count}, tables: {table_layouts}.",
                )
            )
        return issues

    def _contact_issues(self, soup: BeautifulSoup) -> list[WebsiteIssue]:
        forms = soup.find_all("form")
        mailto = soup.find("a", href=lambda href: href and href.lower().startswith("mailto:"))
        contact_form = False
        for form in forms:
            form_text = str(form).lower()
            if any(word in form_text for word in ("email", "message", "name", "phone")):
                contact_form = True
                break
        if not contact_form and not mailto:
            return [
                WebsiteIssue(
                    code="no_contact_form",
                    label="No contact form or mailto link found",
                    severity="medium",
                    evidence="Homepage did not include an obvious contact form or email link.",
                )
            ]
        return []

    def _score(self, issues: list[WebsiteIssue]) -> float:
        penalties = {"high": 18, "medium": 11, "low": 5}
        score = 100 - sum(penalties.get(issue.severity, 8) for issue in issues)
        return float(max(0, min(100, score)))

    def _robots_allows(self, url: str) -> bool:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            response = self.session.get(robots_url, timeout=min(5, self.settings.website_analysis_timeout))
            if response.status_code >= 400:
                return True
            parser.parse(response.text.splitlines())
        except Exception:
            return True
        return parser.can_fetch(self.settings.public_source_user_agent, url)

    def _normalize_url(self, url: str) -> str:
        cleaned = url.strip()
        if not cleaned.startswith(("http://", "https://")):
            return f"https://{cleaned}"
        return cleaned
