import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.question import Question
    from app.models.study_plan import StudyPlan


class StudyPlanItem(Base):
    __tablename__ = "study_plan_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_known: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_answer_text: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(String, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    plan: Mapped["StudyPlan"] = relationship("StudyPlan", back_populates="items")
    question: Mapped["Question"] = relationship("Question")
