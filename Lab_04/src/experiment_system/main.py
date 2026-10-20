from experiment_system.dto import ExperimentPayload
from experiment_system.models import Experiment, ExperimentSeries
from experiment_system.protocols import StandardAnalysisStrategy
from experiment_system.repositories import InMemoryRepository
from experiment_system.services import (
    ConsoleNotifier,
    ExperimentService,
    JsonLikeExporter,
)


def main() -> None:
    print("=== SCIENTIFIC EXPERIMENT SYSTEM (LAB 4) ===")

    # 1. Dependency Injection setup
    repo = InMemoryRepository[Experiment]()
    strategy = StandardAnalysisStrategy()
    notifier = ConsoleNotifier()
    exporter = JsonLikeExporter()

    service = ExperimentService(
        repository=repo,
        analysis_strategy=strategy,
        exporter=exporter,
        notifier=notifier,
    )

    # 2. Ingest TypedDict payloads
    exp1_payload: ExperimentPayload = {
        "id": 1,
        "title": "Quantum Resistance Test",
        "parameter": "Resistance",
        "value": 12.45,
        "unit": "Ohm",
        "researcher_name": "Dr. Dmytro Frankov",
        "researcher_email": "d.frankov@lnu.edu.ua",
    }

    exp2_payload: ExperimentPayload = {
        "id": 2,
        "title": "Thermal Drift Measurement",
        "parameter": "Temperature",
        "value": 24.80,
        "unit": "Celsius",
        "researcher_name": "Dr. Dmytro Frankov",
        "researcher_email": "d.frankov@lnu.edu.ua",
        "calibration_offset": 0.35,
    }

    exp3_invalid_payload: ExperimentPayload = {
        "id": 3,
        "title": "Superconductor Overload",
        "parameter": "Voltage",
        "value": 1500.0,  # Exceeds max_bound (1000.0)
        "unit": "Volt",
        "researcher_name": "Dr. Dmytro Frankov",
        "researcher_email": "d.frankov@lnu.edu.ua",
    }

    e1 = service.register_experiment(exp1_payload)
    e2 = service.register_experiment(exp2_payload)
    e3 = service.register_experiment(exp3_invalid_payload)

    # 3. Aggregate into ExperimentSeries (Composition and Dunder methods)
    series = ExperimentSeries(series_name="Series Alpha 2026")
    series.add(e1)
    series.add(e2)
    series.add(e3)

    print("\n--- ExperimentSeries Container Check ---")
    print(f"Total experiments in series (__len__): {len(series)}")
    print(f"Is experiment ID 2 present? (__contains__): {2 in series}")
    print(f"Is experiment ID 99 present? (__contains__): {99 in series}")

    print("\n--- Iteration over series (__iter__) ---")
    for exp in series:
        print(f"-> {exp}")

    # 4. Statistical Analysis (ABC strategy)
    stats = service.analyze_series(series)
    print("\n--- Analysis Strategy Results ---")
    for metric, val in stats.items():
        print(f"{metric.capitalize()}: {val:.4f}")

    # 5. Exporting (Protocol structural typing)
    export_output = service.export_series(series)
    print(f"\nExport payload: {export_output}")
    print(f"Repository count: {len(repo)}")


if __name__ == "__main__":
    main()