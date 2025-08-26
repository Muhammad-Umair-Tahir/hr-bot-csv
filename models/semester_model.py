from __future__ import annotations
from sqlalchemy import Integer, String, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .academic_year_model import AcademicYear
    from .faculty_course_history_model import FacultyCourseHistory

class Semester(Base):
    __tablename__ = "semester"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "Fall", "Spring"
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_year.id", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)

    # 🔗 Relationships
    academic_year: Mapped[AcademicYear] = relationship(back_populates="semesters")
    faculty_course_histories: Mapped[list["FacultyCourseHistory"]] = relationship("FacultyCourseHistory", back_populates="semester")

    def __repr__(self) -> str:
        return f"<Semester id={self.id} name='{self.name}' academic_year_id={self.academic_year_id}>"
