import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.study_plan import StudyMode


class SubjectStatsOut(BaseModel):
    subject_id: uuid.UUID
    subject_name: Optional[str] = None
    correct_count: int
    wrong_count: int
    skipped_count: int
    accuracy: float


class WeekStatsOut(BaseModel):
    week_id: uuid.UUID
    week_number: int
    title: str
    correct_count: int
    wrong_count: int
    accuracy: float


class SessionOut(BaseModel):
    id: uuid.UUID
    mode: StudyMode
    total_cards: int
    correct_count: int
    wrong_count: int
    skipped_count: int
    accuracy: float
    completed_at: datetime

    model_config = {"from_attributes": True}


class WeakTopicOut(BaseModel):
    question_id: uuid.UUID
    question_text: str
    week_title: str
    subject_name: str
    views: int
    ease_factor: float
