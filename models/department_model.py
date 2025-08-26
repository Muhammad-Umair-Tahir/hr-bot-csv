# models/department.py

from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .school_model import School
    from .course_model import Course
    from .program_model import Program
    from .faculty_model import Faculty
    from .faculty_course_history_model import FacultyCourseHistory
    from .faculty_transfer_model import FacultyTransfer

class Department(Base):
    __tablename__ = "department"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    abv: Mapped[str] = mapped_column(String(20), unique=True, nullable=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("school.id", ondelete="CASCADE"), nullable=False)

    # 🔗 Relationships
    school: Mapped["School"] = relationship(back_populates="departments")
    courses: Mapped[list["Course"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    programs: Mapped[list["Program"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    faculty_course_histories: Mapped[list["FacultyCourseHistory"]] = relationship(back_populates="assigned_by_department", cascade="all, delete-orphan")    
    faculties: Mapped[list["Faculty"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    faculty_transfers_from: Mapped[list["FacultyTransfer"]] = relationship(
        back_populates="from_department",
        foreign_keys="FacultyTransfer.from_department_id",
        cascade="all, delete-orphan"
    )
    faculty_transfers_to: Mapped[list["FacultyTransfer"]] = relationship(
        back_populates="to_department",
        foreign_keys="FacultyTransfer.to_department_id",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id} name='{self.name}' abv='{self.abv}' school_id={self.school_id}>"
