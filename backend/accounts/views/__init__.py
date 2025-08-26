"""
Views package for the accounts app.

Simplified for PWA migration - using Django web views with HTMX and Alpine.js.
No DRF APIs needed for PWA functionality.
"""

# Import the new Django web authentication views
from .auth_views import (
    SignInView,
    SignUpView,
    VerifyOTPView,
    DashboardView,
    resend_code,
)

# Export all views for backward compatibility
__all__ = [
    # Django web authentication views
    "SignInView",
    "SignUpView", 
    "VerifyOTPView",
    "DashboardView",
    "resend_code",
]