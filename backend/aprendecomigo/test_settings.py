# Import all settings from the main settings file
from .settings import REST_FRAMEWORK as BASE_REST_FRAMEWORK

# Override settings for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable throttling for tests
REST_FRAMEWORK = {
    **BASE_REST_FRAMEWORK,  # Keep existing settings
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "anon": None,
        "user": None,
    },
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
