# models/program.py

from __future__ import annotations
from sqlalchemy import Integer, String, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .department_model import Department
    from .program_course import ProgramCourseAssociation

class ProgramLevel(enum.Enum):
    BS = "BS"
    MS = "MS"
    PhD = "PhD"

class Program(Base):
    __tablename__ = "program"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    level: Mapped[ProgramLevel] = mapped_column(Enum(ProgramLevel), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("department.id", ondelete="CASCADE"))

    # 🔗 Relationships
    department: Mapped["Department"] = relationship(back_populates="programs")
    course_links: Mapped[list["ProgramCourseAssociation"]] = relationship(
        back_populates="program", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Program id={self.id} name='{self.name}' level={self.level.value}>"
