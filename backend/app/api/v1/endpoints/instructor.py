from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.dependencies import require_instructor
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate, CourseOut, CourseListItem
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonOut, LessonReorderRequest
from app.schemas.progress import StudentProgressSummary, CourseProgressOut
from app.services import course_service, lesson_service, progress_service

router = APIRouter(prefix="/instructor", tags=["instructor"])


# ── Courses ───────────────────────────────────────────────────────────────────

@router.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    data: CourseCreate,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    return course_service.create_course(db, instructor, data)


@router.get("/courses", response_model=list[CourseListItem])
def list_my_courses(
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    courses = course_service.get_instructor_courses(db, instructor.id)
    result = []
    for c in courses:
        count = course_service.get_enrollment_count(db, c.id)
        result.append(CourseListItem.model_validate({**c.__dict__, "enrollment_count": count}))
    return result


@router.get("/courses/{course_id}", response_model=CourseOut)
def get_my_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    return course


@router.patch("/courses/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    data: CourseUpdate,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    return course_service.update_course(db, course, data)


@router.post("/courses/{course_id}/publish", response_model=CourseOut)
def publish_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    return course_service.publish_course(db, course)


@router.post("/courses/{course_id}/archive", response_model=CourseOut)
def archive_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    return course_service.archive_course(db, course)


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    course_service.delete_course(db, course)


# ── Lessons — reorder MUST come before /{lesson_id} to avoid path conflict ───

@router.patch("/courses/{course_id}/lessons/reorder", response_model=list[LessonOut])
def reorder_lessons(
    course_id: int,
    data: LessonReorderRequest,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    return lesson_service.reorder_lessons(db, course, data)


@router.post("/courses/{course_id}/lessons", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
def create_lesson(
    course_id: int,
    data: LessonCreate,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    return lesson_service.create_lesson(db, course, data)


@router.get("/courses/{course_id}/lessons", response_model=list[LessonOut])
def list_lessons(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    return lesson_service.get_course_lessons(db, course_id)


@router.patch("/courses/{course_id}/lessons/{lesson_id}", response_model=LessonOut)
def update_lesson(
    course_id: int,
    lesson_id: int,
    data: LessonUpdate,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    lesson = lesson_service.get_lesson_or_404(db, lesson_id, course_id)
    return lesson_service.update_lesson(db, lesson, data)


@router.delete("/courses/{course_id}/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    course_id: int,
    lesson_id: int,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    lesson = lesson_service.get_lesson_or_404(db, lesson_id, course_id)
    lesson_service.delete_lesson(db, lesson)


# ── Progress ──────────────────────────────────────────────────────────────────

@router.get("/courses/{course_id}/progress", response_model=list[StudentProgressSummary])
def course_progress(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    return progress_service.get_instructor_course_progress(db, course_id)


@router.get("/courses/{course_id}/students/{student_id}/progress", response_model=CourseProgressOut)
def student_progress(
    course_id: int,
    student_id: int,
    db: Annotated[Session, Depends(get_db)],
    instructor: Annotated[User, Depends(require_instructor)],
):
    course = course_service.get_course_or_404(db, course_id)
    course_service.assert_owns_course(course, instructor)
    return progress_service.get_course_progress(db, student_id, course_id)
