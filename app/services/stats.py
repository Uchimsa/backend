import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stats import stats_repo


class StatsService:
    async def get_subject_stats(self, db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
        return await stats_repo.get_subject_stats(db, user_id)

    async def get_sessions(self, db: AsyncSession, user_id: uuid.UUID) -> list:
        return await stats_repo.get_sessions(db, user_id)

    async def get_weak_topics(self, db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
        return await stats_repo.get_weak_topics(db, user_id)


stats_service = StatsService()
