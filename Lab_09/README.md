# Лабораторна робота № 9. Паралельність, багатопроцесність та оптимізація

**Індивідуальний варіант:** № 15 — *«Облік результатів наукових експериментів»*  
**Студент:** Франков  
**Дисципліна:** «Програмування на Python»  
**Рік:** 2026  

---

## 1. Опис проєкту

Даний проєкт присвячений глибокому аналізу продуктивності, виявленню вузьких місць (bottlenecks) та комплексному експериментальному дослідженню методів оптимізації у середовищі CPython для системи обліку результатів наукових експериментів.

У проєкті реалізовано:
- **Baseline implementation** на базі чистих Python-циклів;
- **NumPy SIMD Vectorization** для миттєвої векторної обробки числових вибірок експериментів;
- **Багатопоточність (`threading`, `ThreadPoolExecutor`)** з демонстрацією впливу **Global Interpreter Lock (GIL)** на CPU-bound задачах та прискорення на I/O-bound операціях паралельного завантаження батчів;
- **Синхронізація (`Lock`)** з практичною демонстрацією стану гонитви (`race condition`) на незахищеному лічильнику та його усуненням;
- **Багатопроцесність (`multiprocessing`, `ProcessPoolExecutor`)** з обходом GIL та дослідженням закону Амдала при масштабуванні воркерів ($1, 2, 4, 8, 16$ процесів);
- **Інтелектуальне кешування (`caching`)** з підрахунком хітів/промахів (telemetry), збереженого часу та механізмом інвалідації кешу (`cache invalidation`);
- **Профілювання** часу (`cProfile`, `perf_counter`) та пам'яті (`tracemalloc`).

---

## 2. Структура проєкту

```
Lab_09/
├── pyproject.toml
├── README.md
├── generate_report.py
├── src/
│   └── experiment_optimizer/
│       ├── __init__.py
│       ├── models.py          # Легковагові моделі Researcher, Experiment, ExperimentStatistics
│       ├── dataset.py         # Детермінований генератор датасетів (10k, 100k, 1M) та I/O утиліти
│       ├── analytics.py       # Baseline Python loops vs NumPy vectorization
│       ├── parallel.py        # ThreadPool, ProcessPool, Lock, Race Condition, I/O Concurrency
│       ├── caching.py         # ExperimentStatsCache, hit/miss telemetry, cache invalidation
│       └── profiling.py       # Обгортки cProfile та tracemalloc
├── benchmarks/
│   ├── benchmark.py           # Повний цикл автоматизованого бенчмаркінгу
│   └── results/
│       ├── benchmark_results.csv
│       ├── execution_time_comparison.png
│       ├── speedup_comparison.png
│       ├── worker_scaling.png
│       └── memory_usage_comparison.png
├── tests/
│   ├── conftest.py
│   ├── test_analytics.py      # Перевірка збігу результатів Baseline vs NumPy
│   ├── test_parallel.py       # Тестування Thread/Process Pool та захисту Lock
│   ├── test_caching.py        # Тести кешу, hit/miss та invalidation
│   └── test_profiling.py      # Тести утиліт cProfile та tracemalloc
└── report/
    ├── ПП_ЛАБ9_ФРАНКОВ.docx   # Офіційний звіт у форматі Word
    └── ПП_ЛАБ9_ФРАНКОВ.pdf    # Звіт у форматі PDF
```

---

## 3. Встановлення та запуск

### Активація віртуального середовища
```powershell
& c:\Users\frankov\Documents\projects\labs\PPython\Lab_01\.venv\Scripts\Activate.ps1
```

### Встановлення пакета в режимі розробки
```powershell
pip install -e Lab_09
```

### Запуск автоматизованого бенчмаркінгу
```powershell
python Lab_09/benchmarks/benchmark.py
```

### Запуск повного набору тестів із покриттям (Coverage)
```powershell
pytest Lab_09/tests --cov=Lab_09/src/experiment_optimizer --cov-report=term-missing
```

### Генерація офіційного звіту
```powershell
python Lab_09/generate_report.py
```

---

## 4. Зведені результати бенчмаркінгу

| Розмір вибірки | Метод обчислення | Кількість Workers | Середній час (с) | Speedup | Пікова пам'ять (КБ) |
|---|---|---|---|---|---|
| **10 000** | Sequential (Baseline) | 1 | 0.00352 | 1.00× | 78.80 |
| **10 000** | ThreadPoolExecutor | 4 | 0.00485 | 0.73× | 176.21 |
| **10 000** | ProcessPoolExecutor | 1 | 0.57694 | 0.01× | 1 070.39 |
| **10 000** | NumPy Vectorization | 1 | 0.00021 | **16.79×** | 235.66 |
| **100 000** | Sequential (Baseline) | 1 | 0.01599 | 1.00× | 781.69 |
| **100 000** | ThreadPoolExecutor | 4 | 0.01603 | 1.00× | 1 758.24 |
| **100 000** | NumPy Vectorization | 1 | 0.00253 | **6.33×** | 2 344.16 |
| **1 000 000** | Sequential (Baseline) | 1 | 0.16507 | 1.00× | 7 812.94 |
| **1 000 000** | ThreadPoolExecutor | 4 | 0.17360 | 0.95× | 17 578.55 |
| **1 000 000** | ProcessPoolExecutor | 2 | 0.72971 | 0.23× | 16 895.58 |
| **1 000 000** | NumPy Vectorization | 1 | 0.03533 | **4.67×** | 23 437.91 |

- **I/O-Bound Speedup:** ThreadPoolExecutor досяг прискорення **1.16×** при конкурентному читанні 10 файлів батчів (0.3282 с проти 0.3795 с).
- **Caching Speedup:** Повторний доступ до розрахованої статистики забезпечив прискорення у **21 583×** (0.0000008 с проти 0.01727 с).
- **Синхронізація:** Підтверджено виникнення `race condition` на незахищеному лічильнику та 100% гарантію консистентності при застосуванні `threading.Lock`.
