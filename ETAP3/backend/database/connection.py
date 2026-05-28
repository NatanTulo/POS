"""
@file connection.py
@brief Zarządzanie połączeniem z bazą danych SQLite.
@details Używa SQLAlchemy jako ORM do komunikacji z bazą SQLite.
         Wszystkie operacje na bazie odbywają się przez współdzielony
         silnik (engine) i sesję (SessionLocal).

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-05-28
"""

import logging
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SQLSession, sessionmaker

from backend.database.models import Base

## @brief Ścieżka do pliku bazy danych SQLite (tworzony w katalogu projektu).
DB_PATH = Path(__file__).resolve().parent.parent.parent / "vehicle_monitor.db"

## @brief URL połączenia SQLAlchemy dla SQLite.
DATABASE_URL = f"sqlite:///{DB_PATH}"

##
# @brief Silnik bazy danych SQLAlchemy.
# @details Skonfigurowany z check_same_thread=False dla współbieżności FastAPI.
##
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

##
# @brief Fabryka sesji ORM.
# @details Każde żądanie HTTP tworzy własną sesję przez zależność
#          wstrzykiwaną przez FastAPI.
##
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

## @brief Logger dla modułu bazy danych.
logger = logging.getLogger(__name__)


def create_tables() -> None:
    """
    @brief Tworzy wszystkie tabele zdefiniowane w modelach ORM.
    @details Wywołuje Base.metadata.create_all(), które tworzy tabele
         tylko wtedy, gdy jeszcze nie istnieją. Funkcja bezpieczna
         do wielokrotnego wywołania (idempotentna).
    """
    logger.info("Creating database tables at %s", DB_PATH)
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")


def get_db() -> Generator[SQLSession, None, None]:
    """
    @brief Generator sesji bazy danych dla FastAPI (Dependency Injection).
    @details Używany jako zależność w endpointach FastAPI. Automatycznie
             zamyka sesję po zakończeniu żądania.
    @return Generator zwracajacy instancje SQLAlchemy Session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
