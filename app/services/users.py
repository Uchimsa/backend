from app.services.supabase_utils import run_query
from supabase import Client


async def attach_subjects(
    client: Client, user_id: str, subject_ids: list[str]
) -> list[dict]:
    if not subject_ids:
        return []
    payload = [
        {"user_id": user_id, "subject_id": subject_id} for subject_id in subject_ids
    ]
    query = client.table("user_subjects").upsert(
        payload,
        on_conflict="user_id,subject_id",
    )
    return await run_query(query, "Failed to attach subjects")


async def detach_subject(client: Client, user_id: str, subject_id: str) -> list[dict]:
    query = (
        client.table("user_subjects")
        .delete()
        .eq("user_id", user_id)
        .eq("subject_id", subject_id)
    )
    return await run_query(query, "Failed to detach subject")
