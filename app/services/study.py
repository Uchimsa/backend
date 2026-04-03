import random
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status

from app.models.catalog import QuestionType
from app.services.supabase_utils import run_query, run_query_one
from supabase import Client


async def create_study_plan(
    client: Client,
    user_id: str,
    week_ids: list[str],
    types: list[QuestionType],
    max_items: Optional[int],
    shuffle: bool,
) -> dict[str, Any]:
    if not week_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="week_ids cannot be empty",
        )

    query = (
        client.table("questions")
        .select(
            "id,week_id,type,question_text,answer_text,options,correct_option_index,explanation"
        )
        .in_("week_id", week_ids)
    )
    if types:
        query = query.in_("type", [item.value for item in types])

    questions = await run_query(query, "Failed to load questions for plan")
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions available for the selected weeks",
        )

    if shuffle:
        random.shuffle(questions)
    else:
        questions.sort(key=lambda item: item.get("id"))

    if max_items:
        questions = questions[:max_items]

    plan_payload = {
        "user_id": user_id,
        "total_items": len(questions),
        "correct_count": 0,
        "wrong_count": 0,
        "status": "active",
    }
    plan = await run_query_one(
        client.table("study_plans").insert(plan_payload).select("*"),
        "Failed to create study plan",
    )

    items_payload = [
        {
            "plan_id": plan["id"],
            "question_id": question["id"],
            "position": index,
        }
        for index, question in enumerate(questions)
    ]
    await run_query(
        client.table("study_plan_items").insert(items_payload),
        "Failed to create study plan items",
    )

    return {
        "plan_id": plan["id"],
        "total_items": plan["total_items"],
        "remaining": plan["total_items"],
        "status": plan["status"],
    }


async def get_next_item(
    client: Client,
    user_id: str,
    plan_id: str,
) -> Optional[dict[str, Any]]:
    plan = await run_query_one(
        client.table("study_plans").select("id,user_id").eq("id", plan_id),
        "Study plan not found",
    )
    if plan.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    items = await run_query(
        client.table("study_plan_items")
        .select("id,question_id,position,answered_at")
        .eq("plan_id", plan_id)
        .is_("answered_at", "null")
        .order("position")
        .limit(1),
        "Failed to load next item",
    )
    if not items:
        return None
    return items[0]


async def get_question(client: Client, question_id: str) -> dict[str, Any]:
    return await run_query_one(
        client.table("questions").select("*").eq("id", question_id),
        "Question not found",
    )


async def submit_answer(
    client: Client,
    user_id: str,
    plan_id: str,
    question_id: str,
    is_correct: bool,
    is_known: Optional[bool],
) -> dict[str, Any]:
    item_query = (
        client.table("study_plan_items")
        .select("id,question_id,answered_at")
        .eq("plan_id", plan_id)
        .eq("question_id", question_id)
        .limit(1)
    )
    item = await run_query_one(item_query, "Study item not found")
    if item.get("answered_at") is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question already answered",
        )

    now = datetime.now(timezone.utc).isoformat()
    await run_query(
        client.table("study_plan_items")
        .update({"is_correct": is_correct, "answered_at": now})
        .eq("id", item["id"]),
        "Failed to update study item",
    )

    plan = await run_query_one(
        client.table("study_plans").select("*").eq("id", plan_id),
        "Study plan not found",
    )
    if plan.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    correct_count = plan.get("correct_count", 0) + (1 if is_correct else 0)
    wrong_count = plan.get("wrong_count", 0) + (0 if is_correct else 1)

    await run_query(
        client.table("study_plans")
        .update({"correct_count": correct_count, "wrong_count": wrong_count})
        .eq("id", plan_id),
        "Failed to update study plan",
    )

    await _update_progress(client, user_id, question_id, is_correct, is_known)

    remaining = await _count_remaining_items(client, plan_id)
    status_value = "completed" if remaining == 0 else plan.get("status", "active")

    if remaining == 0 and plan.get("status") != "completed":
        await run_query(
            client.table("study_plans")
            .update({"status": "completed"})
            .eq("id", plan_id),
            "Failed to mark study plan complete",
        )
        await run_query(
            client.table("study_sessions").insert(
                {
                    "user_id": user_id,
                    "total_cards": plan.get("total_items", 0),
                    "correct_count": correct_count,
                    "wrong_count": wrong_count,
                }
            ),
            "Failed to create study session",
        )

    return {
        "plan_id": plan_id,
        "total_items": plan.get("total_items", 0),
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "remaining": remaining,
        "status": status_value,
    }


async def _update_progress(
    client: Client,
    user_id: str,
    question_id: str,
    is_correct: bool,
    is_known: Optional[bool],
) -> None:
    existing = await run_query(
        client.table("user_progress")
        .select("id,views")
        .eq("user_id", user_id)
        .eq("question_id", question_id)
        .limit(1),
        "Failed to load user progress",
    )

    status_value = "mastered" if is_correct and is_known else "learning"
    if not is_correct:
        status_value = "learning"

    if existing:
        progress = existing[0]
        await run_query(
            client.table("user_progress")
            .update(
                {
                    "status": status_value,
                    "is_known": is_known,
                    "views": (progress.get("views", 0) or 0) + 1,
                }
            )
            .eq("id", progress["id"]),
            "Failed to update progress",
        )
        return

    await run_query(
        client.table("user_progress").insert(
            {
                "user_id": user_id,
                "question_id": question_id,
                "status": status_value,
                "is_known": is_known,
                "interval": 0,
                "ease_factor": 2.5,
                "views": 1,
            }
        ),
        "Failed to create progress",
    )


async def _count_remaining_items(client: Client, plan_id: str) -> int:
    items = await run_query(
        client.table("study_plan_items")
        .select("id,answered_at")
        .eq("plan_id", plan_id),
        "Failed to load study plan items",
    )
    return len([item for item in items if item.get("answered_at") is None])
