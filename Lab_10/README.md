# Лабораторна робота № 10. Production Python: Docker, CI/CD та захист проєкту

**Індивідуальний варіант:** № 15 — *«Облік результатів наукових експериментів»*  
**Пакет:** `experiment-registry` (`experiment_registry`)  
**Версія:** `1.0.0`  
**Студент:** Франков  
**Дисципліна:** «Програмування на Python»  
**Рік:** 2026  

---

## 1. Опис проєкту

Проєкт **`experiment-registry`** є фінальним етапом розвитку навчальної системи та являє собою повноцінний **production-ready** RESTful мікросервіс для централізованого обліку, валідації та статистичного аналізу результатів наукових експериментів.

Система спроєктована за стандартами промислової розробки:
- **Чиста багатошарова архітектура:** поділ на рівні представлення (FastAPI), бізнес-сервісів (Service Layer), доступу до даних (Repository Layer) та ORM моделей (SQLAlchemy 2.0).
- **Декларативне керування конфігурацією:** безпечне читання змінних середовища та файлів `.env` засобами `pydantic-settings` без збереження секретів у репозиторії.
- **Спостережуваність (Observability):** стандартизований ендпоінт перевірки здоров'я `GET /health` та структуроване логування.
- **Контейнеризація:** оптимізований multi-stage `Dockerfile`, ізоляція через `.dockerignore`, запуск від імені непривілейованого користувача (`non-root user appuser`), інструкція `HEALTHCHECK` та оркестрація через `docker-compose.yml` з persistent volumes для збереження бази даних.
- **Контроль якості коду та CI/CD:** автоматизований пайплайн на базі GitHub Actions із перевіркою форматування (`ruff format`), лінтингу (`ruff check`), статичної типізації (`mypy`), тестів із порогом покриття `pytest --cov-fail-under=85`, автоматичної збірки дистрибутивів `wheel`/`sdist` та збірки Docker image.

---

## 2. Архітектурна схема проєкту

```
                    GitHub Actions (CI/CD Pipeline)
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       ▼                          ▼                          ▼
 Ruff Lint & Format          MyPy Typecheck           Pytest (Cov >= 85%)
                                                             │
                                  ┌──────────────────────────┘
                                  ▼
                        python -m build
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
     Wheel (*.whl) & Sdist (*.tar.gz)       Docker Multi-Stage Build
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                 Release / Production Deployment
                                  │
                                  ▼
                 Client / Orchestrator (Docker / K8s)
                                  │
                                  ▼
                        FastAPI Web Layer
                       (/health, /docs, REST)
                                  │
                                  ▼
                      ExperimentRegistryService
                                  │
                                  ▼
                       Researcher & Experiment
                          Repository Layer
                                  │
                                  ▼
                     SQLite / PostgreSQL Database
                        (Persistent Volumes)
```

---

## 3. Специфікація змінних середовища (Environment Variables)

Конфігурація застосунку повністю винесена за межі вихідного коду відповідно до принципів **The Twelve-Factor App**:

| Змінна середовища | Тип | За замовчуванням | Опис |
|---|---|---|---|
| `APP_NAME` | `str` | `Scientific Experiments Registry` | Назва сервісу |
| `ENVIRONMENT` | `str` | `development` | Середовище запуску (`development`, `test`, `production`) |
| `HOST` | `str` | `0.0.0.0` | IP-адреса для прив'язки веб-сервера |
| `PORT` | `int` | `8000` | Мережевий порт сервісу |
| `DATABASE_URL` | `str` | `sqlite:///./data/experiments.db` | SQLAlchemy connection string |
| `LOG_LEVEL` | `str` | `INFO` | Рівень деталізації логів (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `SECRET_KEY` | `str` | *dev-secret-key* | Секретний ключ криптографічного підпису |
| `CORS_ORIGINS` | `list` | `["*"]` | Дозволені домени клієнтів CORS |

> [!CAUTION]
> Файл `.env` з реальними секретами внесено до `.gitignore` і він **ніколи** не повинен потрапляти у публічні репозиторії! Для налаштування середовища використовуйте шаблон `.env.example`:
> ```bash
> cp .env.example .env
> ```

---

## 4. Встановлення та запуск

### 4.1. Локальне встановлення у віртуальне середовище
```powershell
# Встановлення пакета у режимі розробки
pip install -e ".[dev]"

# Запуск REST API сервера через команду CLI
experiment-registry --host 127.0.0.1 --port 8000
```

### 4.2. Збірка дистрибутивних пакетів (Wheel та Source Distribution)
```powershell
python -m build

# Перевірка згенерованих артефактів:
# dist/experiment_registry-1.0.0-py3-none-any.whl
# dist/experiment_registry-1.0.0.tar.gz
```

### 4.3. Запуск у Docker контейнері
```bash
# 1. Збірка production образу з multi-stage Dockerfile
docker build -t experiment-registry:1.0.0 .

# 2. Запуск контейнера з persistent volume для бази даних
docker run -d \
  --name experiment_registry_app \
  -p 8000:8000 \
  -v experiment_data:/app/data \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  experiment-registry:1.0.0
```

### 4.4. Запуск через Docker Compose
```bash
docker compose up -d --build
```

---

## 5. Документація REST API Endpoints

Після запуску сервісу автоматично генерується інтерактивна документація:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

| HTTP Метод | Шлях | Опис | Статус |
|---|---|---|---|
| `GET` | `/health` | Моніторинг стану сервісу та підключення до БД | `200 OK` |
| `GET` | `/researchers` | Список зареєстрованих дослідників (пагінація `skip`, `limit`) | `200 OK` |
| `POST` | `/researchers` | Реєстрація нового дослідника | `201 Created` |
| `GET` | `/researchers/{id}` | Детальна інформація про дослідника за ID | `200 OK` / `404` |
| `DELETE` | `/researchers/{id}` | Видалення дослідника та каскадне видалення його вимірювань | `204 No Content` |
| `GET` | `/researchers/{id}/experiments` | Список усіх експериментів конкретного дослідника | `200 OK` |
| `GET` | `/researchers/{id}/statistics` | Агрегована статистика вимірювань дослідника | `200 OK` |
| `GET` | `/experiments` | Список експериментів із фільтрацією за діапазоном та сортуванням | `200 OK` |
| `POST` | `/experiments` | Додавання запису експерименту (з валідацією фізичних меж) | `201 Created` / `422` |
| `GET` | `/experiments/{id}` | Отримання даних експерименту за ID | `200 OK` / `404` |
| `DELETE` | `/experiments/{id}` | Видалення запису експерименту | `204 No Content` |
| `GET` | `/experiments/statistics` | Глобальна статистика вимірювань (`count`, `mean`, `min`, `max`, `std_dev`) | `200 OK` |

---

## 6. Контроль якості та CI/CD Pipeline

Усі зміни проходять повний набір локальних та хмарних перевірок:
```powershell
# 1. Перевірка форматування коду
ruff format --check .

# 2. Перевірка лінтером
ruff check .

# 3. Статичний аналіз типів
mypy src

# 4. Запуск автоматизованих тестів із порогом покриття (Fail under 85%)
pytest -v --cov=experiment_registry --cov-report=term-missing --cov-fail-under=85
```

---

## 7. Фінальний Production Checklist для захисту

- [x] **Architecture:** Реалізовано чистий поділ на шари (Models, Repositories, Services, API).
- [x] **Packaging:** Створено `pyproject.toml`, згенеровано `wheel` та `sdist`, перевірено встановлення у чистому `venv`.
- [x] **Configuration:** Використано Pydantic Settings, налаштовано підтримку `.env` та змінних середовища.
- [x] **Security:** Файл `.env` виключено з Git через `.gitignore`, реальні паролі та токени відсутні у репозиторії.
- [x] **Observability:** Реалізовано ендпоінт `GET /health` та структуроване логування.
- [x] **Docker:** Створено Multi-Stage `Dockerfile` із запуском від `non-root` користувача `appuser` та `HEALTHCHECK`.
- [x] **Orchestration:** Налаштовано `docker-compose.yml` з persistent volumes для бази даних.
- [x] **CI/CD:** Створено GitHub Actions workflow для перевірки матриці версій Python, лінтингу, тестів та збірки Docker.
- [x] **Quality:** Забезпечено 100% проходження тестів (18/18) та покриття коду понад 91%.
