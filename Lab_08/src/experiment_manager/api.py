"""FastAPI REST API application for scientific experiments management (Variant 15)."""

from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from experiment_manager.database import get_db, init_db
from experiment_manager.repositories import ExperimentRepository, ResearcherRepository
from experiment_manager.schemas import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
    ResearcherCreate,
    ResearcherResponse,
    ResearcherStatisticsResponse,
    StatisticsResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown hooks."""
    init_db()
    yield


app = FastAPI(
    title="Scientific Experiments REST API",
    description=(
        "FastAPI RESTful service for scientific research and experiment tracking. "
        "Laboratory Work № 8, Variant 15 (Student: Frankov)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ==================== Dependency Injection Helpers ====================

def get_researcher_repo(db: Session = Depends(get_db)) -> ResearcherRepository:
    return ResearcherRepository(db)


def get_experiment_repo(db: Session = Depends(get_db)) -> ExperimentRepository:
    return ExperimentRepository(db)


# ==================== Researchers Endpoints ====================

@app.get(
    "/researchers",
    response_model=List[ResearcherResponse],
    summary="List all researchers",
    tags=["Researchers"],
)
def list_researchers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max number of records to return"),
    repo: ResearcherRepository = Depends(get_researcher_repo),
):
    """Retrieve researchers with pagination support."""
    return repo.get_all(skip=skip, limit=limit)


@app.post(
    "/researchers",
    response_model=ResearcherResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new researcher",
    tags=["Researchers"],
)
def create_researcher(
    payload: ResearcherCreate,
    repo: ResearcherRepository = Depends(get_researcher_repo),
):
    """Add a new scientific researcher."""
    return repo.create(payload)


@app.get(
    "/researchers/{id}",
    response_model=ResearcherResponse,
    summary="Get researcher by ID",
    tags=["Researchers"],
)
def get_researcher(
    id: int = Path(..., ge=1, description="Researcher primary identifier"),
    repo: ResearcherRepository = Depends(get_researcher_repo),
):
    """Retrieve details of a specific researcher."""
    researcher = repo.get_by_id(id)
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Researcher with ID {id} not found",
        )
    return researcher


@app.delete(
    "/researchers/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete researcher",
    tags=["Researchers"],
)
def delete_researcher(
    id: int = Path(..., ge=1),
    repo: ResearcherRepository = Depends(get_researcher_repo),
):
    """Delete a researcher and cascade delete all their experiment records."""
    success = repo.delete(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Researcher with ID {id} not found",
        )
    return None


@app.get(
    "/researchers/{id}/experiments",
    response_model=List[ExperimentResponse],
    summary="List experiments of a researcher",
    tags=["Researchers", "Experiments"],
)
def get_researcher_experiments(
    id: int = Path(..., ge=1, description="Researcher ID"),
    r_repo: ResearcherRepository = Depends(get_researcher_repo),
    e_repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Fetch all experiments conducted by the specified researcher."""
    researcher = r_repo.get_by_id(id)
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Researcher with ID {id} not found",
        )
    return e_repo.get_by_researcher(id)


@app.get(
    "/researchers/{id}/statistics",
    response_model=ResearcherStatisticsResponse,
    summary="Get aggregated statistics for a specific researcher",
    tags=["Researchers", "Statistics"],
)
def get_researcher_statistics(
    id: int = Path(..., ge=1),
    r_repo: ResearcherRepository = Depends(get_researcher_repo),
    e_repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Compute statistics for an individual researcher (used in async aggregations)."""
    researcher = r_repo.get_by_id(id)
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Researcher with ID {id} not found",
        )
    count, avg_res, min_res, max_res = e_repo.get_statistics(researcher_id=id)
    return ResearcherStatisticsResponse(
        researcher_id=researcher.id,
        researcher_name=researcher.name,
        count=count,
        average=avg_res,
        min=min_res,
        max=max_res,
    )


# ==================== Experiments Endpoints ====================

@app.get(
    "/experiments",
    response_model=List[ExperimentResponse],
    summary="List experiments with filters and ordering",
    tags=["Experiments"],
)
def list_experiments(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    researcher_id: Optional[int] = Query(None, ge=1, description="Filter by researcher ID"),
    parameter: Optional[str] = Query(None, description="Filter by parameter keyword"),
    min_result: Optional[float] = Query(None, description="Minimum result threshold"),
    max_result: Optional[float] = Query(None, description="Maximum result threshold"),
    sort_by_date: str = Query(
        "desc", pattern="^(asc|desc)$", description="Sort by date: 'asc' or 'desc'"
    ),
    repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Retrieve experiments with filtering by result range, parameter, researcher, and date ordering."""
    return repo.get_all(
        skip=skip,
        limit=limit,
        researcher_id=researcher_id,
        parameter=parameter,
        min_result=min_result,
        max_result=max_result,
        sort_by_date=sort_by_date,
    )


@app.get(
    "/experiments/statistics",
    response_model=StatisticsResponse,
    summary="Get global or parameter-specific experiment statistics",
    tags=["Experiments", "Statistics"],
)
def get_experiment_statistics(
    parameter: Optional[str] = Query(None, description="Optional parameter name filter"),
    repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Obtain count, average, minimum, and maximum of measured experiment results."""
    count, avg_res, min_res, max_res = repo.get_statistics(parameter=parameter)
    return StatisticsResponse(
        count=count,
        average=avg_res,
        min=min_res,
        max=max_res,
        parameter=parameter,
    )


@app.get(
    "/experiments/{id}",
    response_model=ExperimentResponse,
    summary="Get experiment by ID",
    tags=["Experiments"],
)
def get_experiment(
    id: int = Path(..., ge=1, description="Experiment primary ID"),
    repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Fetch details of a single experiment by ID."""
    experiment = repo.get_by_id(id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID {id} not found",
        )
    return experiment


@app.post(
    "/experiments",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new experiment",
    tags=["Experiments"],
)
def create_experiment(
    payload: ExperimentCreate,
    r_repo: ResearcherRepository = Depends(get_researcher_repo),
    e_repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Add a new experiment with foreign key validation."""
    researcher = r_repo.get_by_id(payload.researcher_id)
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Associated researcher with ID {payload.researcher_id} does not exist",
        )
    return e_repo.create(payload)


@app.patch(
    "/experiments/{id}",
    response_model=ExperimentResponse,
    summary="Partially update an experiment",
    tags=["Experiments"],
)
def update_experiment(
    id: int = Path(..., ge=1),
    payload: ExperimentUpdate = ...,
    repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Update experiment attributes (result, notes, title, etc.)."""
    updated = repo.update(id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID {id} not found",
        )
    return updated


@app.delete(
    "/experiments/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete experiment",
    tags=["Experiments"],
)
def delete_experiment(
    id: int = Path(..., ge=1),
    repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Delete an experiment by ID."""
    success = repo.delete(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID {id} not found",
        )
    return None
