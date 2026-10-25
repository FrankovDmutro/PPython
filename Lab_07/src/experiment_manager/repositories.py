"""Repository pattern implementations for researchers and experiments."""

from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from experiment_manager.models import Experiment, Researcher


class ResearcherRepository:
    """Persistence repository for Researcher entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, name: str, department: str) -> Researcher:
        """Create and persist a new researcher."""
        researcher = Researcher(name=name.strip(), department=department.strip())
        self.session.add(researcher)
        self.session.flush()
        return researcher

    def get_by_id(self, researcher_id: int) -> Researcher | None:
        """Fetch researcher by primary key id."""
        return self.session.get(Researcher, researcher_id)

    def get_by_name(self, name: str) -> Researcher | None:
        """Fetch researcher by unique name."""
        stmt = select(Researcher).where(Researcher.name == name.strip())
        return self.session.scalars(stmt).first()

    def list_all(self) -> list[Researcher]:
        """Return all registered researchers."""
        stmt = select(Researcher).order_by(Researcher.name)
        return list(self.session.scalars(stmt).all())

    def update(self, researcher_id: int, department: str | None = None) -> Researcher | None:
        """Update researcher attributes."""
        researcher = self.get_by_id(researcher_id)
        if researcher is None:
            return None
        if department is not None:
            researcher.department = department.strip()
        self.session.flush()
        return researcher

    def delete(self, researcher_id: int) -> bool:
        """Delete researcher by id. Cascades to experiments."""
        researcher = self.get_by_id(researcher_id)
        if researcher is None:
            return False
        self.session.delete(researcher)
        self.session.flush()
        return True


class ExperimentRepository:
    """Persistence repository for Experiment entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        title: str,
        researcher_id: int,
        parameter: str,
        result: float,
        date: str,
        notes: str | None = None,
    ) -> Experiment:
        """Create and persist a new scientific experiment."""
        experiment = Experiment(
            title=title.strip(),
            researcher_id=researcher_id,
            parameter=parameter.strip().lower(),
            result=float(result),
            date=date.strip(),
            notes=notes.strip() if notes else None,
        )
        self.session.add(experiment)
        self.session.flush()
        return experiment

    def get_by_id(self, experiment_id: int) -> Experiment | None:
        """Fetch experiment by id."""
        return self.session.get(Experiment, experiment_id)

    def list_all(self, order_by_date: bool = False, ascending: bool = True) -> list[Experiment]:
        """List all experiments with optional sorting by date."""
        stmt = select(Experiment)
        if order_by_date:
            stmt = stmt.order_by(Experiment.date.asc() if ascending else Experiment.date.desc())
        else:
            stmt = stmt.order_by(Experiment.id.asc())
        return list(self.session.scalars(stmt).all())

    def find_by_researcher_name(self, researcher_name: str) -> list[Experiment]:
        """Find experiments conducted by researcher (via JOIN)."""
        stmt = (
            select(Experiment)
            .join(Experiment.researcher)
            .where(Researcher.name == researcher_name.strip())
            .order_by(Experiment.date.asc())
        )
        return list(self.session.scalars(stmt).all())

    def find_by_range(
        self,
        min_val: float,
        max_val: float,
        parameter: str | None = None,
    ) -> list[Experiment]:
        """Filter experiments with result in [min_val, max_val] interval."""
        stmt = select(Experiment).where(
            Experiment.result >= min_val,
            Experiment.result <= max_val,
        )
        if parameter is not None:
            stmt = stmt.where(Experiment.parameter == parameter.strip().lower())
        stmt = stmt.order_by(Experiment.result.asc())
        return list(self.session.scalars(stmt).all())

    def update(
        self,
        experiment_id: int,
        result: float | None = None,
        notes: str | None = None,
    ) -> Experiment | None:
        """Update result or notes of an experiment."""
        exp = self.get_by_id(experiment_id)
        if exp is None:
            return None
        if result is not None:
            exp.result = float(result)
        if notes is not None:
            exp.notes = notes.strip()
        self.session.flush()
        return exp

    def delete(self, experiment_id: int) -> bool:
        """Delete an experiment by id."""
        exp = self.get_by_id(experiment_id)
        if exp is None:
            return False
        self.session.delete(exp)
        self.session.flush()
        return True

    def get_aggregates(self, parameter: str | None = None) -> dict[str, float]:
        """Calculate SQL aggregate metrics: COUNT, AVG, MIN, MAX."""
        stmt = select(
            func.count(Experiment.id).label("count"),
            func.coalesce(func.avg(Experiment.result), 0.0).label("avg"),
            func.coalesce(func.min(Experiment.result), 0.0).label("min"),
            func.coalesce(func.max(Experiment.result), 0.0).label("max"),
        )
        if parameter is not None:
            stmt = stmt.where(Experiment.parameter == parameter.strip().lower())

        row = self.session.execute(stmt).one()
        return {
            "count": float(row.count),
            "average": float(row.avg),
            "min": float(row.min),
            "max": float(row.max),
        }
