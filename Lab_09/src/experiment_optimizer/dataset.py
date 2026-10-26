"""Dataset generation and I/O utilities for experimental benchmarking."""

from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import List, Sequence

from .models import Experiment, Researcher

RESEARCHER_NAMES = [
    ("Олександр", "Франков", "Кафедра кібербезпеки та програмування"),
    ("Ірина", "Коваленко", "Лабораторія нанотехнологій"),
    ("Максим", "Бондаренко", "Відділ квантової фізики"),
    ("Юлія", "Шевченко", "Інститут прикладної оптики"),
    ("Дмитро", "Ткаченко", "Кафедра радіоелектроніки"),
]

PARAMETERS = [
    "Температура (°C)",
    "Тиск (кПа)",
    "Напруга (В)",
    "Опір (Ом)",
    "Інтенсивність випромінювання (лк)",
]


def generate_researchers() -> List[Researcher]:
    """Generate default list of researchers."""
    return [
        Researcher(id=i + 1, name=f"{first} {last}", department=dept)
        for i, (first, last, dept) in enumerate(RESEARCHER_NAMES)
    ]


def generate_experiments(
    count: int,
    researchers: Sequence[Researcher] | None = None,
    seed: int = 42,
) -> List[Experiment]:
    """Generate a reproducible deterministic dataset of experiments."""
    rnd = random.Random(seed)
    if not researchers:
        researchers = generate_researchers()

    researcher_ids = [r.id for r in researchers]
    base_date = date(2026, 1, 1)

    experiments: List[Experiment] = []
    for idx in range(1, count + 1):
        param = PARAMETERS[rnd.randrange(len(PARAMETERS))]
        res_val = round(rnd.uniform(10.0, 500.0) + rnd.gauss(0.0, 5.0), 4)
        exp_date = base_date + timedelta(days=rnd.randint(0, 300))
        r_id = rnd.choice(researcher_ids)

        experiments.append(
            Experiment(
                id=idx,
                title=f"Дослідження №{idx}: {param}",
                researcher_id=r_id,
                parameter=param,
                result=res_val,
                date=exp_date,
                notes=f"Автоматично згенерований замір №{idx}",
            )
        )
    return experiments


def export_experiment_batches(
    experiments: Sequence[Experiment],
    output_dir: Path | str,
    num_batches: int = 10,
) -> List[Path]:
    """Split and export experiments into multiple JSON files for I/O concurrency testing."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    batch_size = (len(experiments) + num_batches - 1) // num_batches
    saved_paths: List[Path] = []

    for i in range(num_batches):
        batch = experiments[i * batch_size : (i + 1) * batch_size]
        if not batch:
            continue
        filepath = target_dir / f"batch_{i + 1:02d}.json"
        data = [
            {
                "id": exp.id,
                "title": exp.title,
                "researcher_id": exp.researcher_id,
                "parameter": exp.parameter,
                "result": exp.result,
                "date": exp.date.isoformat(),
                "notes": exp.notes,
            }
            for exp in batch
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)
        saved_paths.append(filepath)

    return saved_paths


def load_experiments_from_file(filepath: Path | str) -> List[Experiment]:
    """Load experiments from a single JSON file."""
    path = Path(filepath)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [
        Experiment(
            id=item["id"],
            title=item["title"],
            researcher_id=item["researcher_id"],
            parameter=item["parameter"],
            result=item["result"],
            date=date.fromisoformat(item["date"]),
            notes=item.get("notes"),
        )
        for item in data
    ]
