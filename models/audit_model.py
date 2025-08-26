from sqlalchemy import Integer, String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from models.base_model import Base
import datetime

class Audit(Base):
    __tablename__ = "audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., INSERT, UPDATE, DELETE
    record_id: Mapped[str] = mapped_column(String(50), nullable=False)  # Primary key of affected record
    changed_by: Mapped[str] = mapped_column(String(100), nullable=True)  # Username or user id
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    old_data: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string of old data
    new_data: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string of new data
    remarks: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Audit id={self.id} table={self.table_name} action={self.action} "
            f"record_id={self.record_id} changed_by={self.changed_by} at={self.changed_at}>"
        )