# models/campus_school_association.py

from __future__ import annotations
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .campus_model import Campus
    from .school_model import School

class CampusSchoolAssociation(Base):
    __tablename__ = "campus_school_association"

    campus_id: Mapped[int] = mapped_column(ForeignKey("campus.id", ondelete="CASCADE"), primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("school.id", ondelete="CASCADE"), primary_key=True)

    # 🔗 Relationships
    campus: Mapped["Campus"] = relationship(back_populates="school_associations")
    school: Mapped["School"] = relationship(back_populates="campus_associations")

    def __repr__(self) -> str:
        return f"<CampusSchoolAssociation campus_id={self.campus_id} school_id={self.school_id}>"
