from __future__ import annotations
from sqlalchemy import Integer, ForeignKey, Date, Boolean, Text, Enum
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


class SubmissionStatus(enum.Enum):
    draft = "draft"
    submitted = "submitted"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"


class ReviewStage(enum.Enum):
    faculty = "faculty"
    cod = "cod"
    dean = "dean"
    hr = "hr"


class FacultyTrackAssignment(Base):
    __tablename__ = "faculty_track_assignment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    track_id: Mapped[int] = mapped_column(ForeignKey("track.id", ondelete="SET NULL"), nullable=True)
    track_level_id: Mapped[int] = mapped_column(ForeignKey("track_level.id", ondelete="SET NULL"), nullable=True)
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_year.id", ondelete="SET NULL"), nullable=True)

    submission_status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus), default=SubmissionStatus.draft
    )
    review_stage: Mapped[ReviewStage] = mapped_column(Enum(ReviewStage), default=ReviewStage.faculty)
    submitted_on: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    justification: Mapped[str] = mapped_column(Text, nullable=True)

    cod_comments: Mapped[str] = mapped_column(Text, nullable=True)
    dean_comments: Mapped[str] = mapped_column(Text, nullable=True)
    hr_comments: Mapped[str] = mapped_column(Text, nullable=True)

    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False)

    recommended_by: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)
    approved_by: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)
    approved_on: Mapped[datetime.date] = mapped_column(Date, nullable=True)

    # 🔗 Relationships
    faculty: Mapped["Faculty"] = relationship(
        back_populates="track_assignments", foreign_keys=[faculty_id]
    )
    track: Mapped["Track"] = relationship(back_populates="track_assignments")
    track_level: Mapped["TrackLevel"] = relationship(back_populates="track_assignments")
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="track_assignments")

    recommended_by_faculty: Mapped["Faculty"] = relationship(
        foreign_keys=[recommended_by],
        primaryjoin="FacultyTrackAssignment.recommended_by == Faculty.id"
    )
    approved_by_faculty: Mapped["Faculty"] = relationship(
        foreign_keys=[approved_by],
        primaryjoin="FacultyTrackAssignment.approved_by == Faculty.id"
    )

    def __repr__(self) -> str:
        return (
            f"<FacultyTrackAssignment id={self.id} faculty_id={self.faculty_id} "
            f"track_id={self.track_id} level_id={self.track_level_id} "
            f"status={self.submission_status.value} stage={self.review_stage.value}>"
        )
