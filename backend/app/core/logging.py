import logging
import logging.config
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.request_context import get_request_id

REDACTED = "***REDACTED***"
DEFAULT_REDACT_FIELDS = {
    "authorization",
    "password",
    "token",
    "tokenid",
    "clientid",
    "jwt",
    "access_token",
    "refresh_token",
    "api_key",
    "secret",
    "pan",
    "passportno",
    "passportnumber",
    "passport",
    "email",
    "contactno",
    "mobile",
    "phone",
}


# inject request_id into every log record
class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


# Prevents crashes if request_id missing
class SafeExtraFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return super().format(record)


def _logs_dir() -> Path:
    if settings.BACKEND_LOG_DIR:
        return Path(settings.BACKEND_LOG_DIR)
    backend_root = Path(__file__).resolve().parents[2]
    base = (
        backend_root.parent if backend_root.name.lower() == "backend" else backend_root
    )
    return base / "logs"


def setup_logging() -> None:
    logs_dir = _logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "backend.log"

    handlers = ["file"]
    if settings.ENABLE_CONSOLE_LOGGING:
        handlers.append("console")

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {"()": "app.core.logging.RequestIdFilter"},
            },
            "formatters": {
                "standard": {
                    "()": "app.core.logging.SafeExtraFormatter",
                    "format": "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s",
                }
            },
            "handlers": {
                # logs to terminal
                "console": {
                    "class": "logging.StreamHandler",
                    "level": settings.LOG_LEVEL,
                    "formatter": "standard",
                    "filters": ["request_id"],
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": settings.LOG_LEVEL,
                    "formatter": "standard",
                    "filters": ["request_id"],
                    "filename": str(log_file),
                    "when": "midnight",
                    "backupCount": settings.LOG_RETENTION_DAYS,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": settings.LOG_LEVEL,
                "handlers": handlers,
            },
            # Ensures FastAPI server logs use same format
            "loggers": {
                "uvicorn": {
                    "level": settings.LOG_LEVEL,
                    "handlers": handlers,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": settings.LOG_LEVEL,
                    "handlers": handlers,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": settings.LOG_LEVEL,
                    "handlers": handlers,
                    "propagate": False,
                },
            },
        }
    )


def _normalize_redact_fields(custom_fields: str | None) -> set[str]:
    fields = set(DEFAULT_REDACT_FIELDS)
    if custom_fields:
        fields.update(
            part.strip().lower() for part in custom_fields.split(",") if part.strip()
        )
    return fields


def sanitize_for_logging(value: Any, redact_fields: set[str] | None = None) -> Any:
    fields = redact_fields or _normalize_redact_fields(settings.LOG_REDACT_FIELDS)

    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, inner_value in value.items():
            if key.lower() in fields:
                sanitized[key] = REDACTED
            else:
                sanitized[key] = sanitize_for_logging(inner_value, fields)
        return sanitized

    if isinstance(value, list):
        return [sanitize_for_logging(item, fields) for item in value]

    if isinstance(value, tuple):
        return tuple(sanitize_for_logging(item, fields) for item in value)

    return value
