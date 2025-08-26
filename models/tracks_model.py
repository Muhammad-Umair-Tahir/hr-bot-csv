from __future__ import annotations
from sqlalchemy import Integer, String, Text, Boolean, Enum, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING
import enum

if TYPE_CHECKING:
    from .faculty_model import Faculty
    from .faculty_track_assignment_model import FacultyTrackAssignment
    from .track_level import TrackLevel


class TrackType(str, enum.Enum):
    teaching = "teaching"
    research = "research"
    innovation = "innovation"
    industry = "industry"


class EligibilityCriteria(str, enum.Enum):
    auto_phd = "auto_phd"
    manual_check = "manual_check"
    industry_only = "industry_only"
    research_funded = "research_funded"
    restricted = "restricted"


class Track(Base):
    __tablename__ = "track"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Track-wide policies
    percentage_cap: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    track_type: Mapped[TrackType] = mapped_column(Enum(TrackType))
    eligibility_criteria: Mapped[EligibilityCriteria] = mapped_column(
        Enum(EligibilityCriteria), default=EligibilityCriteria.manual_check
    )
    allow_self_selection: Mapped[bool] = mapped_column(Boolean, default=True)
    is_special_track: Mapped[bool] = mapped_column(Boolean, default=False)
    title_suffix: Mapped[str] = mapped_column(String(50), nullable=True)

    course_load_policy: Mapped[str] = mapped_column(Text, nullable=True)
    research_requirement: Mapped[str] = mapped_column(Text, nullable=True)
    admin_limitations: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 🔗 Relationships
    faculties: Mapped[list["Faculty"]] = relationship(back_populates="track")
    track_assignments: Mapped[list["FacultyTrackAssignment"]] = relationship(
        back_populates="track", cascade="all, delete-orphan"
    )
    levels: Mapped[list["TrackLevel"]] = relationship(
        back_populates="track", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Track id={self.id} code='{self.code}' name='{self.name}'>"
