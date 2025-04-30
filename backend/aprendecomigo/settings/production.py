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

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs/django-error.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

# Google API settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Set JWT signing key
SIMPLE_JWT = {**BASE_SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}

# Import all settings from base.py
from .base import *  # noqa: F403, E402
