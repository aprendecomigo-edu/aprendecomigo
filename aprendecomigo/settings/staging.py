"""
Django staging settings for aprendecomigo project.
"""

import os

import dj_database_url

# Import all settings from base.py
from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise ValueError("SECRET_KEY environment variable is not set")
SECRET_KEY = str(secret_key)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True") == "True"  # Railway docs recommend DEBUG=True for staging

# Define allowed hosts
allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
if not allowed_hosts:
    raise ValueError("ALLOWED_HOSTS environment variable is not set")
ALLOWED_HOSTS = allowed_hosts.split(",")
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# Use PostgreSQL in production
# Railway provides DATABASE_URL automatically when PostgreSQL is provisioned
# Falls back to individual PG* variables if DATABASE_URL is not set
if os.environ.get("DATABASE_URL"):
    DATABASES = {
        'default': dj_database_url.parse(
            os.environ["DATABASE_URL"],
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ["PGDATABASE"],
            'USER': os.environ["PGUSER"],
            'PASSWORD': os.environ["PGPASSWORD"],
            'HOST': os.environ["PGHOST"],
            'PORT': os.environ["PGPORT"],
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
                'MAX_CONNS': 20,
            }
        }
    }

# Email configuration - Mailgun via django-anymail
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

# Mailgun configuration
ANYMAIL = {
    "MAILGUN_API_KEY": os.getenv("MAILGUN_API_KEY", ""),
    "MAILGUN_SENDER_DOMAIN": os.getenv("MAILGUN_SENDER_DOMAIN", "sandbox4b37e78e50fa4f0bba82524e148f5738.mailgun.org"),
    # For sandbox domains, you need to add authorized recipients in Mailgun dashboard
    "MAILGUN_API_URL": os.getenv("MAILGUN_API_URL", "https://api.mailgun.net/v3"),  # Use api.eu.mailgun.net for EU
}

# Validate Mailgun API key is set
if not ANYMAIL["MAILGUN_API_KEY"]:
    print("WARNING: MAILGUN_API_KEY not set. Email sending will fail.")

# Email settings
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Aprende Comigo <noreply@sandbox4b37e78e50fa4f0bba82524e148f5738.mailgun.org>")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", "server@sandbox4b37e78e50fa4f0bba82524e148f5738.mailgun.org")

# Email tracking and analytics (optional)
ANYMAIL_SEND_DEFAULTS = {
    "tags": ["staging"],
    "track_clicks": True,
    "track_opens": True,
}

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


