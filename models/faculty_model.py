from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey, Boolean, DateTime, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
import datetime
from models.base_model import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .designation_model import Designation
    from .tracks_model import Track
    from .track_level import TrackLevel
    from .department_model import Department
    from .school_model import School
    from .person_model import Person
    from .faculty_track_assignment_model import FacultyTrackAssignment
    from .faculty_contract_model import FacultyContract
    from .faculty_transfer_model import FacultyTransfer
    from .faculty_course_history_model import FacultyCourseHistory


class FacultyRole(str, Enum):
    ADMIN = "admin"
    HR = "hr"
    FACULTY = "faculty"


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # Faculty code/ID
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    university_email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)

    designation_id: Mapped[int] = mapped_column(ForeignKey("designation.id", ondelete="SET NULL"), nullable=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("track.id", ondelete="SET NULL"), nullable=True)
    track_level_id: Mapped[int] = mapped_column(ForeignKey("track_level.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("department.id", ondelete="SET NULL"), nullable=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("school.id", ondelete="SET NULL"), nullable=True)
    date_of_joining: Mapped[str] = mapped_column(String(20), nullable=False)

    # Authentication fields (merged User functionality)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=True)
    role: Mapped[FacultyRole] = mapped_column(SqlEnum(FacultyRole, name="facultyrole"), nullable=True)
    last_login: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    token: Mapped[str] = mapped_column(String(512), nullable=True)  # OAuth/JWT/Session token

    # 🔗 Relationships
    person: Mapped["Person"] = relationship(back_populates="faculty")
    designation: Mapped["Designation"] = relationship(back_populates="faculties")
    track: Mapped["Track"] = relationship(back_populates="faculties")
    track_level: Mapped["TrackLevel"] = relationship(back_populates="faculties")

    department: Mapped["Department"] = relationship(back_populates="faculties")
    school: Mapped["School"] = relationship(back_populates="faculties")

    contracts: Mapped[list["FacultyContract"]] = relationship(
        "FacultyContract", back_populates="faculty", cascade="all, delete-orphan"
    )
    transfers: Mapped[list["FacultyTransfer"]] = relationship(
        "FacultyTransfer", back_populates="faculty", foreign_keys="[FacultyTransfer.faculty_id]"
    )
    course_history: Mapped[list["FacultyCourseHistory"]] = relationship(
        "FacultyCourseHistory", back_populates="faculty", cascade="all, delete-orphan"
    )
    track_assignments: Mapped[list["FacultyTrackAssignment"]] = relationship(
        back_populates="faculty", cascade="all, delete-orphan", foreign_keys="[FacultyTrackAssignment.faculty_id]"
    )

    # Faculty approvals and recommendations
    approved_transfers: Mapped[list["FacultyTransfer"]] = relationship(
        foreign_keys="FacultyTransfer.approved_by",
        primaryjoin="Faculty.id == FacultyTransfer.approved_by"
    )
    approved_track_assignments: Mapped[list["FacultyTrackAssignment"]] = relationship(
        foreign_keys="FacultyTrackAssignment.approved_by",
        primaryjoin="Faculty.id == FacultyTrackAssignment.approved_by"
    )
    recommended_track_assignments: Mapped[list["FacultyTrackAssignment"]] = relationship(
        foreign_keys="FacultyTrackAssignment.recommended_by",
        primaryjoin="Faculty.id == FacultyTrackAssignment.recommended_by"
    )

    def __repr__(self) -> str:
        return (
            f"<Faculty id={self.id} code='{self.code}' username='{self.username}' "
            f"title='{self.title}' role='{self.role}'>"
        )

    # -------------------
    # User-like utilities
    # -------------------
    @property
    def is_user(self) -> bool:
        """Check if faculty is also a system user"""
        return self.is_active

    def validate_user_fields(self) -> tuple[bool, str]:
        """Validate required fields if faculty is an active system user."""
        if not self.is_active:
            return True, ""

        if not self.username:
            return False, "Username is required for active faculty users"
        if not self.password_hash and not self.token:
            return False, "Either password or token is required for active faculty users"
        if not self.role:
            return False, "Role is required for active faculty users"
        return True, ""

    def activate_user(self, username: str, password_hash: str | None, role: str, token: str | None = None) -> None:
        """Activate faculty as a system user (with password or OAuth token)."""
        self.username = username
        self.password_hash = password_hash
        self.token = token
        self.role = role
        self.is_active = True

    def deactivate_user(self) -> None:
        """Deactivate faculty as a system user but keep user data."""
        self.is_active = False
