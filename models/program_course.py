# models/program_course_association.py

from __future__ import annotations
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .program_model import Program
    from .course_model import Course

class ProgramCourseAssociation(Base):
    __tablename__ = "program_course_association"

    program_id: Mapped[int] = mapped_column(ForeignKey("program.id", ondelete="CASCADE"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id", ondelete="CASCADE"), primary_key=True)

    # 🔗 Relationships
    program: Mapped["Program"] = relationship(back_populates="course_links")
    course: Mapped["Course"] = relationship(back_populates="program_links")

    def __repr__(self) -> str:
        return f"<ProgramCourseAssociation program_id={self.program_id} course_id={self.course_id}>"
