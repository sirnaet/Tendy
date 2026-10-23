# Firebase Setup & Connection Guide

This application is configured to connect to Google Cloud Firebase / Cloud Firestore for real-time attendance logging and user management.

## Current Firebase Project Configuration

- **Project ID**: `tendy-eb67` (configured in `.firebaserc`)
- **Collection Structure**:
  - `users/{uid}`: User profiles and global settings (`email`, `max_absence_pct`).
  - `users/{uid}/semesters/{semester_id}`: Semester definitions & date bounds.
  - `users/{uid}/semesters/{semester_id}/units/{unit_code}`: Course unit definitions and recurring weekly schedule time slots.
  - `users/{uid}/attendance_logs/{log_id}`: Attendance records (`Present`, `Absent`, `Cancelled`, `Pending`).

---

## Connection Options

`firebase_client.py` supports multiple seamless authentication methods:

### Option 1: Service Account Key File (Recommended for Local Dev)
1. Go to the [Firebase Console](https://console.firebase.google.com/) -> Select project `tendy-eb67`.
2. Navigate to **Project Settings** -> **Service accounts**.
3. Click **Generate new private key** and download the JSON file.
4. Save the file in the project root folder as `serviceAccountKey.json` (or set `FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/key.json`).
5. Restart the application. The status pill will change to `🟢 Firebase: tendy-eb67`.

### Option 2: Google Application Default Credentials (ADC)
If you have the Google Cloud CLI (`gcloud`) installed on your system:
```bash
gcloud auth application-default login
```
The application will automatically detect ADC and connect to project `tendy-eb67`.

### Option 3: Firebase Emulator (For local testing without cloud resources)
To run with the local Firestore emulator:
```bash
export FIRESTORE_EMULATOR_HOST="localhost:8080"
export FIREBASE_PROJECT_ID="tendy-eb67"
reflex run
```

### Option 4: Local MemoryStore Mode (Automatic Offline Fallback)
If no Firebase credentials or emulator are detected, the app automatically falls back to an in-memory Firestore emulator so that development and UI testing never crash!

---

## Live Status Indicator
The top navigation bar displays a live indicator pill:
- `🟢 Firebase: tendy-eb67` – Connected to live Cloud Firestore / Service Account / ADC / Emulator.
- `🟡 Local Store (MemoryStore)` – Operating in local offline fallback mode.
