from fastapi import APIRouter, Depends

from app.core.auth import UserContext, get_current_user
from app.core.deps import get_supabase_dep
from app.models.task_scans import TaskScanCreate, TaskScanOut
from app.services import task_scans as task_scans_service
from supabase import Client

router = APIRouter(prefix="/task-scans", tags=["task-scans"])


@router.post("", response_model=TaskScanOut)
async def create_task_scan(
    payload: TaskScanCreate,
    user: UserContext = Depends(get_current_user),
    client: Client = Depends(get_supabase_dep),
) -> dict:
    data = payload.model_dump()
    data["user_id"] = user.user_id
    return await task_scans_service.create_task_scan(client, data)


@router.get("", response_model=list[TaskScanOut])
async def list_task_scans(
    user: UserContext = Depends(get_current_user),
    client: Client = Depends(get_supabase_dep),
) -> list[dict]:
    return await task_scans_service.list_task_scans(client, user.user_id)
