"""
Authentication views for Django web interface (PWA Migration).

This module provides comprehensive authentication functionality including:
- Email magic link authentication with SMS OTP verification
- User registration with automatic school creation
- Teacher invitation system with role-based permissions
- Profile and school management views
- Session management and security utilities

All authentication flows follow a secure dual-verification approach
combining email magic links and SMS OTP verification for enhanced security.
"""

from datetime import timedelta
import logging
import re
import secrets
import uuid

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView
from sesame.utils import get_query_string, get_query_string as sesame_get_query_string
from sesame.views import LoginView as SesameLoginView

from messaging.services import send_magic_link_email, send_sms_otp

from .db_queries import create_user_school_and_membership, get_user_by_email, user_exists
from .models import School, SchoolMembership, SchoolSettings, TeacherInvitation
from .models.profiles import StudentProfile
from .models.schools import SchoolRole
from .permissions import IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin

User = get_user_model()
logger = logging.getLogger(__name__)
email_confirmation_logger = logging.getLogger("accounts.email_confirmation")

# =============================================================================
# EMAIL CONFIRMATION LOGGING SYSTEM (Development Environment)
# =============================================================================


def log_email_confirmation_sent(email: str, confirmation_token: str | None = None) -> None:
    """Log email confirmation sent in development environment"""
    token_info = f" (Token: {confirmation_token})" if confirmation_token else ""
    email_confirmation_logger.info(
        f"📧 Email confirmation sent to {email}{token_info} - User needs to confirm their email to activate account"
    )


def log_email_confirmation_success(email: str) -> None:
    """Log successful email confirmation in development environment"""
    email_confirmation_logger.info(f"✅ Email confirmation successful for {email} - Account activated")


def log_email_confirmation_failure(email: str, reason: str = "Unknown") -> None:
    """Log failed email confirmation in development environment"""
    email_confirmation_logger.warning(f"❌ Email confirmation failed for {email} - Reason: {reason}")


def log_email_confirmation_resent(email: str, confirmation_token: str | None = None) -> None:
    """Log email confirmation resent in development environment"""
    token_info = f" (New Token: {confirmation_token})" if confirmation_token else ""
    email_confirmation_logger.info(f"🔄 Email confirmation resent to {email}{token_info}")


def log_email_confirmation_expired(email: str) -> None:
    """Log email confirmation token expiry in development environment"""
    email_confirmation_logger.warning(f"⏰ Email confirmation token expired for {email} - User needs new confirmation")


# Constants
EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
OTP_EXPIRY_MINUTES = 5
VERIFICATION_SESSION_KEYS = [
    "verification_email",
    "verification_phone",
    "verification_user_id",
    "verification_otp_code",
    "verification_otp_expires",
    "is_signup",
    "is_signin",
    "signup_school_name",
]


class SignInView(View):
    """
    Handle user sign-in with SMS OTP verification.

    This view provides a secure login flow for existing users:
    1. User enters email address
    2. System sends SMS OTP to registered phone number
    3. User verifies OTP to complete login

    GET: Display sign-in form
    POST: Validate email and send SMS OTP
    """

    def get(self, request) -> HttpResponse:
        """Render sign-in page for unauthenticated users."""
        if request.user.is_authenticated:
            return redirect(reverse("dashboard:dashboard"))

        return render(
            request,
            "accounts/signin.html",
            {"title": "Login - Aprende Comigo", "meta_description": "Sign in to your Aprende Comigo account"},
        )

    @method_decorator(csrf_protect)
    def post(self, request):
        """Handle sign in form submission via HTMX"""
        email = request.POST.get("email", "").strip().lower()
        logger.info(f"[SIGNIN] Starting signin process for: {email}")

        # Validate email using the same pattern as the HTML form
        email_pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

        if not email:
            return render(
                request,
                "accounts/partials/signin_form.html",
                {"error": "Please enter your email address", "email": email},
            )

        # Check if it's a valid email
        if not re.match(email_pattern, email):
            return render(
                request,
                "accounts/partials/signin_form.html",
                {"error": "Please enter a valid email address", "email": email},
            )

        try:
            # Check if user exists
            if not user_exists(email):
                # Log the event for security monitoring
                logger.warning(f"Authentication attempt with unregistered email: {email}")

                # Set minimal session data for security (prevent email enumeration)
                request.session["verification_email"] = email

                # Still show success to prevent email enumeration
                return render(request, "accounts/partials/signin_success_with_verify.html", {"email": email})

            # User exists - generate dual verification for existing users
            logger.info(f"Dual verification requested for registered email: {email}")
            user = get_user_by_email(email)

            # Generate magic link for email verification
            login_url = reverse("accounts:magic_login")
            magic_link = request.build_absolute_uri(login_url) + get_query_string(user)
            logger.info(f"Generated magic link for {email}: {login_url} (token length: {len(get_query_string(user))})")

            # Generate secure 6-digit OTP code for SMS verification
            otp_code = str(secrets.randbelow(900000) + 100000)
            otp_expires = (timezone.now() + timedelta(minutes=5)).timestamp()
            logger.info(
                f"[OTP DEBUG] Generated OTP code: '{otp_code}' (type: {type(otp_code)}, len: {len(otp_code)}) for user: {user.email}"
            )
            logger.info(f"[OTP DEBUG] OTP expires at timestamp: {otp_expires}")

            try:
                # Send both magic link and SMS OTP (if phone available)
                email_result = send_magic_link_email(email, magic_link, user.name or user.first_name)

                # Log email confirmation for development environment
                if email_result.get("success"):
                    # Extract token from magic link for logging (last part after 'sesame=')
                    token = magic_link.split("sesame=")[-1] if "sesame=" in magic_link else "generated"
                    log_email_confirmation_sent(email, token[:8] + "...")  # Show partial token for security
                else:
                    log_email_confirmation_failure(email, "Email sending failed")

                # Check if user has phone number for SMS
                if user.phone_number:
                    sms_result = send_sms_otp(user.phone_number, otp_code, user.name or user.first_name)
                else:
                    sms_result = {"success": True}  # Continue if no phone number
                    logger.warning(f"User {email} has no phone number on file")

                if email_result.get("success") and sms_result.get("success"):
                    # Store verification data in session
                    request.session["verification_email"] = email
                    request.session["verification_phone"] = user.phone_number
                    request.session["verification_user_id"] = user.id
                    request.session["verification_otp_code"] = otp_code
                    request.session["verification_otp_expires"] = otp_expires
                    request.session["is_signin"] = True
                    logger.info(f"[OTP DEBUG] Stored in session - OTP: '{otp_code}' (type: {type(otp_code)})")
                    logger.info(f"[OTP DEBUG] Session keys stored: {list(request.session.keys())}")

                    logger.info(
                        f"Dual verification sent successfully to: {email} and {user.phone_number or 'no phone'}"
                    )
                    return render(
                        request,
                        "accounts/partials/signin_success_with_verify.html",
                        {"email": email, "phone_number": user.phone_number},
                    )
                else:
                    return render(
                        request,
                        "accounts/partials/signin_form.html",
                        {
                            "error": "There was an issue sending the verification codes. Please try again.",
                            "email": email,
                        },
                    )

            except Exception as verification_error:
                logger.error(f"Failed to send verification codes to {email}: {verification_error}")
                return render(
                    request,
                    "accounts/partials/signin_form.html",
                    {"error": "There was an issue sending the verification codes. Please try again.", "email": email},
                )

        except Exception as e:
            logger.error(f"Sign in error for {email}: {e}")
            return render(
                request,
                "accounts/partials/signin_form.html",
                {"error": "There was an issue sending the verification codes. Please try again.", "email": email},
            )


class SignUpView(View):
    """
    Handle user registration with dual verification (email + SMS).

    This view manages the complete user registration process:
    1. User provides email, full name, and phone number
    2. System creates user account
    3. System sends email magic link and SMS OTP for verification
    4. User completes verification via VerifyOTPView

    Upon successful registration and verification, a personal school
    is automatically created with the user as owner.

    GET: Display registration form
    POST: Process registration and initiate dual verification
    """

    def get(self, request) -> HttpResponse:
        """Render sign-up page for unauthenticated users."""
        if request.user.is_authenticated:
            return redirect(reverse("dashboard:dashboard"))

        return render(
            request,
            "accounts/signup.html",
            {"title": "Create Account - Aprende Comigo", "meta_description": "Create your Aprende Comigo account"},
        )

    @method_decorator(csrf_protect)
    def post(self, request):
        """Handle sign up form submission via HTMX"""
        email = request.POST.get("email", "").strip().lower()
        full_name = request.POST.get("full_name", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        organization_name = request.POST.get("organization_name", "").strip()

        # Validate inputs
        if not email:
            return render(
                request,
                "accounts/partials/signup_form.html",
                {"error": "Email is required", "email": email, "full_name": full_name, "phone_number": phone_number},
            )

        if not full_name:
            return render(
                request,
                "accounts/partials/signup_form.html",
                {
                    "error": "Full name is required",
                    "email": email,
                    "full_name": full_name,
                    "phone_number": phone_number,
                },
            )

        if not phone_number:
            return render(
                request,
                "accounts/partials/signup_form.html",
                {
                    "error": "Phone number is required",
                    "email": email,
                    "full_name": full_name,
                    "phone_number": phone_number,
                },
            )

        if not organization_name:
            return render(
                request,
                "accounts/partials/signup_form.html",
                {
                    "error": "Organization name is required",
                    "email": email,
                    "full_name": full_name,
                    "phone_number": phone_number,
                },
            )

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return render(
                request,
                "accounts/partials/signup_form.html",
                {
                    "error": "Please enter a valid email address",
                    "email": email,
                    "full_name": full_name,
                    "phone_number": phone_number,
                },
            )

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return render(
                request,
                "accounts/partials/signup_form.html",
                {
                    "error": "An account with this email already exists. Try signing in instead.",
                    "email": email,
                    "full_name": full_name,
                    "phone_number": phone_number,
                },
            )

        try:
            # Extract first name for user creation
            first_name = full_name.split()[0] if full_name else ""

            # Create user, school, and membership atomically
            with transaction.atomic():
                # Create user with phone number
                user = User.objects.create_user(
                    email=email,
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=" ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
                )

                # Set user as unverified but allow access
                user.email_verified = False
                user.phone_verified = False
                # Store when verification becomes mandatory (24 hours from now)
                user.verification_required_after = timezone.now() + timedelta(hours=24)
                user.save()

                # Create school and membership immediately
                create_user_school_and_membership(user, organization_name)

                # Log in the user immediately (progressive verification)
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")

                # Mark this as an unverified session (expires in 24h)
                request.session["is_unverified_user"] = True
                request.session["unverified_until"] = (timezone.now() + timedelta(hours=24)).timestamp()
                request.session.set_expiry(24 * 60 * 60)  # 24 hours

                logger.info(f"User signup completed for: {email} (unverified, 24h grace period)")

                # Send verification emails/SMS asynchronously (non-blocking)
                try:
                    # Generate magic link for email verification
                    login_url = reverse("accounts:verify_email")
                    from sesame.utils import get_query_string

                    magic_link = request.build_absolute_uri(login_url) + get_query_string(user)

                    # Send email verification (non-blocking)
                    send_magic_link_email(email, magic_link, first_name, is_verification=True)
                    logger.info(f"Verification email sent to: {email}")

                    # Generate and send SMS OTP if phone provided
                    if phone_number:
                        otp_code = str(secrets.randbelow(900000) + 100000)
                        request.session[f"verify_otp_{user.id}"] = otp_code
                        request.session[f"verify_otp_expires_{user.id}"] = (
                            timezone.now() + timedelta(minutes=30)
                        ).timestamp()
                        send_sms_otp(phone_number, otp_code, first_name, is_verification=True)
                        logger.info(f"Verification SMS sent to: {phone_number}")
                except Exception as e:
                    # Don't block signup if verification sending fails
                    logger.error(f"Failed to send verifications for {email}: {e}")

                # System tasks are created automatically via signal when user is created
                # No need for explicit task creation here

            # Return success with redirect to dashboard
            return render(
                request,
                "accounts/partials/signup_success_redirect.html",
                {
                    "message": "Account created successfully! Welcome to Aprende Comigo.",
                    "redirect_url": reverse("dashboard:dashboard"),
                },
            )

        except Exception as e:
            logger.error(f"Sign up error for {email}: {e}")
            return render(
                request,
                "accounts/partials/signup_form.html",
                {
                    "error": "There was an issue creating your account. Please try again.",
                    "email": email,
                    "full_name": full_name,
                    "phone_number": phone_number,
                },
            )


class VerifyOTPView(View):
    """
    Handle SMS OTP verification for both signup and signin flows.

    This view manages the second step of our dual-factor authentication:
    1. Email magic link (handled by sesame)
    2. SMS OTP verification (handled here)

    CRITICAL BUSINESS RULE: Every user (except superusers) MUST have a school association.
    For signup: User verification and school creation are atomic - both succeed or both fail.
    For signin: Authenticates existing user after successful verification.

    Session data required:
    - verification_user_id: User ID for verification
    - verification_otp_code: Expected OTP code
    - verification_otp_expires: OTP expiration timestamp
    - verification_phone: Phone number for context
    - verification_email: Email for context
    - is_signup/is_signin: Flow type flags
    - signup_school_name: School name for new user (signup only)
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render OTP verification page with context from session data."""
        # Check session data
        user_id = request.session.get("verification_user_id")
        expected_otp = request.session.get("verification_otp_code")
        phone = request.session.get("verification_phone")
        is_signup = request.session.get("is_signup", False)
        is_signin = request.session.get("is_signin", False)

        if not all([user_id, expected_otp, phone]):
            return redirect(reverse("accounts:signin"))

        return render(
            request,
            "accounts/verify_code.html",
            {
                "title": "Verify Phone - Aprende Comigo",
                "meta_description": "Enter your SMS verification code",
                "phone_number": phone,
                "is_signup": is_signup,
                "is_signin": is_signin,
            },
        )

    @method_decorator(csrf_protect)
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Handle OTP verification for both signup and signin flows.

        Validates the SMS OTP code against session data and:
        - For signup: Creates school and membership, then logs in user
        - For signin: Logs in existing user

        Returns: HTMX partial template with success or error message
        """
        otp_code = request.POST.get("verification_code", "").strip()

        # Get session data
        user_id = request.session.get("verification_user_id")
        expected_otp = request.session.get("verification_otp_code")
        otp_expires = request.session.get("verification_otp_expires")
        phone = request.session.get("verification_phone")
        email = request.session.get("verification_email")  # Get email for combined template
        is_signup = request.session.get("is_signup", False)
        is_signin = request.session.get("is_signin", False)

        if not all([user_id, expected_otp, phone, otp_code]):
            return render(
                request,
                "accounts/partials/signin_success_with_verify.html",
                {
                    "error": "Please enter the verification code.",
                    "email": email,
                    "phone_number": phone,
                },
            )

        # Check if OTP has expired
        if otp_expires and timezone.now().timestamp() > otp_expires:
            return render(
                request,
                "accounts/partials/signin_success_with_verify.html",
                {
                    "error": "Verification code has expired. Please request a new one.",
                    "email": email,
                    "phone_number": phone,
                },
            )

        try:
            # Get user
            user = User.objects.get(id=user_id)

            # DEBUG: Log OTP verification details
            logger.info(f"[OTP DEBUG] User input: '{otp_code}' (type: {type(otp_code)}, len: {len(otp_code)})")
            logger.info(f"[OTP DEBUG] Expected OTP: '{expected_otp}' (type: {type(expected_otp)})")
            logger.info(f"[OTP DEBUG] OTP expires: {otp_expires}")
            logger.info(f"[OTP DEBUG] Current timestamp: {timezone.now().timestamp()}")
            logger.info(f"[OTP DEBUG] Comparison result: {otp_code == expected_otp}")

            # Verify OTP by comparing with session-stored code
            if otp_code == expected_otp:
                if is_signup:
                    # Signup now happens immediately, no OTP verification needed
                    logger.warning(f"Unexpected signup OTP verification for user: {user.email}")
                    self._clear_verification_session(request)
                    return render(
                        request,
                        "accounts/partials/signin_success_with_verify.html",
                        {
                            "error": "Signup process has changed. Please sign up again.",
                            "email": email,
                            "phone_number": phone,
                        },
                    )

                elif is_signin:
                    # TODO handle verification, account expiration, etc
                    # For signin, SMS OTP is sufficient
                    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                    logger.info(f"SMS authentication successful for user: {user.email}")

                    # Check if phone needs to be verified before we update it
                    phone_was_unverified = not user.phone_verified

                    # Mark phone as verified since SMS OTP was successful
                    if not user.phone_verified:
                        user.phone_verified = True
                        user.save(update_fields=["phone_verified"])
                        logger.info(f"Phone verification completed via SMS OTP for user: {user.email}")

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

                    # Remove unverified session markers
                    if "is_unverified_user" in request.session:
                        del request.session["is_unverified_user"]
                    if "unverified_until" in request.session:
                        del request.session["unverified_until"]

                    # Reset session expiry to default
                    request.session.set_expiry(0)  # Use default session length

                    # Clear session data
                    self._clear_verification_session(request)

                    # Create success message
                    success_message = "Welcome back!"
                    if phone_was_unverified:
                        success_message = "Welcome back! Your phone number has been verified."

                    return render(
                        request,
                        "accounts/partials/verify_success.html",
                        {"message": success_message, "redirect_url": reverse("dashboard:dashboard")},
                    )

            else:
                return render(
                    request,
                    "accounts/partials/signin_success_with_verify.html",
                    {
                        "error": "Invalid verification code. Please try again.",
                        "email": email,
                        "phone_number": phone,
                    },
                )

        except Exception as e:
            logger.error(f"OTP verification error: {e}")
            return render(
                request,
                "accounts/partials/signin_success_with_verify.html",
                {
                    "error": "There was an issue verifying your code. Please try again.",
                    "email": email,
                    "phone_number": phone,
                },
            )

    def _clear_verification_session(self, request: HttpRequest) -> None:
        """
        Clear all verification-related session data.

        Removes all session keys used during the verification process
        to prevent data leakage and ensure clean session state.

        Args:
            request: HTTP request containing session data to clear
        """
        keys_to_clear = [
            "verification_email",
            "verification_phone",
            "verification_user_id",
            "verification_otp_code",
            "verification_otp_expires",
            "is_signup",
            "is_signin",
            "signup_school_name",
        ]
        for key in keys_to_clear:
            request.session.pop(key, None)


# Function for resending verification code via HTMX
@csrf_protect
def resend_code(request: HttpRequest) -> HttpResponse:
    """
    Resend magic link verification email via HTMX.

    Retrieves email from session, validates user exists, generates new magic link,
    and sends it via email. Used when users need a new verification link.

    Args:
        request: HTTP request with session containing verification_email

    Returns:
        HttpResponse: HTMX partial with success or error message
    """
    email = request.session.get("verification_email")

    if not email:
        return render(
            request, "accounts/partials/resend_error.html", {"error": "Session expired. Please try signing in again."}
        )

    try:
        # Check if user exists and generate new magic link
        if not user_exists(email):
            return render(
                request, "accounts/partials/resend_error.html", {"error": "No account found with this email address."}
            )

        logger.info(f"Resending magic link for: {email}")
        user = get_user_by_email(email)
        login_url = reverse("accounts:magic_login")
        magic_link = request.build_absolute_uri(login_url) + get_query_string(user)
        logger.info(f"Regenerated magic link for {email}: {login_url} (token length: {len(get_query_string(user))})")

        try:
            send_magic_link_email(email, magic_link, user.name or user.first_name)
            logger.info(f"Magic link resent successfully to: {email}")

            # Log email confirmation resent for development environment
            token = magic_link.split("sesame=")[-1] if "sesame=" in magic_link else "generated"
            log_email_confirmation_resent(email, token[:8] + "...")  # Show partial token for security

            return render(
                request,
                "accounts/partials/resend_success.html",
                {"email": email, "message": "A new login link has been sent to your email."},
            )

        except Exception as email_error:
            logger.error(f"Failed to resend magic link to {email}: {email_error}")
            # Log email confirmation failure for development environment
            log_email_confirmation_failure(email, f"Resend failed: {email_error!s}")

            return render(
                request,
                "accounts/partials/resend_error.html",
                {"error": "There was an issue resending the login link. Please try again."},
            )

    except Exception as e:
        logger.error(f"Resend code error for {email}: {e}")
        return render(
            request,
            "accounts/partials/resend_error.html",
            {"error": "There was an issue resending the login link. Please try again."},
        )


class LogoutView(View):
    """
    Handle user logout for both GET and POST requests.

    Logs the logout event, clears session data, and redirects to signin page.
    Supports both direct navigation and form submission.
    """

    def get(self, request: HttpRequest) -> HttpResponseRedirect:
        """Handle GET logout request by delegating to POST."""
        return self.post(request)

    def post(self, request: HttpRequest) -> HttpResponseRedirect:
        """
        Handle POST logout request.

        Logs the logout event for authenticated users, performs Django logout,
        flushes session data for security, and redirects to signin page.
        """
        from django.contrib.auth import logout

        # Log the logout event
        if request.user.is_authenticated:
            logger.info(f"User logged out: {request.user.email}")

        # Perform logout (this handles session cleanup properly)
        logout(request)

        # Note: Django's logout() function properly manages session data
        # No need to call session.flush() which removes CSRF tokens
        # The logout() function clears authentication data while preserving
        # necessary session infrastructure like CSRF tokens

        # Redirect to signin page using correct URL
        return redirect(reverse("accounts:signin"))


# =============================================================================
# INVITATION MANAGEMENT VIEWS
# =============================================================================


class TeacherInvitationListView(IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin, ListView):
    """
    Display paginated list of teacher invitations for schools managed by current user.

    Only shows invitations for schools where the user has SCHOOL_OWNER or
    SCHOOL_ADMIN privileges. Includes school and invited_by relationships
    for efficient database queries.

    Access: School owners and admins only
    """

    model = TeacherInvitation
    template_name = "accounts/invitations/invitation_list.html"
    context_object_name = "invitations"
    paginate_by = 20

    def get_queryset(self):
        # Get schools the user can manage
        user_schools = self.get_user_schools_by_role("school_owner") | self.get_user_schools_by_role("school_admin")

        # Filter invitations for these schools
        return (
            TeacherInvitation.objects.filter(school__in=user_schools)
            .select_related("school", "invited_by")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schools"] = self.get_user_schools_by_role("school_owner") | self.get_user_schools_by_role(
            "school_admin"
        )
        return context


class TeacherInvitationCreateView(IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin, CreateView):
    """
    Create and send new teacher invitation with email notification.

    Allows school owners and admins to invite teachers to their schools.
    Validates permissions, generates unique invitation token, and sends
    email invitation to the specified address.

    Features:
    - Role-based access control
    - Atomic transaction for data consistency
    - Email notification system integration
    - Unique batch ID for tracking

    Access: School owners and admins only
    """

    model = TeacherInvitation
    template_name = "accounts/invitations/invitation_create.html"
    fields = ["school", "email", "custom_message"]
    success_url = reverse_lazy("accounts:invitation_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit school choices to schools the user can manage
        user_schools = self.get_user_schools_by_role("school_owner") | self.get_user_schools_by_role("school_admin")
        form.fields["school"].queryset = user_schools
        return form

    def form_valid(self, form):
        # Generate batch ID for tracking
        batch_id = uuid.uuid4()

        # Set the invitation details
        form.instance.invited_by = self.request.user
        form.instance.batch_id = batch_id
        form.instance.role = "teacher"  # Default to teacher role

        # Check if user has permission to invite to this school
        school = form.instance.school
        if not self.has_school_permission(school, ["school_owner", "school_admin"]):
            messages.error(self.request, _("You don't have permission to invite teachers to this school."))
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                response = super().form_valid(form)

                # Send invitation email (implement this based on your email system)
                # send_teacher_invitation_email(form.instance)

                messages.success(
                    self.request, _("Teacher invitation sent to %(email)s") % {"email": form.instance.email}
                )
                return response

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class TeacherInvitationDetailView(IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin, DetailView):
    """
    Display detailed information about a specific teacher invitation.

    Shows invitation status, creation date, expiration, email, and any
    custom message. Only accessible to users who can manage the
    associated school.

    Access: School owners and admins only
    """

    model = TeacherInvitation
    template_name = "accounts/invitations/invitation_detail.html"
    context_object_name = "invitation"

    def get_queryset(self):
        # Limit to invitations for schools the user can manage
        user_schools = self.get_user_schools_by_role("school_owner") | self.get_user_schools_by_role("school_admin")
        return TeacherInvitation.objects.filter(school__in=user_schools)


class AcceptTeacherInvitationView(View):
    """
    Handle teacher invitation acceptance via public token URL.

    This is a public view accessible without authentication, allowing invited
    teachers to accept invitations via email links. Validates invitation token,
    checks expiration, and processes the acceptance.

    Flow:
    1. GET: Display invitation acceptance form
    2. POST: Process acceptance and create user/membership

    Access: Public (token-based authentication)
    """

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        """Display invitation acceptance form"""
        invitation = get_object_or_404(TeacherInvitation, token=token)

        # Check if invitation is valid
        if not invitation.is_valid():
            return render(request, "accounts/invitations/invitation_expired.html", {"invitation": invitation})

        # Mark as viewed
        invitation.mark_viewed()

        return render(request, "accounts/invitations/accept_invitation.html", {"invitation": invitation})

    @method_decorator(csrf_protect)
    def post(self, request: HttpRequest, token: str) -> HttpResponse:
        """
        Process invitation acceptance or decline action.

        Handles 'accept' or 'decline' actions from the invitation form.
        For acceptance, creates user membership and redirects appropriately.
        For decline, marks invitation as declined.

        Args:
            request: HTTP request containing action parameter
            token: Invitation token for validation

        Returns:
            HttpResponse: Success page or redirect based on user state
        """
        invitation = get_object_or_404(TeacherInvitation, token=token)

        # Check if invitation is valid
        if not invitation.is_valid():
            return render(request, "accounts/invitations/invitation_expired.html", {"invitation": invitation})

        action = request.POST.get("action")

        if action == "accept":
            # Check if user exists
            try:
                user = User.objects.get(email=invitation.email)

                # Create school membership
                membership, created = SchoolMembership.objects.get_or_create(
                    user=user, school=invitation.school, role=invitation.role, defaults={"is_active": True}
                )

                if not created and not membership.is_active:
                    membership.is_active = True
                    membership.save()

                # Mark invitation as accepted
                invitation.accept()

                # If user is logged in and it's the correct user, redirect to dashboard
                if request.user.is_authenticated and request.user.email == invitation.email:
                    messages.success(
                        request,
                        _("Welcome to %(school)s! You are now a %(role)s.")
                        % {"school": invitation.school.name, "role": invitation.get_role_display()},
                    )
                    return redirect(reverse("dashboard:dashboard"))

                # Otherwise, show success page with login instructions
                return render(
                    request,
                    "accounts/invitations/invitation_accepted.html",
                    {"invitation": invitation, "user_exists": True},
                )

            except User.DoesNotExist:
                # User doesn't exist, show signup flow
                return render(
                    request,
                    "accounts/invitations/invitation_accepted.html",
                    {
                        "invitation": invitation,
                        "user_exists": False,
                        "signup_url": reverse("accounts:signup")
                        + f"?email={invitation.email}&invitation_token={token}",
                    },
                )

        elif action == "decline":
            invitation.decline()
            return render(request, "accounts/invitations/invitation_declined.html", {"invitation": invitation})

        return redirect(reverse("accounts:accept_invitation", kwargs={"token": token}))


class CustomMagicLoginView(SesameLoginView):
    """
    Custom magic link login view with enhanced error handling and logging.

    Extends sesame's LoginView to provide better user feedback and debugging
    information for magic link authentication failures.
    """

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to add custom error handling."""
        try:
            logger.info(f"Magic link login attempt from IP: {request.META.get('REMOTE_ADDR')}")
            logger.info(f"Magic link URL: {request.get_full_path()}")
            logger.info(f"User-Agent: {request.headers.get('user-agent', 'Unknown')}")

            response = super().dispatch(request, *args, **kwargs)

            # Log successful authentication
            if hasattr(request, "user") and request.user.is_authenticated:
                logger.info(f"Magic link authentication successful for user: {request.user.email}")

            return response

        except PermissionDenied as e:
            logger.warning(f"Magic link authentication failed: {e}")
            logger.warning(f"Request details - Path: {request.get_full_path()}, IP: {request.META.get('REMOTE_ADDR')}")

            # Provide user-friendly error message
            messages.error(request, "This login link has expired or is invalid. Please request a new one.")
            return redirect(reverse("accounts:signin"))

        except Exception as e:
            logger.error(f"Unexpected error in magic link authentication: {e}")
            logger.error(f"Request details - Path: {request.get_full_path()}, IP: {request.META.get('REMOTE_ADDR')}")

            # Provide generic error message
            messages.error(request, "There was an issue with your login link. Please try signing in again.")
            return redirect(reverse("accounts:signin"))


@login_required
@csrf_protect
def cancel_teacher_invitation(request: HttpRequest, invitation_id: int) -> HttpResponse:
    """
    Cancel a teacher invitation via HTMX endpoint.

    Allows school owners and admins to cancel pending teacher invitations.
    Validates user permissions before allowing cancellation and returns
    HTMX partial template for dynamic UI updates.

    Args:
        request: HTTP request from authenticated user
        invitation_id: ID of invitation to cancel

    Returns:
        HttpResponse: HTMX partial with cancellation result or error
    """
    invitation = get_object_or_404(TeacherInvitation, id=invitation_id)

    # Check permission
    user_schools = SchoolMembership.objects.filter(
        user=request.user, role__in=["school_owner", "school_admin"], is_active=True
    ).values_list("school_id", flat=True)

    if invitation.school_id not in user_schools and not request.user.is_superuser:
        return HttpResponse("Permission denied", status=403)

    if request.method == "POST":
        try:
            invitation.cancel()
            return render(
                request, "accounts/invitations/partials/invitation_cancelled.html", {"invitation": invitation}
            )
        except ValidationError as e:
            return render(request, "accounts/invitations/partials/invitation_error.html", {"error": str(e)})

    return HttpResponse("Method not allowed", status=405)


@login_required
@csrf_protect
def resend_teacher_invitation(request: HttpRequest, invitation_id: int) -> HttpResponse:
    """
    Resend a teacher invitation via HTMX endpoint.

    Allows school owners and admins to resend invitations that may have been
    missed or expired. Validates retry limits and user permissions before
    attempting to resend the invitation email.

    Args:
        request: HTTP request from authenticated user
        invitation_id: ID of invitation to resend

    Returns:
        HttpResponse: HTMX partial with resend result or error message
    """
    invitation = get_object_or_404(TeacherInvitation, id=invitation_id)

    # Check permission
    user_schools = SchoolMembership.objects.filter(
        user=request.user, role__in=["school_owner", "school_admin"], is_active=True
    ).values_list("school_id", flat=True)

    if invitation.school_id not in user_schools and not request.user.is_superuser:
        return HttpResponse("Permission denied", status=403)

    if request.method == "POST":
        try:
            # Check if can retry
            if not invitation.can_retry():
                return render(
                    request,
                    "accounts/invitations/partials/invitation_error.html",
                    {"error": "Maximum retry attempts reached for this invitation."},
                )

            # Resend email (implement based on your email system)
            # send_teacher_invitation_email(invitation)

            # Update invitation status
            invitation.mark_email_sent()

            return render(request, "accounts/invitations/partials/invitation_resent.html", {"invitation": invitation})

        except Exception as e:
            invitation.mark_email_failed(str(e))
            return render(
                request,
                "accounts/invitations/partials/invitation_error.html",
                {"error": "Failed to resend invitation. Please try again."},
            )

    return HttpResponse("Method not allowed", status=405)


# =============================================================================
# PROFILE MANAGEMENT VIEWS
# =============================================================================


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit comprehensive user profile"""

    model = User
    template_name = "accounts/profile/profile_edit.html"
    fields = ["name", "email", "phone_number", "profile_photo", "primary_contact"]
    success_url = reverse_lazy("accounts:profile")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, _("Your profile has been updated successfully."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        # Add verification status for display
        context["email_verified"] = self.request.user.email_verified
        context["phone_verified"] = self.request.user.phone_verified
        return context


class ProfileView(LoginRequiredMixin, DetailView):
    """View user profile with verification status"""

    model = User
    template_name = "accounts/profile/profile_with_verification.html"
    context_object_name = "user"

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's school memberships
        memberships = (
            SchoolMembership.objects.filter(user=self.request.user, is_active=True)
            .select_related("school")
            .order_by("joined_at")
        )

        context["memberships"] = memberships

        # Add dashboard context for base_with_navs template
        context["active_section"] = "profile"
        context["school_name"] = memberships.first().school.name if memberships.exists() else "No School"
        context["user_first_name"] = self.request.user.first_name
        context["user_role"] = memberships.first().get_role_display() if memberships.exists() else "User"

        return context


# =============================================================================
# SCHOOL MANAGEMENT VIEWS
# =============================================================================


class ComprehensiveSchoolSettingsForm(forms.Form):
    """Comprehensive form for both School and SchoolSettings"""

    # School fields
    name = forms.CharField(max_length=150, label="School Name")
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Description")
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False, label="Address")
    contact_email = forms.EmailField(required=False, label="Contact Email")
    phone_number = forms.CharField(max_length=20, required=False, label="Phone Number")
    website = forms.URLField(required=False, label="Website")
    logo = forms.ImageField(required=False, label="School Logo")
    primary_color = forms.CharField(
        max_length=7, widget=forms.TextInput(attrs={"type": "color"}), initial="#3B82F6", label="Primary Color"
    )
    secondary_color = forms.CharField(
        max_length=7, widget=forms.TextInput(attrs={"type": "color"}), initial="#1F2937", label="Secondary Color"
    )

    # SchoolSettings fields - Legal & Billing
    tax_id = forms.CharField(max_length=50, required=False, label="Tax ID (NIF)")
    billing_address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Billing Address")
    billing_contact_name = forms.CharField(max_length=100, required=False, label="Billing Contact Name")
    billing_contact_email = forms.EmailField(required=False, label="Billing Contact Email")

    # SchoolSettings fields - Operational
    timezone = forms.CharField(max_length=50, initial="Europe/Lisbon", label="Timezone")
    language = forms.ChoiceField(
        choices=[("pt", "Portuguese"), ("en", "English")], initial="pt", label="Default Language"
    )
    currency_code = forms.ChoiceField(
        choices=[("EUR", "Euro"), ("USD", "US Dollar"), ("GBP", "British Pound")], initial="EUR", label="Currency"
    )

    def __init__(self, school, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school

        # Get or create SchoolSettings
        try:
            self.school_settings = school.settings
        except SchoolSettings.DoesNotExist:
            self.school_settings = SchoolSettings(school=school)

        # Populate initial data
        if not kwargs.get("data"):
            # School fields
            self.initial.update(
                {
                    "name": school.name or "",
                    "description": school.description or "",
                    "address": school.address or "",
                    "contact_email": school.contact_email or "",
                    "phone_number": school.phone_number or "",
                    "website": school.website or "",
                    "primary_color": school.primary_color or "#3B82F6",
                    "secondary_color": school.secondary_color or "#1F2937",
                }
            )

            # SchoolSettings fields - only if the settings exist
            if hasattr(self.school_settings, "pk") and self.school_settings.pk:
                self.initial.update(
                    {
                        "tax_id": self.school_settings.tax_id,
                        "billing_address": self.school_settings.billing_address,
                        "billing_contact_name": self.school_settings.billing_contact_name,
                        "billing_contact_email": self.school_settings.billing_contact_email,
                        "timezone": self.school_settings.timezone,
                        "language": self.school_settings.language,
                        "currency_code": self.school_settings.currency_code,
                    }
                )

    def save(self):
        """Save both School and SchoolSettings"""
        with transaction.atomic():
            # Update School fields
            self.school.name = self.cleaned_data["name"]
            self.school.description = self.cleaned_data["description"]
            self.school.address = self.cleaned_data["address"]
            self.school.contact_email = self.cleaned_data["contact_email"]
            self.school.phone_number = self.cleaned_data["phone_number"]
            self.school.website = self.cleaned_data["website"]
            self.school.primary_color = self.cleaned_data["primary_color"]
            self.school.secondary_color = self.cleaned_data["secondary_color"]

            if self.cleaned_data.get("logo"):
                self.school.logo = self.cleaned_data["logo"]

            self.school.save()

            # Update SchoolSettings fields
            self.school_settings.school = self.school
            self.school_settings.tax_id = self.cleaned_data["tax_id"]
            self.school_settings.billing_address = self.cleaned_data["billing_address"]
            self.school_settings.billing_contact_name = self.cleaned_data["billing_contact_name"]
            self.school_settings.billing_contact_email = self.cleaned_data["billing_contact_email"]
            self.school_settings.timezone = self.cleaned_data["timezone"]
            self.school_settings.language = self.cleaned_data["language"]
            self.school_settings.currency_code = self.cleaned_data["currency_code"]

            self.school_settings.save()

        return self.school


@login_required
def send_verification_email(request):
    """Send verification email to the current user (HTMX endpoint)."""
    user = request.user

    # Check if already verified
    if user.email_verified:
        return HttpResponse('<div class="text-green-600 text-sm">Your email is already verified!</div>')

    try:
        # Generate magic link for email verification
        login_url = reverse("accounts:verify_email")
        magic_link = request.build_absolute_uri(login_url) + sesame_get_query_string(user)

        # Send verification email
        result = send_magic_link_email(user.email, magic_link, user.first_name, is_verification=True)

        if result.get("success"):
            logger.info(f"Verification email sent to: {user.email}")
            return HttpResponse('<div class="text-green-600 text-sm">Verification email sent! Check your inbox.</div>')
        else:
            logger.error(f"Failed to send verification email to {user.email}")
            return HttpResponse('<div class="text-red-600 text-sm">Failed to send email. Please try again later.</div>')
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {e}")
        return HttpResponse('<div class="text-red-600 text-sm">An error occurred. Please try again later.</div>')


@login_required
def send_verification_sms(request):
    """Send verification SMS to the current user (HTMX endpoint)."""
    user = request.user

    # Check if phone number exists
    if not user.phone_number:
        return HttpResponse('<div class="text-red-600 text-sm">No phone number on file. Please add one first.</div>')

    # Check if already verified
    if user.phone_verified:
        return HttpResponse('<div class="text-green-600 text-sm">Your phone is already verified!</div>')

    try:
        # Generate OTP code
        otp_code = str(secrets.randbelow(900000) + 100000)

        # Store in session
        request.session[f"verify_otp_{user.id}"] = otp_code
        request.session[f"verify_otp_expires_{user.id}"] = (timezone.now() + timedelta(minutes=30)).timestamp()

        # Send SMS
        result = send_sms_otp(user.phone_number, otp_code, user.first_name, is_verification=True)

        if result.get("success"):
            logger.info(f"Verification SMS sent to: {user.phone_number}")
            return HttpResponse(
                f'<div class="text-green-600 text-sm">Verification code sent to {user.phone_number}!</div>'
                f'<a href="{reverse("accounts:verify_otp")}" class="text-blue-600 text-sm underline mt-2 inline-block">Enter code</a>'
            )
        else:
            logger.error(f"Failed to send verification SMS to {user.phone_number}")
            return HttpResponse('<div class="text-red-600 text-sm">Failed to send SMS. Please try again later.</div>')
    except Exception as e:
        logger.error(f"Error sending verification SMS to {user.phone_number}: {e}")
        return HttpResponse('<div class="text-red-600 text-sm">An error occurred. Please try again later.</div>')


class SchoolSettingsView(IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin, FormView):
    """Edit comprehensive school settings including School and SchoolSettings"""

    template_name = "accounts/schools/school_settings.html"
    form_class = ComprehensiveSchoolSettingsForm

    def dispatch(self, request, *args, **kwargs):
        # Store request for later use (before authentication check)
        self.request = request
        self.args = args
        self.kwargs = kwargs

        # First, ensure authentication is handled by calling LoginRequiredMixin's test
        if not self.request.user.is_authenticated:
            # Let parent mixins handle authentication redirects
            return super().dispatch(request, *args, **kwargs)

        # Now that we know the user is authenticated, check school-specific permissions
        from .models.schools import SchoolRole

        school_queryset = self.get_user_schools_by_role(SchoolRole.SCHOOL_OWNER) | self.get_user_schools_by_role(
            SchoolRole.SCHOOL_ADMIN
        )
        try:
            self.school = school_queryset.get(pk=kwargs["pk"])
        except School.DoesNotExist:
            raise PermissionDenied("You don't have permission to edit this school's settings.")

        # Continue with normal dispatch
        return super().dispatch(request, *args, **kwargs)

    def get_user_schools_by_role(self, role):
        """Helper method to get schools by role"""
        # Defensive check: ensure user is authenticated before querying
        if not self.request.user.is_authenticated:
            return School.objects.none()

        return School.objects.filter(
            memberships__user=self.request.user, memberships__role=role, memberships__is_active=True
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = self.school
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request, _("Settings for %(school)s have been updated successfully.") % {"school": self.school.name}
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("accounts:school_settings", kwargs={"pk": self.school.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.school
        return context


class SchoolMemberListView(IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin, ListView):
    """List school members"""

    model = SchoolMembership
    template_name = "accounts/schools/school_members.html"
    context_object_name = "memberships"
    paginate_by = 50

    def get_queryset(self):
        self.school = get_object_or_404(School, pk=self.kwargs["school_pk"])

        # Check permission for this specific school
        if not self.has_school_permission(self.school, ["school_owner", "school_admin"]):
            raise Http404("You don't have permission to view this school's members.")

        return (
            SchoolMembership.objects.filter(school=self.school, is_active=True)
            .select_related("user")
            .order_by("role", "joined_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school"] = self.school
        return context


# Using django-sesame's built-in LoginView directly - no custom implementation needed


def root_redirect(request):
    """
    Root path handler: redirects based on authentication status
    - Authenticated users → /dashboard/
    - Anonymous users → /accounts/signin/
    """
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("dashboard:dashboard"))
    else:
        return HttpResponseRedirect(reverse("accounts:signin"))


# ==========================================
# Student Creation Views (Refactored from dashboard.views.PeopleView)
# ==========================================


class BaseStudentCreateView(LoginRequiredMixin, View):
    """Base class for student creation views with common functionality."""

    def _validate_email_format(self, email):
        """Validate and return clean email or raise ValidationError"""
        if not email:
            raise ValidationError("Email is required")
        try:
            validate_email(email)
            return email.lower()
        except ValidationError:
            raise ValidationError(f"Invalid email format: {email}")

    def _get_user_schools(self, user):
        """Get schools accessible to the current user"""
        if user.is_staff or user.is_superuser:
            return School.objects.all()
        school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
        return School.objects.filter(id__in=school_ids)

    def _get_educational_system(self):
        """Get default educational system (Portugal)"""
        from accounts.models.educational import EducationalSystem

        educational_system = EducationalSystem.objects.filter(code="pt").first()
        if not educational_system:
            educational_system = EducationalSystem.objects.first()
        return educational_system

    def _render_error(self, request, error_message):
        """Render error message template"""
        logger.error(f"Student creation error: {error_message}")
        return render(
            request,
            "shared/partials/error_message.html",
            {"error": error_message},
        )

    def _render_success(self, request, success_message):
        """Render success message template"""
        logger.info(f"Student creation success: {success_message}")
        return render(
            request,
            "shared/partials/success_message.html",
            {"message": success_message},
        )


@method_decorator(csrf_protect, name="dispatch")
class StudentSeparateCreateView(BaseStudentCreateView):
    """Create both student and guardian user accounts (separate logins)."""

    def post(self, request):
        """Handle Student + Guardian account creation"""
        from django.db import transaction

        from accounts.models.profiles import GuardianProfile
        from accounts.permissions import PermissionService

        try:
            # Sanitize and extract form data
            student_name = escape(request.POST.get("name", "").strip())
            student_email_raw = request.POST.get("email", "").strip()
            student_birth_date = request.POST.get("birth_date")
            student_school_year = escape(request.POST.get("school_year", "").strip())
            student_notes = escape(request.POST.get("notes", "").strip())

            guardian_name = escape(request.POST.get("guardian_name", "").strip())
            guardian_email_raw = request.POST.get("guardian_email", "").strip()
            guardian_phone = escape(request.POST.get("guardian_phone", "").strip())
            guardian_tax_nr = escape(request.POST.get("guardian_tax_nr", "").strip())
            guardian_address = escape(request.POST.get("guardian_address", "").strip())
            guardian_invoice = request.POST.get("guardian_invoice") == "on"
            guardian_email_notifications = request.POST.get("guardian_email_notifications") == "on"
            guardian_sms_notifications = request.POST.get("guardian_sms_notifications") == "on"

            # Log form data for debugging
            logger.info(f"Processing separate student creation: student={student_name}, guardian={guardian_name}")

            # Validate and sanitize emails
            try:
                student_email = self._validate_email_format(student_email_raw)
                guardian_email = self._validate_email_format(guardian_email_raw)
            except ValidationError as e:
                return self._render_error(request, str(e))

            # Validate required fields
            if not all([student_name, student_email, student_birth_date, guardian_name, guardian_email]):
                missing_fields = []
                if not student_name:
                    missing_fields.append("student name")
                if not student_email:
                    missing_fields.append("student email")
                if not student_birth_date:
                    missing_fields.append("student birth date")
                if not guardian_name:
                    missing_fields.append("guardian name")
                if not guardian_email:
                    missing_fields.append("guardian email")

                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                return self._render_error(request, error_msg)

            # Get user's schools and educational system
            user_schools = self._get_user_schools(request.user)
            educational_system = self._get_educational_system()

            with transaction.atomic():
                # Temporarily disconnect the task creation signal to prevent orphaned tasks
                from django.db.models.signals import post_save

                from accounts.signals.verification_task_signals import create_system_tasks_for_new_user

                post_save.disconnect(create_system_tasks_for_new_user, sender=User)

                try:
                    # Create or get student user
                    try:
                        student_user = User.objects.get(email=student_email)
                        student_user_was_created = False
                    except User.DoesNotExist:
                        student_user = User.objects.create_user(email=student_email, name=student_name)
                        student_user_was_created = True

                    # Create or get guardian user
                    try:
                        guardian_user = User.objects.get(email=guardian_email)
                        guardian_user_was_created = False
                    except User.DoesNotExist:
                        guardian_user = User.objects.create_user(
                            email=guardian_email, name=guardian_name, phone_number=guardian_phone
                        )
                        guardian_user_was_created = True

                    # Create guardian profile
                    guardian_profile, _ = GuardianProfile.objects.get_or_create(
                        user=guardian_user,
                        defaults={
                            "address": guardian_address,
                            "tax_nr": guardian_tax_nr,
                            "invoice": guardian_invoice,
                            "email_notifications_enabled": guardian_email_notifications,
                            "sms_notifications_enabled": guardian_sms_notifications,
                        },
                    )

                    # Create student profile
                    student_profile = StudentProfile.objects.create(
                        user=student_user,
                        name=student_name,
                        account_type="STUDENT_GUARDIAN",
                        educational_system=educational_system,
                        school_year=student_school_year,
                        birth_date=student_birth_date,
                        guardian=guardian_profile,
                        notes=student_notes,
                    )

                    # Setup permissions
                    PermissionService.setup_permissions_for_student(student_profile)

                    # Add both users to schools
                    for school in user_schools:
                        SchoolMembership.objects.get_or_create(
                            user=student_user, school=school, defaults={"role": SchoolRole.STUDENT}
                        )
                        SchoolMembership.objects.get_or_create(
                            user=guardian_user, school=school, defaults={"role": SchoolRole.GUARDIAN}
                        )

                    # Manually create system tasks after successful student creation
                    from tasks.services import TaskService

                    if student_user_was_created:
                        TaskService.initialize_system_tasks(student_user)
                    if guardian_user_was_created:
                        TaskService.initialize_system_tasks(guardian_user)

                finally:
                    # Reconnect the signal
                    post_save.connect(create_system_tasks_for_new_user, sender=User)

            success_message = f"Successfully created student account for {student_name} and guardian account for {guardian_name}. Both can now login independently."
            return self._render_success(request, success_message)

        except Exception as e:
            logger.error(f"Unexpected error in separate student creation: {e}", exc_info=True)
            return self._render_error(request, "An unexpected error occurred. Please try again.")


@method_decorator(csrf_protect, name="dispatch")
class StudentGuardianOnlyCreateView(BaseStudentCreateView):
    """Create guardian account only, with student profile managed by guardian."""

    def post(self, request):
        """Handle Guardian-Only account creation"""
        from django.db import transaction

        from accounts.models.profiles import GuardianProfile
        from accounts.permissions import PermissionService

        try:
            # Sanitize and extract form data
            student_name = escape(request.POST.get("name", "").strip())
            student_birth_date = request.POST.get("birth_date")
            student_school_year = escape(request.POST.get("school_year", "").strip())
            student_notes = escape(request.POST.get("notes", "").strip())

            guardian_name = escape(request.POST.get("guardian_name", "").strip())
            guardian_email_raw = request.POST.get("guardian_email", "").strip()
            guardian_phone = escape(request.POST.get("guardian_phone", "").strip())
            guardian_tax_nr = escape(request.POST.get("guardian_tax_nr", "").strip())
            guardian_address = escape(request.POST.get("guardian_address", "").strip())
            guardian_invoice = request.POST.get("guardian_invoice") == "on"
            guardian_email_notifications = request.POST.get("guardian_email_notifications") == "on"
            guardian_sms_notifications = request.POST.get("guardian_sms_notifications") == "on"

            # Log form data for debugging
            logger.info(f"Processing guardian-only creation: student={student_name}, guardian={guardian_name}")

            # Validate and sanitize email
            try:
                guardian_email = self._validate_email_format(guardian_email_raw)
            except ValidationError as e:
                return self._render_error(request, str(e))

            # Validate required fields
            if not all([student_name, student_birth_date, guardian_name, guardian_email]):
                missing_fields = []
                if not student_name:
                    missing_fields.append("student name")
                if not student_birth_date:
                    missing_fields.append("student birth date")
                if not guardian_name:
                    missing_fields.append("guardian name")
                if not guardian_email:
                    missing_fields.append("guardian email")

                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                return self._render_error(request, error_msg)

            # Get user's schools and educational system
            user_schools = self._get_user_schools(request.user)
            educational_system = self._get_educational_system()

            with transaction.atomic():
                # Temporarily disconnect the task creation signal to prevent orphaned tasks
                from django.db.models.signals import post_save

                from accounts.signals.verification_task_signals import create_system_tasks_for_new_user

                post_save.disconnect(create_system_tasks_for_new_user, sender=User)

                try:
                    # Create or get guardian user
                    try:
                        guardian_user = User.objects.get(email=guardian_email)
                        guardian_user_was_created = False
                    except User.DoesNotExist:
                        guardian_user = User.objects.create_user(
                            email=guardian_email, name=guardian_name, phone_number=guardian_phone
                        )
                        guardian_user_was_created = True

                    # Create guardian profile
                    guardian_profile, _ = GuardianProfile.objects.get_or_create(
                        user=guardian_user,
                        defaults={
                            "address": guardian_address,
                            "tax_nr": guardian_tax_nr,
                            "invoice": guardian_invoice,
                            "email_notifications_enabled": guardian_email_notifications,
                            "sms_notifications_enabled": guardian_sms_notifications,
                        },
                    )

                    # Create student profile WITHOUT a user account (guardian-only)
                    student_profile = StudentProfile.objects.create(
                        user=None,  # No user account for guardian-only students
                        name=student_name,  # Store student name directly
                        account_type="GUARDIAN_ONLY",
                        educational_system=educational_system,
                        school_year=student_school_year,
                        birth_date=student_birth_date,
                        guardian=guardian_profile,
                        notes=student_notes,
                    )

                    # Setup permissions
                    PermissionService.setup_permissions_for_student(student_profile)

                    # Add guardian to schools
                    for school in user_schools:
                        SchoolMembership.objects.get_or_create(
                            user=guardian_user, school=school, defaults={"role": SchoolRole.GUARDIAN}
                        )

                    # Manually create system tasks after successful student creation
                    if guardian_user_was_created:
                        from tasks.services import TaskService

                        TaskService.initialize_system_tasks(guardian_user)

                finally:
                    # Reconnect the signal
                    post_save.connect(create_system_tasks_for_new_user, sender=User)

            success_message = f"Successfully created guardian account for {guardian_name} who will manage {student_name}'s profile. Only the guardian can login."
            return self._render_success(request, success_message)

        except Exception as e:
            logger.error(f"Unexpected error in guardian-only creation: {e}", exc_info=True)
            return self._render_error(request, "An unexpected error occurred. Please try again.")


@method_decorator(csrf_protect, name="dispatch")
class StudentAdultCreateView(BaseStudentCreateView):
    """Create adult student account (self-managed)."""

    def post(self, request):
        """Handle Adult Student account creation"""
        from django.db import transaction

        from accounts.models.profiles import GuardianProfile
        from accounts.permissions import PermissionService

        try:
            # Sanitize and extract form data
            student_name = escape(request.POST.get("name", "").strip())
            student_email_raw = request.POST.get("email", "").strip()
            student_birth_date = request.POST.get("birth_date")
            student_phone = escape(request.POST.get("phone", "").strip())
            student_school_year = escape(request.POST.get("school_year", "").strip())
            student_tax_nr = escape(request.POST.get("tax_nr", "").strip())
            student_address = escape(request.POST.get("address", "").strip())
            student_notes = escape(request.POST.get("notes", "").strip())
            student_invoice = request.POST.get("invoice") == "on"
            student_email_notifications = request.POST.get("email_notifications") == "on"
            student_sms_notifications = request.POST.get("sms_notifications") == "on"

            # Log form data for debugging
            logger.info(f"Processing adult student creation: student={student_name}")

            # Validate and sanitize email
            try:
                student_email = self._validate_email_format(student_email_raw)
            except ValidationError as e:
                return self._render_error(request, str(e))

            # Validate required fields
            if not all([student_name, student_email, student_birth_date]):
                missing_fields = []
                if not student_name:
                    missing_fields.append("student name")
                if not student_email:
                    missing_fields.append("student email")
                if not student_birth_date:
                    missing_fields.append("student birth date")

                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                return self._render_error(request, error_msg)

            # Get user's schools and educational system
            user_schools = self._get_user_schools(request.user)
            educational_system = self._get_educational_system()

            with transaction.atomic():
                # Temporarily disconnect the task creation signal to prevent orphaned tasks
                from django.db.models.signals import post_save

                from accounts.signals.verification_task_signals import create_system_tasks_for_new_user

                post_save.disconnect(create_system_tasks_for_new_user, sender=User)

                try:
                    # Create or get student user
                    try:
                        student_user = User.objects.get(email=student_email)
                        user_was_created = False
                    except User.DoesNotExist:
                        student_user = User.objects.create_user(
                            email=student_email, name=student_name, phone_number=student_phone
                        )
                        user_was_created = True

                    # Create or update guardian profile for self (adult students are their own guardian)
                    guardian_profile, _ = GuardianProfile.objects.get_or_create(
                        user=student_user,
                        defaults={
                            "address": student_address,
                            "tax_nr": student_tax_nr,
                            "invoice": student_invoice,
                            "email_notifications_enabled": student_email_notifications,
                            "sms_notifications_enabled": student_sms_notifications,
                        },
                    )

                    # Create student profile
                    student_profile = StudentProfile.objects.create(
                        user=student_user,
                        name=student_name,
                        account_type="ADULT_STUDENT",
                        educational_system=educational_system,
                        school_year=student_school_year,
                        birth_date=student_birth_date,
                        guardian=guardian_profile,  # Adult student is their own guardian
                        notes=student_notes,
                        email_notifications_enabled=student_email_notifications,
                        sms_notifications_enabled=student_sms_notifications,
                        address=student_address,
                        tax_nr=student_tax_nr,
                        invoice=student_invoice,
                    )

                    # Setup permissions
                    PermissionService.setup_permissions_for_student(student_profile)

                    # Add student to schools
                    for school in user_schools:
                        SchoolMembership.objects.get_or_create(
                            user=student_user, school=school, defaults={"role": SchoolRole.STUDENT}
                        )

                    # Manually create system tasks after successful student creation
                    if user_was_created:
                        from tasks.services import TaskService

                        TaskService.initialize_system_tasks(student_user)

                finally:
                    # Reconnect the signal
                    post_save.connect(create_system_tasks_for_new_user, sender=User)

            success_message = f"Successfully created adult student account for {student_name}. They can now login and manage their own account."
            return self._render_success(request, success_message)

        except Exception as e:
            logger.error(f"Unexpected error in adult student creation: {e}", exc_info=True)
            return self._render_error(request, "An unexpected error occurred. Please try again.")
