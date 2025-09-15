"""
SMS service using configurable backends.
Simple, clean interface for sending SMS messages via different backends.
"""

import logging

from .sms_backends import get_sms_backend

logger = logging.getLogger(__name__)


# Global SMS backend instance (lazy initialization)
_sms_backend = None


def get_sms_backend_instance():
    """Get or create the SMS backend instance."""
    global _sms_backend
    if _sms_backend is None:
        _sms_backend = get_sms_backend()
    return _sms_backend


# Convenience functions for easy usage
def send_sms(to: str, message: str, from_number: str | None = None) -> dict:
    """Send a single SMS message using the configured backend."""
    backend = get_sms_backend_instance()
    return backend.send(to, message, from_number)


async def send_sms_async(to: str, message: str, from_number: str | None = None) -> dict:
    """Send a single SMS message asynchronously using the configured backend."""
    backend = get_sms_backend_instance()
    return await backend.send_async(to, message, from_number)


def send_bulk_sms(recipients: list[str], message: str, from_number: str | None = None) -> list[dict]:
    """Send SMS to multiple recipients using the configured backend."""
    backend = get_sms_backend_instance()
    return backend.send_bulk(recipients, message, from_number)


async def send_bulk_sms_async(recipients: list[str], message: str, from_number: str | None = None) -> list[dict]:
    """Send SMS to multiple recipients asynchronously using the configured backend."""
    backend = get_sms_backend_instance()
    return await backend.send_bulk_async(recipients, message, from_number)


# For backwards compatibility
def sms_service():
    """Get the SMS backend instance (backwards compatibility)."""
    return get_sms_backend_instance()
