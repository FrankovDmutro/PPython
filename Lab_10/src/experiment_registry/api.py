"""FastAPI RESTful web service for scientific experiments registry."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .database import get_db, init_db
from .logging_config import setup_logging
from .schemas import (
    ExperimentCreate,
    ExperimentResponse,
    HealthResponse,
    ResearcherCreate,
    ResearcherResponse,
    ResearcherStatisticsResponse,
    StatisticsResponse,
)
from .services import ExperimentRegistryService

logger = logging.getLogger("experiment_registry.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing database initialization and background resources."""
    settings = get_settings()
    setup_logging(settings)
    logger.info("Starting up %s in %s mode", settings.app_name, settings.environment)
    init_db()
    yield
    logger.info("Shutting down %s", settings.app_name)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Production-grade RESTful API for scientific experiment data tracking, "
        "measurements auditing, and analytical statistics. Laboratory Work 10, Variant 15."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_service(db: Session = Depends(get_db)) -> ExperimentRegistryService:
    """Dependency provider for business registry service."""
    return ExperimentRegistryService(db)


# ==================== Health Endpoint ====================


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    tags=["Observability"],
)
def health_check(
    db: Session = Depends(get_db),
    cfg: Settings = Depends(get_settings),
) -> HealthResponse:
    """Operational health status verifying database connectivity and configuration."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        logger.error("Database health check failed: %s", exc)
        db_status = f"unhealthy: {exc}"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        app_name=cfg.app_name,
        environment=cfg.environment,
        version="1.0.0",
        database=db_status,
    )


# ==================== Researchers Endpoints ====================


@app.get(
    "/researchers",
    response_model=list[ResearcherResponse],
    summary="List Researchers",
    tags=["Researchers"],
)
def list_researchers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ExperimentRegistryService = Depends(get_service),
):
    return service.list_researchers(skip=skip, limit=limit)


@app.post(
    "/researchers",
    response_model=ResearcherResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Researcher",
    tags=["Researchers"],
)
def create_researcher(
    payload: ResearcherCreate,
    service: ExperimentRegistryService = Depends(get_service),
):
    return service.create_researcher(payload)


@app.get(
    "/researchers/{id}",
    response_model=ResearcherResponse,
    summary="Get Researcher by ID",
    tags=["Researchers"],
)
def get_researcher(
    id: int = Path(..., gt=0),
    service: ExperimentRegistryService = Depends(get_service),
):
    researcher = service.get_researcher(id)
    if not researcher:
        raise HTTPException(status_code=404, detail=f"Researcher with ID {id} not found")
    return researcher


@app.delete(
    "/researchers/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Researcher",
    tags=["Researchers"],
)
def delete_researcher(
    id: int = Path(..., gt=0),
    service: ExperimentRegistryService = Depends(get_service),
):
    success = service.delete_researcher(id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Researcher with ID {id} not found")


@app.get(
    "/researchers/{id}/experiments",
    response_model=list[ExperimentResponse],
    summary="List Experiments of Researcher",
    tags=["Researchers"],
)
def list_researcher_experiments(
    id: int = Path(..., gt=0),
    service: ExperimentRegistryService = Depends(get_service),
):
    researcher = service.get_researcher(id)
    if not researcher:
        raise HTTPException(status_code=404, detail=f"Researcher with ID {id} not found")
    return service.list_experiments(researcher_id=id, limit=100)


@app.get(
    "/researchers/{id}/statistics",
    response_model=ResearcherStatisticsResponse,
    summary="Get Researcher Aggregate Statistics",
    tags=["Researchers"],
)
def get_researcher_statistics(
    id: int = Path(..., gt=0),
    service: ExperimentRegistryService = Depends(get_service),
):
    res_stats = service.get_researcher_statistics(id)
    if not res_stats:
        raise HTTPException(status_code=404, detail=f"Researcher with ID {id} not found")
    return res_stats


# ==================== Experiments Endpoints ====================


@app.get(
    "/experiments",
    response_model=list[ExperimentResponse],
    summary="List Experiments",
    tags=["Experiments"],
)
def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    researcher_id: int | None = Query(None, gt=0),
    parameter: str | None = Query(None),
    min_result: float | None = Query(None),
    max_result: float | None = Query(None),
    sort_by_date: str = Query("desc", pattern="^(asc|desc)$"),
    service: ExperimentRegistryService = Depends(get_service),
):
    return service.list_experiments(
        skip=skip,
        limit=limit,
        researcher_id=researcher_id,
        parameter=parameter,
        min_result=min_result,
        max_result=max_result,
        sort_by_date=sort_by_date,
    )


@app.post(
    "/experiments",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record New Experiment",
    tags=["Experiments"],
)
def create_experiment(
    payload: ExperimentCreate,
    service: ExperimentRegistryService = Depends(get_service),
):
    try:
        return service.create_experiment(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get(
    "/experiments/statistics",
    response_model=StatisticsResponse,
    summary="Get Experiments Global Statistics",
    tags=["Experiments"],
)
def get_global_statistics(
    parameter: str | None = Query(None),
    researcher_id: int | None = Query(None, gt=0),
    service: ExperimentRegistryService = Depends(get_service),
):
    return service.get_statistics(parameter=parameter, researcher_id=researcher_id)


@app.get(
    "/experiments/{id}",
    response_model=ExperimentResponse,
    summary="Get Experiment Details",
    tags=["Experiments"],
)
def get_experiment(
    id: int = Path(..., gt=0),
    service: ExperimentRegistryService = Depends(get_service),
):
    exp = service.get_experiment(id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment with ID {id} not found")
    return exp


@app.delete(
    "/experiments/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Experiment",
    tags=["Experiments"],
)
def delete_experiment(
    id: int = Path(..., gt=0),
    service: ExperimentRegistryService = Depends(get_service),
):
    success = service.delete_experiment(id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Experiment with ID {id} not found")
