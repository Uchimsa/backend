from typing import Optional

from pydantic import BaseModel


class SubjectStatsOut(BaseModel):
    subject_id: str
    subject_name: Optional[str] = None
    correct_count: int
    wrong_count: int
    accuracy: float
