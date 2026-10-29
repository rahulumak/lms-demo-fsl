from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator
from app.models.course import CourseStatus


class CourseCreate(BaseModel):
    title: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title is required")
        return v


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None


class CourseOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    instructor_id: int
    title: str
    slug: str
    short_description: Optional[str]
    description: Optional[str]
    thumbnail_url: Optional[str]
    status: CourseStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]


class CourseListItem(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    title: str
    slug: str
    short_description: Optional[str]
    thumbnail_url: Optional[str]
    status: CourseStatus
    instructor_id: int
    published_at: Optional[datetime]
    enrollment_count: int = 0
