"""
@file profile_app.py
@brief Skrypt profilujący wydajność kluczowych operacji bazodanowych i biznesowych.
@details Wykorzystuje moduły cProfile i pstats do analizy czasu wykonania operacji
         tworzenia sesji, zapisu pomiarów i odpytywania bazy.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""

import cProfile
import pstats
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, Session, SensorReading
from backend.database.alerts import check_reading_threshold
from backend.database.logging_db import log_event
from backend.obd.interface import ObdInterface
from backend.sensors.interface import ExternalSensorInterface

# Inicjalizacja bazy w pamięci na potrzeby testów profilowania
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


def setup_db():
    """Tworzy tabele w bazie danych."""
    Base.metadata.create_all(bind=engine)


def run_session_creation(n=50):
    """Symuluje wielokrotne tworzenie nowych sesji."""
    db = SessionLocal()
    for i in range(n):
        session = Session(vehicle_id=f"VEHICLE_{i}", status="active")
        db.add(session)
        db.flush()
        log_event("INFO", "profiler", f"Created session {session.id}", db=db)
        db.commit()
    db.close()


def run_readings_collection(session_id=1, n=50):
    """Symuluje pobieranie i zapis odczytów wraz z walidacją alertów."""
    db = SessionLocal()
    obd_interface = ObdInterface()
    sensor_interface = ExternalSensorInterface()

    for _ in range(n):
        obd_readings = obd_interface.read_all()
        external_readings = sensor_interface.read_all()

        saved = []
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
            check_reading_threshold(
                db=db,
                session_id=session_id,
                parameter=record.parameter,
                value=record.value,
                unit=record.unit,
                timestamp=record.timestamp,
            )

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
            check_reading_threshold(
                db=db,
                session_id=session_id,
                parameter=record.parameter,
                value=record.value,
                unit=record.unit,
                timestamp=record.timestamp,
            )

        log_event("INFO", "profiler", f"Collected {len(saved)} readings", db=db)
        db.commit()
    db.close()


def run_readings_query(session_id=1, n=100):
    """Symuluje odpytywanie o dane pomiarowe sesji."""
    db = SessionLocal()
    for _ in range(n):
        readings = db.query(SensorReading).filter(SensorReading.session_id == session_id).all()
        # Dostęp do pól celem symulacji serializacji JSON
        for r in readings:
            _ = r.parameter
            _ = r.value
            _ = r.timestamp
    db.close()


def main():
    setup_db()

    print("==========================================")
    print("   PROFILOWANIE: TWORZENIE SESJI (50x)")
    print("==========================================")
    pr = cProfile.Profile()
    pr.enable()
    run_session_creation()
    pr.disable()
    ps = pstats.Stats(pr).sort_stats("cumulative")
    ps.print_stats(12)

    print("\n==========================================")
    print("   PROFILOWANIE: ZBIERANIE Telemetrii (50x)")
    print("==========================================")
    pr = cProfile.Profile()
    pr.enable()
    run_readings_collection()
    pr.disable()
    ps = pstats.Stats(pr).sort_stats("cumulative")
    ps.print_stats(12)

    print("\n==========================================")
    print("   PROFILOWANIE: ZAPYTANIA O ODCZYTY (100x)")
    print("==========================================")
    pr = cProfile.Profile()
    pr.enable()
    run_readings_query()
    pr.disable()
    ps = pstats.Stats(pr).sort_stats("cumulative")
    ps.print_stats(12)


if __name__ == "__main__":
    main()
