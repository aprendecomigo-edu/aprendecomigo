from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Maximum allowed upload size for chat attachments: 5 MB
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


def validate_file_size(value) -> None:
    """Ensure uploaded files do not exceed ``MAX_UPLOAD_SIZE`` bytes."""
    if value.size > MAX_UPLOAD_SIZE:
        raise ValidationError(
            _(f"File size exceeds {MAX_UPLOAD_SIZE // (1024 * 1024)} MB limit.")
        )
