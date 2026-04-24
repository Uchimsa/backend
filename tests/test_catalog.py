import pytest
import pytest_asyncio

from app.repositories.user import user_repo


async def _promote_admin(session_factory, email: str) -> None:
    async with session_factory() as db:
        user = await user_repo.get_by_email(db, email)
        if user:
            user.is_admin = True
            await db.commit()


@pytest_asyncio.fixture(scope="session")
async def admin_headers(client, session_factory):
    email = "admin_catalog@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "pw"})
    await _promote_admin(session_factory, email)
    login_r = await client.post("/api/v1/auth/login", json={"email": email, "password": "pw"})
    return {"Authorization": f"Bearer {login_r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_create_subject(client, admin_headers):
    r = await client.post(
        "/api/v1/admin/subjects",
        json={"name": "Математика", "icon_name": "math"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["name"] == "Математика"


@pytest.mark.asyncio
async def test_list_subjects_public(client, admin_headers):
    await client.post("/api/v1/admin/subjects", json={"name": "Физика"}, headers=admin_headers)
    r = await client.get("/api/v1/subjects")
    assert r.status_code == 200
    names = [s["name"] for s in r.json()]
    assert "Физика" in names


@pytest.mark.asyncio
async def test_hidden_subject_not_in_public(client, admin_headers):
    create_r = await client.post(
        "/api/v1/admin/subjects", json={"name": "Секретный предмет"}, headers=admin_headers
    )
    subject_id = create_r.json()["id"]

    await client.patch(
        f"/api/v1/admin/subjects/{subject_id}",
        json={"is_hidden": True},
        headers=admin_headers,
    )

    r = await client.get("/api/v1/subjects")
    names = [s["name"] for s in r.json()]
    assert "Секретный предмет" not in names


@pytest.mark.asyncio
async def test_create_week_and_list(client, admin_headers):
    subject_r = await client.post(
        "/api/v1/admin/subjects", json={"name": "Химия"}, headers=admin_headers
    )
    subject_id = subject_r.json()["id"]

    week_r = await client.post(
        "/api/v1/admin/weeks",
        json={"subject_id": subject_id, "week_number": 1, "title": "Неделя 1. Введение"},
        headers=admin_headers,
    )
    assert week_r.status_code == 201

    r = await client.get(f"/api/v1/subjects/{subject_id}/weeks")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_create_question(client, admin_headers):
    subject_r = await client.post(
        "/api/v1/admin/subjects", json={"name": "Биология"}, headers=admin_headers
    )
    week_r = await client.post(
        "/api/v1/admin/weeks",
        json={"subject_id": subject_r.json()["id"], "week_number": 1, "title": "Клетка"},
        headers=admin_headers,
    )
    q_r = await client.post(
        "/api/v1/admin/questions",
        json={
            "week_id": week_r.json()["id"],
            "type": "test",
            "question_text": "Из чего состоит клетка?",
            "options": ["Ядро", "Митохондрия", "Вода", "Всё"],
            "correct_option_index": 3,
            "explanation": "Клетка содержит ядро, митохондрии и воду.",
        },
        headers=admin_headers,
    )
    assert q_r.status_code == 201
    assert q_r.json()["type"] == "test"
