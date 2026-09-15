from lab_logging.models import Experiment

def add_experiment(
    experiments: list[Experiment],
    experiment: Experiment,
) -> None:
    """Add an experiment to the experiments list"""
    experiments.append(experiment)

def find_by_research(
    experiments: list[Experiment],
    researcher: str,
) -> list[Experiment]:
    """Find an experiment in the experiments list"""
    query = researcher.lower().strip()
    return [
        exp
        for exp in experiments
        if query in exp.researcher.lower()
    ]

def average_result(
    experiments: list[Experiment],
) -> float:
    """Calculate the average result of the experiments"""
    if not experiments:
        return 0.0
    
    total = 0
    for exp in experiments:
        total += exp.result

    total = total / len(experiments)

    return total

def min_max_result(
    experiments: list[Experiment],
) -> tuple[Experiment, Experiment]:
    """Calculate the minimum and maximum result of the experiments"""
    if not experiments:
        return None
    
    min_exp = min(experiments, key=lambda x: x.result)
    max_exp = max(experiments, key=lambda x: x.result)

    return min_exp, max_exp

def filter_by_range(
    experiments: list[Experiment],
    start: float,
    end: float,
) -> list[Experiment]:
    """Filter experiments by the range sorted by result"""
    return sorted(
        [exp
         for exp in experiments
         if start <= exp.result <= end],
        key=lambda exp: exp.result,
    )