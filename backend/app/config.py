from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24

    TBO_SHARED_BASE_URL: str
    TBO_AIR_BASE_URL: str
    TBO_CLIENT_ID: str
    TBO_USERNAME: str
    TBO_PASSWORD: str
    TBO_END_USER_IP: str

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        env_file_encoding = "utf-8"


settings = Settings()  # type: ignore
