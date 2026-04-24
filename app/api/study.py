import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext, get_current_user
from app.core.deps import get_db
from app.schemas.catalog import QuestionOut
from app.schemas.study import (
    FlashcardAnswerIn,
    FlashcardAnswerOut,
    SkipTaskIn,
    StudyPlanCreate,
    StudyPlanItemOut,
    StudyPlanOut,
    StudyPlanProgressOut,
    TaskAnswerIn,
    TaskAnswerOut,
    TestAnswerIn,
    TestAnswerOut,
)
from app.services.study import study_service

router = APIRouter(prefix="/study", tags=["study"])


@router.post("/plans", response_model=StudyPlanOut, status_code=201)
async def create_plan(
    payload: StudyPlanCreate,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await study_service.create_plan(
        db,
        uuid.UUID(user.user_id),
        payload.mode,
        payload.week_ids,
        payload.max_items,
        payload.shuffle,
        payload.time_limit_seconds,
    )


@router.get("/plans/{plan_id}", response_model=StudyPlanProgressOut)
async def get_plan(
    plan_id: uuid.UUID,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await study_service.get_progress(db, uuid.UUID(user.user_id), plan_id)


@router.get("/plans/{plan_id}/next", response_model=StudyPlanItemOut)
async def next_item(
    plan_id: uuid.UUID,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await study_service.get_next_item(db, plan_id, uuid.UUID(user.user_id))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No remaining items")
    return StudyPlanItemOut(
        plan_id=plan_id,
        question_id=result["item"].question_id,
        position=result["item"].position,
        question=QuestionOut.model_validate(result["question"]),
    )


@router.post("/plans/{plan_id}/answer/test", response_model=TestAnswerOut)
async def submit_test_answer(
    plan_id: uuid.UUID,
    payload: TestAnswerIn,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await study_service.submit_test_answer(
        db, uuid.UUID(user.user_id), plan_id, payload.question_id, payload.chosen_option_index
    )


@router.post("/plans/{plan_id}/answer/flashcard", response_model=FlashcardAnswerOut)
async def submit_flashcard_answer(
    plan_id: uuid.UUID,
    payload: FlashcardAnswerIn,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await study_service.submit_flashcard_answer(
        db, uuid.UUID(user.user_id), plan_id, payload.question_id, payload.knowledge_level
    )


@router.post("/plans/{plan_id}/answer/task", response_model=TaskAnswerOut)
async def submit_task_answer(
    plan_id: uuid.UUID,
    payload: TaskAnswerIn,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await study_service.submit_task_answer(
        db, uuid.UUID(user.user_id), plan_id, payload.question_id, payload.answer_text
    )


@router.post("/plans/{plan_id}/skip", response_model=StudyPlanProgressOut)
async def skip_task(
    plan_id: uuid.UUID,
    payload: SkipTaskIn,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await study_service.skip_task(
        db, uuid.UUID(user.user_id), plan_id, payload.question_id
    )
