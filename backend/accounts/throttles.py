"""
Throttling classes for accounts app security.
"""

import logging
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

logger = logging.getLogger(__name__)


class ProfileWizardThrottle(UserRateThrottle):
    """
    Custom throttle for Teacher Profile Wizard endpoints.
    Limits users to 10 requests per minute to prevent abuse.
    """
    
    rate = '10/min'  # 10 requests per minute
    scope = 'profile_wizard'
    
    def throttle_failure(self):
        """Log throttling events for security monitoring."""
        request = getattr(self, 'request', None)
        user = getattr(request, 'user', None) if request else None
        user_id = getattr(user, 'id', 'anonymous') if user else 'anonymous'
        ip = self.get_ident(request) if request else 'unknown'
        
        logger.warning(
            f"Rate limit exceeded for profile wizard. "
            f"User: {user_id}, IP: {ip}, "
            f"Rate: {self.rate}"
        )
        
        return super().throttle_failure()


class FileUploadThrottle(UserRateThrottle):
    """
    Custom throttle for file upload endpoints.
    More restrictive rate limiting for file uploads to prevent abuse.
    """
    
    rate = '5/min'  # 5 file uploads per minute
    scope = 'file_upload'
    
    def throttle_failure(self):
        """Log file upload throttling events for security monitoring."""
        request = getattr(self, 'request', None)
        user = getattr(request, 'user', None) if request else None
        user_id = getattr(user, 'id', 'anonymous') if user else 'anonymous'
        ip = self.get_ident(request) if request else 'unknown'
        
        logger.warning(
            f"File upload rate limit exceeded. "
            f"User: {user_id}, IP: {ip}, "
            f"Rate: {self.rate}"
        )
        
        return super().throttle_failure()


class SecurityEventThrottle(UserRateThrottle):
    """
    Very restrictive throttle for endpoints that have experienced security events.
    Applied temporarily to users who have triggered security warnings.
    """
    
    rate = '3/min'  # 3 requests per minute
    scope = 'security_event'
    
    def throttle_failure(self):
        """Log security-related throttling."""
        request = getattr(self, 'request', None)
        user = getattr(request, 'user', None) if request else None
        user_id = getattr(user, 'id', 'anonymous') if user else 'anonymous'
        ip = self.get_ident(request) if request else 'unknown'
        
        logger.error(
            f"Security event throttle triggered. "
            f"User: {user_id}, IP: {ip}, "
            f"Rate: {self.rate}"
        )
        
        return super().throttle_failure()


class IPBasedThrottle(AnonRateThrottle):
    """
    IP-based throttle for public endpoints like tutor discovery.
    Rate limits requests from the same IP address to prevent abuse of public APIs.
    """
    
    rate = '100/h'  # 100 requests per hour per IP
    scope = 'ip_based'
    
    def throttle_failure(self):
        """Log IP-based throttling events for monitoring."""
        request = getattr(self, 'request', None)
        ip = self.get_ident(request) if request else 'unknown'
        
        logger.warning(
            f"IP-based rate limit exceeded. "
            f"IP: {ip}, "
            f"Rate: {self.rate}"
        )
        
        return super().throttle_failure()