# Import all settings from the main settings file

from .settings import REST_FRAMEWORK

# Override settings for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable throttling for tests
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # Keep existing settings
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "anon": None,
        "user": None,
        "email": None,
        "ip": None,
    },
}

# Use a faster password hasher
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# TODO: check use of this - use in-memory file storage
# STORAGES: dict[str, Any] = {
#     **STORAGES,
#     "default": {
#         "BACKEND": "inmemorystorage.InMemoryStorage",
#     },
# }

# Use an in-memory email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
