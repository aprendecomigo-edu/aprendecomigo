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
from django.db import models, transaction
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView
from sesame.utils import get_query_string, get_query_string as sesame_get_query_string
from sesame.views import LoginView as SesameLoginView
from waffle import switch_is_active

from messaging.services import send_magic_link_email, send_otp_email_message, send_sms_otp

from .db_queries import create_user_school_and_membership, get_user_by_email, user_exists
from .models import School, SchoolMembership, SchoolSettings, TeacherInvitation
from .models.profiles import StudentProfile
from .models.schools import SchoolRole
from .permissions import IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin
from .services.otp_service import OTPService

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
    Handle user sign-in with OTP delivery choice.

    New flow:
    1. User enters email
    2. System shows delivery choice based on verified methods
    3. User chooses email or SMS delivery
    4. OTP is sent and verified
    """

    def get(self, request) -> HttpResponse:
        """Render sign-in page for unauthenticated users."""
        if request.user.is_authenticated:
            return redirect(reverse("dashboard:dashboard"))

        # Store the next parameter in session for post-login redirect (with security validation)
        next_url = request.GET.get("next")
        if (
            next_url
            and next_url.strip()
            and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            )
        ):
            request.session["signin_next_url"] = next_url

        return render(
            request,
            "accounts/signin.html",
            {
                "title": "Sign In - Aprende Comigo",
                "meta_description": "Sign in to your Aprende Comigo account",
                "sms_enabled": switch_is_active("sms_feature"),
            },
        )

    @method_decorator(csrf_protect)
    def post(self, request):
        """
        Simplified handler for sign-in form submission.
        Since the consolidated form now handles both email input and delivery choice on one page,
        this method just renders the form with any provided email value.
        All validation and user verification is now handled by send_otp_email and send_otp_sms.
        """
        email = request.POST.get("email", "").strip().lower()

        # Simply render the consolidated signin form
        return render(
            request,
            "accounts/partials/signin_form.html",
            {
                "email": email,
                "sms_enabled": switch_is_active("sms_feature"),
            },
        )


@require_http_methods(["POST"])
@csrf_protect
def send_otp_email(request):
    """Send OTP via email for signin"""
    email = request.POST.get("email", "").strip().lower()
    logger.info(f"[SIGNIN] OTP email request for: {email}")

    # Validate email
    if not email:
        return render(
            request,
            "accounts/partials/signin_form.html",
            {
                "error": "Please enter your email address",
                "email": email,
                "sms_enabled": switch_is_active("sms_feature"),
            },
        )

    if not re.match(EMAIL_REGEX, email):
        return render(
            request,
            "accounts/partials/signin_form.html",
            {
                "error": "Please enter a valid email address",
                "email": email,
                "sms_enabled": switch_is_active("sms_feature"),
            },
        )

    try:
        # Check if user exists and is verified
        if not user_exists(email):
            logger.warning(f"OTP email attempt with unregistered email: {email}")
            return render(
                request,
                "accounts/partials/signin_form.html",
                {
                    "error": "Invalid email or account not verified",
                    "email": email,
                    "sms_enabled": switch_is_active("sms_feature"),
                },
            )

        user = get_user_by_email(email)

        # Check if user's email is verified
        if not user.email_verified:
            logger.warning(f"OTP email attempt with unverified email: {email}")
            return render(
                request,
                "accounts/partials/signin_form.html",
                {
                    "error": "Please verify your email address first",
                    "email": email,
                    "sms_enabled": switch_is_active("sms_feature"),
                },
            )

        # Store email and user_id in session for OTP verification
        request.session["signin_email"] = email
        request.session["signin_user_id"] = user.id

        # Generate OTP
        otp_code, token_id = OTPService.generate_otp(user, "email")

        # Send via email
        result = send_otp_email_message(user.email, otp_code, user.first_name)

        if result.get("success"):
            # Store token ID in session for verification
            request.session["otp_token_id"] = token_id
            request.session["otp_delivery_method"] = "email"

            logger.info(f"OTP sent via email to: {email}")
            return render(
                request,
                "accounts/partials/signin_success_with_verify.html",
                {
                    "delivery_method": "email",
                    "masked_contact": f"{email[:3]}***{email[email.index('@') :]}",
                    "email": email,
                },
            )
        else:
            return render(
                request,
                "accounts/partials/signin_form.html",
                {
                    "error": "Failed to send email. Please try again later.",
                    "email": email,
                    "sms_enabled": switch_is_active("sms_feature"),
                },
            )
    except Exception as e:
        logger.error(f"Error in send_otp_email for {email}: {e!s}")
        return render(
            request,
            "accounts/partials/signin_form.html",
            {
                "error": "An error occurred. Please try again later.",
                "email": email,
                "sms_enabled": switch_is_active("sms_feature"),
            },
        )


@require_http_methods(["POST"])
@csrf_protect
def send_otp_sms(request):
    """Send OTP via SMS for signin"""
    # Check if SMS feature is enabled
    if not switch_is_active("sms_feature"):
        return render(
            request,
            "accounts/partials/signin_form.html",
            {
                "error": "SMS service is temporarily unavailable. Please use email instead.",
                "email": request.POST.get("email", ""),
                "sms_enabled": False,
            },
        )

    email = request.POST.get("email", "").strip().lower()
    logger.info(f"[SIGNIN] OTP SMS request for: {email}")

    # Validate email
    if not email:
        return render(
            request,
            "accounts/partials/signin_form.html",
            {
                "error": "Please enter your email address",
                "email": email,
                "sms_enabled": switch_is_active("sms_feature"),
            },
        )

    if not re.match(EMAIL_REGEX, email):
        return render(
            request,
            "accounts/partials/signin_form.html",
            {
                "error": "Please enter a valid email address",
                "email": email,
                "sms_enabled": switch_is_active("sms_feature"),
            },
        )

    try:
        # Check if user exists and is verified
        if not user_exists(email):
            logger.warning(f"OTP SMS attempt with unregistered email: {email}")
            return render(
                request,
                "accounts/partials/signin_form.html",
                {
                    "error": "Invalid email or account not verified",
                    "email": email,
                    "sms_enabled": switch_is_active("sms_feature"),
                },
            )

        user = get_user_by_email(email)

        # Check if user's email is verified
        if not user.email_verified:
            logger.warning(f"OTP SMS attempt with unverified email: {email}")
            return render(
                request,
                "accounts/partials/signin_form.html",
                {
                    "error": "Please verify your email address first",
                    "email": email,
                    "sms_enabled": switch_is_active("sms_feature"),
                },
            )

        # Check if phone is verified
        if not user.phone_verified or not user.phone_number:
            return render(
                request,
                "accounts/partials/signin_form.html",
                {
                    "error": "Phone not verified. Please choose email or verify your phone first.",
                    "email": email,
                    "sms_enabled": switch_is_active("sms_feature"),
                },
            )

        # Store email and user_id in session for OTP verification
        request.session["signin_email"] = email
        request.session["signin_user_id"] = user.id

        # Generate OTP
        otp_code, token_id = OTPService.generate_otp(user, "sms")

        # Send via SMS
        result = send_sms_otp(user.phone_number, otp_code, user.first_name)

        if result.get("success"):
            # Store token ID in session for verification
            request.session["otp_token_id"] = token_id
            request.session["otp_delivery_method"] = "sms"

            logger.info(f"OTP sent via SMS to: {user.phone_number}")
            return render(
                request,
                "accounts/partials/signin_success_with_verify.html",
                {
                    "delivery_method": "sms",
                    "masked_contact": f"***{user.phone_number[-4:]}",
                    "email": email,
                },
            )
        else:
            return render(
                request,
                "accounts/partials/signin_form.html",
                {
                    "error": "Failed to send SMS. Please try email or try again later.",
                    "email": email,
                    "sms_enabled": switch_is_active("sms_feature"),
                },
            )
    except Exception as e:
        logger.error(f"Error in send_otp_sms for {email}: {e!s}")
        return render(
            request,
            "accounts/partials/signin_form.html",
            {
                "error": "An error occurred. Please try again later.",
                "email": email,
                "sms_enabled": switch_is_active("sms_feature"),
            },
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

        # Helper function to get safe context for template rendering
        # Note: Only escape values for display, not for business logic
        def get_safe_context(error_msg):
            return {
                "error": error_msg,
                "email": escape(email),
                "full_name": escape(full_name),
                "phone_number": escape(phone_number),
                "organization_name": escape(organization_name),
            }

        # Validate inputs
        if not email:
            return render(
                request,
                "accounts/partials/signup_form.html",
                get_safe_context("Email is required"),
            )

        if not full_name:
            return render(
                request,
                "accounts/partials/signup_form.html",
                get_safe_context("Full name is required"),
            )

        if not phone_number:
            return render(
                request,
                "accounts/partials/signup_form.html",
                get_safe_context("Phone number is required"),
            )

        if not organization_name:
            return render(
                request,
                "accounts/partials/signup_form.html",
                get_safe_context("Organization name is required"),
            )

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return render(
                request,
                "accounts/partials/signup_form.html",
                get_safe_context("Please enter a valid email address"),
            )

        # Check for duplicates (email OR phone) using phone validation service
        from accounts.services.phone_validation import PhoneValidationService

        try:
            phone_normalized = PhoneValidationService.validate_and_normalize(phone_number)
        except ValidationError as e:
            return render(
                request,
                "accounts/partials/signup_form.html",
                get_safe_context(str(e)),
            )

        if User.objects.filter(models.Q(email=email) | models.Q(phone_number_normalized=phone_normalized)).exists():
            return render(
                request,
                "accounts/partials/signup_form.html",
                get_safe_context("Account with this email or phone already exists"),
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

                # Send verification emails/SMS asynchronously (UPDATE THIS PART)
                try:
                    # Generate SEPARATE magic links for email and phone verification
                    email_verify_url = reverse("accounts:verify_email")
                    phone_verify_url = reverse("accounts:verify_phone")

                    email_magic_link = request.build_absolute_uri(email_verify_url) + get_query_string(user)
                    phone_magic_link = request.build_absolute_uri(phone_verify_url) + get_query_string(user)

                    # Send email verification (non-blocking)
                    send_magic_link_email(email, email_magic_link, first_name, is_verification=True)
                    logger.info(f"Email verification link sent to: {email}")

                    # Send SMS verification (non-blocking) - only if SMS feature is enabled
                    if phone_number and switch_is_active("sms_feature"):
                        from messaging.services import send_verification_sms

                        send_verification_sms(phone_number, phone_magic_link, first_name)
                        logger.info(f"SMS verification link sent to: {phone_number}")
                    elif phone_number and not switch_is_active("sms_feature"):
                        logger.info(f"SMS verification skipped for {phone_number} - SMS feature disabled")

                except Exception as e:
                    logger.error(f"Error sending verification messages to {email}: {e}")
                    # Don't fail signup if verification sending fails

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
                get_safe_context("There was an issue creating your account. Please try again."),
            )


class VerifyOTPView(View):
    """
    Handle OTP verification for signin flow.

    Validates the OTP code and logs the user in with appropriate session duration.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render OTP input page if session is valid"""
        token_id = request.session.get("otp_token_id")
        delivery_method = request.session.get("otp_delivery_method")

        if not token_id or not delivery_method:
            return redirect(reverse("accounts:signin"))

        # Get masked contact info for display
        if delivery_method == "email":
            email = request.session.get("signin_email", "")
            masked_contact = f"{email[:3]}***{email[email.index('@') :] if '@' in email else ''}"
        else:  # SMS
            user_id = request.session.get("signin_user_id")
            try:
                user = User.objects.get(id=user_id)
                masked_contact = f"***{user.phone_number[-4:] if user.phone_number else '****'}"
            except Exception:
                masked_contact = "***"

        return render(
            request,
            "accounts/verify_otp.html",
            {
                "title": "Enter Verification Code - Aprende Comigo",
                "delivery_method": delivery_method,
                "masked_contact": masked_contact,
            },
        )

    @method_decorator(csrf_protect)
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Handle OTP verification for signin flows using OTPService.

        Returns: HTMX partial template with success or error message
        """
        from .services.otp_service import OTPService

        otp_code = request.POST.get("verification_code", "").strip()

        # Get session data for signin flow
        token_id = request.session.get("otp_token_id")
        email = request.session.get("signin_email")
        delivery_method = request.session.get("otp_delivery_method")

        if not token_id or not otp_code:
            return render(
                request,
                "accounts/partials/signin_success_with_verify.html",
                {
                    "error": "Please enter the verification code.",
                    "email": email,
                    "delivery_method": delivery_method,
                },
            )

        # Verify OTP using OTPService
        success, result = OTPService.verify_otp(token_id, otp_code)

        if success:
            user = result
            # Log user in for signin flow
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            logger.info(f"OTP authentication successful for user: {user.email}")

            # Mark email as verified if using email delivery
            if delivery_method == "email" and not user.email_verified:
                user.email_verified = True
                user.save(update_fields=["email_verified"])
                logger.info(f"Email verification completed via OTP for user: {user.email}")

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

            # Get next URL from session or default to dashboard
            next_url = request.session.get("signin_next_url") or reverse("dashboard:dashboard")

            # Clean up session
            if "otp_token_id" in request.session:
                del request.session["otp_token_id"]
            if "otp_delivery_method" in request.session:
                del request.session["otp_delivery_method"]
            if "signin_email" in request.session:
                del request.session["signin_email"]
            if "signin_user_id" in request.session:
                del request.session["signin_user_id"]
            if "signin_next_url" in request.session:
                del request.session["signin_next_url"]

            # Clean up unverified user session markers after successful OTP verification
            if "is_unverified_user" in request.session:
                del request.session["is_unverified_user"]
            if "unverified_until" in request.session:
                del request.session["unverified_until"]

            # Reset session expiry to default (consistent with VerificationCompletionMiddleware)
            request.session.set_expiry(0)  # Use default session length

            # Redirect to next URL or dashboard
            return HttpResponse(
                status=200,
                headers={"HX-Redirect": next_url},
            )
        else:
            # Verification failed
            error_message = result
            return render(
                request,
                "accounts/partials/signin_success_with_verify.html",
                {
                    "error": error_message,
                    "email": email,
                    "delivery_method": delivery_method,
                },
            )


# Function for resending verification code via HTMX
@csrf_protect
def resend_code(request: HttpRequest) -> HttpResponse:
    """
    Resend OTP code via email or SMS using OTPService.

    Args:
        request: HTTP request with session containing signin data

    Returns:
        HttpResponse: HTMX partial with new OTP form or error message
    """
    from messaging.services import send_otp_email_message

    from .services.otp_service import OTPService

    email = request.session.get("signin_email")
    user_id = request.session.get("signin_user_id")
    delivery_method = request.session.get("otp_delivery_method", "email")

    if not email or not user_id:
        logger.warning("Resend code attempted with missing session data")
        return render(
            request,
            "accounts/partials/signin_success_with_verify.html",
            {
                "error": "Your session has expired. Please sign in again to receive a new verification code.",
                "email": email or "",
                "delivery_method": delivery_method,
                "session_expired": True,
            },
        )

    try:
        user = User.objects.get(id=user_id, email=email)

        # Generate new OTP
        otp_code, token_id = OTPService.generate_otp(user, delivery_method)

        # Send OTP based on delivery method
        if delivery_method == "email":
            result = send_otp_email_message(user.email, otp_code, user.first_name)
        else:
            # SMS sending would go here
            result = {"success": False, "error": "SMS not yet implemented"}

        if result.get("success"):
            # Update session with new token
            request.session["otp_token_id"] = token_id
            logger.info(f"OTP resent successfully via {delivery_method} to: {email}")

            # Return the OTP input form again
            return render(
                request,
                "accounts/partials/signin_success_with_verify.html",
                {
                    "delivery_method": delivery_method,
                    "masked_contact": f"{email[:3]}***{email[email.index('@') :]}",
                    "email": email,
                    "message": "A new verification code has been sent.",
                },
            )
        else:
            error_msg = result.get("error", "Failed to resend verification code.")
            logger.error(f"Failed to resend OTP to {email}: {error_msg}")
            return render(
                request,
                "accounts/partials/signin_success_with_verify.html",
                {
                    "error": error_msg,
                    "email": email,
                    "delivery_method": delivery_method,
                },
            )

    except User.DoesNotExist:
        logger.error(f"User not found for resend code: {email} (ID: {user_id})")
        return render(
            request,
            "accounts/partials/signin_success_with_verify.html",
            {
                "error": "User account not found. Please sign in again.",
                "email": email,
                "delivery_method": delivery_method,
                "session_expired": True,
            },
        )
    except Exception as e:
        logger.error(f"Resend code error for {email}: {e}")
        return render(
            request,
            "accounts/partials/signin_success_with_verify.html",
            {
                "error": "There was an issue resending the verification code. Please try again.",
                "email": email,
                "delivery_method": delivery_method,
            },
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


class EmailVerificationView(SesameLoginView):
    """Handle email verification via magic link"""

    def login_success(self):
        """Mark email as verified and redirect to dashboard with success message"""
        user = self.request.user

        if not user.email_verified:
            user.email_verified = True
            user.email_verified_at = timezone.now()
            user.save(update_fields=["email_verified", "email_verified_at"])

            messages.success(self.request, "✅ Email verified successfully!")
            logger.info(f"Email verified for user: {user.email}")

            # Log email confirmation success
            log_email_confirmation_success(user.email)
        else:
            messages.info(self.request, "Your email is already verified!")

        # Handle redirect directly to avoid 403 from parent class
        return self._handle_verification_success_redirect()

    def _handle_verification_success_redirect(self):
        """Handle post-verification redirect with success UX"""
        # Create success page with auto-redirect to dashboard
        context = {
            "verification_type": "email",
            "redirect_url": reverse("dashboard:dashboard"),
            "success_message": "Your email has been successfully verified!",
        }
        return render(self.request, "accounts/partials/verify_success.html", context)


class PhoneVerificationView(SesameLoginView):
    """Handle phone verification via magic link"""

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"PhoneVerificationView.dispatch called - URL: {request.get_full_path()}")
        logger.info(f"PhoneVerificationView.dispatch called - GET params: {request.GET}")
        logger.info(f"PhoneVerificationView.dispatch called - METHOD: {request.method}")

        # Check if this is a redirect by looking at HTTP_REFERER
        referer = request.headers.get("referer")
        if referer:
            logger.info(f"PhoneVerificationView.dispatch called - REFERER: {referer}")

        response = super().dispatch(request, *args, **kwargs)

        # Log the response status
        logger.info(f"PhoneVerificationView.dispatch response status: {response.status_code}")
        if hasattr(response, "url"):
            logger.info(f"PhoneVerificationView.dispatch response redirect to: {response.url}")

        return response

    def get_user(self, request):
        """Override to add debugging for sesame authentication"""
        logger.info("PhoneVerificationView.get_user called")
        logger.info(f"PhoneVerificationView.get_user - sesame token: {request.GET.get('sesame', 'NO TOKEN')}")
        try:
            user = super().get_user(request)
            logger.info(f"PhoneVerificationView.get_user success: {user}")
            return user
        except Exception as e:
            logger.error(f"PhoneVerificationView.get_user failed: {e}")
            raise

    def login_failure(self, request):
        logger.error("PhoneVerificationView.login_failure called - sesame authentication failed")
        messages.error(request, "Phone verification link is invalid or expired.")
        return redirect(reverse("accounts:signin"))

    def login_success(self):
        """Mark phone as verified and log user in"""
        # Access request and user from the view instance
        user = self.request.user
        logger.info(f"PhoneVerificationView.login_success called for user: {user.email}")
        logger.info(f"Phone verified before: {user.phone_verified}")

        if not user.phone_verified:
            user.phone_verified = True
            user.phone_verified_at = timezone.now()
            user.save(update_fields=["phone_verified", "phone_verified_at"])

            logger.info(f"Phone verified after save: {user.phone_verified}")
            messages.success(self.request, "✅ Phone verified successfully!")
            logger.info(f"Phone verified for user: {user.email}")
        else:
            messages.info(self.request, "Your phone is already verified!")

        # Let the parent class handle the redirect properly
        logger.info("PhoneVerificationView.login_success delegating to parent class")
        return super().login_success()


class CustomMagicLoginView(SesameLoginView):
    """
    Custom magic link login view with enhanced error handling and logging.

    This handles magic link logins for signin (not verification).
    For verification, use EmailVerificationView or PhoneVerificationView.
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

    def login_success(self):
        """Override to add verification check for signin magic links"""
        # Access request and user from the view instance
        user = self.request.user
        # This is for signin, not verification, so check if user is verified
        if not (user.email_verified or user.phone_verified):
            messages.error(self.request, "Please verify your email or phone number before signing in.")
            return redirect(reverse("accounts:signin"))

        # User is verified, proceed with login
        logger.info(f"Successful magic link signin for verified user: {user.email}")
        return super().login_success()


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
        context["sms_enabled"] = switch_is_active("sms_feature")

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
    # Check if SMS feature is enabled
    if not switch_is_active("sms_feature"):
        return HttpResponse(
            '<div class="text-red-600 text-sm">SMS service is temporarily unavailable. Please try again later.</div>'
        )

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


@require_http_methods(["POST"])
@csrf_protect
def resend_verification_email_signin(request):
    """
    Resend verification email for unverified users during signin flow (HTMX endpoint).

    This endpoint is for users who are not logged in yet but trying to sign in
    with an unverified account. It looks up the user by email from POST data.
    """
    email = request.POST.get("email", "").strip().lower()

    if not email:
        return HttpResponse('<div class="text-red-600 text-sm">Email address is required.</div>')

    try:
        # Validate email format
        from django.core.validators import validate_email

        validate_email(email)
    except ValidationError:
        return HttpResponse('<div class="text-red-600 text-sm">Please enter a valid email address.</div>')

    try:
        # Get user by email
        user = get_user_by_email(email)
        if not user:
            # Don't reveal if user exists - security best practice
            return HttpResponse(
                '<div class="text-red-600 text-sm">If this email is registered, a verification email will be sent.</div>'
            )

        # Check if already verified
        if user.email_verified:
            return HttpResponse(
                '<div class="text-green-600 text-sm">Your email is already verified! Please try signing in again.</div>'
            )

        # Generate magic link for email verification
        login_url = reverse("accounts:verify_email")
        magic_link = request.build_absolute_uri(login_url) + sesame_get_query_string(user)

        # Send verification email
        result = send_magic_link_email(user.email, magic_link, user.first_name, is_verification=True)

        if result.get("success"):
            logger.info(f"Verification email resent to unverified signin user: {email}")
            return HttpResponse(
                '<div class="text-green-600 text-sm">Verification email sent! Check your inbox and click the verification link.</div>'
            )
        else:
            logger.error(f"Failed to resend verification email to {email}")
            return HttpResponse('<div class="text-red-600 text-sm">Failed to send email. Please try again later.</div>')

    except Exception as e:
        logger.error(f"Error resending verification email to {email}: {e}")
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

    def _render_error(self, request, error_message):
        """Render error message template"""
        logger.error(f"Student creation error: {error_message}")
        return render(
            request,
            "shared/partials/error_message.html",
            {"error": error_message},
        )

    def _render_success(self, request, success_message):
        """Render success message template with HX-Trigger to refresh students list"""
        logger.info(f"Student creation success: {success_message}")
        response = render(
            request,
            "shared/partials/success_message.html",
            {"message": success_message},
        )
        # Add HX-Trigger header to automatically refresh the students list
        response["HX-Trigger"] = "refreshStudents"
        return response


@method_decorator(csrf_protect, name="dispatch")
class StudentSeparateCreateView(BaseStudentCreateView):
    """Create both student and guardian user accounts (separate logins)."""

    def post(self, request):
        """Handle Student + Guardian account creation with support for multiple guardians"""
        from django.db import transaction

        from accounts.models.profiles import GuardianProfile, GuardianStudentRelationship
        from accounts.permissions import PermissionService

        try:
            # Sanitize and extract student form data
            student_name = escape(request.POST.get("name", "").strip())
            student_email_raw = request.POST.get("email", "").strip()
            student_birth_date = request.POST.get("birth_date")
            student_school_year = escape(request.POST.get("school_year", "").strip())
            student_notes = escape(request.POST.get("notes", "").strip())

            # Extract multiple guardians from POST data
            guardians = []
            index = 0
            while f"guardian_{index}_name" in request.POST:
                guardian_data = {
                    "name": escape(request.POST.get(f"guardian_{index}_name", "").strip()),
                    "email": request.POST.get(f"guardian_{index}_email", "").strip(),
                    "phone": escape(request.POST.get(f"guardian_{index}_phone", "").strip()),
                    "tax_nr": escape(request.POST.get(f"guardian_{index}_tax_nr", "").strip()),
                    "address": escape(request.POST.get(f"guardian_{index}_address", "").strip()),
                    "is_primary": index == 0,  # First guardian is always primary
                    "permissions": {
                        "can_manage_bookings": request.POST.get(f"guardian_{index}_can_manage_bookings") == "on",
                        "can_view_financial_info": request.POST.get(f"guardian_{index}_can_view_financial_info")
                        == "on",
                        "can_communicate_with_teachers": request.POST.get(
                            f"guardian_{index}_can_communicate_with_teachers"
                        )
                        == "on",
                    },
                    "notifications": {
                        "email": request.POST.get(f"guardian_{index}_email_notifications") == "on",
                        "sms": request.POST.get(f"guardian_{index}_sms_notifications") == "on",
                    },
                    "invoice": request.POST.get(f"guardian_{index}_invoice") == "on",
                }
                guardians.append(guardian_data)
                index += 1

            # Log form data for debugging
            logger.info(f"Processing separate student creation: student={student_name}, guardians={len(guardians)}")

            # Validate student email
            try:
                student_email = self._validate_email_format(student_email_raw)
            except ValidationError as e:
                return self._render_error(request, str(e))

            # Validate that at least one guardian is provided
            if not guardians:
                return self._render_error(request, "At least one guardian is required")

            # Validate required fields for student and guardians
            if not all([student_name, student_email, student_birth_date]):
                missing_fields = []
                if not student_name:
                    missing_fields.append("student name")
                if not student_email:
                    missing_fields.append("student email")
                if not student_birth_date:
                    missing_fields.append("student birth date")
                error_msg = f"Missing required student fields: {', '.join(missing_fields)}"
                return self._render_error(request, error_msg)

            # Validate guardian emails and required fields
            for i, guardian_data in enumerate(guardians):
                if not guardian_data["name"] or not guardian_data["email"]:
                    return self._render_error(request, f"Guardian {i + 1}: Name and email are required")
                try:
                    guardian_data["email"] = self._validate_email_format(guardian_data["email"])
                except ValidationError as e:
                    return self._render_error(request, f"Guardian {i + 1}: {e!s}")

            # Get user's schools
            user_schools = self._get_user_schools(request.user)
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

                    # Create student profile (without setting the legacy guardian field)
                    student_profile = StudentProfile.objects.create(
                        user=student_user,
                        name=student_name,
                        account_type="STUDENT_GUARDIAN",
                        school_year=student_school_year,
                        birth_date=student_birth_date,
                        guardian=None,  # Will be handled via GuardianStudentRelationship
                        notes=student_notes,
                    )

                    # Track created guardian users for system tasks
                    created_guardian_users = []

                    # Create guardian users and relationships
                    primary_guardian_profile = None
                    for guardian_data in guardians:
                        # Create or get guardian user
                        try:
                            guardian_user = User.objects.get(email=guardian_data["email"])
                        except User.DoesNotExist:
                            guardian_user = User.objects.create_user(
                                email=guardian_data["email"],
                                name=guardian_data["name"],
                                phone_number=guardian_data["phone"],
                            )
                            created_guardian_users.append(guardian_user)

                        # Create or get guardian profile
                        guardian_profile, _ = GuardianProfile.objects.get_or_create(
                            user=guardian_user,
                            defaults={
                                "address": guardian_data["address"],
                                "tax_nr": guardian_data["tax_nr"],
                                "invoice": guardian_data["invoice"],
                                "email_notifications_enabled": guardian_data["notifications"]["email"],
                                "sms_notifications_enabled": guardian_data["notifications"]["sms"],
                            },
                        )

                        # Remember primary guardian to populate legacy FK later
                        if guardian_data.get("is_primary"):
                            primary_guardian_profile = guardian_profile

                        # Add both users to schools and create relationship
                        for school in user_schools:
                            SchoolMembership.objects.get_or_create(
                                user=guardian_user, school=school, defaults={"role": SchoolRole.GUARDIAN}
                            )

                            # Create GuardianStudentRelationship
                            GuardianStudentRelationship.objects.get_or_create(
                                guardian=guardian_user,
                                student=student_user,
                                school=school,
                                defaults={
                                    "is_primary": guardian_data["is_primary"],
                                    "can_manage_finances": guardian_data[
                                        "is_primary"
                                    ],  # Primary guardian always manages finances
                                    "can_book_classes": guardian_data["permissions"]["can_manage_bookings"],
                                    "can_view_records": guardian_data["permissions"]["can_view_financial_info"],
                                    "can_edit_profile": guardian_data["permissions"]["can_communicate_with_teachers"],
                                    "can_receive_notifications": guardian_data["notifications"]["email"]
                                    or guardian_data["notifications"]["sms"],
                                    "created_by": request.user,
                                },
                            )

                    # Populate deprecated guardian FK for backward compatibility
                    if primary_guardian_profile:
                        student_profile.guardian = primary_guardian_profile
                        student_profile.save()

                    # Add student to schools
                    for school in user_schools:
                        SchoolMembership.objects.get_or_create(
                            user=student_user, school=school, defaults={"role": SchoolRole.STUDENT}
                        )

                    # Setup permissions
                    PermissionService.setup_permissions_for_student(student_profile)

                    # Manually create system tasks after successful student creation
                    from tasks.services import TaskService

                    if student_user_was_created:
                        TaskService.initialize_system_tasks(student_user)
                    for guardian_user in created_guardian_users:
                        TaskService.initialize_system_tasks(guardian_user)

                finally:
                    # Reconnect the signal
                    post_save.connect(create_system_tasks_for_new_user, sender=User)

            guardian_names = [g["name"] for g in guardians]
            success_message = f"Successfully created student account for {student_name} and guardian accounts for {', '.join(guardian_names)}. All users can now login independently."
            return self._render_success(request, success_message)

        except Exception as e:
            logger.error(f"Unexpected error in separate student creation: {e}", exc_info=True)
            return self._render_error(request, "An unexpected error occurred. Please try again.")


@method_decorator(csrf_protect, name="dispatch")
class StudentGuardianOnlyCreateView(BaseStudentCreateView):
    """Create guardian account only, with student profile managed by guardian."""

    def post(self, request):
        """Handle Guardian-Only account creation with support for multiple guardians"""
        from django.db import transaction

        from accounts.models.profiles import GuardianProfile
        from accounts.permissions import PermissionService

        try:
            # Sanitize and extract student form data
            student_name = escape(request.POST.get("name", "").strip())
            student_birth_date = request.POST.get("birth_date")
            student_school_year = escape(request.POST.get("school_year", "").strip())
            student_notes = escape(request.POST.get("notes", "").strip())

            # Extract multiple guardians from POST data
            guardians = []
            index = 0
            while f"guardian_{index}_name" in request.POST:
                guardian_data = {
                    "name": escape(request.POST.get(f"guardian_{index}_name", "").strip()),
                    "email": request.POST.get(f"guardian_{index}_email", "").strip(),
                    "phone": escape(request.POST.get(f"guardian_{index}_phone", "").strip()),
                    "tax_nr": escape(request.POST.get(f"guardian_{index}_tax_nr", "").strip()),
                    "address": escape(request.POST.get(f"guardian_{index}_address", "").strip()),
                    "is_primary": index == 0,  # First guardian is always primary
                    "permissions": {
                        "can_manage_bookings": request.POST.get(f"guardian_{index}_can_manage_bookings") == "on",
                        "can_view_financial_info": request.POST.get(f"guardian_{index}_can_view_financial_info")
                        == "on",
                        "can_communicate_with_teachers": request.POST.get(
                            f"guardian_{index}_can_communicate_with_teachers"
                        )
                        == "on",
                    },
                    "notifications": {
                        "email": request.POST.get(f"guardian_{index}_email_notifications") == "on",
                        "sms": request.POST.get(f"guardian_{index}_sms_notifications") == "on",
                    },
                    "invoice": request.POST.get(f"guardian_{index}_invoice") == "on",
                }
                guardians.append(guardian_data)
                index += 1

            # Log form data for debugging
            logger.info(f"Processing guardian-only creation: student={student_name}, guardians={len(guardians)}")

            # Validate that at least one guardian is provided
            if not guardians:
                return self._render_error(request, "At least one guardian is required")

            # Validate required fields for student
            if not all([student_name, student_birth_date]):
                missing_fields = []
                if not student_name:
                    missing_fields.append("student name")
                if not student_birth_date:
                    missing_fields.append("student birth date")
                error_msg = f"Missing required student fields: {', '.join(missing_fields)}"
                return self._render_error(request, error_msg)

            # Validate guardian emails and required fields
            for i, guardian_data in enumerate(guardians):
                if not guardian_data["name"] or not guardian_data["email"]:
                    return self._render_error(request, f"Guardian {i + 1}: Name and email are required")
                try:
                    guardian_data["email"] = self._validate_email_format(guardian_data["email"])
                except ValidationError as e:
                    return self._render_error(request, f"Guardian {i + 1}: {e!s}")

            # Get user's schools
            user_schools = self._get_user_schools(request.user)
            with transaction.atomic():
                # Temporarily disconnect the task creation signal to prevent orphaned tasks
                from django.db.models.signals import post_save

                from accounts.signals.verification_task_signals import create_system_tasks_for_new_user

                post_save.disconnect(create_system_tasks_for_new_user, sender=User)

                try:
                    # For guardian-only students, create student profile without user account
                    # We'll handle the guardian relationships via the legacy guardian field for now
                    # and set up the new relationships once the student has a user account
                    student_profile = StudentProfile.objects.create(
                        user=None,  # No user account for guardian-only students
                        name=student_name,
                        account_type="GUARDIAN_ONLY",
                        school_year=student_school_year,
                        birth_date=student_birth_date,
                        guardian=None,  # Will be set to primary guardian below
                        notes=student_notes,
                    )

                    # Track created guardian users for system tasks
                    created_guardian_users = []
                    primary_guardian_profile = None

                    # Create guardian users and profiles
                    for guardian_data in guardians:
                        # Create or get guardian user
                        try:
                            guardian_user = User.objects.get(email=guardian_data["email"])
                        except User.DoesNotExist:
                            guardian_user = User.objects.create_user(
                                email=guardian_data["email"],
                                name=guardian_data["name"],
                                phone_number=guardian_data["phone"],
                            )
                            created_guardian_users.append(guardian_user)

                        # Create guardian profile
                        guardian_profile, _ = GuardianProfile.objects.get_or_create(
                            user=guardian_user,
                            defaults={
                                "address": guardian_data["address"],
                                "tax_nr": guardian_data["tax_nr"],
                                "invoice": guardian_data["invoice"],
                                "email_notifications_enabled": guardian_data["notifications"]["email"],
                                "sms_notifications_enabled": guardian_data["notifications"]["sms"],
                            },
                        )

                        # Set primary guardian for the legacy guardian field
                        if guardian_data["is_primary"]:
                            primary_guardian_profile = guardian_profile

                        # Add guardian to schools
                        for school in user_schools:
                            SchoolMembership.objects.get_or_create(
                                user=guardian_user, school=school, defaults={"role": SchoolRole.GUARDIAN}
                            )

                    # Set the primary guardian in the student profile (legacy field)
                    if primary_guardian_profile:
                        student_profile.guardian = primary_guardian_profile
                        student_profile.save()

                    # Note: GuardianStudentRelationship entries will be created when/if the student
                    # gets a user account in the future, or through a separate management interface

                    # Setup permissions
                    PermissionService.setup_permissions_for_student(student_profile)

                    # Manually create system tasks for guardian users only (not the placeholder student)
                    from tasks.services import TaskService

                    for guardian_user in created_guardian_users:
                        TaskService.initialize_system_tasks(guardian_user)

                finally:
                    # Reconnect the signal
                    post_save.connect(create_system_tasks_for_new_user, sender=User)

            guardian_names = [g["name"] for g in guardians]
            success_message = f"Successfully created guardian accounts for {', '.join(guardian_names)} who will manage {student_name}'s profile. Only the guardians can login."
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
