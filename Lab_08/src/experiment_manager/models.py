"""SQLAlchemy 2.0 ORM models for scientific experiments tracking."""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class for ORM entities."""
    pass


class Researcher(Base):
    """Researcher domain model."""

    __tablename__ = "researchers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    experiments: Mapped[List["Experiment"]] = relationship(
        "Experiment",
        back_populates="researcher",
        cascade="all, delete-orphan",
        order_by="Experiment.date.desc()",
    )

    def __repr__(self) -> str:
        return f"<Researcher(id={self.id}, name='{self.name}', department='{self.department}')>"


class Experiment(Base):
    """Scientific experiment record model."""

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    parameter: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    result: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    researcher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("researchers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    researcher: Mapped[Researcher] = relationship("Researcher", back_populates="experiments")

    def __repr__(self) -> str:
        return (
            f"<Experiment(id={self.id}, title='{self.title}', "
            f"parameter='{self.parameter}', result={self.result}, date='{self.date}')>"
        )
