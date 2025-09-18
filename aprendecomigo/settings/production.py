"""
Django production settings for aprendecomigo project.
"""

import os

# Import all settings from staging (which includes base)
from .staging import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Waffle feature switches - ON by default in production
# Override with WAFFLE_DEFAULT_STATE=false to disable all new switches
WAFFLE_DEFAULT_STATE = os.getenv("WAFFLE_DEFAULT_STATE", "true")

# Stricter AWS validation - raise errors instead of warnings
if not os.getenv("AWS_ACCESS_KEY_ID") and not os.getenv("AWS_PROFILE"):
    raise ValueError("AWS_ACCESS_KEY_ID environment variable is not set (or use AWS_PROFILE for IAM roles)")
if not os.getenv("AWS_SECRET_ACCESS_KEY") and not os.getenv("AWS_PROFILE"):
    raise ValueError("AWS_SECRET_ACCESS_KEY environment variable is not set (or use AWS_PROFILE for IAM roles)")
if not os.getenv("AWS_DEFAULT_REGION"):
    raise ValueError("AWS_DEFAULT_REGION environment variable is not set")

# Production email defaults
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Aprende Comigo <noreply@aprendecomigo.com>")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", "server@aprendecomigo.com")

# SMS backend for production - inherits from staging but explicit is better
SMS_BACKEND = "messaging.services.sms_backends.SNSSMSBackend"

# Email tracking and analytics for production
ANYMAIL_SEND_DEFAULTS = {
    "tags": ["production"],
    "metadata": {
        "environment": "production",
        "application": "aprende-comigo",
    },
}

# CORS settings - strict for production
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
if not CORS_ALLOWED_ORIGINS or CORS_ALLOWED_ORIGINS == [""]:
    CORS_ALLOWED_ORIGINS = [
        "https://aprendecomigo.com",
        "https://www.aprendecomigo.com",
    ]

# Production Redis configuration - use staging base but with production-specific settings
# Override cache key prefixes and add additional caches
CACHES["default"]["KEY_PREFIX"] = "aprendecomigo_prod"
CACHES["default"]["TIMEOUT"] = 60 * 15  # 15 minutes default timeout
CACHES["default"]["LOCATION"] = f"{redis_url}/0"  # Use database 0
CACHES["default"]["OPTIONS"]["CONNECTION_POOL_KWARGS"].update(
    {
        "max_connections": 100,
        "socket_keepalive": True,
        "socket_keepalive_options": {},
    }
)

CACHES["sessions"]["KEY_PREFIX"] = "sessions_prod"
CACHES["sessions"]["LOCATION"] = f"{redis_url}/1"  # Use database 1
CACHES["sessions"]["TIMEOUT"] = 60 * 60 * 24  # 24 hours for sessions
CACHES["sessions"]["OPTIONS"]["CONNECTION_POOL_KWARGS"]["max_connections"] = 50

# Add template fragments cache for production
CACHES["template_fragments"] = {
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": f"{redis_url}/3",
    "OPTIONS": {
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
        "CONNECTION_POOL_KWARGS": RAILWAY_REDIS_CONNECTION_KWARGS.copy(),
        "PICKLE_VERSION": -1,
        "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        "IGNORE_EXCEPTIONS": False,
    },
    "KEY_PREFIX": "templates_prod",
    "TIMEOUT": 60 * 30,  # 30 minutes for template fragments
}
CACHES["template_fragments"]["OPTIONS"]["CONNECTION_POOL_KWARGS"]["max_connections"] = 50

# Production static files configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
WHITENOISE_COMPRESS_OFFLINE = True
WHITENOISE_USE_FINDERS = False
WHITENOISE_AUTOREFRESH = False

SECURE_SSL_REDIRECT = False  # Railway handles HTTPS at the edge

# Logging Configuration inherited from staging.py
# Production-specific logging overrides
LOGGING["handlers"]["console"]["level"] = "INFO"  # Example override

# Production overrides (can be overridden)
REMINDER_MOCK_MODE = False
COMMUNICATION_SERVICE_ENABLED = True
