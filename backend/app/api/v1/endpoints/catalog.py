from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.course import CourseStatus
from app.schemas.course import CourseOut, CourseListItem
from app.schemas.lesson import LessonOut
from app.services import course_service, lesson_service, enrollment_service

router = APIRouter(prefix="/courses", tags=["catalog"])

@router.get("", response_model=dict)
def list_courses(
    db: Annotated[Session, Depends(get_db)],
    search: Optional[str] = Query(None, max_length=200),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    courses, total = course_service.list_published_courses(db, search, skip, limit)
    items = []
    for c in courses:
        count = course_service.get_enrollment_count(db, c.id)
        items.append(CourseListItem.model_validate({**c.__dict__, "enrollment_count": count}))
    return {"total": total, "items": items, "skip": skip, "limit": limit}


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Annotated[Session, Depends(get_db)]):
    course = course_service.get_course_or_404(db, course_id)
    if course.status != CourseStatus.published:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/lessons", response_model=list[LessonOut])
def get_course_lessons(course_id: int, db: Annotated[Session, Depends(get_db)]):
    course = course_service.get_course_or_404(db, course_id)
    if course.status != CourseStatus.published:
        raise HTTPException(status_code=404, detail="Course not found")
    return lesson_service.get_course_lessons(db, course_id, published_only=True)


@router.post("/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
def enroll(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can enroll in courses")
    enrollment = enrollment_service.enroll_student(db, current_user, course_id)
    return {"enrollment_id": enrollment.id, "course_id": enrollment.course_id}
