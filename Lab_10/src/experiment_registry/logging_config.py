"""Structured production logging configuration."""

from __future__ import annotations

import logging
import sys

from .config import Settings, get_settings


def setup_logging(settings: Settings | None = None) -> logging.Logger:
    """Configure application logging according to environment settings."""
    if settings is None:
        settings = get_settings()

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    log_format = "%(asctime)s [%(levelname)s] [%(name)s] [env=%(environment)s]: %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Add custom extra attribute adapter if needed
    logger = logging.getLogger("experiment_registry")
    logger.setLevel(log_level)
    return logger
