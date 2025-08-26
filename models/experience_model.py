# models/experience.py

from __future__ import annotations
from sqlalchemy import Integer, String, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .person_model import Person
import datetime

class Experience(Base):
    __tablename__ = "experience"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    organization: Mapped[str] = mapped_column(String(150), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # 🔗 Relationship to Person
    person: Mapped["Person"] = relationship(back_populates="experiences")

    def __repr__(self) -> str:
        return f"<Experience id={self.id} person_id={self.person_id} job_title='{self.job_title}'>"
