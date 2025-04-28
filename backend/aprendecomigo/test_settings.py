# Import all settings from the main settings file
from .settings import *

# Override settings for tests
DEBUG = False

# Disable throttling for tests
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # Keep existing settings
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {
        'anon': None,
        'user': None,
    }
}

# Use a faster password hasher
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use in-memory file storage
DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'

# Use an in-memory email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
