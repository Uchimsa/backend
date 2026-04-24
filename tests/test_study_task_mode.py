import pytest
import pytest_asyncio

from app.repositories.user import user_repo


@pytest_asyncio.fixture(scope="session")
async def task_scenario(client, session_factory):
    admin_email = "admin_task@example.com"
    await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "pw"})
    async with session_factory() as db:
        user = await user_repo.get_by_email(db, admin_email)
        user.is_admin = True
        await db.commit()
    login_r = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "pw"})
    admin_h = {"Authorization": f"Bearer {login_r.json()['access_token']}"}

    subject_r = await client.post(
        "/api/v1/admin/subjects", json={"name": "Task Subject"}, headers=admin_h
    )
    week_r = await client.post(
        "/api/v1/admin/weeks",
        json={"subject_id": subject_r.json()["id"], "week_number": 1, "title": "Task Week"},
        headers=admin_h,
    )
    week_id = week_r.json()["id"]

    for i in range(3):
        await client.post(
            "/api/v1/admin/questions",
            json={
                "week_id": week_id,
                "type": "task",
                "question_text": f"Задача {i}: решите уравнение...",
                "answer_text": f"Ответ {i}: x = {i}",
                "explanation": f"Решение {i}",
            },
            headers=admin_h,
        )

    user_email = "student_task@example.com"
    await client.post("/api/v1/auth/register", json={"email": user_email, "password": "pw"})
    login = await client.post("/api/v1/auth/login", json={"email": user_email, "password": "pw"})
    user_h = {"Authorization": f"Bearer {login.json()['access_token']}"}

    return {"week_id": week_id, "headers": user_h}


@pytest.mark.asyncio
async def test_task_answer(client, task_scenario):
    week_id = task_scenario["week_id"]
    headers = task_scenario["headers"]

    plan_r = await client.post(
        "/api/v1/study/plans",
        json={"mode": "task", "week_ids": [week_id], "shuffle": False, "max_items": 1},
        headers=headers,
    )
    plan_id = plan_r.json()["plan_id"]

    next_r = await client.get(f"/api/v1/study/plans/{plan_id}/next", headers=headers)
    question_id = next_r.json()["question_id"]

    ans_r = await client.post(
        f"/api/v1/study/plans/{plan_id}/answer/task",
        json={"question_id": question_id, "answer_text": "x = 0"},
        headers=headers,
    )
    assert ans_r.status_code == 200
    data = ans_r.json()
    assert "ai_score" in data
    assert 0.0 <= data["ai_score"] <= 1.0


@pytest.mark.asyncio
async def test_skip_task(client, task_scenario):
    week_id = task_scenario["week_id"]
    headers = task_scenario["headers"]

    plan_r = await client.post(
        "/api/v1/study/plans",
        json={"mode": "task", "week_ids": [week_id], "shuffle": False, "max_items": 2},
        headers=headers,
    )
    plan_id = plan_r.json()["plan_id"]

    next_r = await client.get(f"/api/v1/study/plans/{plan_id}/next", headers=headers)
    question_id = next_r.json()["question_id"]

    skip_r = await client.post(
        f"/api/v1/study/plans/{plan_id}/skip",
        json={"question_id": question_id},
        headers=headers,
    )
    assert skip_r.status_code == 200
    assert skip_r.json()["skipped_count"] == 1
