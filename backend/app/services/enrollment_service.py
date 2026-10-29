from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.course import Course, CourseStatus
from app.models.user import User


def enroll_student(db: Session, student: User, course_id: int) -> Enrollment:
    course = db.get(Course, course_id)
    if not course or course.status != CourseStatus.published:
        raise HTTPException(status_code=400, detail="Course not available for enrollment")

    existing = db.query(Enrollment).filter(
        Enrollment.student_id == student.id,
        Enrollment.course_id == course_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already enrolled")

    enrollment = Enrollment(student_id=student.id, course_id=course_id)
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Already enrolled")
    db.refresh(enrollment)
    return enrollment


def get_student_enrollments(db: Session, student_id: int) -> list[Enrollment]:
    return (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student_id)
        .order_by(Enrollment.enrolled_at.desc())
        .all()
    )


def get_enrollment_or_404(db: Session, student_id: int, course_id: int) -> Enrollment:
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id,
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment


def touch_last_accessed(db: Session, enrollment: Enrollment) -> None:
    enrollment.last_accessed_at = datetime.now(timezone.utc)
    db.commit()
