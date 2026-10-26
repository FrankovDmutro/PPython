"""Pydantic v2 schemas for request validation, serialization, and health status."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

# ==================== Health Response ====================


class HealthResponse(BaseModel):
    """Schema for /health status endpoint."""

    status: str = Field(default="ok", description="Service operational status")
    app_name: str = Field(description="Name of running application")
    environment: str = Field(description="Active runtime environment")
    version: str = Field(description="Application semantic version")
    database: str = Field(description="Database connectivity status")


# ==================== Researcher Schemas ====================


class ResearcherBase(BaseModel):
    """Base schema for researcher data."""

    name: str = Field(..., min_length=2, max_length=100, description="Full name of researcher")
    department: str = Field(..., min_length=2, max_length=100, description="Department name")

    @field_validator("name", "department")
    @classmethod
    def not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or contain only whitespace")
        return stripped


class ResearcherCreate(ResearcherBase):
    """Schema for researcher creation."""

    pass


class ResearcherResponse(ResearcherBase):
    """Schema for researcher responses."""

    id: int
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Experiment Schemas ====================


class ExperimentBase(BaseModel):
    """Base schema for scientific experiment data."""

    title: str = Field(..., min_length=3, max_length=200, description="Title of experiment")
    parameter: str = Field(..., min_length=1, max_length=100, description="Measured parameter name")
    result: float = Field(..., description="Numerical measured result value")
    date: dt.date = Field(..., description="Date of the experiment (YYYY-MM-DD)")
    notes: str | None = Field(None, max_length=1000, description="Additional experiment notes")

    @field_validator("title", "parameter")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or contain only whitespace")
        return stripped

    @field_validator("result")
    @classmethod
    def validate_result_physical_bounds(cls, v: float, info: ValidationInfo) -> float:
        param = info.data.get("parameter", "") if info.data else ""
        if "температура" in param.lower() and v < -273.15:
            raise ValueError(f"Temperature cannot be below absolute zero (-273.15 C), got {v}")
        return v


class ExperimentCreate(ExperimentBase):
    """Schema for experiment creation request."""

    researcher_id: int = Field(..., gt=0, description="ID of associated researcher")


class ExperimentUpdate(BaseModel):
    """Schema for updating experiment fields."""

    title: str | None = Field(None, min_length=3, max_length=200)
    parameter: str | None = Field(None, min_length=1, max_length=100)
    result: float | None = None
    date: dt.date | None = None
    notes: str | None = Field(None, max_length=1000)

    @field_validator("title", "parameter")
    @classmethod
    def text_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Field cannot be whitespace")
            return stripped
        return v


class ExperimentResponse(ExperimentBase):
    """Schema for experiment response."""

    id: int
    researcher_id: int

    model_config = ConfigDict(from_attributes=True)


# ==================== Statistics Schemas ====================


class StatisticsResponse(BaseModel):
    """Statistical summary of experiments."""

    count: int = Field(..., description="Total count of measurements")
    mean: float = Field(..., description="Average result value")
    min: float = Field(..., description="Minimum measured result")
    max: float = Field(..., description="Maximum measured result")
    std_dev: float = Field(default=0.0, description="Standard deviation")


class ResearcherStatisticsResponse(BaseModel):
    """Statistics per researcher."""

    researcher_id: int
    researcher_name: str
    statistics: StatisticsResponse
