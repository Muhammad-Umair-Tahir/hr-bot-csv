# models/faculty_course_history.py

from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .faculty_model import Faculty
    from .course_model import Course
    from .department_model import Department
    from .semester_model import Semester

class FacultyCourseHistory(Base):
    __tablename__ = "faculty_course_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    assigned_by_dept_id: Mapped[int] = mapped_column(ForeignKey("department.id", ondelete="CASCADE"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id", ondelete="CASCADE"), nullable=False)
    credit_hours: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    is_cross_dept: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_for_cross: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remarks: Mapped[str] = mapped_column(String(255), nullable=True)

    # 🔗 Relationships
    faculty: Mapped[Faculty] = relationship(back_populates="course_history")
    course: Mapped[Course] = relationship(back_populates="faculty_course_histories")
    assigned_by_department: Mapped[Department] = relationship(back_populates="faculty_course_histories")
    semester: Mapped["Semester"] = relationship(back_populates="faculty_course_histories")

    def __repr__(self) -> str:
        return (
            f"<FacultyCourseHistory id={self.id} faculty_id={self.faculty_id} "
            f"course_id={self.course_id} semester='{self.semester}'>"
        )
