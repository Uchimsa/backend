from app.services.supabase_utils import run_query, run_query_one
from supabase import Client


async def create_subject(client: Client, payload: dict) -> dict:
    return await run_query_one(
        client.table("subjects").insert(payload).select("*"),
        "Failed to create subject",
    )


async def update_subject(client: Client, subject_id: str, payload: dict) -> dict:
    return await run_query_one(
        client.table("subjects").update(payload).eq("id", subject_id).select("*"),
        "Failed to update subject",
    )


async def delete_subject(client: Client, subject_id: str) -> None:
    await run_query(
        client.table("subjects").delete().eq("id", subject_id),
        "Failed to delete subject",
    )


async def create_week(client: Client, payload: dict) -> dict:
    return await run_query_one(
        client.table("weeks").insert(payload).select("*"),
        "Failed to create week",
    )


async def update_week(client: Client, week_id: str, payload: dict) -> dict:
    return await run_query_one(
        client.table("weeks").update(payload).eq("id", week_id).select("*"),
        "Failed to update week",
    )


async def delete_week(client: Client, week_id: str) -> None:
    await run_query(
        client.table("weeks").delete().eq("id", week_id),
        "Failed to delete week",
    )


async def create_question(client: Client, payload: dict) -> dict:
    return await run_query_one(
        client.table("questions").insert(payload).select("*"),
        "Failed to create question",
    )


async def update_question(client: Client, question_id: str, payload: dict) -> dict:
    return await run_query_one(
        client.table("questions").update(payload).eq("id", question_id).select("*"),
        "Failed to update question",
    )


async def delete_question(client: Client, question_id: str) -> None:
    await run_query(
        client.table("questions").delete().eq("id", question_id),
        "Failed to delete question",
    )
