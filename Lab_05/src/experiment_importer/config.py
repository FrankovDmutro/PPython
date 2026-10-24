"""Configuration loading and validation module."""

from pathlib import Path
from typing import Any
import yaml

from experiment_importer.exceptions import ConfigurationError
from experiment_importer.models import AppConfig, LoggingConfig, ProcessingConfig

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def load_config(path: Path) -> AppConfig:
    """Load, parse, and validate YAML application configuration.

    Raises ConfigurationError if the file is missing, malformed, or invalid.
    """
    if not path.is_file():
        raise ConfigurationError(f"Configuration file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as err:
        raise ConfigurationError(f"Failed to parse YAML configuration: {err}") from err
    except OSError as err:
        raise ConfigurationError(f"Cannot read configuration file {path}: {err}") from err

    if not isinstance(data, dict):
        raise ConfigurationError("Configuration root must be a YAML mapping/dictionary")

    return _validate_and_build(data, config_dir=path.parent)


def _validate_and_build(raw: dict[str, Any], config_dir: Path) -> AppConfig:
    """Validate raw configuration dictionary and construct AppConfig."""
    # Validate input section
    input_sec = raw.get("input")
    if not isinstance(input_sec, dict) or "path" not in input_sec:
        raise ConfigurationError("Missing or invalid 'input.path' configuration section")
    input_path = config_dir / Path(str(input_sec["path"]))

    # Validate output section
    output_sec = raw.get("output")
    if not isinstance(output_sec, dict) or "path" not in output_sec:
        raise ConfigurationError("Missing or invalid 'output.path' configuration section")
    output_path = config_dir / Path(str(output_sec["path"]))
    summary_path_raw = output_sec.get("summary_path", "output/summary.json")
    summary_path = config_dir / Path(str(summary_path_raw))

    # Validate processing section
    proc_sec = raw.get("processing")
    if not isinstance(proc_sec, dict):
        raise ConfigurationError("Missing or invalid 'processing' configuration section")

    allowed_raw = proc_sec.get("allowed_parameters")
    if not isinstance(allowed_raw, (list, tuple)) or not allowed_raw:
        raise ConfigurationError(
            "'processing.allowed_parameters' must be a non-empty list of strings"
        )
    allowed_parameters = tuple(str(p).strip().lower() for p in allowed_raw if str(p).strip())
    if not allowed_parameters:
        raise ConfigurationError("'processing.allowed_parameters' contains no valid strings")

    try:
        min_result = float(proc_sec.get("min_result", float("-inf")))
        max_result = float(proc_sec.get("max_result", float("inf")))
    except (ValueError, TypeError) as err:
        raise ConfigurationError(
            "min_result and max_result must be valid numeric values"
        ) from err

    if min_result > max_result:
        raise ConfigurationError(
            f"min_result ({min_result}) cannot exceed max_result ({max_result})"
        )

    skip_invalid = bool(proc_sec.get("skip_invalid", True))

    # Validate logging section
    log_sec = raw.get("logging")
    if not isinstance(log_sec, dict):
        raise ConfigurationError("Missing or invalid 'logging' configuration section")

    log_level = str(log_sec.get("level", "INFO")).upper().strip()
    if log_level not in VALID_LOG_LEVELS:
        raise ConfigurationError(
            f"Invalid log level '{log_level}'. Must be one of: {', '.join(sorted(VALID_LOG_LEVELS))}"
        )

    log_path_raw = log_sec.get("path", "logs/application.log")
    log_path = config_dir / Path(str(log_path_raw))

    return AppConfig(
        input_path=input_path,
        output_path=output_path,
        summary_path=summary_path,
        processing=ProcessingConfig(
            allowed_parameters=allowed_parameters,
            min_result=min_result,
            max_result=max_result,
            skip_invalid=skip_invalid,
        ),
        logging=LoggingConfig(
            level=log_level,
            path=log_path,
        ),
    )
