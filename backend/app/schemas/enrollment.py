from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enrollment import EnrollmentStatus


class EnrollmentOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    student_id: int
    course_id: int
    status: EnrollmentStatus
    enrolled_at: datetime
    completed_at: Optional[datetime]
    last_accessed_at: Optional[datetime]
