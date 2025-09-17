"""Test utilities for generating unique test data."""

import random
from threading import Lock

_phone_counter = 0
_phone_lock = Lock()


def get_unique_phone_number():
    """Generate a unique Portuguese phone number for testing."""
    global _phone_counter
    with _phone_lock:
        _phone_counter += 1
        # Generate unique phone numbers starting from +351900000001
        phone_suffix = str(900000000 + _phone_counter).zfill(9)
        return f"+351{phone_suffix}"


def get_unique_email(prefix="test"):
    """Generate a unique email address for testing."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}@example.com"


def get_unique_guardian_phone():
    """Generate a unique guardian phone number for testing."""
    return get_unique_phone_number()
