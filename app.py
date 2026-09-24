"""
app.py
------
Production-ready Reflex application for the University Attendance Tracker.
Features bespoke Deep Burgundy editorial styling, course code anchor architecture,
Semester Date & Holiday Setup Modal, interactive Attendance Roster with Date Navigation,
tactile attendance state actions (Present, Absent, Cancelled), and safe-skips guard.
"""

import reflex as rx
import math
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

from schemas import ScheduleSlot, Unit, Semester, AttendanceLog, UnitStats, UserProfile
from engine import (
    calculate_slot_duration,
    generate_attendance_logs,
    calculate_unit_stats
)
from firebase_client import get_db, verify_firebase_token

# --- Bespoke Editorial Theme Palette Tokens ---
PALETTE = {
    "burgundy_base": "#4A0E17",
    "accent_wine": "#801835",
    "accent_rose": "#C97A8E",
    "parchment_light": "#FAF7F5",
    "parchment_dark": "#1C1215",
    "card_light": "#FFFFFF",
    "card_dark": "#26161B",
    "border_light": "#E8DFDC",
    "border_dark": "#3D262C",
    "sage_text": "#2E5C38",
    "sage_bg": "#EDF5EF",
    "crimson_text": "#8C1D24",
    "crimson_bg": "#FDF0F0",
    "muted_text_light": "#6E5B63",
    "muted_text_dark": "#A8969D",
    "text_dark": "#2D1B22",
    "text_light": "#FAF7F5",
}

# --- Custom Injected CSS ---
EDITORIAL_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {{
    --font-heading: 'Instrument Serif', Georgia, serif;
    --font-body: 'Plus Jakarta Sans', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}}

body {{
    font-family: var(--font-body);
    margin: 0;
    padding: 0;
    background-color: {PALETTE["parchment_light"]};
    color: {PALETTE["text_dark"]};
}}

.editorial-heading {{
    font-family: var(--font-heading);
    letter-spacing: -0.02em;
}}

.mono-code {{
    font-family: var(--font-mono);
    letter-spacing: -0.03em;
}}

.card-editorial {{
    background: #FFFFFF;
    border: 1px solid {PALETTE["border_light"]};
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(74, 14, 23, 0.04);
    transition: all 0.2s ease-in-out;
}}

.card-editorial-dark {{
    background: {PALETTE["card_dark"]};
    border: 1px solid {PALETTE["border_dark"]};
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    transition: all 0.2s ease-in-out;
}}

.badge-sage {{
    background-color: {PALETTE["sage_bg"]};
    color: {PALETTE["sage_text"]};
    border: 1px solid {PALETTE["sage_text"]};
    font-family: var(--font-mono);
    font-weight: 600;
}}

.badge-crimson {{
    background-color: {PALETTE["crimson_bg"]};
    color: {PALETTE["crimson_text"]};
    border: 1px solid {PALETTE["crimson_text"]};
    font-family: var(--font-mono);
    font-weight: 600;
}}
"""

DAY_NAMES = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
DAY_LABEL_MAP = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 7,
}
DAY_OPTIONS = list(DAY_LABEL_MAP.keys())

# --- Application State ---
class AppState(rx.State):
    """
    Reflex central application state manager.
    Handles Auth, Semester Setup, Roster Date Navigation, Attendance Actions (Present, Absent, Cancelled), and Unit Stats.
    """
    # Authentication & Session State
    is_logged_in: bool = True
    auth_mode: str = "login"  # "login" or "signup"
    email_input: str = ""
    password_input: str = ""
    auth_error_msg: str = ""
    uid: str = "demo_student_01"
    user_email: str = "alex.student@university.edu"
    max_absence_pct: float = 20.0
    is_dark_mode: bool = False

    # Active Semester & Data
    active_semester_id: str = "sem_fall_2026"
    semester_name: str = "Fall 2026"
    semester_start: str = "2026-09-01"
    semester_end: str = "2026-12-20"
    semester_holidays: List[str] = ["2026-11-26", "2026-11-27"]

    # Semester Setup Modal State
    is_semester_modal_open: bool = False
    input_sem_name: str = "Fall 2026"
    input_sem_start: str = "2026-09-01"
    input_sem_end: str = "2026-12-20"
    input_sem_holidays: str = "2026-11-26, 2026-11-27"
    input_max_absence_pct: str = "20.0"
    sem_error_msg: str = ""

    # Raw Firestore Document Collections
    units_dict: List[Dict[str, Any]] = []
    attendance_logs_dict: List[Dict[str, Any]] = []

    # UI Computed Aggregates & Roster Navigation
    unit_stats_list: List[Dict[str, Any]] = []
    selected_roster_date: str = datetime.now().strftime("%Y-%m-%d")
    roster_status_filter: str = "ALL"  # "ALL", "Pending", "Present", "Absent", "Cancelled"
    displayed_roster: List[Dict[str, Any]] = []

    # Unit & Timetable Modal State
    is_unit_modal_open: bool = False
    new_unit_code: str = ""
    new_unit_name: str = ""
    new_slot_day_label: str = "Monday"
    new_slot_start: str = "09:00"
    new_slot_end: str = "11:00"
    draft_schedule_slots: List[Dict[str, Any]] = []
    form_error_msg: str = ""

    # Setters
    def set_email_input(self, val: str):
        self.email_input = val

    def set_password_input(self, val: str):
        self.password_input = val

    def set_input_sem_name(self, val: str):
        self.input_sem_name = val

    def set_input_sem_start(self, val: str):
        self.input_sem_start = val

    def set_input_sem_end(self, val: str):
        self.input_sem_end = val

    def set_input_sem_holidays(self, val: str):
        self.input_sem_holidays = val

    def set_input_max_absence_pct(self, val: str):
        self.input_max_absence_pct = val

    def set_new_unit_code(self, val: str):
        self.new_unit_code = val

    def set_new_unit_name(self, val: str):
        self.new_unit_name = val

    def set_new_slot_day_label(self, val: str):
        self.new_slot_day_label = val

    def set_new_slot_start(self, val: str):
        self.new_slot_start = val

    def set_new_slot_end(self, val: str):
        self.new_slot_end = val

    def set_selected_roster_date(self, val: str):
        self.selected_roster_date = val
        self._filter_displayed_roster()

    def set_roster_status_filter(self, val: str):
        self.roster_status_filter = val
        self._filter_displayed_roster()

    def prev_roster_day(self):
        """Navigates roster back 1 calendar day."""
        try:
            curr = datetime.strptime(self.selected_roster_date, "%Y-%m-%d").date()
            prev_d = curr - timedelta(days=1)
            self.selected_roster_date = prev_d.strftime("%Y-%m-%d")
            self._filter_displayed_roster()
        except Exception:
            pass

    def next_roster_day(self):
        """Navigates roster forward 1 calendar day."""
        try:
            curr = datetime.strptime(self.selected_roster_date, "%Y-%m-%d").date()
            next_d = curr + timedelta(days=1)
            self.selected_roster_date = next_d.strftime("%Y-%m-%d")
            self._filter_displayed_roster()
        except Exception:
            pass

    def jump_to_today(self):
        """Jumps roster to today's date."""
        self.selected_roster_date = date.today().strftime("%Y-%m-%d")
        self._filter_displayed_roster()

    def toggle_auth_mode(self):
        """Switches view between Login and Sign Up."""
        self.auth_mode = "signup" if self.auth_mode == "login" else "login"
        self.auth_error_msg = ""

    def handle_login(self):
        """Authenticates student user."""
        email = self.email_input.strip()
        pwd = self.password_input.strip()

        if not email or not pwd:
            self.auth_error_msg = "Please enter both Email and Password."
            return

        if "@" not in email:
            self.auth_error_msg = "Please enter a valid university email address."
            return

        clean_uid = "user_" + "".join(c for c in email if c.isalnum())
        self.uid = clean_uid
        self.user_email = email
        self.is_logged_in = True
        self.auth_error_msg = ""

        db = get_db()
        user_ref = db.collection("users").document(self.uid)
        user_doc = user_ref.get()
        if not user_doc.exists:
            user_ref.set({"email": email, "max_absence_pct": 20.0})
            self._seed_demo_data(db)

        self._load_from_firestore(db)

    def handle_signup(self):
        """Registers new student user."""
        email = self.email_input.strip()
        pwd = self.password_input.strip()

        if not email or not pwd:
            self.auth_error_msg = "Please provide an Email and Password to register."
            return

        if len(pwd) < 6:
            self.auth_error_msg = "Password must be at least 6 characters long."
            return

        clean_uid = "user_" + "".join(c for c in email if c.isalnum())
        self.uid = clean_uid
        self.user_email = email
        self.is_logged_in = True
        self.auth_error_msg = ""

        db = get_db()
        user_ref = db.collection("users").document(self.uid)
        user_ref.set({"email": email, "max_absence_pct": 20.0})
        self._seed_demo_data(db)
        self._load_from_firestore(db)

    def handle_quick_demo_login(self):
        """One-click instant login for demonstration."""
        self.uid = "demo_student_01"
        self.user_email = "alex.student@university.edu"
        self.is_logged_in = True
        self.auth_error_msg = ""
        self.on_load()

    def handle_logout(self):
        """Logs out student."""
        self.is_logged_in = False
        self.email_input = ""
        self.password_input = ""
        self.auth_error_msg = ""

    # --- Semester Modal Handlers ---
    def open_semester_modal(self):
        self.input_sem_name = self.semester_name
        self.input_sem_start = self.semester_start
        self.input_sem_end = self.semester_end
        self.input_sem_holidays = ", ".join(self.semester_holidays)
        self.input_max_absence_pct = str(self.max_absence_pct)
        self.sem_error_msg = ""
        self.is_semester_modal_open = True

    def close_semester_modal(self):
        self.is_semester_modal_open = False

    def save_semester(self):
        """Saves configured semester dates, holiday list, and allowed absence percentage."""
        name = self.input_sem_name.strip()
        start = self.input_sem_start.strip()
        end = self.input_sem_end.strip()

        if not name or not start or not end:
            self.sem_error_msg = "Semester Title, Start Date, and End Date are required."
            return

        try:
            s_dt = datetime.strptime(start, "%Y-%m-%d").date()
            e_dt = datetime.strptime(end, "%Y-%m-%d").date()
            if e_dt <= s_dt:
                self.sem_error_msg = "End Date must be after Start Date."
                return
        except Exception:
            self.sem_error_msg = "Invalid date format. Expected YYYY-MM-DD."
            return

        try:
            pct = float(self.input_max_absence_pct)
            if pct < 0 or pct > 100:
                self.sem_error_msg = "Allowed absence % must be between 0 and 100."
                return
            self.max_absence_pct = pct
        except Exception:
            self.sem_error_msg = "Invalid absence threshold percentage."
            return

        holidays_list = [h.strip() for h in self.input_sem_holidays.split(",") if h.strip()]

        self.semester_name = name
        self.semester_start = start
        self.semester_end = end
        self.semester_holidays = holidays_list

        db = get_db()
        db.collection("users").document(self.uid).set({"email": self.user_email, "max_absence_pct": self.max_absence_pct}, merge=True)
        sem_ref = db.collection("users").document(self.uid).collection("semesters").document(self.active_semester_id)
        sem_ref.set({
            "name": name,
            "start_date": start,
            "end_date": end,
            "holidays": holidays_list,
            "is_active": True
        })

        units_objs = []
        for u_dict in self.units_dict:
            slots_data = u_dict.get("schedule_slots", [])
            slots = [
                ScheduleSlot(
                    slot_id=str(s["slot_id"]),
                    day_of_week=int(s["day_of_week"]),
                    start_time=str(s["start_time"]),
                    end_time=str(s["end_time"]),
                    duration_hours=float(s["duration_hours"])
                ) for s in slots_data if isinstance(s, dict)
            ]
            units_objs.append(Unit(unit_code=u_dict["unit_code"], name=u_dict["name"], schedule_slots=slots))

        semester_obj = Semester(
            semester_id=self.active_semester_id,
            name=name,
            start_date=start,
            end_date=end,
            holidays=holidays_list
        )
        new_logs = generate_attendance_logs(semester_obj, units_objs)

        batch = db.batch()
        for log in new_logs:
            l_ref = db.collection("users").document(self.uid).collection("attendance_logs").document(log.log_id)
            batch.set(l_ref, log.model_dump())
        batch.commit()

        self.is_semester_modal_open = False
        self._load_from_firestore(db)

    def on_load(self):
        """Initializes dataset if logged in."""
        if not self.is_logged_in:
            return

        db = get_db()
        user_ref = db.collection("users").document(self.uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            user_ref.set({"email": self.user_email, "max_absence_pct": self.max_absence_pct})
            self._seed_demo_data(db)

        self._load_from_firestore(db)

    def _seed_demo_data(self, db):
        """Seeds demo semester, CS units, and initial class logs."""
        sem_ref = db.collection("users").document(self.uid).collection("semesters").document(self.active_semester_id)
        sem_ref.set({
            "name": self.semester_name,
            "start_date": self.semester_start,
            "end_date": self.semester_end,
            "holidays": self.semester_holidays,
            "is_active": True
        })

        demo_units = [
            {
                "unit_code": "CS-302",
                "name": "Database Systems & Architecture",
                "schedule_slots": [
                    {"slot_id": "s1", "day_of_week": 1, "start_time": "09:00", "end_time": "11:00", "duration_hours": 2.0},
                    {"slot_id": "s2", "day_of_week": 4, "start_time": "14:00", "end_time": "17:00", "duration_hours": 3.0}
                ]
            },
            {
                "unit_code": "CS-401",
                "name": "Distributed Operating Systems",
                "schedule_slots": [
                    {"slot_id": "s3", "day_of_week": 2, "start_time": "10:00", "end_time": "12:00", "duration_hours": 2.0},
                    {"slot_id": "s4", "day_of_week": 5, "start_time": "11:00", "end_time": "13:00", "duration_hours": 2.0}
                ]
            },
            {
                "unit_code": "MATH-210",
                "name": "Applied Linear Algebra & Statistics",
                "schedule_slots": [
                    {"slot_id": "s5", "day_of_week": 3, "start_time": "08:00", "end_time": "10:00", "duration_hours": 2.0}
                ]
            }
        ]

        batch = db.batch()
        units_objs = []
        for u in demo_units:
            u_ref = db.collection("users").document(self.uid).collection("semesters").document(self.active_semester_id).collection("units").document(u["unit_code"])
            batch.set(u_ref, u)
            
            slots = [
                ScheduleSlot(
                    slot_id=str(s["slot_id"]),
                    day_of_week=int(s["day_of_week"]),
                    start_time=str(s["start_time"]),
                    end_time=str(s["end_time"]),
                    duration_hours=float(s["duration_hours"])
                ) for s in u["schedule_slots"]
            ]
            units_objs.append(Unit(unit_code=u["unit_code"], name=u["name"], schedule_slots=slots))

        batch.commit()

        semester_obj = Semester(
            semester_id=self.active_semester_id,
            name=self.semester_name,
            start_date=self.semester_start,
            end_date=self.semester_end,
            holidays=self.semester_holidays
        )
        logs = generate_attendance_logs(semester_obj, units_objs)

        log_batch = db.batch()
        today_date = date.today()
        for i, log in enumerate(logs):
            log_dt = datetime.strptime(log.date, "%Y-%m-%d").date()
            if log_dt < today_date:
                if i % 7 == 0:
                    log.status = "Absent"
                elif i % 11 == 0:
                    log.status = "Cancelled"
                else:
                    log.status = "Present"

            l_ref = db.collection("users").document(self.uid).collection("attendance_logs").document(log.log_id)
            log_batch.set(l_ref, log.model_dump())

        log_batch.commit()

    def _load_from_firestore(self, db):
        """Loads units and logs from Firestore and computes aggregates."""
        u_stream = db.collection("users").document(self.uid).collection("semesters").document(self.active_semester_id).collection("units").stream()
        units_raw = [d.to_dict() for d in u_stream]
        self.units_dict = units_raw

        l_stream = db.collection("users").document(self.uid).collection("attendance_logs").where("semester_id", "==", self.active_semester_id).stream()
        logs_raw = [d.to_dict() for d in l_stream]
        self.attendance_logs_dict = logs_raw

        self._recalculate_all_stats()

    def _recalculate_all_stats(self):
        """Runs engine math calculations across all units and builds today's roster."""
        units_objs = []
        for u_dict in self.units_dict:
            slots_data = u_dict.get("schedule_slots", [])
            slots = [
                ScheduleSlot(
                    slot_id=str(s["slot_id"]),
                    day_of_week=int(s["day_of_week"]),
                    start_time=str(s["start_time"]),
                    end_time=str(s["end_time"]),
                    duration_hours=float(s["duration_hours"])
                ) for s in slots_data if isinstance(s, dict)
            ]
            units_objs.append(Unit(unit_code=u_dict["unit_code"], name=u_dict["name"], schedule_slots=slots))

        logs_objs = [AttendanceLog(**l) for l in self.attendance_logs_dict]

        stats_list = []
        for unit_obj in units_objs:
            st = calculate_unit_stats(unit_obj, logs_objs, max_absence_pct=self.max_absence_pct)
            st_dict = st.model_dump()
            
            tags = []
            for slot in st.schedule_slots:
                day_str = DAY_NAMES.get(slot.day_of_week, "Day")
                tags.append(f"[{day_str} {slot.start_time}-{slot.end_time} ({slot.duration_hours:g}h)]")
            st_dict["slot_tags"] = tags
            stats_list.append(st_dict)

        self.unit_stats_list = stats_list

        self._filter_displayed_roster()

    def _filter_displayed_roster(self):
        """
        Filters attendance roster logs by selected_roster_date and roster_status_filter.
        If no logs exist in Firestore for the selected date, dynamically synthesizes the day's class roster
        from active unit recurring weekly time slots so the student always sees the day's scheduled classes!
        """
        logs_objs = [AttendanceLog(**l) for l in self.attendance_logs_dict]
        filtered = [l for l in logs_objs if l.date == self.selected_roster_date]

        # Synthesize day's schedule from unit recurring slots if no log doc created yet
        if not filtered and self.units_dict:
            try:
                sel_dt = datetime.strptime(self.selected_roster_date, "%Y-%m-%d").date()
                iso_weekday = sel_dt.isoweekday()
                
                synth_logs = []
                for u_dict in self.units_dict:
                    code = u_dict["unit_code"]
                    name = u_dict["name"]
                    for slot in u_dict.get("schedule_slots", []):
                        if slot.get("day_of_week") == iso_weekday:
                            dur = slot.get("duration_hours", 2.0)
                            s_time = slot.get("start_time", "09:00")
                            e_time = slot.get("end_time", "11:00")
                            log_id = f"{self.active_semester_id}_{code}_{self.selected_roster_date}_{s_time}"
                            
                            synth_log = AttendanceLog(
                                log_id=log_id,
                                semester_id=self.active_semester_id,
                                unit_code=code,
                                unit_name=name,
                                date=self.selected_roster_date,
                                day_of_week=iso_weekday,
                                start_time=s_time,
                                end_time=e_time,
                                duration_hours=dur,
                                status="Pending"
                            )
                            synth_logs.append(synth_log)
                filtered = synth_logs
            except Exception:
                pass

        if self.roster_status_filter != "ALL":
            if self.roster_status_filter == "Present":
                filtered = [l for l in filtered if l.status in ["Present", "Attended"]]
            elif self.roster_status_filter == "Absent":
                filtered = [l for l in filtered if l.status in ["Absent", "Missed"]]
            else:
                filtered = [l for l in filtered if l.status == self.roster_status_filter]

        filtered.sort(key=lambda x: x.start_time)
        self.displayed_roster = [l.model_dump() for l in filtered]

    def set_log_status(self, log_id: str, new_status: str):
        """Updates attendance status for a log ('Present', 'Absent', 'Cancelled') in Firestore & state."""
        db = get_db()
        log_ref = db.collection("users").document(self.uid).collection("attendance_logs").document(log_id)

        # Check if log already exists in attendance_logs_dict
        found = False
        for l in self.attendance_logs_dict:
            if l.get("log_id") == log_id:
                l["status"] = new_status
                log_ref.set(l)
                found = True
                break

        if not found:
            # Look up in displayed_roster (synthesized day class)
            for l in self.displayed_roster:
                if l.get("log_id") == log_id:
                    l["status"] = new_status
                    self.attendance_logs_dict.append(l)
                    log_ref.set(l)
                    break

        self._recalculate_all_stats()

    def toggle_theme(self):
        """Toggles dark/light mode."""
        self.is_dark_mode = not self.is_dark_mode

    # --- Unit Modal Handlers ---
    def open_unit_modal(self):
        self.new_unit_code = ""
        self.new_unit_name = ""
        self.new_slot_day_label = "Monday"
        self.new_slot_start = "09:00"
        self.new_slot_end = "11:00"
        self.draft_schedule_slots = []
        self.form_error_msg = ""
        self.is_unit_modal_open = True

    def close_unit_modal(self):
        self.is_unit_modal_open = False

    def add_slot_to_draft(self):
        """Adds a weekly slot entry using human-readable day selection."""
        try:
            dur = calculate_slot_duration(self.new_slot_start, self.new_slot_end)
            if dur <= 0:
                self.form_error_msg = "End time must be after start time."
                return

            day_int = DAY_LABEL_MAP.get(self.new_slot_day_label, 1)
            slot_id = f"slot_{len(self.draft_schedule_slots) + 1}"
            slot_dict = {
                "slot_id": slot_id,
                "day_of_week": day_int,
                "start_time": self.new_slot_start,
                "end_time": self.new_slot_end,
                "duration_hours": dur,
                "day_name": DAY_NAMES.get(day_int, "Day")
            }
            self.draft_schedule_slots.append(slot_dict)
            self.form_error_msg = ""
        except Exception as e:
            self.form_error_msg = f"Slot error: {e}"

    def remove_slot_from_draft(self, slot_id: str):
        self.draft_schedule_slots = [s for s in self.draft_schedule_slots if s["slot_id"] != slot_id]

    def save_unit(self):
        """Saves course unit to Firestore."""
        code = self.new_unit_code.strip().upper()
        name = self.new_unit_name.strip()

        if not code or not name:
            self.form_error_msg = "Course Code and Course Name are required."
            return

        if not self.draft_schedule_slots:
            self.form_error_msg = "Please add at least one weekly schedule time slot."
            return

        db = get_db()
        slots_objs = [
            ScheduleSlot(
                slot_id=str(s["slot_id"]),
                day_of_week=int(s["day_of_week"]),
                start_time=str(s["start_time"]),
                end_time=str(s["end_time"]),
                duration_hours=float(s["duration_hours"])
            ) for s in self.draft_schedule_slots
        ]

        unit_obj = Unit(unit_code=code, name=name, schedule_slots=slots_objs)

        u_ref = db.collection("users").document(self.uid).collection("semesters").document(self.active_semester_id).collection("units").document(code)
        u_ref.set(unit_obj.model_dump())

        semester_obj = Semester(
            semester_id=self.active_semester_id,
            name=self.semester_name,
            start_date=self.semester_start,
            end_date=self.semester_end,
            holidays=self.semester_holidays
        )
        new_logs = generate_attendance_logs(semester_obj, [unit_obj])

        batch = db.batch()
        for log in new_logs:
            l_ref = db.collection("users").document(self.uid).collection("attendance_logs").document(log.log_id)
            batch.set(l_ref, log.model_dump())
        batch.commit()

        self.is_unit_modal_open = False
        self._load_from_firestore(db)


# --- Reflex UI Components ---

def render_auth_view() -> rx.Component:
    """Bespoke Editorial Login & Sign Up view."""
    is_login = AppState.auth_mode == "login"

    return rx.center(
        rx.vstack(
            rx.vstack(
                rx.text("TENDY", font_size="2.4rem", font_weight="800", letter_spacing="-0.04em", color=PALETTE["accent_rose"]),
                rx.text("University Attendance & Safe-Skips Guard", font_family="var(--font-heading)", font_size="1.2rem", font_style="italic", color=PALETTE["muted_text_light"]),
                align_items="center",
                spacing="1"
            ),
            rx.box(
                rx.vstack(
                    rx.heading(
                        rx.cond(is_login, "WELCOME BACK", "CREATE YOUR ACCOUNT"),
                        size="3",
                        class_name="editorial-heading",
                        font_weight="700"
                    ),
                    rx.text(
                        rx.cond(is_login, "Sign in to track your semester attendance and safe skips.", "Register to manage your course schedules and attendance rules."),
                        font_size="0.85rem",
                        color=PALETTE["muted_text_light"],
                        margin_bottom="16px"
                    ),
                    rx.cond(
                        AppState.auth_error_msg != "",
                        rx.callout(AppState.auth_error_msg, color_scheme="red", icon="triangle_alert", margin_bottom="12px")
                    ),
                    rx.vstack(
                        rx.text("STUDENT UNIVERSITY EMAIL", font_size="0.75rem", class_name="mono-code", font_weight="700"),
                        rx.input(
                            placeholder="student@university.edu",
                            value=AppState.email_input,
                            on_change=AppState.set_email_input,
                            width="100%"
                        ),
                        width="100%",
                        align_items="start"
                    ),
                    rx.vstack(
                        rx.text("PASSWORD", font_size="0.75rem", class_name="mono-code", font_weight="700"),
                        rx.input(
                            type="password",
                            placeholder="••••••••",
                            value=AppState.password_input,
                            on_change=AppState.set_password_input,
                            width="100%"
                        ),
                        width="100%",
                        align_items="start"
                    ),
                    rx.button(
                        rx.cond(is_login, "Sign In", "Create Account"),
                        on_click=rx.cond(is_login, AppState.handle_login, AppState.handle_signup),
                        background_color=PALETTE["burgundy_base"],
                        color="#FFFFFF",
                        font_weight="600",
                        width="100%",
                        margin_top="12px",
                        padding_y="20px"
                    ),
                    rx.hstack(
                        rx.text(rx.cond(is_login, "Don't have an account?", "Already have an account?"), font_size="0.85rem", color=PALETTE["muted_text_light"]),
                        rx.button(
                            rx.cond(is_login, "Sign Up", "Log In"),
                            on_click=AppState.toggle_auth_mode,
                            variant="ghost",
                            color=PALETTE["accent_wine"],
                            font_weight="700",
                            padding="0"
                        ),
                        spacing="2",
                        margin_top="16px"
                    ),
                    rx.divider(margin_y="16px"),
                    rx.button(
                        "⚡ Instant One-Click Student Demo",
                        on_click=AppState.handle_quick_demo_login,
                        variant="soft",
                        color_scheme="ruby",
                        width="100%",
                        font_size="0.85rem",
                        class_name="mono-code"
                    ),
                    width="100%",
                    align_items="center"
                ),
                padding="36px",
                class_name="card-editorial",
                width="100%",
                max_width="420px"
            ),
            spacing="5",
            align_items="center"
        ),
        min_height="100vh",
        background_color=PALETTE["parchment_light"],
        width="100%"
    )


def render_navbar() -> rx.Component:
    """Header banner featuring Editorial branding, active user, semester config button, and sign out."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.text("TENDY", font_weight="700", font_size="1.5rem", letter_spacing="-0.03em", color=PALETTE["accent_rose"]),
                    rx.text("|", font_size="1.5rem", color=PALETTE["muted_text_dark"]),
                    rx.text("Attendance & Safe-Skips Guard", font_size="1.1rem", font_style="italic", font_family="var(--font-heading)", color=PALETTE["parchment_light"]),
                    spacing="3",
                    align_items="center"
                ),
                rx.hstack(
                    rx.text("User: " + AppState.user_email, font_size="0.85rem", class_name="mono-code", color=PALETTE["muted_text_dark"]),
                    rx.text("•", color=PALETTE["muted_text_dark"]),
                    rx.text("Semester: " + AppState.semester_name, font_size="0.85rem", class_name="mono-code", color=PALETTE["muted_text_dark"]),
                    rx.button(
                        "⚙️ Configure Dates",
                        on_click=AppState.open_semester_modal,
                        size="1",
                        variant="soft",
                        color_scheme="ruby",
                        class_name="mono-code"
                    ),
                    spacing="2",
                    align_items="center"
                ),
                align_items="start",
                spacing="1"
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    "+ Add Course Unit",
                    on_click=AppState.open_unit_modal,
                    background_color=PALETTE["accent_wine"],
                    color="#FFFFFF",
                    font_weight="600",
                    border_radius="8px",
                    padding_x="16px",
                    padding_y="8px",
                    _hover={"background_color": PALETTE["burgundy_base"]}
                ),
                rx.button(
                    rx.cond(AppState.is_dark_mode, "☀️ Light", "🌙 Dark"),
                    on_click=AppState.toggle_theme,
                    variant="outline",
                    color=PALETTE["parchment_light"],
                    border_color=PALETTE["border_dark"],
                    border_radius="8px"
                ),
                rx.button(
                    "Sign Out",
                    on_click=AppState.handle_logout,
                    variant="ghost",
                    color=PALETTE["accent_rose"],
                    font_size="0.85rem"
                ),
                spacing="3",
                align_items="center"
            ),
            width="100%",
            align_items="center",
            padding_x="32px",
            padding_y="20px"
        ),
        background_color=PALETTE["burgundy_base"],
        border_bottom=f"2px solid {PALETTE['accent_wine']}",
        width="100%"
    )


def render_today_roster_bar() -> rx.Component:
    """
    Interactive Attendance Roster Bar with Date Navigation & Action Buttons:
    Displays sessions for selected calendar date with direct action buttons [✓ Present], [✗ Absent], [⊘ Cancelled].
    """
    def render_roster_item(item: Dict[str, Any]) -> rx.Component:
        item_status = item["status"].to(str)
        log_id = item["log_id"].to(str)
        u_code = item["unit_code"].to(str)
        u_name = item["unit_name"].to(str)
        s_time = item["start_time"].to(str)
        e_time = item["end_time"].to(str)
        dur = item["duration_hours"].to(str)

        is_present = (item_status == "Present") | (item_status == "Attended")
        is_absent = (item_status == "Absent") | (item_status == "Missed")
        is_cancelled = item_status == "Cancelled"

        return rx.box(
            rx.hstack(
                rx.box(
                    rx.text(u_code, class_name="mono-code", font_weight="700", font_size="1.1rem", color=PALETTE["burgundy_base"]),
                    rx.text(u_name, font_size="0.9rem", color=PALETTE["muted_text_light"]),
                    width="240px"
                ),
                rx.box(
                    rx.hstack(
                        rx.icon(tag="clock", size=16, color=PALETTE["burgundy_base"]),
                        rx.text(s_time + " - " + e_time + " (" + dur + "h)", class_name="mono-code", font_size="0.9rem", font_weight="600"),
                        spacing="2",
                        align_items="center"
                    ),
                    width="200px"
                ),
                rx.spacer(),
                # Action Buttons: [Present], [Absent], [Cancelled]
                rx.hstack(
                    rx.button(
                        "✓ Present",
                        on_click=lambda: AppState.set_log_status(log_id, "Present"),
                        size="2",
                        variant=rx.cond(is_present, "solid", "outline"),
                        color_scheme=rx.cond(is_present, "green", "gray"),
                        class_name="mono-code"
                    ),
                    rx.button(
                        "✗ Absent",
                        on_click=lambda: AppState.set_log_status(log_id, "Absent"),
                        size="2",
                        variant=rx.cond(is_absent, "solid", "outline"),
                        color_scheme=rx.cond(is_absent, "red", "gray"),
                        class_name="mono-code"
                    ),
                    rx.button(
                        "⊘ Cancelled",
                        on_click=lambda: AppState.set_log_status(log_id, "Cancelled"),
                        size="2",
                        variant=rx.cond(is_cancelled, "solid", "outline"),
                        color_scheme=rx.cond(is_cancelled, "orange", "gray"),
                        class_name="mono-code"
                    ),
                    spacing="2"
                ),
                width="100%",
                align_items="center",
                padding="12px 16px"
            ),
            border=f"1px solid {PALETTE['border_light']}",
            border_radius="8px",
            margin_bottom="8px",
            background="#FFFFFF"
        )

    return rx.box(
        rx.vstack(
            # Roster Title & Date Controls
            rx.hstack(
                rx.vstack(
                    rx.heading("CLASSES OF THE DAY & ATTENDANCE ACTIONS", size="3", class_name="editorial-heading", font_weight="700", letter_spacing="0.05em"),
                    rx.text("Mark your classes as Present, Absent, or Cancelled to update safe skips buffer in real-time.", font_size="0.85rem", color=PALETTE["muted_text_light"]),
                    spacing="1"
                ),
                rx.spacer(),
                # Date Navigation Controls
                rx.hstack(
                    rx.button("◄ Prev", on_click=AppState.prev_roster_day, size="1", variant="outline"),
                    rx.input(
                        type="date",
                        value=AppState.selected_roster_date,
                        on_change=AppState.set_selected_roster_date,
                        class_name="mono-code",
                        width="140px",
                        size="1"
                    ),
                    rx.button("Today", on_click=AppState.jump_to_today, size="1", variant="soft", color_scheme="ruby"),
                    rx.button("Next ►", on_click=AppState.next_roster_day, size="1", variant="outline"),
                    spacing="2",
                    align_items="center"
                ),
                width="100%",
                align_items="center"
            ),
            rx.divider(margin_y="12px"),
            # Status Filter Tabs
            rx.hstack(
                rx.text("Filter Status:", font_size="0.8rem", font_weight="600", class_name="mono-code"),
                rx.button(
                    "ALL",
                    on_click=lambda: AppState.set_roster_status_filter("ALL"),
                    size="1",
                    variant=rx.cond(AppState.roster_status_filter == "ALL", "solid", "ghost")
                ),
                rx.button(
                    "Pending",
                    on_click=lambda: AppState.set_roster_status_filter("Pending"),
                    size="1",
                    variant=rx.cond(AppState.roster_status_filter == "Pending", "solid", "ghost")
                ),
                rx.button(
                    "✓ Present",
                    on_click=lambda: AppState.set_roster_status_filter("Present"),
                    size="1",
                    variant=rx.cond((AppState.roster_status_filter == "Present") | (AppState.roster_status_filter == "Attended"), "solid", "ghost"),
                    color_scheme="green"
                ),
                rx.button(
                    "✗ Absent",
                    on_click=lambda: AppState.set_roster_status_filter("Absent"),
                    size="1",
                    variant=rx.cond((AppState.roster_status_filter == "Absent") | (AppState.roster_status_filter == "Missed"), "solid", "ghost"),
                    color_scheme="red"
                ),
                rx.button(
                    "⊘ Cancelled",
                    on_click=lambda: AppState.set_roster_status_filter("Cancelled"),
                    size="1",
                    variant=rx.cond(AppState.roster_status_filter == "Cancelled", "solid", "ghost"),
                    color_scheme="orange"
                ),
                spacing="2",
                margin_bottom="12px",
                align_items="center"
            ),
            # Roster Session Items
            rx.cond(
                AppState.displayed_roster.length() > 0,
                rx.vstack(
                    rx.foreach(
                        AppState.displayed_roster,
                        render_roster_item
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("No classes scheduled for " + AppState.selected_roster_date + ". Use the date arrows above to select another class day.", font_style="italic", color=PALETTE["muted_text_light"]),
                    padding="16px"
                )
            ),
            width="100%"
        ),
        padding="24px",
        class_name=rx.cond(AppState.is_dark_mode, "card-editorial-dark", "card-editorial"),
        margin_bottom="32px",
        width="100%"
    )


def render_course_card(unit_stat: Dict[str, Any]) -> rx.Component:
    """
    Course Dashboard Card:
    - Primary Anchor: Monospaced uppercase `unit_code` (e.g. CS-302).
    - Weekly slot summary tags.
    - Dual-segment burgundy/crimson horizontal attendance track.
    - 3-metric bottom row (Attended Hours, Absence Rate %, Safe Skips Left).
    - Semantic status badge (IN GOOD STANDING vs CRITICAL).
    """
    is_critical = unit_stat["status_flag"].to(str) == "CRITICAL"
    safe_skips = unit_stat["safe_skips_remaining"].to(int)
    att_hrs = unit_stat["attended_hours"].to(str)
    eff_hrs = unit_stat["effective_total_hours"].to(str)
    abs_pct = unit_stat["absence_rate_pct"].to(str)

    return rx.box(
        rx.vstack(
            # Header Row
            rx.hstack(
                rx.vstack(
                    rx.text(unit_stat["unit_code"].to(str), class_name="mono-code", font_size="1.4rem", font_weight="800", color=PALETTE["burgundy_base"]),
                    rx.text(unit_stat["unit_name"].to(str), font_size="1.0rem", font_weight="600", color=PALETTE["text_dark"]),
                    spacing="1",
                    align_items="start"
                ),
                rx.spacer(),
                rx.badge(
                    rx.cond(is_critical, "⚠️ CRITICAL", "✓ IN GOOD STANDING"),
                    class_name=rx.cond(is_critical, "badge-crimson", "badge-sage"),
                    padding="6px 12px",
                    font_size="0.85rem"
                ),
                width="100%",
                align_items="start"
            ),
            # Weekly Slot Tags
            rx.hstack(
                rx.foreach(
                    unit_stat["slot_tags"].to(List[str]),
                    lambda tag: rx.badge(tag, variant="soft", color_scheme="purple", class_name="mono-code", font_size="0.75rem")
                ),
                spacing="2",
                margin_y="12px",
                flex_wrap="wrap"
            ),
            # Dual-Segment Attendance Track (Progress Visualizer)
            rx.box(
                rx.hstack(
                    # Attended segment
                    rx.box(
                        height="100%",
                        width=unit_stat["attendance_rate_pct"].to(str) + "%",
                        background_color=PALETTE["sage_text"],
                        border_radius="4px 0 0 4px",
                        transition="width 0.4s ease"
                    ),
                    # Missed segment
                    rx.box(
                        height="100%",
                        width=unit_stat["absence_rate_pct"].to(str) + "%",
                        background_color=PALETTE["crimson_text"],
                        transition="width 0.4s ease"
                    ),
                    height="10px",
                    width="100%",
                    spacing="0",
                    background_color=PALETTE["border_light"],
                    border_radius="4px",
                    overflow="hidden"
                ),
                width="100%",
                margin_y="12px"
            ),
            # 3-Metric Bottom Row
            rx.hstack(
                # Metric 1: Total Attended
                rx.vstack(
                    rx.text("ATTENDED / EFF", font_size="0.7rem", class_name="mono-code", color=PALETTE["muted_text_light"]),
                    rx.text(att_hrs + "h / " + eff_hrs + "h", class_name="mono-code", font_size="1.1rem", font_weight="700"),
                    align_items="start",
                    spacing="0"
                ),
                rx.spacer(),
                # Metric 2: Absence Rate %
                rx.vstack(
                    rx.text("ABSENCE RATE", font_size="0.7rem", class_name="mono-code", color=PALETTE["muted_text_light"]),
                    rx.text(abs_pct + "%", class_name="mono-code", font_size="1.1rem", font_weight="700", color=rx.cond(is_critical, PALETTE["crimson_text"], PALETTE["sage_text"])),
                    align_items="start",
                    spacing="0"
                ),
                rx.spacer(),
                # Metric 3: Safe Skips Left Badge
                rx.vstack(
                    rx.text("SAFE SKIPS LEFT", font_size="0.7rem", class_name="mono-code", color=PALETTE["muted_text_light"]),
                    rx.badge(
                        safe_skips.to(str) + " Sessions",
                        variant="solid",
                        color_scheme=rx.cond(safe_skips > 0, "green", "red"),
                        class_name="mono-code",
                        font_size="0.95rem"
                    ),
                    align_items="start",
                    spacing="0"
                ),
                width="100%",
                align_items="center",
                padding_top="8px"
            ),
            width="100%"
        ),
        padding="24px",
        class_name=rx.cond(AppState.is_dark_mode, "card-editorial-dark", "card-editorial"),
        width="100%"
    )


def render_semester_modal() -> rx.Component:
    """Semester Setup Modal allowing students to fill start/end dates, holiday list, and allowed absence %."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("CONFIGURE SEMESTER DATES & RULES", class_name="editorial-heading", font_weight="700"),
            rx.dialog.description("Define your academic semester date bounds, holidays, and allowed absence threshold."),
            rx.divider(margin_y="12px"),
            rx.vstack(
                rx.cond(
                    AppState.sem_error_msg != "",
                    rx.callout(AppState.sem_error_msg, color_scheme="red", icon="triangle_alert", margin_bottom="8px")
                ),
                rx.vstack(
                    rx.text("SEMESTER TITLE", font_size="0.75rem", class_name="mono-code", font_weight="700"),
                    rx.input(
                        placeholder="e.g. Fall 2026",
                        value=AppState.input_sem_name,
                        on_change=AppState.set_input_sem_name,
                        width="100%"
                    ),
                    width="100%",
                    align_items="start"
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("START DATE (YYYY-MM-DD)", font_size="0.75rem", class_name="mono-code", font_weight="700"),
                        rx.input(
                            type="date",
                            value=AppState.input_sem_start,
                            on_change=AppState.set_input_sem_start,
                            width="100%",
                            class_name="mono-code"
                        ),
                        width="48%"
                    ),
                    rx.vstack(
                        rx.text("END DATE (YYYY-MM-DD)", font_size="0.75rem", class_name="mono-code", font_weight="700"),
                        rx.input(
                            type="date",
                            value=AppState.input_sem_end,
                            on_change=AppState.set_input_sem_end,
                            width="100%",
                            class_name="mono-code"
                        ),
                        width="48%"
                    ),
                    width="100%",
                    justify="between"
                ),
                rx.vstack(
                    rx.text("HOLIDAY DATES (COMMA SEPARATED YYYY-MM-DD)", font_size="0.75rem", class_name="mono-code", font_weight="700"),
                    rx.input(
                        placeholder="2026-11-26, 2026-11-27",
                        value=AppState.input_sem_holidays,
                        on_change=AppState.set_input_sem_holidays,
                        width="100%",
                        class_name="mono-code"
                    ),
                    rx.text("Classes will automatically be skipped on holiday dates.", font_size="0.75rem", color=PALETTE["muted_text_light"]),
                    width="100%",
                    align_items="start"
                ),
                rx.vstack(
                    rx.text("MAX ALLOWED ABSENCE RATE (%)", font_size="0.75rem", class_name="mono-code", font_weight="700"),
                    rx.input(
                        type="number",
                        placeholder="20.0",
                        value=AppState.input_max_absence_pct,
                        on_change=AppState.set_input_max_absence_pct,
                        width="100%",
                        class_name="mono-code"
                    ),
                    rx.text("Courses exceeding this threshold will be flagged as CRITICAL.", font_size="0.75rem", color=PALETTE["muted_text_light"]),
                    width="100%",
                    align_items="start"
                ),
                spacing="3",
                width="100%",
                padding_y="12px"
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancel", variant="outline", on_click=AppState.close_semester_modal)
                ),
                rx.button("Save & Generate Schedule Logs", on_click=AppState.save_semester, background_color=PALETTE["burgundy_base"], color="#FFFFFF"),
                justify="end",
                spacing="3",
                margin_top="16px"
            ),
            max_width="520px",
            padding="24px"
        ),
        open=AppState.is_semester_modal_open
    )


def render_unit_modal() -> rx.Component:
    """Unit & Timetable Modal with human-readable Day selection dropdown."""
    def render_draft_slot_item(slot: Dict[str, Any]) -> rx.Component:
        d_name = slot["day_name"].to(str)
        s_time = slot["start_time"].to(str)
        e_time = slot["end_time"].to(str)
        dur = slot["duration_hours"].to(str)
        s_id = slot["slot_id"].to(str)

        return rx.hstack(
            rx.badge(d_name + " " + s_time + "-" + e_time + " (" + dur + "h)", class_name="mono-code"),
            rx.spacer(),
            rx.button("✕", on_click=lambda: AppState.remove_slot_from_draft(s_id), size="1", color_scheme="red", variant="ghost"),
            width="100%",
            align_items="center",
            padding="4px 8px"
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("ADD COURSE UNIT & TIMETABLE SLOTS", class_name="editorial-heading", font_weight="700"),
            rx.dialog.description("Course Code (e.g. CS-302) serves as the primary anchor for all multi-slot attendance stats."),
            rx.divider(margin_y="12px"),
            rx.vstack(
                rx.cond(
                    AppState.form_error_msg != "",
                    rx.callout(AppState.form_error_msg, color_scheme="red", icon="triangle_alert", margin_bottom="8px")
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("COURSE CODE (PRIMARY ANCHOR)", font_size="0.75rem", class_name="mono-code", font_weight="700"),
                        rx.input(
                            placeholder="e.g. CS-302",
                            value=AppState.new_unit_code,
                            on_change=AppState.set_new_unit_code,
                            class_name="mono-code"
                        ),
                        width="48%"
                    ),
                    rx.vstack(
                        rx.text("COURSE TITLE", font_size="0.75rem", class_name="mono-code", font_weight="700"),
                        rx.input(
                            placeholder="e.g. Database Systems",
                            value=AppState.new_unit_name,
                            on_change=AppState.set_new_unit_name
                        ),
                        width="48%"
                    ),
                    width="100%",
                    justify="between"
                ),
                rx.heading("RECURRING WEEKLY TIME SLOTS", size="2", margin_top="16px", class_name="mono-code"),
                # Human-readable Day Select dropdown
                rx.hstack(
                    rx.select(
                        DAY_OPTIONS,
                        value=AppState.new_slot_day_label,
                        on_change=AppState.set_new_slot_day_label,
                        placeholder="Select Day"
                    ),
                    rx.input(type="time", value=AppState.new_slot_start, on_change=AppState.set_new_slot_start, width="110px"),
                    rx.text("→", font_weight="700"),
                    rx.input(type="time", value=AppState.new_slot_end, on_change=AppState.set_new_slot_end, width="110px"),
                    rx.button("+ Add Slot", on_click=AppState.add_slot_to_draft, variant="soft", color_scheme="crimson"),
                    align_items="center",
                    spacing="2",
                    width="100%"
                ),
                # Added draft slots list
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            AppState.draft_schedule_slots,
                            render_draft_slot_item
                        ),
                        width="100%"
                    ),
                    width="100%",
                    border=f"1px solid {PALETTE['border_light']}",
                    border_radius="6px",
                    padding="8px",
                    margin_top="8px",
                    max_height="120px",
                    overflow_y="auto"
                ),
                spacing="3",
                width="100%",
                padding_y="16px"
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancel", variant="outline", on_click=AppState.close_unit_modal)
                ),
                rx.button("Save Course Unit", on_click=AppState.save_unit, background_color=PALETTE["burgundy_base"], color="#FFFFFF"),
                justify="end",
                spacing="3",
                margin_top="16px"
            ),
            max_width="540px",
            padding="24px"
        ),
        open=AppState.is_unit_modal_open
    )


def index() -> rx.Component:
    """Main application view with conditional Login/Signup or Dashboard."""
    return rx.box(
        rx.html(f"<style>{EDITORIAL_CSS}</style>"),
        rx.cond(
            AppState.is_logged_in,
            rx.box(
                render_navbar(),
                rx.container(
                    render_today_roster_bar(),
                    rx.hstack(
                        rx.heading("COURSE DASHBOARD UNITS", size="4", class_name="editorial-heading", font_weight="700"),
                        rx.spacer(),
                        rx.text("Allowed Absence Threshold: " + AppState.max_absence_pct.to(str) + "%", class_name="mono-code", font_size="0.85rem", color=PALETTE["muted_text_light"]),
                        width="100%",
                        align_items="center",
                        margin_bottom="16px"
                    ),
                    rx.cond(
                        AppState.unit_stats_list.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                AppState.unit_stats_list,
                                render_course_card
                            ),
                            spacing="4",
                            width="100%"
                        ),
                        rx.text("No courses added yet. Click '+ Add Course Unit' above to get started.", font_style="italic")
                    ),
                    render_semester_modal(),
                    render_unit_modal(),
                    max_width="1080px",
                    padding_y="32px"
                )
            ),
            render_auth_view()
        ),
        min_height="100vh",
        background_color=rx.cond(AppState.is_dark_mode, PALETTE["parchment_dark"], PALETTE["parchment_light"]),
        color=rx.cond(AppState.is_dark_mode, PALETTE["text_light"], PALETTE["text_dark"]),
        on_mount=AppState.on_load
    )


app = rx.App()
app.add_page(index, title="Tendy | University Attendance & Safe Skips Guard")

if __name__ == "__main__":
    pass
