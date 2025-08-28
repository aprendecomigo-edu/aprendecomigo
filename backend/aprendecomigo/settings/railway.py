"""
Railway-specific settings for Django Channels deployment
"""
import os
from .production import *  # noqa: F403, F401

# Channel Layers Configuration for Railway
# Railway provides REDIS_URL automatically when you add Redis service
redis_url = os.getenv("REDIS_URL") or os.getenv("CHANNEL_LAYERS_REDIS_URL")

if redis_url:
    # Parse Redis URL for Django Channels
    import urllib.parse
    parsed = urllib.parse.urlparse(redis_url)
    
    CHANNEL_LAYERS = {  # noqa: F405
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [(parsed.hostname or "localhost", parsed.port or 6379)],
                "password": parsed.password,
            },
        },
    }
else:
    # Fallback to localhost for development
    CHANNEL_LAYERS = {  # noqa: F405
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [("127.0.0.1", 6379)],
            },
        },
    }

# Railway-specific ALLOWED_HOSTS
# Railway provides automatic domain: *.up.railway.app
railway_domain = os.getenv("RAILWAY_STATIC_URL", "")
if railway_domain:
    ALLOWED_HOSTS.append(railway_domain.replace("https://", "").replace("http://", ""))  # noqa: F405

# Static files configuration for Railway
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Ensure WhiteNoise is in middleware
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405