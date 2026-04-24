import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import Question
from app.models.study_plan import StudyPlan
from app.models.study_plan_item import StudyPlanItem
from app.models.study_session import StudySession
from app.models.subject import Subject
from app.models.user_progress import UserProgress
from app.models.week import Week
from app.repositories.base import BaseRepository


class StatsRepository:
    async def get_sessions(self, db: AsyncSession, user_id: uuid.UUID) -> list[StudySession]:
        result = await db.execute(
            select(StudySession)
            .where(StudySession.user_id == user_id)
            .order_by(StudySession.completed_at.desc())
            .limit(50)
        )
        return list(result.scalars().all())

    async def get_answered_items_by_user(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> list[StudyPlanItem]:
        plan_ids_result = await db.execute(
            select(StudyPlan.id).where(StudyPlan.user_id == user_id)
        )
        plan_ids = list(plan_ids_result.scalars().all())
        if not plan_ids:
            return []
        result = await db.execute(
            select(StudyPlanItem)
            .where(
                StudyPlanItem.plan_id.in_(plan_ids),
                StudyPlanItem.answered_at.isnot(None),
                StudyPlanItem.is_skipped.is_(False),
            )
        )
        return list(result.scalars().all())

    async def get_weak_topics(
        self, db: AsyncSession, user_id: uuid.UUID, limit: int = 10
    ) -> list[dict]:
        result = await db.execute(
            select(UserProgress, Question, Week, Subject)
            .join(Question, UserProgress.question_id == Question.id)
            .join(Week, Question.week_id == Week.id)
            .join(Subject, Week.subject_id == Subject.id)
            .where(
                UserProgress.user_id == user_id,
                UserProgress.correct_streak < 2,
            )
            .order_by(UserProgress.ease_factor.asc(), UserProgress.views.desc())
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "question_id": progress.question_id,
                "question_text": question.question_text,
                "week_title": week.title,
                "subject_name": subject.name,
                "views": progress.views,
                "ease_factor": progress.ease_factor,
            }
            for progress, question, week, subject in rows
        ]

    async def get_subject_stats(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> list[dict]:
        items = await self.get_answered_items_by_user(db, user_id)
        if not items:
            return []

        question_ids = list({item.question_id for item in items})
        questions_result = await db.execute(
            select(Question).where(Question.id.in_(question_ids))
        )
        questions = {q.id: q for q in questions_result.scalars().all()}

        week_ids = list({q.week_id for q in questions.values()})
        weeks_result = await db.execute(select(Week).where(Week.id.in_(week_ids)))
        weeks = {w.id: w for w in weeks_result.scalars().all()}

        subject_ids = list({w.subject_id for w in weeks.values()})
        subjects_result = await db.execute(select(Subject).where(Subject.id.in_(subject_ids)))
        subjects = {s.id: s for s in subjects_result.scalars().all()}

        summary: dict[uuid.UUID, dict] = {}
        for item in items:
            question = questions.get(item.question_id)
            if not question:
                continue
            week = weeks.get(question.week_id)
            if not week:
                continue
            subject_id = week.subject_id
            if subject_id not in summary:
                summary[subject_id] = {
                    "subject_id": subject_id,
                    "subject_name": subjects[subject_id].name if subject_id in subjects else None,
                    "correct_count": 0,
                    "wrong_count": 0,
                    "skipped_count": 0,
                }
            if item.is_correct is True:
                summary[subject_id]["correct_count"] += 1
            else:
                summary[subject_id]["wrong_count"] += 1

        result_list = []
        for data in summary.values():
            total = data["correct_count"] + data["wrong_count"]
            data["accuracy"] = data["correct_count"] / total if total else 0.0
            result_list.append(data)
        return result_list


stats_repo = StatsRepository()
