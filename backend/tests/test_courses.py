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
    # l2 was given position 1, so it should appear first
    assert ordered[0]["id"] == l2["id"]
    assert ordered[0]["position"] == 1
    assert ordered[1]["id"] == l1["id"]
    assert ordered[1]["position"] == 2


def test_reorder_with_duplicate_positions_rejected(client):
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]
    l1 = client.post(f"/api/v1/instructor/courses/{cid}/lessons", json={"title": "L1"}, headers=h).json()
    l2 = client.post(f"/api/v1/instructor/courses/{cid}/lessons", json={"title": "L2"}, headers=h).json()
    r = client.patch(f"/api/v1/instructor/courses/{cid}/lessons/reorder",
                     json={"lessons": [{"lesson_id": l1["id"], "position": 1}, {"lesson_id": l2["id"], "position": 1}]},
                     headers=h)
    assert r.status_code == 400


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
    ids = [l["id"] for l in lessons]
    assert l1["id"] in ids
    assert l3["id"] in ids
    assert l2["id"] not in ids


def test_delete_course_cascades_lessons_and_enrollments(client):
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]
    client.post(f"/api/v1/instructor/courses/{cid}/lessons", json={"title": "L1", "is_published": True}, headers=h)
    client.post(f"/api/v1/instructor/courses/{cid}/publish", headers=h)

    # enroll a student
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)

    # delete the course
    r = client.delete(f"/api/v1/instructor/courses/{cid}", headers=h)
    assert r.status_code == 204

    # course no longer accessible
    r = client.get(f"/api/v1/instructor/courses/{cid}", headers=h)
    assert r.status_code == 404

    # student's enrolled courses list is now empty
    r = client.get("/api/v1/students/me/courses", headers=sh)
    assert r.status_code == 200
    assert r.json() == []


def test_delete_course_not_owner_rejected(client):
    h1 = _instructor_token(client)
    course = _create_course(client, h1)

    from tests.conftest import TestingSession
    from app.models.user import User, UserRole
    from app.core.security import hash_password
    db = TestingSession()
    u2 = User(full_name="Inst2", email="inst2@test.com", password_hash=hash_password("Pass1234!"), role=UserRole.instructor)
    db.add(u2); db.commit(); db.close()
    r2 = client.post("/api/v1/auth/login", json={"email": "inst2@test.com", "password": "Pass1234!"})
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    r = client.delete(f"/api/v1/instructor/courses/{course['id']}", headers=h2)
    assert r.status_code == 403


def test_update_lesson_video_url_validated(client):
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]
    lesson = client.post(f"/api/v1/instructor/courses/{cid}/lessons", json={"title": "L1"}, headers=h).json()
    r = client.patch(f"/api/v1/instructor/courses/{cid}/lessons/{lesson['id']}",
                     json={"video_url": "https://evil.com/video"}, headers=h)
    assert r.status_code == 422


def test_create_lesson_invalid_video_url_rejected(client):
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]
    r = client.post(f"/api/v1/instructor/courses/{cid}/lessons",
                    json={"title": "L1", "video_url": "http://not-youtube.com/watch"}, headers=h)
    assert r.status_code == 422


def test_catalog_search(client):
    h = _instructor_token(client)
    _create_course(client, h, "Python Basics")
    _create_course(client, h, "React Advanced")
    # publish both
    courses = client.get("/api/v1/instructor/courses", headers=h).json()
    for c in courses:
        client.post(f"/api/v1/instructor/courses/{c['id']}/publish", headers=h)

    r = client.get("/api/v1/courses?search=python")
    assert r.status_code == 200
    items = r.json()["items"]
    assert all("python" in item["title"].lower() for item in items)


def test_catalog_draft_not_visible(client):
    h = _instructor_token(client)
    course = _create_course(client, h, "Secret Draft")
    r = client.get(f"/api/v1/courses/{course['id']}")
    assert r.status_code == 404


# ── FIND-003: _optional_user dead code removed ───────────────────────────────

def test_catalog_accessible_unauthenticated(client):
    """Catalog endpoints work without auth — confirms _optional_user removal didn't break anything."""
    r = client.get("/api/v1/courses")
    assert r.status_code == 200
    assert "items" in r.json()


def test_catalog_no_optional_user_attribute():
    """_optional_user must not exist in catalog module."""
    from app.api.v1.endpoints import catalog
    assert not hasattr(catalog, "_optional_user")


# ── FIND-004: my_courses response is typed ───────────────────────────────────

def test_my_courses_response_fields(client):
    """my_courses must return only the declared StudentCourseItem fields."""
    h = _instructor_token(client)
    course = _create_course(client, h)
    client.post(f"/api/v1/instructor/courses/{course['id']}/publish", headers=h)
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{course['id']}/enroll", headers=sh)

    r = client.get("/api/v1/students/me/courses", headers=sh)
    assert r.status_code == 200
    item = r.json()[0]
    expected_keys = {
        "enrollment_id", "course_id", "course_title", "course_slug",
        "course_thumbnail", "enrollment_status", "enrolled_at",
        "last_accessed_at", "progress_percentage", "completed_lessons",
        "total_published_lessons",
    }
    assert set(item.keys()) == expected_keys
    assert "password_hash" not in item


# ── FIND-005: my_course_lessons single DB call ────────────────────────────────

def test_my_course_lessons_returns_lessons(client):
    """my_course_lessons works correctly after the double-call fix."""
    h = _instructor_token(client)
    course = _create_course(client, h)
    cid = course["id"]
    client.post(f"/api/v1/instructor/courses/{cid}/lessons",
                json={"title": "L1", "is_published": True}, headers=h)
    client.post(f"/api/v1/instructor/courses/{cid}/publish", headers=h)
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)

    r = client.get(f"/api/v1/students/me/courses/{cid}/lessons", headers=sh)
    assert r.status_code == 200
    assert len(r.json()) == 1
