from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BusinessResult:
    name: str
    website: str | None
    email: str | None
    phone: str | None
    address: str | None
    source_url: str | None


class PublicBusinessScraper:
    """Collects public business records without bypassing logins, captchas, or paywalls.

    This first connector uses OpenStreetMap/Nominatim/Overpass public data. It only
    reads public tags such as website, phone, email, and address.
    """

    nominatim_url = "https://nominatim.openstreetmap.org/search"
    overpass_url = "https://overpass-api.de/api/interpreter"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.settings.public_source_user_agent})

    def search(self, city: str, niche: str, limit: int = 15) -> list[BusinessResult]:
        bbox = self._geocode_city(city)
        if not bbox:
            raise ValueError(f"Could not find a public map boundary for {city}.")

        raw_elements = self._query_overpass(bbox=bbox, limit=max(limit * 5, 25))
        candidates = [self._element_to_business(element) for element in raw_elements]
        filtered = self._filter_by_niche(candidates, raw_elements, niche)

        # Prefer businesses with websites because the product is designed for website review.
        filtered.sort(key=lambda item: (item.website is None, item.email is None, item.name))
        unique = self._dedupe(filtered)
        return unique[:limit]

    @retry(wait=wait_exponential(multiplier=1, min=1, max=6), stop=stop_after_attempt(3))
    def _geocode_city(self, city: str) -> tuple[float, float, float, float] | None:
        response = self.session.get(
            self.nominatim_url,
            params={"q": city, "format": "json", "limit": 1},
            timeout=self.settings.scraper_request_timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        south, north, west, east = [float(value) for value in data[0]["boundingbox"]]
        return south, west, north, east

    @retry(wait=wait_exponential(multiplier=1, min=1, max=6), stop=stop_after_attempt(3))
    def _query_overpass(
        self, bbox: tuple[float, float, float, float], limit: int
    ) -> list[dict[str, Any]]:
        south, west, north, east = bbox
        query = f"""
        [out:json][timeout:25];
        (
          nwr["name"]["website"]({south},{west},{north},{east});
          nwr["name"]["contact:website"]({south},{west},{north},{east});
          nwr["name"]["email"]({south},{west},{north},{east});
          nwr["name"]["contact:email"]({south},{west},{north},{east});
          nwr["name"]["shop"]({south},{west},{north},{east});
          nwr["name"]["amenity"]({south},{west},{north},{east});
          nwr["name"]["office"]({south},{west},{north},{east});
          nwr["name"]["craft"]({south},{west},{north},{east});
        );
        out center tags {limit};
        """
        response = self.session.post(
            self.overpass_url,
            data={"data": query},
            timeout=self.settings.scraper_request_timeout + 15,
        )
        response.raise_for_status()
        return response.json().get("elements", [])

    def _element_to_business(self, element: dict[str, Any]) -> BusinessResult:
        tags = element.get("tags", {})
        osm_type = element.get("type", "node")
        osm_id = element.get("id")
        return BusinessResult(
            name=self._clean(tags.get("name")) or "Unnamed business",
            website=self._normalize_website(tags.get("website") or tags.get("contact:website")),
            email=self._clean(tags.get("email") or tags.get("contact:email")),
            phone=self._clean(tags.get("phone") or tags.get("contact:phone")),
            address=self._format_address(tags),
            source_url=f"https://www.openstreetmap.org/{osm_type}/{osm_id}" if osm_id else None,
        )

    def _filter_by_niche(
        self, businesses: list[BusinessResult], elements: list[dict[str, Any]], niche: str
    ) -> list[BusinessResult]:
        words = [word for word in re.split(r"\W+", niche.lower()) if len(word) > 2]
        if not words:
            return businesses

        matches: list[BusinessResult] = []
        fallback: list[BusinessResult] = []
        for business, element in zip(businesses, elements):
            tags_text = " ".join(str(value) for value in element.get("tags", {}).values()).lower()
            haystack = f"{business.name} {business.website or ''} {tags_text}".lower()
            if any(word in haystack for word in words):
                matches.append(business)
            elif business.website:
                fallback.append(business)

        # If public tags do not contain the exact niche, still return website-owning businesses
        # so the user can manually review a small, transparent candidate set.
        return matches or fallback or businesses

    def _dedupe(self, businesses: list[BusinessResult]) -> list[BusinessResult]:
        seen: set[str] = set()
        unique: list[BusinessResult] = []
        for business in businesses:
            key = (business.website or business.name).strip().lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(business)
        return unique

    def _format_address(self, tags: dict[str, Any]) -> str | None:
        parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:city"),
            tags.get("addr:state"),
            tags.get("addr:postcode"),
        ]
        value = ", ".join(str(part) for part in parts if part)
        return value or None

    def _normalize_website(self, website: str | None) -> str | None:
        cleaned = self._clean(website)
        if not cleaned:
            return None
        if not cleaned.startswith(("http://", "https://")):
            cleaned = f"https://{cleaned}"
        return cleaned

    def _clean(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

