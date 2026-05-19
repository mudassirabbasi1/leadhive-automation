from __future__ import annotations

from dataclasses import dataclass

from analyzer.website_analyzer import WebsiteIssue
from backend.app.core.config import get_settings


@dataclass(slots=True)
class GeneratedEmail:
    subject: str
    body: str


class OutreachEmailGenerator:
    """Creates transparent, non-spammy draft emails for human review."""

    def generate(
        self,
        business_name: str,
        niche: str,
        city: str,
        website: str | None,
        issues: list[WebsiteIssue],
        score: float,
    ) -> GeneratedEmail:
        settings = get_settings()
        issue_sentence = self._issue_sentence(issues)
        subject = f"Quick website idea for {business_name}"
        website_line = f"I was looking at {website}" if website else "I was checking public business listings"
        body = f"""Hi {business_name} team,

{website_line} while researching {niche} businesses in {city}. I noticed a few fixable items that may be costing visitors confidence or inquiries: {issue_sentence}

I work with service businesses on practical website improvements, not generic redesign pitches. Based on the current public review score of {score:.0f}/100, I would start with the items above because they are usually quick wins for more calls, form fills, and trust.

Would it be useful if I sent over a short before/after checklist for {business_name}?

Best,
{settings.smtp_from_name}

{settings.unsubscribe_text}
"""
        return GeneratedEmail(subject=subject, body=body)

    def _issue_sentence(self, issues: list[WebsiteIssue]) -> str:
        if not issues:
            return "the site already covers the basics well, so any outreach should focus on growth opportunities."
        labels = [issue.label[0].lower() + issue.label[1:] for issue in issues[:3]]
        if len(labels) == 1:
            return labels[0] + "."
        return ", ".join(labels[:-1]) + f", and {labels[-1]}."
