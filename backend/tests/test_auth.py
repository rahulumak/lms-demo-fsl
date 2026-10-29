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
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_logout_revokes_session(client):
    register(client)
    login(client)
    client.post("/api/v1/auth/logout")
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 401
