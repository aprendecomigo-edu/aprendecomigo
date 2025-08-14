"""
Advanced logging utilities for Aprende Comigo platform.

This module provides custom formatters, filters, and handlers to support
comprehensive logging for a multi-tenant tutoring platform with enhanced
security, performance monitoring, and business event tracking.
"""

from datetime import datetime
import json
import logging
import re
import threading
import time
from typing import Any, ClassVar
import uuid

# Thread-local storage for correlation IDs
_local = threading.local()


class CorrelationID:
    """Manages correlation IDs for request tracking."""

    @classmethod
    def generate(cls) -> str:
        """Generate a new correlation ID."""
        return f"req_{uuid.uuid4().hex[:12]}"

    @classmethod
    def set(cls, correlation_id: str) -> None:
        """Set correlation ID for current thread."""
        _local.correlation_id = correlation_id

    @classmethod
    def get(cls) -> str | None:
        """Get correlation ID for current thread."""
        return getattr(_local, "correlation_id", None)

    @classmethod
    def clear(cls) -> None:
        """Clear correlation ID for current thread."""
        if hasattr(_local, "correlation_id"):
            delattr(_local, "correlation_id")


class BusinessContext:
    """Manages business context for logging."""

    @classmethod
    def set_context(cls, school_id: int | None = None, user_id: int | None = None, role: str | None = None) -> None:
        """Set business context for current thread."""
        _local.school_id = school_id
        _local.user_id = user_id
        _local.role = role

    @classmethod
    def get_context(cls) -> dict[str, Any | None]:
        """Get business context for current thread."""
        return {
            "school_id": getattr(_local, "school_id", None),
            "user_id": getattr(_local, "user_id", None),
            "role": getattr(_local, "role", None),
        }

    @classmethod
    def clear(cls) -> None:
        """Clear business context for current thread."""
        for attr in ["school_id", "user_id", "role"]:
            if hasattr(_local, attr):
                delattr(_local, attr)


class SensitiveDataFilter(logging.Filter):
    """Filter to remove or redact sensitive information from log records."""

    # Patterns for sensitive data detection
    PATTERNS: ClassVar = {
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "phone": re.compile(r"\b\+?[\d\s\-\(\)]{10,15}\b"),
        "card_number": re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
        "token": re.compile(r"\b[A-Za-z0-9]{20,}\b"),  # Generic token pattern
        "password": re.compile(r'(?i)(password|passwd|pwd)["\'\s]*[:=]["\'\s]*[^\s"\']+'),
        "api_key": re.compile(r'(?i)(api_key|apikey|secret_key)["\'\s]*[:=]["\'\s]*[^\s"\']+'),
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact sensitive data from log record."""
        # Redact sensitive data from message
        if hasattr(record, "getMessage"):
            message = record.getMessage()
            for pattern_name, pattern in self.PATTERNS.items():
                if pattern_name == "email":
                    # Keep domain for debugging, redact username
                    message = pattern.sub(lambda m: f"***@{m.group().split('@')[1]}", message)
                elif pattern_name == "card_number":
                    # Keep last 4 digits
                    message = pattern.sub(lambda m: f"****-****-****-{m.group()[-4:]}", message)
                else:
                    message = pattern.sub("[REDACTED]", message)

            # Update the record's args to reflect redacted message
            record.args = ()
            record.msg = message

        return True


class CorrelationFilter(logging.Filter):
    """Filter to add correlation ID and business context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID and business context to log record."""
        # Add correlation ID
        record.correlation_id = CorrelationID.get() or "no-correlation-id"

        # Add business context
        context = BusinessContext.get_context()
        record.school_id = context.get("school_id")
        record.user_id = context.get("user_id")
        record.role = context.get("role")

        # Add timestamp for JSON formatting
        record.timestamp_iso = datetime.utcnow().isoformat() + "Z"

        return True


class RateLimitFilter(logging.Filter):
    """Filter to prevent log spam from repeated identical messages."""

    def __init__(self, rate_limit_seconds: int = 60):
        super().__init__()
        self.rate_limit_seconds = rate_limit_seconds
        self.message_timestamps: dict[str, float] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply rate limiting to repeated messages."""
        message_key = f"{record.levelno}:{record.msg}"
        current_time = time.time()

        # Check if we've seen this message recently
        if message_key in self.message_timestamps:
            time_diff = current_time - self.message_timestamps[message_key]
            if time_diff < self.rate_limit_seconds:
                return False  # Suppress this log entry

        # Update timestamp for this message
        self.message_timestamps[message_key] = current_time

        # Clean up old entries to prevent memory growth
        cutoff_time = current_time - self.rate_limit_seconds * 2
        self.message_timestamps = {
            key: timestamp for key, timestamp in self.message_timestamps.items() if timestamp > cutoff_time
        }

        return True


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log structure
        log_entry = {
            "timestamp": getattr(record, "timestamp_iso", datetime.utcnow().isoformat() + "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id

        # Add business context if available
        if hasattr(record, "school_id") and record.school_id:
            log_entry["school_id"] = record.school_id
        if hasattr(record, "user_id") and record.user_id:
            log_entry["user_id"] = record.user_id
        if hasattr(record, "role") and record.role:
            log_entry["role"] = record.role

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields that were passed to the logger
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "correlation_id",
                "school_id",
                "user_id",
                "role",
                "timestamp_iso",
            }:
                extra_fields[key] = value

        if extra_fields:
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class DevelopmentFormatter(logging.Formatter):
    """Human-readable formatter for development with colors."""

    # ANSI color codes
    COLORS: ClassVar = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for development."""
        # Add color to level name
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]

        # Format correlation ID if available
        correlation_info = ""
        if hasattr(record, "correlation_id") and record.correlation_id != "no-correlation-id":
            correlation_info = f"[{record.correlation_id}] "

        # Format business context if available
        business_context = ""
        if hasattr(record, "school_id") and record.school_id:
            business_context += f"school:{record.school_id} "
        if hasattr(record, "user_id") and record.user_id:
            business_context += f"user:{record.user_id} "
        if hasattr(record, "role") and record.role:
            business_context += f"role:{record.role} "

        if business_context:
            business_context = f"({business_context.strip()}) "

        # Create formatted message
        formatted = (
            f"{color}{record.levelname:<8}{reset} "
            f"{record.asctime} "
            f"{correlation_info}"
            f"{business_context}"
            f"{record.name}:{record.lineno} "
            f"- {record.getMessage()}"
        )

        # Add exception information if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


class SecurityFormatter(logging.Formatter):
    """Enhanced formatter for security-related events."""

    def format(self, record: logging.LogRecord) -> str:
        """Format security log record with enhanced context."""
        # Base security log structure
        security_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "security_level": record.levelname,
            "event_type": getattr(record, "event_type", "general"),
            "source_ip": getattr(record, "source_ip", None),
            "user_agent": getattr(record, "user_agent", None),
            "correlation_id": getattr(record, "correlation_id", None),
            "school_id": getattr(record, "school_id", None),
            "user_id": getattr(record, "user_id", None),
            "message": record.getMessage(),
            "module": f"{record.module}:{record.lineno}",
        }

        # Add any additional security context
        if hasattr(record, "security_context"):
            security_entry["security_context"] = record.security_context

        return json.dumps(security_entry, default=str, ensure_ascii=False)


def setup_logging_context_middleware():
    """Create middleware to inject logging context from HTTP requests."""

    class LoggingContextMiddleware:
        """Middleware to inject correlation IDs and business context into logs."""

        def __init__(self, get_response):
            self.get_response = get_response

        def __call__(self, request):
            # Generate or extract correlation ID
            correlation_id = request.headers.get("X-Correlation-ID") or CorrelationID.generate()
            CorrelationID.set(correlation_id)

            # Set business context if user is authenticated
            if hasattr(request, "user") and request.user.is_authenticated:
                # Extract business context from user
                user_id = request.user.id
                role = None
                school_id = None

                # Try to get role and school context
                if hasattr(request, "school") and request.school:
                    school_id = request.school.id

                if hasattr(request.user, "get_role_for_school"):
                    try:
                        role = request.user.get_role_for_school(school_id)
                    except Exception:
                        role = "unknown"

                BusinessContext.set_context(school_id=school_id, user_id=user_id, role=role)

            try:
                # Add correlation ID to response headers
                response = self.get_response(request)
                response["X-Correlation-ID"] = correlation_id
                return response
            finally:
                # Clean up thread-local data
                CorrelationID.clear()
                BusinessContext.clear()

    return LoggingContextMiddleware


def get_business_event_logger(event_type: str) -> logging.Logger:
    """Get a logger configured for specific business events."""
    logger_name = f"business.{event_type}"
    return logging.getLogger(logger_name)


def log_security_event(event_type: str, message: str, **kwargs):
    """Log a security event with enhanced context."""
    logger = logging.getLogger("security.events")

    # Create log record with security context
    extra = {"event_type": event_type, "security_context": kwargs}

    # Add request context if available
    # This would typically come from middleware or view context

    logger.warning(message, extra=extra)


def log_business_event(event_type: str, message: str, **metadata):
    """Log a business event with metadata."""
    logger = get_business_event_logger(event_type)

    extra = {"event_type": event_type, "business_metadata": metadata}

    logger.info(message, extra=extra)


def log_performance_event(operation: str, duration_ms: float, **metadata):
    """Log a performance event."""
    logger = logging.getLogger("performance")

    extra = {"operation": operation, "duration_ms": duration_ms, "performance_metadata": metadata}

    # Log as warning if operation is slow
    level = logging.WARNING if duration_ms > 1000 else logging.INFO
    logger.log(level, f"Operation '{operation}' took {duration_ms:.2f}ms", extra=extra)
