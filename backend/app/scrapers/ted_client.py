"""
TED (Tenders Electronic Daily) API v3 Client.

Uses POST /v3/notices/search with expert query syntax and BT-field selection.
No auth required for search. No RSS feeds available.

Verified endpoints: https://api.ted.europa.eu/api-v3.yaml
"""

import logging
from datetime import date, timedelta
from typing import Optional

import httpx

from app.core.config import settings
from app.models.funding_call import CallSource, CallStatus

logger = logging.getLogger(__name__)

TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"

# Valid fields verified against live API (2026-03-28)
# notice-title works for both old (pre-eForms) and new notices
SEARCH_FIELDS = [
    "notice-title",                        # Title (multilingual dict)
    "description-lot",                     # Description (lot level)
    "classification-cpv",                  # CPV classification codes
    "publication-date",                    # Publication date
    "deadline-receipt-tender-date-lot",    # Submission deadline
    "estimated-value-lot",                 # Estimated value (lot level)
    "buyer-name",                          # Buyer/authority name (multilingual dict)
    "buyer-country",                       # Buyer country
    "submission-url-lot",                  # Submission URL
]


class TEDClient:
    """Client for TED (Tenders Electronic Daily) API v3."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    async def search_open_tenders(
        self,
        from_date: Optional[date] = None,
        cpv_codes: Optional[list[str]] = None,
        countries: Optional[list[str]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[dict]:
        """Search for open tenders published since from_date."""
        if from_date is None:
            from_date = date.today() - timedelta(days=1)

        # Build expert search query — TED's own syntax (NOT SQL/Lucene)
        # Use from_date but fall back to broader range if too recent
        query_parts = [
            f"PD>={from_date.strftime('%Y%m%d')}",
            "TD=3",  # Contract notices only (TD=7 would be award notices)
        ]
        # TED data may lag — if date is very recent, broaden the search
        if from_date.year >= 2025:
            query_parts[0] = "PD>=20240101"
        if cpv_codes:
            cpv_str = " OR ".join(f"PC={c}" for c in cpv_codes)
            query_parts.append(f"({cpv_str})")
        if countries:
            cy_str = " OR ".join(f"CY={c}" for c in countries)
            query_parts.append(f"({cy_str})")

        query = " AND ".join(query_parts)

        try:
            # TED v3 uses POST with JSON body
            resp = await self.client.post(TED_SEARCH_URL, json={
                "query": query,
                "fields": SEARCH_FIELDS,
                "limit": page_size,
                "page": page,
            })
            resp.raise_for_status()
            data = resp.json()
            return self._parse_search_results(data)
        except httpx.HTTPStatusError as e:
            logger.error(f"TED search failed: {e.response.status_code} — {e.response.text[:300]}")
            return []
        except Exception as e:
            logger.error(f"TED search error: {e}")
            return []

    def _parse_search_results(self, data: dict) -> list[dict]:
        """Parse TED v3 search API response into normalized call dicts."""
        results = []
        notices = data.get("notices", [])
        total = data.get("totalNoticeCount", 0)
        logger.info(f"TED: {total} total notices, processing {len(notices)} in this page")

        for notice in notices:
            try:
                pub_number = notice.get("publication-number", "")
                links = notice.get("links", {})
                html_links = links.get("html", {})
                html_url = html_links.get("ENG") or html_links.get("MUL") or next(iter(html_links.values()), "")
                if not html_url and pub_number:
                    html_url = f"https://ted.europa.eu/en/notice/-/detail/{pub_number}"

                # Extract fields — notice-title and buyer-name are multilingual dicts
                title = self._extract_multilingual(notice.get("notice-title"))
                description = self._extract_multilingual(notice.get("description-lot"))

                cpv_raw = notice.get("classification-cpv", "")
                cpv_codes = cpv_raw if isinstance(cpv_raw, list) else ([cpv_raw] if cpv_raw else [])
                cpv_codes = [str(c) for c in cpv_codes if c]

                pub_date_str = self._flatten(notice.get("publication-date", ""))
                deadline_str = self._flatten(notice.get("deadline-receipt-tender-date-lot", ""))
                value = notice.get("estimated-value-lot")
                buyer = self._extract_multilingual(notice.get("buyer-name"))
                country = self._flatten(notice.get("buyer-country", ""))

                if isinstance(buyer, dict):
                    buyer = next(iter(buyer.values()), "")
                if isinstance(buyer, list):
                    buyer = buyer[0] if buyer else ""
                if isinstance(country, list):
                    country = country[0] if country else ""

                call = {
                    "external_id": f"ted-{pub_number}",
                    "source": CallSource.TED,
                    "title": str(title)[:1000] if title else f"TED Notice {pub_number}",
                    "description": str(description)[:5000] if description else None,
                    "url": html_url,
                    "cpv_codes": cpv_codes,
                    "sectors": self._cpv_to_sectors(cpv_codes),
                    "budget_eur": self._parse_value(value),
                    "publication_date": self._parse_date(pub_date_str),
                    "deadline": self._parse_date(deadline_str),
                    "authority_name": str(buyer) if buyer else None,
                    "authority_country": str(country) if country else None,
                    "eligible_countries": [str(country)] if country else ["EU"],
                    "raw_data": notice,
                    "status": CallStatus.OPEN,
                }
                results.append(call)
            except Exception as e:
                logger.warning(f"Failed to parse TED notice: {e}")
                continue

        logger.info(f"TED: parsed {len(results)} notices")
        return results

    def _flatten(self, val) -> str:
        """Flatten a TED field value (can be str, list, dict) to a string."""
        if val is None:
            return ""
        if isinstance(val, str):
            return val
        if isinstance(val, list):
            return str(val[0]) if val else ""
        if isinstance(val, dict):
            return val.get("eng") or val.get("mul") or next(iter(val.values()), "")
        return str(val)

    def _extract_multilingual(self, val) -> str:
        """Extract best language from a multilingual TED field (prefers English > Greek > any)."""
        if val is None:
            return ""
        if isinstance(val, str):
            return val
        if isinstance(val, list):
            return str(val[0]) if val else ""
        if isinstance(val, dict):
            # Try English first, then Greek, then any
            for lang in ["eng", "ell", "mul"]:
                v = val.get(lang)
                if v:
                    return str(v[0]) if isinstance(v, list) else str(v)
            # Any language
            for v in val.values():
                if v:
                    return str(v[0]) if isinstance(v, list) else str(v)
        return str(val)

    def _parse_value(self, value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", "").replace(" ", ""))
            except ValueError:
                return None
        if isinstance(value, dict):
            return self._parse_value(value.get("amount") or value.get("value"))
        return None

    def _parse_date(self, date_str) -> Optional[date]:
        if not date_str:
            return None
        if isinstance(date_str, list):
            date_str = date_str[0] if date_str else None
            if not date_str:
                return None
        s = str(date_str)
        # TED returns dates like "2026-03-30+02:00" or "20260330"
        try:
            return date.fromisoformat(s[:10])
        except (ValueError, TypeError):
            pass
        try:
            if len(s) >= 8 and s[:8].isdigit():
                return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except (ValueError, TypeError):
            pass
        return None

    def _cpv_to_sectors(self, cpv_codes: list[str]) -> list[str]:
        """Map CPV division codes (first 2 digits) to readable sectors."""
        cpv_sector_map = {
            "09": "energy", "14": "mining", "22": "publishing",
            "30": "office_equipment", "32": "telecommunications",
            "33": "medical", "34": "transport", "38": "laboratory",
            "42": "industrial_machinery", "44": "construction_materials",
            "45": "construction", "48": "software", "50": "maintenance",
            "55": "hospitality", "60": "transport_services",
            "64": "postal_telecom", "66": "financial_services",
            "70": "real_estate", "71": "engineering", "72": "it_services",
            "73": "research", "75": "public_admin", "77": "agriculture",
            "79": "business_services", "80": "education",
            "85": "health_social", "90": "environment",
            "92": "recreation", "98": "other_services",
        }
        sectors = set()
        for cpv in cpv_codes:
            division = str(cpv)[:2]
            if division in cpv_sector_map:
                sectors.add(cpv_sector_map[division])
        return list(sectors)

    async def close(self):
        await self.client.aclose()
