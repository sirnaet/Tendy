"""
test_all_modules.py
-------------------
Comprehensive verification suite testing firebase_client, schemas, engine, and database interactions.
"""

import sys
import math
from datetime import date
from firebase_client import get_db, verify_firebase_token, MemoryStore
from schemas import ScheduleSlot, Unit, Semester, AttendanceLog, UnitStats, UserProfile
from engine import (
    calculate_slot_duration,
    generate_attendance_logs,
    calculate_unit_stats
)

def test_firebase_client_and_auth():
    print("[1/3] Testing firebase_client & token verification...")
    db = get_db()
    assert db is not None

    uid = "test_user_99"

    user_ref = db.collection("users").document(uid)
    user_ref.set({"email": "test@university.edu", "max_absence_pct": 20.0})
    
    doc = user_ref.get()
    assert doc.exists
    assert doc.to_dict()["email"] == "test@university.edu"
    print("      ✓ firebase_client tests passed.")

def test_demo_token_is_rejected():
    for token in ("demo_token_test_user_99", "not-a-firebase-token"):
        try:
            verify_firebase_token(token)
        except ValueError:
            continue
        raise AssertionError("Unverified tokens must not authenticate users")

def test_schemas_validation():
    print("[2/3] Testing Pydantic v2 schemas...")
    slot = ScheduleSlot(slot_id="s1", day_of_week=1, start_time="09:00", end_time="11:30", duration_hours=2.5)
    assert slot.duration_hours == 2.5

    # Case normalization check for unit_code
    unit = Unit(unit_code=" cs-302 ", name="Database Systems", schedule_slots=[slot])
    assert unit.unit_code == "CS-302"

    sem = Semester(
        semester_id="sem_1",
        name="Fall 2026",
        start_date="2026-09-01",
        end_date="2026-12-20",
        holidays=["2026-11-26"]
    )
    assert sem.is_active is True
    print("      ✓ schemas tests passed.")

def test_engine_math_rules():
    print("[3/3] Testing engine calculations & holiday skipping...")
    # 2.0h slot on Mon (1), 3.0h slot on Thu (4)
    s1 = ScheduleSlot(slot_id="s1", day_of_week=1, start_time="09:00", end_time="11:00", duration_hours=2.0)
    s2 = ScheduleSlot(slot_id="s2", day_of_week=4, start_time="14:00", end_time="17:00", duration_hours=3.0)

    unit = Unit(unit_code="CS-302", name="Database Systems", schedule_slots=[s1, s2])

    # 1 week semester: Mon 2026-10-05 to Sun 2026-10-11
    # Oct 5 (Mon, 2h)
    # Oct 8 (Thu, 3h)
    sem = Semester(
        semester_id="sem_test",
        name="Test Week",
        start_date="2026-10-05",
        end_date="2026-10-11",
        holidays=[]
    )

    logs = generate_attendance_logs(sem, [unit])
    assert len(logs) == 2
    assert logs[0].log_id == "sem_test_CS-302_2026-10-05_09:00"
    assert logs[1].log_id == "sem_test_CS-302_2026-10-08_14:00"

    # Initial Stats (0 attended, 0 missed, 0 cancelled)
    # H_total = 5.0, H_eff = 5.0
    # Max missable = 20% of 5.0 = 1.0h. Avg slot duration = 2.5h.
    # Safe skips = floor(1.0 / 2.5) = 0.
    stats = calculate_unit_stats(unit, logs, max_absence_pct=20.0)
    assert stats.total_scheduled_hours == 5.0
    assert stats.effective_total_hours == 5.0
    assert stats.absence_rate_pct == 0.0
    assert stats.safe_skips_remaining == 0
    assert stats.status_flag == "OKAY"

    # Cancel Thursday slot (3.0h cancelled)
    logs[1].status = "Cancelled"
    stats_cancelled = calculate_unit_stats(unit, logs, max_absence_pct=20.0)
    # H_total = 5.0, H_cancelled = 3.0, H_eff = max(5.0 - 3.0, 1.0) = 2.0h
    assert stats_cancelled.cancelled_hours == 3.0
    assert stats_cancelled.effective_total_hours == 2.0

    # Mark Monday slot as Missed (2.0h missed out of 2.0h H_eff)
    logs[0].status = "Missed"
    stats_critical = calculate_unit_stats(unit, logs, max_absence_pct=20.0)
    # Absence rate = (2.0 / 2.0) * 100 = 100.0% > 20.0% -> CRITICAL
    assert stats_critical.absence_rate_pct == 100.0
    assert stats_critical.status_flag == "CRITICAL"

    print("      ✓ engine math tests passed.")

if __name__ == "__main__":
    print("\n--- RUNNING SYSTEM-WIDE TEST SUITE FOR UNIVERSITY ATTENDANCE TRACKER ---")
    test_firebase_client_and_auth()
    test_demo_token_is_rejected()
    test_schemas_validation()
    test_engine_math_rules()
    print("-------------------------------------------------------------------------")
    print("ALL SYSTEM TESTS PASSED SUCCESSFULLY WITH ZERO ERRORS!")
