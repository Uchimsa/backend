from typing import Any, Generic, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.repositories.base import BaseRepository, ModelT


class BaseService(Generic[ModelT]):
    def __init__(self, repo: BaseRepository[ModelT]) -> None:
        self.repo = repo

    async def get_or_404(self, db: AsyncSession, id: Any) -> ModelT:
        instance = await self.repo.get(db, id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return instance

    async def list(self, db: AsyncSession) -> list[ModelT]:
        return await self.repo.list(db)

    async def create(self, db: AsyncSession, **data: Any) -> ModelT:
        return await self.repo.create(db, **data)

    async def update(self, db: AsyncSession, id: Any, **data: Any) -> ModelT:
        instance = await self.get_or_404(db, id)
        return await self.repo.update(db, instance, **data)

    async def delete(self, db: AsyncSession, id: Any) -> None:
        instance = await self.get_or_404(db, id)
        await self.repo.delete(db, instance)
