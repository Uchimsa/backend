import random
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import Question, QuestionType
from app.models.study_plan import PlanStatus, StudyMode, StudyPlan
from app.models.study_plan_item import StudyPlanItem
from app.repositories.question import question_repo
from app.repositories.study import study_plan_repo
from app.schemas.study import FlashcardKnowledgeLevel
from app.services.ai_evaluation import evaluate_task_answer


class StudyService:
    async def create_plan(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        mode: StudyMode,
        week_ids: list[uuid.UUID],
        max_items: int | None,
        shuffle: bool,
        time_limit_seconds: int | None,
    ) -> dict[str, Any]:
        question_type = QuestionType(mode.value)
        questions = await question_repo.list_by_weeks(db, week_ids, [question_type])

        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No questions available for the selected weeks and mode",
            )

        if shuffle:
            random.shuffle(questions)
        if max_items:
            questions = questions[:max_items]

        plan = await study_plan_repo.create(
            db,
            user_id=user_id,
            mode=mode,
            total_items=len(questions),
            time_limit_seconds=time_limit_seconds,
        )

        for position, question in enumerate(questions):
            db.add(StudyPlanItem(plan_id=plan.id, question_id=question.id, position=position))
        await db.flush()

        return {
            "plan_id": plan.id,
            "mode": plan.mode,
            "total_items": plan.total_items,
            "remaining": plan.total_items,
            "status": plan.status.value,
        }

    async def _get_plan_for_user(
        self, db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID
    ) -> StudyPlan:
        plan = await study_plan_repo.get(db, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        if plan.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        if plan.status == PlanStatus.completed:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plan already completed")
        return plan

    async def get_next_item(
        self, db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict[str, Any] | None:
        plan = await study_plan_repo.get(db, plan_id)
        if not plan or plan.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

        item = await study_plan_repo.get_next_item(db, plan_id)
        if not item:
            return None

        question = await question_repo.get(db, item.question_id)
        return {"item": item, "question": question}

    async def submit_test_answer(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
        question_id: uuid.UUID,
        chosen_option_index: int,
    ) -> dict[str, Any]:
        plan = await self._get_plan_for_user(db, plan_id, user_id)
        item = await study_plan_repo.get_item_by_question(db, plan_id, question_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        if item.answered_at is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already answered")

        question = await question_repo.get(db, question_id)
        if not question or question.correct_option_index is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question")

        is_correct = chosen_option_index == question.correct_option_index
        await study_plan_repo.mark_item_answered(db, item, is_correct=is_correct)

        if is_correct:
            plan.correct_count += 1
        else:
            plan.wrong_count += 1
        await db.flush()

        await study_plan_repo.upsert_progress(db, user_id, question_id, is_correct)
        remaining = await study_plan_repo.count_remaining(db, plan_id)
        if remaining == 0:
            await study_plan_repo.complete_plan(db, plan)
            await study_plan_repo.create_session(db, user_id, plan)

        return {
            "is_correct": is_correct,
            "correct_option_index": question.correct_option_index,
            "explanation": question.explanation,
            "plan_status": plan.status.value,
            "remaining": remaining,
        }

    async def submit_flashcard_answer(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
        question_id: uuid.UUID,
        knowledge_level: FlashcardKnowledgeLevel,
    ) -> dict[str, Any]:
        plan = await self._get_plan_for_user(db, plan_id, user_id)
        item = await study_plan_repo.get_item_by_question(db, plan_id, question_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        if item.answered_at is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already answered")

        is_known = knowledge_level == FlashcardKnowledgeLevel.known
        is_correct = is_known
        await study_plan_repo.mark_item_answered(db, item, is_correct=is_correct, is_known=is_known)

        if is_correct:
            plan.correct_count += 1
        else:
            plan.wrong_count += 1
        await db.flush()

        await study_plan_repo.upsert_progress(db, user_id, question_id, is_correct, is_known)
        question = await question_repo.get(db, question_id)
        remaining = await study_plan_repo.count_remaining(db, plan_id)
        if remaining == 0:
            await study_plan_repo.complete_plan(db, plan)
            await study_plan_repo.create_session(db, user_id, plan)

        return {
            "plan_status": plan.status.value,
            "remaining": remaining,
            "definition": question.answer_text if question else None,
            "explanation": question.explanation if question else None,
        }

    async def submit_task_answer(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
        question_id: uuid.UUID,
        answer_text: str,
    ) -> dict[str, Any]:
        plan = await self._get_plan_for_user(db, plan_id, user_id)
        item = await study_plan_repo.get_item_by_question(db, plan_id, question_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        if item.answered_at is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already answered")

        question = await question_repo.get(db, question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        eval_result = await evaluate_task_answer(
            question.question_text, question.answer_text, answer_text
        )
        is_correct = eval_result.score >= 0.5

        await study_plan_repo.mark_item_answered(
            db,
            item,
            is_correct=is_correct,
            user_answer_text=answer_text,
            ai_score=eval_result.score,
            ai_explanation=eval_result.explanation,
        )

        if is_correct:
            plan.correct_count += 1
        else:
            plan.wrong_count += 1
        await db.flush()

        await study_plan_repo.upsert_progress(db, user_id, question_id, is_correct)
        remaining = await study_plan_repo.count_remaining(db, plan_id)
        if remaining == 0:
            await study_plan_repo.complete_plan(db, plan)
            await study_plan_repo.create_session(db, user_id, plan)

        return {
            "ai_score": eval_result.score,
            "ai_explanation": eval_result.explanation,
            "reference_answer": question.answer_text,
            "explanation": question.explanation,
            "plan_status": plan.status.value,
            "remaining": remaining,
        }

    async def skip_task(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> dict[str, Any]:
        plan = await self._get_plan_for_user(db, plan_id, user_id)
        item = await study_plan_repo.get_item_by_question(db, plan_id, question_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        if item.answered_at is not None or item.is_skipped:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already answered or skipped")

        await study_plan_repo.mark_item_answered(db, item, is_skipped=True)
        plan.skipped_count += 1
        await db.flush()

        remaining = await study_plan_repo.count_remaining(db, plan_id)
        if remaining == 0:
            await study_plan_repo.complete_plan(db, plan)
            await study_plan_repo.create_session(db, user_id, plan)

        return {
            "plan_id": plan_id,
            "total_items": plan.total_items,
            "correct_count": plan.correct_count,
            "wrong_count": plan.wrong_count,
            "skipped_count": plan.skipped_count,
            "remaining": remaining,
            "status": plan.status.value,
        }

    async def get_progress(
        self, db: AsyncSession, user_id: uuid.UUID, plan_id: uuid.UUID
    ) -> dict[str, Any]:
        plan = await study_plan_repo.get(db, plan_id)
        if not plan or plan.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        remaining = await study_plan_repo.count_remaining(db, plan_id)
        return {
            "plan_id": plan.id,
            "total_items": plan.total_items,
            "correct_count": plan.correct_count,
            "wrong_count": plan.wrong_count,
            "skipped_count": plan.skipped_count,
            "remaining": remaining,
            "status": plan.status.value,
        }


study_service = StudyService()
