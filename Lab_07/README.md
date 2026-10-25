# Лабораторна робота № 7: Робота з базами даних у Python

**Дисципліна:** Програмування на Python  
**Студент:** Франков  
**Варіант № 15:** «Облік результатів наукових експериментів»  
**Віртуальне середовище:** `Lab_01/.venv`  

---

## 1. Опис проєкту

Проєкт є повноцінним рівнем збереження даних (Persistence Layer) для предметної області наукових експериментів, створеним як логічне продовження попередніх лабораторних робіт відповідно до стандарту `src-layout`, PEP 8 та суворої типізації.

### Реалізовані архітектурні та технічні рішення:
- **СУБД SQLite та SQLAlchemy 2.0 ORM:** реляційна схема з первинними (`PRIMARY KEY`) та зовнішніми ключами (`FOREIGN KEY`), зв'язком **One-to-Many** (`relationship`) та каскадним видаленням (`cascade="all, delete-orphan"`).
- **Паттерн Repository:** ізоляція операцій збереження у класах `ResearcherRepository` та `ExperimentRepository` із підтримкою повного циклу CRUD, фільтрації за числовим діапазоном та сортування за датою (`ORDER BY`).
- **Python DB-API (sqlite3):** прямі безпечні параметризовані SQL-запити (захист від SQL Injection), підтримка агрегатних функцій `COUNT()`, `AVG()`, `MIN()`, `MAX()`.
- **Транзакції та принципи ACID:** пакетне додавання серій експериментів із гарантованим відкатом (`rollback()`) у разі порушення фізичних обмежень (наприклад, температура нижче абсолютного нуля $-273.15$ °C).
- **Міграції бази даних (Alembic):** налаштування схеми міграцій та скрипт `001_add_notes_to_experiments.py` для додавання стовпця `notes` до таблиці експериментів.
- **Інтеграційне тестування (pytest):** набір із 15 інтеграційних тестів на базі ізольованої тестової бази даних в оперативній пам'яті (`:memory:`), що перевіряють CRUD, зв'язки, агрегати, транзакції та міграції з 91% тестовим покриттям.

---

## 2. Структура проєкту

```
Lab_07/
├── pyproject.toml              # Метадані пакета, залежності (SQLAlchemy, Alembic), pytest
├── alembic.ini                 # Конфігурація Alembic для SQLite
├── README.md                   # Документація проєкту
├── migrations/                 # Каталог міграцій Alembic
│   ├── env.py                  # Середовище виконання міграцій (online/offline)
│   ├── script.py.mako          # Шаблон нових міграцій
│   └── versions/
│       └── 001_add_notes_to_experiments.py # Міграція додавання поля notes
├── data/
│   └── experiments.db          # База даних SQLite
├── report/                     # Офіційний звіт з лабораторної роботи
│   └── ПП_ЛАБ7_ФРАНКОВ.docx
├── tests/                      # Інтеграційні тести (15 тестів)
│   ├── __init__.py
│   ├── conftest.py             # Фікстури ізольованої тестової сесії (:memory:)
│   ├── test_repositories.py    # Тести CRUD, relationships, range filter, order by
│   ├── test_services.py        # Тести сервісу, транзакцій та rollback
│   ├── test_db_api.py          # Тести параметризованих DB-API запитів та SQL-агрегацій
│   ├── test_migrations.py      # Тести застосування міграції Alembic
│   └── test_main.py            # Тести CLI точки входу
└── src/
    └── experiment_manager/
        ├── __init__.py
        ├── database.py         # Налаштування engine, sessionmaker, Base та DB-API
        ├── models.py           # ORM-моделі Researcher та Experiment
        ├── repositories.py     # Реалізація ResearcherRepository та ExperimentRepository
        ├── services.py         # Service Layer: бізнес-логіка та транзакційний batch insert
        ├── db_api.py           # Прямі параметризовані SQL-запити через sqlite3 DB-API
        └── main.py             # CLI точка входу
```

---

## 3. Схема бази даних (Варіант № 15)

```
+--------------------+            +---------------------------------+
|    researchers     | 1        * |           experiments           |
+--------------------+------------+---------------------------------+
| id (PK, Integer)   |            | id (PK, Integer)                |
| name (String, UQ)  |            | title (String)                  |
| department (String)|            | researcher_id (FK -> res.id)    |
+--------------------+            | parameter (String)              |
                                  | result (Float)                  |
                                  | date (String ISO YYYY-MM-DD)    |
                                  | notes (Text, Nullable)          |
                                  +---------------------------------+
```

---

## 4. Інструкція із запуску та використання

### Активація віртуального середовища (PowerShell):
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& c:\Users\frankov\Documents\projects\labs\PPython\Lab_01\.venv\Scripts\Activate.ps1
```

### Застосування міграцій бази даних:
```powershell
alembic -c Lab_07/alembic.ini upgrade head
```

### Демонстраційний запуск CLI додатку:
```powershell
python -m experiment_manager.main --db-path Lab_07/data/experiments.db
```

### Запуск інтеграційних тестів та вимірювання покриття:
```powershell
pytest Lab_07/tests -v --cov=experiment_manager --cov-branch --cov-report=term-missing
```

---

## 5. Підсумки тестування

- **Кількість тестів:** **15 passed in 0.78s** (0 failures).
- **Загальне покриття коду (Total Coverage):** **91 %**.
- **Покриття модулів:**
  - `main.py`: **96 %**
  - `services.py`: **94 %**
  - `database.py`: **92 %**
  - `db_api.py`: **92 %**
  - `models.py`: **86 %**
  - `repositories.py`: **86 %**
