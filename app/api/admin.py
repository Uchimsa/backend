import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext, require_admin
from app.core.deps import get_db
from app.schemas.catalog import (
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate,
    WeekCreate,
    WeekOut,
    WeekUpdate,
)
from app.services.catalog import question_service, subject_service, week_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects_admin(
    _: UserContext = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    return await subject_service.list_all(db)


@router.post("/subjects", response_model=SubjectOut, status_code=201)
async def create_subject(
    payload: SubjectCreate,
    _: UserContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await subject_service.create(db, **payload.model_dump())


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
async def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    _: UserContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await subject_service.update(db, subject_id, **payload.model_dump(exclude_unset=True))


@router.delete("/subjects/{subject_id}", status_code=204)
async def delete_subject(
    subject_id: uuid.UUID,
    _: UserContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await subject_service.delete(db, subject_id)


@router.post("/weeks", response_model=WeekOut, status_code=201)
async def create_week(
    payload: WeekCreate,
    _: UserContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await week_service.create(db, **payload.model_dump())


@router.patch("/weeks/{week_id}", response_model=WeekOut)
async def update_week(
    week_id: uuid.UUID,
    payload: WeekUpdate,
    _: UserContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await week_service.update(db, week_id, **payload.model_dump(exclude_unset=True))


@router.delete("/weeks/{week_id}", status_code=204)
async def delete_week(
    week_id: uuid.UUID,
    _: UserContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await week_service.delete(db, week_id)


@router.post("/questions", response_model=QuestionOut, status_code=201)
async def create_question(
    payload: QuestionCreate,
    _: UserContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await question_service.create(db, **payload.model_dump())


@router.patch("/questions/{question_id}", response_model=QuestionOut)
async def update_question(
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    _: UserContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await question_service.update(db, question_id, **payload.model_dump(exclude_unset=True))


@router.delete("/questions/{question_id}", status_code=204)
async def delete_question(
    question_id: uuid.UUID,
    _: UserContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await question_service.delete(db, question_id)
