from typing import Optional

from pydantic import BaseModel


class TaskScanCreate(BaseModel):
    question_id: Optional[str] = None
    image_url: str


class TaskScanOut(BaseModel):
    id: str
    user_id: str
    question_id: Optional[str] = None
    image_url: str
    ocr_text: Optional[str] = None
    ai_feedback: Optional[str] = None
    is_correct: Optional[bool] = None
    created_at: Optional[str] = None
