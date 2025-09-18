"""
Middleware for Progressive Verification System and PWA Session Management

This module contains middleware for:
1. Progressive verification requirements after grace period
2. PWA detection and differentiated session management (24h web vs 7d PWA)
3. User activity tracking and security headers
"""

from datetime import datetime, timedelta
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from .utils.pwa_detection import PWADetector

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
        "/signin/",
        "/signup/",
        "/logout/",
        "/verify-otp/",
        "/verify-email/",
        "/verify-phone/",  # Added missing phone verification endpoint
        "/magic-login/",
        "/resend-code/",
        "/admin/",
        "/static/",
        "/media/",
        "/health/",
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
        return all(not request.path.startswith(path) for path in self.WHITELISTED_PATHS)

    def check_verification_status(self, request):
        """Check if user needs to verify their account."""
        user = request.user

        # Check if user has verification_required_after field
        if not hasattr(user, "verification_required_after"):
            return None

        # If no deadline set, user doesn't need verification (legacy accounts)
        if not user.verification_required_after:
            return None

        # TODO: Re-enable after beta - Check if grace period has expired
        # BETA: Verification deadline enforcement disabled for beta period
        if False:  # timezone.now() > user.verification_required_after:
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
                    _(
                        "Your 24-hour grace period has expired. "
                        "Please verify your email or phone number to continue using Aprende Comigo."
                    ),
                )

                # Redirect to sign-in page
                return redirect(reverse("accounts:signin"))
        else:
            # Still in grace period - check session expiry
            unverified_until = request.session.get("unverified_until")
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
                        "Remember to verify your email or phone to avoid this in the future.",
                    )
                    return redirect(reverse("accounts:signin"))

                # Still in grace period - add reminder if not already shown this session
                if not request.session.get("verification_reminder_shown"):
                    hours_left = (user.verification_required_after - timezone.now()).total_seconds() / 3600
                    if hours_left < 12:  # Show reminder when less than 12 hours left
                        messages.info(
                            request,
                            f"You have {int(hours_left)} hours left to verify your email or phone number. "
                            f"Check your tasks for verification instructions.",
                        )
                        request.session["verification_reminder_shown"] = True

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
            "verification_email",
            "verification_phone",
            "verification_user_id",
            "verification_otp_code",
            "verification_otp_expires",
            "is_signup",
            "is_signin",
            "signup_school_name",
            "is_unverified_user",
            "unverified_until",
            "verification_reminder_shown",
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

        # Check if user just authenticated via magic link on verification endpoints
        if request.user.is_authenticated:
            user = request.user

            # Handle email verification
            if request.path == "/verify-email/" and not user.email_verified:
                user.email_verified = True
                user.email_verified_at = timezone.now()
                user.save(update_fields=["email_verified", "email_verified_at"])

                # Mark the email verification task as completed
                try:
                    from tasks.models import Task

                    email_task = Task.objects.filter(
                        user=user, title="Verify your email address", status="pending"
                    ).first()
                    if email_task:
                        email_task.status = "completed"
                        email_task.save()
                        logger.info(f"Email verification task completed for {user.email}")
                except Exception as e:
                    logger.error(f"Failed to update email verification task: {e}")

                messages.success(request, _("Your email has been successfully verified!"))
                logger.info(f"Email verified for user {user.email}")

            # Handle phone verification
            elif request.path == "/verify-phone/" and not user.phone_verified:
                user.phone_verified = True
                user.phone_verified_at = timezone.now()
                user.save(update_fields=["phone_verified", "phone_verified_at"])

                # Mark the phone verification task as completed
                try:
                    from tasks.models import Task

                    phone_task = Task.objects.filter(
                        user=user, title="Verify your phone number", status="pending"
                    ).first()
                    if phone_task:
                        phone_task.status = "completed"
                        phone_task.save()
                        logger.info(f"Phone verification task completed for {user.email}")
                except Exception as e:
                    logger.error(f"Failed to update phone verification task: {e}")

                messages.success(request, _("Your phone has been successfully verified!"))
                logger.info(f"Phone verified for user {user.email}")

            # Common cleanup for both verification types
            if request.path in ["/verify-email/", "/verify-phone/"]:
                # Remove unverified session markers
                if "is_unverified_user" in request.session:
                    del request.session["is_unverified_user"]
                if "unverified_until" in request.session:
                    del request.session["unverified_until"]

                # Reset session expiry to default
                request.session.set_expiry(0)  # Use default session length

        return response


class SessionManagementMiddleware:
    """
    Middleware for PWA detection and differentiated session management.

    Features:
    - Detects PWA mode using comprehensive fallback strategies
    - Sets appropriate session duration: 24h (web) vs 7d (PWA)
    - Updates user activity tracking (limited to every 5 minutes)
    - Sets security headers for session cookies
    - Handles session duration changes when client type changes

    Business Requirements:
    - FR-4.1: Web browser sessions = 24 hours
    - FR-4.2: PWA installation sessions = 7 days
    - FR-4.3: Automatic session extension based on activity
    - FR-4.4: Secure session management with proper headers
    """

    # Activity update interval (5 minutes to avoid excessive DB writes)
    ACTIVITY_UPDATE_INTERVAL = timedelta(minutes=5)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request before view
        self.configure_session_duration(request)
        self.update_user_activity(request)

        # Get response from view
        response = self.get_response(request)

        # Set security headers on response
        self.set_security_headers(response, request)

        return response

    def configure_session_duration(self, request):
        """
        Configure session duration based on PWA detection.

        Sets session duration and metadata:
        - is_pwa_session: Boolean flag for PWA mode
        - session_created_at: Timestamp when session was configured
        - session_duration_set: The duration that was set
        """
        # Add defensive check - request.user might not be available yet
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return

        # Detect PWA mode
        is_pwa = PWADetector.is_pwa_request(request)
        session_duration = PWADetector.get_session_duration(request)

        # Get current session metadata
        current_pwa_session = request.session.get("is_pwa_session")

        # Check if we need to update session configuration
        current_duration = request.session.get("session_duration_set")

        # Debug logging for tests
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Session config check - PWA: {is_pwa}, current_pwa: {current_pwa_session}, "
                f"current_duration: {current_duration}, expected_duration: {session_duration}"
            )

        should_update_session = (
            current_pwa_session is None  # First time configuration
            or current_pwa_session != is_pwa  # Client type changed
            or not current_duration  # Missing configuration
            or current_duration != session_duration  # Duration changed
        )

        if should_update_session:
            # Set session duration
            request.session.set_expiry(session_duration)

            # Store session metadata
            request.session["is_pwa_session"] = is_pwa
            request.session["session_created_at"] = timezone.now().isoformat()
            request.session["session_duration_set"] = session_duration

            # Log the configuration
            client_type = "PWA" if is_pwa else "Web Browser"
            duration_hours = session_duration / 3600
            logger.info(
                f"Session configured for user {request.user.email}: {client_type} mode, {duration_hours}h duration"
            )

            # Debug information
            if logger.isEnabledFor(logging.DEBUG):
                detection_info = PWADetector.get_detection_info(request)
                logger.debug(f"PWA detection details: {detection_info}")

    def update_user_activity(self, request):
        """
        Update user activity tracking with rate limiting.

        Only updates last_activity field every 5 minutes to avoid
        excessive database writes while maintaining reasonable activity tracking.
        """
        # Add defensive check - request.user might not be available yet
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return

        user = request.user
        now = timezone.now()

        # Check if enough time has passed since last activity update
        if user.last_activity is None or now - user.last_activity >= self.ACTIVITY_UPDATE_INTERVAL:
            try:
                # Update last_activity field efficiently
                User = get_user_model()
                User.objects.filter(pk=user.pk).update(last_activity=now)

                # Update the current user instance to avoid stale data
                user.last_activity = now

                logger.debug(f"Updated activity for user {user.email}")

            except Exception as e:
                logger.error(f"Failed to update user activity for {user.email}: {e}")

    def set_security_headers(self, response, request):
        """
        Set security headers for session management and PWA support.

        Sets headers for:
        - Session cookie security
        - Content security and XSS protection
        - PWA-specific caching headers when appropriate
        """
        # Standard security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"

        # PWA-specific cache control headers
        if request.session.get("is_pwa_session"):
            # More aggressive caching for PWA to improve offline experience
            if request.path.startswith("/static/") or request.path.startswith("/media/"):
                response["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                # Dynamic content should still be validated
                response["Cache-Control"] = "private, max-age=300"
        else:
            # Standard web browser cache control
            response["Cache-Control"] = "private, no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        # Add Vary header for PWA detection
        vary_header = response.get("Vary", "")
        pwa_headers = ["User-Agent", "Cookie"]

        for header in pwa_headers:
            if header not in vary_header:
                if vary_header:
                    vary_header += f", {header}"
                else:
                    vary_header = header

        response["Vary"] = vary_header
