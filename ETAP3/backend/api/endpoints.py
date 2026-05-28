"""
@file endpoints.py
@brief Endpointy REST API systemu monitorowania pojazdu.
@details Implementuje kolekcję zasobów REST zgodnie ze specyfikacją
         interfejsów (rozdz. 8.2 specyfikacji funkcjonalnej).
         Każdy endpoint jest udokumentowany za pomocą Doxygen.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-05-28
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlalchemy.orm import Session as SQLSession

from backend.database.connection import get_db
from backend.database.models import Alert, EventLog, SensorReading, Session
from backend.obd.interface import ObdInterface, ObdParameter
from backend.sensors.interface import ExternalSensorInterface

## @brief Router API z przedrostkiem /api/v1 (rejestrowany w main.py).
router = APIRouter()

## @brief Logger dla modułu API.
logger = logging.getLogger(__name__)

##
# @brief Globalna instancja interfejsu OBD.
# @note W docelowej wersji powinna byę zarządzana przez mechanizm
#       wstrzykiwania zależności (Dependency Injection).
##
obd_interface = ObdInterface()

##
# @brief Globalna instancja interfejsu czujników zewnętrznych.
##
sensor_interface = ExternalSensorInterface()


@router.get("/sessions")
def list_sessions(
    skip: int = Query(0, ge=0, description="Liczba pomijanych rekordów (pagination)"),
    limit: int = Query(100, ge=1, le=500, description="Maksymalna liczba sesji"),
    db: SQLSession = Depends(get_db),
):
    """
    @brief Pobiera listę wszystkich sesji monitorowania.
    @details Zwraca sesje posortowane malejąco według czasu rozpoczęcia.
             Wspiera paginację przez parametry skip i limit.
    @param skip  Liczba pomijanych rekordów (offset).
    @param limit Maksymalna liczba zwracanych sesji (domyślnie 100, max 500).
    @param db    Sesja bazy danych (wstrzykiwana przez FastAPI).
    @return Lista sesji w formacie JSON.

    ### Schemat odpowiedzi:
    @code{.json}
    [
      {
        "id": 1,
        "vehicle_id": "ABC123",
        "start_time": "2026-05-28T10:00:00",
        "end_time": null,
        "status": "active"
      }
    ]
    @endcode

    @throws HTTP 400 jeśli parametry paginacji są nieprawidłowe (walidacja FastAPI).
    """
    sessions = (
        db.query(Session)
        .order_by(Session.start_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return sessions


@router.get("/sessions/{session_id}")
def get_session(session_id: int, db: SQLSession = Depends(get_db)):
    """
    @brief Pobiera szczegóły pojedynczej sesji monitorowania.
    @param session_id Identyfikator sesji.
    @param db         Sesja bazy danych.
    @return Szczegóły sesji w formacie JSON.
    @throws HTTP 404 jeśli sesja nie istnieje.
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions")
def create_session(
    vehicle_id: str = Query(..., description="Identyfikator pojazdu (VIN / rejestracja)"),
    db: SQLSession = Depends(get_db),
):
    """
    @brief Tworzy nową sesję monitorowania pojazdu.
    @details Ustawia status na @c active i czas startu na aktualny moment UTC.
    @param vehicle_id Identyfikator pojazdu.
    @param db         Sesja bazy danych.
    @return Utworzona sesja w formacie JSON.
    """
    session = Session(vehicle_id=vehicle_id, status="active")
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info("Created session %d for vehicle %s", session.id, vehicle_id)
    return session


@router.post("/sessions/{session_id}/stop")
def stop_session(session_id: int, db: SQLSession = Depends(get_db)):
    """
    @brief Kończy aktywną sesję monitorowania.
    @details Ustawia status na @c completed i zapisuje czas zakończenia.
    @param session_id Identyfikator sesji.
    @param db         Sesja bazy danych.
    @return Zaktualizowana sesja.
    @throws HTTP 404 jeśli sesja nie istnieje.
    @throws HTTP 409 jeśli sesja jest już zakończona.
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="Session is not active")
    session.status = "completed"
    session.end_time = datetime.utcnow()
    db.commit()
    db.refresh(session)
    logger.info("Stopped session %d", session_id)
    return session


@router.get("/sessions/{session_id}/readings")
def get_readings(
    session_id: int,
    parameter: Optional[str] = Query(None, description="Filtruj po nazwie parametru"),
    from_time: Optional[datetime] = Query(None, alias="from", description="Początek zakresu czasowego"),
    to_time: Optional[datetime] = Query(None, description="Koniec zakresu czasowego"),
    db: SQLSession = Depends(get_db),
):
    """
    @brief Pobiera odczyty czujników dla danej sesji.
    @details Wspiera filtrowanie po parametrze oraz zakresie czasowym.
             Zgodne z wymaganiem FR-12 (endpoint GET /sessions/{id}/readings).
    @param session_id Identyfikator sesji.
    @param parameter  Opcjonalny filtr nazwy parametru.
    @param from_time  Opcjonalny początek zakresu ISO8601.
    @param to_time    Opcjonalny koniec zakresu ISO8601.
    @param db         Sesja bazy danych.
    @return Lista odczytów.
    @throws HTTP 404 jeśli sesja nie istnieje.
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    query = db.query(SensorReading).filter(SensorReading.session_id == session_id)

    if parameter:
        query = query.filter(SensorReading.parameter == parameter)
    if from_time:
        query = query.filter(SensorReading.timestamp >= from_time)
    if to_time:
        query = query.filter(SensorReading.timestamp <= to_time)

    readings = query.order_by(SensorReading.timestamp.asc()).all()
    return readings


@router.get("/sessions/{session_id}/alerts")
def get_alerts(
    session_id: int,
    severity: Optional[str] = Query(None, description="Filtruj po poziomie: info, warning, critical"),
    db: SQLSession = Depends(get_db),
):
    """
    @brief Pobiera alerty dla danej sesji.
    @details Zgodne z wymaganiem FR-08 i FR-10.
    @param session_id Identyfikator sesji.
    @param severity   Opcjonalny filtr poziomu ważności.
    @param db         Sesja bazy danych.
    @return Lista alertów.
    @throws HTTP 404 jeśli sesja nie istnieje.
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    query = db.query(Alert).filter(Alert.session_id == session_id)
    if severity:
        query = query.filter(Alert.severity == severity)
    alerts = query.order_by(Alert.timestamp.desc()).all()
    return alerts


@router.post("/sessions/{session_id}/readings/collect")
def collect_readings(
    session_id: int,
    db: SQLSession = Depends(get_db),
):
    """
    @brief Wykonuje natychmiastowy odczyt wszystkich parametrów (OBD + zewnętrzne).
    @details Odczytuje dane z OBD i czujników zewnętrznych, a następnie
             zapisuje je do bazy w ramach jednej transakcji.
    @param session_id Identyfikator sesji.
    @param db         Sesja bazy danych.
    @return Lista zapisanych odczytów.
    @throws HTTP 404 jeśli sesja nie istnieje lub nie jest aktywna.
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="Session is not active")

    obd_interface.connect()
    obd_readings = obd_interface.read_all()
    external_readings = sensor_interface.read_all()

    saved: list[SensorReading] = []
    for obd_reading in obd_readings:
        record = SensorReading(
            session_id=session_id,
            parameter=obd_reading.parameter.value,
            value=obd_reading.value if obd_reading.value is not None else 0.0,
            unit=obd_reading.unit,
            source=obd_reading.source,
            timestamp=obd_reading.timestamp,
        )
        db.add(record)
        saved.append(record)

    for ext_reading in external_readings:
        record = SensorReading(
            session_id=session_id,
            parameter=ext_reading.sensor_name,
            value=ext_reading.value,
            unit=ext_reading.unit,
            source=ext_reading.source,
            timestamp=ext_reading.timestamp,
        )
        db.add(record)
        saved.append(record)

    db.commit()
    for r in saved:
        db.refresh(r)

    logger.info("Collected %d readings for session %d", len(saved), session_id)
    return saved


@router.get("/sessions/{session_id}/export")
def export_session(
    session_id: int,
    fmt: str = Query("json", regex="^(json|csv)$", description="Format eksportu: json lub csv"),
    db: SQLSession = Depends(get_db),
):
    """
    @brief Eksportuje dane sesji do JSON lub CSV.
    @details Zgodne z wymaganiem FR-11. Dla formatu CSV zwraca
             nagłówki: id, parameter, value, unit, source, timestamp.
    @param session_id Identyfikator sesji.
    @param fmt        Format eksportu: @c json (domyślnie) lub @c csv .
    @param db         Sesja bazy danych.
    @return Plik z danymi (application/json lub text/csv).
    @throws HTTP 404 jeśli sesja nie istnieje.
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    readings = (
        db.query(SensorReading)
        .filter(SensorReading.session_id == session_id)
        .order_by(SensorReading.timestamp.asc())
        .all()
    )

    data = [
        {
            "id": r.id,
            "parameter": r.parameter,
            "value": r.value,
            "unit": r.unit,
            "source": r.source,
            "timestamp": r.timestamp.isoformat(),
        }
        for r in readings
    ]

    if fmt == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "parameter", "value", "unit", "source", "timestamp"])
        writer.writeheader()
        writer.writerows(data)
        return Response(content=output.getvalue(), media_type="text/csv")

    return data


@router.get("/vehicles/{vehicle_id}/metrics")
def get_vehicle_metrics(
    vehicle_id: str,
    from_time: datetime = Query(..., alias="from", description="Początek zakresu"),
    to_time: datetime = Query(..., description="Koniec zakresu"),
    db: SQLSession = Depends(get_db),
):
    """
    @brief Pobiera zagregowane metryki pojazdu w zadanym przedziale czasu.
    @details Oblicza średnie, maksymalne i minimalne wartości parametrów
             dla wszystkich sesji danego pojazdu w zadanym zakresie.
    @param vehicle_id Identyfikator pojazdu.
    @param from_time  Początek zakresu ISO8601 (wymagane).
    @param to_time    Koniec zakresu ISO8601 (wymagane).
    @param db         Sesja bazy danych.
    @return Lista metryk: { parameter, avg_value, max_value, min_value, unit }.
    """
    metrics = (
        db.query(
            SensorReading.parameter,
            func.avg(SensorReading.value).label("avg_value"),
            func.max(SensorReading.value).label("max_value"),
            func.min(SensorReading.value).label("min_value"),
            SensorReading.unit,
        )
        .join(Session)
        .filter(
            Session.vehicle_id == vehicle_id,
            SensorReading.timestamp >= from_time,
            SensorReading.timestamp <= to_time,
        )
        .group_by(SensorReading.parameter, SensorReading.unit)
        .all()
    )
    return metrics


@router.get("/health")
def health_check():
    """
    @brief Endpoint kondycji usługi.
    @details Służy do monitorowania dostępności backendu (health check).
             Zwraca status OK oraz znacznik czasu.
    @return { "status": "ok", "timestamp": "..." }
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/logs")
def get_logs(
    level: Optional[str] = Query(None, description="Filtr poziomu: DEBUG, INFO, WARNING, ERROR"),
    limit: int = Query(100, ge=1, le=1000, description="Limit rekordów"),
    db: SQLSession = Depends(get_db),
):
    """
    @brief Pobiera dziennik zdarzeń systemowych.
    @details Zgodne z wymaganiem FR-13. Zwraca zdarzenia operacyjne
             i błędy z znacznikami czasu, poziomem i Żródłem.
    @param level Opcjonalny filtr poziomu zdarzenia.
    @param limit Maksymalna liczba wpisów (domyślnie 100, max 1000).
    @param db    Sesja bazy danych.
    @return Lista wpisów dziennika.
    """
    query = db.query(EventLog)
    if level:
        query = query.filter(EventLog.level == level.upper())
    logs = query.order_by(EventLog.timestamp.desc()).limit(limit).all()
    return logs
