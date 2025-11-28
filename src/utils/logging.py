"""Structured logging utility for production-grade logging."""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from src.utils.config import get_settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_logger(name: str, level: str | None = None) -> logging.Logger:
    """
    Setup logger with structured JSON formatting.

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Determine if in production environment
    try:
        is_production = get_settings().is_production
    except Exception:
        is_production = False  # Default to development if settings fail

    # Set log level
    log_level = level or ("DEBUG" if not is_production else "INFO")
    logger.setLevel(getattr(logging, log_level))

    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            JSONFormatter()
            if is_production
            else logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(handler)

    # Don't propagate to root logger
    logger.propagate = False

    return logger


def log_with_context(
    logger: logging.Logger, level: str, message: str, **context: Any
) -> None:
    """
    Log message with additional context fields.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **context: Additional context fields to include in log
    """
    log_method = getattr(logger, level.lower())

    # Create a log record with extra fields
    extra = {"extra_fields": context}
    log_method(message, extra=extra)


# Default logger for the application
logger = setup_logger(__name__)
