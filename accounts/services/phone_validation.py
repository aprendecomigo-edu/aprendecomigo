"""
Phone number validation and normalization service.
Handles international phone number validation with E.164 format.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PhoneValidationService:
    """Service for validating and normalizing phone numbers"""

    # Basic E.164 format validation
    E164_PATTERN = re.compile(r"^\+[1-9]\d{1,14}$")

    # Common country codes and their basic patterns
    COUNTRY_PATTERNS = {
        "US": re.compile(r"^\+1[2-9]\d{2}[2-9]\d{2}\d{4}$"),
        "UK": re.compile(r"^\+44[1-9]\d{8,9}$"),
        "PT": re.compile(r"^\+351[1-9]\d{8}$"),
        "BR": re.compile(r"^\+55[1-9]\d{9,10}$"),
        "ES": re.compile(r"^\+34[6-9]\d{8}$"),
    }

    @classmethod
    def validate_and_normalize(cls, phone_number):
        """Validate and normalize phone number to E.164 format"""
        if not phone_number:
            raise ValidationError(_("Phone number is required"))

        # Clean the input
        cleaned = cls._clean_phone_number(phone_number)

        # Add country code if missing (assume based on common patterns)
        normalized = cls._add_country_code(cleaned)

        # Validate E.164 format
        if not cls.E164_PATTERN.match(normalized):
            raise ValidationError(_("Please enter a valid phone number with country code (e.g., +1234567890)"))

        return normalized

    @classmethod
    def _clean_phone_number(cls, phone_number):
        """Remove all non-digit characters except +"""
        cleaned = re.sub(r"[^\d+]", "", phone_number.strip())

        # Handle common formatting issues
        if cleaned.startswith("00"):
            cleaned = "+" + cleaned[2:]  # Convert 00 prefix to +
        elif cleaned.startswith("0") and not cleaned.startswith("+"):
            # Remove leading 0 for national numbers
            cleaned = cleaned[1:]

        return cleaned

    @classmethod
    def _add_country_code(cls, phone_number):
        """Add country code if missing based on common patterns"""
        if phone_number.startswith("+"):
            return phone_number

        # More permissive US/Canada detection
        if len(phone_number) == 10 and phone_number[0] in "2-9":
            return "+1" + phone_number  # US/Canada 10-digit
        elif len(phone_number) == 11 and phone_number.startswith("1"):
            return "+" + phone_number  # US/Canada with 1 prefix
        # Portugal mobile patterns (main use case)
        elif len(phone_number) == 9 and phone_number.startswith("9"):
            return "+351" + phone_number  # Portugal mobile
        elif len(phone_number) == 12 and phone_number.startswith("351"):
            return "+" + phone_number  # Portugal with country code
        # Spain mobile patterns
        elif len(phone_number) == 9 and phone_number.startswith("6"):
            return "+34" + phone_number  # Spain mobile

        # More permissive fallback - allow if looks like valid number
        elif len(phone_number) >= 8 and phone_number.isdigit():
            # For MVP, accept and let user specify if needed
            raise ValidationError(_("Please include your country code (e.g., +1 for US, +351 for Portugal)"))

        raise ValidationError(_("Invalid phone number format"))

    @classmethod
    def format_for_display(cls, phone_number):
        """Format phone number for user-friendly display"""
        if not phone_number or not phone_number.startswith("+"):
            return phone_number

        # US/Canada formatting
        if phone_number.startswith("+1") and len(phone_number) == 12:
            return f"+1 ({phone_number[2:5]}) {phone_number[5:8]}-{phone_number[8:]}"

        # Generic international formatting
        if len(phone_number) > 8:
            return phone_number  # Keep as-is for international numbers

        return phone_number


def phone_number_validator(value):
    """Django validator for phone number fields"""
    PhoneValidationService.validate_and_normalize(value)
