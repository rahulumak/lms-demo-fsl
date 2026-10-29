import pytest
from tests.conftest import TestingSession
from app.models.user import User, UserRole
from app.core.security import hash_password


def _make_instructor(email="inst@test.com"):
    db = TestingSession()
    u = User(full_name="Inst", email=email, password_hash=hash_password("Pass1234!"), role=UserRole.instructor)
    db.add(u)
    db.commit()
    db.refresh(u)
    db.close()


def _instructor_token(client, email="inst@test.com"):
    _make_instructor(email)
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Pass1234!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _student_token(client, email="stu@test.com"):
    client.post("/api/v1/auth/register", json={"email": email, "password": "Pass1234!", "full_name": "Stu"})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Pass1234!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _setup_published_course_with_lessons(client):
    ih = _instructor_token(client)
    course = client.post("/api/v1/instructor/courses", json={"title": "Pub Course"}, headers=ih).json()
    cid = course["id"]
    l1 = client.post(f"/api/v1/instructor/courses/{cid}/lessons",
                     json={"title": "L1", "is_published": True}, headers=ih).json()
    l2 = client.post(f"/api/v1/instructor/courses/{cid}/lessons",
                     json={"title": "L2", "is_published": True}, headers=ih).json()
    l3 = client.post(f"/api/v1/instructor/courses/{cid}/lessons",
                     json={"title": "L3 Draft", "is_published": False}, headers=ih).json()
    client.post(f"/api/v1/instructor/courses/{cid}/publish", headers=ih)
    return cid, l1, l2, l3, ih


# ── Enrollment ────────────────────────────────────────────────────────────────

def test_student_can_enroll_published(client):
    cid, *_ = _setup_published_course_with_lessons(client)
    sh = _student_token(client)
    r = client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)
    assert r.status_code == 201


def test_duplicate_enrollment_rejected(client):
    cid, *_ = _setup_published_course_with_lessons(client)
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)
    r = client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)
    assert r.status_code == 409


def test_cannot_enroll_draft_course(client):
    ih = _instructor_token(client)
    course = client.post("/api/v1/instructor/courses", json={"title": "Draft"}, headers=ih).json()
    sh = _student_token(client)
    r = client.post(f"/api/v1/courses/{course['id']}/enroll", headers=sh)
    assert r.status_code == 400


def test_instructor_cannot_enroll(client):
    cid, *_, ih = _setup_published_course_with_lessons(client)
    r = client.post(f"/api/v1/courses/{cid}/enroll", headers=ih)
    assert r.status_code == 403


# ── Progress ──────────────────────────────────────────────────────────────────

def test_lesson_completion_and_progress(client):
    cid, l1, l2, l3, ih = _setup_published_course_with_lessons(client)
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)

    # complete l1
    r = client.post(f"/api/v1/students/me/lessons/{l1['id']}/complete", headers=sh)
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    # check progress: 1/2 published = 50%
    r = client.get(f"/api/v1/students/me/courses/{cid}/progress", headers=sh)
    assert r.json()["progress_percentage"] == 50
    assert r.json()["total_published_lessons"] == 2  # draft excluded


def test_completion_is_idempotent(client):
    cid, l1, *_ = _setup_published_course_with_lessons(client)
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)
    client.post(f"/api/v1/students/me/lessons/{l1['id']}/complete", headers=sh)
    r = client.post(f"/api/v1/students/me/lessons/{l1['id']}/complete", headers=sh)
    assert r.status_code == 200


def test_course_marked_complete_when_all_lessons_done(client):
    cid, l1, l2, l3, ih = _setup_published_course_with_lessons(client)
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)
    client.post(f"/api/v1/students/me/lessons/{l1['id']}/complete", headers=sh)
    client.post(f"/api/v1/students/me/lessons/{l2['id']}/complete", headers=sh)

    r = client.get(f"/api/v1/students/me/courses/{cid}/progress", headers=sh)
    assert r.json()["progress_percentage"] == 100
    assert r.json()["enrollment"]["status"] == "completed"


def test_student_cannot_access_other_student_progress(client):
    cid, l1, *_ = _setup_published_course_with_lessons(client)
    sh1 = _student_token(client, "s1@test.com")
    sh2 = _student_token(client, "s2@test.com")
    client.post(f"/api/v1/courses/{cid}/enroll", headers=sh1)

    r = client.get(f"/api/v1/students/me/courses/{cid}/progress", headers=sh2)
    assert r.status_code == 404


def test_student_cannot_complete_unenrolled_lesson(client):
    cid, l1, *_ = _setup_published_course_with_lessons(client)
    sh = _student_token(client)
    # not enrolled
    r = client.post(f"/api/v1/students/me/lessons/{l1['id']}/complete", headers=sh)
    assert r.status_code == 403


def test_instructor_progress_report_own_course(client):
    cid, l1, l2, l3, ih = _setup_published_course_with_lessons(client)
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)
    client.post(f"/api/v1/students/me/lessons/{l1['id']}/complete", headers=sh)

    r = client.get(f"/api/v1/instructor/courses/{cid}/progress", headers=ih)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["progress_percentage"] == 50


def test_instructor_cannot_access_other_course_progress(client):
    cid, *_, ih1 = _setup_published_course_with_lessons(client)
    _make_instructor("inst2@test.com")
    r2 = client.post("/api/v1/auth/login", json={"email": "inst2@test.com", "password": "Pass1234!"})
    ih2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}
    r = client.get(f"/api/v1/instructor/courses/{cid}/progress", headers=ih2)
    assert r.status_code == 403


def test_unpublished_lessons_excluded_from_progress(client):
    cid, l1, l2, l3, ih = _setup_published_course_with_lessons(client)
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{cid}/enroll", headers=sh)

    # l3 is draft — student cannot complete it
    r = client.post(f"/api/v1/students/me/lessons/{l3['id']}/complete", headers=sh)
    assert r.status_code in (403, 404)

    r = client.get(f"/api/v1/students/me/courses/{cid}/progress", headers=sh)
    assert r.json()["total_published_lessons"] == 2


# ── FIND-008: Cross-course progress guard ───────────────────────────────────

def test_cannot_complete_lesson_from_different_course(client):
    """A student enrolled in course A cannot mark a lesson from course B as complete."""
    ih = _instructor_token(client)

    # Course A with one published lesson
    ca = client.post("/api/v1/instructor/courses", json={"title": "Course A"}, headers=ih).json()
    la = client.post(f"/api/v1/instructor/courses/{ca['id']}/lessons",
                     json={"title": "LA", "is_published": True}, headers=ih).json()
    client.post(f"/api/v1/instructor/courses/{ca['id']}/publish", headers=ih)

    # Course B with one published lesson
    cb = client.post("/api/v1/instructor/courses", json={"title": "Course B"}, headers=ih).json()
    lb = client.post(f"/api/v1/instructor/courses/{cb['id']}/lessons",
                     json={"title": "LB", "is_published": True}, headers=ih).json()
    client.post(f"/api/v1/instructor/courses/{cb['id']}/publish", headers=ih)

    # Student enrolls only in Course A
    sh = _student_token(client)
    client.post(f"/api/v1/courses/{ca['id']}/enroll", headers=sh)

    # Attempt to complete a lesson from Course B (not enrolled)
    r = client.post(f"/api/v1/students/me/lessons/{lb['id']}/complete", headers=sh)
    assert r.status_code == 403
