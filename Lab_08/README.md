# Лабораторна робота № 8. Мережеве та асинхронне програмування. REST API

**Індивідуальний варіант:** № 15 — *«Облік результатів наукових експериментів»*  
**Студент:** Франков  
**Дисципліна:** «Програмування на Python»  
**Рік:** 2026

---

## 1. Опис проєкту

Проєкт є сучасною веб-системою на базі **FastAPI**, **Pydantic v2** та **SQLAlchemy 2.0 ORM**, призначеною для централізованого обліку та аналізу результатів наукових досліджень і вимірювань. 

Система надає повний RESTful API для керування сутностями дослідників (`researchers`) та наукових експериментів (`experiments`), забезпечує сувору валідацію фізичних меж параметрів (наприклад, неможливість температури нижче абсолютного нуля $-273.15^\circ\text{C}$), підтримує сортування за датою проведення, фільтрацію результатів за діапазоном значень, обчислення агрегованої статистики (`AVG`, `MIN`, `MAX`, `COUNT`) та асинхронну паралельну агрегацію за допомогою **HTTPX**, `asyncio.Task`, `asyncio.gather` та обмеження конкурентності через `asyncio.Semaphore`.

---

## 2. Архітектурні компоненти

- **`src/experiment_manager/api.py`** — головний веб-сервіс FastAPI з налаштованим `lifespan`, ін'єкцією залежностей (`Depends(get_db)`), каскадними операціями та структурованими HTTP статус-кодами.
- **`src/experiment_manager/schemas.py`** — схеми Pydantic v2 із валідацією полів (`@field_validator`), конфігурацією серіалізації ORM (`from_attributes=True`) та схемами статистичних запитів.
- **`src/experiment_manager/models.py`** — декларативні ORM-моделі `Researcher` та `Experiment` зі зв'язком One-to-Many та каскадним видаленням (`cascade="all, delete-orphan"`).
- **`src/experiment_manager/repositories.py`** — шар ізоляції даних (Repository Pattern) із підтримкою CRUD, діапазонної фільтрації, сортування та SQL-агрегацій.
- **`src/experiment_manager/async_client.py`** — клієнт асинхронної взаємодії (`httpx.AsyncClient`) з підтримкою паралельних запитів (`asyncio.create_task`, `asyncio.gather`), контролем конкурентності (`asyncio.Semaphore`), таймаутами та експоненційним повторенням запитів (`retry with backoff`).
- **`src/experiment_manager/main.py`** — консольна точка входу для запуску Uvicorn ASGI-сервера.

---

## 3. Встановлення та запуск

### Активація віртуального середовища
```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\Users\frankov\Documents\projects\labs\PPython\Lab_01\.venv\Scripts\Activate.ps1)
```

### Встановлення пакета в режимі розробки
```powershell
pip install -e Lab_08
```

### Запуск REST API сервера
```powershell
python -m experiment_manager.main 127.0.0.1 8000
```
Після запуску доступні:
- **Інтерактивна документація Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Альтернативна документація ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 4. Специфікація REST API Endpoints

| Метод | Шлях | Опис | Статус |
|---|---|---|---|
| `GET` | `/researchers` | Отримання списку дослідників (пагінація `skip`, `limit`) | `200 OK` |
| `POST` | `/researchers` | Створення нового дослідника | `201 Created` |
| `GET` | `/researchers/{id}` | Отримання даних дослідника за ID | `200 OK` / `404 Not Found` |
| `DELETE` | `/researchers/{id}` | Видалення дослідника та каскадне видалення його експериментів | `204 No Content` / `404 Not Found` |
| `GET` | `/researchers/{id}/experiments` | Список усіх експериментів конкретного дослідника | `200 OK` / `404 Not Found` |
| `GET` | `/researchers/{id}/statistics` | Статистика вимірювань дослідника (`count`, `avg`, `min`, `max`) | `200 OK` / `404 Not Found` |
| `POST` | `/researchers/batch-statistics` | Асинхронний збір статистики для переліку ID із Semaphore | `200 OK` |
| `GET` | `/experiments` | Список експериментів із фільтрами (`min_result`, `max_result`, `parameter`, `sort_by_date`) | `200 OK` |
| `POST` | `/experiments` | Створення експерименту (з валідацією меж та зовнішнього ключа) | `201 Created` / `422` / `404` |
| `GET` | `/experiments/{id}` | Деталі експерименту за ID | `200 OK` / `404 Not Found` |
| `PATCH` | `/experiments/{id}` | Часткове оновлення результату або приміток експерименту | `200 OK` / `404 Not Found` |
| `DELETE` | `/experiments/{id}` | Видалення запису експерименту за ID | `204 No Content` / `404 Not Found` |
| `GET` | `/experiments/statistics` | Загальна статистика за числовими показниками експериментів | `200 OK` |

---

## 5. Запуск автоматизованих тестів та перевірка покриття

Запуск інтеграційного тестового набору:
```powershell
pytest Lab_08/tests -v --cov=experiment_manager --cov-branch
```

Результати тестування:
- **Успішність:** 13/13 тестів пройдено (100%).
- **Покриття коду:** 88% branch coverage (`src/experiment_manager`).
