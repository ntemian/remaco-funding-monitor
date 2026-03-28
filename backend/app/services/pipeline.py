"""
Daily Pipeline — orchestrates the fetch → store → match → notify cycle.
"""

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.funding_call import FundingCall, CallStatus
from app.models.company_profile import CompanyProfile
from app.models.match_result import MatchResult
from app.scrapers.ted_client import TEDClient
from app.scrapers.ftop_client import FTOPClient
from app.services.matching_engine import MatchingEngine

logger = logging.getLogger(__name__)


class DailyPipeline:
    """Orchestrates the daily funding call scan and matching."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ted = TEDClient()
        self.ftop = FTOPClient()
        self.matcher = MatchingEngine()

    async def run(self, days_back: int = 1) -> dict:
        """Run the full daily pipeline. Returns stats."""
        from_date = date.today() - timedelta(days=days_back)
        stats = {"new_calls": 0, "updated_calls": 0, "matches_created": 0, "errors": []}

        # 1. Fetch from all sources
        logger.info(f"Pipeline: fetching calls since {from_date}")
        all_calls = []

        try:
            ted_calls = await self.ted.search_open_tenders(from_date=from_date)
            all_calls.extend(ted_calls)
            logger.info(f"TED: {len(ted_calls)} calls fetched")
        except Exception as e:
            stats["errors"].append(f"TED fetch failed: {e}")
            logger.error(f"TED fetch failed: {e}")

        try:
            ftop_calls = await self.ftop.search_open_calls(from_date=from_date)
            all_calls.extend(ftop_calls)
            logger.info(f"FTOP: {len(ftop_calls)} calls fetched")
        except Exception as e:
            stats["errors"].append(f"FTOP fetch failed: {e}")
            logger.error(f"FTOP fetch failed: {e}")

        # 2. Upsert calls into database
        for call_data in all_calls:
            try:
                result = await self._upsert_call(call_data)
                if result == "new":
                    stats["new_calls"] += 1
                elif result == "updated":
                    stats["updated_calls"] += 1
            except Exception as e:
                stats["errors"].append(f"Upsert failed for {call_data.get('external_id')}: {e}")

        await self.db.commit()

        # 3. Update closing-soon status
        await self._update_statuses()

        # 4. Run matching against all active profiles
        profiles = (await self.db.execute(select(CompanyProfile))).scalars().all()
        open_calls = (await self.db.execute(
            select(FundingCall).where(FundingCall.status.in_([CallStatus.OPEN, CallStatus.CLOSING_SOON]))
        )).scalars().all()

        for profile in profiles:
            for call in open_calls:
                # Check if already matched
                existing = (await self.db.execute(
                    select(MatchResult).where(
                        MatchResult.call_id == call.id,
                        MatchResult.profile_id == profile.id,
                    )
                )).scalar_one_or_none()

                if not existing:
                    match = self.matcher.evaluate(call, profile)
                    self.db.add(match)
                    stats["matches_created"] += 1

        await self.db.commit()

        # Cleanup
        await self.ted.close()
        await self.ftop.close()

        logger.info(f"Pipeline complete: {stats}")
        return stats

    async def _upsert_call(self, call_data: dict) -> str:
        """Insert or update a funding call. Returns 'new' or 'updated'."""
        external_id = call_data.pop("external_id")
        raw_data = call_data.pop("raw_data", None)
        source = call_data.pop("source")
        status = call_data.pop("status", CallStatus.OPEN)

        existing = (await self.db.execute(
            select(FundingCall).where(FundingCall.external_id == external_id)
        )).scalar_one_or_none()

        if existing:
            for key, value in call_data.items():
                if value is not None:
                    setattr(existing, key, value)
            existing.raw_data = raw_data
            return "updated"
        else:
            call = FundingCall(
                external_id=external_id,
                source=source,
                status=status,
                raw_data=raw_data,
                **call_data,
            )
            self.db.add(call)
            return "new"

    async def _update_statuses(self):
        """Mark calls as closing_soon or closed based on deadlines."""
        today = date.today()
        week_ahead = today + timedelta(days=7)

        # Mark closing soon
        closing = (await self.db.execute(
            select(FundingCall).where(
                FundingCall.status == CallStatus.OPEN,
                FundingCall.deadline <= week_ahead,
                FundingCall.deadline > today,
            )
        )).scalars().all()
        for call in closing:
            call.status = CallStatus.CLOSING_SOON

        # Mark closed
        closed = (await self.db.execute(
            select(FundingCall).where(
                FundingCall.status.in_([CallStatus.OPEN, CallStatus.CLOSING_SOON]),
                FundingCall.deadline < today,
            )
        )).scalars().all()
        for call in closed:
            call.status = CallStatus.CLOSED

        await self.db.commit()
