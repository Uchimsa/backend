import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.week import Week
    from app.models.user_subject import UserSubject


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    weeks: Mapped[list["Week"]] = relationship(
        "Week", back_populates="subject", cascade="all, delete-orphan"
    )
    user_subjects: Mapped[list["UserSubject"]] = relationship(
        "UserSubject", back_populates="subject", cascade="all, delete-orphan"
    )
