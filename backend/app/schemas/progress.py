from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.enrollment import EnrollmentStatus
from app.models.lesson_progress import ProgressStatus


class EnrollmentOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    student_id: int
    course_id: int
    status: EnrollmentStatus
    enrolled_at: datetime
    completed_at: Optional[datetime]
    last_accessed_at: Optional[datetime]


class LessonProgressOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    enrollment_id: int
    lesson_id: int
    status: ProgressStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_position_seconds: Optional[int]
    updated_at: datetime


class CourseProgressOut(BaseModel):
    enrollment: EnrollmentOut
    progress_percentage: int
    completed_lessons: int
    total_published_lessons: int
    lesson_progress: List[LessonProgressOut] = []


class StudentProgressSummary(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    enrollment: EnrollmentOut
    progress_percentage: int
    completed_lessons: int
    total_published_lessons: int
