from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime
from models.person_model import Base

class Track(Base):
    __tablename__ = "track"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    def __repr__(self):
        return f"Track(id={self.id}, name={self.name})"
