"""
@file test_sensors.py
@brief Testy jednostkowe dla interfejsu czujników zewnętrznych.
@details Sprawdza konfigurację i symulację czujników dodatkowych (temperatura oleju, ciśnienie paliwa).

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""

from backend.sensors.interface import ExternalSensorInterface


def test_sensors_simulation_values():
    """
    @brief Weryfikuje poprawność generowania danych z czujników zewnętrznych.
    """
    interface = ExternalSensorInterface()

    # Read all sensors
    readings = interface.read_all()
    assert len(readings) == 2

    # Check oil_temp
    oil_temp = next((r for r in readings if r.sensor_name == "oil_temp"), None)
    assert oil_temp is not None
    assert oil_temp.unit == "°C"
    assert oil_temp.value >= 20.0 and oil_temp.value <= 150.0
    assert oil_temp.source == "external"

    # Check fuel_pressure
    fuel_pressure = next((r for r in readings if r.sensor_name == "fuel_pressure"), None)
    assert fuel_pressure is not None
    assert fuel_pressure.unit == "bar"
    assert fuel_pressure.value >= 0.5 and fuel_pressure.value <= 6.0


def test_read_single_sensor():
    """
    @brief Testuje odczyt pojedynczego czujnika po nazwie.
    """
    interface = ExternalSensorInterface()

    # Valid sensor
    reading = interface.read_sensor("oil_temp")
    assert reading is not None
    assert reading.sensor_name == "oil_temp"

    # Invalid sensor
    reading_invalid = interface.read_sensor("non_existent_sensor")
    assert reading_invalid is None
