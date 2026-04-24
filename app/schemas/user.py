import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserSubjectsUpdate(BaseModel):
    subject_ids: list[uuid.UUID]
