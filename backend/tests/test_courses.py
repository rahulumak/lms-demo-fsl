import pytest


def _make_instructor(client):
    """Create an instructor directly via DB override."""
    from tests.conftest import TestingSession
    from app.models.user import User, UserRole
    from app.core.security import hash_password
    db = TestingSession()
    u = User(full_name="Inst", email="inst@test.com", password_hash=hash_password("Pass1234!"), role=UserRole.instructor)
    db.add(u)
    db.commit()
    db.refresh(u)
    db.close()
    return u


def _instructor_token(client):
    _make_instructor(client)
    r = client.post("/api/v1/auth/login", json={"email": "inst@test.com", "password": "Pass1234!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _student_token(client, email="stu@test.com"):
    client.post("/api/v1/auth/register", json={"email": email, "password": "Pass1234!", "full_name": "Stu"})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Pass1234!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _create_course(client, headers, title="Test Course"):
    r = client.post("/api/v1/instructor/courses", json={"title": title}, headers=headers)
    assert r.status_code == 201
    return r.json()


# ── Course CRUD ───────────────────────────────────────────────────────────────

def test_instructor_create_course(client):
    h = _instructor_token(client)
    r = client.post("/api/v1/instructor/courses", json={"title": "My Course"}, headers=h)
    assert r.status_code == 201
    assert r.json()["status"] == "draft"


def test_student_cannot_create_course(client):
    h = _student_token(client)
    r = client.post("/api/v1/instructor/courses", json={"title": "Hack"}, headers=h)
    assert r.status_code == 403


def test_instructor_cannot_edit_other_course(client):
    h1 = _instructor_token(client)
    course = _create_course(client, h1)

    # second instructor
    from tests.conftest import TestingSession
    from app.models.user import User, UserRole
    from app.core.security import hash_password
    db = TestingSession()
    u2 = User(full_name="Inst2", email="inst2@test.com", password_hash=hash_password("Pass1234!"), role=UserRole.instructor)
    db.add(u2)
    db.commit()
    db.close()
    r2 = client.post("/api/v1/auth/login", json={"email": "inst2@test.com", "password": "Pass1234!"})
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    r = client.patch(f"/api/v1/instructor/courses/{course['id']}", json={"title": "Stolen"}, headers=h2)
    assert r.status_code == 403


def test_publish_and_archive_course(client):
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]

    r = client.post(f"/api/v1/instructor/courses/{cid}/publish", headers=h)
    assert r.json()["status"] == "published"

    r = client.post(f"/api/v1/instructor/courses/{cid}/archive", headers=h)
    assert r.json()["status"] == "archived"


def test_cannot_publish_archived_course(client):
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]
    client.post(f"/api/v1/instructor/courses/{cid}/archive", headers=h)
    r = client.post(f"/api/v1/instructor/courses/{cid}/publish", headers=h)
    assert r.status_code == 400


# ── Lessons ───────────────────────────────────────────────────────────────────

def test_create_and_list_lessons(client):
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]

    r = client.post(f"/api/v1/instructor/courses/{cid}/lessons",
                    json={"title": "Lesson 1"}, headers=h)
    assert r.status_code == 201
    assert r.json()["position"] == 1

    r2 = client.post(f"/api/v1/instructor/courses/{cid}/lessons",
                     json={"title": "Lesson 2"}, headers=h)
    assert r2.json()["position"] == 2

    r3 = client.get(f"/api/v1/instructor/courses/{cid}/lessons", headers=h)
    assert len(r3.json()) == 2


def test_reorder_lessons(client):
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]
    l1 = client.post(f"/api/v1/instructor/courses/{cid}/lessons", json={"title": "L1"}, headers=h).json()
    l2 = client.post(f"/api/v1/instructor/courses/{cid}/lessons", json={"title": "L2"}, headers=h).json()

    r = client.patch(f"/api/v1/instructor/courses/{cid}/lessons/reorder",
                     json={"lessons": [{"lesson_id": l1["id"], "position": 2}, {"lesson_id": l2["id"], "position": 1}]},
                     headers=h)
    assert r.status_code == 200
    ordered = r.json()
    assert ordered[0]["id"] == l2["id"]


def test_delete_lesson_compacts_positions(client):
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]
    l1 = client.post(f"/api/v1/instructor/courses/{cid}/lessons", json={"title": "L1"}, headers=h).json()
    l2 = client.post(f"/api/v1/instructor/courses/{cid}/lessons", json={"title": "L2"}, headers=h).json()
    l3 = client.post(f"/api/v1/instructor/courses/{cid}/lessons", json={"title": "L3"}, headers=h).json()

    client.delete(f"/api/v1/instructor/courses/{cid}/lessons/{l2['id']}", headers=h)
    lessons = client.get(f"/api/v1/instructor/courses/{cid}/lessons", headers=h).json()
    positions = [l["position"] for l in lessons]
    assert positions == [1, 2]
