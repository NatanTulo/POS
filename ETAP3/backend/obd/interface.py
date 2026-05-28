"""
@file interface.py
@brief Moduł komunikacji z adapterem OBD-II (ELM327) przez bibliotekę python-obd.
@details Odpowiada za inicjalizację połączenia, cykliczny odczyt parametrów
         silnika (RPM, temperatura cieczy, MAP/MAF, napięcie) oraz normalizację
         surowych danych do modelu SensorReading.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-05-28
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional

##
# @brief Próba importu biblioteki python-obd.
# @details Jeśli adapter nie jest dostępny (brak biblioteki), moduł działa
#          w trybie symulacji – zwraca wygenerowane wartości.
##
try:
    import obd

    OBD_AVAILABLE = True
except ImportError:
    OBD_AVAILABLE = False

## @brief Logger dla modułu OBD.
logger = logging.getLogger(__name__)


class ObdParameter(Enum):
    """
    @brief Enumeracja monitorowanych parametrów OBD.
    @details Mapuje nazwy parametrów na odpowiadające im identyfikatory PID OBD.
    """

    ## @brief Obroty silnika (RPM).
    RPM = "RPM"
    ## @brief Temperatura płynu chłodzącego (°C).
    COOLANT_TEMP = "COOLANT_TEMP"
    ## @brief Ciśnienie kolektora dolotowego (kPa).
    MAP = "MAP"
    ## @brief Masowy przepływ powietrza (g/s).
    MAF = "MAF"
    ## @brief Napięcie instalacji elektrycznej (V).
    VOLTAGE = "VOLTAGE"


## @brief Mapowanie parametrów OBD na komendy biblioteki python-obd.
PID_MAP: dict[ObdParameter, str] = {
    ObdParameter.RPM: "RPM",
    ObdParameter.COOLANT_TEMP: "COOLANT_TEMP",
    ObdParameter.MAP: "INTAKE_MAP",
    ObdParameter.MAF: "MAF",
    ObdParameter.VOLTAGE: "ELM_VOLTAGE",
}


class ObdReading:
    """
    @brief Przechowuje pojedynczy, znormalizowany odczyt z adaptera OBD.
    @details Zawiera nazwę parametru, wartość liczbową, jednostkę oraz znacznik
             czasu pobrania próbki. Obiekt jest gotowy do zapisu do bazy danych.
    """

    def __init__(self, parameter: ObdParameter, raw_value: Optional[float]) -> None:
        """
        @brief Konstruktor odczytu OBD.
        @param parameter  Parametr OBD, który został odczytany.
        @param raw_value  Surowa wartość zwrócona przez adapter (może byę None).
        """
        self.parameter = parameter
        self.value = raw_value
        self.timestamp = datetime.utcnow()
        self.source = "obd"

    @property
    def unit(self) -> str:
        """
        @brief Zwraca jednostkę dla danego parametru OBD.
        @details Jednostki są znormalizowane zgodnie z SI:
                 - RPM -> rpm
                 - COOLANT_TEMP -> °C
                 - MAP -> kPa
                 - MAF -> g/s
                 - VOLTAGE -> V
        @return Jednostka parametru jako napis.
        """
        units: dict[ObdParameter, str] = {
            ObdParameter.RPM: "rpm",
            ObdParameter.COOLANT_TEMP: "\u00b0C",
            ObdParameter.MAP: "kPa",
            ObdParameter.MAF: "g/s",
            ObdParameter.VOLTAGE: "V",
        }
        return units.get(self.parameter, "unknown")

    def to_dict(self) -> dict:
        """
        @brief Konwertuje odczyt do słownika (przydatne przy JSON).
        @return Słownik z polami: parameter, value, unit, source, timestamp.
        """
        return {
            "parameter": self.parameter.value,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }


class ObdInterface:
    """
    @brief Główna klasa odpowiedzialna za komunikację z adapterem ELM327.
    @details Zarządza cyklem życia połączenia, konfiguruje parametry odczytu
             oraz dostarcza znormalizowane wartości do reszty systemu.
             W przypadku braku adaptera przechodzi w tryb symulacji.

    ## Przykład użycia:

    @code{.py}
    interface = ObdInterface()
    interface.connect()
    readings = interface.read_all()
    for r in readings:
        print(r.to_dict())
    interface.disconnect()
    @endcode
    """

    def __init__(self, port: Optional[str] = None) -> None:
        """
        @brief Inicjalizuje interfejs OBD.
        @param port  Ścieżka portu szeregowego (np. /dev/ttyUSB0).
                     Jeśli None, python-obd próbuje autodetekcję.
        """
        self.port = port
        self.connection: Optional[obd.OBD] = None

    def connect(self) -> bool:
        """
        @brief Nawązuje połączenie z adapterem ELM327.
        @details Próbuje połączyę się przez bibliotekę python-obd.
                 Jeśli biblioteka nie jest dostępna – przechodzi w tryb symulacji.
                 @n **Algorytm**: Wywołuje obd.OBD(port) z domyślną
                 szybkością transmisji (38400 baud). W przypadku niepowodzenia
                 zapisuje ostrzeżenie i kontynuuje w trybie symulowanym.

        @return True jeśli połączenie nawązane (lub symulacja), False w p.p.
        """
        if not OBD_AVAILABLE:
            logger.warning("python-obd not available – running in simulation mode.")
            return True

        try:
            self.connection = obd.OBD(self.port)
            if self.connection.is_connected():
                logger.info("OBD connection established on port %s", self.port)
                return True
            else:
                logger.warning("OBD connection failed – running in simulation mode.")
                return True
        except Exception as exc:
            logger.error("OBD error: %s – simulation mode.", exc)
            return True

    def disconnect(self) -> None:
        """
        @brief Zamyka połączenie z adapterem OBD.
        @details Wywołuje close() na aktywnym połączeniu, jeśli istnieje.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("OBD connection closed.")

    def read_parameter(self, param: ObdParameter) -> ObdReading:
        """
        @brief Odczytuje pojedynczy parametr przez OBD.
        @details Używa python-obd do wysłania zapytania PID. W trybie symulacji
                 zwraca losową wartość z przedziału realistycznego.
                 Wartości są walidowane: None oznacza błąd odczytu.

        ## Mapowanie parametrów na wartości symulowane:
        | Parametr        | Zakres symulacji |
        |-----------------|-------------------|
        | RPM             | 700 – 6500       |
        | COOLANT_TEMP    | 70 – 110         |
        | MAP             | 20 – 250         |
        | MAF             | 3 – 40           |
        | VOLTAGE         | 11.5 – 14.8      |

        @param param  Parametr OBD do odczytania.
        @return Obiekt ObdReading z wartością (lub None, gdy błąd).
        """
        import random

        command_name = PID_MAP.get(param)

        if OBD_AVAILABLE and self.connection and self.connection.is_connected():
            response = self.connection.query(obd.commands[command_name])
            raw_value = response.value.magnitude if response.value else None
        else:
            simulation_ranges: dict[ObdParameter, tuple[float, float]] = {
                ObdParameter.RPM: (700.0, 6500.0),
                ObdParameter.COOLANT_TEMP: (70.0, 110.0),
                ObdParameter.MAP: (20.0, 250.0),
                ObdParameter.MAF: (3.0, 40.0),
                ObdParameter.VOLTAGE: (11.5, 14.8),
            }
            lo, hi = simulation_ranges.get(param, (0.0, 100.0))
            raw_value = round(random.uniform(lo, hi), 2)

        return ObdReading(param, raw_value)

    def read_all(self) -> list[ObdReading]:
        """
        @brief Odczytuje wszystkie skonfigurowane parametry OBD.
        @details Iteruje po wszystkich elementach ObdParameter i zwraca
                 listę znormalizowanych odczytów.
        @return Lista obiektów ObdReading.

        @note Kolejność odczytów odpowiada kolejności w enumeracji ObdParameter.
        """
        return [self.read_parameter(param) for param in ObdParameter]
