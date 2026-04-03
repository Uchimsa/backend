from fastapi import APIRouter, Depends

from app.core.auth import UserContext, require_admin
from app.core.deps import get_supabase_dep
from app.models.catalog import (
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
from app.services import admin as admin_service
from supabase import Client

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/subjects", response_model=SubjectOut)
async def create_subject(
    payload: SubjectCreate,
    _: UserContext = Depends(require_admin),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    return await admin_service.create_subject(client, payload.model_dump())


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
async def update_subject(
    subject_id: str,
    payload: SubjectUpdate,
    _: UserContext = Depends(require_admin),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    return await admin_service.update_subject(
        client, subject_id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: str,
    _: UserContext = Depends(require_admin),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    await admin_service.delete_subject(client, subject_id)
    return {"status": "ok"}


@router.post("/weeks", response_model=WeekOut)
async def create_week(
    payload: WeekCreate,
    _: UserContext = Depends(require_admin),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    return await admin_service.create_week(client, payload.model_dump())


@router.patch("/weeks/{week_id}", response_model=WeekOut)
async def update_week(
    week_id: str,
    payload: WeekUpdate,
    _: UserContext = Depends(require_admin),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    return await admin_service.update_week(
        client, week_id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/weeks/{week_id}")
async def delete_week(
    week_id: str,
    _: UserContext = Depends(require_admin),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    await admin_service.delete_week(client, week_id)
    return {"status": "ok"}


@router.post("/questions", response_model=QuestionOut)
async def create_question(
    payload: QuestionCreate,
    _: UserContext = Depends(require_admin),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    return await admin_service.create_question(client, payload.model_dump())


@router.patch("/questions/{question_id}", response_model=QuestionOut)
async def update_question(
    question_id: str,
    payload: QuestionUpdate,
    _: UserContext = Depends(require_admin),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    return await admin_service.update_question(
        client, question_id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    _: UserContext = Depends(require_admin),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    await admin_service.delete_question(client, question_id)
    return {"status": "ok"}
