import pytest
from fastapi.testclient import TestClient


def register(client, email="u@test.com", password="Password1!", name="Test User"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": name})


def login(client, email="u@test.com", password="Password1!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_header(client, email="u@test.com", password="Password1!"):
    r = login(client, email, password)
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── Registration ──────────────────────────────────────────────────────────────

def test_register_student(client):
    r = register(client)
    assert r.status_code == 201
    data = r.json()
    assert data["role"] == "student"
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    register(client)
    r = register(client)
    assert r.status_code == 409


def test_register_weak_password(client):
    r = register(client, password="short")
    assert r.status_code == 422


def test_register_cannot_set_instructor_role(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "hack@test.com", "password": "Password1!", "full_name": "Hacker", "role": "instructor"
    })
    # role field is ignored; user is always student
    if r.status_code == 201:
        assert r.json()["role"] == "student"


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    register(client)
    r = login(client, password="WrongPass1!")
    assert r.status_code == 401


def test_login_unknown_email(client):
    r = login(client, email="nobody@test.com")
    assert r.status_code == 401


def test_login_sets_refresh_cookie(client):
    register(client)
    r = login(client)
    assert "refresh_token" in r.cookies


# ── /me ───────────────────────────────────────────────────────────────────────

def test_me_authenticated(client):
    register(client)
    headers = auth_header(client)
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "u@test.com"


def test_me_unauthenticated(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


# ── Refresh & Logout ──────────────────────────────────────────────────────────

def test_refresh_token(client):
    register(client)
    login(client)  # sets cookie on client
    r = client.post("/api/v1/auth/refresh", headers={"origin": "http://localhost:3000"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_logout_revokes_session(client):
    register(client)
    login(client)
    client.post("/api/v1/auth/logout", headers={"origin": "http://localhost:3000"})
    r = client.post("/api/v1/auth/refresh", headers={"origin": "http://localhost:3000"})
    assert r.status_code == 401


def test_refresh_without_origin_rejected(client):
    register(client)
    login(client)
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 403


def test_logout_without_origin_rejected(client):
    register(client)
    login(client)
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 403


# ── FIND-002a: SECRET_KEY minimum length ──────────────────────────────────────

def test_secret_key_validator_rejects_short_key():
    from pydantic import ValidationError
    from app.core.config import Settings
    with pytest.raises(ValidationError, match="SECRET_KEY must be at least 32 characters"):
        Settings(SECRET_KEY="tooshort", DATABASE_URL="sqlite:///./x.db")


def test_secret_key_validator_accepts_32_char_key():
    from app.core.config import Settings
    s = Settings(SECRET_KEY="a" * 32, DATABASE_URL="sqlite:///./x.db")
    assert len(s.SECRET_KEY) == 32


# ── FIND-007: Rate limiter uses X-Forwarded-For ───────────────────────────────

def test_rate_limiter_reads_x_forwarded_for(client):
    """Rate limiter must use X-Forwarded-For, not request.client.host."""
    from app.main import _rate_store
    # Clear any prior state for this IP
    key = "1.2.3.4:/api/v1/auth/login"
    _rate_store.pop(key, None)
    # 10 requests succeed (limit is 10/min for /auth/login)
    for _ in range(10):
        client.post("/api/v1/auth/login",
                    json={"email": "x@x.com", "password": "x"},
                    headers={"x-forwarded-for": "1.2.3.4"})
    # 11th must be rate-limited
    r = client.post("/api/v1/auth/login",
                    json={"email": "x@x.com", "password": "x"},
                    headers={"x-forwarded-for": "1.2.3.4"})
    assert r.status_code == 429
    _rate_store.pop(key, None)  # cleanup
