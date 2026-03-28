"""
EU Funding & Tenders Portal (FTOP) Client — SEDIA Search API.

Uses form-encoded POST (NOT JSON) with apiKey=SEDIA (public, no registration).
Covers: Horizon Europe, Digital Europe, CEF, AMIF, ISF, EDF, LIFE, etc.
All programmes use the same API — filter by frameworkProgramme metadata.

Topic detail available at:
  GET https://ec.europa.eu/info/funding-tenders/opportunities/data/topicDetails/{ID}.json
"""

import logging
from datetime import date, timedelta
from typing import Optional

import httpx

from app.core.config import settings
from app.models.funding_call import CallSource, CallStatus

logger = logging.getLogger(__name__)

FTOP_SEARCH_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
FTOP_TOPIC_DETAIL = "https://ec.europa.eu/info/funding-tenders/opportunities/data/topicDetails"
FTOP_PORTAL_BASE = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details"


class FTOPClient:
    """Client for EU Funding & Tenders Portal (SEDIA search API)."""

    def __init__(self):
        # No Content-Type header — httpx sets it for form-encoded automatically
        self.client = httpx.AsyncClient(timeout=30.0, headers={
            "Accept": "application/json",
        })

    async def search_open_calls(
        self,
        from_date: Optional[date] = None,
        programmes: Optional[list[str]] = None,
        keywords: Optional[list[str]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[dict]:
        """Search for open calls for proposals / grants on FTOP."""
        if from_date is None:
            from_date = date.today() - timedelta(days=7)

        # SEDIA API uses application/x-www-form-urlencoded (NOT JSON)
        # Sort by deadline descending to get calls with future deadlines first
        form_data = {
            "apiKey": "SEDIA",
            "dataSetId": "cftDataset",
            "text": " ".join(keywords) if keywords else "*",
            "pageSize": str(page_size),
            "pageNumber": str(page),
            "sortBy": "deadlineDate",
            "sortOrder": "DESC",
        }

        try:
            resp = await self.client.post(FTOP_SEARCH_URL, data=form_data)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_results(data, programmes)
        except httpx.HTTPStatusError as e:
            logger.error(f"FTOP search failed: {e.response.status_code} — {e.response.text[:300]}")
            return []
        except Exception as e:
            logger.error(f"FTOP search error: {e}")
            return []

    async def get_topic_detail(self, topic_id: str) -> Optional[dict]:
        """Fetch full detail JSON for a specific topic."""
        try:
            resp = await self.client.get(f"{FTOP_TOPIC_DETAIL}/{topic_id}.json")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"FTOP topic detail failed for {topic_id}: {e}")
            return None

    def _parse_results(self, data: dict, programmes: Optional[list[str]] = None) -> list[dict]:
        """Parse FTOP SEDIA search API response."""
        results = []
        items = data.get("results", [])
        total = data.get("totalResults", 0)
        logger.info(f"FTOP: {total} total results, processing {len(items)} in this page")

        for item in items:
            try:
                metadata = item.get("metadata", {})
                deadline = self._parse_date(self._get_meta(metadata, "deadlineDate"))

                # Note: SEDIA dataset marks most calls as 31094503 (closed) even
                # when deadlines are in the future. We rely on deadline filtering above
                # instead of status codes for accurate open/closed determination.

                # Filter by programme if specified
                if programmes:
                    item_programme = self._get_meta(metadata, "frameworkProgramme")
                    if item_programme and not any(p.lower() in item_programme.lower() for p in programmes):
                        continue

                identifier = self._get_meta(metadata, "identifier") or item.get("reference", "")
                title = self._get_meta(metadata, "title") or item.get("summary", "")
                description = self._get_meta(metadata, "descriptionByte") or ""

                call = {
                    "external_id": f"ftop-{identifier}",
                    "source": CallSource.FTOP,
                    "title": str(title)[:1000],
                    "description": str(description)[:5000] if description else None,
                    "url": f"{FTOP_PORTAL_BASE}/{identifier}" if identifier else item.get("url", ""),
                    "programme": self._get_meta(metadata, "frameworkProgramme") or self._get_meta(metadata, "callIdentifier"),
                    "sectors": self._extract_sectors(metadata),
                    "keywords": self._get_meta_list(metadata, "keywords"),
                    "budget_eur": self._parse_budget(metadata),
                    "min_grant": self._parse_float(self._get_meta(metadata, "minGrantAmount")),
                    "max_grant": self._parse_float(self._get_meta(metadata, "maxGrantAmount")),
                    "co_financing_rate": self._parse_float(self._get_meta(metadata, "coFinancingRate")),
                    "publication_date": self._parse_date(self._get_meta(metadata, "startDate")),
                    "deadline": deadline,
                    "authority_name": "European Commission",
                    "authority_country": "EU",
                    "eligible_countries": self._get_meta_list(metadata, "eligibleCountries") or ["EU"],
                    "consortium_required": None,
                    "min_consortium_partners": self._parse_int(self._get_meta(metadata, "minParticipants")),
                    "raw_data": item,
                    "status": CallStatus.OPEN,
                }
                results.append(call)
            except Exception as e:
                logger.warning(f"Failed to parse FTOP result: {e}")
                continue

        logger.info(f"FTOP: parsed {len(results)} open/forthcoming calls from {len(items)} results")
        return results

    def _get_meta(self, metadata: dict, key: str) -> Optional[str]:
        """Extract a metadata value — FTOP metadata values can be strings or lists."""
        val = metadata.get(key)
        if val is None:
            return None
        if isinstance(val, list):
            return val[0] if val else None
        return str(val)

    def _get_meta_list(self, metadata: dict, key: str) -> list[str]:
        """Extract a metadata value as a list."""
        val = metadata.get(key)
        if val is None:
            return []
        if isinstance(val, list):
            return [str(v) for v in val]
        if isinstance(val, str):
            return [s.strip() for s in val.split(",") if s.strip()]
        return [str(val)]

    def _extract_sectors(self, metadata: dict) -> list[str]:
        sectors = []
        for field in ["tags", "programmeDivision", "typesOfAction", "crossCuttingPriorities", "focusArea"]:
            sectors.extend(self._get_meta_list(metadata, field))
        return sectors

    def _parse_budget(self, metadata: dict) -> Optional[float]:
        for field in ["budgetOverview", "budgetTopicActionTotal", "budget"]:
            val = self._parse_float(self._get_meta(metadata, field))
            if val:
                return val
        return None

    def _parse_float(self, val) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(str(val).replace(",", "").replace(" ", ""))
        except (ValueError, TypeError):
            return None

    def _parse_int(self, val) -> Optional[int]:
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def _parse_date(self, date_str) -> Optional[date]:
        if not date_str:
            return None
        if isinstance(date_str, list):
            date_str = date_str[0] if date_str else None
            if not date_str:
                return None
        try:
            return date.fromisoformat(str(date_str)[:10])
        except (ValueError, TypeError):
            return None

    async def close(self):
        await self.client.aclose()
