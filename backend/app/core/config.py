from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./lms_dev.db"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    COOKIE_SECURE: bool = False
    LOG_LEVEL: str = "INFO"

    # Seed credentials
    SEED_INSTRUCTOR_EMAIL: str = "rahul.umak@test.com"
    SEED_INSTRUCTOR_PASSWORD: str = "InstructorPass1!"
    SEED_STUDENT1_EMAIL: str = "rutwij.bawaskar@test.com"
    SEED_STUDENT1_PASSWORD: str = "StudentPass1!"
    SEED_STUDENT2_EMAIL: str = "srividhya.suri@test.com"
    SEED_STUDENT2_PASSWORD: str = "StudentPass1!"
    SEED_STUDENT3_EMAIL: str = "rushikesh.cheke@test.com"
    SEED_STUDENT3_PASSWORD: str = "StudentPass1!"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
