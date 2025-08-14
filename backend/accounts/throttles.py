"""
Throttling classes for accounts app security.
"""

import logging

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

logger = logging.getLogger(__name__)


class ProfileWizardThrottle(UserRateThrottle):
    """
    Custom throttle for Teacher Profile Wizard endpoints.
    Limits users to 10 requests per minute to prevent abuse.
    """

    rate = "10/min"  # 10 requests per minute
    scope = "profile_wizard"

    def throttle_failure(self):
        """Log throttling events for security monitoring."""
        user = getattr(self.request, "user", None)
        user_id = getattr(user, "id", "anonymous") if user else "anonymous"

        logger.warning(
            f"Rate limit exceeded for profile wizard. User: {user_id}, IP: {self.get_ident()}, Rate: {self.rate}"
        )

        return super().throttle_failure()


class FileUploadThrottle(UserRateThrottle):
    """
    Custom throttle for file upload endpoints.
    More restrictive rate limiting for file uploads to prevent abuse.
    """

    rate = "5/min"  # 5 file uploads per minute
    scope = "file_upload"

    def throttle_failure(self):
        """Log file upload throttling events for security monitoring."""
        user = getattr(self.request, "user", None)
        user_id = getattr(user, "id", "anonymous") if user else "anonymous"

        logger.warning(f"File upload rate limit exceeded. User: {user_id}, IP: {self.get_ident()}, Rate: {self.rate}")

        return super().throttle_failure()


class SecurityEventThrottle(UserRateThrottle):
    """
    Very restrictive throttle for endpoints that have experienced security events.
    Applied temporarily to users who have triggered security warnings.
    """

    rate = "3/min"  # 3 requests per minute
    scope = "security_event"

    def throttle_failure(self):
        """Log security-related throttling."""
        user = getattr(self.request, "user", None)
        user_id = getattr(user, "id", "anonymous") if user else "anonymous"

        logger.error(f"Security event throttle triggered. User: {user_id}, IP: {self.get_ident()}, Rate: {self.rate}")

        return super().throttle_failure()


class IPBasedThrottle(AnonRateThrottle):
    """
    IP-based throttle for public endpoints like tutor discovery.
    Rate limits requests from the same IP address to prevent abuse of public APIs.
    """

    rate = "100/hour"  # 100 requests per hour per IP
    scope = "ip_based"

    def throttle_failure(self):
        """Log IP-based throttling events for monitoring."""
        logger.warning(f"IP-based rate limit exceeded. IP: {self.get_ident()}, Rate: {self.rate}")

        return super().throttle_failure()
