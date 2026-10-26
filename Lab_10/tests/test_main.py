"""Tests for command-line interface entry point."""

from __future__ import annotations

from experiment_registry.main import parse_args


def test_cli_default_args() -> None:
    """Verify CLI defaults align with settings."""
    args = parse_args([])
    assert args.port == 8000
    assert args.host == "0.0.0.0"


def test_cli_custom_args() -> None:
    """Verify CLI flags override parameters."""
    args = parse_args(["--host", "127.0.0.1", "--port", "9090", "--reload"])
    assert args.host == "127.0.0.1"
    assert args.port == 9090
    assert args.reload is True
