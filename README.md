# Tendy

Tendy is a university attendance tracker built with [Reflex](https://reflex.dev/). It lets students record class attendance, review attendance by course, and see how close they are to their configured absence limit.

## Features

- Email/password sign-up and sign-in through Firebase Authentication.
- Semester date range, holidays, and allowed absence percentage configuration.
- Course units with recurring weekly timetable slots.
- Daily roster with date navigation, status filters, and attendance recording.
- Per-course attended and missed hours, attendance/absence rates, and remaining safe skips.
- Light and dark themes.
- Firestore storage, with an in-memory store available for local UI development when Firestore credentials are not configured.
- A separate FastAPI service for generating semester schedules and serving dashboard and class endpoints.

## Requirements

- Python with a version supported by the installed Reflex release.
- `pip`.
- Firebase project credentials for real sign-up/sign-in and cloud data storage.

`requirements.txt` currently installs Reflex. The application also imports the Firebase Admin SDK directly, so install it explicitly in a fresh environment.

## Run the Reflex application

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt firebase-admin
reflex run
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Reflex starts the frontend and backend development services. Open the local URL printed by the command (typically `http://localhost:3000`).

## Firebase configuration

The UI signs users in through Firebase Authentication and verifies the returned ID token with Firebase Admin. A local in-memory Firestore fallback does **not** provide demo or anonymous sign-in; Firebase Authentication must be configured to register or log in.

1. Create or select a Firebase project and enable **Authentication → Sign-in method → Email/Password**.
2. Set the project's Web API key as `FIREBASE_WEB_API_KEY`.
3. Configure Firebase Admin credentials for Firestore. Either:
   - Set `FIREBASE_SERVICE_ACCOUNT_PATH` to a service account JSON file, or
   - Set up Google Application Default Credentials (ADC).
4. Optionally set `FIREBASE_PROJECT_ID` to choose a project. The code defaults to `tendy-eb67`.

For example, in a local shell:

```bash
export FIREBASE_WEB_API_KEY="your-firebase-web-api-key"
export FIREBASE_SERVICE_ACCOUNT_PATH="/path/outside/the/repository/service-account.json"
export FIREBASE_PROJECT_ID="your-firebase-project-id"
reflex run
```

Alternatively, configure ADC with the Google Cloud CLI:

```bash
gcloud auth application-default login
```

Do not commit service-account keys or put them in a publicly accessible location. If no Firestore credentials are available, the app uses an in-memory store; its data is temporary and is lost when the process stops. To connect to a Firestore emulator, set `FIRESTORE_EMULATOR_HOST` and `FIREBASE_PROJECT_ID` before starting the app. Firebase Authentication still requires an appropriately configured Firebase Authentication project.

The navigation bar reports the active Firestore mode. For further Firebase guidance, see [FIREBASE_SETUP.md](FIREBASE_SETUP.md).

## Using Tendy

1. Create an account or sign in with Firebase Authentication.
2. Set your semester name, start and end dates, holiday dates, and allowed absence percentage in the configuration panel.
3. Add each course with a code, title, and one or more weekly schedule slots.
4. Select a day in the daily roster and mark each class as **Present**, **Absent**, or **Cancelled**. Use the date controls and status filter to review other days.
5. Review each course card for attendance statistics and the safe-skips estimate.

Holiday dates are entered as comma-separated `YYYY-MM-DD` values. Attendance and unit records are scoped to the signed-in user.

## Optional FastAPI service

The repository also includes a separate FastAPI implementation under `backend/`. It is not the server used by the Reflex UI and has a distinct API data model and Firestore collection layout.

Install the API's runtime packages in addition to the root requirements:

```bash
python -m pip install fastapi uvicorn python-dotenv firebase-admin
```

Start the service from the repository root:

```bash
uvicorn main:app --app-dir backend --reload
```

The API is available at `http://localhost:8000`. Its unauthenticated health endpoint is `GET /api/health`; the other routes require a valid Firebase Authentication ID token in the HTTP Authorization header.

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/semesters/generate` | Create a semester, its units, and generated class logs. |
| `GET` | `/api/v1/dashboard` | Return per-unit attendance summaries. |
| `GET` | `/api/v1/classes/today` | List today's classes for the authenticated user. |
| `PUT` | `/api/v1/classes/{class_id}/status` | Update a class status (`Pending`, `Attended`, `Missed`, or `Cancelled`). |

## Tests

The repository includes standalone tests for the attendance engine, schemas, and Firebase helpers:

```bash
python test_core.py
python test_all_modules.py
```

The FastAPI tests require the API dependencies above and can be run from the repository root with:

```bash
python -m pip install pytest
python -m pytest backend/test_backend.py
```

## Project layout

```text
app.py                 Reflex UI and application state
Tendy/Tendy.py         Reflex package entry point
engine.py              Schedule generation and attendance calculations
schemas.py             Pydantic models for the Reflex application
firebase_client.py     Firebase initialization, auth, and local store
backend/               Separate FastAPI application
dataconnect/           Firebase Data Connect schema and connector config
assets/                Static assets
```
