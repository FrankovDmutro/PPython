"""Command-line interface entry point for the experiment importer application."""

import argparse
import logging
from pathlib import Path
import sys

from experiment_importer.config import load_config
from experiment_importer.exceptions import ApplicationError
from experiment_importer.logging_config import configure_logging
from experiment_importer.services import run_pipeline

logger = logging.getLogger("experiment_importer.main")


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scientific Experiment Data Ingestion & Serialization System (Lab 5, Variant 15)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help="Optional override for input CSV file path",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Optional override for output file path",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "jsonl"],
        default="json",
        help="Output serialization format (json array or jsonl)",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--strict",
        action="store_true",
        help="Force strict validation mode (fail-fast on first error)",
    )
    mode_group.add_argument(
        "--tolerant",
        action="store_true",
        help="Force tolerant validation mode (skip and record invalid rows)",
    )

    return parser.parse_args(argv)


def resolve_config_path(cli_path: Path) -> Path:
    """Find configuration file resolving relative paths."""
    if cli_path.is_file():
        return cli_path
    # Try looking in Lab_05 directory if invoked from repo root
    alt_path = Path("Lab_05") / cli_path
    if alt_path.is_file():
        return alt_path
    return cli_path


def main(argv: list[str] | None = None) -> int:
    """Application main function."""
    args = parse_arguments(argv)

    config_path = resolve_config_path(args.config)
    try:
        app_config = load_config(config_path)
    except ApplicationError as err:
        sys.stderr.write(f"Configuration error: {err}\n")
        return 1
    except Exception as err:
        sys.stderr.write(f"Unexpected error loading configuration: {err}\n")
        return 1

    # Configure logging
    try:
        configure_logging(app_config.logging.level, app_config.logging.path)
    except Exception as err:
        sys.stderr.write(f"Failed to configure logging: {err}\n")
        return 1

    logger.info("Starting Experiment Importer System (Variant 15)")
    logger.info("Loaded configuration from: %s", config_path)

    # CLI overrides
    if args.input:
        app_config = app_config.__class__(
            input_path=args.input,
            output_path=app_config.output_path,
            summary_path=app_config.summary_path,
            processing=app_config.processing,
            logging=app_config.logging,
        )
    if args.output:
        app_config = app_config.__class__(
            input_path=app_config.input_path,
            output_path=args.output,
            summary_path=app_config.summary_path,
            processing=app_config.processing,
            logging=app_config.logging,
        )

    override_skip: bool | None = None
    if args.strict:
        override_skip = False
    elif args.tolerant:
        override_skip = True

    try:
        exported_count, statistics = run_pipeline(
            app_config,
            output_format=args.format,
            override_skip_invalid=override_skip,
        )
        print(f"\nProcessing completed successfully.")
        print(f"Total rows read: {statistics.total}")
        print(f"Valid records:   {statistics.valid}")
        print(f"Invalid records: {statistics.invalid}")
        print(f"Exported records: {exported_count}")
        print(f"Output saved to:  {app_config.output_path}")
        print(f"Summary saved to: {app_config.summary_path}")
        return 0
    except ApplicationError as err:
        logger.error("Application error occurred: %s", err)
        print(f"\nExecution failed: {err}", file=sys.stderr)
        return 2
    except Exception as err:
        logger.exception("Unexpected system failure: %s", err)
        print(f"\nFatal system error: {err}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
