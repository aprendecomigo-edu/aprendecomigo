"""
Django production settings for aprendecomigo project.
"""

import os

# Import specific settings from base
from .base import BASE_DIR
from .base import SIMPLE_JWT as BASE_SIMPLE_JWT

# SECURITY WARNING: keep the secret key used in production secret!
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise ValueError("SECRET_KEY environment variable is not set")
SECRET_KEY = str(secret_key)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Define allowed hosts
allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
if not allowed_hosts:
    raise ValueError("ALLOWED_HOSTS environment variable is not set")
ALLOWED_HOSTS = allowed_hosts.split(",")

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# Use PostgreSQL in production
if os.getenv("DATABASE_URL"):
    import dj_database_url  # type: ignore

    DATABASES = {"default": dj_database_url.config(default=os.getenv("DATABASE_URL"))}
else:
    raise ValueError("DATABASE_URL environment variable is not set")

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

email_host = os.getenv("EMAIL_HOST")
if not email_host:
    raise ValueError("EMAIL_HOST environment variable is not set")
EMAIL_HOST = str(email_host)

EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"

email_host_user = os.getenv("EMAIL_HOST_USER")
if not email_host_user:
    raise ValueError("EMAIL_HOST_USER environment variable is not set")
EMAIL_HOST_USER = str(email_host_user)

email_host_password = os.getenv("EMAIL_HOST_PASSWORD")
if not email_host_password:
    raise ValueError("EMAIL_HOST_PASSWORD environment variable is not set")
EMAIL_HOST_PASSWORD = str(email_host_password)

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@aprendecomigo.com")

# CORS settings - strict for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "https://aprendecomigo.com",
        "https://www.aprendecomigo.com",
    ]

# Security settings for cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# HTTP Strict Transport Security
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Other security settings
SECURE_SSL_REDIRECT = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Production Logging Configuration
# Optimized for production monitoring, security, and performance
LOGS_DIR = BASE_DIR.parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "common.logging_utils.JSONFormatter",
        },
        "security": {
            "()": "common.logging_utils.SecurityFormatter",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "filters": {
        "sensitive_data": {
            "()": "common.logging_utils.SensitiveDataFilter",
        },
        "correlation": {
            "()": "common.logging_utils.CorrelationFilter",
        },
        "rate_limit": {
            "()": "common.logging_utils.RateLimitFilter",
            "rate_limit_seconds": 30,  # Faster rate limiting in production
        },
    },
    "handlers": {
        # Main application logs - JSON format for monitoring tools
        "application_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "application.log",
            "when": "H",  # Hourly rotation
            "interval": 1,
            "backupCount": 168,  # Keep 1 week of hourly logs
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
        
        # Error logs - separate file for easier monitoring
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "errors.log",
            "when": "D",
            "interval": 1,
            "backupCount": 30,
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
        
        # Security events - long retention for compliance
        "security_file": {
            "level": "WARNING",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "security.log",
            "when": "D",
            "interval": 1,
            "backupCount": 365,  # Keep 1 year for compliance
            "formatter": "security",
            "filters": ["correlation"],
        },
        
        # Business events - JSON for analytics
        "business_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "business-events.log",
            "when": "H",
            "interval": 6,  # Every 6 hours
            "backupCount": 168,  # Keep 1 month
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
        
        # Performance monitoring
        "performance_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "performance.log",
            "when": "H",
            "interval": 1,
            "backupCount": 72,  # Keep 3 days of hourly logs
            "formatter": "json",
            "filters": ["correlation"],
        },
        
        # Audit trail - financial and educational events
        "audit_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "audit-trail.log",
            "when": "D",
            "interval": 1,
            "backupCount": 2555,  # Keep 7 years for compliance
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
        
        # Console output for container environments
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["sensitive_data", "correlation", "rate_limit"],
        },
        
        # Syslog integration for monitoring systems
        "syslog": {
            "level": "WARNING",
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",  # Unix socket
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
    },
    "root": {
        "handlers": ["application_file", "console"],
        "level": "INFO",
    },
    "loggers": {
        # Django core - production levels
        "django": {
            "handlers": ["application_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file", "console", "syslog"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["performance_file"],
            "level": "WARNING",  # Log slow queries
            "propagate": False,
        },
        "django.channels": {
            "handlers": ["performance_file", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
        
        # Application loggers - business-focused levels
        "accounts": {
            "handlers": ["application_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts.auth": {
            "handlers": ["security_file", "audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts.security": {
            "handlers": ["security_file", "error_file", "syslog"],
            "level": "WARNING",
            "propagate": False,
        },
        "accounts.throttles": {
            "handlers": ["security_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        
        # Financial operations - comprehensive logging
        "finances": {
            "handlers": ["business_file", "audit_file", "application_file"],
            "level": "INFO",
            "propagate": False,
        },
        "finances.payments": {
            "handlers": ["audit_file", "business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "finances.stripe": {
            "handlers": ["audit_file", "error_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "finances.fraud": {
            "handlers": ["security_file", "audit_file", "console", "syslog"],
            "level": "WARNING",
            "propagate": False,
        },
        "finances.webhooks": {
            "handlers": ["business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        
        # Scheduling - business events
        "scheduler": {
            "handlers": ["business_file", "application_file"],
            "level": "INFO",
            "propagate": False,
        },
        "scheduler.bookings": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "scheduler.conflicts": {
            "handlers": ["business_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "scheduler.reminders": {
            "handlers": ["business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        
        # Communication
        "messaging": {
            "handlers": ["business_file", "application_file"],
            "level": "INFO",
            "propagate": False,
        },
        "messaging.email": {
            "handlers": ["business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "messaging.invitations": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        
        # Multi-tenant operations
        "common.permissions": {
            "handlers": ["security_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        
        # Classroom operations
        "classroom": {
            "handlers": ["business_file", "application_file"],
            "level": "INFO",
            "propagate": False,
        },
        "classroom.sessions": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        
        # Business event loggers
        "business": {
            "handlers": ["business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "business.payments": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "business.sessions": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "business.authentication": {
            "handlers": ["security_file", "audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        
        # Security loggers
        "security.events": {
            "handlers": ["security_file", "syslog"],
            "level": "WARNING",
            "propagate": False,
        },
        "security.auth_failures": {
            "handlers": ["security_file", "console", "syslog"],
            "level": "WARNING",
            "propagate": False,
        },
        
        # Performance monitoring
        "performance": {
            "handlers": ["performance_file"],
            "level": "INFO",
            "propagate": False,
        },
        
        # Third-party - errors only
        "stripe": {
            "handlers": ["error_file", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "knox": {
            "handlers": ["security_file", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Google API settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Set JWT signing key
SIMPLE_JWT = {**BASE_SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}

# Production overrides for reminder system
REMINDER_MOCK_MODE = False  # Disable mock mode in production
COMMUNICATION_SERVICE_ENABLED = True  # Enable real communication service in production

# Import all settings from base.py
from .base import *  # noqa: F403, E402
