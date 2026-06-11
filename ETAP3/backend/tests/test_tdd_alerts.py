"""
@file test_tdd_alerts.py
@brief TDD testy jednostkowe weryfikujące generowanie alertów przekroczenia progów.
@details Sprawdza, czy przekroczenie zdefiniowanych progów bezpieczeństwa dla RPM,
         temperatury chłodnicy, napięcia, temp. oleju i ciśnienia paliwa poprawnie
         generuje alerty w bazie danych.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""

from unittest.mock import patch
from backend.obd.interface import ObdParameter, ObdReading
from backend.sensors.interface import ExternalSensorReading


def test_alert_generation_on_threshold_violation(client, db):
    """
    @brief Weryfikuje generowanie alertów przy zebraniu nieprawidłowych pomiarów (TDD).
    """
    # 1. Mock sensor data to exceed thresholds:
    # RPM: 6000 (threshold: warning > 5500)
    # COOLANT_TEMP: 108 (threshold: critical > 105)
    # VOLTAGE: 11.5 (threshold: critical < 11.8)
    mock_obd = [
        ObdReading(ObdParameter.RPM, 6000.0),
        ObdReading(ObdParameter.COOLANT_TEMP, 108.0),
        ObdReading(ObdParameter.VOLTAGE, 11.5),
        ObdReading(ObdParameter.MAP, 100.0),
        ObdReading(ObdParameter.MAF, 15.0),
    ]

    # oil_temp: 140.0 (threshold: critical > 130)
    # fuel_pressure: 1.5 (threshold: warning < 2.0)
    mock_ext = [
        ExternalSensorReading("oil_temp", 140.0, "°C", "external"),
        ExternalSensorReading("fuel_pressure", 1.5, "bar", "external"),
    ]

    # Create session
    response = client.post("/api/v1/sessions?vehicle_id=TDD_ALERT_CAR")
    session_id = response.json()["id"]

    # Patch interfaces to return mocked readings
    with patch("backend.api.endpoints.obd_interface.read_all", return_value=mock_obd), \
         patch("backend.api.endpoints.sensor_interface.read_all", return_value=mock_ext):
        # Trigger collection
        collect_resp = client.post(f"/api/v1/sessions/{session_id}/readings/collect")
        assert collect_resp.status_code == 200

    # 2. Verify alerts are generated in the database:
    alert_resp = client.get(f"/api/v1/sessions/{session_id}/alerts")
    assert alert_resp.status_code == 200
    alerts = alert_resp.json()

    # We expect exactly 5 alerts (RPM, Coolant Temp, Voltage, Oil Temp, Fuel Pressure)
    assert len(alerts) == 5

    # Check coolant temp critical alert
    coolant_alert = next((a for a in alerts if a["parameter"] == "COOLANT_TEMP"), None)
    assert coolant_alert is not None
    assert coolant_alert["severity"] == "critical"
    assert coolant_alert["actual_value"] == 108.0
    assert coolant_alert["threshold"] == 105.0

    # Check fuel pressure warning alert
    fuel_alert = next((a for a in alerts if a["parameter"] == "fuel_pressure"), None)
    assert fuel_alert is not None
    assert fuel_alert["severity"] == "warning"
    assert fuel_alert["actual_value"] == 1.5
    assert fuel_alert["threshold"] == 2.0
