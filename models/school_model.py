# models/school.py

from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .department_model import Department
    from .campus_school import CampusSchoolAssociation
    from .faculty_model import Faculty

class School(Base):
    __tablename__ = "school"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    abv: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g., "SEN"

    # 🔗 Relationships
    departments: Mapped[list["Department"]] = relationship(back_populates="school", cascade="all, delete-orphan")
    campus_associations: Mapped[list["CampusSchoolAssociation"]] = relationship(back_populates="school", cascade="all, delete-orphan")
    faculties: Mapped[list["Faculty"]] = relationship("Faculty", back_populates="school")

    def __repr__(self) -> str:
        return f"<School id={self.id} name='{self.name}' abv='{self.abv}'>"
