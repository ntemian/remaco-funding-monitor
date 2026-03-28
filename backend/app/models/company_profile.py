"""CompanyProfile — Remaco's (or any company's) capability profile for eligibility matching."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ΑΦΜ
    country: Mapped[str] = mapped_column(String(3), default="GR")

    # Financial capacity (last 3 years)
    turnover_year1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turnover_year2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turnover_year3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Staff
    total_staff: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phd_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    msc_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Certifications & capacity
    certifications: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["ISO 9001", "ISO 27001"]
    sectors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["digital", "environment"]
    geographic_reach: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["GR", "CY", "BG"]

    # Consortium partners
    known_partners: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # [{name, sector, country}]

    # Relationships
    completed_projects: Mapped[list["CompletedProject"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    staff_members: Mapped[list["StaffMember"]] = relationship(back_populates="company", cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def avg_turnover(self) -> Optional[float]:
        values = [v for v in [self.turnover_year1, self.turnover_year2, self.turnover_year3] if v]
        return sum(values) / len(values) if values else None

    def __repr__(self):
        return f"<CompanyProfile {self.name}>"


class CompletedProject(Base):
    __tablename__ = "completed_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id"))
    company: Mapped["CompanyProfile"] = relationship(back_populates="completed_projects")

    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    client: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    value_eur: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    year_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    funding_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "ESPA", "Horizon", etc.


class StaffMember(Base):
    __tablename__ = "staff_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id"))
    company: Mapped["CompanyProfile"] = relationship(back_populates="staff_members")

    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "Project Manager", "Senior Engineer"
    qualification: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "PhD", "MSc", "BSc"
    sectors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    years_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
