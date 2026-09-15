from .models import Experiment
from .services import (
    add_experiment,
    average_result,
    filter_by_range,
    find_by_research,
    min_max_result,
)


def create_demo_experiments() -> list[Experiment]:
    return [
        Experiment(
            name="Thermal Expansion",
            researcher="Oleh Koval",
            parameter="Delta L (mm)",
            result=2.45,
            date="2026-03-10",
        ),
        Experiment(
            name="Tensile Strength",
            researcher="Iryna Melnyk",
            parameter="Stress (MPa)",
            result=450.0,
            date="2026-03-12",
        ),
        Experiment(
            name="Thermal Conductivity",
            researcher="Oleh Koval",
            parameter="Watts/(m*K)",
            result=15.8,
            date="2026-03-15",
        ),
    ]


def print_experiments(experiments: list[Experiment]) -> None:
    if not experiments:
        print("  [Немає записів]")
        return

    print(
        f"{'Назва':<22} {'Дослідник':<16} {'Параметр':<18} {'Результат':<10} {'Дата'}"
    )
    print("-" * 75)
    for exp in experiments:
        print(
            f"{exp.name:<22} {exp.researcher:<16} {exp.parameter:<18} {exp.result:<10.2f} {exp.date}"
        )


def main() -> None:
    experiments = create_demo_experiments()

    print("=== Початковий список експериментів ===")
    print_experiments(experiments)

    print("\n1. Додавання нового експерименту:")
    new_exp = Experiment(
        name="Electrical Resistance",
        researcher="Anna Shevchenko",
        parameter="Resistance (Ohm)",
        result=120.5,
        date="2026-03-18",
    )
    add_experiment(experiments, new_exp)
    print(f"Додано: {new_exp.name}")

    target_researcher = "Koval"
    print(f"\n2. Пошук експериментів дослідника '{target_researcher}':")
    found_by_author = find_by_research(experiments, target_researcher)
    print_experiments(found_by_author)

    avg = average_result(experiments)
    print(f"\n3. Середнє значення результатів: {avg:.2f}")

    min_exp, max_exp = min_max_result(experiments)
    print(
        f"\n4. Мінімум: {min_exp.name} ({min_exp.result}) | Дослідник: {min_exp.researcher}"
    )
    print(
        f"   Максимум: {max_exp.name} ({max_exp.result}) | Дослідник: {max_exp.researcher}"
    )

    range_start, range_end = 10.0, 200.0
    print(
        f"\n5. Фільтрація результатів у діапазоні [{range_start}; {range_end}] (відсортовано):"
    )
    filtered = filter_by_range(experiments, range_start, range_end)
    print_experiments(filtered)


if __name__ == "__main__":
    main()