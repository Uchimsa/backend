from fastapi import FastAPI
from markupsafe import Markup
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from app.core.auth import _decode_token
from app.core.database import engine
from app.core.settings import get_settings
from app.models.question import Question
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.subject import Subject
from app.models.user import User
from app.models.week import Week
from app.router import router

_TYPE_LABELS = {"test": "Тест", "task": "Задача", "flashcard": "Карточка"}
_STATUS_LABELS = {"active": "Активен", "completed": "Завершён"}
_MODE_LABELS = {"test": "Тест", "task": "Задача", "flashcard": "Карточки"}


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        token = str(form.get("password", ""))
        try:
            settings = get_settings()
            payload = _decode_token(token, settings)
            if payload.get("is_admin"):
                request.session.update({"token": token})
                return True
        except Exception:
            pass
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        try:
            settings = get_settings()
            payload = _decode_token(token, settings)
            return bool(payload.get("is_admin"))
        except Exception:
            return False


class SubjectAdmin(ModelView, model=Subject):
    name = "Предмет"
    name_plural = "Предметы"
    icon = "fa-solid fa-book"

    column_list = [Subject.name, Subject.icon_name, Subject.is_hidden, Subject.created_at]
    column_searchable_list = [Subject.name]
    column_sortable_list = [Subject.name, Subject.is_hidden, Subject.created_at]
    column_default_sort = [(Subject.name, False)]

    column_labels = {
        Subject.name: "Название",
        Subject.icon_name: "Иконка",
        Subject.is_hidden: "Скрыт",
        Subject.created_at: "Создан",
    }

    form_args = {
        "name": {
            "label": "Название предмета",
            "description": "Полное название курса, например: «Вероятность и Статистика»",
        },
        "icon_name": {
            "label": "Иконка",
            "description": "Название иконки из библиотеки Font Awesome без префикса fa-, например: calculator, flask, chart-bar",
        },
        "is_hidden": {
            "label": "Скрыть предмет",
            "description": "Скрытый предмет не отображается у студентов, но данные сохраняются",
        },
    }

    column_formatters = {
        Subject.is_hidden: lambda m, a: (
            Markup('<span style="color:red">●  Скрыт</span>')
            if m.is_hidden
            else Markup('<span style="color:green">●  Виден</span>')
        ),
    }


class WeekAdmin(ModelView, model=Week):
    name = "Неделя (тема)"
    name_plural = "Недели (темы)"
    icon = "fa-solid fa-calendar-week"

    column_list = [Week.subject, Week.week_number, Week.title, Week.created_at]
    column_searchable_list = [Week.title]
    column_sortable_list = [Week.week_number, Week.created_at]
    column_default_sort = [(Week.week_number, False)]

    column_labels = {
        "subject": "Предмет",
        Week.week_number: "Номер недели",
        Week.title: "Тема",
        Week.created_at: "Создана",
    }

    form_args = {
        "subject": {
            "label": "Предмет",
            "description": "К какому курсу относится эта неделя",
        },
        "week_number": {
            "label": "Номер недели",
            "description": "Порядковый номер, например: 1, 2, 13. Используется для сортировки",
        },
        "title": {
            "label": "Тема",
            "description": "Название темы, например: «Неделя 13. Определённый интеграл»",
        },
    }

    form_ajax_refs = {
        "subject": {
            "fields": ("name",),
            "order_by": "name",
        }
    }


class QuestionAdmin(ModelView, model=Question):
    name = "Вопрос / Карточка"
    name_plural = "Вопросы и карточки"
    icon = "fa-solid fa-circle-question"

    column_list = [Question.week, Question.type, Question.question_text, Question.created_at]
    column_searchable_list = [Question.question_text]
    column_sortable_list = [Question.type, Question.created_at]
    column_default_sort = [(Question.created_at, True)]

    column_labels = {
        "week": "Неделя",
        Question.type: "Тип",
        Question.question_text: "Вопрос",
        Question.answer_text: "Ответ / Определение",
        Question.options: "Варианты ответа",
        Question.correct_option_index: "Верный вариант (индекс)",
        Question.explanation: "Пояснение / Решение",
        Question.created_at: "Создан",
    }

    column_formatters = {
        Question.type: lambda m, a: _TYPE_LABELS.get(m.type.value, m.type.value),
        Question.question_text: lambda m, a: (
            (m.question_text[:80] + "…") if len(m.question_text) > 80 else m.question_text
        ),
    }

    form_args = {
        "week": {
            "label": "Неделя (тема)",
            "description": "К какой неделе относится этот вопрос",
        },
        "type": {
            "label": "Тип вопроса",
            "description": (
                "Тест — 4 варианта ответа, один верный. "
                "Задача — студент вводит развёрнутый ответ, оценивается нейросетью. "
                "Карточка — студент оценивает, знает ли он определение (Знаю / Повторить / Не знаю)."
            ),
        },
        "question_text": {
            "label": "Текст вопроса",
            "description": (
                "Поддерживается Markdown и LaTeX. "
                "Формулы в строке: $x^2$, блочные: $$\\int_0^1 x\\,dx$$. "
                "Жирный: **текст**, курсив: *текст*, код: `код`."
            ),
        },
        "answer_text": {
            "label": "Ответ / Определение",
            "description": (
                "Для Задачи — эталонное решение (Markdown + LaTeX), по которому нейросеть оценивает студента. "
                "Для Карточки — определение термина, которое показывается студенту при нажатии «Пояснение»."
            ),
        },
        "options": {
            "label": "Варианты ответа (только для Теста)",
            "description": (
                "Только для типа «Тест». JSON-массив ровно из 4 строк. "
                'Пример: ["Первый вариант", "Второй вариант", "Третий вариант", "Четвёртый вариант"]. '
                "Для Задачи и Карточки оставьте пустым."
            ),
        },
        "correct_option_index": {
            "label": "Индекс верного ответа (только для Теста)",
            "description": (
                "Только для типа «Тест». Номер верного варианта начиная с 0: "
                "0 = первый вариант, 1 = второй, 2 = третий, 3 = четвёртый. "
                "Для Задачи и Карточки оставьте пустым."
            ),
        },
        "explanation": {
            "label": "Подробное пояснение / Решение",
            "description": (
                "Для Теста — подробный разбор, который студент видит после ответа. "
                "Для Задачи — расширенный разбор решения. "
                "Для Карточки — дополнительное пояснение к определению. "
                "Поддерживается Markdown + LaTeX."
            ),
        },
    }

    form_ajax_refs = {
        "week": {
            "fields": ("title",),
            "order_by": "week_number",
        }
    }


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-users"

    column_list = [User.email, User.is_admin, User.created_at]
    column_searchable_list = [User.email]
    column_sortable_list = [User.email, User.is_admin, User.created_at]
    column_default_sort = [(User.created_at, True)]

    column_labels = {
        User.email: "Email",
        User.is_admin: "Администратор",
        User.created_at: "Зарегистрирован",
    }

    column_formatters = {
        User.is_admin: lambda m, a: (
            Markup('<span style="color:#b91c1c;font-weight:600">★ Админ</span>')
            if m.is_admin
            else "—"
        ),
    }

    form_excluded_columns = [User.hashed_password, User.is_admin]
    can_create = False


class StudyPlanAdmin(ModelView, model=StudyPlan):
    name = "План обучения"
    name_plural = "Планы обучения"
    icon = "fa-solid fa-list-check"

    column_list = [
        StudyPlan.mode,
        StudyPlan.status,
        StudyPlan.total_items,
        StudyPlan.correct_count,
        StudyPlan.wrong_count,
        StudyPlan.started_at,
        StudyPlan.completed_at,
    ]
    column_sortable_list = [StudyPlan.started_at, StudyPlan.status, StudyPlan.mode]
    column_default_sort = [(StudyPlan.started_at, True)]

    column_labels = {
        StudyPlan.mode: "Режим",
        StudyPlan.status: "Статус",
        StudyPlan.total_items: "Всего",
        StudyPlan.correct_count: "Верных",
        StudyPlan.wrong_count: "Неверных",
        StudyPlan.skipped_count: "Пропущено",
        StudyPlan.started_at: "Начат",
        StudyPlan.completed_at: "Завершён",
    }

    column_formatters = {
        StudyPlan.mode: lambda m, a: _MODE_LABELS.get(m.mode.value, m.mode.value),
        StudyPlan.status: lambda m, a: (
            Markup('<span style="color:green">Завершён</span>')
            if m.status.value == "completed"
            else Markup('<span style="color:orange">Активен</span>')
        ),
    }

    can_create = False
    can_edit = False


class StudySessionAdmin(ModelView, model=StudySession):
    name = "Сессия"
    name_plural = "Сессии (завершённые планы)"
    icon = "fa-solid fa-chart-line"

    column_list = [
        StudySession.mode,
        StudySession.total_cards,
        StudySession.correct_count,
        StudySession.wrong_count,
        StudySession.accuracy,
        StudySession.completed_at,
    ]
    column_sortable_list = [StudySession.completed_at, StudySession.accuracy, StudySession.mode]
    column_default_sort = [(StudySession.completed_at, True)]

    column_labels = {
        StudySession.mode: "Режим",
        StudySession.total_cards: "Карточек",
        StudySession.correct_count: "Верных",
        StudySession.wrong_count: "Неверных",
        StudySession.skipped_count: "Пропущено",
        StudySession.accuracy: "Точность",
        StudySession.completed_at: "Дата",
    }

    column_formatters = {
        StudySession.mode: lambda m, a: _MODE_LABELS.get(m.mode.value, m.mode.value),
        StudySession.accuracy: lambda m, a: f"{m.accuracy * 100:.1f}%",
    }

    can_create = False
    can_edit = False


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ЦУчимся! API", version="1.0.0")
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    app.include_router(router)

    authentication_backend = AdminAuth(secret_key=settings.secret_key)
    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title="ЦУчимся! — Админка",
    )
    admin.add_view(SubjectAdmin)
    admin.add_view(WeekAdmin)
    admin.add_view(QuestionAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(StudyPlanAdmin)
    admin.add_view(StudySessionAdmin)

    return app


app = create_app()
