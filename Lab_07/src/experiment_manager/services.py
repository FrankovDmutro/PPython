"""Service layer orchestrating business logic and transactional database operations."""

from typing import Any
from sqlalchemy.orm import Session

from experiment_manager.models import Experiment, Researcher
from experiment_manager.repositories import ExperimentRepository, ResearcherRepository


class ExperimentService:
    """Business service coordinating researcher and experiment persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.researcher_repo = ResearcherRepository(session)
        self.experiment_repo = ExperimentRepository(session)

    def register_researcher(self, name: str, department: str) -> Researcher:
        """Find existing researcher or create a new one."""
        existing = self.researcher_repo.get_by_name(name)
        if existing:
            return existing
        return self.researcher_repo.create(name, department)

    def record_experiment(
        self,
        title: str,
        researcher_name: str,
        parameter: str,
        result: float,
        date: str,
        notes: str | None = None,
        department: str = "General Physics",
    ) -> Experiment:
        """Create and associate an experiment with a researcher."""
        researcher = self.register_researcher(researcher_name, department)
        return self.experiment_repo.create(
            title=title,
            researcher_id=researcher.id,
            parameter=parameter,
            result=result,
            date=date,
            notes=notes,
        )

    def get_experiment_statistics(self, parameter: str | None = None) -> dict[str, float]:
        """Fetch statistical metrics (COUNT, AVG, MIN, MAX) via repository."""
        return self.experiment_repo.get_aggregates(parameter)

    def filter_experiments(
        self,
        min_result: float,
        max_result: float,
        parameter: str | None = None,
    ) -> list[Experiment]:
        """Find experiments within specified result interval."""
        return self.experiment_repo.find_by_range(min_result, max_result, parameter)

    def batch_add_experiments_transactional(
        self,
        records: list[dict[str, Any]],
    ) -> list[Experiment]:
        """Execute atomic batch insertion of experiments with rollback on error.

        Guarantees ACID Atomicity: either all records are persisted or none are.
        """
        created_experiments: list[Experiment] = []
        try:
            # We use a nested transaction (savepoint) or explicit rollback
            for item in records:
                res_val = float(item["result"])
                param_name = str(item["parameter"]).strip().lower()

                # Domain validation constraint
                if param_name == "temperature" and res_val < -273.15:
                    raise ValueError(f"Physical constraint violation: Temperature {res_val} < -273.15 C")
                if param_name == "pressure" and res_val < 0.0:
                    raise ValueError(f"Physical constraint violation: Negative pressure {res_val} Pa")

                researcher = self.register_researcher(
                    name=item["researcher_name"],
                    department=item.get("department", "General Physics"),
                )

                exp = self.experiment_repo.create(
                    title=item["title"],
                    researcher_id=researcher.id,
                    parameter=param_name,
                    result=res_val,
                    date=item["date"],
                    notes=item.get("notes"),
                )
                created_experiments.append(exp)

            self.session.flush()
            return created_experiments
        except Exception:
            self.session.rollback()
            raise
