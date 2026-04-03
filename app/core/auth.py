from typing import Any, Optional, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.settings import Settings, get_settings


class UserContext(BaseModel):
    user_id: str
    role: Optional[str] = None
    email: Optional[str] = None


security = HTTPBearer()


def _decode_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[settings.supabase_jwt_alg],
            options={"verify_aud": False},
        )
        return cast(dict[str, Any], payload)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> UserContext:
    payload = _decode_token(credentials.credentials, settings)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return UserContext(
        user_id=user_id,
        role=payload.get("role"),
        email=payload.get("email"),
    )


def require_admin(user: UserContext = Depends(get_current_user)) -> UserContext:
    if user.role not in {"admin", "service_role"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
