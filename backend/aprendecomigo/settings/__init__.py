"""
Initialize the settings module.
Determines which settings file to use based on the DJANGO_SETTINGS_MODULE environment variable.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

# Default to development settings
environment = os.getenv("DJANGO_ENV", "development")

if environment == "production":
    # Import all other production settings
    from .production import *  # type: ignore[assignment]
    from .production import ALLOWED_HOSTS, DATABASES, DEBUG, SECRET_KEY  # type: ignore[assignment]
elif environment == "staging":
    # Import all other staging settings
    from .staging import *  # type: ignore[assignment]
    from .staging import ALLOWED_HOSTS, DATABASES, DEBUG, SECRET_KEY  # type: ignore[assignment]
elif environment == "testing":
    # Import all other testing settings
    from .testing import *  # type: ignore[assignment]
    from .testing import DATABASES, DEBUG, SECRET_KEY  # type: ignore[assignment]
else:
    # Import all other development settings
    from .development import *  # type: ignore[assignment]
    from .development import (  # type: ignore[assignment]  # noqa: F401
        ALLOWED_HOSTS,
        DATABASES,
        DEBUG,
        SECRET_KEY,
    )
