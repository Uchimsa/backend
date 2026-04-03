from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    flashcard = "flashcard"
    test = "test"
    task = "task"


class SubjectOut(BaseModel):
    id: str
    name: str
    icon_name: Optional[str] = None


class SubjectCreate(BaseModel):
    name: str
    icon_name: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    icon_name: Optional[str] = None


class WeekOut(BaseModel):
    id: str
    subject_id: str
    week_number: int
    title: str


class WeekCreate(BaseModel):
    subject_id: str
    week_number: int
    title: str


class WeekUpdate(BaseModel):
    week_number: Optional[int] = None
    title: Optional[str] = None


class QuestionOut(BaseModel):
    id: str
    week_id: str
    type: QuestionType
    question_text: str
    answer_text: Optional[str] = None
    options: Optional[list[str]] = None
    correct_option_index: Optional[int] = None
    explanation: Optional[str] = None


class QuestionCreate(BaseModel):
    week_id: str
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
    week_id: Optional[str] = None
