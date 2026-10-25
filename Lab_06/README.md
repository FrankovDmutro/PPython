# Лабораторна робота № 6: Автоматизоване тестування, pytest, coverage та mocks

**Дисципліна:** Програмування на Python  
**Студент:** Франков  
**Варіант № 15:** «Система обліку результатів наукових експериментів»  

---

## 1. Опис проєкту

Проєкт є повноцінною, надійною системою обліку наукових експериментів та вимірювань, розробленою відповідно до архітектурного підходу `src-layout`, стандарту PEP 8 та суворої типізації, із всебічним автоматизованим тестовим покриттям на базі фреймворку `pytest`.

### Ключові можливості системи:
- **Доменні сутності та Value Objects:** `Researcher` (дослідник), `Measurement` (вимірювання з фізичною величиною, одиницею та часовою міткою), `Experiment` (експеримент з обчисленням середнього, мін/макс, СКВ та фільтрацією за діапазоном), `ExperimentSeries` (серія експериментів).
- **Багаторівнева валідація:** сувора перевірка дозволених фізичних параметрів (`ALLOWED_PARAMETERS`), одиниць вимірювань (`ALLOWED_UNITS`), граничних числових меж (включно з абсолютним нулем -273.15 °C) та міжнародного формату дати ISO 8601.
- **Шаблони репозиторію та сервісів:** протокол `ExperimentRepository`, інверсія залежностей у `ExperimentService`, підтримка стратегій аналізу (`AnalysisStrategy`) та експортерів (`Exporter`).
- **Асинхронні джерела телеметрії:** `AsyncSensorClient` для отримання вимірювань з апаратних датчиків у неблокуючому режимі.
- **Введення/виведення та атомарний експорт:** читання потоків CSV та атомарний запис JSON-структур.

---

## 2. Структура проєкту

```
Lab_06/
├── pyproject.toml              # Метадані пакета, залежності, конфігурація pytest та coverage
├── pytest.ini                 # Конфігурація pytest та реєстрація маркерів
├── README.md                   # Документація проєкту
├── data/                       # Тестові вхідні дані
│   └── sample_experiments.csv  # Еталонний набір вимірювань
├── output/                     # Каталог експортованих файлів
├── report/                     # Офіційний звіт з лабораторної роботи
│   └── ПП_ЛАБ6_ФРАНКОВ.docx
├── tests/                      # Автоматизований набір тестів (76 тестів)
│   ├── __init__.py
│   ├── conftest.py             # Спільні фікстури (researcher, experiment, tmp_path, repo)
│   ├── test_models.py          # Модульні тести моделей, метрик та EmptySeriesError
│   ├── test_validators.py      # Тести валідації, параметризація, граничні значення
│   ├── test_repository.py      # Тести репозиторію та симуляції збоїв
│   ├── test_services.py        # Тести сервісу з Mock, return_value, side_effect, integration
│   ├── test_async_sensor.py    # Тести асинхронного клієнта з AsyncMock
│   ├── test_io.py              # Тести CSV імпорту, JSON експорту, monkeypatch
│   ├── test_experiments.py     # Методичні експерименти 1–7 з методички
│   └── test_main.py            # Тести CLI точки входу та життєвого циклу
└── src/
    └── experiment_tracker/
        ├── __init__.py
        ├── models.py           # Доменні моделі Experiment, Measurement, Researcher
        ├── exceptions.py       # Кастомна ієрархія винятків ExperimentTrackerError
        ├── validators.py       # Валідація фізичних параметрів та меж
        ├── repository.py       # Протокол ExperimentRepository та Fake репозиторій
        ├── services.py         # Бізнес-сервіс ExperimentService та Exporter
        ├── async_sensor.py     # Асинхронний сенсорний клієнт
        ├── io.py               # Потоковий імпорт CSV та атомарний експорт JSON
        └── main.py             # CLI точка входу
```

---

## 3. Встановлення та налаштування

```bash
# Встановлення пакета в режимі розробки:
python -m pip install -e Lab_06

# Встановлення тестових залежностей:
python -m pip install pytest pytest-cov pytest-asyncio
```

---

## 4. Запуск тестів та генерація Coverage

### Базовий запуск тестів:
```bash
python -m pytest Lab_06/tests
```

### Запуск із детальним виведенням та вимірюванням покриття:
```bash
python -m pytest Lab_06/tests --cov=experiment_tracker --cov-branch --cov-report=term-missing
```

### Генерація HTML-звіту про покриття коду:
```bash
python -m pytest Lab_06/tests --cov=experiment_tracker --cov-branch --cov-report=html:Lab_06/htmlcov
```

---

## 5. Підсумки тестування

- **Загальна кількість тестів:** **76 passed in 1.05s** (0 failures, 0 errors).
- **Загальне покриття коду (Total Coverage):** **93 %**.
- **Покриття ключових модулів:**
  - `async_sensor.py`: **100 %**
  - `services.py`: **100 %**
  - `models.py`: **97 %**
  - `io.py`: **93 %**
  - `exceptions.py`: **92 %**
  - `main.py`: **88 %**
  - `repository.py`: **88 %**
  - `validators.py`: **86 %**
