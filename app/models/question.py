import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.week import Week


class QuestionType(str, Enum):
    test = "test"
    task = "task"
    flashcard = "flashcard"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    week_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("weeks.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[QuestionType] = mapped_column(
        SAEnum(QuestionType, name="question_type"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(String, nullable=False)
    answer_text: Mapped[str | None] = mapped_column(String, nullable=True)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    correct_option_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explanation: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    week: Mapped["Week"] = relationship("Week", back_populates="questions")
