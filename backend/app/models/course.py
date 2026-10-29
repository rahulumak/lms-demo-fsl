import enum
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Enum as SAEnum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CourseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, nullable=False, index=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[CourseStatus] = mapped_column(SAEnum(CourseStatus), nullable=False, default=CourseStatus.draft)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    instructor: Mapped["User"] = relationship("User", back_populates="courses")
    lessons: Mapped[list["Lesson"]] = relationship("Lesson", back_populates="course", cascade="all, delete-orphan", order_by="Lesson.position")
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
