import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.study_plan import PlanStatus, StudyPlan
from app.models.study_plan_item import StudyPlanItem
from app.models.study_session import StudySession
from app.models.user_progress import ProgressStatus, UserProgress
from app.repositories.base import BaseRepository


class StudyPlanRepository(BaseRepository[StudyPlan]):
    model = StudyPlan

    async def get_with_items(self, db: AsyncSession, plan_id: uuid.UUID) -> StudyPlan | None:
        result = await db.execute(
            select(StudyPlan)
            .where(StudyPlan.id == plan_id)
            .options(selectinload(StudyPlan.items))
        )
        return result.scalar_one_or_none()

    async def count_remaining(self, db: AsyncSession, plan_id: uuid.UUID) -> int:
        result = await db.execute(
            select(StudyPlanItem).where(
                StudyPlanItem.plan_id == plan_id,
                StudyPlanItem.answered_at.is_(None),
                StudyPlanItem.is_skipped.is_(False),
            )
        )
        return len(result.scalars().all())

    async def get_next_item(self, db: AsyncSession, plan_id: uuid.UUID) -> StudyPlanItem | None:
        result = await db.execute(
            select(StudyPlanItem)
            .where(
                StudyPlanItem.plan_id == plan_id,
                StudyPlanItem.answered_at.is_(None),
                StudyPlanItem.is_skipped.is_(False),
            )
            .order_by(StudyPlanItem.position)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_item_by_question(
        self, db: AsyncSession, plan_id: uuid.UUID, question_id: uuid.UUID
    ) -> StudyPlanItem | None:
        result = await db.execute(
            select(StudyPlanItem).where(
                StudyPlanItem.plan_id == plan_id,
                StudyPlanItem.question_id == question_id,
            )
        )
        return result.scalar_one_or_none()

    async def mark_item_answered(
        self,
        db: AsyncSession,
        item: StudyPlanItem,
        is_correct: bool | None = None,
        is_known: bool | None = None,
        user_answer_text: str | None = None,
        ai_score: float | None = None,
        ai_explanation: str | None = None,
        is_skipped: bool = False,
    ) -> StudyPlanItem:
        item.answered_at = datetime.now(timezone.utc)
        item.is_correct = is_correct
        item.is_known = is_known
        item.user_answer_text = user_answer_text
        item.ai_score = ai_score
        item.ai_explanation = ai_explanation
        item.is_skipped = is_skipped
        await db.flush()
        return item

    async def complete_plan(self, db: AsyncSession, plan: StudyPlan) -> StudyPlan:
        plan.status = PlanStatus.completed
        plan.completed_at = datetime.now(timezone.utc)
        await db.flush()
        return plan

    async def upsert_progress(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        question_id: uuid.UUID,
        is_correct: bool,
        is_known: bool | None = None,
    ) -> None:
        result = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.question_id == question_id,
            )
        )
        progress = result.scalar_one_or_none()
        new_status = ProgressStatus.mastered if (is_correct and is_known) else ProgressStatus.learning

        if progress:
            progress.status = new_status
            progress.is_known = is_known
            progress.views += 1
            if is_correct:
                progress.correct_streak += 1
            else:
                progress.correct_streak = 0
        else:
            db.add(
                UserProgress(
                    user_id=user_id,
                    question_id=question_id,
                    status=new_status,
                    views=1,
                    correct_streak=1 if is_correct else 0,
                )
            )
        await db.flush()

    async def create_session(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        plan: StudyPlan,
    ) -> StudySession:
        answered = plan.correct_count + plan.wrong_count
        accuracy = plan.correct_count / answered if answered else 0.0
        session = StudySession(
            user_id=user_id,
            plan_id=plan.id,
            mode=plan.mode,
            total_cards=plan.total_items,
            correct_count=plan.correct_count,
            wrong_count=plan.wrong_count,
            skipped_count=plan.skipped_count,
            accuracy=accuracy,
        )
        db.add(session)
        await db.flush()
        return session


study_plan_repo = StudyPlanRepository()
