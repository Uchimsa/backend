import pytest
import pytest_asyncio

from app.repositories.user import user_repo


@pytest_asyncio.fixture(scope="session")
async def flashcard_scenario(client, session_factory):
    admin_email = "admin_flash@example.com"
    await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "pw"})
    async with session_factory() as db:
        user = await user_repo.get_by_email(db, admin_email)
        user.is_admin = True
        await db.commit()
    login_r = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "pw"})
    admin_h = {"Authorization": f"Bearer {login_r.json()['access_token']}"}

    subject_r = await client.post(
        "/api/v1/admin/subjects", json={"name": "Flash Subject"}, headers=admin_h
    )
    week_r = await client.post(
        "/api/v1/admin/weeks",
        json={"subject_id": subject_r.json()["id"], "week_number": 1, "title": "Flash Week"},
        headers=admin_h,
    )
    week_id = week_r.json()["id"]

    for i in range(2):
        await client.post(
            "/api/v1/admin/questions",
            json={
                "week_id": week_id,
                "type": "flashcard",
                "question_text": f"Термин {i}",
                "answer_text": f"Определение {i}",
                "explanation": f"Пояснение {i}",
            },
            headers=admin_h,
        )

    user_email = "student_flash@example.com"
    await client.post("/api/v1/auth/register", json={"email": user_email, "password": "pw"})
    login = await client.post("/api/v1/auth/login", json={"email": user_email, "password": "pw"})
    user_h = {"Authorization": f"Bearer {login.json()['access_token']}"}

    return {"week_id": week_id, "headers": user_h}


@pytest.mark.asyncio
async def test_flashcard_full_cycle(client, flashcard_scenario):
    week_id = flashcard_scenario["week_id"]
    headers = flashcard_scenario["headers"]

    plan_r = await client.post(
        "/api/v1/study/plans",
        json={"mode": "flashcard", "week_ids": [week_id], "shuffle": False},
        headers=headers,
    )
    assert plan_r.status_code == 201
    plan_id = plan_r.json()["plan_id"]

    levels = ["known", "unknown"]
    for i in range(2):
        next_r = await client.get(f"/api/v1/study/plans/{plan_id}/next", headers=headers)
        assert next_r.status_code == 200
        question_id = next_r.json()["question_id"]

        ans_r = await client.post(
            f"/api/v1/study/plans/{plan_id}/answer/flashcard",
            json={"question_id": question_id, "knowledge_level": levels[i]},
            headers=headers,
        )
        assert ans_r.status_code == 200

    progress_r = await client.get(f"/api/v1/study/plans/{plan_id}", headers=headers)
    assert progress_r.json()["status"] == "completed"
    assert progress_r.json()["correct_count"] == 1
    assert progress_r.json()["wrong_count"] == 1
