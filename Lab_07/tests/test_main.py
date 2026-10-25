"""Integration tests for CLI main entrypoint."""

from pathlib import Path
from experiment_manager.main import main


def test_main_cli_execution(tmp_path: Path) -> None:
    """Test full CLI flow execution on isolated database."""
    db_file = tmp_path / "cli_test.db"
    exit_code = main(["--db-path", str(db_file), "--seed"])
    assert exit_code == 0
    assert db_file.is_file()
