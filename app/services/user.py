import uuid

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.core.settings import get_settings
from app.models.user import User
from app.repositories.user import user_repo
from app.services.base import BaseService


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


class UserService(BaseService[User]):
    async def register(self, db: AsyncSession, email: str, password: str) -> User:
        existing = await user_repo.get_by_email(db, email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        return await user_repo.create(db, email=email, hashed_password=_hash(password))

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> User:
        user = await user_repo.get_by_email(db, email)
        if not user or not _verify(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return user

    def make_token(self, user: User) -> str:
        settings = get_settings()
        return create_access_token(
            {"sub": str(user.id), "email": user.email, "is_admin": user.is_admin},
            settings,
        )

    async def get_subjects(self, db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
        return await user_repo.get_subjects(db, user_id)

    async def set_subjects(
        self, db: AsyncSession, user_id: uuid.UUID, subject_ids: list[uuid.UUID]
    ) -> None:
        await user_repo.set_subjects(db, user_id, subject_ids)


user_service = UserService(user_repo)
