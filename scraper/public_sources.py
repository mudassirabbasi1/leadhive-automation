from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import requests
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

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
    overpass_mirrors = (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
    )
    known_city_bboxes = {
        "austin": (30.098, -97.938, 30.516, -97.561),
        "austin texas": (30.098, -97.938, 30.516, -97.561),
        "new york": (40.477, -74.259, 40.917, -73.700),
        "new york city": (40.477, -74.259, 40.917, -73.700),
        "nyc": (40.477, -74.259, 40.917, -73.700),
        "nyc new york": (40.477, -74.259, 40.917, -73.700),
        "chicago": (41.644, -87.940, 42.023, -87.524),
        "los angeles": (33.704, -118.668, 34.337, -118.155),
        "houston": (29.523, -95.823, 30.111, -95.070),
        "miami": (25.709, -80.319, 25.855, -80.139),
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.settings.public_source_user_agent})

    def search(self, city: str, niche: str, limit: int = 15) -> list[BusinessResult]:
        query_limit = max(limit * 5, 25)
        raw_elements = self._query_by_known_bbox(city=city, niche=niche, limit=query_limit)
        if not raw_elements:
            raw_elements = self._query_by_public_area(city=city, niche=niche, limit=query_limit)
        if not raw_elements:
            try:
                bbox = self._geocode_city(city)
            except RetryError as exc:
                raise ValueError(
                    "The public city lookup source rejected this request. Try another city spelling, "
                    "or wait a few minutes and retry."
                ) from exc
            if not bbox:
                raise ValueError(f"Could not find a public map boundary for {city}.")
            raw_elements = self._query_overpass(bbox=bbox, limit=query_limit)

        candidates = [self._element_to_business(element) for element in raw_elements]
        filtered = self._filter_by_niche(candidates, raw_elements, niche)

        # Prefer businesses with websites because the product is designed for website review.
        filtered.sort(key=lambda item: (item.website is None, item.email is None, item.name))
        unique = self._dedupe(filtered)
        return unique[:limit]

    def _query_by_known_bbox(self, city: str, niche: str, limit: int) -> list[dict[str, Any]]:
        bbox = self.known_city_bboxes.get(self._city_key(city))
        if not bbox:
            return []
        try:
            return self._query_overpass_bbox_niche(bbox=bbox, niche=niche, limit=limit)
        except RetryError:
            logger.warning("Known bbox lookup failed", extra={"city": city})
            return []

    def _query_by_public_area(self, city: str, niche: str, limit: int) -> list[dict[str, Any]]:
        area_name = self._city_area_name(city)
        if not area_name:
            return []
        try:
            return self._query_overpass_area(area_name=area_name, niche=niche, limit=limit)
        except RetryError:
            logger.warning("Overpass area lookup failed", extra={"city": city})
            return []

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
        return self._post_overpass(query=query, timeout=self.settings.scraper_request_timeout + 15)

    @retry(wait=wait_exponential(multiplier=1, min=1, max=6), stop=stop_after_attempt(2))
    def _query_overpass_bbox_niche(
        self, bbox: tuple[float, float, float, float], niche: str, limit: int
    ) -> list[dict[str, Any]]:
        south, west, north, east = bbox
        filters = self._overpass_niche_filters(niche=niche, location=f"({south},{west},{north},{east})")
        query = f"""
        [out:json][timeout:25];
        (
          {filters}
        );
        out center tags {limit};
        """
        return self._post_overpass(query=query, timeout=self.settings.scraper_request_timeout + 15)

    @retry(wait=wait_exponential(multiplier=1, min=1, max=6), stop=stop_after_attempt(3))
    def _query_overpass_area(self, area_name: str, niche: str, limit: int) -> list[dict[str, Any]]:
        safe_area_name = self._escape_overpass_string(area_name)
        filters = self._overpass_niche_filters(niche=niche, location="(area.searchArea)")
        query = f"""
        [out:json][timeout:25];
        area["name"="{safe_area_name}"]["boundary"="administrative"]->.searchArea;
        (
          {filters}
        );
        out center tags {limit};
        """
        return self._post_overpass(query=query, timeout=self.settings.scraper_request_timeout + 20)

    def _post_overpass(self, query: str, timeout: int) -> list[dict[str, Any]]:
        last_error: Exception | None = None
        for url in self.overpass_mirrors:
            try:
                response = self.session.post(
                    url,
                    data={"data": query},
                    headers={"Accept": "application/json"},
                    timeout=timeout,
                )
                response.raise_for_status()
                return response.json().get("elements", [])
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("Overpass mirror failed", extra={"url": url, "error": str(exc)})
        if last_error:
            raise last_error
        return []

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

    def _city_area_name(self, city: str) -> str:
        # Overpass area search works best with the municipality name.
        return city.split(",", 1)[0].strip()

    def _city_key(self, city: str) -> str:
        return re.sub(r"\s+", " ", city.replace(",", " ").strip().lower())

    def _escape_overpass_string(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _escape_overpass_regex(self, value: str) -> str:
        words = [word for word in re.split(r"\W+", value.lower()) if len(word) > 2]
        if not words:
            return ".*"
        aliases = {
            "dentist": ["dentist", "dental", "orthodont"],
            "doctor": ["doctor", "clinic", "medical", "physician"],
            "plumber": ["plumber", "plumbing"],
            "restaurant": ["restaurant", "cafe", "food"],
            "lawyer": ["lawyer", "attorney", "legal"],
            "furniture": ["furniture", "furnishing", "home"],
        }
        patterns: list[str] = []
        for word in words:
            patterns.extend(aliases.get(word, [word]))
        escaped = [re.escape(pattern) for pattern in patterns]
        return "|".join(escaped).replace('"', '\\"')

    def _overpass_niche_filters(self, niche: str, location: str) -> str:
        words = set(word for word in re.split(r"\W+", niche.lower()) if len(word) > 2)
        if {"furniture", "furnishing", "furnishings"} & words:
            return "\n          ".join(
                [
                    f'nwr["shop"="furniture"]{location};',
                    f'nwr["shop"="interior_decoration"]{location};',
                    f'nwr["shop"="bed"]{location};',
                    f'nwr["shop"="kitchen"]{location};',
                    f'nwr["name"~"furniture|furnishing",i]{location};',
                ]
            )
        if {"dentist", "dental", "orthodontist"} & words:
            return "\n          ".join(
                [
                    f'nwr["amenity"="dentist"]{location};',
                    f'nwr["healthcare"="dentist"]{location};',
                    f'nwr["name"~"dentist|dental|orthodont",i]{location};',
                ]
            )

        safe_niche = self._escape_overpass_regex(niche)
        return "\n          ".join(
            [
                f'nwr["amenity"~"{safe_niche}",i]{location};',
                f'nwr["shop"~"{safe_niche}",i]{location};',
                f'nwr["office"~"{safe_niche}",i]{location};',
                f'nwr["craft"~"{safe_niche}",i]{location};',
                f'nwr["healthcare"~"{safe_niche}",i]{location};',
                f'nwr["name"~"{safe_niche}",i]{location};',
            ]
        )
