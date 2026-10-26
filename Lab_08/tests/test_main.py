"""Tests for main entrypoint and database initialization."""

import sys
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine
from experiment_manager.database import init_db
from experiment_manager.main import run_server
from experiment_manager.models import Base


def test_init_db():
    """Verify init_db initializes schema properly."""
    engine = create_engine("sqlite:///:memory:")
    init_db(target_engine=engine)
    assert "researchers" in Base.metadata.tables
    assert "experiments" in Base.metadata.tables


def test_main_run_server():
    """Verify run_server calls uvicorn.run with expected arguments."""
    with patch("uvicorn.run") as mock_run:
        run_server(host="127.0.0.1", port=8000)
        mock_run.assert_called_once_with(
            "experiment_manager.api:app", host="127.0.0.1", port=8000, reload=False
        )


def test_main_cli_execution():
    """Verify main module CLI execution with custom arguments."""
    with patch("uvicorn.run") as mock_run, patch("sys.argv", ["main.py", "0.0.0.0", "9000"]):
        import experiment_manager.main as m
        m.run_server(sys.argv[1], int(sys.argv[2]))
        mock_run.assert_called_with(
            "experiment_manager.api:app", host="0.0.0.0", port=9000, reload=False
        )

