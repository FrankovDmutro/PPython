"""Unit tests for validation logic, parametrization, and boundary testing."""

import pytest

from experiment_tracker.exceptions import ValidationError
from experiment_tracker.validators import (
    validate_iso_date,
    validate_measurement_value,
    validate_parameter,
    validate_unit,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "raw_param, expected",
    [
        ("temperature", "temperature"),
        ("TEMPERATURE", "temperature"),
        ("  pressure  ", "pressure"),
        ("voltage", "voltage"),
        ("current", "current"),
        ("humidity", "humidity"),
        ("radiation", "radiation"),
    ],
    ids=[
        "temp_lower",
        "temp_upper",
        "pressure_whitespace",
        "voltage_exact",
        "current_exact",
        "humidity_exact",
        "radiation_exact",
    ],
)
def test_validate_parameter_valid(raw_param: str, expected: str) -> None:
    """Test valid parameter names with different casing and whitespace."""
    assert validate_parameter(raw_param) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "invalid_param",
    ["", "   ", "quantum_flux", "dark_matter", "velocity"],
    ids=["empty", "spaces", "unknown_param_1", "unknown_param_2", "unsupported_param"],
)
def test_validate_parameter_invalid(invalid_param: str) -> None:
    """Test that invalid parameters raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        validate_parameter(invalid_param)
    assert exc_info.value.field == "parameter"


@pytest.mark.unit
@pytest.mark.parametrize(
    "unit, expected",
    [
        ("celsius", "celsius"),
        ("KELVIN", "kelvin"),
        ("pascal", "pascal"),
        ("bar", "bar"),
        ("volt", "volt"),
        ("ampere", "ampere"),
        ("percent", "percent"),
        ("sievert", "sievert"),
    ],
    ids=["celsius", "kelvin", "pascal", "bar", "volt", "ampere", "percent", "sievert"],
)
def test_validate_unit_valid(unit: str, expected: str) -> None:
    """Test valid measurement units."""
    assert validate_unit(unit) == expected


@pytest.mark.unit
def test_validate_unit_invalid() -> None:
    """Test invalid measurement unit raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        validate_unit("inches")
    assert exc_info.value.field == "unit"
    assert "Unsupported measurement unit" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, parameter, expected",
    [
        (25.0, "temperature", 25.0),
        ("101325", "pressure", 101325.0),
        (3.3, "voltage", 3.3),
        (50.0, "humidity", 50.0),
    ],
    ids=["temp_float", "pressure_str_num", "voltage_float", "humidity_float"],
)
def test_validate_measurement_value_normal(value: object, parameter: str, expected: float) -> None:
    """Test valid measurement values convert to float."""
    result = validate_measurement_value(value, parameter)
    assert result == pytest.approx(expected)


@pytest.mark.unit
@pytest.mark.parametrize(
    "boundary_val, should_pass",
    [
        (-273.15, True),   # Absolute zero: exactly at lower boundary
        (-273.1501, False), # Just below absolute zero
        (5000.0, True),    # Exactly at upper boundary
        (5000.01, False),  # Just above upper boundary
    ],
    ids=["exact_abs_zero", "below_abs_zero", "exact_max_temp", "above_max_temp"],
)
def test_temperature_boundary_testing(boundary_val: float, should_pass: bool) -> None:
    """Boundary testing for temperature physical limits [-273.15, 5000.0]."""
    if should_pass:
        res = validate_measurement_value(boundary_val, "temperature")
        assert res == pytest.approx(boundary_val)
    else:
        with pytest.raises(ValidationError) as exc_info:
            validate_measurement_value(boundary_val, "temperature")
        assert "outside boundary limits" in str(exc_info.value)
        assert exc_info.value.field == "value"


@pytest.mark.unit
def test_validate_measurement_non_numeric() -> None:
    """Test non-numeric value conversion failure."""
    with pytest.raises(ValidationError) as exc_info:
        validate_measurement_value("not_a_number", "temperature")
    assert "must be numeric" in str(exc_info.value)
    assert exc_info.value.__cause__ is not None


@pytest.mark.unit
def test_validate_iso_date_valid() -> None:
    """Test valid ISO date parsing."""
    assert validate_iso_date("2026-04-15") == "2026-04-15"


@pytest.mark.unit
def test_validate_iso_date_invalid() -> None:
    """Test malformed date string raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        validate_iso_date("15/04/2026")
    assert "Invalid ISO date format" in str(exc_info.value)
