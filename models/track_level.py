from __future__ import annotations
from sqlalchemy import Integer, String, Text, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tracks_model import Track
    from .faculty_track_assignment_model import FacultyTrackAssignment
    from .faculty_model import Faculty


class TrackLevel(Base):
    __tablename__ = "track_level"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("track.id", ondelete="CASCADE"), nullable=False)

    level_code: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g., "L1", "L2"
    title: Mapped[str] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Level-specific requirements
    course_load_min: Mapped[int] = mapped_column(Integer, nullable=True)
    course_load_max: Mapped[int] = mapped_column(Integer, nullable=True)
    min_publications: Mapped[int] = mapped_column(Integer, nullable=True)

    min_funding_required: Mapped[int] = mapped_column(Integer, nullable=True)
    funding_max: Mapped[int] = mapped_column(Integer, nullable=True)  # NEW
    min_consulting_required: Mapped[int] = mapped_column(Integer, nullable=True)
    case_studies_required: Mapped[int] = mapped_column(Integer, nullable=True)  # NEW

    experience_min: Mapped[int] = mapped_column(Integer, nullable=True)  # NEW
    experience_max: Mapped[int] = mapped_column(Integer, nullable=True)  # NEW

    is_admin_eligible: Mapped[bool] = mapped_column(Boolean, default=False)

    # 🔗 Relationships
    track: Mapped["Track"] = relationship(back_populates="levels")
    track_assignments: Mapped[list["FacultyTrackAssignment"]] = relationship(
        back_populates="track_level"
    )
    faculties: Mapped[list["Faculty"]] = relationship(
        back_populates="track_level",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TrackLevel id={self.id} track_id={self.track_id} level_code='{self.level_code}'>"
