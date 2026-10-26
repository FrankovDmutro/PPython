"""Production Scientific Experiments Registry Package (Lab 10, Variant 15)."""

__version__ = "1.0.0"

from .api import app
from .config import Settings, get_settings
from .database import get_db, init_db
from .models import Experiment, Researcher
from .repositories import ExperimentRepository, ResearcherRepository
from .services import ExperimentRegistryService

__all__ = [
    "__version__",
    "Settings",
    "get_settings",
    "app",
    "get_db",
    "init_db",
    "Researcher",
    "Experiment",
    "ResearcherRepository",
    "ExperimentRepository",
    "ExperimentRegistryService",
]
