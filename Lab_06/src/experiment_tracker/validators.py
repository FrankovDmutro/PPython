"""Validation rules and boundary checks for scientific experiments."""

from datetime import date
from typing import Any

from experiment_tracker.exceptions import ValidationError

ALLOWED_PARAMETERS: frozenset[str] = frozenset({
    "temperature",
    "pressure",
    "voltage",
    "current",
    "humidity",
    "radiation",
})

ALLOWED_UNITS: frozenset[str] = frozenset({
    "celsius",
    "kelvin",
    "pascal",
    "bar",
    "volt",
    "ampere",
    "percent",
    "sievert",
})

DEFAULT_BOUNDS: dict[str, tuple[float, float]] = {
    "temperature": (-273.15, 5000.0),
    "pressure": (0.0, 100_000_000.0),
    "voltage": (-10000.0, 10000.0),
    "current": (-1000.0, 1000.0),
    "humidity": (0.0, 100.0),
    "radiation": (0.0, 1000.0),
}


def validate_parameter(parameter: str) -> str:
    """Validate that the parameter name belongs to the allowed catalog."""
    param = parameter.strip().lower()
    if not param:
        raise ValidationError("Parameter cannot be empty", field="parameter", invalid_value=parameter)
    if param not in ALLOWED_PARAMETERS:
        raise ValidationError(
            f"Unsupported physical parameter '{param}'. Allowed: {sorted(ALLOWED_PARAMETERS)}",
            field="parameter",
            invalid_value=param,
        )
    return param


def validate_unit(unit: str) -> str:
    """Validate that the measurement unit belongs to allowed physical units."""
    u = unit.strip().lower()
    if not u:
        raise ValidationError("Unit cannot be empty", field="unit", invalid_value=unit)
    if u not in ALLOWED_UNITS:
        raise ValidationError(
            f"Unsupported measurement unit '{u}'. Allowed: {sorted(ALLOWED_UNITS)}",
            field="unit",
            invalid_value=u,
        )
    return u


def validate_measurement_value(
    value: Any,
    parameter: str,
    *,
    custom_min: float | None = None,
    custom_max: float | None = None,
) -> float:
    """Validate that the measurement value is numeric and within boundary limits."""
    try:
        val = float(value)
    except (ValueError, TypeError) as err:
        raise ValidationError(
            f"Measurement value must be numeric, got '{value}'",
            field="value",
            invalid_value=value,
        ) from err

    min_b, max_b = DEFAULT_BOUNDS.get(parameter.lower(), (float("-inf"), float("inf")))
    if custom_min is not None:
        min_b = custom_min
    if custom_max is not None:
        max_b = custom_max

    if val < min_b or val > max_b:
        raise ValidationError(
            f"Value {val} is outside boundary limits [{min_b}, {max_b}] for parameter '{parameter}'",
            field="value",
            invalid_value=val,
        )
    return val


def validate_iso_date(date_str: str) -> str:
    """Validate ISO format date (YYYY-MM-DD)."""
    s = str(date_str).strip()
    if not s:
        raise ValidationError("Date string cannot be empty", field="date", invalid_value=date_str)
    try:
        parsed = date.fromisoformat(s)
        return parsed.isoformat()
    except ValueError as err:
        raise ValidationError(
            f"Invalid ISO date format '{s}', expected YYYY-MM-DD",
            field="date",
            invalid_value=s,
        ) from err
