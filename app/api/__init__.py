from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.catalog import router as catalog_router
from app.api.stats import router as stats_router
from app.api.study import router as study_router
from app.api.task_scans import router as task_scans_router
from app.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(catalog_router)
api_router.include_router(users_router)
api_router.include_router(study_router)
api_router.include_router(stats_router)
api_router.include_router(task_scans_router)
api_router.include_router(admin_router)

__all__ = ["api_router"]
