from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
import re


ALLOWED_VIDEO_SCHEMES = ("https://www.youtube.com", "https://youtu.be", "https://vimeo.com", "https://player.vimeo.com")


def validate_video_url(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        return None
    if not any(v.startswith(prefix) for prefix in ALLOWED_VIDEO_SCHEMES):
        raise ValueError("video_url must be a YouTube or Vimeo URL")
    return v


class LessonCreate(BaseModel):
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_published: bool = False

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title is required")
        return v

    @field_validator("video_url")
    @classmethod
    def check_video_url(cls, v):
        return validate_video_url(v)

    @field_validator("duration_minutes")
    @classmethod
    def non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("duration_minutes must be non-negative")
        return v


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_published: Optional[bool] = None

    @field_validator("video_url")
    @classmethod
    def check_video_url(cls, v):
        return validate_video_url(v)


class LessonReorderItem(BaseModel):
    lesson_id: int
    position: int


class LessonReorderRequest(BaseModel):
    lessons: List[LessonReorderItem]


class LessonOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    course_id: int
    title: str
    position: int
    content: Optional[str]
    video_url: Optional[str]
    duration_minutes: Optional[int]
    is_published: bool
    created_at: datetime
    updated_at: datetime
