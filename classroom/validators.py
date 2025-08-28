"""
File validators for classroom app.
"""

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_file_size(value):
    """
    Validate that uploaded file size doesn't exceed maximum allowed size.
    Default maximum size is 10MB.
    """
    max_size = getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)  # 10MB

    if value.size > max_size:
        raise ValidationError(f"File too large. Size should not exceed {max_size // (1024 * 1024)}MB.")
