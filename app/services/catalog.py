from typing import Optional

from app.models.catalog import QuestionType
from app.services.supabase_utils import run_query
from supabase import Client


async def list_subjects(client: Client) -> list[dict]:
    query = client.table("subjects").select("*").order("name")
    return await run_query(query, "Failed to load subjects")


async def list_weeks(client: Client, subject_id: str) -> list[dict]:
    query = (
        client.table("weeks")
        .select("*")
        .eq("subject_id", subject_id)
        .order("week_number")
    )
    return await run_query(query, "Failed to load weeks")


async def list_questions(
    client: Client,
    week_id: str,
    types: Optional[list[QuestionType]] = None,
) -> list[dict]:
    query = client.table("questions").select("*").eq("week_id", week_id)
    if types:
        query = query.in_("type", [item.value for item in types])
    return await run_query(query, "Failed to load questions")
