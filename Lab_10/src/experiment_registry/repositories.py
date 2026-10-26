"""Repository pattern implementation for Researcher and Experiment entities."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Experiment, Researcher
from .schemas import ExperimentCreate, ExperimentUpdate, ResearcherCreate


class ResearcherRepository:
    """Persistence repository for Researcher entity."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, researcher_id: int) -> Researcher | None:
        """Fetch a researcher by ID."""
        return self.session.get(Researcher, researcher_id)

    def get_all(self, skip: int = 0, limit: int = 50) -> list[Researcher]:
        """Fetch researchers list with pagination."""
        stmt = select(Researcher).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

    def create(self, data: ResearcherCreate) -> Researcher:
        """Create a new researcher record."""
        researcher = Researcher(name=data.name, department=data.department)
        self.session.add(researcher)
        self.session.commit()
        self.session.refresh(researcher)
        return researcher

    def delete(self, researcher_id: int) -> bool:
        """Delete a researcher and cascade delete associated experiments."""
        researcher = self.get_by_id(researcher_id)
        if not researcher:
            return False
        self.session.delete(researcher)
        self.session.commit()
        return True


class ExperimentRepository:
    """Persistence repository for Experiment entity."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, experiment_id: int) -> Experiment | None:
        """Fetch an experiment by ID."""
        return self.session.get(Experiment, experiment_id)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        researcher_id: int | None = None,
        parameter: str | None = None,
        min_result: float | None = None,
        max_result: float | None = None,
        sort_by_date: str = "desc",
    ) -> list[Experiment]:
        """Fetch experiments with rich filtering, date ordering, and pagination."""
        stmt = select(Experiment)

        if researcher_id is not None:
            stmt = stmt.where(Experiment.researcher_id == researcher_id)
        if parameter:
            stmt = stmt.where(Experiment.parameter.ilike(f"%{parameter}%"))
        if min_result is not None:
            stmt = stmt.where(Experiment.result >= min_result)
        if max_result is not None:
            stmt = stmt.where(Experiment.result <= max_result)

        if sort_by_date.lower() == "asc":
            stmt = stmt.order_by(Experiment.date.asc(), Experiment.id.asc())
        else:
            stmt = stmt.order_by(Experiment.date.desc(), Experiment.id.desc())

        stmt = stmt.offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

    def get_by_researcher(self, researcher_id: int) -> list[Experiment]:
        """Fetch all experiments for a specific researcher."""
        stmt = (
            select(Experiment)
            .where(Experiment.researcher_id == researcher_id)
            .order_by(Experiment.date.desc())
        )
        return list(self.session.scalars(stmt).all())

    def create(self, data: ExperimentCreate) -> Experiment:
        """Create a new experiment record."""
        experiment = Experiment(
            title=data.title,
            parameter=data.parameter,
            result=data.result,
            date=data.date,
            notes=data.notes,
            researcher_id=data.researcher_id,
        )
        self.session.add(experiment)
        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def update(self, experiment_id: int, update_data: ExperimentUpdate) -> Experiment | None:
        """Partially update an existing experiment."""
        experiment = self.get_by_id(experiment_id)
        if not experiment:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(experiment, field, value)

        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def delete(self, experiment_id: int) -> bool:
        """Delete an experiment by ID."""
        experiment = self.get_by_id(experiment_id)
        if not experiment:
            return False
        self.session.delete(experiment)
        self.session.commit()
        return True

    def get_statistics(
        self, parameter: str | None = None, researcher_id: int | None = None
    ) -> tuple[int, float | None, float | None, float | None]:
        """Compute COUNT, AVG, MIN, MAX using SQL aggregate functions."""
        stmt = select(
            func.count(Experiment.id),
            func.avg(Experiment.result),
            func.min(Experiment.result),
            func.max(Experiment.result),
        )
        if parameter:
            stmt = stmt.where(Experiment.parameter.ilike(f"%{parameter}%"))
        if researcher_id is not None:
            stmt = stmt.where(Experiment.researcher_id == researcher_id)

        row = self.session.execute(stmt).first()
        if not row:
            return 0, None, None, None
        count, avg_res, min_res, max_res = row
        avg_rounded = round(float(avg_res), 2) if avg_res is not None else None
        min_val = round(float(min_res), 2) if min_res is not None else None
        max_val = round(float(max_res), 2) if max_res is not None else None
        return int(count), avg_rounded, min_val, max_val
