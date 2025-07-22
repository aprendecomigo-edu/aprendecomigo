"""
Django test settings for aprendecomigo project.
"""

# Import specific settings from base
from .base import (
    BASE_DIR,
)
from .base import (
    REST_FRAMEWORK as BASE_REST_FRAMEWORK,
)
from .base import (
    SIMPLE_JWT as BASE_SIMPLE_JWT,
)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-test-key-not-used-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # String to boolean conversion for mypy

# Override settings for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

# Set JWT signing key
SIMPLE_JWT = {**BASE_SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}

# Disable throttling during tests
REST_FRAMEWORK = {
    **BASE_REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
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
    }
}

# Use an in-memory email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


# Import all settings from base.py
from .base import *  # noqa: F403, E402
