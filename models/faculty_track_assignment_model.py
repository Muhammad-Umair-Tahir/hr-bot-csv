from __future__ import annotations
from sqlalchemy import Integer, ForeignKey, Date, Text, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING
import datetime
import enum

if TYPE_CHECKING:
    from .faculty_model import Faculty
    from .tracks_model import Track
    from .track_level import TrackLevel
    from .academic_year_model import AcademicYear


class Status(enum.Enum):
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class FacultyTrackAssignment(Base):
    __tablename__ = "faculty_track_assignment"
    __table_args__ = (
        UniqueConstraint("faculty_id", "academic_year_id", name="uq_faculty_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    track_id: Mapped[int] = mapped_column(ForeignKey("track.id", ondelete="SET NULL"), nullable=True)
    track_level_id: Mapped[int] = mapped_column(ForeignKey("track_level.id", ondelete="SET NULL"), nullable=True)
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_year.id", ondelete="SET NULL"), nullable=True)

    remarks: Mapped[str] = mapped_column(Text, nullable=True)

    status: Mapped[Status] = mapped_column(SAEnum(Status), default=None, nullable=False)
    submitted_on: Mapped[datetime.date] = mapped_column(Date, nullable=True)

    approved_by: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)
    approved_on: Mapped[datetime.date] = mapped_column(Date, nullable=True)

    # Relationships (minimal)
    faculty: Mapped["Faculty"] = relationship(back_populates="track_assignments", foreign_keys=[faculty_id])
    track: Mapped["Track"] = relationship(back_populates="track_assignments")
    track_level: Mapped["TrackLevel"] = relationship(back_populates="track_assignments")
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="track_assignments")
    approved_by_faculty: Mapped["Faculty"] = relationship(
        foreign_keys=[approved_by],
        primaryjoin="FacultyTrackAssignment.approved_by == Faculty.id",
    )

    def __repr__(self) -> str:
        return f"<FacultyTrackAssignment id={self.id} faculty_id={self.faculty_id} status={self.status.value}>" 