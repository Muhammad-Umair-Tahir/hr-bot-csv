from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class FacultyOut(BaseModel):
    id: int
    person_id: int
    code: Optional[int] = None
    title: Optional[str] = None
    university_email: Optional[str] = None
    designation_id: Optional[int] = None
    track_id: Optional[int] = None
    department_id: Optional[int] = None
    school_id: Optional[int] = None
    status: Optional[str] = None
    date_of_joining: Optional[date] = None
    
    class Config:
        orm_mode = True
