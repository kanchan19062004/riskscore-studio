from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

USER = {"email": "Analyst@Example.com", "full_name": "Risk Analyst", "password": "secret123"}


def register(client, **overrides):
    return client.post("/api/v1/auth/register", json={**USER, **overrides})


def login(client, email=USER["email"], password=USER["password"]):
    return client.post("/api/v1/auth/login", data={"username": email, "password": password})


def test_register_creates_user_without_leaking_password(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "analyst@example.com"
    assert body["role"] == "analyst"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email_case_insensitively(client):
    register(client)
    response = register(client, email="ANALYST@example.com")

    assert response.status_code == 409


def test_register_rejects_weak_password(client):
    response = register(client, password="onlyletters")

    assert response.status_code == 422


def test_login_returns_token_that_unlocks_me(client):
    register(client)
    response = login(client)

    assert response.status_code == 200
    token = response.json()["access_token"]
    assert response.json()["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "analyst@example.com"


def test_login_gives_same_error_for_wrong_password_and_unknown_email(client):
    register(client)
    wrong_password = login(client, password="wrongpass1")
    unknown_email = login(client, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_requires_a_valid_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    garbage = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert garbage.status_code == 401


def test_me_rejects_expired_token(client):
    user_id = register(client).json()["id"]
    expired = jwt.encode(
        {"sub": user_id, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_me_rejects_token_signed_with_another_secret(client):
    user_id = register(client).json()["id"]
    forged = jwt.encode(
        {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "attacker-controlled-secret-that-is-long-enough",
        algorithm="HS256",
    )

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401
