"""MatchResult — eligibility assessment of a FundingCall against a CompanyProfile."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.database import Base


class MatchVerdict(str, enum.Enum):
    GO = "go"              # 🟢 Eligible, can bid solo
    CONSORTIUM = "consortium"  # 🟡 Needs consortium partner
    NO_GO = "no_go"        # 🔴 Not eligible


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("funding_calls.id"), index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id"), index=True)

    call: Mapped["FundingCall"] = relationship()
    profile: Mapped["CompanyProfile"] = relationship()

    # Scoring
    score: Mapped[int] = mapped_column(Integer)  # 0-100
    verdict: Mapped[MatchVerdict] = mapped_column(SAEnum(MatchVerdict))

    # Breakdown
    sector_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)      # 0-100
    financial_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)    # 0-100
    staff_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)        # 0-100
    experience_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 0-100
    geographic_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 0-100

    # Gap analysis
    gaps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    # e.g. [{"type": "turnover", "message": "Need €500K more — consider consortium"},
    #        {"type": "certification", "message": "Missing ISO 14001"}]

    recommendations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    # e.g. ["Partner with EcoTech for environmental certification"]

    # Metadata
    matched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dismissed: Mapped[bool] = mapped_column(default=False)  # User dismissed this match
    bookmarked: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        return f"<MatchResult call={self.call_id} score={self.score} {self.verdict.value}>"
