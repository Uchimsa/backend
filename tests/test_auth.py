import pytest


@pytest.mark.asyncio
async def test_register(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "test_reg@example.com", "password": "secret123"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "test_reg@example.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate(client):
    email = "dup@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "secret123"})
    r = await client.post("/api/v1/auth/register", json={"email": email, "password": "secret123"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    email = "login_ok@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "password"})
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "password"})
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    email = "login_fail@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "correct"})
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client):
    email = "me@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "pw"})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "pw"})
    token = login.json()["access_token"]

    r = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email
