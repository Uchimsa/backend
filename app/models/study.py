from typing import Optional

from pydantic import BaseModel, Field

from app.models.catalog import QuestionOut, QuestionType


class StudyPlanCreate(BaseModel):
    week_ids: list[str]
    types: list[QuestionType]
    max_items: Optional[int] = Field(default=None, ge=1)
    shuffle: bool = False


class StudyPlanOut(BaseModel):
    plan_id: str
    total_items: int
    remaining: int
    status: str


class StudyPlanItemOut(BaseModel):
    plan_id: str
    question_id: str
    position: int
    question: QuestionOut


class StudyAnswerIn(BaseModel):
    question_id: str
    is_correct: bool
    is_known: Optional[bool] = None


class StudyPlanProgressOut(BaseModel):
    plan_id: str
    total_items: int
    correct_count: int
    wrong_count: int
    remaining: int
    status: str
