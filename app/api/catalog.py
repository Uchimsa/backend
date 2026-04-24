import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query  # <-- Добавлен импорт Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.question import QuestionType
from app.schemas.catalog import QuestionOut, SubjectOut, WeekOut
from app.services.catalog import question_service, subject_service, week_service

router = APIRouter(tags=["catalog"])


@router.get("/subjects", response_model=list[SubjectOut])
async def get_subjects(db: AsyncSession = Depends(get_db)):
    return await subject_service.list_visible(db)


@router.get("/subjects/{subject_id}/weeks", response_model=list[WeekOut])
async def get_weeks(subject_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await week_service.list_by_subject(db, subject_id)


@router.get("/weeks/{week_id}/questions", response_model=list[QuestionOut])
async def get_questions(
    week_id: uuid.UUID,
    types: Optional[list[QuestionType]] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await question_service.list_by_week(db, week_id, types)
