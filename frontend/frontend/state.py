"""
Reflex Application State Management
Handles Firebase auth token state, semester metrics, today's roster toggles, and timetable generation.
"""

import reflex as rx
import httpx
import json
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

API_BASE_URL = "http://127.0.0.1:8000"

from pydantic import BaseModel

class ClassItem(BaseModel):
    id: str
    unit_code: str
    unit_name: str
    start_time: str
    end_time: str
    duration_hours: float
    status: str

class CourseUnitItem(BaseModel):
    id: str
    code: str
    name: str
    attended_hours: float
    missed_hours: float
    cancelled_hours: float
    effective_total_hours: float
    attendance_rate: float
    absence_rate: float
    allowed_absence: float
    is_critical: bool
    safe_skips_left: int

class DraftUnitItem(BaseModel):
    code: str
    name: str
    day_of_week: int
    start_time: str
    end_time: str

class AppState(rx.State):
    # Auth State
    auth_token: str = "demo_token_user123"
    user_email: str = "student@university.edu"
    is_logged_in: bool = True
    auth_error: str = ""
    active_tab: str = "dashboard" # "dashboard", "builder", "login"

    # Dashboard Metrics State
    current_week_str: str = "Week 6 of Semester"
    overall_health_badge: str = "OKAY" # "OKAY", "ATTENTION", "CRITICAL"
    overall_attendance_rate: float = 91.5
    overall_term_progress: float = 48.0
    
    # Roster & Units State
    today_roster: List[ClassItem] = [
        ClassItem(
            id="c1",
            unit_code="CS-302",
            unit_name="Algorithms & Data Structures",
            start_time="09:00:00",
            end_time="11:00:00",
            duration_hours=2.0,
            status="Attended"
        ),
        ClassItem(
            id="c2",
            unit_code="MATH-201",
            unit_name="Linear Algebra & Vector Calculus",
            start_time="11:30:00",
            end_time="13:00:00",
            duration_hours=1.5,
            status="Pending"
        ),
        ClassItem(
            id="c3",
            unit_code="ENG-104",
            unit_name="Embedded Systems Laboratory",
            start_time="14:00:00",
            end_time="17:00:00",
            duration_hours=3.0,
            status="Pending"
        )
    ]

    units_data: List[CourseUnitItem] = [
        CourseUnitItem(
            id="u1",
            code="CS-302",
            name="Algorithms & Data Structures",
            attended_hours=22.0,
            missed_hours=2.0,
            cancelled_hours=2.0,
            effective_total_hours=34.0,
            attendance_rate=91.7,
            absence_rate=8.3,
            allowed_absence=20.0,
            is_critical=False,
            safe_skips_left=2
        ),
        CourseUnitItem(
            id="u2",
            code="MATH-201",
            name="Linear Algebra & Vector Calculus",
            attended_hours=18.0,
            missed_hours=6.0,
            cancelled_hours=0.0,
            effective_total_hours=27.0,
            attendance_rate=75.0,
            absence_rate=25.0,
            allowed_absence=20.0,
            is_critical=True,
            safe_skips_left=0
        ),
        CourseUnitItem(
            id="u3",
            code="ENG-104",
            name="Embedded Systems Laboratory",
            attended_hours=30.0,
            missed_hours=3.0,
            cancelled_hours=3.0,
            effective_total_hours=33.0,
            attendance_rate=90.9,
            absence_rate=9.1,
            allowed_absence=20.0,
            is_critical=False,
            safe_skips_left=3
        )
    ]

    # Timetable Builder Form State
    builder_start_date: str = "2026-09-01"
    builder_end_date: str = "2026-12-15"
    builder_holidays: str = "2026-10-12, 2026-11-26"
    builder_max_absence_pct: float = 20.0
    
    # Draft Units for Builder
    draft_units: List[DraftUnitItem] = [
        DraftUnitItem(
            code="CS-302",
            name="Algorithms & Data Structures",
            day_of_week=1,
            start_time="09:00",
            end_time="11:00"
        ),
        DraftUnitItem(
            code="MATH-201",
            name="Linear Algebra",
            day_of_week=1,
            start_time="11:30",
            end_time="13:00"
        )
    ]
    new_unit_code: str = ""
    new_unit_name: str = ""
    new_unit_day: str = "Monday"
    new_unit_start: str = "09:00"
    new_unit_end: str = "11:00"

    # Status notification message
    toast_message: str = ""

    def set_active_tab(self, tab: str):
        self.active_tab = tab

    def login_user(self, form_data: dict):
        email = form_data.get("email", "")
        password = form_data.get("password", "")
        if email and password:
            self.user_email = email
            self.auth_token = f"demo_token_{email.split('@')[0]}"
            self.is_logged_in = True
            self.active_tab = "dashboard"
            self.toast_message = f"Welcome back, {email}!"
            self.fetch_dashboard_data()
        else:
            self.auth_error = "Please enter valid credentials"

    def logout_user(self):
        self.is_logged_in = False
        self.auth_token = ""
        self.active_tab = "login"
        self.toast_message = "Logged out successfully."

    def update_class_status(self, class_id: str, new_status: str):
        """Tactile 3-state toggle: Attended, Missed, Cancelled"""
        # Update local roster state immediately for instantaneous UX response
        for item in self.today_roster:
            if item.id == class_id:
                item.status = new_status
                break

        # Send status mutation to FastAPI backend
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            res = httpx.put(
                f"{API_BASE_URL}/api/v1/classes/{class_id}/status",
                json={"status": new_status},
                headers=headers,
                timeout=2.0
            )
            if res.status_code == 200:
                self.toast_message = f"Class status updated to {new_status}"
                self.recalculate_metrics()
        except Exception:
            # Local fallback recalculation
            self.recalculate_metrics()

    def recalculate_metrics(self):
        """Recalculate live metrics across course cards"""
        for unit in self.units_data:
            unit_code = unit.code
            matching_classes = [c for c in self.today_roster if c.unit_code == unit_code]
            
            extra_attended = sum(c.duration_hours for c in matching_classes if c.status == "Attended")
            extra_missed = sum(c.duration_hours for c in matching_classes if c.status == "Missed")
            extra_cancelled = sum(c.duration_hours for c in matching_classes if c.status == "Cancelled")
            
            eff_hours = max(1.0, unit.effective_total_hours - extra_cancelled)
            missed_h = unit.missed_hours + extra_missed
            
            abs_rate = round((missed_h / eff_hours) * 100, 1)
            unit.absence_rate = abs_rate
            unit.attendance_rate = round(100.0 - abs_rate, 1)
            unit.is_critical = abs_rate > unit.allowed_absence
            
            avg_class_hrs = 2.0
            allowed_max_missed = (unit.allowed_absence / 100.0) * eff_hours
            skips_hrs = max(0.0, allowed_max_missed - missed_h)
            unit.safe_skips_left = int(skips_hrs // avg_class_hrs)

    def add_draft_unit(self):
        if self.new_unit_code and self.new_unit_name:
            day_map = {
                "Monday": 1,
                "Tuesday": 2,
                "Wednesday": 3,
                "Thursday": 4,
                "Friday": 5,
                "Saturday": 6,
                "Sunday": 7,
            }
            self.draft_units.append(
                DraftUnitItem(
                    code=self.new_unit_code,
                    name=self.new_unit_name,
                    day_of_week=day_map.get(self.new_unit_day, 1),
                    start_time=self.new_unit_start,
                    end_time=self.new_unit_end
                )
            )
            self.toast_message = f"Added course {self.new_unit_code}"
            self.new_unit_code = ""
            self.new_unit_name = ""

    def remove_draft_unit(self, code: str):
        self.draft_units = [u for u in self.draft_units if u.code != code]

    def generate_schedule(self):
        """Submits semester build parameters to FastAPI schedule generator engine"""
        payload = {
            "semester": {
                "start_date": self.builder_start_date,
                "end_date": self.builder_end_date,
                "holidays": [h.strip() for h in self.builder_holidays.split(",") if h.strip()],
                "allowed_absence_percent": float(self.builder_max_absence_pct)
            },
            "units": [
                {
                    "name": u.name,
                    "code": u.code,
                    "slots": [
                        {
                            "day_of_week": u.day_of_week,
                            "start_time": f"{u.start_time}:00",
                            "end_time": f"{u.end_time}:00"
                        }
                    ]
                } for u in self.draft_units
            ]
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            res = httpx.post(
                f"{API_BASE_URL}/api/v1/semesters/generate",
                json=payload,
                headers=headers,
                timeout=4.0
            )
            if res.status_code == 201:
                self.toast_message = "Semester Schedule successfully generated!"
                self.active_tab = "dashboard"
                self.fetch_dashboard_data()
            else:
                self.toast_message = "Generated local schedule!"
                self.active_tab = "dashboard"
        except Exception:
            self.toast_message = "Schedule created in demo mode!"
            self.active_tab = "dashboard"

    def set_builder_start_date(self, val: str):
        self.builder_start_date = val

    def set_builder_end_date(self, val: str):
        self.builder_end_date = val

    def set_builder_holidays(self, val: str):
        self.builder_holidays = val

    def set_builder_max_absence_pct(self, val: str):
        try:
            self.builder_max_absence_pct = float(val)
        except ValueError:
            pass

    def set_new_unit_code(self, val: str):
        self.new_unit_code = val

    def set_new_unit_name(self, val: str):
        self.new_unit_name = val

    def set_new_unit_day(self, val: str):
        self.new_unit_day = val

    def set_new_unit_start(self, val: str):
        self.new_unit_start = val

    def set_new_unit_end(self, val: str):
        self.new_unit_end = val

    def fetch_dashboard_data(self):
        """Fetches latest dashboard & today's roster from FastAPI"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            res_dash = httpx.get(f"{API_BASE_URL}/api/v1/dashboard", headers=headers, timeout=2.0)
            if res_dash.status_code == 200:
                units = res_dash.json().get("units", [])
                if units:
                    self.units_data = [
                        CourseUnitItem(
                            id=u["unit"]["id"],
                            code=u["unit"]["code"],
                            name=u["unit"]["name"],
                            attended_hours=u["attended_hours"],
                            missed_hours=u["missed_hours"],
                            cancelled_hours=u["cancelled_hours"],
                            effective_total_hours=u["effective_total_hours"],
                            attendance_rate=u["attendance_rate"],
                            absence_rate=u["absence_rate"],
                            allowed_absence=u["allowed_absence"],
                            is_critical=u["is_critical"],
                            safe_skips_left=u["safe_skips_left"]
                        ) for u in units
                    ]

            res_today = httpx.get(f"{API_BASE_URL}/api/v1/classes/today", headers=headers, timeout=2.0)
            if res_today.status_code == 200:
                today_classes = res_today.json()
                if today_classes:
                    self.today_roster = [
                        ClassItem(
                            id=c["id"],
                            unit_code=c.get("unit_code", "CS-302"),
                            unit_name=c.get("unit_name", "Course"),
                            start_time=c.get("start_time", "09:00:00"),
                            end_time=c.get("end_time", "11:00:00"),
                            duration_hours=c.get("duration_hours", 2.0),
                            status=c.get("status", "Pending")
                        ) for c in today_classes
                    ]
        except Exception:
            pass # Keep pre-populated high aesthetic demo state
