from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime
from models.person_model import Base

class Qualification(Base):
    __tablename__ = "qualification"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person.id"), nullable=False)
    degree = Column(String(100))
    field_of_study = Column(String(100))
    institution = Column(String(200))
    country = Column(String(100))
    year_completed = Column(Integer)
    
    # Relationships
    person = relationship("Person", back_populates="qualification")
    
    def __repr__(self):
        return f"Qualification(id={self.id}, degree={self.degree}, institution={self.institution})"
