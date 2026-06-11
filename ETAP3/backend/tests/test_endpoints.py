"""
@file test_endpoints.py
@brief Testy integracyjne dla endpointów FastAPI.
@details Testuje interakcję przez klienta HTTP z bazą danych i logiką biznesową.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""

from datetime import datetime


def test_health_check(client):
    """
    @brief Testuje endpoint GET /health.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_create_and_get_session(client):
    """
    @brief Testuje tworzenie sesji, pobieranie szczegółów oraz listowanie.
    """
    # 1. Create session
    response = client.post("/api/v1/sessions?vehicle_id=GD12345")
    assert response.status_code == 200
    session_data = response.json()
    assert session_data["id"] is not None
    assert session_data["vehicle_id"] == "GD12345"
    assert session_data["status"] == "active"

    session_id = session_data["id"]

    # 2. Get session details
    response = client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["vehicle_id"] == "GD12345"

    # 3. List sessions
    response = client.get("/api/v1/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == session_id


def test_stop_session(client):
    """
    @brief Testuje zatrzymanie sesji.
    """
    # Create session
    response = client.post("/api/v1/sessions?vehicle_id=GD999")
    session_id = response.json()["id"]

    # Stop session
    response = client.post(f"/api/v1/sessions/{session_id}/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["end_time"] is not None

    # Try to stop again - should fail (409 Conflict)
    response = client.post(f"/api/v1/sessions/{session_id}/stop")
    assert response.status_code == 409


def test_collect_and_get_readings(client):
    """
    @brief Testuje zbieranie odczytów i ich pobieranie z filtracją.
    """
    # Create session
    response = client.post("/api/v1/sessions?vehicle_id=GD111")
    session_id = response.json()["id"]

    # Collect readings
    response = client.post(f"/api/v1/sessions/{session_id}/readings/collect")
    assert response.status_code == 200
    readings = response.json()
    assert len(readings) > 0

    # Get readings
    response = client.get(f"/api/v1/sessions/{session_id}/readings")
    assert response.status_code == 200
    assert len(response.json()) == len(readings)

    # Get readings filtered by parameter
    first_param = readings[0]["parameter"]
    response = client.get(f"/api/v1/sessions/{session_id}/readings?parameter={first_param}")
    assert response.status_code == 200
    for r in response.json():
        assert r["parameter"] == first_param


def test_export_session_data(client):
    """
    @brief Testuje eksport danych sesji do JSON i CSV.
    """
    # Create session and collect data
    response = client.post("/api/v1/sessions?vehicle_id=GD_EXPORT")
    session_id = response.json()["id"]
    client.post(f"/api/v1/sessions/{session_id}/readings/collect")

    # Export JSON
    response = client.get(f"/api/v1/sessions/{session_id}/export?fmt=json")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

    # Export CSV
    response = client.get(f"/api/v1/sessions/{session_id}/export?fmt=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "parameter,value,unit,source,timestamp" in response.text
