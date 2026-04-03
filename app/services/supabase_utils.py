import asyncio
from typing import Any

from fastapi import HTTPException, status


def _handle_error(response: Any, message: str) -> None:
    error = getattr(response, "error", None)
    if error:
        detail = getattr(error, "message", None) or str(error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{message}: {detail}",
        )


async def run_query(query: Any, message: str) -> list[dict[str, Any]]:
    response = await asyncio.to_thread(query.execute)
    _handle_error(response, message)
    return response.data or []


async def run_query_one(query: Any, message: str) -> dict[str, Any]:
    response = await asyncio.to_thread(query.execute)
    _handle_error(response, message)
    data = response.data or []
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )
    return data[0]
