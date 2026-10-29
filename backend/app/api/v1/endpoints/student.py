from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.dependencies import require_student
from app.models.user import User
from app.schemas.enrollment import StudentCourseItem
from app.schemas.lesson import LessonOut
from app.schemas.progress import CourseProgressOut, LessonProgressOut
from app.services import enrollment_service, lesson_service, progress_service

router = APIRouter(prefix="/students/me", tags=["student"])


@router.get("/courses", response_model=list[StudentCourseItem])
def my_courses(
    db: Annotated[Session, Depends(get_db)],
    student: Annotated[User, Depends(require_student)],
):
    enrollments = enrollment_service.get_student_enrollments(db, student.id)
    result = []
    for e in enrollments:
        stats = progress_service.compute_progress(db, e)
        result.append(StudentCourseItem(
            enrollment_id=e.id,
            course_id=e.course_id,
            course_title=e.course.title,
            course_slug=e.course.slug,
            course_thumbnail=e.course.thumbnail_url,
            enrollment_status=e.status,
            enrolled_at=e.enrolled_at,
            last_accessed_at=e.last_accessed_at,
            **stats,
        ))
    return result


@router.get("/courses/{course_id}/progress", response_model=CourseProgressOut)
def course_progress(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    student: Annotated[User, Depends(require_student)],
):
    return progress_service.get_course_progress(db, student.id, course_id)


@router.get("/courses/{course_id}/lessons", response_model=list[LessonOut])
def my_course_lessons(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    student: Annotated[User, Depends(require_student)],
):
    enrollment = enrollment_service.get_enrollment_or_404(db, student.id, course_id)
    enrollment_service.touch_last_accessed(db, enrollment)
    return lesson_service.get_course_lessons(db, course_id, published_only=True)


@router.post("/lessons/{lesson_id}/start", response_model=LessonProgressOut)
def start_lesson(
    lesson_id: int,
    db: Annotated[Session, Depends(get_db)],
    student: Annotated[User, Depends(require_student)],
):
    return progress_service.start_lesson(db, student.id, lesson_id)


@router.post("/lessons/{lesson_id}/complete", response_model=LessonProgressOut)
def complete_lesson(
    lesson_id: int,
    db: Annotated[Session, Depends(get_db)],
    student: Annotated[User, Depends(require_student)],
):
    return progress_service.complete_lesson(db, student.id, lesson_id)
