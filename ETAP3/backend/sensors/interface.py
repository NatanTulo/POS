"""
@file interface.py
@brief Moduł dodatkowych czujników (spoza OBD-II).
@details Umożliwia integrację czujników takich jak temperatura oleju,
         ciśnienie paliwa, prędkość obrotowa kół itp., które nie są
         dostępne przez standardowy interfejs OBD.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-05-28
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

## @brief Logger modułu czujników zewnętrznych.
logger = logging.getLogger(__name__)


@dataclass
class ExternalSensorReading:
    """
    @brief Przechowuje pojedynczy odczyt z czujnika zewnętrznego.
    @details Używa @c dataclass dla automatycznej generacji metod
             __init__, __repr__ oraz porównań.
    """

    ## @brief Nazwa czujnika (np. @c oil_temp , @c fuel_pressure ).
    sensor_name: str

    ## @brief Znormalizowana wartość odczytu.
    value: float

    ## @brief Jednostka wartości (np. @c °C , @c bar ).
    unit: str

    ## @brief Źródło danych (np. @c gpio , @c analog_input ).
    source: str

    ## @brief Znacznik czasu odczytu. Ustawiany automatycznie.
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """
        @brief Konwertuje odczyt do słownika.
        @return Słownik z polami: sensor_name, value, unit, source, timestamp.
        """
        return {
            "sensor_name": self.sensor_name,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }


class ExternalSensorInterface:
    """
    @brief Interfejs do obsługi dodatkowych czujników.
    @details W podstawowej wersji dostarcza symulowane odczyty.
             Docelowo może byę rozszerzony o obsługę wejść GPIO,
             ADC (przetwornik analogowo-cyfrowy) lub magistrali I2C.

    ## Architektura rozszerzeń:
    Aby dodaę nowy typ czujnika, należy:
    1. Utworzyę podklasę ExternalSensorInterface.
    2. Zaimplementowaę metodę read().
    3. Zarejestrowaę w fabryce czujników.
    """

    def __init__(self) -> None:
        """Inicjalizuje interfejs czujników."""
        self._sensors: dict[str, dict] = {
            "oil_temp": {"unit": "\u00b0C", "min": 20.0, "max": 150.0},
            "fuel_pressure": {"unit": "bar", "min": 0.5, "max": 6.0},
        }

    def read_all(self) -> list[ExternalSensorReading]:
        """
        @brief Odczytuje wszystkie dostępne czujniki zewnętrzne.
        @details W trybie podstawowym zwraca wartości symulowane.
                 Algorytm: dla każdego czujnika zdefiniowanego w self._sensors
                 generuje losową wartość z zakresu [min, max].
        @return Lista obiektów ExternalSensorReading.

        @warning W docelowej wersji należy zastąpię symulację
                 rzeczywistym odczytem z GPIO / ADC.
        """
        import random

        readings: list[ExternalSensorReading] = []
        for name, config in self._sensors.items():
            value = round(random.uniform(config["min"], config["max"]), 1)
            readings.append(
                ExternalSensorReading(
                    sensor_name=name,
                    value=value,
                    unit=config["unit"],
                    source="external",
                )
            )
        return readings

    def read_sensor(self, name: str) -> Optional[ExternalSensorReading]:
        """
        @brief Odczytuje pojedynczy czujnik zewnętrzny po nazwie.
        @param name  Nazwa czujnika (np. @c oil_temp ).
        @return Obiekt ExternalSensorReading lub None, jeśli czujnik
                nie istnieje.
        """
        config = self._sensors.get(name)
        if config is None:
            logger.warning("Sensor '%s' not found.", name)
            return None
        import random

        value = round(random.uniform(config["min"], config["max"]), 1)
        return ExternalSensorReading(
            sensor_name=name,
            value=value,
            unit=config["unit"],
            source="external",
        )
