# PROJECT_PLAN.md — ЦУчимся! Backend

## Текущее состояние

Проект частично реализован на FastAPI + Supabase (Python SDK). Есть слои `api` и `services`,
Pydantic-схемы в `models`, базовая JWT-авторизация через Supabase JWT.

**Что нужно переделать полностью:**

- Убрать Supabase SDK, перейти на прямой PostgreSQL через SQLAlchemy
- Добавить слой `repositories` с `BaseRepository[T]`
- Добавить `BaseService` поверх репозитория
- Добавить SQLAlchemy ORM-модели (отдельно от Pydantic-схем)
- Настроить Docker-окружения, Traefik, Makefile
- Добавить тесты (testcontainers)
- Добавить административный веб-интерфейс

---

## Фазы реализации

---

### Фаза 1. Структура и инфраструктура проекта

#### 1.1 Реорганизация директорий

Привести к виду:

```
app/
├── api/          # роутеры (тонкие, только HTTP-слой)
├── services/     # бизнес-логика, используют репозитории и другие сервисы
├── repositories/ # CRUD поверх SQLAlchemy, BaseRepository[T]
├── models/       # SQLAlchemy ORM-модели (таблицы)
├── schemas/      # Pydantic-схемы (запросы/ответы API)
└── core/         # настройки, DI, утилиты
```

Текущие `app/models/` (Pydantic) переименовать в `app/schemas/`.
Создать `app/models/` для SQLAlchemy ORM-моделей.
Создать `app/repositories/`.

#### 1.2 Переход с Supabase SDK на SQLAlchemy + asyncpg

- Убрать зависимости `supabase`, `python-jose` (заменить на `PyJWT` или `python-jose` оставить)
- Добавить зависимости:
  - `sqlalchemy[asyncio]>=2.0`
  - `asyncpg` — async-драйвер для PostgreSQL
  - `alembic` — миграции
  - `passlib[bcrypt]` — хеширование паролей
  - `python-jose[cryptography]` — JWT (уже есть)
  - `sqladmin` — административная панель (современная замена flask-admin для FastAPI)
  - `testcontainers[postgres]` — для тестов
  - `pytest-asyncio`, `httpx` — тесты

- Создать `app/core/database.py`:
  - `AsyncEngine`, `AsyncSessionLocal`, `get_db` (Depends)
  - `Base = DeclarativeBase()`

#### 1.3 BaseRepository

Файл `app/repositories/base.py`:

```python
class BaseRepository[T: Base]:
    model: type[T]

    async def get(self, db, id) -> T | None
    async def list(self, db, **filters) -> list[T]
    async def create(self, db, data: dict) -> T
    async def update(self, db, id, data: dict) -> T
    async def delete(self, db, id) -> None
```

Все репозитории наследуются: `class SubjectRepository(BaseRepository[Subject])`.

#### 1.4 BaseService

Файл `app/services/base.py`:

```python
class BaseService[T]:
    def __init__(self, repo: BaseRepository[T]):
        self.repo = repo

    # делегирует в repo с бизнес-правилами поверх
    async def get(self, db, id) -> T
    async def list(self, db, **filters) -> list[T]
    async def create(self, db, schema) -> T
    async def update(self, db, id, schema) -> T
    async def delete(self, db, id) -> None
```

#### 1.5 Настройки (`app/core/settings.py`)

Убрать Supabase-специфичные поля, добавить:

- `database_url: str` — строка подключения к PostgreSQL
- `secret_key: str` — для подписи JWT
- `jwt_algorithm: str = "HS256"`
- `access_token_expire_minutes: int = 60`

---

### Фаза 2. ORM-модели и миграции

#### 2.1 SQLAlchemy ORM-модели (`app/models/`)

**`subject.py`** — таблица `subjects`:

- `id: UUID PK`
- `name: str`
- `icon_name: str | None`
- `is_hidden: bool = False` ← для скрытия из каталога без удаления
- `created_at: datetime`

**`week.py`** — таблица `weeks`:

- `id: UUID PK`
- `subject_id: UUID FK → subjects`
- `week_number: int`
- `title: str`
- `created_at: datetime`

**`question.py`** — таблица `questions`:

- `id: UUID PK`
- `week_id: UUID FK → weeks`
- `type: Enum("test", "task", "flashcard")`
- `question_text: str` — формат md+LaTeX
- `answer_text: str | None` — md+LaTeX, для задач
- `options: JSON | None` — список из 4 строк (только для type=test)
- `correct_option_index: int | None` — (только для type=test)
- `explanation: str | None` — подробное решение, md+LaTeX
- `created_at: datetime`

**`user.py`** — таблица `users`:

- `id: UUID PK`
- `email: str UNIQUE`
- `hashed_password: str`
- `is_admin: bool = False`
- `created_at: datetime`

**`user_subject.py`** — таблица `user_subjects` (M2M):

- `user_id: UUID FK → users`
- `subject_id: UUID FK → subjects`

**`study_plan.py`** — таблица `study_plans`:

- `id: UUID PK`
- `user_id: UUID FK → users`
- `mode: Enum("test", "task", "flashcard")`
- `total_items: int`
- `correct_count: int = 0`
- `wrong_count: int = 0`
- `skipped_count: int = 0`
- `status: Enum("active", "completed") = "active"`
- `time_limit_seconds: int | None` — лимит времени на весь план
- `started_at: datetime`
- `completed_at: datetime | None`

**`study_plan_item.py`** — таблица `study_plan_items`:

- `id: UUID PK`
- `plan_id: UUID FK → study_plans`
- `question_id: UUID FK → questions`
- `position: int`
- `is_correct: bool | None`
- `is_known: bool | None` — для flashcard (Знаю/Не знаю)
- `is_skipped: bool = False` — для task (можно скипнуть)
- `user_answer_text: str | None` — текстовый ответ пользователя
- `ai_score: float | None` — 0.0–1.0 от нейронки (для task)
- `ai_explanation: str | None` — пояснение от нейронки
- `answered_at: datetime | None`

**`user_progress.py`** — таблица `user_progress`:

- `id: UUID PK`
- `user_id: UUID FK → users`
- `question_id: UUID FK → questions`
- `status: Enum("learning", "mastered")`
- `views: int = 0`
- `correct_streak: int = 0`
- `ease_factor: float = 2.5`
- `interval_days: int = 0`
- `last_reviewed_at: datetime | None`

**`study_session.py`** — таблица `study_sessions`:

- `id: UUID PK`
- `user_id: UUID FK → users`
- `plan_id: UUID FK → study_plans`
- `mode: Enum("test", "task", "flashcard")`
- `subject_id: UUID FK → subjects`
- `total_cards: int`
- `correct_count: int`
- `wrong_count: int`
- `skipped_count: int`
- `accuracy: float` — вычисляемое при сохранении
- `completed_at: datetime`

#### 2.2 Alembic

- `alembic init alembic`
- Настроить `env.py` на `AsyncEngine` + `Base.metadata`
- Первая миграция: создание всех таблиц
- Добавить команду `make migrate` в Makefile

---

### Фаза 3. Аутентификация и пользователи

#### 3.1 Схемы (`app/schemas/auth.py`, `app/schemas/user.py`)

- `RegisterIn(email, password)`
- `LoginIn(email, password)`
- `TokenOut(access_token, token_type)`
- `UserOut(id, email, is_admin, created_at)`

#### 3.2 `UserRepository(BaseRepository[User])`

- `get_by_email(db, email) -> User | None`

#### 3.3 `UserService(BaseService[User])`

- `register(db, email, password) -> User` — хеш пароля через `passlib`
- `authenticate(db, email, password) -> User | HTTPException`
- `create_access_token(user) -> str` — JWT с `user_id`, `email`, `is_admin`

#### 3.4 API (`app/api/auth.py`)

- `POST /auth/register`
- `POST /auth/login` → `TokenOut`

#### 3.5 DI (`app/core/deps.py`)

- `get_db` — сессия из `AsyncSessionLocal`
- `get_current_user(token) -> UserContext` — декодирование JWT
- `require_admin(user) -> UserContext` — проверка `is_admin`

---

### Фаза 4. Каталог (предметы и недели)

#### 4.1 Репозитории

- `SubjectRepository(BaseRepository[Subject])`
  - `list_visible(db) -> list[Subject]` — только `is_hidden=False`
  - `list_all(db) -> list[Subject]` — включая скрытые (для админа)
- `WeekRepository(BaseRepository[Week])`
  - `list_by_subject(db, subject_id) -> list[Week]`
- `QuestionRepository(BaseRepository[Question])`
  - `list_by_week(db, week_id, types=None) -> list[Question]`
  - `list_by_weeks(db, week_ids, types=None) -> list[Question]`

#### 4.2 Сервисы

- `SubjectService(BaseService[Subject])`
- `WeekService(BaseService[Week])`
- `QuestionService(BaseService[Question])`

#### 4.3 API (публичные)

- `GET /subjects` — список видимых предметов
- `GET /subjects/{id}/weeks` — недели предмета
- `GET /weeks/{id}/questions?types=` — вопросы недели по типу

#### 4.4 API пользователя

- `GET /me/subjects` — подписки пользователя
- `PUT /me/subjects` — обновить подписки

---

### Фаза 5. Режим Тест

**Сценарий:**

1. Пользователь выбирает предмет + неделю (опционально) → `POST /study/plans`
2. Сервер создаёт `StudyPlan` (mode=test, time_limit_seconds=600 по умолчанию)
3. `GET /study/plans/{id}/next` → возвращает вопрос с 4 вариантами (без правильного ответа)
4. `POST /study/plans/{id}/answer` → `{question_id, chosen_option_index}`
5. Ответ содержит `is_correct`, `explanation`
6. По истечении `time_limit_seconds` или всех вопросов → статус `completed`

**Реализация:**

- `StudyService.create_plan(db, user_id, mode, week_ids, max_items, time_limit_seconds, shuffle)`
- `StudyService.get_next(db, user_id, plan_id) -> StudyPlanItem | None`
- `StudyService.submit_test_answer(db, user_id, plan_id, question_id, chosen_option_index)`
  - Проверяет `chosen_option_index == question.correct_option_index`
  - Обновляет `study_plan_items`, `user_progress`, счётчики плана
- Схемы: `TestAnswerIn(question_id, chosen_option_index)`, `TestAnswerOut(is_correct, correct_option_index, explanation)`

---

### Фаза 6. Режим Задача

**Сценарий:**

1. Создаётся план (mode=task)
2. Пользователю выдаётся условие задачи (md+LaTeX)
3. Пользователь присылает ответ одним из способов:
   - Текст + LaTeX → `POST /study/plans/{id}/answer` с `{answer_text}`
   - Фото → `POST /study/plans/{id}/answer/photo` с файлом → OCR-сервис → LaTeX
4. Ответ + эталонное решение скармливается LLM → `score (0/1 + logprob)`, `ai_explanation`
5. Пользователь видит: «Верно» / «Неверно» + пояснение нейронки + эталонное решение
6. Пользователь может скипнуть задачу → `POST /study/plans/{id}/skip`

**Реализация:**

- `TaskScanService.scan_photo(image_bytes) -> str (LaTeX)` — запрос к `math.cu-trainer.ru` (сейчас мок)
- `AIEvaluationService.evaluate(question, reference_answer, user_answer) -> EvalResult`
  - Запрос к LLM (Anthropic Claude API)
  - Парсинг logprob для уверенности
  - Возвращает `score: float`, `explanation: str`
- `StudyService.submit_task_answer(db, user_id, plan_id, question_id, answer_text)`
- `StudyService.skip_task(db, user_id, plan_id, question_id)`
- Схемы: `TaskAnswerIn(answer_text)`, `TaskAnswerOut(score, ai_explanation, reference_answer, explanation)`

---

### Фаза 7. Режим Карточки (Flashcards)

**Сценарий:**

1. Создаётся план (mode=flashcard, time_limit_seconds=опционально)
2. Показывается карточка с термином/вопросом (md+LaTeX)
3. Пользователь может нажать «Пояснение» → показывается `explanation`
4. Пользователь выбирает: `Знаю` / `Надо повторить` / `Не знаю`
5. Статистика: `Знаю` → mastered, остальное → learning

**Реализация:**

- `StudyService.submit_flashcard_answer(db, user_id, plan_id, question_id, knowledge_level)`
  - `knowledge_level: Enum("known", "repeat", "unknown")`
  - `is_known = (knowledge_level == "known")`
  - `is_correct = is_known`
- Схемы: `FlashcardAnswerIn(question_id, knowledge_level)`, `FlashcardAnswerOut(definition, explanation)`

---

### Фаза 8. Статистика

#### 8.1 Репозитории

- `StudySessionRepository(BaseRepository[StudySession])`
  - `list_by_user(db, user_id, limit=50) -> list[StudySession]`
  - `list_by_user_and_subject(db, user_id, subject_id) -> list[StudySession]`
- `UserProgressRepository(BaseRepository[UserProgress])`
  - `get_by_user_and_question(db, user_id, question_id) -> UserProgress | None`
  - `summary_by_subject(db, user_id, subject_id) -> dict`

#### 8.2 API статистики

- `GET /stats/subjects` — сводка по всем предметам пользователя:
  ```json
  [{"subject_id", "subject_name", "correct_count", "wrong_count", "accuracy"}]
  ```
- `GET /stats/subjects/{id}` — детальная статистика по предмету (по неделям)
- `GET /stats/sessions` — история сессий (для графиков прогресса по времени)
- `GET /stats/progress` — слабые темы: вопросы со статусом `learning` и низким `ease_factor`

---

### Фаза 9. Административный интерфейс

Использовать **SQLAdmin** (`sqladmin`) — современная веб-панель для FastAPI + SQLAlchemy.

- Подключить `Admin(app, engine)` с базовой HTTP-аутентификацией через `is_admin`
- Создать `ModelView` для каждой модели:
  - `SubjectAdmin` — управление предметами, переключение `is_hidden`
  - `WeekAdmin` — управление неделями, выбор предмета
  - `QuestionAdmin` — управление вопросами, markdown-предпросмотр, фильтр по типу/неделе
  - `UserAdmin` — просмотр пользователей (без показа пароля)
  - `StudySessionAdmin` — просмотр сессий, статистика
- Маршрут: `/admin` (защищён через `is_admin`)

---

### Фаза 10. Docker и инфраструктура

#### 10.1 Docker-файлы

**`Dockerfile`** (production):

```dockerfile
FROM python:3.12-slim
# uv для установки зависимостей
# копируем только нужное, не venv
# CMD granian
```

**`docker-compose.yaml`** — общая база:

- сервис `app` (образ из Dockerfile)
- сервис `db` (PostgreSQL 16)
- общая сеть `uchimsa-net`
- volumes для данных postgres

**`docker-compose.dev.yaml`** — оверрайд для разработки:

- монтирование исходников `./app:/app/app`
- `--reload` для hot-reload
- `ports: 8000:8000` напрямую
- `POSTGRES_*` переменные для локальной БД

**`docker-compose.prod.yaml`** — оверрайд для продакшна:

- Traefik как reverse-proxy с автоматическим Let's Encrypt
- Traefik labels на сервисе `app`
- Только внутренняя сеть для БД (не пробрасывать порты наружу)
- `restart: always`

#### 10.2 Makefile

```makefile
dev:       # docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up --build
up:        # docker compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d --build
down:      # docker compose down
migrate:   # docker compose exec app alembic upgrade head
test:      # uv run pytest tests/ -v
lint:      # uv run ruff check app/
fmt:       # uv run ruff format app/
```

---

### Фаза 11. Тесты

Использовать `testcontainers[postgres]` + `pytest-asyncio` + `httpx.AsyncClient`.

#### 11.1 Фикстуры (`tests/conftest.py`)

- `postgres_container` — поднимает контейнер с PostgreSQL
- `db_session` — AsyncSession для тестов
- `client` — `AsyncClient` поверх тестового приложения с тестовой БД
- `auth_headers(user)` — готовые заголовки с токеном

#### 11.2 Тесты CRUD (базовые)

- `tests/test_subjects.py` — создать, получить, обновить, скрыть, удалить предмет
- `tests/test_weeks.py` — CRUD недель
- `tests/test_questions.py` — CRUD вопросов всех типов

#### 11.3 Тесты сценариев (бизнес-логика)

- `tests/test_auth.py`:
  - Регистрация → логин → получение токена
  - Попытка войти с неверным паролем → 401
  - Доступ к /admin без `is_admin` → 403

- `tests/test_study_test_mode.py`:
  - Создать план (test), получить вопросы, ответить правильно/неправильно, дойти до конца → статус completed
  - Проверить, что `study_session` создался с правильной статистикой
  - Повторный ответ на тот же вопрос → 409

- `tests/test_study_flashcard_mode.py`:
  - Полный цикл flashcard (Знаю / Надо повторить / Не знаю)
  - Проверить `user_progress` после сессии

- `tests/test_study_task_mode.py`:
  - Skip задачи
  - Текстовый ответ → мок AI-оценки → проверить `ai_score` в `study_plan_items`

- `tests/test_stats.py`:
  - Завершить несколько сессий → проверить агрегаты `/stats/subjects`
  - Проверить точность (accuracy) в ответе

---

## Порядок реализации (приоритеты)

| #   | Фаза                                            | Приоритет     |
| --- | ----------------------------------------------- | ------------- |
| 1   | Структура + SQLAlchemy + BaseRepository/Service | Критично      |
| 2   | ORM-модели + Alembic миграции                   | Критично      |
| 3   | Auth (регистрация/логин, JWT)                   | Критично      |
| 4   | Каталог (Subject, Week, Question CRUD)          | Высокий       |
| 5   | Режим Тест                                      | Высокий       |
| 6   | Режим Карточки                                  | Высокий       |
| 7   | Статистика (базовая)                            | Высокий       |
| 8   | Режим Задача (текстовый ответ + мок AI)         | Средний       |
| 9   | Административный интерфейс (SQLAdmin)           | Средний       |
| 10  | Docker + Traefik + Makefile                     | Средний       |
| 11  | Тесты                                           | Средний       |
| 12  | Режим Задача (фото + реальный AI)               | Низкий (MVP+) |

---

## Зависимости для установки

```toml
# pyproject.toml
dependencies = [
    "fastapi>=0.115",
    "granian>=2.7",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "alembic>=1.13",
    "pydantic-settings>=2.0",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "sqladmin>=0.18",
    "anthropic>=0.30",  # для AI-оценки задач
    "httpx>=0.27",      # для запросов к math.cu-trainer.ru
]

[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "testcontainers[postgres]>=4",
    "ruff>=0.4",
]
```

---

## Что удалить из текущего проекта

- `app/core/supabase.py` — Supabase клиент
- `app/services/supabase_utils.py` — утилиты для Supabase SDK
- `app/services/admin.py` — заменить на SQLAdmin ModelView
- `supabase/` директорию (если есть)
- `plan.md` (уже удалён по git status)
