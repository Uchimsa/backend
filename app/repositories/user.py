import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_subject import UserSubject
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_subjects(self, db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
        result = await db.execute(
            select(UserSubject.subject_id).where(UserSubject.user_id == user_id)
        )
        return list(result.scalars().all())

    async def set_subjects(
        self, db: AsyncSession, user_id: uuid.UUID, subject_ids: list[uuid.UUID]
    ) -> None:
        await db.execute(delete(UserSubject).where(UserSubject.user_id == user_id))
        for subject_id in subject_ids:
            db.add(UserSubject(user_id=user_id, subject_id=subject_id))
        await db.flush()


user_repo = UserRepository()
