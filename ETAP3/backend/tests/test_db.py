"""
@file test_db.py
@brief Testy jednostkowe dla modeli bazy danych.
@details Weryfikuje poprawność zapisu, odczytu oraz relacji między modelami.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""

from datetime import datetime
from backend.database.models import Session, SensorReading, Alert, EventLog


def test_create_session(db):
    """
    @brief Testuje tworzenie sesji w bazie danych.
    """
    session = Session(vehicle_id="XYZ123", status="active")
    db.add(session)
    db.commit()
    db.refresh(session)

    assert session.id is not None
    assert session.vehicle_id == "XYZ123"
    assert session.status == "active"
    assert isinstance(session.start_time, datetime)
    assert session.end_time is None


def test_session_relationships(db):
    """
    @brief Testuje relacje między sesją, odczytami oraz alertami.
    """
    session = Session(vehicle_id="WARSZAWA01", status="active")
    db.add(session)
    db.commit()

    reading = SensorReading(
        session_id=session.id,
        parameter="rpm",
        value=3000.0,
        unit="rpm",
        source="obd",
    )
    alert = Alert(
        session_id=session.id,
        severity="warning",
        message="RPM too high",
        parameter="rpm",
        threshold=2500.0,
        actual_value=3000.0,
    )
    db.add_all([reading, alert])
    db.commit()

    # Re-fetch session
    db.refresh(session)
    assert len(session.readings) == 1
    assert session.readings[0].value == 3000.0
    assert len(session.alerts) == 1
    assert session.alerts[0].severity == "warning"


def test_create_event_log(db):
    """
    @brief Testuje zapis dziennika zdarzeń.
    """
    log = EventLog(
        level="INFO",
        source="test_db",
        message="Database test log message",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    assert log.id is not None
    assert log.level == "INFO"
    assert log.source == "test_db"
    assert log.message == "Database test log message"
    assert isinstance(log.timestamp, datetime)
