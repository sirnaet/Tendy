"""
test_core.py
------------
Unit test suite verifying firebase_client, schemas, and engine calculations.
"""

from firebase_client import get_db, verify_firebase_token
from schemas import ScheduleSlot, Unit, Semester, AttendanceLog, UserProfile
from engine import (
    calculate_slot_duration,
    generate_attendance_logs,
    calculate_unit_stats
)

def test_duration_calculation():
    assert calculate_slot_duration("09:00", "11:00") == 2.0
    assert calculate_slot_duration("14:00", "17:00") == 3.0
    assert calculate_slot_duration("08:30", "10:15") == 1.75
    print("✓ test_duration_calculation passed")

def test_attendance_generation_and_stats():
    slot1 = ScheduleSlot(slot_id="slot_1", day_of_week=1, start_time="09:00", end_time="11:00", duration_hours=2.0) # Mon 2h
    slot2 = ScheduleSlot(slot_id="slot_2", day_of_week=4, start_time="14:00", end_time="17:00", duration_hours=3.0) # Thu 3h

    unit = Unit(
        unit_code="cs-302", # Should normalize to CS-302
        name="Database Systems",
        schedule_slots=[slot1, slot2]
    )
    assert unit.unit_code == "CS-302"

    # Semester: 2 weeks (2026-10-05 Mon to 2026-10-18 Sun)
    # Mondays: Oct 5, Oct 12 (2 logs of 2h = 4h)
    # Thursdays: Oct 8, Oct 15 (2 logs of 3h = 6h)
    # Total scheduled: 10h
    semester = Semester(
        semester_id="sem_fall2026",
        name="Fall 2026",
        start_date="2026-10-05",
        end_date="2026-10-18",
        holidays=["2026-10-12"], # Oct 12 Monday is a holiday!
        is_active=True
    )

    logs = generate_attendance_logs(semester, [unit])
    # Expect: Oct 5 (Mon, 2h), Oct 8 (Thu, 3h), Oct 15 (Thu, 3h). Total 3 logs.
    assert len(logs) == 3
    assert logs[0].date == "2026-10-05"
    assert logs[0].duration_hours == 2.0
    assert logs[1].date == "2026-10-08"
    assert logs[1].duration_hours == 3.0
    assert logs[2].date == "2026-10-15"
    assert logs[2].duration_hours == 3.0

    # Initial stats (all pending)
    stats = calculate_unit_stats(unit, logs, max_absence_pct=20.0)
    assert stats.total_scheduled_hours == 8.0 # (2h + 3h + 3h, since Oct 12 was holiday)
    assert stats.effective_total_hours == 8.0
    assert stats.absence_rate_pct == 0.0
    assert stats.status_flag == "OKAY"
    # Max missable hours = 20% of 8h = 1.6h. Avg session duration = (2+3)/2 = 2.5h.
    # Safe skips = floor(1.6 / 2.5) = 0 skips.
    assert stats.safe_skips_remaining == 0

    # Mark 1 session missed (3h missed on Oct 8)
    logs[1].status = "Missed"
    stats_missed = calculate_unit_stats(unit, logs, max_absence_pct=20.0)
    # Absence rate = 3 / 8 = 37.5% > 20% -> CRITICAL
    assert stats_missed.absence_rate_pct == 37.5
    assert stats_missed.status_flag == "CRITICAL"

    print("✓ test_attendance_generation_and_stats passed")

def test_firebase_memory_client():
    db = get_db()
    uid = "test_user_123"

    user_ref = db.collection("users").document(uid)
    user_ref.set({"email": "student@uni.edu", "max_absence_pct": 20.0})

    doc = user_ref.get()
    assert doc.exists
    assert doc.to_dict()["email"] == "student@uni.edu"
    print("✓ test_firebase_memory_client passed")

def test_demo_token_is_rejected():
    for token in ("demo_token_user_123", "not-a-firebase-token"):
        try:
            verify_firebase_token(token)
        except ValueError:
            continue
        raise AssertionError("Unverified tokens must not authenticate users")

if __name__ == "__main__":
    test_duration_calculation()
    test_attendance_generation_and_stats()
    test_firebase_memory_client()
    test_demo_token_is_rejected()
    print("ALL CORE TESTS PASSED SUCCESSFULLY!")
