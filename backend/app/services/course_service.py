import re
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.course import Course, CourseStatus
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate
from datetime import datetime, timezone


def _slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:200]


def _unique_slug(db: Session, base: str) -> str:
    slug = base
    counter = 1
    while db.query(Course).filter(Course.slug == slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def create_course(db: Session, instructor: User, data: CourseCreate) -> Course:
    slug = _unique_slug(db, _slugify(data.title))
    course = Course(
        instructor_id=instructor.id,
        title=data.title.strip(),
        slug=slug,
        short_description=data.short_description,
        description=data.description,
        thumbnail_url=data.thumbnail_url,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def get_instructor_courses(db: Session, instructor_id: int) -> list[Course]:
    return db.query(Course).filter(Course.instructor_id == instructor_id).order_by(Course.created_at.desc()).all()


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def assert_owns_course(course: Course, instructor: User) -> None:
    if course.instructor_id != instructor.id:
        raise HTTPException(status_code=403, detail="Not your course")


def update_course(db: Session, course: Course, data: CourseUpdate) -> Course:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


def publish_course(db: Session, course: Course) -> Course:
    if course.status == CourseStatus.archived:
        raise HTTPException(status_code=400, detail="Cannot publish an archived course")
    course.status = CourseStatus.published
    if not course.published_at:
        course.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(course)
    return course


def archive_course(db: Session, course: Course) -> Course:
    course.status = CourseStatus.archived
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()


def list_published_courses(db: Session, search: str | None, skip: int, limit: int):
    q = db.query(Course).filter(Course.status == CourseStatus.published)
    if search:
        q = q.filter(Course.title.ilike(f"%{search}%"))
    total = q.count()
    courses = q.order_by(Course.published_at.desc()).offset(skip).limit(limit).all()
    return courses, total


def get_enrollment_count(db: Session, course_id: int) -> int:
    return db.query(func.count(Enrollment.id)).filter(Enrollment.course_id == course_id).scalar() or 0
