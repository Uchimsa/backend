from fastapi import APIRouter

from app.api import api_router

router = APIRouter(prefix="/api/v1")
router.include_router(api_router)
