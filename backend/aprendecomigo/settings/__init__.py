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
    from .production import *  # noqa: F403
    from .production import ALLOWED_HOSTS, DATABASES, DEBUG, SECRET_KEY, SIMPLE_JWT
elif environment == "staging":
    # Import all other staging settings
    from .staging import *  # noqa: F403
    from .staging import ALLOWED_HOSTS, DATABASES, DEBUG, SECRET_KEY, SIMPLE_JWT
elif environment == "testing":
    # Import all other testing settings
    from .testing import *  # noqa: F403
    from .testing import DATABASES, DEBUG, SECRET_KEY, SIMPLE_JWT
else:
    # Import all other development settings
    from .development import *  # noqa: F403
    from .development import ALLOWED_HOSTS, DATABASES, DEBUG, SECRET_KEY, SIMPLE_JWT  # noqa: F401
