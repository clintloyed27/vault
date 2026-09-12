import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class SafeJsonFormatter(logging.Formatter):
    """
    Format logs as JSON. Masks sensitive fields like passwords, tokens, and authorization headers.
    """
    SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "secret", "authorization"}

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra attributes
        for key, val in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "message"
            }:
                if any(s in key.lower() for s in self.SENSITIVE_KEYS):
                    log_obj[key] = "[REDACTED]"
                else:
                    log_obj[key] = val

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("vault")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(SafeJsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging()
