"""
schemas.py
----------
Pydantic v2 data models for Cloud Firestore database structure,
mathematical engine inputs/outputs, and UI state representations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional
from datetime import datetime

class ScheduleSlot(BaseModel):
    """
    Represents a recurring weekly time slot for a unit session.
    """
    slot_id: str = Field(..., description="Unique slot identifier within the unit")
    day_of_week: int = Field(..., ge=1, le=7, description="ISO weekday: 1=Monday, 7=Sunday")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Start time in HH:MM format")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="End time in HH:MM format")
    duration_hours: float = Field(..., ge=0.0, description="Session duration in hours")


class Unit(BaseModel):
    """
    Course / Unit entity anchored by unique uppercase `unit_code`.
    Collection path: users/{uid}/semesters/{semester_id}/units/{unit_code}
    """
    unit_code: str = Field(..., description="Uppercase course code (Document ID), e.g. CS-302")
    name: str = Field(..., description="Full course name, e.g. Database Systems")
    schedule_slots: List[ScheduleSlot] = Field(default_factory=list, description="Weekly recurring time slots")

    @field_validator("unit_code")
    @classmethod
    def validate_unit_code(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("unit_code cannot be empty")
        return cleaned


class Semester(BaseModel):
    """
    Semester entity containing date bounds and holiday schedule.
    Collection path: users/{uid}/semesters/{semester_id}
    """
    semester_id: str = Field(..., description="Unique semester identifier")
    name: str = Field(..., description="Semester name, e.g. Fall 2026")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date YYYY-MM-DD")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date YYYY-MM-DD")
    holidays: List[str] = Field(default_factory=list, description="List of holiday dates YYYY-MM-DD")
    is_active: bool = Field(default=True, description="Whether this semester is currently active")


class AttendanceLog(BaseModel):
    """
    Individual generated class session log.
    Collection path: users/{uid}/attendance_logs/{log_id}
    log_id format: {semester_id}_{unit_code}_{date}_{start_time}
    """
    log_id: str = Field(..., description="Deterministic log identifier")
    semester_id: str = Field(..., description="Referenced semester ID")
    unit_code: str = Field(..., description="Referenced uppercase course code")
    unit_name: str = Field(..., description="Course name snippet")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Class date YYYY-MM-DD")
    day_of_week: int = Field(..., ge=1, le=7, description="ISO weekday: 1=Monday, 7=Sunday")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Start time HH:MM")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="End time HH:MM")
    duration_hours: float = Field(..., ge=0.0, description="Class duration in hours")
    status: Literal["Pending", "Attended", "Missed", "Cancelled", "Present", "Absent"] = Field(
        default="Pending",
        description="Attendance status"
    )

    @field_validator("unit_code")
    @classmethod
    def uppercase_unit_code(cls, v: str) -> str:
        return v.strip().upper()


class UnitStats(BaseModel):
    """
    Aggregated unit-level statistics computed by engine.py across all weekly slots and logs.
    """
    unit_code: str
    unit_name: str
    total_scheduled_hours: float = Field(..., description="H_total")
    cancelled_hours: float = Field(..., description="H_cancelled")
    effective_total_hours: float = Field(..., description="H_eff")
    attended_hours: float = Field(..., description="H_attended")
    missed_hours: float = Field(..., description="H_missed")
    attendance_rate_pct: float = Field(..., description="Attended / H_eff * 100")
    absence_rate_pct: float = Field(..., description="Missed / H_eff * 100")
    safe_skips_remaining: int = Field(..., description="Floor of remaining missable hours buffer / avg slot duration")
    status_flag: Literal["OKAY", "CRITICAL"] = Field(..., description="CRITICAL if absence_rate_pct > max_absence_pct else OKAY")
    schedule_slots: List[ScheduleSlot] = Field(default_factory=list)


class UserProfile(BaseModel):
    """
    User profile metadata stored at users/{uid}
    """
    email: str
    max_absence_pct: float = Field(default=20.0, ge=0.0, le=100.0)
    updated_at: Optional[str] = None
