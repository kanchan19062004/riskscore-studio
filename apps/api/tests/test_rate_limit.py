from app.core.config import settings
from app.core.rate_limit import BrokenRateLimiter, set_rate_limiter
from tests.conftest import train
from tests.test_auth import login, register
from tests.test_scores import GROCERY, score


def test_login_returns_429_after_the_email_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_IP", 100)
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_EMAIL", 3)

    register(client, email="limited@example.com")
    for _ in range(3):
        assert login(client, email="limited@example.com", password="wrongpass1").status_code == 401

    blocked = login(client, email="limited@example.com", password="wrongpass1")
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"].isdigit()
    assert int(blocked.headers["Retry-After"]) >= 1
    assert blocked.headers["X-RateLimit-Limit"] == "3"
    assert blocked.headers["X-RateLimit-Remaining"] == "0"
    assert "try again" in blocked.json()["detail"].lower()


def test_successful_login_still_consumes_the_budget(client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_IP", 100)
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_EMAIL", 2)

    register(client, email="ok@example.com")
    assert login(client, email="ok@example.com").status_code == 200
    assert login(client, email="ok@example.com").status_code == 200
    blocked = login(client, email="ok@example.com")
    assert blocked.status_code == 429


def test_login_fails_closed_when_the_limiter_is_down(client):
    register(client)
    set_rate_limiter(BrokenRateLimiter())

    response = login(client)
    assert response.status_code == 429
    assert "try again" in response.json()["detail"].lower()


def test_scoring_returns_429_and_cache_hits_count(client, admin, analyst, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_SCORE_USER", 2)
    monkeypatch.setattr(settings, "RATE_LIMIT_SCORE_IP", 100)
    train(client, admin, seed=3)

    assert score(client, analyst, GROCERY).status_code == 201
    cached = score(client, analyst, GROCERY)
    assert cached.status_code == 201
    assert cached.json()["cache_hit"] is True

    blocked = score(client, analyst, GROCERY)
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"].isdigit()
    assert "scoring rate limit" in blocked.json()["detail"].lower()


def test_scoring_fails_open_when_the_limiter_is_down(client, admin, analyst):
    train(client, admin, seed=3)
    set_rate_limiter(BrokenRateLimiter())

    response = score(client, analyst, GROCERY)
    assert response.status_code == 201


def test_register_fails_closed_when_the_limiter_is_down(client):
    set_rate_limiter(BrokenRateLimiter())
    response = register(client, email="new@example.com")
    assert response.status_code == 429


def test_security_headers_are_present(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"


def test_oversized_body_is_rejected(client):
    response = client.post(
        "/api/v1/auth/register",
        content=b"x" * (64 * 1024 + 1),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
