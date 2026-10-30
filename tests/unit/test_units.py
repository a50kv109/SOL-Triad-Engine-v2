"""
Unit tests for UnitRegistry and dimensional checks.
"""

import pytest
from sol_triad.units import UnitRegistry, DimensionalityError, UnknownUnitError


def test_recognized_dimensions():
    assert UnitRegistry.get_dimension("bar") == "pressure"
    assert UnitRegistry.get_dimension("psi") == "pressure"
    assert UnitRegistry.get_dimension("atm") == "pressure"
    assert UnitRegistry.get_dimension("sec") == "time"
    assert UnitRegistry.get_dimension("ms") == "time"
    assert UnitRegistry.get_dimension("celsius") == "temperature"
    assert UnitRegistry.get_dimension("kelvin") == "temperature"
    assert UnitRegistry.get_dimension("percent") == "ratio"
    assert UnitRegistry.get_dimension("fraction") == "ratio"
    assert UnitRegistry.get_dimension("joule") == "energy"


def test_unknown_units_not_compatible():
    # Anti-bypass test: two unknown units must NOT be compatible
    compat, msg = UnitRegistry.are_compatible("flurps", "glorps")
    assert not compat
    assert "unknown" in msg.lower() or "not recognized" in msg.lower()


def test_asymmetric_unit_specification_fails():
    # Anti-bypass test: one unit missing, one specified must FAIL
    compat, msg = UnitRegistry.are_compatible(None, "bar")
    assert not compat
    assert "asymmetric" in msg.lower() or "missing" in msg.lower()

    compat2, msg2 = UnitRegistry.are_compatible("sec", None)
    assert not compat2


def test_incompatible_dimensions_fail():
    compat, msg = UnitRegistry.are_compatible("bar", "sec")
    assert not compat
    assert "incompatibility" in msg.lower()


def test_unit_conversion_pressure():
    # 1 bar = 100,000 Pa; 1 atm = 101,325 Pa
    val_atm = UnitRegistry.convert(1.0, "bar", "atm")
    assert abs(val_atm - (100000.0 / 101325.0)) < 1e-4

    val_psi = UnitRegistry.convert(1.0, "bar", "psi")
    assert abs(val_psi - 14.50377) < 1e-3


def test_unit_conversion_time():
    assert UnitRegistry.convert(2.5, "sec", "ms") == 2500.0
    assert UnitRegistry.convert(120.0, "sec", "min") == 2.0


def test_unit_conversion_temperature():
    # 0 C = 273.15 K
    assert abs(UnitRegistry.convert(0.0, "celsius", "kelvin") - 273.15) < 1e-4
    assert abs(UnitRegistry.convert(100.0, "celsius", "kelvin") - 373.15) < 1e-4


def test_temperature_delta_conversion_omits_absolute_offset():
    assert UnitRegistry.convert_delta(1.0, "kelvin", "celsius") == 1.0
    assert abs(UnitRegistry.convert_delta(1.0, "fahrenheit", "celsius") - (5.0 / 9.0)) < 1e-12


def test_linear_delta_conversion_matches_absolute_conversion():
    assert UnitRegistry.convert_delta(1.0, "bar", "psi") == UnitRegistry.convert(1.0, "bar", "psi")


def test_unit_conversion_ratio():
    assert UnitRegistry.convert(50.0, "percent", "fraction") == 0.5
    assert UnitRegistry.convert(0.25, "fraction", "percent") == 25.0


def test_conversion_incompatible_dimension_raises():
    with pytest.raises(DimensionalityError):
        UnitRegistry.convert(10.0, "bar", "sec")


def test_conversion_unknown_unit_raises():
    with pytest.raises(UnknownUnitError):
        UnitRegistry.convert(10.0, "unknown_unit", "bar")
