from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_routes_reject_demo_tokens():
    for token in ("demo_token_attacker", "not-a-firebase-token"):
        headers = {"Authorization": f"Bearer {token}"}

        dashboard = client.get("/api/v1/dashboard", headers=headers)
        assert dashboard.status_code == 401

        response = client.get("/api/v1/classes/today", headers=headers)
        assert response.status_code == 401
