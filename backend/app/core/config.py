from urllib.parse import urlsplit

from pydantic import SecretStr, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://eve_user:eve_password@localhost:5433/eve_healthcare"
    MIGRATION_DATABASE_URL: str | None = None

    JWT_SECRET_KEY: str = "local-only-change-me-before-deployment"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    FIREBASE_CREDENTIALS_PATH: str | None = None
    FIREBASE_CREDENTIALS_JSON: SecretStr | None = None

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
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    @field_validator("REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND")
    @classmethod
    def validate_redis_url(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None or (value == "" and info.field_name != "REDIS_URL"):
            return None
        try:
            parsed = urlsplit(value)
            valid = parsed.scheme in {"redis", "rediss"} and bool(parsed.hostname)
            # Accessing port validates malformed port numbers without exposing the URL.
            _ = parsed.port
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("Redis URLs must use redis:// or rediss:// and include a valid host")
        return value

    @model_validator(mode="after")
    def validate_deployment_settings(self):
        if self.CELERY_BROKER_URL is None:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if self.CELERY_RESULT_BACKEND is None:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL

        if self.ENVIRONMENT.lower() == "production":
            if self.ENABLE_DEV_AUTH:
                raise ValueError("ENABLE_DEV_AUTH must be disabled in production")
            if self.JWT_SECRET_KEY == "local-only-change-me-before-deployment" or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("Production JWT_SECRET_KEY must be a strong value of at least 32 characters")
            if self.RAZORPAY_MODE != "test":
                raise ValueError("Only Razorpay test mode is currently supported")
            database_url = urlsplit(self.DATABASE_URL)
            if database_url.scheme not in {"postgresql", "postgresql+psycopg"} or not database_url.hostname or database_url.hostname in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("DATABASE_URL must point to the configured production database")
            redis_urls = (self.REDIS_URL, self.CELERY_BROKER_URL, self.CELERY_RESULT_BACKEND)
            if any(urlsplit(url).hostname in {"localhost", "127.0.0.1", "::1"} for url in redis_urls):
                raise ValueError("Production Redis and Celery URLs must point to configured services")
            if any(urlsplit(url).scheme != "rediss" for url in redis_urls):
                raise ValueError("Production Redis and Celery URLs must use TLS (rediss://)")
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
            if not origins or "*" in origins or any(not origin.startswith("https://") for origin in origins):
                raise ValueError("Production CORS_ORIGINS must list exact public HTTPS origins")
        return self


settings = Settings()
