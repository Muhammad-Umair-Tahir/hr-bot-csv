# models/campus.py

from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .campus_school import CampusSchoolAssociation

class Campus(Base):
    __tablename__ = "campus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    # 🔗 Relationship to CampusSchoolAssociation
    school_associations: Mapped[List["CampusSchoolAssociation"]] = relationship(
        back_populates="campus",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Campus id={self.id} name='{self.name}' location='{self.location}'>"
