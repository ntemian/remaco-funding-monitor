"""FundingCall — a single tender, grant call, or call for proposals."""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Text, Float, Date, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.models.database import Base


class CallSource(str, enum.Enum):
    TED = "ted"                  # Tenders Electronic Daily
    FTOP = "ftop"                # Funding & Tenders Portal
    ESPA = "espa"                # ΕΣΠΑ 2021-2027
    RECOVERY = "recovery"        # Greece 2.0 Recovery Fund
    GREEN = "green"              # Πράσινο Ταμείο
    JTF = "jtf"                  # Just Transition Fund
    AMIF = "amif"                # Migration & Asylum Fund
    EDF = "edf"                  # European Defence Fund
    OTHER = "other"


class CallStatus(str, enum.Enum):
    OPEN = "open"
    CLOSING_SOON = "closing_soon"  # < 7 days
    CLOSED = "closed"
    UPCOMING = "upcoming"


class FundingCall(Base):
    __tablename__ = "funding_calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source: Mapped[CallSource] = mapped_column(SAEnum(CallSource), index=True)
    status: Mapped[CallStatus] = mapped_column(SAEnum(CallStatus), default=CallStatus.OPEN, index=True)

    # Core fields
    title: Mapped[str] = mapped_column(Text)
    title_el: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Programme & classification
    programme: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g. "Horizon Europe", "AMIF"
    cpv_codes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # EU CPV classification codes
    sectors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["digital", "environment", "defence"]
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Financial
    budget_eur: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_grant: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_grant: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    co_financing_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # e.g. 0.80 = 80%

    # Eligibility
    eligible_countries: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    min_turnover: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_staff: Mapped[Optional[int]] = mapped_column(nullable=True)
    required_certifications: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    consortium_required: Mapped[Optional[bool]] = mapped_column(nullable=True)
    min_consortium_partners: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Dates
    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Contracting authority
    authority_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    authority_country: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)

    # Metadata
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def days_until_deadline(self) -> Optional[int]:
        if self.deadline:
            return (self.deadline - date.today()).days
        return None

    def __repr__(self):
        return f"<FundingCall {self.external_id}: {self.title[:60]}>"
