from fastapi import APIRouter, Depends

from app.core.deps import get_supabase_dep
from app.models.catalog import QuestionOut, QuestionType, SubjectOut, WeekOut
from app.services import catalog as catalog_service
from supabase import Client

router = APIRouter(tags=["catalog"])


@router.get("/subjects", response_model=list[SubjectOut])
async def get_subjects(client: Client = Depends(get_supabase_dep)) -> list[dict]:
    return await catalog_service.list_subjects(client)


@router.get("/subjects/{subject_id}/weeks", response_model=list[WeekOut])
async def get_weeks(
    subject_id: str,
    client: Client = Depends(get_supabase_dep),
) -> list[dict]:
    return await catalog_service.list_weeks(client, subject_id)


@router.get("/weeks/{week_id}/questions", response_model=list[QuestionOut])
async def get_questions(
    week_id: str,
    types: list[QuestionType] | None = None,
    client: Client = Depends(get_supabase_dep),
) -> list[dict]:
    return await catalog_service.list_questions(client, week_id, types)
