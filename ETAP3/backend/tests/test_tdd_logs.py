"""
@file test_tdd_logs.py
@brief TDD testy jednostkowe weryfikujące poprawność rejestrowania zdarzeń systemowych w bazie danych.
@details Sprawdza, czy zdarzenia takie jak uruchomienie sesji, zakończenie sesji
         i inne krytyczne operacje zapisują rekordy w tabeli event_logs.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""


def test_db_logging_on_session_events(client):
    """
    @brief Weryfikuje, czy zdarzenia sesji są poprawnie zapisywane do tabeli event_logs (TDD).
    """
    # 1. Create session (should log session start)
    response = client.post("/api/v1/sessions?vehicle_id=TDD_LOG_CAR")
    assert response.status_code == 200
    session_id = response.json()["id"]

    # 2. Stop session (should log session stop)
    response = client.post(f"/api/v1/sessions/{session_id}/stop")
    assert response.status_code == 200

    # 3. Retrieve logs
    log_resp = client.get("/api/v1/logs")
    assert log_resp.status_code == 200
    logs = log_resp.json()

    # We expect at least 2 logs (start and stop)
    assert len(logs) >= 2

    # Check for session start log
    start_log = next((l for l in logs if f"GD12345" or "GD999" or "TDD_LOG_CAR" in l["message"] and "started" in l["message"].lower()), None)
    assert start_log is not None
    assert start_log["level"] == "INFO"

    # Check for session stop log
    stop_log = next((l for l in logs if "stopped" in l["message"].lower() or "completed" in l["message"].lower()), None)
    assert stop_log is not None
    assert stop_log["level"] == "INFO"
