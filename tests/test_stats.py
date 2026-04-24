import pytest
import pytest_asyncio

from app.repositories.user import user_repo


@pytest_asyncio.fixture(scope="session")
async def stats_scenario(client, session_factory):
    admin_email = "admin_stats@example.com"
    await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "pw"})
    async with session_factory() as db:
        user = await user_repo.get_by_email(db, admin_email)
        user.is_admin = True
        await db.commit()
    login_r = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "pw"})
    admin_h = {"Authorization": f"Bearer {login_r.json()['access_token']}"}

    subject_r = await client.post(
        "/api/v1/admin/subjects", json={"name": "Stats Subject"}, headers=admin_h
    )
    week_r = await client.post(
        "/api/v1/admin/weeks",
        json={"subject_id": subject_r.json()["id"], "week_number": 1, "title": "Stats Week"},
        headers=admin_h,
    )
    week_id = week_r.json()["id"]

    for i in range(4):
        await client.post(
            "/api/v1/admin/questions",
            json={
                "week_id": week_id,
                "type": "test",
                "question_text": f"Stats Q{i}?",
                "options": ["A", "B", "C", "D"],
                "correct_option_index": 0,
            },
            headers=admin_h,
        )

    user_email = "student_stats@example.com"
    await client.post("/api/v1/auth/register", json={"email": user_email, "password": "pw"})
    login = await client.post("/api/v1/auth/login", json={"email": user_email, "password": "pw"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    plan_r = await client.post(
        "/api/v1/study/plans",
        json={"mode": "test", "week_ids": [week_id], "shuffle": False},
        headers=headers,
    )
    plan_id = plan_r.json()["plan_id"]

    wrong_done = False
    for _ in range(4):
        next_r = await client.get(f"/api/v1/study/plans/{plan_id}/next", headers=headers)
        question_id = next_r.json()["question_id"]
        chosen = 1 if not wrong_done else 0
        wrong_done = True
        await client.post(
            f"/api/v1/study/plans/{plan_id}/answer/test",
            json={"question_id": question_id, "chosen_option_index": chosen},
            headers=headers,
        )

    return {"headers": headers}


@pytest.mark.asyncio
async def test_subject_stats(client, stats_scenario):
    headers = stats_scenario["headers"]
    r = await client.get("/api/v1/stats/subjects", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) > 0
    stat = r.json()[0]
    assert "accuracy" in stat
    assert 0.0 <= stat["accuracy"] <= 1.0


@pytest.mark.asyncio
async def test_session_history(client, stats_scenario):
    headers = stats_scenario["headers"]
    r = await client.get("/api/v1/stats/sessions", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert r.json()[0]["mode"] == "test"
