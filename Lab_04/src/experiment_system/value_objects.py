from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeasurementUnit:
    """Immutable Value Object representing an SI or derived measurement unit."""

    symbol: str
    dimension: str

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("Unit symbol cannot be empty.")
        if not self.dimension.strip():
            raise ValueError("Unit dimension cannot be empty.")

    def __str__(self) -> str:
        return self.symbol