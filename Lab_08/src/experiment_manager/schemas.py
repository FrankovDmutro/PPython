"""Pydantic v2 schemas for request validation and response serialization."""

import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


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
    notes: Optional[str] = Field(None, max_length=1000, description="Additional experiment notes")

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
        if isinstance(param, str) and any(kw in param.lower() for kw in ("temp", "темп")):
            if v < -273.15:
                raise ValueError(f"Temperature {v} °C cannot be below absolute zero (-273.15 °C)")
        return v


class ExperimentCreate(ExperimentBase):
    """Schema for experiment creation."""

    researcher_id: int = Field(..., gt=0, description="Identifier of the associated researcher")


class ExperimentUpdate(BaseModel):
    """Schema for partial update of an experiment."""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    parameter: Optional[str] = Field(None, min_length=1, max_length=100)
    result: Optional[float] = None
    date: Optional[dt.date] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("title", "parameter")
    @classmethod
    def text_not_blank_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Field cannot be empty or contain only whitespace")
            return stripped
        return v

    @field_validator("result")
    @classmethod
    def validate_update_physical_bounds(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        if v is not None:
            param = info.data.get("parameter", "") if info.data else ""
            if isinstance(param, str) and any(kw in param.lower() for kw in ("temp", "темп")):
                if v < -273.15:
                    raise ValueError(f"Temperature {v} °C cannot be below absolute zero (-273.15 °C)")
        return v


class ExperimentResponse(ExperimentBase):
    """Schema for experiment response."""

    id: int
    researcher_id: int

    model_config = ConfigDict(from_attributes=True)


# ==================== Aggregations & Statistics Schemas ====================

class StatisticsResponse(BaseModel):
    """Aggregated numerical statistics schema."""

    count: int = Field(..., description="Total count of experiments")
    average: Optional[float] = Field(None, description="Average result value")
    min: Optional[float] = Field(None, description="Minimum result value")
    max: Optional[float] = Field(None, description="Maximum result value")
    parameter: Optional[str] = Field(None, description="Filtered parameter name if applied")


class ResearcherStatisticsResponse(BaseModel):
    """Per-researcher aggregated statistics."""

    researcher_id: int
    researcher_name: str
    count: int
    average: Optional[float]
    min: Optional[float]
    max: Optional[float]


class ConcurrentStatisticsRequest(BaseModel):
    """Request schema for concurrent batch statistics collection."""

    researcher_ids: List[int] = Field(..., min_length=1, max_length=50)
    max_concurrency: int = Field(3, ge=1, le=20)
    timeout_seconds: float = Field(5.0, gt=0.0, le=60.0)


class BatchStatisticsResponse(BaseModel):
    """Response schema for concurrent statistics aggregation."""

    total_queries: int
    successful_queries: int
    failed_queries: int
    results: List[ResearcherStatisticsResponse]
    duration_seconds: float
