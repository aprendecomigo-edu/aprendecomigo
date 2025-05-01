"""
Django staging settings for aprendecomigo project.
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
DEBUG = os.getenv("DEBUG", "False") == "True"

# Define allowed hosts
allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
if not allowed_hosts:
    raise ValueError("ALLOWED_HOSTS environment variable is not set")
ALLOWED_HOSTS = allowed_hosts.split(",")

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

email_host = os.getenv("EMAIL_HOST", "")
if not email_host:
    print("EMAIL_HOST environment variable is not set")
EMAIL_HOST = str(email_host)

EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"

email_host_user = os.getenv("EMAIL_HOST_USER")
if not email_host_user:
    print("EMAIL_HOST_USER environment variable is not set")
EMAIL_HOST_USER = str(email_host_user)

email_host_password = os.getenv("EMAIL_HOST_PASSWORD")
if not email_host_password:
    print("EMAIL_HOST_PASSWORD environment variable is not set")
EMAIL_HOST_PASSWORD = str(email_host_password)

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@aprendecomigo.com")

# CORS settings - more restrictive for staging
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

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

# Google API settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Set JWT signing key
SIMPLE_JWT = {**BASE_SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}

# Import all settings from base.py
from .base import *  # noqa: F403, E402
