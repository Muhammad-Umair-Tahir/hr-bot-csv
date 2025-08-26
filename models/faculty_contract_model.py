# models/faculty_contract.py

from __future__ import annotations
from sqlalchemy import Integer, String, Date, ForeignKey, Boolean, Enum, Text, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
import enum
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .faculty_model import Faculty

class ContractStatus(enum.Enum):
    active = "active"
    expired = "expired"
    terminated = "terminated"
    resigned = "resigned"

class ContractType(enum.Enum):
    FCA = "FCA"
    FTC = "FTC"
    FTC_Adhoc = "FTC - Adhoc"
    FTP = "FTP"
    FTP_Adhoc = "FTP - Adhoc"
    PTC = "PTC"

class FacultyContract(Base):
    __tablename__ = "faculty_contract"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    contract_type: Mapped[ContractType] = mapped_column(Enum(ContractType), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), nullable=False)
    is_renewable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remarks: Mapped[str] = mapped_column(Text, nullable=True)

    # 🔗 Relationship to Faculty
    faculty: Mapped[Faculty] = relationship(back_populates="contracts")

    def __repr__(self) -> str:
        return f"<FacultyContract id={self.id} faculty_id={self.faculty_id} status='{self.status.value}'>"
