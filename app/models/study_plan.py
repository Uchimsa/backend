import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.study_plan_item import StudyPlanItem
    from app.models.study_session import StudySession


class StudyMode(str, Enum):
    test = "test"
    task = "task"
    flashcard = "flashcard"


class PlanStatus(str, Enum):
    active = "active"
    completed = "completed"


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[StudyMode] = mapped_column(
        SAEnum(StudyMode, name="study_mode"), nullable=False
    )
    total_items: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[PlanStatus] = mapped_column(
        SAEnum(PlanStatus, name="plan_status"), default=PlanStatus.active, nullable=False
    )
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["StudyPlanItem"]] = relationship(
        "StudyPlanItem", back_populates="plan", cascade="all, delete-orphan"
    )
    session: Mapped["StudySession | None"] = relationship(
        "StudySession", back_populates="plan", uselist=False
    )
