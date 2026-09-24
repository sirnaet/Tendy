from datetime import date, time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

HEADERS = {"Authorization": "Bearer demo_token_testuser"}

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_generate_semester_and_dashboard():
    # Generate schedule
    payload = {
        "semester": {
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
            "holidays": ["2026-09-07"],
            "allowed_absence_percent": 20.0
        },
        "units": [
            {
                "name": "Algorithms & Data Structures",
                "code": "CS-302",
                "slots": [
                    {
                        "day_of_week": 1, # Monday
                        "start_time": "09:00:00",
                        "end_time": "11:00:00"
                    }
                ]
            }
        ]
    }
    
    gen_resp = client.post("/api/v1/semesters/generate", json=payload, headers=HEADERS)
    assert gen_resp.status_code == 201
    data = gen_resp.json()
    assert "semester_id" in data

    # Check dashboard
    dash_resp = client.get("/api/v1/dashboard", headers=HEADERS)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert "units" in dash_data
    assert len(dash_data["units"]) > 0
    unit_entry = dash_data["units"][0]
    assert unit_entry["unit"]["code"] == "CS-302"
    assert "safe_skips_left" in unit_entry
    assert "absence_rate" in unit_entry
