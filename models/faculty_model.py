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
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    code = Column(Integer, unique=True)
    title = Column(String(100))
    university_email = Column(String(100))
    designation_id = Column(Integer, ForeignKey("designation.id"))
    track_id = Column(Integer, ForeignKey("track.id"))
    department_id = Column(Integer, ForeignKey("department.id"))
    school_id = Column(Integer, ForeignKey("school.id"))
    status = Column(String(50))
    date_of_joining = Column(Date)
    
    # Relationships
    person = relationship("Person", back_populates="faculty")
    
    def __repr__(self):
        return f"Faculty(id={self.id}, code={self.code})"
