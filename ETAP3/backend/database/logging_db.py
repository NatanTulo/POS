"""
@file logging_db.py
@brief Moduł zapisujący dziennik zdarzeń operacyjnych do bazy danych.
@details Dostarcza funkcję log_event, która w bezpieczny sposób (w niezależnej sesji)
         tworzy wpisy w tabeli event_logs. Spełnia wymaganie FR-13.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session as SQLSession
from backend.database.connection import SessionLocal
from backend.database.models import EventLog

logger = logging.getLogger(__name__)


def log_event(level: str, source: str, message: str, db: Optional[SQLSession] = None) -> None:
    """
    @brief Tworzy wpis w dzienniku zdarzeń w bazie danych.
    @details Wykorzystuje przekazaną sesję bazy danych lub otwiera nową (izolowaną),
             aby zapisać log operacyjny.
    @param level   Poziom zdarzenia: DEBUG, INFO, WARNING, ERROR.
    @param source  Źródło zdarzenia (nazwa modułu lub klasy).
    @param message Treść komunikatu zdarzenia.
    @param db      Opcjonalna sesja bazy danych (do koordynacji transakcji).
    """
    # Tradycyjne logowanie konsolowe/plikowe
    log_func = getattr(logger, level.lower(), logger.info)
    log_func("[%s] %s", source, message)

    log_entry = EventLog(
        level=level.upper(),
        source=source,
        message=message,
        timestamp=datetime.utcnow(),
    )

    if db is not None:
        try:
            db.add(log_entry)
        except Exception as exc:
            logger.error(
                "Failed to add EventLog to provided database session (Source: %s). Error: %s",
                source,
                exc,
            )
    else:
        # Zapis do bazy danych w wydzielonej sesji
        db_session = SessionLocal()
        try:
            db_session.add(log_entry)
            db_session.commit()
        except Exception as exc:
            db_session.rollback()
            logger.error(
                "Failed to save EventLog to database in isolated session (Source: %s). Error: %s",
                source,
                exc,
            )
        finally:
            db_session.close()

