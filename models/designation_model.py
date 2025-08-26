# models/designation.py

from __future__ import annotations
from sqlalchemy import Integer, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .faculty_model import Faculty
import enum

class DesignationType(enum.Enum):
    academic = "academic"
    administrative = "administrative"

class Designation(Base):
    __tablename__ = "designation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[DesignationType] = mapped_column(Enum(DesignationType), nullable=False)

    # 🔗 Relationships
    faculties: Mapped[list["Faculty"]] = relationship(
        back_populates="designation"
    )

    def __repr__(self) -> str:
        return f"<Designation id={self.id} title='{self.title}' type='{self.type.value}'>"
