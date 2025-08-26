# models/course.py

from __future__ import annotations
from sqlalchemy import Integer, String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .department_model import Department
    from .program_course import ProgramCourseAssociation
    from .faculty_course_history_model import FacultyCourseHistory

class Course(Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g., CS101
    credits: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)       # e.g., 3.0, 1.5
    is_elective: Mapped[bool] = mapped_column(Boolean, default=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("department.id", ondelete="CASCADE"), nullable=False)

    # 🔗 Relationships
    department: Mapped[Department] = relationship(back_populates="courses")
    program_links: Mapped[list[ProgramCourseAssociation]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan"
    )
    faculty_course_histories: Mapped[list[FacultyCourseHistory]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course id={self.id} code='{self.code}' name='{self.name}' credits={self.credits}>"
