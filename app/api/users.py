from fastapi import APIRouter, Depends

from app.core.auth import UserContext, get_current_user
from app.core.deps import get_supabase_dep
from app.models.user import UserSubjectsUpdate
from app.services import users as user_service
from supabase import Client

router = APIRouter(tags=["users"])


@router.post("/users/me/subjects")
async def add_subjects(
    payload: UserSubjectsUpdate,
    user: UserContext = Depends(get_current_user),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    data = await user_service.attach_subjects(client, user.user_id, payload.subject_ids)
    return {"items": data}


@router.delete("/users/me/subjects/{subject_id}")
async def remove_subject(
    subject_id: str,
    user: UserContext = Depends(get_current_user),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    await user_service.detach_subject(client, user.user_id, subject_id)
    return {"status": "ok"}
