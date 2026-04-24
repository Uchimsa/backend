import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.question import QuestionType


class SubjectOut(BaseModel):
    id: uuid.UUID
    name: str
    icon_name: Optional[str] = None
    is_hidden: bool

    model_config = {"from_attributes": True}


class SubjectCreate(BaseModel):
    name: str
    icon_name: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    icon_name: Optional[str] = None
    is_hidden: Optional[bool] = None


class WeekOut(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    week_number: int
    title: str

    model_config = {"from_attributes": True}


class WeekCreate(BaseModel):
    subject_id: uuid.UUID
    week_number: int
    title: str


class WeekUpdate(BaseModel):
    week_number: Optional[int] = None
    title: Optional[str] = None


class QuestionOut(BaseModel):
    id: uuid.UUID
    week_id: uuid.UUID
    type: QuestionType
    question_text: str
    answer_text: Optional[str] = None
    options: Optional[list[str]] = None
    correct_option_index: Optional[int] = None
    explanation: Optional[str] = None

    model_config = {"from_attributes": True}


class QuestionCreate(BaseModel):
    week_id: uuid.UUID
    type: QuestionType
    question_text: str
    answer_text: Optional[str] = None
    options: Optional[list[str]] = None
    correct_option_index: Optional[int] = Field(default=None, ge=0)
    explanation: Optional[str] = None


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    answer_text: Optional[str] = None
    options: Optional[list[str]] = None
    correct_option_index: Optional[int] = Field(default=None, ge=0)
    explanation: Optional[str] = None
    type: Optional[QuestionType] = None
    week_id: Optional[uuid.UUID] = None
