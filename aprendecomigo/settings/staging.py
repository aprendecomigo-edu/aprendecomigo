"""
Django staging settings for aprendecomigo project.
"""

import os
import socket
from urllib.parse import urlparse

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
ALLOWED_HOSTS = ["*"] # railway settings
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# Use PostgreSQL in production
# Railway provides DATABASE_URL automatically when PostgreSQL is provisioned
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
            'PORT': os.environ.get("PGPORT", "5432"),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
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

# Validate AWS configuration is set
if not os.getenv("AWS_ACCESS_KEY_ID") and not os.getenv("AWS_PROFILE"):
    print("WARNING: AWS_ACCESS_KEY_ID not set. Email sending will fail (unless using IAM roles).")

# Email settings
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Aprende Comigo <aprendecomigoclaude@gmail.com>")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", "aprendecomigoclaude@gmail.com")

# Email tracking and analytics (optional)
ANYMAIL_SEND_DEFAULTS = {
    "tags": ["staging"],
    # Note: SES tracking is configured via Configuration Sets, not per-message settings
    # "track_clicks" and "track_opens" are not supported at message level for SES
    "metadata": {
        "environment": "staging",
        "application": "aprende-comigo",
    },
}

# SMS Configuration - Amazon SNS
AWS_SNS_REGION = os.getenv("AWS_SNS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

# Validate SMS configuration
if not os.getenv("AWS_ACCESS_KEY_ID") and not os.getenv("AWS_PROFILE"):
    print("WARNING: AWS credentials not set. SNS SMS sending will fail.")

# CORS settings - more restrictive for staging
CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

# CSRF trusted origins for Railway deployment
railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
if railway_domain:
    CSRF_TRUSTED_ORIGINS = [f"https://{railway_domain}"]
else:
    # Fallback if not set
    CSRF_TRUSTED_ORIGINS = ["https://aprendecomigo-staging.up.railway.app"]


# Security settings for cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# HTTP Strict Transport Security
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Other security settings
# Railway handles SSL termination, so we don't need to redirect
SECURE_SSL_REDIRECT = False  # Railway handles SSL, avoid redirect loops
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Trust Railway's proxy
SECURE_REFERRER_POLICY = "same-origin"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Redis configuration for Railway staging
# Railway's internal network is IPv6-only
redis_url = os.getenv('REDIS_URL', '')

if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set")

print(f"Using Redis URL for staging: {redis_url}")

# Connection pool configuration (passed through custom connection factory)
RAILWAY_REDIS_CONNECTION_KWARGS = {
    'max_connections': 50,  # Finite pool size
    'retry_on_timeout': True,  # Retry commands on TimeoutError
}

# django-redis cache configuration with IPv6 support for Railway
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': redis_url,  # Database 0 (default)
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_FACTORY': 'aprendecomigo.redis_ipv6.RailwayIPv6ConnectionFactory',
            'CONNECTION_POOL_KWARGS': RAILWAY_REDIS_CONNECTION_KWARGS,
            'PICKLE_VERSION': -1,  # Use latest pickle protocol
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',  # Compress large values
            'IGNORE_EXCEPTIONS': True,  # Graceful degradation for cache
        },
        'KEY_PREFIX': 'aprendecomigo',
        'VERSION': 1,
        'TIMEOUT': 300,  # 5 minutes default timeout
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{redis_url}/1",  # Database 1 for sessions
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_FACTORY': 'aprendecomigo.redis_ipv6.RailwayIPv6ConnectionFactory',
            'CONNECTION_POOL_KWARGS': RAILWAY_REDIS_CONNECTION_KWARGS,
            'PICKLE_VERSION': -1,
            'IGNORE_EXCEPTIONS': False,  # Sessions are critical - fail if Redis is down
        },
        'KEY_PREFIX': 'sessions',
        'TIMEOUT': 86400,  # 24 hours for sessions
    },
    'template_fragments': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{redis_url}/2",  # Database 2 for template fragments
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_FACTORY': 'aprendecomigo.redis_ipv6.RailwayIPv6ConnectionFactory',
            'CONNECTION_POOL_KWARGS': RAILWAY_REDIS_CONNECTION_KWARGS,
            'PICKLE_VERSION': -1,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,  # Template cache can degrade gracefully
        },
        'KEY_PREFIX': 'templates',
        'TIMEOUT': 3600,  # 1 hour for template fragments
    }
}

# Use Redis for sessions with database fallback for resilience
# This provides the best of both worlds: Redis performance with database reliability
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 86400  # 24 hours


