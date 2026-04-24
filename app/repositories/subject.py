import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.repositories.base import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    model = Subject

    async def list_visible(self, db: AsyncSession) -> list[Subject]:
        result = await db.execute(select(Subject).where(Subject.is_hidden.is_(False)).order_by(Subject.name))
        return list(result.scalars().all())

    async def list_all(self, db: AsyncSession) -> list[Subject]:
        result = await db.execute(select(Subject).order_by(Subject.name))
        return list(result.scalars().all())


subject_repo = SubjectRepository()
