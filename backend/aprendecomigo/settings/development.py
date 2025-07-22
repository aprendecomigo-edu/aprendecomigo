"""
Django development settings for aprendecomigo project.
"""

import os

# Import specific settings from base
from .base import BASE_DIR
from .base import SIMPLE_JWT as BASE_SIMPLE_JWT

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY", "django-insecure-r0i5j27-gmjj&c6v@0mf5=mz$oi%e75o%iw8-i1ma6ej0m7=^q"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "TEST": {
            "NAME": BASE_DIR / "test_db.sqlite3",
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

# Disable some security settings for development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Google API settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Set JWT signing key
SIMPLE_JWT = {**BASE_SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}

# Development Logging Configuration
# Set to DEBUG level to see all log messages during development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "common": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "classroom": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


# Import all settings from base.py
from .base import *  # noqa: F403, E402

# Development-specific overrides
# Disable throttling for development/testing to avoid rate limiting during QA tests
REST_FRAMEWORK.update(
    {
        "DEFAULT_THROTTLE_CLASSES": [],  # Disable all throttling in development
        "DEFAULT_THROTTLE_RATES": {},  # Clear all throttle rates
    }
)
