from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from models.person_model import Base

class DesignationType(enum.Enum):
    academic = "academic"
    administrative = "administrative"

class Designation(Base):
    __tablename__ = "designation"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    type = Column(Enum(DesignationType), nullable=False)
    description = Column(Text)
    
    def __repr__(self):
        return f"Designation(id={self.id}, title={self.title}, type={self.type})"
