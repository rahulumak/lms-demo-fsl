from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress, ProgressStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.course import Course
from app.schemas.progress import CourseProgressOut, StudentProgressSummary


def _get_or_create_progress(db: Session, enrollment: Enrollment, lesson: Lesson) -> LessonProgress:
    """Get or create a LessonProgress record. Raises 400 if lesson does not belong to enrollment's course."""
    if enrollment.course_id != lesson.course_id:
        raise HTTPException(
            status_code=400,
            detail="Lesson does not belong to the enrolled course",
        )
    lp = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enrollment.id,
        LessonProgress.lesson_id == lesson.id,
    ).first()
    if not lp:
        lp = LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson.id)
        db.add(lp)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            lp = db.query(LessonProgress).filter(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.lesson_id == lesson.id,
            ).first()
    return lp


def start_lesson(db: Session, student_id: int, lesson_id: int) -> LessonProgress:
    lesson = db.get(Lesson, lesson_id)
    if not lesson or not lesson.is_published:
        raise HTTPException(status_code=404, detail="Lesson not found")

    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == lesson.course_id,
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")

    lp = _get_or_create_progress(db, enrollment, lesson)
    if lp.status == ProgressStatus.not_started:
        lp.status = ProgressStatus.in_progress
        lp.started_at = datetime.now(timezone.utc)
    enrollment.last_accessed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lp)
    return lp


def complete_lesson(db: Session, student_id: int, lesson_id: int) -> LessonProgress:
    lesson = db.get(Lesson, lesson_id)
    if not lesson or not lesson.is_published:
        raise HTTPException(status_code=404, detail="Lesson not found")

    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == lesson.course_id,
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")

    lp = _get_or_create_progress(db, enrollment, lesson)
    now = datetime.now(timezone.utc)
    if lp.status != ProgressStatus.completed:
        lp.status = ProgressStatus.completed
        lp.completed_at = now
        if not lp.started_at:
            lp.started_at = now
    enrollment.last_accessed_at = now
    db.flush()

    _check_course_completion(db, enrollment)
    db.commit()
    db.refresh(lp)
    return lp


def _check_course_completion(db: Session, enrollment: Enrollment) -> None:
    published_lessons = db.query(Lesson).filter(
        Lesson.course_id == enrollment.course_id,
        Lesson.is_published == True,
    ).all()
    if not published_lessons:
        return
    completed_ids = {
        lp.lesson_id for lp in db.query(LessonProgress).filter(
            LessonProgress.enrollment_id == enrollment.id,
            LessonProgress.status == ProgressStatus.completed,
        ).all()
    }
    published_ids = {l.id for l in published_lessons}
    if published_ids.issubset(completed_ids):
        enrollment.status = EnrollmentStatus.completed
        if not enrollment.completed_at:
            enrollment.completed_at = datetime.now(timezone.utc)


def compute_progress(db: Session, enrollment: Enrollment) -> dict:
    published_lessons = db.query(Lesson).filter(
        Lesson.course_id == enrollment.course_id,
        Lesson.is_published == True,
    ).all()
    total = len(published_lessons)
    if total == 0:
        return {"progress_percentage": 0, "completed_lessons": 0, "total_published_lessons": 0}

    published_ids = {l.id for l in published_lessons}
    completed = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enrollment.id,
        LessonProgress.lesson_id.in_(published_ids),
        LessonProgress.status == ProgressStatus.completed,
    ).count()

    pct = round(completed / total * 100)
    return {"progress_percentage": pct, "completed_lessons": completed, "total_published_lessons": total}


def get_course_progress(db: Session, student_id: int, course_id: int) -> CourseProgressOut:
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id,
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    stats = compute_progress(db, enrollment)
    lesson_progress = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enrollment.id,
    ).all()
    return CourseProgressOut(
        enrollment=enrollment,
        lesson_progress=lesson_progress,
        **stats,
    )


def get_instructor_course_progress(db: Session, course_id: int) -> list[StudentProgressSummary]:
    from sqlalchemy.orm import joinedload
    enrollments = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.student))
        .filter(Enrollment.course_id == course_id)
        .all()
    )
    result = []
    for enrollment in enrollments:
        stats = compute_progress(db, enrollment)
        result.append(StudentProgressSummary(
            student_id=enrollment.student.id,
            student_name=enrollment.student.full_name,
            student_email=enrollment.student.email,
            enrollment=enrollment,
            **stats,
        ))
    return result


def get_student_lesson_progress(db: Session, enrollment_id: int, lesson_id: int) -> LessonProgress | None:
    return db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enrollment_id,
        LessonProgress.lesson_id == lesson_id,
    ).first()
