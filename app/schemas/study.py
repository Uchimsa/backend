import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.models.study_plan import StudyMode
from app.schemas.catalog import QuestionOut


class StudyPlanCreate(BaseModel):
    mode: StudyMode
    week_ids: list[uuid.UUID]
    max_items: Optional[int] = Field(default=None, ge=1)
    shuffle: bool = True
    time_limit_seconds: Optional[int] = Field(default=None, ge=60)


class StudyPlanOut(BaseModel):
    plan_id: uuid.UUID
    mode: StudyMode
    total_items: int
    remaining: int
    status: str

    model_config = {"from_attributes": True}


class StudyPlanItemOut(BaseModel):
    plan_id: uuid.UUID
    question_id: uuid.UUID
    position: int
    question: QuestionOut


class TestAnswerIn(BaseModel):
    question_id: uuid.UUID
    chosen_option_index: int = Field(ge=0)


class TestAnswerOut(BaseModel):
    is_correct: bool
    correct_option_index: int
    explanation: Optional[str] = None
    plan_status: str
    remaining: int


class FlashcardKnowledgeLevel(str, Enum):
    known = "known"
    repeat = "repeat"
    unknown = "unknown"


class FlashcardAnswerIn(BaseModel):
    question_id: uuid.UUID
    knowledge_level: FlashcardKnowledgeLevel


class FlashcardAnswerOut(BaseModel):
    plan_status: str
    remaining: int
    definition: Optional[str] = None
    explanation: Optional[str] = None


class TaskAnswerIn(BaseModel):
    question_id: uuid.UUID
    answer_text: str


class TaskAnswerOut(BaseModel):
    ai_score: float
    ai_explanation: str
    reference_answer: Optional[str] = None
    explanation: Optional[str] = None
    plan_status: str
    remaining: int


class SkipTaskIn(BaseModel):
    question_id: uuid.UUID


class StudyPlanProgressOut(BaseModel):
    plan_id: uuid.UUID
    total_items: int
    correct_count: int
    wrong_count: int
    skipped_count: int
    remaining: int
    status: str
