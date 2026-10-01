from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://eve_user:eve_password@localhost:5433/eve_healthcare"

    JWT_SECRET_KEY: str = "local-only-change-me-before-deployment"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    FIREBASE_CREDENTIALS_PATH: str | None = None

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    RAZORPAY_MODE: str = "test"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    ENVIRONMENT: str = "development"
    ENABLE_DEV_AUTH: bool = False
    FIREBASE_PROJECT_ID: str | None = None
    INITIAL_ADMIN_EMAIL: str | None = None

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_deployment_settings(self):
        if self.ENVIRONMENT.lower() == "production":
            if self.ENABLE_DEV_AUTH:
                raise ValueError("ENABLE_DEV_AUTH must be disabled in production")
            if self.JWT_SECRET_KEY == "local-only-change-me-before-deployment" or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("Production JWT_SECRET_KEY must be a strong value of at least 32 characters")
            if self.RAZORPAY_MODE != "test":
                raise ValueError("Only Razorpay test mode is currently supported")
        return self


settings = Settings()
