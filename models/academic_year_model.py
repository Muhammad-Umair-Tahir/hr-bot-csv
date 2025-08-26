from __future__ import annotations
from sqlalchemy import Integer, String, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .faculty_track_assignment_model import FacultyTrackAssignment
    from .semester_model import Semester
from models.base_model import Base

class AcademicYear(Base):
    semesters: Mapped[list["Semester"]] = relationship(back_populates="academic_year", cascade="all, delete-orphan")
    # 🔗 Relationships
    track_assignments: Mapped[list["FacultyTrackAssignment"]] = relationship(back_populates="academic_year", cascade="all, delete-orphan")
    __tablename__ = "academic_year"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g., "2025-2026"
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<AcademicYear id={self.id} name='{self.name}' is_current={self.is_current}>"
