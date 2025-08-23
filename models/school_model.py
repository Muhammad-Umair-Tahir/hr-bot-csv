from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime
from models.person_model import Base

class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True)
    description = Column(Text)
    
    departments = relationship("Department", backref="school")
    
    def __repr__(self):
        return f"School(id={self.id}, name={self.name})"
