from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, time

class SemesterBase(BaseModel):
    start_date: date
    end_date: date
    holidays: List[date] = []
    allowed_absence_percent: float = 20.0

class SemesterCreate(SemesterBase):
    pass

class Semester(SemesterBase):
    id: str

class UnitSlot(BaseModel):
    day_of_week: int = Field(..., ge=1, le=7, description="1=Monday, 7=Sunday")
    start_time: time
    end_time: time

class UnitBase(BaseModel):
    name: str
    code: str
    slots: List[UnitSlot]

class UnitCreate(UnitBase):
    pass

class Unit(UnitBase):
    id: str

class ClassLogBase(BaseModel):
    unit_id: str
    date: date
    start_time: time
    end_time: time
    duration_hours: float
    status: str = Field(default="Pending", description="Pending, Attended, Missed, Cancelled")

class ClassLogCreate(ClassLogBase):
    pass

class ClassLog(ClassLogBase):
    id: str

class SemesterGenerateRequest(BaseModel):
    semester: SemesterCreate
    units: List[UnitCreate]
