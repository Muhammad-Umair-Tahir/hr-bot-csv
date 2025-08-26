# models/person.py

from __future__ import annotations
from sqlalchemy import Integer, String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import Base
import datetime
from cryptography.fernet import Fernet
import os
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .faculty_model import Faculty
    from .education_model import Qualification
    from .experience_model import Experience

# Load or generate encryption key
FERNET_KEY = os.getenv("FERNET_KEY")
_logger = logging.getLogger("PersonModel")
if FERNET_KEY:
    fernet: Fernet | None = Fernet(FERNET_KEY)
else:
    # Fallback to no-encryption mode for non-prod/dev environments to avoid import-time crashes
    fernet = None
    _logger.warning("FERNET_KEY not set. CNIC values will be stored/read as plaintext. Set FERNET_KEY in production.")

class Person(Base):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    father_husband_name: Mapped[str] = mapped_column(String(100), nullable=True)
    sex: Mapped[str] = mapped_column(String(10), nullable=False)
    dob: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    _cnic: Mapped[str] = mapped_column("cnic", String(200), unique=True, nullable=True)  # Increased to 200 for encrypted values
    cnic_expiry: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(200), unique=False, nullable=True)  # Increased length, removed unique constraint
    blood_group: Mapped[str] = mapped_column(String(10), nullable=True)
    marital_status: Mapped[str] = mapped_column(String(20), nullable=True)
    date_of_marriage: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    no_of_dependents: Mapped[int] = mapped_column(Integer, nullable=True)

    # 🔗 Relationships
    # user relationship removed
    qualifications: Mapped[list["Qualification"]] = relationship(back_populates="person", cascade="all, delete-orphan")
    experiences: Mapped[list["Experience"]] = relationship(back_populates="person", cascade="all, delete-orphan")
    faculty: Mapped["Faculty"] = relationship(back_populates="person", uselist=False)

    # 🔐 CNIC encryption/decryption
    @property
    def cnic(self) -> str:
        if not self._cnic:
            return None
        if fernet is None:
            return self._cnic
        return fernet.decrypt(self._cnic.encode()).decode()

    @cnic.setter
    def cnic(self, value: str):
        if value:
            if fernet is None:
                self._cnic = value
            else:
                self._cnic = fernet.encrypt(value.encode()).decode()
        else:
            self._cnic = None

    @property
    def age(self) -> int:
        if not self.dob:
            return None
        today = datetime.date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

    def __repr__(self) -> str:
        return f"<Person id={self.id} name={self.first_name} {self.last_name}>"
