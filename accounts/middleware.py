"""
Middleware for Progressive Verification System

This middleware enforces verification requirements after the grace period expires.
Users have 24 hours after signup to verify their email/phone before being required to do so.
"""

from datetime import datetime
import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class ProgressiveVerificationMiddleware:
    """
    Middleware to enforce progressive verification requirements.
    
    Features:
    - Allows 24h grace period for new users
    - Checks if verification is required based on verification_required_after timestamp
    - Redirects unverified users to verification page after grace period
    - Allows access to certain whitelisted URLs even when unverified
    """
    
    # URLs that unverified users can always access
    WHITELISTED_PATHS = [
        '/signin/',
        '/signup/',
        '/logout/',
        '/verify-otp/',
        '/verify-email/',
        '/magic-login/',
        '/resend-code/',
        '/admin/',
        '/static/',
        '/media/',
        '/health/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request before view
        if self.should_check_verification(request):
            verification_result = self.check_verification_status(request)
            if verification_result:
                return verification_result
        
        response = self.get_response(request)
        return response
    
    def should_check_verification(self, request):
        """Determine if we should check verification for this request."""
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return False
        
        # Skip for superusers
        if request.user.is_superuser:
            return False
        
        # Skip for whitelisted paths
        for path in self.WHITELISTED_PATHS:
            if request.path.startswith(path):
                return False
        
        return True
    
    def check_verification_status(self, request):
        """Check if user needs to verify their account."""
        user = request.user
        
        # Check if user has verification_required_after field
        if not hasattr(user, 'verification_required_after'):
            return None
            
        # If no deadline set, user doesn't need verification (legacy accounts)
        if not user.verification_required_after:
            return None
        
        # Check if grace period has expired
        if timezone.now() > user.verification_required_after:
            # User must verify if neither email nor phone is verified
            if not user.email_verified and not user.phone_verified:
                logger.warning(
                    f"User {user.email} attempted to access {request.path} "
                    f"but verification is required (deadline: {user.verification_required_after})"
                )
                
                # Clear authentication data while preserving CSRF tokens
                self._clear_auth_session_data(request)
                
                # Add message explaining the requirement
                messages.warning(
                    request,
                    _("Your 24-hour grace period has expired. "
                      "Please verify your email or phone number to continue using Aprende Comigo.")
                )
                
                # Redirect to sign-in page
                return redirect(reverse('accounts:signin'))
        else:
            # Still in grace period - check session expiry
            unverified_until = request.session.get('unverified_until')
            if unverified_until:
                # Convert timestamp to datetime
                session_expiry = datetime.fromtimestamp(unverified_until, tz=timezone.get_current_timezone())
                
                # If session has expired, require re-authentication
                if timezone.now() > session_expiry:
                    logger.info(f"Session expired for unverified user {user.email}")
                    self._clear_auth_session_data(request)
                    messages.info(
                        request,
                        "Your session has expired. Please sign in again. "
                        "Remember to verify your email or phone to avoid this in the future."
                    )
                    return redirect(reverse('accounts:signin'))
                
                # Still in grace period - add reminder if not already shown this session
                if not request.session.get('verification_reminder_shown'):
                    hours_left = (user.verification_required_after - timezone.now()).total_seconds() / 3600
                    if hours_left < 12:  # Show reminder when less than 12 hours left
                        messages.info(
                            request,
                            f"You have {int(hours_left)} hours left to verify your email or phone number. "
                            f"Check your tasks for verification instructions."
                        )
                        request.session['verification_reminder_shown'] = True
        
        return None
    
    def _clear_auth_session_data(self, request):
        """
        Clear authentication-related session data while preserving CSRF tokens
        and other necessary session infrastructure.
        """
        from django.contrib.auth import logout
        
        # Use Django's logout which properly handles session management
        # This clears authentication data while preserving CSRF tokens
        logout(request)
        
        # Clear any custom verification session data
        verification_keys = [
            'verification_email', 'verification_phone', 'verification_user_id',
            'verification_otp_code', 'verification_otp_expires', 'is_signup',
            'is_signin', 'signup_school_name', 'is_unverified_user',
            'unverified_until', 'verification_reminder_shown'
        ]
        
        for key in verification_keys:
            request.session.pop(key, None)


class VerificationCompletionMiddleware:
    """
    Middleware to handle verification completion and update user status.
    
    This middleware checks if a user has completed verification via magic link
    and updates their verification status accordingly.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if user just authenticated via magic link on verify-email endpoint
        if request.user.is_authenticated and request.path == '/verify-email/':
            user = request.user
            
            # Mark email as verified
            if not user.email_verified:
                user.email_verified = True
                user.save(update_fields=['email_verified'])
                
                # Mark the email verification task as completed
                try:
                    from tasks.models import Task
                    email_task = Task.objects.filter(
                        user=user,
                        title="Verify your email address",
                        status="pending"
                    ).first()
                    if email_task:
                        email_task.status = "completed"
                        email_task.save()
                        logger.info(f"Email verification task completed for {user.email}")
                except Exception as e:
                    logger.error(f"Failed to update email verification task: {e}")
                
                # Remove unverified session markers
                if 'is_unverified_user' in request.session:
                    del request.session['is_unverified_user']
                if 'unverified_until' in request.session:
                    del request.session['unverified_until']
                
                # Reset session expiry to default
                request.session.set_expiry(0)  # Use default session length
                
                messages.success(request, _("Your email has been successfully verified!"))
                logger.info(f"Email verified for user {user.email}")
        
        return response