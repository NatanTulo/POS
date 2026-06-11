"""
@file test_obd.py
@brief Testy jednostkowe dla interfejsu OBD.
@details Sprawdza konfigurację, jednostki oraz wartości zwracane w trybie symulacji.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""

from backend.obd.interface import ObdInterface, ObdParameter, ObdReading


def test_obd_reading_units():
    """
    @brief Weryfikuje poprawne przypisanie jednostek do parametrów OBD.
    """
    reading_rpm = ObdReading(ObdParameter.RPM, 2000.0)
    assert reading_rpm.unit == "rpm"

    reading_temp = ObdReading(ObdParameter.COOLANT_TEMP, 90.0)
    assert reading_temp.unit == "°C"

    reading_voltage = ObdReading(ObdParameter.VOLTAGE, 14.1)
    assert reading_voltage.unit == "V"


def test_obd_simulation_values():
    """
    @brief Weryfikuje, czy wartości symulowane mieszczą się w dopuszczalnych zakresach.
    """
    interface = ObdInterface()
    assert interface.connect() is True

    # Test RPM simulation
    rpm_reading = interface.read_parameter(ObdParameter.RPM)
    assert rpm_reading.parameter == ObdParameter.RPM
    assert rpm_reading.value >= 700.0 and rpm_reading.value <= 6500.0
    assert rpm_reading.source == "obd"

    # Test Coolant Temp simulation
    temp_reading = interface.read_parameter(ObdParameter.COOLANT_TEMP)
    assert temp_reading.value >= 70.0 and temp_reading.value <= 110.0

    # Test all readings list
    all_readings = interface.read_all()
    assert len(all_readings) == len(ObdParameter)
