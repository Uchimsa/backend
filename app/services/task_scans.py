from app.services.supabase_utils import run_query, run_query_one
from supabase import Client


async def create_task_scan(client: Client, payload: dict) -> dict:
    return await run_query_one(
        client.table("task_scans").insert(payload).select("*"),
        "Failed to create task scan",
    )


async def list_task_scans(client: Client, user_id: str) -> list[dict]:
    return await run_query(
        client.table("task_scans")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True),
        "Failed to load task scans",
    )
