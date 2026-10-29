# Import all models so Alembic can detect them
from app.db.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.auth_session import AuthSession  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.lesson import Lesson  # noqa: F401
from app.models.enrollment import Enrollment  # noqa: F401
from app.models.lesson_progress import LessonProgress  # noqa: F401
