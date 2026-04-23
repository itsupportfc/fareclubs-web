from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    TBO_SHARED_BASE_URL: str
    TBO_AIR_BASE_URL: str
    TBO_CLIENT_ID: str
    TBO_USERNAME: str
    TBO_PASSWORD: str
    TBO_END_USER_IP: str

    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str

    # Redis — in docker-compose the hostname "redis" resolves to the redis container
    REDIS_URL: str = "redis://localhost:6379/0"

    SUPPORT_PHONE: str = ""
    SUPPORT_EMAIL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    STAFF_ALERT_EMAILS: str = ""  # comma-separated

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 14
    ENABLE_CONSOLE_LOGGING: bool = True
    ENABLE_TBO_BODY_LOGGING: bool = True
    LOG_REDACT_FIELDS: str = ""
    BACKEND_LOG_DIR: str | None = None

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        env_file_encoding = "utf-8"


settings = Settings()  # type: ignore
