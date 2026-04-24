import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext, get_current_user
from app.core.deps import get_db
from app.schemas.user import UserOut, UserSubjectsUpdate
from app.services.user import user_service

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=UserOut)
async def get_me(
    user: UserContext = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await user_service.get_or_404(db, uuid.UUID(user.user_id))


@router.get("/subjects")
async def get_my_subjects(
    user: UserContext = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    subject_ids = await user_service.get_subjects(db, uuid.UUID(user.user_id))
    return {"subject_ids": subject_ids}


@router.put("/subjects", status_code=204)
async def set_my_subjects(
    payload: UserSubjectsUpdate,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await user_service.set_subjects(db, uuid.UUID(user.user_id), payload.subject_ids)
