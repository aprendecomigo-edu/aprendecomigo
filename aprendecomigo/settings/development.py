"""
Django development settings for aprendecomigo project.
"""

import os

# Import specific settings from base
from .base import BASE_DIR

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-r0i5j27-gmjj&c6v@0mf5=mz$oi%e75o%iw8-i1ma6ej0m7=^q")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Will be overridden after base import

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "TEST": {
            "NAME": ":memory:",  # Use in-memory database for faster dev tests
        },
    }
}

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@aprendecomigo.com"

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:19006",  # Expo web port
]

# Will override cache settings after base import

# Disable some security settings for development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Allow CSRF tokens from iPhone/external IPs
CSRF_TRUSTED_ORIGINS = [
    "http://192.168.1.98:8000",
    "http://10.1.14.101:8000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Google API settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")


# Development Logging Configuration
# Optimized for development with enhanced visibility and debugging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "development": {
            "format": "{asctime} {name} {levelname} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "json": {
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s",
            "style": "%",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "development",
        },
        # Optional file handler for debugging specific issues
        "debug_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": BASE_DIR.parent / "logs" / "development-debug.log",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        # Django core - reduced verbosity for development
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "ERROR",  # Only show database errors in development
            "propagate": False,
        },
        # Application loggers - DEBUG level for development
        "accounts": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "accounts.auth": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "accounts.security": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "finances": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "finances.payments": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "finances.stripe": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "scheduler": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "scheduler.bookings": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "scheduler.conflicts": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "messaging": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "messaging.email": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "common.permissions": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "classroom": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "tasks": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        # Business and security events - visible in development
        "business": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "security.events": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "performance": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Third-party - reduced noise
        "stripe": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# Import all settings from base.py
from .base import *  # noqa: E402

# Override cache to use local memory instead of Redis (must be after base import)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "default-cache",
        "TIMEOUT": 60 * 15,
    },
    "sessions": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "sessions-cache",
        "TIMEOUT": 60 * 60 * 24,
    },
}

# Override session backend to use database for reliable persistence in development
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Development-specific overrides
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "192.168.1.98", "192.168.1.98:8000", "10.1.14.101", "10.1.14.101:8000", "*"]

# Override security settings for development (ensure these override base)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Session cookies settings for iPhone Safari cross-origin access
SESSION_COOKIE_SAMESITE = None  # Allow cross-origin cookies for development
SESSION_COOKIE_HTTPONLY = False  # Allow JavaScript access for debugging
SESSION_SAVE_EVERY_REQUEST = True  # Force session save on every request

CSRF_TRUSTED_ORIGINS = [
    "http://192.168.1.98:8000",
    "http://10.1.14.101:8000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
