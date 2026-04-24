import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.week import Week
from app.repositories.base import BaseRepository


class WeekRepository(BaseRepository[Week]):
    model = Week

    async def list_by_subject(self, db: AsyncSession, subject_id: uuid.UUID) -> list[Week]:
        result = await db.execute(
            select(Week).where(Week.subject_id == subject_id).order_by(Week.week_number)
        )
        return list(result.scalars().all())


week_repo = WeekRepository()
