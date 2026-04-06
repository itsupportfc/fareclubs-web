import json
import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler
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


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class SafeExtraFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return super().format(record)


def _project_logs_dir() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    if backend_root.name.lower() == "backend":
        return backend_root.parent / "logs"
    return backend_root / "logs"


def get_logs_dir() -> Path:
    return Path(settings.BACKEND_LOG_DIR) if settings.BACKEND_LOG_DIR else _project_logs_dir()


def get_log_paths() -> dict[str, Path]:
    logs_dir = get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    return {
        "backend": Path(settings.BACKEND_LOG_FILE) if settings.BACKEND_LOG_FILE else logs_dir / "backend.log",
        "internal_api": Path(settings.INTERNAL_API_LOG_FILE) if settings.INTERNAL_API_LOG_FILE else logs_dir / "internal_api.log",
        "tbo": Path(settings.TBO_LOG_FILE) if settings.TBO_LOG_FILE else logs_dir / "tbo_api.log",
    }


def setup_logging() -> None:
    log_paths = get_log_paths()
    console_handlers = ["console"] if settings.ENABLE_CONSOLE_LOGGING else []
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {
                    "()": "app.core.logging.RequestIdFilter",
                }
            },
            "formatters": {
                "standard": {
                    "()": "app.core.logging.SafeExtraFormatter",
                    "format": "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": settings.LOG_LEVEL,
                    "formatter": "standard",
                    "filters": ["request_id"],
                    "stream": "ext://sys.stdout",
                },
                "backend_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": settings.LOG_LEVEL,
                    "formatter": "standard",
                    "filters": ["request_id"],
                    "filename": str(log_paths["backend"]),
                    "when": "midnight",
                    "backupCount": settings.LOG_RETENTION_DAYS,
                    "encoding": "utf-8",
                },
                "internal_api_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": settings.LOG_LEVEL,
                    "formatter": "standard",
                    "filters": ["request_id"],
                    "filename": str(log_paths["internal_api"]),
                    "when": "midnight",
                    "backupCount": settings.LOG_RETENTION_DAYS,
                    "encoding": "utf-8",
                },
                "tbo_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": settings.LOG_LEVEL,
                    "formatter": "standard",
                    "filters": ["request_id"],
                    "filename": str(log_paths["tbo"]),
                    "when": "midnight",
                    "backupCount": settings.LOG_RETENTION_DAYS,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": settings.LOG_LEVEL,
                "handlers": console_handlers + ["backend_file"],
            },
            "loggers": {
                "uvicorn": {
                    "level": settings.LOG_LEVEL,
                    "handlers": console_handlers + ["backend_file"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": settings.LOG_LEVEL,
                    "handlers": console_handlers + ["backend_file"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": settings.LOG_LEVEL,
                    "handlers": console_handlers + ["backend_file"],
                    "propagate": False,
                },
                "app.internal_api": {
                    "level": settings.LOG_LEVEL,
                    "handlers": ["internal_api_file"],
                    "propagate": True,
                },
                # Logger name intentionally differs from module path
                # (app.clients.tbo_client) to route TBO logs to a dedicated file.
                "app.integrations.tbo": {
                    "level": settings.LOG_LEVEL,
                    "handlers": ["tbo_file"],
                    "propagate": True,
                },
            },
        }
    )


def _normalize_redact_fields(custom_fields: str | None) -> set[str]:
    fields = set(DEFAULT_REDACT_FIELDS)
    if custom_fields:
        fields.update(part.strip().lower() for part in custom_fields.split(",") if part.strip())
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


def truncate_for_logging(value: Any, max_chars: int | None = None) -> Any:
    limit = max_chars or settings.LOG_MAX_BODY_CHARS
    if isinstance(value, str) and len(value) > limit:
        return f"{value[:limit]}... [truncated {len(value) - limit} chars]"
    return value


def dump_for_logging(value: Any, *, max_chars: int | None = None) -> str:
    try:
        sanitized = sanitize_for_logging(value)
        rendered = json.dumps(sanitized, default=str, ensure_ascii=False)
    except Exception:
        rendered = str(value)
    return truncate_for_logging(rendered, max_chars)


def parse_body_for_logging(content_type: str | None, body: bytes) -> Any:
    if not body:
        return None

    text = body.decode("utf-8", errors="replace")
    if content_type and "application/json" in content_type.lower():
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text
