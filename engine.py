"""
engine.py
---------
Pure Python mathematical engine for generating daily class attendance logs
and calculating aggregated unit-level statistics strictly anchored by unit_code.
"""

import math
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Set
from schemas import ScheduleSlot, Unit, Semester, AttendanceLog, UnitStats

def parse_time_to_minutes(time_str: str) -> int:
    """
    Converts a time string in "HH:MM" format to minutes past midnight.
    """
    parts = time_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: '{time_str}'. Expected 'HH:MM'")
    hours, minutes = int(parts[0]), int(parts[1])
    return hours * 60 + minutes

def calculate_slot_duration(start_time: str, end_time: str) -> float:
    """
    Computes session duration in hours from "HH:MM" start and end times.
    Formula: duration_hours = (end_time - start_time) / 60 minutes
    """
    start_mins = parse_time_to_minutes(start_time)
    end_mins = parse_time_to_minutes(end_time)
    
    diff_mins = end_mins - start_mins
    if diff_mins < 0:
        # Midnight spanning handling
        diff_mins += 24 * 60

    return round(diff_mins / 60.0, 2)

def generate_attendance_logs(semester: Semester, units: List[Unit]) -> List[AttendanceLog]:
    """
    Generates individual daily class logs from start_date through end_date.
    
    Rules:
    1. Iterate date-by-date from semester.start_date through semester.end_date.
    2. Skip any date present in semester.holidays.
    3. Match ISO weekday (1=Mon..7=Sun) against each unit's recurring schedule_slots.
    4. Persist logs with initial status="Pending" and deterministic log_id:
       {semester_id}_{unit_code}_{date}_{start_time}
    """
    start_dt = datetime.strptime(semester.start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(semester.end_date, "%Y-%m-%d").date()
    holiday_set: Set[str] = set(semester.holidays)

    logs: List[AttendanceLog] = []
    curr_dt = start_dt
    step = timedelta(days=1)

    while curr_dt <= end_dt:
        date_str = curr_dt.strftime("%Y-%m-%d")
        
        # Skip holidays
        if date_str in holiday_set:
            curr_dt += step
            continue

        iso_weekday = curr_dt.isoweekday()

        for unit in units:
            unit_code = unit.unit_code.upper()
            for slot in unit.schedule_slots:
                if slot.day_of_week == iso_weekday:
                    duration = calculate_slot_duration(slot.start_time, slot.end_time)
                    log_id = f"{semester.semester_id}_{unit_code}_{date_str}_{slot.start_time}"
                    
                    log = AttendanceLog(
                        log_id=log_id,
                        semester_id=semester.semester_id,
                        unit_code=unit_code,
                        unit_name=unit.name,
                        date=date_str,
                        day_of_week=iso_weekday,
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        duration_hours=duration,
                        status="Pending"
                    )
                    logs.append(log)

        curr_dt += step

    return logs

def calculate_unit_stats(
    unit: Unit, 
    logs: List[AttendanceLog], 
    max_absence_pct: float = 20.0
) -> UnitStats:
    """
    Computes course-level aggregated attendance statistics for a single unit_code across the semester.
    
    Formulas:
    1. H_total = sum(duration_hours of all logs for unit)
    2. H_cancelled = sum(duration_hours of logs with status == 'Cancelled')
    3. H_eff = max(H_total - H_cancelled, 1.0)
    4. H_attended = sum(duration_hours of logs with status in ['Attended', 'Present'])
    5. H_missed = sum(duration_hours of logs with status in ['Missed', 'Absent'])
    6. Absence Rate (%) = (H_missed / H_eff) * 100
    7. Max Missable Hours = (max_absence_pct / 100) * H_eff
    8. Remaining Hours Buffer = max(0.0, Max Missable Hours - H_missed)
    9. Safe Skips Remaining = floor(Remaining Hours Buffer / Avg Session Duration)
    10. Status Flag: CRITICAL if Absence Rate (%) > max_absence_pct else OKAY
    """
    unit_code = unit.unit_code.upper()
    unit_logs = [l for l in logs if l.unit_code.upper() == unit_code]

    total_scheduled_hours = sum(l.duration_hours for l in unit_logs)
    cancelled_hours = sum(l.duration_hours for l in unit_logs if l.status == "Cancelled")
    
    effective_total_hours = max(total_scheduled_hours - cancelled_hours, 1.0)
    
    attended_hours = sum(l.duration_hours for l in unit_logs if l.status in ["Attended", "Present"])
    missed_hours = sum(l.duration_hours for l in unit_logs if l.status in ["Missed", "Absent"])

    absence_rate_pct = (missed_hours / effective_total_hours) * 100.0
    attendance_rate_pct = (attended_hours / effective_total_hours) * 100.0

    if unit.schedule_slots:
        avg_session_duration = sum(s.duration_hours for s in unit.schedule_slots) / len(unit.schedule_slots)
    elif unit_logs:
        avg_session_duration = sum(l.duration_hours for l in unit_logs) / len(unit_logs)
    else:
        avg_session_duration = 1.0

    if avg_session_duration <= 0:
        avg_session_duration = 1.0

    max_missable_hours = (max_absence_pct / 100.0) * effective_total_hours
    remaining_hours_buffer = max(0.0, max_missable_hours - missed_hours)
    safe_skips_remaining = math.floor(remaining_hours_buffer / avg_session_duration)

    status_flag = "CRITICAL" if absence_rate_pct > max_absence_pct else "OKAY"

    return UnitStats(
        unit_code=unit_code,
        unit_name=unit.name,
        total_scheduled_hours=round(total_scheduled_hours, 2),
        cancelled_hours=round(cancelled_hours, 2),
        effective_total_hours=round(effective_total_hours, 2),
        attended_hours=round(attended_hours, 2),
        missed_hours=round(missed_hours, 2),
        attendance_rate_pct=round(attendance_rate_pct, 1),
        absence_rate_pct=round(absence_rate_pct, 1),
        safe_skips_remaining=safe_skips_remaining,
        status_flag=status_flag,
        schedule_slots=unit.schedule_slots
    )
