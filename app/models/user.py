from pydantic import BaseModel, Field


class UserSubjectsUpdate(BaseModel):
    subject_ids: list[str] = Field(default_factory=list)
