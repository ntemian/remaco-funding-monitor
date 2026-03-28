"""SectorFilter — configurable watchlists for call filtering."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class SectorFilter(Base):
    __tablename__ = "sector_filters"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id"), index=True)

    name: Mapped[str] = mapped_column(String(255))  # e.g. "Digital Transformation"
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Filter criteria
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["AI", "machine learning", "data"]
    cpv_codes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["72000000", "48000000"]
    sources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["ted", "ftop"]
    programmes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["Horizon Europe", "Digital Europe"]

    # Thresholds
    min_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_match_score: Mapped[int] = mapped_column(Integer, default=50)  # Only show matches >= this score

    # Alert preferences
    alert_on_new: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_deadline_days: Mapped[int] = mapped_column(Integer, default=7)  # Alert when deadline < N days

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
