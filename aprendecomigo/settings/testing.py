"""
Django test settings for aprendecomigo project.
"""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-test-key-not-used-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # String to boolean conversion for mypy

# Testing flag to skip rate limiting and other production-only security measures
TESTING = True

# Override settings for tests - Use in-memory database for fastest execution
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Use a faster session backend
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Use a faster cache backend
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Use a faster storage backend
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Use an in-memory email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Silence Swagger warnings in tests
SWAGGER_USE_COMPAT_RENDERERS = False


# Import all settings from base.py
from .base import *  # type: ignore[assignment]  # noqa: E402

# Allow testserver for Django test client
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# Stripe Test Configuration - Use realistic test key formats
STRIPE_SECRET_KEY = "sk_test_51234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
STRIPE_PUBLIC_KEY = "pk_test_51234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
STRIPE_WEBHOOK_SECRET = "whsec_1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"

# Testing Logging Configuration
# Optimized for test execution with minimal I/O and noise reduction
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "test_detailed": {
            "format": "{levelname} {asctime} {name}:{lineno} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        # Console handler with higher threshold to reduce test noise
        "console": {
            "level": "WARNING",  # Only warnings and errors in tests
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        # Memory handler for capturing logs during tests
        "memory": {
            "level": "DEBUG",
            "class": "logging.handlers.MemoryHandler",
            "capacity": 1000,
            "target": "console",
            "formatter": "test_detailed",
        },
        # Null handler to discard logs entirely
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        # Django core - minimal logging during tests
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["null"],  # Discard request logs during tests
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["null"],  # Discard database logs during tests
            "level": "ERROR",
            "propagate": False,
        },
        "django.channels": {
            "handlers": ["null"],
            "level": "ERROR",
            "propagate": False,
        },
        # Application loggers - reduced levels for testing
        "accounts": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "accounts.auth": {
            "handlers": ["memory"],  # Capture auth events for test verification
            "level": "INFO",
            "propagate": False,
        },
        "accounts.security": {
            "handlers": ["memory"],  # Capture security events for test verification
            "level": "WARNING",
            "propagate": False,
        },
        "finances": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "finances.payments": {
            "handlers": ["memory"],  # Capture payment events for test verification
            "level": "INFO",
            "propagate": False,
        },
        "finances.stripe": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "finances.fraud": {
            "handlers": ["memory"],  # Capture fraud events for test verification
            "level": "WARNING",
            "propagate": False,
        },
        "scheduler": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "scheduler.bookings": {
            "handlers": ["memory"],  # Capture booking events for test verification
            "level": "INFO",
            "propagate": False,
        },
        "scheduler.conflicts": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "messaging": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "messaging.email": {
            "handlers": ["memory"],  # Capture email events for test verification
            "level": "INFO",
            "propagate": False,
        },
        "common.permissions": {
            "handlers": ["memory"],  # Capture permission events for test verification
            "level": "WARNING",
            "propagate": False,
        },
        "classroom": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "tasks": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # Business event loggers - memory handlers for test verification
        "business": {
            "handlers": ["memory"],
            "level": "INFO",
            "propagate": False,
        },
        "business.payments": {
            "handlers": ["memory"],
            "level": "INFO",
            "propagate": False,
        },
        "business.sessions": {
            "handlers": ["memory"],
            "level": "INFO",
            "propagate": False,
        },
        "business.authentication": {
            "handlers": ["memory"],
            "level": "INFO",
            "propagate": False,
        },
        # Security event loggers
        "security.events": {
            "handlers": ["memory"],
            "level": "WARNING",
            "propagate": False,
        },
        "security.auth_failures": {
            "handlers": ["memory"],
            "level": "WARNING",
            "propagate": False,
        },
        "security.websocket": {
            "handlers": ["memory"],
            "level": "WARNING",
            "propagate": False,
        },
        # Performance - disabled during tests
        "performance": {
            "handlers": ["null"],
            "level": "ERROR",
            "propagate": False,
        },
        # Third-party - errors only
        "stripe": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
