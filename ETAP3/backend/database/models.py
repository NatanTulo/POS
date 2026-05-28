"""
@file models.py
@brief Definicje modeli danych (ORM) dla systemu monitorowania pojazdu.
@details Modele są mapowane na tabele SQLite za pomocą SQLAlchemy.
         Każdy model zawiera atrybuty z adnotacjami typów oraz relacje.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-05-28
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    @brief Klasa bazowa dla wszystkich modeli ORM.
    @details Dziedziczy z DeclarativeBase SQLAlchemy, co pozwala
             na automatyczne mapowanie klas na tabele bazy danych.
    """
    pass


class Session(Base):
    """
    @brief Reprezentuje pojedynczą sesję monitorowania pojazdu.
    @details Każda sesja zawiera identyfikator pojazdu, znacznik czasu
             rozpoczęcia i zakończenia oraz aktualny status. Status może
             przyjmowaę wartości: @c active , @c completed , @c degraded .
    """

    __tablename__ = "sessions"

    ## @brief Unikalny identyfikator sesji (klucz główny).
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ## @brief Identyfikator pojazdu (VIN lub numer rejestracyjny).
    vehicle_id: Mapped[str] = mapped_column(String(50), nullable=False)

    ## @brief Znacznik czasu rozpoczęcia sesji.
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ## @brief Znacznik czasu zakończenia sesji (nullable – NULL gdy sesja trwa).
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    ## @brief Status sesji: @c active , @c completed , @c degraded .
    status: Mapped[str] = mapped_column(String(20), default="active")

    ## @brief Relacja do odczytów czujników w tej sesji.
    readings: Mapped[list["SensorReading"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    ## @brief Relacja do alertów wygenerowanych w tej sesji.
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SensorReading(Base):
    """
    @brief Pojedynczy odczyt z czujnika (OBD lub dodatkowego).
    @details Przechowuje znormalizowaną wartość wraz z jednostką,
             Żródłem i precyzyjnym znacznikiem czasu.
    """

    __tablename__ = "sensor_readings"

    ## @brief Unikalny identyfikator odczytu.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ## @brief Klucz obcy do tabeli sesji.
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id"), nullable=False
    )

    ## @brief Nazwa parametru (np. @c rpm , @c coolant_temp , @c maf ).
    parameter: Mapped[str] = mapped_column(String(50), nullable=False)

    ## @brief Znormalizowana wartość liczbowa odczytu.
    value: Mapped[float] = mapped_column(Float, nullable=False)

    ## @brief Jednostka wartości (np. @c rpm , @c °C , @c V ).
    unit: Mapped[str] = mapped_column(String(20), nullable=False)

    ## @brief Źródło danych: @c obd lub @c external .
    source: Mapped[str] = mapped_column(String(20), nullable=False)

    ## @brief Znacznik czasu wykonania odczytu.
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ## @brief Relacja do rodzica – sesji monitorowania.
    session: Mapped["Session"] = relationship(back_populates="readings")


class Alert(Base):
    """
    @brief Reprezentuje zdarzenie alertu wygenerowane na podstawie reguł progowych.
    @details Każdy alert zawiera poziom ważności, opis oraz link do sesji,
             w której został wygenerowany.
    """

    __tablename__ = "alerts"

    ## @brief Unikalny identyfikator alertu.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ## @brief Klucz obcy do tabeli sesji.
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id"), nullable=False
    )

    ## @brief Poziom ważności: @c info , @c warning , @c critical .
    severity: Mapped[str] = mapped_column(String(20), nullable=False)

    ## @brief Treść komunikatu alertu.
    message: Mapped[str] = mapped_column(Text, nullable=False)

    ## @brief Nazwa parametru, który wywołał alert (np. @c coolant_temp ).
    parameter: Mapped[str] = mapped_column(String(50), nullable=False)

    ## @brief Wartość progowa, która została przekroczona.
    threshold: Mapped[float] = mapped_column(Float, nullable=False)

    ## @brief Rzeczywista wartość odczytu w momencie wywołania alertu.
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)

    ## @brief Znacznik czasu wygenerowania alertu.
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ## @brief Relacja do rodzica – sesji monitorowania.
    session: Mapped["Session"] = relationship(back_populates="alerts")


class EventLog(Base):
    """
    @brief Dziennik zdarzeń operacyjnych i błędów systemu.
    @details Służy do spełnienia wymagania FR-13 – prowadzenia dziennika
             zdarzeń z znacznikami czasu, poziomem i Żródłem.
    """

    __tablename__ = "event_logs"

    ## @brief Unikalny identyfikator zdarzenia.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ## @brief Poziom zdarzenia: @c DEBUG , @c INFO , @c WARNING , @c ERROR .
    level: Mapped[str] = mapped_column(String(20), nullable=False)

    ## @brief Źródło zdarzenia (nazwa modułu).
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    ## @brief Treść komunikatu zdarzenia.
    message: Mapped[str] = mapped_column(Text, nullable=False)

    ## @brief Znacznik czasu wystąpienia zdarzenia.
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
