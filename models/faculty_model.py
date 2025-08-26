from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime
from models.person_model import Base

class Faculty(Base):
    __tablename__ = "faculty"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person.id"), nullable=False)
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
