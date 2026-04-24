import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question, QuestionType
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    model = Question

    async def list_by_week(
        self,
        db: AsyncSession,
        week_id: uuid.UUID,
        types: list[QuestionType] | None = None,
    ) -> list[Question]:
        query = select(Question).where(Question.week_id == week_id)
        if types:
            query = query.where(Question.type.in_(types))
        result = await db.execute(query)
        return list(result.scalars().all())

    async def list_by_weeks(
        self,
        db: AsyncSession,
        week_ids: list[uuid.UUID],
        types: list[QuestionType] | None = None,
    ) -> list[Question]:
        query = select(Question).where(Question.week_id.in_(week_ids))
        if types:
            query = query.where(Question.type.in_(types))
        result = await db.execute(query)
        return list(result.scalars().all())


question_repo = QuestionRepository()
