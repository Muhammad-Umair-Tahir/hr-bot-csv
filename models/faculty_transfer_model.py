# models/faculty_transfer.py

from __future__ import annotations
from sqlalchemy import Integer, String, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .faculty_model import Faculty
    from .department_model import Department
import enum
import datetime

class TransferStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class FacultyTransfer(Base):
    __tablename__ = "faculty_transfer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="CASCADE"))
    from_department_id: Mapped[int] = mapped_column(ForeignKey("department.id", ondelete="SET NULL"))
    to_department_id: Mapped[int] = mapped_column(ForeignKey("department.id", ondelete="SET NULL"))
    transfer_date: Mapped[datetime.date] = mapped_column(Date)
    approved_by: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)
    approved_on: Mapped[datetime.date] = mapped_column(Date)
    status: Mapped[TransferStatus] = mapped_column(Enum(TransferStatus), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    remarks: Mapped[str] = mapped_column(Text, nullable=True)

    # 🔗 Relationships
    faculty: Mapped['Faculty'] = relationship(
        "Faculty",
        back_populates="transfers",
        foreign_keys="[FacultyTransfer.faculty_id]"
    )
    from_department: Mapped["Department"] = relationship(
        foreign_keys=[from_department_id],
        back_populates="faculty_transfers_from"
    )
    to_department: Mapped["Department"] = relationship(
        foreign_keys=[to_department_id],
        back_populates="faculty_transfers_to"
    )
    approved_by_faculty: Mapped["Faculty"] = relationship(
        foreign_keys=[approved_by],
        primaryjoin="FacultyTransfer.approved_by == Faculty.id"
    )

    def __repr__(self) -> str:
        return f"<FacultyTransfer id={self.id} faculty_id={self.faculty_id} from={self.from_department_id} to={self.to_department_id}>"
