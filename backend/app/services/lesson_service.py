from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.lesson import Lesson
from app.models.course import Course
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonReorderRequest


def _next_position(db: Session, course_id: int) -> int:
    from sqlalchemy import func
    result = db.query(func.max(Lesson.position)).filter(Lesson.course_id == course_id).scalar()
    return (result or 0) + 1


def create_lesson(db: Session, course: Course, data: LessonCreate) -> Lesson:
    position = _next_position(db, course.id)
    lesson = Lesson(
        course_id=course.id,
        title=data.title.strip(),
        position=position,
        content=data.content,
        video_url=data.video_url,
        duration_minutes=data.duration_minutes,
        is_published=data.is_published,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def get_lesson_or_404(db: Session, lesson_id: int, course_id: int) -> Lesson:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


def update_lesson(db: Session, lesson: Lesson, data: LessonUpdate) -> Lesson:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(lesson, field, value)
    db.commit()
    db.refresh(lesson)
    return lesson


def delete_lesson(db: Session, lesson: Lesson) -> None:
    course_id = lesson.course_id
    pos = lesson.position
    db.delete(lesson)
    db.flush()
    # Compact positions
    db.query(Lesson).filter(
        Lesson.course_id == course_id, Lesson.position > pos
    ).update({"position": Lesson.position - 1})
    db.commit()


def reorder_lessons(db: Session, course: Course, data: LessonReorderRequest) -> list[Lesson]:
    lesson_ids = {item.lesson_id for item in data.lessons}
    lessons = db.query(Lesson).filter(Lesson.course_id == course.id, Lesson.id.in_(lesson_ids)).all()
    if len(lessons) != len(lesson_ids):
        raise HTTPException(status_code=400, detail="Some lessons not found in this course")

    positions = [item.position for item in data.lessons]
    if len(set(positions)) != len(positions) or any(p < 1 for p in positions):
        raise HTTPException(status_code=400, detail="Positions must be unique positive integers")

    lesson_map = {l.id: l for l in lessons}
    # Use temp negative positions to avoid unique constraint conflicts
    for item in data.lessons:
        lesson_map[item.lesson_id].position = -item.lesson_id
    db.flush()
    for item in data.lessons:
        lesson_map[item.lesson_id].position = item.position
    db.commit()
    return sorted(lessons, key=lambda l: l.position)


def get_course_lessons(db: Session, course_id: int, published_only: bool = False) -> list[Lesson]:
    q = db.query(Lesson).filter(Lesson.course_id == course_id)
    if published_only:
        q = q.filter(Lesson.is_published == True)
    return q.order_by(Lesson.position).all()
