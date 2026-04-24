import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question, QuestionType
from app.models.subject import Subject
from app.models.week import Week
from app.repositories.question import question_repo
from app.repositories.subject import subject_repo
from app.repositories.week import week_repo
from app.services.base import BaseService


class SubjectService(BaseService[Subject]):
    async def list_visible(self, db: AsyncSession) -> list[Subject]:
        return await self.repo.list_visible(db)  # type: ignore[attr-defined]

    async def list_all(self, db: AsyncSession) -> list[Subject]:
        return await self.repo.list_all(db)  # type: ignore[attr-defined]


class WeekService(BaseService[Week]):
    async def list_by_subject(self, db: AsyncSession, subject_id: uuid.UUID) -> list[Week]:
        return await self.repo.list_by_subject(db, subject_id)  # type: ignore[attr-defined]


class QuestionService(BaseService[Question]):
    async def list_by_week(
        self, db: AsyncSession, week_id: uuid.UUID, types: list[QuestionType] | None = None
    ) -> list[Question]:
        return await self.repo.list_by_week(db, week_id, types)  # type: ignore[attr-defined]


subject_service = SubjectService(subject_repo)
week_service = WeekService(week_repo)
question_service = QuestionService(question_repo)
