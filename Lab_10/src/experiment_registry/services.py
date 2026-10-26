"""Domain business services, analytics aggregation, and cache management."""

from __future__ import annotations

import math

from sqlalchemy.orm import Session

from .models import Experiment, Researcher
from .repositories import ExperimentRepository, ResearcherRepository
from .schemas import (
    ExperimentCreate,
    ResearcherCreate,
    ResearcherStatisticsResponse,
    StatisticsResponse,
)


class ExperimentRegistryService:
    """High-level business service coordinating repository operations and analytical metrics."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.researcher_repo = ResearcherRepository(session)
        self.experiment_repo = ExperimentRepository(session)
        self._stats_cache: dict[str, StatisticsResponse] = {}

    def get_researcher(self, researcher_id: int) -> Researcher | None:
        return self.researcher_repo.get_by_id(researcher_id)

    def list_researchers(self, skip: int = 0, limit: int = 50) -> list[Researcher]:
        return self.researcher_repo.get_all(skip=skip, limit=limit)

    def create_researcher(self, data: ResearcherCreate) -> Researcher:
        return self.researcher_repo.create(data)

    def delete_researcher(self, researcher_id: int) -> bool:
        self._stats_cache.clear()  # Invalidate cached analytics
        return self.researcher_repo.delete(researcher_id)

    def get_experiment(self, experiment_id: int) -> Experiment | None:
        return self.experiment_repo.get_by_id(experiment_id)

    def list_experiments(
        self,
        skip: int = 0,
        limit: int = 20,
        researcher_id: int | None = None,
        parameter: str | None = None,
        min_result: float | None = None,
        max_result: float | None = None,
        sort_by_date: str = "desc",
    ) -> list[Experiment]:
        return self.experiment_repo.get_all(
            skip=skip,
            limit=limit,
            researcher_id=researcher_id,
            parameter=parameter,
            min_result=min_result,
            max_result=max_result,
            sort_by_date=sort_by_date,
        )

    def create_experiment(self, data: ExperimentCreate) -> Experiment:
        # Validate that researcher exists
        if not self.researcher_repo.get_by_id(data.researcher_id):
            raise ValueError(f"Researcher with id {data.researcher_id} does not exist")
        exp = self.experiment_repo.create(data)
        self._stats_cache.clear()  # Invalidate cached analytics
        return exp

    def delete_experiment(self, experiment_id: int) -> bool:
        success = self.experiment_repo.delete(experiment_id)
        if success:
            self._stats_cache.clear()
        return success

    def get_statistics(
        self,
        parameter: str | None = None,
        researcher_id: int | None = None,
    ) -> StatisticsResponse:
        """Calculate descriptive metrics with cache acceleration."""
        cache_key = f"{parameter}::{researcher_id}"
        if cache_key in self._stats_cache:
            return self._stats_cache[cache_key]

        count, avg_val, min_val, max_val = self.experiment_repo.get_statistics(
            parameter=parameter, researcher_id=researcher_id
        )

        if count == 0 or avg_val is None or min_val is None or max_val is None:
            stats = StatisticsResponse(count=0, mean=0.0, min=0.0, max=0.0, std_dev=0.0)
        else:
            # Calculate standard deviation across matching records
            all_matching = self.experiment_repo.get_all(
                skip=0, limit=10_000, researcher_id=researcher_id, parameter=parameter
            )
            vals = [e.result for e in all_matching]
            mean = avg_val
            variance = sum((x - mean) ** 2 for x in vals) / len(vals) if vals else 0.0
            std_dev = round(math.sqrt(variance), 4)

            stats = StatisticsResponse(
                count=count,
                mean=round(mean, 2),
                min=round(min_val, 2),
                max=round(max_val, 2),
                std_dev=std_dev,
            )

        self._stats_cache[cache_key] = stats
        return stats

    def get_researcher_statistics(self, researcher_id: int) -> ResearcherStatisticsResponse | None:
        researcher = self.researcher_repo.get_by_id(researcher_id)
        if not researcher:
            return None
        stats = self.get_statistics(researcher_id=researcher_id)
        return ResearcherStatisticsResponse(
            researcher_id=researcher.id,
            researcher_name=researcher.name,
            statistics=stats,
        )
