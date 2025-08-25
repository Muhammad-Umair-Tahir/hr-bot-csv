from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Enum, Text, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class Person(Base):
    __tablename__ = "person"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    father_husband_name = Column(String(100))
    sex = Column(String(20))
    dob = Column(Date)
    cnic = Column(String(20), unique=True)
    cnic_expiry = Column(Date)
    phone = Column(String(20))
    email = Column(String(100))
    blood_group = Column(String(10))
    marital_status = Column(String(20))
    date_of_marriage = Column(Date)
    no_of_dependents = Column(Integer, default=0)
    
    # Relationships
    faculty = relationship("Faculty", back_populates="person", uselist=False)
    qualifications = relationship("Qualification", back_populates="person")

    def __repr__(self):
        return f"Person(id={self.id}, name={self.first_name} {self.last_name})"
