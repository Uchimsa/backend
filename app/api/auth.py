from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.auth import LoginIn, RegisterIn, TokenOut
from app.schemas.user import UserOut
from app.services.user import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)):
    user = await user_service.register(db, payload.email, payload.password)
    return user


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    user = await user_service.authenticate(db, payload.email, payload.password)
    token = user_service.make_token(user)
    return TokenOut(access_token=token)
