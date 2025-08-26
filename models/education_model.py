# models/education.py

from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .person_model import Person


class Qualification(Base):
    __tablename__ = "qualification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)  # 'Education' or 'Experience'
    title: Mapped[str] = mapped_column(String(100), nullable=False)  # Degree, job title, or certification
    institution: Mapped[str] = mapped_column(String(150), nullable=True)  # University, company, or institute
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    start_year: Mapped[int] = mapped_column(Integer, nullable=True)  # For experience
    end_year: Mapped[int] = mapped_column(Integer, nullable=True)    # For experience
    year: Mapped[int] = mapped_column(Integer, nullable=True)        # For education (year of graduation)
    remarks: Mapped[str] = mapped_column(String(200), nullable=True)  # Any extra info (optional)

    # 🔗 Relationship to Person
    person: Mapped["Person"] = relationship(back_populates="qualifications")

    def __repr__(self) -> str:
        return f"<Qualification id={self.id} person_id={self.person_id} category='{self.category}' title='{self.title}'>"


