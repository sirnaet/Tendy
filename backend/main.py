from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta, datetime
import uuid
import math
from dotenv import load_dotenv

from models import (
    SemesterGenerateRequest,
    Semester,
    Unit,
    ClassLog
)
from auth import get_current_user_uid
from database import init_firebase, get_db

load_dotenv()
init_firebase()

app = FastAPI(title="Attendance Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_firestore_db():
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized (missing credentials)")
    return db

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/v1/semesters/generate", status_code=status.HTTP_201_CREATED)
def generate_semester(
    req: SemesterGenerateRequest,
    uid: str = Depends(get_current_user_uid),
    db = Depends(get_firestore_db)
):
    """
    Generates the class schedule for the semester.
    Saves semester, units, and generated class logs to Firestore.
    """
    # 1. Create Semester ID
    semester_id = str(uuid.uuid4())
    semester_data = req.semester.model_dump()
    semester_data['id'] = semester_id
    
    # Batch write is preferred for atomic operations
    batch = db.batch()
    
    semester_ref = db.collection("users").document(uid).collection("semesters").document(semester_id)
    # Convert dates to strings for Firestore compatibility
    fs_semester_data = {
        "id": semester_id,
        "start_date": req.semester.start_date.isoformat(),
        "end_date": req.semester.end_date.isoformat(),
        "holidays": [h.isoformat() for h in req.semester.holidays],
        "allowed_absence_percent": req.semester.allowed_absence_percent
    }
    batch.set(semester_ref, fs_semester_data)
    
    # 2. Setup Units
    unit_expected_hours = {}
    saved_units = []
    
    for unit_in in req.units:
        unit_id = str(uuid.uuid4())
        unit_expected_hours[unit_id] = 0.0
        
        fs_unit_data = {
            "id": unit_id,
            "name": unit_in.name,
            "code": unit_in.code,
            "semester_id": semester_id, # Link back to semester
            "slots": [
                {
                    "day_of_week": s.day_of_week,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat()
                } for s in unit_in.slots
            ]
        }
        unit_ref = db.collection("users").document(uid).collection("units").document(unit_id)
        batch.set(unit_ref, fs_unit_data)
        
        saved_units.append({**unit_in.model_dump(), "id": unit_id})
        
    # 3. Generate Classes
    # We iterate over every day from start_date to end_date
    current_date = req.semester.start_date
    delta = timedelta(days=1)
    
    generated_classes = []
    
    while current_date <= req.semester.end_date:
        # Check if holiday
        if current_date in req.semester.holidays:
            current_date += delta
            continue
            
        iso_weekday = current_date.isoweekday()
        
        # Check if any unit has a slot on this day
        for unit, unit_data in zip(req.units, saved_units):
            for slot in unit.slots:
                if slot.day_of_week == iso_weekday:
                    # Calculate duration
                    dummy_date = datetime(2000, 1, 1)
                    start_dt = datetime.combine(dummy_date, slot.start_time)
                    end_dt = datetime.combine(dummy_date, slot.end_time)
                    
                    # Handle spanning past midnight if needed (unlikely for uni classes, but safe)
                    duration_secs = (end_dt - start_dt).total_seconds()
                    if duration_secs < 0:
                        duration_secs += 24 * 3600
                        
                    duration_hours = duration_secs / 3600.0
                    
                    class_id = str(uuid.uuid4())
                    class_log = {
                        "id": class_id,
                        "unit_id": unit_data["id"],
                        "semester_id": semester_id,
                        "date": current_date.isoformat(),
                        "start_time": slot.start_time.isoformat(),
                        "end_time": slot.end_time.isoformat(),
                        "duration_hours": duration_hours,
                        "status": "Pending"
                    }
                    
                    class_ref = db.collection("users").document(uid).collection("class_logs").document(class_id)
                    batch.set(class_ref, class_log)
                    
                    unit_expected_hours[unit_data["id"]] += duration_hours
                    generated_classes.append(class_log)
                    
        current_date += delta
        
    # 4. Save total expected hours per unit
    for unit_data in saved_units:
        unit_ref = db.collection("users").document(uid).collection("units").document(unit_data["id"])
        batch.update(unit_ref, {"total_expected_hours": unit_expected_hours[unit_data["id"]]})
        
    # Commit all writes
    batch.commit()
    
    return {
        "message": "Semester generated successfully",
        "semester_id": semester_id,
        "total_classes_generated": len(generated_classes)
    }

@app.get("/api/v1/dashboard")
def get_dashboard(uid: str = Depends(get_current_user_uid), db = Depends(get_firestore_db)):
    """
    Returns dashboard statistics:
    - Overall attendance rate
    - Unit specific progress, attendance rates, safe skips.
    """
    # Fetch units
    units_ref = db.collection("users").document(uid).collection("units")
    units = [doc.to_dict() for doc in units_ref.stream()]
    
    # Fetch all classes
    classes_ref = db.collection("users").document(uid).collection("class_logs")
    classes = [doc.to_dict() for doc in classes_ref.stream()]
    
    # Wait, fetching ALL classes might be slow if there are thousands,
    # but for a university semester it's around 12 weeks * 5 days * 4 classes = ~240. Very fast.
    
    # Calculate stats per unit
    dashboard_data = []
    
    for unit in units:
        unit_id = unit["id"]
        unit_classes = [c for c in classes if c.get("unit_id") == unit_id]
        
        attended_hours = sum(c["duration_hours"] for c in unit_classes if c["status"] == "Attended")
        missed_hours = sum(c["duration_hours"] for c in unit_classes if c["status"] == "Missed")
        cancelled_hours = sum(c["duration_hours"] for c in unit_classes if c["status"] == "Cancelled")
        
        total_expected_hours = unit.get("total_expected_hours", 0)
        effective_total_hours = total_expected_hours - cancelled_hours
        
        absence_rate = (missed_hours / effective_total_hours * 100) if effective_total_hours > 0 else 0
        attendance_rate = (attended_hours / effective_total_hours * 100) if effective_total_hours > 0 else 0
        
        # We need the semester to get the allowed absence percent
        # But for simplicity, we assume 20% if not linked, or we can fetch it.
        # Actually, let's fetch the semester
        semester_id = unit.get("semester_id")
        allowed_absence = 20.0
        if semester_id:
            sem_doc = db.collection("users").document(uid).collection("semesters").document(semester_id).get()
            if sem_doc.exists:
                allowed_absence = sem_doc.to_dict().get("allowed_absence_percent", 20.0)
                
        is_critical = absence_rate > allowed_absence
        
        # Safe skips left calculation:
        # Max allowed missed hours = effective_total_hours * (allowed_absence / 100)
        # Remaining missed hours = Max allowed missed hours - missed_hours
        # Safe skips (in terms of average class length or exact classes? We'll approximate by average class length)
        average_class_length = 0
        if len(unit_classes) > 0:
            average_class_length = sum(c["duration_hours"] for c in unit_classes) / len(unit_classes)
            
        safe_skips_hours = max(0, (effective_total_hours * (allowed_absence / 100)) - missed_hours)
        safe_skips = math.floor(safe_skips_hours / average_class_length) if average_class_length > 0 else 0
        
        dashboard_data.append({
            "unit": unit,
            "attended_hours": attended_hours,
            "missed_hours": missed_hours,
            "cancelled_hours": cancelled_hours,
            "effective_total_hours": effective_total_hours,
            "attendance_rate": attendance_rate,
            "absence_rate": absence_rate,
            "allowed_absence": allowed_absence,
            "is_critical": is_critical,
            "safe_skips_left": safe_skips
        })
        
    return {"units": dashboard_data}

@app.get("/api/v1/classes/today")
def get_today_classes(uid: str = Depends(get_current_user_uid), db = Depends(get_firestore_db)):
    """
    Returns today's classes for the user.
    """
    today_iso = datetime.now().date().isoformat()
    
    classes_ref = db.collection("users").document(uid).collection("class_logs")
    query = classes_ref.where("date", "==", today_iso)
    
    today_classes = [doc.to_dict() for doc in query.stream()]
    
    # We should also return the unit name for context
    units_ref = db.collection("users").document(uid).collection("units")
    units = {doc.id: doc.to_dict() for doc in units_ref.stream()}
    
    for c in today_classes:
        unit = units.get(c.get("unit_id"))
        if unit:
            c["unit_name"] = unit.get("name")
            c["unit_code"] = unit.get("code")
            
    # Sort by start time
    today_classes.sort(key=lambda x: x.get("start_time", ""))
    
    return today_classes

from pydantic import BaseModel
class StatusUpdate(BaseModel):
    status: str

@app.put("/api/v1/classes/{class_id}/status")
def update_class_status(
    class_id: str, 
    status_update: StatusUpdate,
    uid: str = Depends(get_current_user_uid), 
    db = Depends(get_firestore_db)
):
    """
    Updates the status of a specific class log.
    """
    if status_update.status not in ["Pending", "Attended", "Missed", "Cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    class_ref = db.collection("users").document(uid).collection("class_logs").document(class_id)
    doc = class_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Class not found")
        
    class_ref.update({"status": status_update.status})
    return {"message": "Status updated successfully", "new_status": status_update.status}
