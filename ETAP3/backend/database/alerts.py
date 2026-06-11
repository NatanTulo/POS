"""
@file alerts.py
@brief Moduł reguł alertowych i walidacji progów pomiarowych.
@details Definiuje konfigurację progów ostrzegawczych (warning) i krytycznych (critical)
         dla kluczowych parametrów OBD i czujników dodatkowych.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session as SQLSession
from backend.database.models import Alert
from backend.database.logging_db import log_event

logger = logging.getLogger(__name__)

##
# @brief Definicje progów ostrzegawczych i krytycznych dla parametrów.
# @details Zawiera operator porównania, wartość progową oraz szablon wiadomości.
##
THRESHOLDS = {
    "RPM": {
        "warning": {"op": ">", "val": 5500.0, "msg": "Engine RPM warning: {} rpm"},
        "critical": {"op": ">", "val": 6200.0, "msg": "Engine RPM critical: {} rpm"},
    },
    "COOLANT_TEMP": {
        "warning": {"op": ">", "val": 98.0, "msg": "Coolant temperature warning: {} \u00b0C"},
        "critical": {"op": ">", "val": 105.0, "msg": "Coolant temperature critical: {} \u00b0C"},
    },
    "VOLTAGE": {
        "warning": {"op": "<", "val": 12.2, "msg": "Battery voltage warning: {} V"},
        "critical": {"op": "<", "val": 11.8, "msg": "Battery voltage critical: {} V"},
    },
    "oil_temp": {
        "warning": {"op": ">", "val": 115.0, "msg": "Oil temperature warning: {} \u00b0C"},
        "critical": {"op": ">", "val": 130.0, "msg": "Oil temperature critical: {} \u00b0C"},
    },
    "fuel_pressure": {
        "warning": {"op": "<", "val": 2.0, "msg": "Fuel pressure warning: {} bar"},
        "critical": {"op": "<", "val": 1.0, "msg": "Fuel pressure critical: {} bar"},
    },
}


def check_reading_threshold(
    db: SQLSession,
    session_id: int,
    parameter: str,
    value: float,
    unit: str,
    timestamp: datetime,
) -> Optional[Alert]:
    """
    @brief Sprawdza odczyt pod kątem przekroczenia progów i generuje ewentualny alert.
    @details Sprawdza najpierw próg krytyczny, a następnie ostrzegawczy.
             W przypadku wykrycia przekroczenia, tworzy i dodaje obiekt Alert do sesji bazy.
    @param db         Sesja bazy danych.
    @param session_id Identyfikator sesji monitorowania.
    @param parameter  Nazwa parametru (np. coolant_temp).
    @param value      Wartość odczytu.
    @param unit       Jednostka.
    @param timestamp  Czas odczytu.
    @return Utworzony obiekt Alert lub None, jeśli próg nie został przekroczony.
    """
    rules = THRESHOLDS.get(parameter)
    if not rules:
        # Wyszukiwanie case-insensitive
        for k, v in THRESHOLDS.items():
            if k.lower() == parameter.lower():
                rules = v
                break

    if not rules:
        return None

    for severity in ["critical", "warning"]:
        rule = rules.get(severity)
        if not rule:
            continue

        op = rule["op"]
        val = rule["val"]
        msg_template = rule["msg"]

        violated = False
        if op == ">" and value > val:
            violated = True
        elif op == "<" and value < val:
            violated = True

        if violated:
            alert = Alert(
                session_id=session_id,
                severity=severity,
                message=msg_template.format(value),
                parameter=parameter,
                threshold=val,
                actual_value=value,
                timestamp=timestamp,
            )
            db.add(alert)
            log_event(
                "WARNING" if severity == "warning" else "ERROR",
                "alerts",
                f"Alert raised: {alert.message} for session {session_id}",
                db=db,
            )
            return alert


    return None
