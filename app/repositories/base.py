from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    async def get(self, db: AsyncSession, id: Any) -> ModelT | None:
        return await db.get(self.model, id)

    async def list(self, db: AsyncSession) -> list[ModelT]:
        result = await db.execute(select(self.model))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, **data: Any) -> ModelT:
        instance = self.model(**data)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update(self, db: AsyncSession, instance: ModelT, **data: Any) -> ModelT:
        for key, value in data.items():
            setattr(instance, key, value)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def delete(self, db: AsyncSession, instance: ModelT) -> None:
        await db.delete(instance)
        await db.flush()
