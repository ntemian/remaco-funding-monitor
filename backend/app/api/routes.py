"""FastAPI routes for the Remaco EU Funding Monitor."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import get_db
from app.models.funding_call import FundingCall, CallSource, CallStatus
from app.models.company_profile import CompanyProfile, CompletedProject, StaffMember
from app.models.match_result import MatchResult, MatchVerdict
from app.models.feedback import Feedback
from app.models.sector_filter import SectorFilter
from app.services.pipeline import DailyPipeline

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CallOut(BaseModel):
    id: int
    external_id: str
    source: str
    status: str
    title: str
    title_el: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    programme: Optional[str] = None
    sectors: Optional[list] = None
    cpv_codes: Optional[list] = None
    budget_eur: Optional[float] = None
    deadline: Optional[date] = None
    publication_date: Optional[date] = None
    authority_name: Optional[str] = None
    authority_country: Optional[str] = None
    days_until_deadline: Optional[int] = None

    class Config:
        from_attributes = True


class MatchOut(BaseModel):
    id: int
    call_id: int
    profile_id: int
    score: int
    verdict: str
    sector_score: Optional[int] = None
    financial_score: Optional[int] = None
    staff_score: Optional[int] = None
    experience_score: Optional[int] = None
    geographic_score: Optional[int] = None
    gaps: Optional[list] = None
    recommendations: Optional[list] = None
    bookmarked: bool = False
    dismissed: bool = False
    call: Optional[CallOut] = None

    class Config:
        from_attributes = True


class ProfileIn(BaseModel):
    name: str
    tax_id: Optional[str] = None
    country: str = "GR"
    turnover_year1: Optional[float] = None
    turnover_year2: Optional[float] = None
    turnover_year3: Optional[float] = None
    total_staff: Optional[int] = None
    phd_count: Optional[int] = None
    msc_count: Optional[int] = None
    certifications: Optional[list[str]] = None
    sectors: Optional[list[str]] = None
    geographic_reach: Optional[list[str]] = None
    known_partners: Optional[list[dict]] = None


class ProjectIn(BaseModel):
    title: str
    description: Optional[str] = None
    client: Optional[str] = None
    sector: Optional[str] = None
    value_eur: Optional[float] = None
    year_completed: Optional[int] = None
    country: Optional[str] = None
    funding_source: Optional[str] = None


class FilterIn(BaseModel):
    name: str
    keywords: Optional[list[str]] = None
    cpv_codes: Optional[list[str]] = None
    sources: Optional[list[str]] = None
    programmes: Optional[list[str]] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    min_match_score: int = 50


class PipelineStats(BaseModel):
    new_calls: int
    updated_calls: int
    matches_created: int
    errors: list[str]


# ── Calls ──────────────────────────────────────────────────────────────────────

@router.get("/calls")
async def list_calls(
    status: Optional[CallStatus] = None,
    source: Optional[CallSource] = None,
    sector: Optional[str] = None,
    min_budget: Optional[float] = None,
    deadline_before: Optional[date] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List funding calls with filters."""
    q = select(FundingCall).order_by(desc(FundingCall.deadline))

    if status:
        q = q.where(FundingCall.status == status)
    if source:
        q = q.where(FundingCall.source == source)
    if min_budget:
        q = q.where(FundingCall.budget_eur >= min_budget)
    if deadline_before:
        q = q.where(FundingCall.deadline <= deadline_before)
    if search:
        q = q.where(FundingCall.title.ilike(f"%{search}%"))

    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    return [_serialize_call(c) for c in result.scalars().all()]


def _serialize_call(c: FundingCall) -> dict:
    return {
        "id": c.id,
        "external_id": c.external_id,
        "source": c.source.value,
        "status": c.status.value,
        "title": c.title,
        "title_el": c.title_el,
        "description": c.description,
        "url": c.url,
        "programme": c.programme,
        "sectors": c.sectors,
        "cpv_codes": c.cpv_codes,
        "budget_eur": c.budget_eur,
        "deadline": c.deadline.isoformat() if c.deadline else None,
        "publication_date": c.publication_date.isoformat() if c.publication_date else None,
        "authority_name": c.authority_name,
        "authority_country": c.authority_country,
        "days_until_deadline": c.days_until_deadline(),
    }


@router.get("/calls/stats")
async def call_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate stats about calls in the database."""
    total = (await db.execute(select(func.count(FundingCall.id)))).scalar()
    open_count = (await db.execute(
        select(func.count(FundingCall.id)).where(FundingCall.status == CallStatus.OPEN)
    )).scalar()
    closing = (await db.execute(
        select(func.count(FundingCall.id)).where(FundingCall.status == CallStatus.CLOSING_SOON)
    )).scalar()

    return {
        "total": total,
        "open": open_count,
        "closing_soon": closing,
        "sources": {
            s.value: (await db.execute(
                select(func.count(FundingCall.id)).where(FundingCall.source == s)
            )).scalar()
            for s in CallSource
        },
    }


@router.get("/calls/{call_id}")
async def get_call(call_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single funding call."""
    call = (await db.execute(select(FundingCall).where(FundingCall.id == call_id))).scalar_one_or_none()
    if not call:
        raise HTTPException(404, "Call not found")
    return _serialize_call(call)


# ── Profile ────────────────────────────────────────────────────────────────────

@router.post("/profiles", response_model=dict)
async def create_profile(data: ProfileIn, db: AsyncSession = Depends(get_db)):
    """Create a company profile."""
    profile = CompanyProfile(**data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return {"id": profile.id, "name": profile.name}


@router.get("/profiles")
async def list_profiles(db: AsyncSession = Depends(get_db)):
    """List all company profiles."""
    result = await db.execute(select(CompanyProfile))
    return [{"id": p.id, "name": p.name, "country": p.country, "avg_turnover": p.avg_turnover}
            for p in result.scalars().all()]


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    """Get a company profile with projects and staff."""
    profile = (await db.execute(
        select(CompanyProfile)
        .where(CompanyProfile.id == profile_id)
        .options(selectinload(CompanyProfile.completed_projects), selectinload(CompanyProfile.staff_members))
    )).scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile


@router.put("/profiles/{profile_id}")
async def update_profile(profile_id: int, data: ProfileIn, db: AsyncSession = Depends(get_db)):
    """Update a company profile."""
    profile = (await db.execute(select(CompanyProfile).where(CompanyProfile.id == profile_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await db.commit()
    return {"status": "updated"}


@router.post("/profiles/{profile_id}/projects")
async def add_project(profile_id: int, data: ProjectIn, db: AsyncSession = Depends(get_db)):
    """Add a completed project to a company profile."""
    project = CompletedProject(company_id=profile_id, **data.model_dump())
    db.add(project)
    await db.commit()
    return {"id": project.id, "title": project.title}


# ── Matches ────────────────────────────────────────────────────────────────────

@router.get("/matches")
async def list_matches(
    profile_id: int = Query(...),
    verdict: Optional[MatchVerdict] = None,
    min_score: int = Query(0, ge=0, le=100),
    bookmarked_only: bool = False,
    hide_dismissed: bool = True,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List match results for a profile, sorted by score."""
    q = (
        select(MatchResult)
        .where(MatchResult.profile_id == profile_id)
        .where(MatchResult.score >= min_score)
        .order_by(desc(MatchResult.score))
    )
    if verdict:
        q = q.where(MatchResult.verdict == verdict)
    if bookmarked_only:
        q = q.where(MatchResult.bookmarked == True)
    if hide_dismissed:
        q = q.where(MatchResult.dismissed == False)

    q = q.options(selectinload(MatchResult.call))
    q = q.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(q)
    matches = result.scalars().all()

    return [
        {
            "id": m.id,
            "call_id": m.call_id,
            "profile_id": m.profile_id,
            "score": m.score,
            "verdict": m.verdict.value,
            "sector_score": m.sector_score,
            "financial_score": m.financial_score,
            "staff_score": m.staff_score,
            "experience_score": m.experience_score,
            "geographic_score": m.geographic_score,
            "gaps": m.gaps,
            "recommendations": m.recommendations,
            "bookmarked": m.bookmarked,
            "dismissed": m.dismissed,
            "call": {
                "id": m.call.id,
                "title": m.call.title,
                "source": m.call.source.value,
                "status": m.call.status.value,
                "programme": m.call.programme,
                "budget_eur": m.call.budget_eur,
                "deadline": m.call.deadline.isoformat() if m.call.deadline else None,
                "url": m.call.url,
                "authority_name": m.call.authority_name,
                "sectors": m.call.sectors,
                "days_until_deadline": m.call.days_until_deadline(),
            } if m.call else None,
        }
        for m in matches
    ]


@router.get("/matches/stats")
async def match_stats(profile_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """Get match verdict counts for a profile."""
    total = (await db.execute(
        select(func.count(MatchResult.id)).where(MatchResult.profile_id == profile_id)
    )).scalar()
    go = (await db.execute(
        select(func.count(MatchResult.id)).where(
            MatchResult.profile_id == profile_id, MatchResult.verdict == MatchVerdict.GO
        )
    )).scalar()
    consortium = (await db.execute(
        select(func.count(MatchResult.id)).where(
            MatchResult.profile_id == profile_id, MatchResult.verdict == MatchVerdict.CONSORTIUM
        )
    )).scalar()
    no_go = (await db.execute(
        select(func.count(MatchResult.id)).where(
            MatchResult.profile_id == profile_id, MatchResult.verdict == MatchVerdict.NO_GO
        )
    )).scalar()
    return {"total": total, "go": go, "consortium": consortium, "no_go": no_go}


@router.post("/matches/{match_id}/bookmark")
async def toggle_bookmark(match_id: int, db: AsyncSession = Depends(get_db)):
    """Toggle bookmark on a match."""
    match = (await db.execute(select(MatchResult).where(MatchResult.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(404, "Match not found")
    match.bookmarked = not match.bookmarked
    await db.commit()
    return {"bookmarked": match.bookmarked}


@router.post("/matches/{match_id}/dismiss")
async def dismiss_match(match_id: int, db: AsyncSession = Depends(get_db)):
    """Dismiss a match (hide from default view)."""
    match = (await db.execute(select(MatchResult).where(MatchResult.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(404, "Match not found")
    match.dismissed = True
    await db.commit()
    return {"dismissed": True}


# ── Filters ────────────────────────────────────────────────────────────────────

@router.post("/filters")
async def create_filter(data: FilterIn, profile_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """Create a sector watchlist filter."""
    f = SectorFilter(profile_id=profile_id, **data.model_dump())
    db.add(f)
    await db.commit()
    return {"id": f.id, "name": f.name}


@router.get("/filters")
async def list_filters(profile_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """List all filters for a profile."""
    result = await db.execute(select(SectorFilter).where(SectorFilter.profile_id == profile_id))
    return result.scalars().all()


# ── Pipeline ───────────────────────────────────────────────────────────────────

@router.post("/pipeline/run", response_model=PipelineStats)
async def run_pipeline(days_back: int = Query(1, ge=1, le=30), db: AsyncSession = Depends(get_db)):
    """Manually trigger the daily pipeline."""
    pipeline = DailyPipeline(db)
    stats = await pipeline.run(days_back=days_back)
    return stats


@router.get("/pipeline/status")
async def pipeline_status(db: AsyncSession = Depends(get_db)):
    """Get pipeline health status."""
    total_calls = (await db.execute(select(func.count(FundingCall.id)))).scalar()
    latest_call = (await db.execute(
        select(FundingCall).order_by(desc(FundingCall.created_at)).limit(1)
    )).scalar_one_or_none()

    return {
        "total_calls_in_db": total_calls,
        "latest_call_date": latest_call.created_at.isoformat() if latest_call else None,
        "status": "healthy" if total_calls > 0 else "empty",
    }


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackIn(BaseModel):
    name: str
    type: str
    message: str


@router.post("/feedback")
async def submit_feedback(data: FeedbackIn, db: AsyncSession = Depends(get_db)):
    """Submit a feedback request."""
    fb = Feedback(name=data.name, type=data.type, message=data.message)
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return {"id": fb.id, "status": "received"}


@router.get("/feedback")
async def list_feedback(db: AsyncSession = Depends(get_db)):
    """List all feedback submissions."""
    result = await db.execute(select(Feedback).order_by(desc(Feedback.created_at)))
    return [
        {
            "id": f.id, "name": f.name, "type": f.type,
            "message": f.message, "reviewed": f.reviewed,
            "date": f.created_at.strftime("%Y-%m-%d"),
        }
        for f in result.scalars().all()
    ]


@router.post("/feedback/{fb_id}/review")
async def mark_reviewed(fb_id: int, db: AsyncSession = Depends(get_db)):
    """Mark feedback as reviewed."""
    fb = (await db.execute(select(Feedback).where(Feedback.id == fb_id))).scalar_one_or_none()
    if not fb:
        raise HTTPException(404, "Feedback not found")
    fb.reviewed = True
    await db.commit()
    return {"reviewed": True}
