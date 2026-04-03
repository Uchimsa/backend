from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import UserContext, get_current_user
from app.core.deps import get_supabase_dep
from app.models.catalog import QuestionOut
from app.models.study import (
    StudyAnswerIn,
    StudyPlanCreate,
    StudyPlanItemOut,
    StudyPlanOut,
    StudyPlanProgressOut,
)
from app.services import study as study_service
from supabase import Client

router = APIRouter(prefix="/study", tags=["study"])


@router.post("/plans", response_model=StudyPlanOut)
async def create_plan(
    payload: StudyPlanCreate,
    user: UserContext = Depends(get_current_user),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    return await study_service.create_study_plan(
        client,
        user.user_id,
        payload.week_ids,
        payload.types,
        payload.max_items,
        payload.shuffle,
    )


@router.get("/plans/{plan_id}/next", response_model=StudyPlanItemOut)
async def next_item(
    plan_id: str,
    user: UserContext = Depends(get_current_user),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    item = await study_service.get_next_item(client, user.user_id, plan_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No remaining items",
        )
    question = await study_service.get_question(client, item["question_id"])
    return {
        "plan_id": plan_id,
        "question_id": item["question_id"],
        "position": item["position"],
        "question": QuestionOut(**question),
    }


@router.post("/plans/{plan_id}/answer", response_model=StudyPlanProgressOut)
async def submit_answer(
    plan_id: str,
    payload: StudyAnswerIn,
    user: UserContext = Depends(get_current_user),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    return await study_service.submit_answer(
        client,
        user.user_id,
        plan_id,
        payload.question_id,
        payload.is_correct,
        payload.is_known,
    )
