import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext, get_current_user
from app.core.deps import get_db
from app.schemas.stats import SessionOut, SubjectStatsOut, WeakTopicOut
from app.services.stats import stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/subjects", response_model=list[SubjectStatsOut])
async def subject_stats(
    user: UserContext = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await stats_service.get_subject_stats(db, uuid.UUID(user.user_id))


@router.get("/sessions", response_model=list[SessionOut])
async def session_history(
    user: UserContext = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await stats_service.get_sessions(db, uuid.UUID(user.user_id))


@router.get("/weak-topics", response_model=list[WeakTopicOut])
async def weak_topics(
    user: UserContext = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await stats_service.get_weak_topics(db, uuid.UUID(user.user_id))
