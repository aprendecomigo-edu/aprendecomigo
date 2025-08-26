"""
Authentication views for Django web interface (PWA Migration)
Consolidated authentication using email magic links + SMS OTP
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse
from sesame.utils import get_query_string

import logging
import re
import secrets
from datetime import timedelta

from django.utils import timezone
from ..db_queries import get_user_by_email, user_exists
from common.messaging import send_magic_link_email, send_sms_otp

User = get_user_model()
logger = logging.getLogger(__name__)


class SignInView(View):
    """Sign in page view - SMS OTP for existing users"""

    def get(self, request):
        """Render sign in page"""
        if request.user.is_authenticated:
            return redirect("accounts:dashboard")

        return render(
            request,
            "accounts/signin.html",
            {"title": "Login - Aprende Comigo", "meta_description": "Sign in to your Aprende Comigo account"},
        )

    @method_decorator(csrf_protect)
    def post(self, request):
        """Handle sign in form submission via HTMX"""
        email = request.POST.get("email", "").strip().lower()

        # Validate email
        if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
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
                # Still show success to prevent email enumeration
                return render(request, "accounts/partials/signin_success.html", {"email": email})

            # User exists - generate SMS OTP for existing users
            logger.info(f"SMS OTP requested for registered email: {email}")
            user = get_user_by_email(email)

            # Check if user has phone number
            if not user.phone_number:
                return render(
                    request,
                    "accounts/partials/signin_form.html",
                    {"error": "No phone number on file. Please contact support.", "email": email},
                )

            # Generate secure 6-digit OTP code
            otp_code = str(secrets.randbelow(900000) + 100000)
            otp_expires = (timezone.now() + timedelta(minutes=5)).timestamp()

            try:
                sms_result = send_sms_otp(user.phone_number, otp_code, user.name or user.first_name)

                if sms_result.get("success"):
                    # Store verification data in session for SMS OTP verification
                    request.session["verification_phone"] = user.phone_number
                    request.session["verification_user_id"] = user.id
                    request.session["verification_otp_code"] = otp_code
                    request.session["verification_otp_expires"] = otp_expires
                    request.session["is_signin"] = True

                    logger.info(f"SMS OTP sent successfully to: {user.phone_number}")
                    return render(
                        request,
                        "accounts/partials/signin_success.html",
                        {"email": email, "phone_number": user.phone_number},
                    )
                else:
                    return render(
                        request,
                        "accounts/partials/signin_form.html",
                        {
                            "error": "There was an issue sending the verification code. Please try again.",
                            "email": email,
                        },
                    )

            except Exception as sms_error:
                logger.error(f"Failed to send SMS OTP to {user.phone_number}: {sms_error}")
                return render(
                    request,
                    "accounts/partials/signin_form.html",
                    {"error": "There was an issue sending the verification code. Please try again.", "email": email},
                )

        except Exception as e:
            logger.error(f"Sign in error for {email}: {e}")
            return render(
                request,
                "accounts/partials/signin_form.html",
                {"error": "There was an issue sending the verification code. Please try again.", "email": email},
            )


class SignUpView(View):
    """Sign up page view - dual verification: email magic link + SMS OTP"""

    def get(self, request):
        """Render sign up page"""
        if request.user.is_authenticated:
            return redirect("accounts:dashboard")

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
            # Create user with phone number
            user = User.objects.create_user(
                email=email,
                phone_number=phone_number,
                first_name=full_name.split()[0] if full_name else "",
                last_name=" ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
            )

            # Generate magic link for email verification
            logger.info(f"Dual verification requested for new user: {email}")
            login_url = reverse("accounts:magic_login")
            magic_link = request.build_absolute_uri(login_url) + get_query_string(user)

            # Generate secure 6-digit OTP code for SMS verification
            otp_code = str(secrets.randbelow(900000) + 100000)
            otp_expires = (timezone.now() + timedelta(minutes=5)).timestamp()

            try:
                # Send both magic link and SMS OTP
                email_result = send_magic_link_email(email, magic_link, user.name or user.first_name)
                sms_result = send_sms_otp(phone_number, otp_code, user.name or user.first_name)

                if email_result.get("success") and sms_result.get("success"):
                    # Store verification data in session
                    request.session["verification_email"] = email
                    request.session["verification_phone"] = phone_number
                    request.session["verification_user_id"] = user.id
                    request.session["verification_otp_code"] = otp_code
                    request.session["verification_otp_expires"] = otp_expires
                    request.session["is_signup"] = True

                    logger.info(f"Dual verification sent successfully to: {email} and {phone_number}")
                    return render(
                        request,
                        "accounts/partials/signup_success.html",
                        {"email": email, "phone_number": phone_number, "full_name": full_name},
                    )
                else:
                    # Clean up if either failed
                    user.delete()
                    error_msg = "There was an issue sending verification. Please try again."
                    if not email_result.get("success"):
                        error_msg = "Failed to send email verification."
                    elif not sms_result.get("success"):
                        error_msg = "Failed to send SMS verification."

                    return render(
                        request,
                        "accounts/partials/signup_form.html",
                        {"error": error_msg, "email": email, "full_name": full_name, "phone_number": phone_number},
                    )

            except Exception as verification_error:
                logger.error(f"Failed to send dual verification to {email}/{phone_number}: {verification_error}")
                user.delete()
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
    """Verify OTP code for both signup and signin"""

    def get(self, request):
        """Render OTP verification page"""
        # Check session data
        user_id = request.session.get("verification_user_id")
        expected_otp = request.session.get("verification_otp_code")
        phone = request.session.get("verification_phone")
        is_signup = request.session.get("is_signup", False)
        is_signin = request.session.get("is_signin", False)

        if not all([user_id, expected_otp, phone]):
            return redirect("accounts:signin")

        return render(
            request,
            "accounts/verify_otp.html",
            {
                "title": "Verify Phone - Aprende Comigo",
                "meta_description": "Enter your SMS verification code",
                "phone_number": phone,
                "is_signup": is_signup,
                "is_signin": is_signin,
            },
        )

    @method_decorator(csrf_protect)
    def post(self, request):
        """Handle OTP verification"""
        otp_code = request.POST.get("otp_code", "").strip()

        # Get session data
        user_id = request.session.get("verification_user_id")
        expected_otp = request.session.get("verification_otp_code")
        otp_expires = request.session.get("verification_otp_expires")
        phone = request.session.get("verification_phone")
        is_signup = request.session.get("is_signup", False)
        is_signin = request.session.get("is_signin", False)

        if not all([user_id, expected_otp, phone, otp_code]):
            return render(
                request,
                "accounts/partials/otp_form.html",
                {
                    "error": "Please enter the verification code.",
                    "phone_number": phone,
                    "is_signup": is_signup,
                    "is_signin": is_signin,
                },
            )

        # Check if OTP has expired
        if otp_expires and timezone.now().timestamp() > otp_expires:
            return render(
                request,
                "accounts/partials/otp_form.html",
                {
                    "error": "Verification code has expired. Please request a new one.",
                    "phone_number": phone,
                    "is_signup": is_signup,
                    "is_signin": is_signin,
                },
            )

        try:
            # Get user
            user = User.objects.get(id=user_id)

            # Verify OTP by comparing with session-stored code
            if otp_code == expected_otp:
                if is_signup:
                    # For signup, SMS verification is sufficient for now
                    # (Email magic link verification can be added later)
                    user.phone_verified = True
                    user.save()

                    login(request, user)
                    logger.info(f"Signup verification completed for new user: {user.email}")

                    # Clear session data
                    self._clear_verification_session(request)

                    return render(
                        request,
                        "accounts/partials/otp_success.html",
                        {
                            "message": "Account verified! Welcome to Aprende Comigo.",
                            "redirect_url": "/accounts/dashboard/",
                        },
                    )

                elif is_signin:
                    # For signin, SMS OTP is sufficient
                    login(request, user)
                    logger.info(f"SMS authentication successful for user: {user.email}")

                    # Clear session data
                    self._clear_verification_session(request)

                    return render(
                        request,
                        "accounts/partials/otp_success.html",
                        {"message": "Welcome back!", "redirect_url": "/accounts/dashboard/"},
                    )

            else:
                return render(
                    request,
                    "accounts/partials/otp_form.html",
                    {
                        "error": "Invalid verification code. Please try again.",
                        "phone_number": phone,
                        "is_signup": is_signup,
                        "is_signin": is_signin,
                    },
                )

        except Exception as e:
            logger.error(f"OTP verification error: {e}")
            return render(
                request,
                "accounts/partials/otp_form.html",
                {
                    "error": "There was an issue verifying your code. Please try again.",
                    "phone_number": phone,
                    "is_signup": is_signup,
                    "is_signin": is_signin,
                },
            )

    def _clear_verification_session(self, request):
        """Clear verification session data"""
        keys_to_clear = [
            "verification_email",
            "verification_phone",
            "verification_user_id",
            "verification_otp_code",
            "verification_otp_expires",
            "is_signup",
            "is_signin",
        ]
        for key in keys_to_clear:
            request.session.pop(key, None)


class DashboardView(View):
    """Simple dashboard redirect based on user role"""

    def get(self, request):
        """Redirect to appropriate dashboard based on user role"""
        if not request.user.is_authenticated:
            return redirect("accounts:signin")

        # Redirect based on user role
        if hasattr(request.user, "teacherprofile"):
            return redirect("dashboard:teacher_dashboard")
        elif hasattr(request.user, "studentprofile"):
            return redirect("dashboard:student_dashboard")
        elif hasattr(request.user, "parentprofile"):
            return redirect("dashboard:parent_dashboard")
        elif request.user.is_staff:
            return redirect("dashboard:admin_dashboard")
        else:
            # Default to a general dashboard
            return render(
                request, "accounts/dashboard.html", {"title": "Dashboard - Aprende Comigo", "user": request.user}
            )


# Function for resending verification code via HTMX
@csrf_protect
def resend_code(request):
    """Resend verification code via HTMX"""
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

        try:
            send_magic_link_email(email, magic_link, user.name or user.first_name)
            logger.info(f"Magic link resent successfully to: {email}")
            return render(
                request,
                "accounts/partials/resend_success.html",
                {"email": email, "message": "A new login link has been sent to your email."},
            )

        except Exception as email_error:
            logger.error(f"Failed to resend magic link to {email}: {email_error}")
            return render(
                request,
                "accounts/partials/resend_error.html",
                {"error": "There was an issue resending the login link. Please try again."},
            )

    except Exception as e:
        logger.error(f"Resend magic link error for {email}: {e}")
        return render(
            request,
            "accounts/partials/resend_error.html",
            {"error": "There was an issue resending the login link. Please try again."},
        )
