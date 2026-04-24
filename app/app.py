from fastapi import FastAPI
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
    column_list = [Subject.id, Subject.name, Subject.icon_name, Subject.is_hidden, Subject.created_at]
    column_searchable_list = [Subject.name]
    column_sortable_list = [Subject.name, Subject.created_at]
    can_delete = True


class WeekAdmin(ModelView, model=Week):
    column_list = [Week.id, Week.subject_id, Week.week_number, Week.title]
    column_searchable_list = [Week.title]
    column_sortable_list = [Week.week_number]


class QuestionAdmin(ModelView, model=Question):
    column_list = [Question.id, Question.week_id, Question.type, Question.question_text]
    column_searchable_list = [Question.question_text]
    column_sortable_list = [Question.type, Question.created_at]


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.is_admin, User.created_at]
    column_searchable_list = [User.email]
    form_excluded_columns = [User.hashed_password]
    can_create = False


class StudyPlanAdmin(ModelView, model=StudyPlan):
    column_list = [
        StudyPlan.id, StudyPlan.user_id, StudyPlan.mode,
        StudyPlan.status, StudyPlan.total_items, StudyPlan.started_at,
    ]
    can_create = False
    can_edit = False


class StudySessionAdmin(ModelView, model=StudySession):
    column_list = [
        StudySession.id, StudySession.user_id, StudySession.mode,
        StudySession.accuracy, StudySession.completed_at,
    ]
    can_create = False
    can_edit = False


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ЦУчимся! API", version="1.0.0")
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    app.include_router(router)

    authentication_backend = AdminAuth(secret_key=settings.secret_key)
    admin = Admin(app, engine, authentication_backend=authentication_backend)
    admin.add_view(SubjectAdmin)
    admin.add_view(WeekAdmin)
    admin.add_view(QuestionAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(StudyPlanAdmin)
    admin.add_view(StudySessionAdmin)

    return app


app = create_app()
