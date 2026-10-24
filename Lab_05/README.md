# Лабораторна робота № 5: Обробка помилок, файли та серіалізація

**Дисципліна:** Програмування на Python  
**Студент:** Франков  
**Варіант № 15:** «Імпорт та експорт результатів наукових експериментів»  

---

## 1. Опис проєкту

Проєкт є надійною модульною системою обробки результатів наукових експериментів, реалізованою відповідно до сучасних стандартів Python (Python 3.11+, `src-layout`, PEP 8, сувора типізація). Система забезпечує:

- **Потокове (streaming) зчитування** CSV-файлів довільного розміру з фіксованим O(1) використанням оперативної пам'яті.
- **Дворівневу валідацію даних** (ID експерименту, назва, дослідник, дозволені фізичні параметри згідно з YAML-конфігурацією, числовий діапазон результатів та ISO-формат дати).
- **Підтримку двох режимів обробки:**
  - `tolerant` (толерантний режим): реєстрація некоректних рядків у лог/статистику та продовження обробки валідних записів.
  - `strict` (суворий режим fail-fast): миттєве переривання обробки з генерацією винятку при виявленні першої помилки.
- **Атомарний експорт даних** (Atomic Write Context Manager): запис у тимчасовий файл `.tmp` та атомарна заміна (`Path.replace`), що гарантує захист від пошкодження цільових файлів у разі збоїв.
- **Серіалізацію у формати JSON та JSON Lines** (ndjson) для потокової інтеграції з аналітичними системами.
- **Агрегацію розширеної статистики** (кількість записів, відсоток валідності, середнє, мінімальне та максимальне значення за кожним параметром, журнал помилок).
- **Ієрархію кастомних винятків** із підтримкою збереження першопричини (exception chaining `raise ... from ...`).
- **Гнучке логування** з ротацією файлів через модуль `logging`.

---

## 2. Структура проєкту

```
Lab_05/
├── pyproject.toml              # Метадані проєкту, залежності та налаштування інструментів
├── config.yaml                 # Конфігурація шляхів, параметрів валідації та логування
├── README.md                   # Документація проєкту
├── data/                       # Тестові набори вхідних даних
│   ├── experiments.csv         # Валідний датасет
│   └── experiments_corrupted.csv # Датасет із типовими помилками
├── output/                     # Згенеровані вихідні файли (JSON / JSONL / Summary)
├── logs/                       # Журнали виконання програми
├── report/                     # Офіційний звіт з лабораторної роботи
│   └── ПП_ЛАБ5_ФРАНКОВ.docx
├── tests/                      # Набір автоматизованих модульних та інтеграційних тестів
│   ├── __init__.py
│   ├── test_config.py          # Тести завантаження та валідації конфігурації
│   ├── test_exceptions.py      # Тести ієрархії та chaining винятків
│   ├── test_validators.py      # Тести валідатора експериментів
│   ├── test_readers.py         # Тести потокового CSV reader
│   ├── test_exporters.py       # Тести атомарного запису та форматів експорту
│   ├── test_services.py        # Тести сервісів, фільтрації та режимів обробки
│   └── test_experiments.py     # Тести експериментів 1–5 згідно з методичкою
└── src/
    └── experiment_importer/
        ├── __init__.py
        ├── config.py           # Завантажувач і валідатор конфігурації
        ├── context_managers.py # Контекстні менеджери logged_operation та atomic_write
        ├── exceptions.py       # Ієрархія кастомних винятків
        ├── exporters.py        # Атомарні експортери JSON та JSONL
        ├── logging_config.py   # Налаштування логування та ротації
        ├── main.py             # CLI точка входу
        ├── models.py           # Датакласи моделі даних та конфігурації
        ├── protocols.py        # Інтерфейси (Protocol) Importer та Exporter
        ├── readers.py          # Потоковий генераторний CSV reader
        ├── services.py         # Бізнес-логіка, агрегація статистики, пайплайн
        └── validators.py       # Валідація окремих записів
```

---

## 3. Встановлення та налаштування

Для роботи потрібен Python версії 3.11 або вище.

### Встановлення залежностей у віртуальне середовище:

```bash
# Встановлення проєкту в режимі редагування (з підтримкою YAML):
python -m pip install -e Lab_05
```

---

## 4. Конфігурація (`config.yaml`)

```yaml
input:
  path: data/experiments.csv

output:
  path: output/experiments.json
  summary_path: output/summary.json

processing:
  allowed_parameters:
    - temperature
    - pressure
    - voltage
    - current
    - humidity
    - radiation
  min_result: 0.0
  max_result: 10000.0
  skip_invalid: true

logging:
  level: INFO
  path: logs/experiment_importer.log
```

---

## 5. Інструкція із запуску (CLI)

### Базовий запуск за конфігураційним файлом:
```bash
python -m experiment_importer.main --config Lab_05/config.yaml
```

### Примусовий запуск у суворому (Strict) режимі:
```bash
python -m experiment_importer.main --config Lab_05/config.yaml --input Lab_05/data/experiments_corrupted.csv --strict
```

### Запуск у толерантному (Tolerant) режимі:
```bash
python -m experiment_importer.main --config Lab_05/config.yaml --input Lab_05/data/experiments_corrupted.csv --tolerant
```

### Експорт у потоковий формат JSON Lines:
```bash
python -m experiment_importer.main --config Lab_05/config.yaml --format jsonl --output Lab_05/output/experiments.jsonl
```

---

## 6. Запуск тестів та результати бенчмарків

Запуск повного набору автоматизованих тестів:
```bash
python -m unittest discover -s Lab_05/tests -v
```

### Результати вимірювання пам'яті (tracemalloc для 20 000 записів):
- **Eager (матеріалізація списку):** 11 442.23 KB
- **Streaming (потоковий генератор):** 51.83 KB
- **Економія пам'яті:** **99.5 %**
