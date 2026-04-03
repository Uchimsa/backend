from app.services.supabase_utils import run_query
from supabase import Client


async def get_subject_stats(client: Client, user_id: str) -> list[dict]:
    plans = await run_query(
        client.table("study_plans").select("id").eq("user_id", user_id),
        "Failed to load study plans",
    )
    plan_ids = [plan["id"] for plan in plans]
    if not plan_ids:
        return []

    items = await run_query(
        client.table("study_plan_items")
        .select("question_id,is_correct")
        .in_("plan_id", plan_ids),
        "Failed to load study plan items",
    )
    scored_items = [item for item in items if item.get("is_correct") is not None]
    if not scored_items:
        return []

    question_ids = list({item["question_id"] for item in scored_items})
    questions = await run_query(
        client.table("questions").select("id,week_id").in_("id", question_ids),
        "Failed to load questions for stats",
    )
    week_ids = list({question["week_id"] for question in questions})
    weeks = await run_query(
        client.table("weeks").select("id,subject_id").in_("id", week_ids),
        "Failed to load weeks for stats",
    )
    subject_ids = list({week["subject_id"] for week in weeks})
    subjects = await run_query(
        client.table("subjects").select("id,name").in_("id", subject_ids),
        "Failed to load subjects for stats",
    )

    question_to_week = {question["id"]: question["week_id"] for question in questions}
    week_to_subject = {week["id"]: week["subject_id"] for week in weeks}
    subject_names = {subject["id"]: subject.get("name") for subject in subjects}

    summary: dict[str, dict[str, int]] = {}
    for item in scored_items:
        week_id = question_to_week.get(item["question_id"])
        subject_id = week_to_subject.get(week_id)
        if not subject_id:
            continue
        summary.setdefault(subject_id, {"correct": 0, "wrong": 0})
        if item.get("is_correct"):
            summary[subject_id]["correct"] += 1
        else:
            summary[subject_id]["wrong"] += 1

    result = []
    for subject_id, counts in summary.items():
        total = counts["correct"] + counts["wrong"]
        accuracy = counts["correct"] / total if total else 0.0
        result.append(
            {
                "subject_id": subject_id,
                "subject_name": subject_names.get(subject_id),
                "correct_count": counts["correct"],
                "wrong_count": counts["wrong"],
                "accuracy": accuracy,
            }
        )

    return result
