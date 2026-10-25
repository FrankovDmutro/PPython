"""Command line interface for the experiment tracking system."""

import argparse
from pathlib import Path
import sys

from experiment_tracker.io import import_measurements_csv
from experiment_tracker.models import Experiment, Researcher
from experiment_tracker.repository import InMemoryExperimentRepository
from experiment_tracker.services import ExperimentService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scientific Experiment Tracking System (Lab 6, Variant 15)"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("data/sample_experiments.csv"),
        help="Input CSV file with experiment measurements",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/sample_export.json"),
        help="Output JSON file destination",
    )
    args = parser.parse_args(argv)

    input_path = args.input
    if not input_path.is_file():
        alt_path = Path("Lab_06") / input_path
        if alt_path.is_file():
            input_path = alt_path

    if not input_path.is_file():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        return 1

    repo = InMemoryExperimentRepository()
    service = ExperimentService(repo)

    print(f"Loading measurements from {input_path}...")
    imported = import_measurements_csv(input_path)

    for exp_id, title, researcher, param, meas in imported:
        exp = repo.get(exp_id)
        if exp is None:
            exp = service.create_experiment(exp_id, title, researcher, param)
        exp.add_measurement(meas)
        repo.save(exp)

    experiments = repo.list_all()
    print(f"Successfully loaded {len(imported)} measurements across {len(experiments)} experiments.\n")

    for exp in experiments:
        summary = service.analyze_experiment(exp.id)
        print(f"Experiment {exp.id}: '{exp.title}' ({exp.parameter})")
        print(f"  Researcher: {exp.researcher.name} ({exp.researcher.department})")
        print(f"  Measurements: {summary['measurements_count']}")
        print(f"  Average: {summary['average']:.2f}, Min: {summary['min']:.2f}, Max: {summary['max']:.2f}\n")

    if experiments:
        target_out = args.output
        if not target_out.is_absolute() and not target_out.parent.exists():
            target_out = Path("Lab_06") / args.output
        service.export_experiment(experiments[0].id, target_out)
        print(f"Exported experiment '{experiments[0].id}' to {target_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
