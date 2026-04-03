from fastapi import APIRouter, Depends

from app.core.auth import UserContext, get_current_user
from app.core.deps import get_supabase_dep
from app.models.stats import SubjectStatsOut
from app.services import stats as stats_service
from supabase import Client

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/subjects", response_model=list[SubjectStatsOut])
async def subject_stats(
    user: UserContext = Depends(get_current_user),
    client: Client = Depends(get_supabase_dep),
) -> list[dict]:
    return await stats_service.get_subject_stats(client, user.user_id)
