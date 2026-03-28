"""
Eligibility Matching Engine.

Compares a FundingCall against a CompanyProfile and produces a MatchResult
with a 0-100 score, verdict (go/consortium/no_go), and gap analysis.

Scoring weights:
  - Sector alignment:      30%
  - Financial capacity:     25%
  - Staff & expertise:      20%
  - Past experience:        15%
  - Geographic eligibility: 10%
"""

import logging
from typing import Optional

from app.models.funding_call import FundingCall
from app.models.company_profile import CompanyProfile
from app.models.match_result import MatchResult, MatchVerdict

logger = logging.getLogger(__name__)

WEIGHTS = {
    "sector": 0.30,
    "financial": 0.25,
    "staff": 0.20,
    "experience": 0.15,
    "geographic": 0.10,
}

# Thresholds
GO_THRESHOLD = 70
CONSORTIUM_THRESHOLD = 40


class MatchingEngine:
    """Rule-based eligibility matching between funding calls and company profiles."""

    def evaluate(self, call: FundingCall, profile: CompanyProfile) -> MatchResult:
        """Evaluate a single call against a company profile."""
        gaps = []
        recommendations = []

        sector_score = self._score_sectors(call, profile, gaps)
        financial_score = self._score_financial(call, profile, gaps, recommendations)
        staff_score = self._score_staff(call, profile, gaps)
        experience_score = self._score_experience(call, profile, gaps)
        geographic_score = self._score_geographic(call, profile, gaps)

        weighted_score = int(
            sector_score * WEIGHTS["sector"]
            + financial_score * WEIGHTS["financial"]
            + staff_score * WEIGHTS["staff"]
            + experience_score * WEIGHTS["experience"]
            + geographic_score * WEIGHTS["geographic"]
        )

        # Determine verdict
        if weighted_score >= GO_THRESHOLD:
            verdict = MatchVerdict.GO
        elif weighted_score >= CONSORTIUM_THRESHOLD:
            verdict = MatchVerdict.CONSORTIUM
            if call.consortium_required or weighted_score < 60:
                recommendations.append("Consider forming a consortium to strengthen the bid")
        else:
            verdict = MatchVerdict.NO_GO

        # Hard disqualifiers override score
        if geographic_score == 0 and call.eligible_countries:
            verdict = MatchVerdict.NO_GO
            gaps.append({"type": "geographic", "message": "Country not eligible for this call", "severity": "critical"})

        return MatchResult(
            call_id=call.id,
            profile_id=profile.id,
            score=weighted_score,
            verdict=verdict,
            sector_score=sector_score,
            financial_score=financial_score,
            staff_score=staff_score,
            experience_score=experience_score,
            geographic_score=geographic_score,
            gaps=gaps if gaps else None,
            recommendations=recommendations if recommendations else None,
        )

    def _score_sectors(self, call: FundingCall, profile: CompanyProfile, gaps: list) -> int:
        """Score sector alignment between call and company."""
        call_sectors = set(call.sectors or [])
        call_cpv = set(call.cpv_codes or [])
        profile_sectors = set(profile.sectors or [])

        if not call_sectors and not call_cpv:
            return 80  # No sector requirement — generous default

        # Direct sector match
        if call_sectors and profile_sectors:
            overlap = call_sectors & profile_sectors
            if overlap:
                ratio = len(overlap) / len(call_sectors)
                return min(100, int(60 + ratio * 40))

        # Check CPV codes against completed projects
        project_sectors = set()
        for proj in profile.completed_projects:
            if proj.sector:
                project_sectors.add(proj.sector)

        if project_sectors & call_sectors:
            return 70

        if call_sectors:
            gaps.append({
                "type": "sector",
                "message": f"Call requires sectors: {', '.join(call_sectors)}. Profile covers: {', '.join(profile_sectors)}",
                "severity": "medium",
            })
            return 30

        return 50  # Inconclusive

    def _score_financial(self, call: FundingCall, profile: CompanyProfile, gaps: list, recs: list) -> int:
        """Score financial capacity."""
        avg_turnover = profile.avg_turnover

        if not call.min_turnover:
            return 80  # No requirement specified

        if not avg_turnover:
            gaps.append({"type": "financial", "message": "Company turnover not specified in profile", "severity": "medium"})
            return 50

        ratio = avg_turnover / call.min_turnover

        if ratio >= 1.5:
            return 100  # Comfortably exceeds
        elif ratio >= 1.0:
            return 85  # Meets requirement
        elif ratio >= 0.7:
            shortfall = call.min_turnover - avg_turnover
            gaps.append({
                "type": "financial",
                "message": f"Turnover gap: need {call.min_turnover:,.0f}€, have {avg_turnover:,.0f}€ (short by {shortfall:,.0f}€)",
                "severity": "medium",
            })
            recs.append(f"Consortium partner could cover the {shortfall:,.0f}€ turnover shortfall")
            return 55
        else:
            shortfall = call.min_turnover - avg_turnover
            gaps.append({
                "type": "financial",
                "message": f"Significant turnover gap: need {call.min_turnover:,.0f}€, have {avg_turnover:,.0f}€",
                "severity": "high",
            })
            return 20

    def _score_staff(self, call: FundingCall, profile: CompanyProfile, gaps: list) -> int:
        """Score staff capacity."""
        if not call.min_staff:
            return 80

        if not profile.total_staff:
            gaps.append({"type": "staff", "message": "Staff count not specified in profile", "severity": "medium"})
            return 50

        ratio = profile.total_staff / call.min_staff

        if ratio >= 1.2:
            return 100
        elif ratio >= 1.0:
            return 85
        elif ratio >= 0.6:
            gaps.append({
                "type": "staff",
                "message": f"Staff gap: need {call.min_staff}, have {profile.total_staff}",
                "severity": "medium",
            })
            return 50
        else:
            gaps.append({
                "type": "staff",
                "message": f"Significant staff gap: need {call.min_staff}, have {profile.total_staff}",
                "severity": "high",
            })
            return 20

        # Bonus for qualifications
        # TODO: check required expert profiles against staff_members

    def _score_experience(self, call: FundingCall, profile: CompanyProfile, gaps: list) -> int:
        """Score based on similar completed projects."""
        projects = profile.completed_projects or []
        if not projects:
            gaps.append({"type": "experience", "message": "No completed projects in profile", "severity": "medium"})
            return 30

        call_sectors = set(call.sectors or [])
        call_budget = call.budget_eur or 0

        # Count relevant projects
        relevant = []
        for proj in projects:
            if proj.sector and proj.sector in call_sectors:
                relevant.append(proj)
            elif proj.funding_source and call.programme and proj.funding_source.lower() in call.programme.lower():
                relevant.append(proj)

        if not relevant and call_sectors:
            # No exact match but have projects
            return 40

        if not relevant:
            return 60  # Have projects, call has no specific sector

        # Score based on relevance
        score = min(100, 50 + len(relevant) * 15)

        # Bonus if project values are in the right ballpark
        if call_budget > 0:
            max_project_value = max((p.value_eur or 0) for p in relevant)
            if max_project_value >= call_budget * 0.5:
                score = min(100, score + 10)

        return score

    def _score_geographic(self, call: FundingCall, profile: CompanyProfile, gaps: list) -> int:
        """Score geographic eligibility."""
        eligible = call.eligible_countries or []

        if not eligible:
            return 100  # No geographic restriction

        # Normalize
        eligible_set = {c.upper() for c in eligible}
        company_country = (profile.country or "GR").upper()
        company_reach = {c.upper() for c in (profile.geographic_reach or [company_country])}

        if "EU" in eligible_set:
            return 100  # All EU countries eligible

        if company_country in eligible_set:
            return 100

        if company_reach & eligible_set:
            return 90  # Company has reach in eligible country

        return 0  # Not eligible


def evaluate_batch(calls: list[FundingCall], profile: CompanyProfile) -> list[MatchResult]:
    """Evaluate multiple calls against a profile."""
    engine = MatchingEngine()
    return [engine.evaluate(call, profile) for call in calls]
