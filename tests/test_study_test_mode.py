import pytest
import pytest_asyncio

from app.repositories.user import user_repo


@pytest_asyncio.fixture(scope="session")
async def test_mode_scenario(client, session_factory):
    admin_email = "admin_study_test@example.com"
    await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "pw"})
    async with session_factory() as db:
        user = await user_repo.get_by_email(db, admin_email)
        user.is_admin = True
        await db.commit()
    login_r = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "pw"})
    admin_h = {"Authorization": f"Bearer {login_r.json()['access_token']}"}

    subject_r = await client.post(
        "/api/v1/admin/subjects", json={"name": "Тест: предмет"}, headers=admin_h
    )
    week_r = await client.post(
        "/api/v1/admin/weeks",
        json={"subject_id": subject_r.json()["id"], "week_number": 1, "title": "Неделя 1"},
        headers=admin_h,
    )
    week_id = week_r.json()["id"]

    for i in range(3):
        await client.post(
            "/api/v1/admin/questions",
            json={
                "week_id": week_id,
                "type": "test",
                "question_text": f"Вопрос {i + 1}?",
                "options": ["A", "B", "C", "D"],
                "correct_option_index": 0,
                "explanation": "Правильный ответ A",
            },
            headers=admin_h,
        )

    user_email = "student_test_mode@example.com"
    await client.post("/api/v1/auth/register", json={"email": user_email, "password": "pw"})
    login = await client.post("/api/v1/auth/login", json={"email": user_email, "password": "pw"})
    user_h = {"Authorization": f"Bearer {login.json()['access_token']}"}

    return {"week_id": week_id, "user_headers": user_h}


@pytest.mark.asyncio
async def test_full_test_mode_cycle(client, test_mode_scenario):
    week_id = test_mode_scenario["week_id"]
    headers = test_mode_scenario["user_headers"]

    plan_r = await client.post(
        "/api/v1/study/plans",
        json={"mode": "test", "week_ids": [week_id], "shuffle": False},
        headers=headers,
    )
    assert plan_r.status_code == 201
    plan_id = plan_r.json()["plan_id"]
    total = plan_r.json()["total_items"]
    assert total == 3

    for _ in range(total):
        next_r = await client.get(f"/api/v1/study/plans/{plan_id}/next", headers=headers)
        assert next_r.status_code == 200
        question_id = next_r.json()["question_id"]

        answer_r = await client.post(
            f"/api/v1/study/plans/{plan_id}/answer/test",
            json={"question_id": question_id, "chosen_option_index": 0},
            headers=headers,
        )
        assert answer_r.status_code == 200
        assert answer_r.json()["is_correct"] is True

    progress_r = await client.get(f"/api/v1/study/plans/{plan_id}", headers=headers)
    assert progress_r.json()["status"] == "completed"
    assert progress_r.json()["correct_count"] == 3


@pytest.mark.asyncio
async def test_wrong_answer(client, test_mode_scenario):
    week_id = test_mode_scenario["week_id"]
    headers = test_mode_scenario["user_headers"]

    plan_r = await client.post(
        "/api/v1/study/plans",
        json={"mode": "test", "week_ids": [week_id], "shuffle": False, "max_items": 1},
        headers=headers,
    )
    plan_id = plan_r.json()["plan_id"]

    next_r = await client.get(f"/api/v1/study/plans/{plan_id}/next", headers=headers)
    question_id = next_r.json()["question_id"]

    answer_r = await client.post(
        f"/api/v1/study/plans/{plan_id}/answer/test",
        json={"question_id": question_id, "chosen_option_index": 2},
        headers=headers,
    )
    assert answer_r.json()["is_correct"] is False
    assert answer_r.json()["correct_option_index"] == 0


@pytest.mark.asyncio
async def test_double_answer_conflict(client, test_mode_scenario):
    week_id = test_mode_scenario["week_id"]
    headers = test_mode_scenario["user_headers"]

    plan_r = await client.post(
        "/api/v1/study/plans",
        json={"mode": "test", "week_ids": [week_id], "shuffle": False, "max_items": 1},
        headers=headers,
    )
    plan_id = plan_r.json()["plan_id"]

    next_r = await client.get(f"/api/v1/study/plans/{plan_id}/next", headers=headers)
    question_id = next_r.json()["question_id"]

    await client.post(
        f"/api/v1/study/plans/{plan_id}/answer/test",
        json={"question_id": question_id, "chosen_option_index": 0},
        headers=headers,
    )
    r2 = await client.post(
        f"/api/v1/study/plans/{plan_id}/answer/test",
        json={"question_id": question_id, "chosen_option_index": 0},
        headers=headers,
    )
    assert r2.status_code == 409
