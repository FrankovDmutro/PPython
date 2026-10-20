from typing import NotRequired, TypedDict


class ExperimentPayload(TypedDict):
    """External structured payload representing incoming experiment data."""

    id: int
    title: str
    parameter: str
    value: float
    unit: str
    researcher_name: str
    researcher_email: str
    calibration_offset: NotRequired[float]