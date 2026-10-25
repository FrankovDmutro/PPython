"""SQLAlchemy ORM models for researchers and experiments (Variant 15)."""

from typing import Any
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from experiment_manager.database import Base


class Researcher(Base):
    """Researcher entity representing the scientist conducting experiments."""

    __tablename__ = "researchers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False)

    # One-to-many relationship: One researcher has many experiments
    experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment",
        back_populates="researcher",
        cascade="all, delete-orphan",
        order_by="Experiment.id",
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize researcher to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "experiments_count": len(self.experiments),
        }

    def __repr__(self) -> str:
        return f"<Researcher(id={self.id}, name='{self.name}', department='{self.department}')>"


class Experiment(Base):
    """Experiment entity storing scientific measurements and physical parameters."""

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    researcher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("researchers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parameter: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    result: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # Format: YYYY-MM-DD
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Field managed by migrations

    # Relationship back to Researcher
    researcher: Mapped["Researcher"] = relationship("Researcher", back_populates="experiments")

    def to_dict(self) -> dict[str, Any]:
        """Serialize experiment to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "researcher_id": self.researcher_id,
            "researcher_name": self.researcher.name if self.researcher else None,
            "parameter": self.parameter,
            "result": self.result,
            "date": self.date,
            "notes": self.notes,
        }

    def __repr__(self) -> str:
        return (
            f"<Experiment(id={self.id}, title='{self.title}', parameter='{self.parameter}', "
            f"result={self.result}, date='{self.date}')>"
        )
