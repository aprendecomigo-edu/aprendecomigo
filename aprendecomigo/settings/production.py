"""
Django production settings for aprendecomigo project.
"""

import os

import dj_database_url

# Import specific settings from base
from .base import BASE_DIR

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

# Email configuration - Amazon SES via django-anymail
EMAIL_BACKEND = "anymail.backends.amazon_ses.EmailBackend"

# Amazon SES configuration
ANYMAIL = {
    "AMAZON_SES_CLIENT_PARAMS": {
        "region_name": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    },
    "AMAZON_SES_CONFIGURATION_SET_NAME": os.getenv("AWS_SES_CONFIGURATION_SET_NAME"),
}

# Validate AWS configuration
if not os.getenv("AWS_ACCESS_KEY_ID") and not os.getenv("AWS_PROFILE"):
    raise ValueError("AWS_ACCESS_KEY_ID environment variable is not set (or use AWS_PROFILE for IAM roles)")
if not os.getenv("AWS_SECRET_ACCESS_KEY") and not os.getenv("AWS_PROFILE"):
    raise ValueError("AWS_SECRET_ACCESS_KEY environment variable is not set (or use AWS_PROFILE for IAM roles)")
if not os.getenv("AWS_DEFAULT_REGION"):
    raise ValueError("AWS_DEFAULT_REGION environment variable is not set")

# Email settings
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Aprende Comigo <noreply@aprendecomigo.com>")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", "server@aprendecomigo.com")

# Email tracking and analytics for production
ANYMAIL_SEND_DEFAULTS = {
    "tags": ["production"],
    # Note: SES tracking is configured via Configuration Sets, not per-message settings
    # "track_clicks" and "track_opens" are not supported at message level for SES
    "metadata": {
        "environment": "production",
        "application": "aprende-comigo",
    },
}

# SMS Configuration - Amazon SNS
AWS_SNS_REGION = os.getenv("AWS_SNS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

# CORS settings - strict for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "https://aprendecomigo.com",
        "https://www.aprendecomigo.com",
    ]

# Redis Cache Configuration for Production
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{REDIS_URL}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            },
        },
        'KEY_PREFIX': 'aprendecomigo_prod',
        'VERSION': 1,
        'TIMEOUT': 60 * 15,  # 15 minutes default timeout
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{REDIS_URL}/2",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'sessions_prod',
        'TIMEOUT': 60 * 60 * 24,  # 24 hours for sessions
    },
    'template_fragments': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{REDIS_URL}/3",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'templates_prod',
        'TIMEOUT': 60 * 30,  # 30 minutes for template fragments
    }
}

# Use Redis for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

# Database Connection Pooling is configured above in DATABASES configuration

# Static Files Configuration - WhiteNoise for Railway
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_COMPRESS_OFFLINE = True
WHITENOISE_USE_FINDERS = False
WHITENOISE_AUTOREFRESH = False

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

# Production Logging Configuration
# Optimized for production monitoring, security, and performance
LOGS_DIR = BASE_DIR.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s",
            "style": "%",
        },
        "security": {
            "format": "SECURITY {asctime} {levelname} {module} {message}",
            "style": "{",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        # Main application logs - JSON format for monitoring tools
        "application_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "application.log",
            "when": "H",  # Hourly rotation
            "interval": 1,
            "backupCount": 168,  # Keep 1 week of hourly logs
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
        # Error logs - separate file for easier monitoring
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "errors.log",
            "when": "D",
            "interval": 1,
            "backupCount": 30,
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
        # Security events - long retention for compliance
        "security_file": {
            "level": "WARNING",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "security.log",
            "when": "D",
            "interval": 1,
            "backupCount": 365,  # Keep 1 year for compliance
            "formatter": "security",
            "filters": ["correlation"],
        },
        # Business events - JSON for analytics
        "business_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "business-events.log",
            "when": "H",
            "interval": 6,  # Every 6 hours
            "backupCount": 168,  # Keep 1 month
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
        # Performance monitoring
        "performance_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "performance.log",
            "when": "H",
            "interval": 1,
            "backupCount": 72,  # Keep 3 days of hourly logs
            "formatter": "json",
            "filters": ["correlation"],
        },
        # Audit trail - financial and educational events
        "audit_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "audit-trail.log",
            "when": "D",
            "interval": 1,
            "backupCount": 2555,  # Keep 7 years for compliance
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
        # Console output for container environments
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["sensitive_data", "correlation", "rate_limit"],
        },
        # Syslog integration for monitoring systems
        "syslog": {
            "level": "WARNING",
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",  # Unix socket
            "formatter": "json",
            "filters": ["sensitive_data", "correlation"],
        },
    },
    "root": {
        "handlers": ["application_file", "console"],
        "level": "INFO",
    },
    "loggers": {
        # Django core - production levels
        "django": {
            "handlers": ["application_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file", "console", "syslog"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["performance_file"],
            "level": "WARNING",  # Log slow queries
            "propagate": False,
        },
        "django.channels": {
            "handlers": ["performance_file", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
        # Application loggers - business-focused levels
        "accounts": {
            "handlers": ["application_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts.auth": {
            "handlers": ["security_file", "audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts.security": {
            "handlers": ["security_file", "error_file", "syslog"],
            "level": "WARNING",
            "propagate": False,
        },
        "accounts.throttles": {
            "handlers": ["security_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        # Financial operations - comprehensive logging
        "finances": {
            "handlers": ["business_file", "audit_file", "application_file"],
            "level": "INFO",
            "propagate": False,
        },
        "finances.payments": {
            "handlers": ["audit_file", "business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "finances.stripe": {
            "handlers": ["audit_file", "error_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "finances.fraud": {
            "handlers": ["security_file", "audit_file", "console", "syslog"],
            "level": "WARNING",
            "propagate": False,
        },
        "finances.webhooks": {
            "handlers": ["business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Scheduling - business events
        "scheduler": {
            "handlers": ["business_file", "application_file"],
            "level": "INFO",
            "propagate": False,
        },
        "scheduler.bookings": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "scheduler.conflicts": {
            "handlers": ["business_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "scheduler.reminders": {
            "handlers": ["business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Communication
        "messaging": {
            "handlers": ["business_file", "application_file"],
            "level": "INFO",
            "propagate": False,
        },
        "messaging.email": {
            "handlers": ["business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "messaging.invitations": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Multi-tenant operations
        # Classroom operations
        "classroom": {
            "handlers": ["business_file", "application_file"],
            "level": "INFO",
            "propagate": False,
        },
        "classroom.sessions": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Business event loggers
        "business": {
            "handlers": ["business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "business.payments": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "business.sessions": {
            "handlers": ["audit_file", "business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "business.authentication": {
            "handlers": ["security_file", "audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Security loggers
        "security.events": {
            "handlers": ["security_file", "syslog"],
            "level": "WARNING",
            "propagate": False,
        },
        "security.auth_failures": {
            "handlers": ["security_file", "console", "syslog"],
            "level": "WARNING",
            "propagate": False,
        },
        # Performance monitoring
        "performance": {
            "handlers": ["performance_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Third-party - errors only
        "stripe": {
            "handlers": ["error_file", "console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
# Production overrides for reminder system
REMINDER_MOCK_MODE = False  # Disable mock mode in production
COMMUNICATION_SERVICE_ENABLED = True  # Enable real communication service in production

# Import all settings from base.py
from .base import *  # type: ignore[assignment]  # noqa: E402
