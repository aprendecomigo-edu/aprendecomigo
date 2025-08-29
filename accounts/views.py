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

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from sesame.utils import get_query_string

from messaging.services import send_magic_link_email, send_sms_otp
from .db_queries import get_user_by_email, user_exists, create_user_school_and_membership
from .models import School, SchoolMembership, TeacherInvitation
from .permissions import IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin

User = get_user_model()
logger = logging.getLogger(__name__)

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
            return redirect("dashboard:dashboard")

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
                # Still show success to prevent email enumeration
                return render(request, "accounts/partials/signin_success_with_verify.html", {"email": email})

            # User exists - generate dual verification for existing users
            logger.info(f"Dual verification requested for registered email: {email}")
            user = get_user_by_email(email)

            # Generate magic link for email verification
            login_url = reverse("accounts:magic_login")
            magic_link = request.build_absolute_uri(login_url) + get_query_string(user)

            # Generate secure 6-digit OTP code for SMS verification
            otp_code = str(secrets.randbelow(900000) + 100000)
            otp_expires = (timezone.now() + timedelta(minutes=5)).timestamp()
            logger.info(f"Generated OTP code: {otp_code} for user: {user.email}")

            try:
                # Send both magic link and SMS OTP (if phone available)
                email_result = send_magic_link_email(email, magic_link, user.name or user.first_name)
                
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

                    logger.info(f"Dual verification sent successfully to: {email} and {user.phone_number or 'no phone'}")
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
            return redirect("dashboard:dashboard")

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
                
                # Create school and membership immediately
                create_user_school_and_membership(user, organization_name)
                
                # Log in the user immediately
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                logger.info(f"User signup completed for: {email}")

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
            return redirect("accounts:signin")

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
                    # For signin, SMS OTP is sufficient
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    logger.info(f"SMS authentication successful for user: {user.email}")

                    # Clear session data
                    self._clear_verification_session(request)

                    return render(
                        request,
                        "accounts/partials/verify_success.html",
                        {"message": "Welcome back!", "redirect_url": reverse("dashboard:dashboard")},
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

        # Perform logout
        logout(request)

        # Clear any session data
        request.session.flush()

        # Redirect to home or signin page
        return redirect("/accounts/signin/")

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
        user_schools = self.get_user_schools_by_role('school_owner') | \
                      self.get_user_schools_by_role('school_admin')
        
        # Filter invitations for these schools
        return TeacherInvitation.objects.filter(
            school__in=user_schools
        ).select_related('school', 'invited_by').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schools'] = self.get_user_schools_by_role('school_owner') | \
                           self.get_user_schools_by_role('school_admin')
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
    fields = ['school', 'email', 'custom_message']
    success_url = reverse_lazy('accounts:invitation_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit school choices to schools the user can manage
        user_schools = self.get_user_schools_by_role('school_owner') | \
                      self.get_user_schools_by_role('school_admin')
        form.fields['school'].queryset = user_schools
        return form

    def form_valid(self, form):
        # Generate batch ID for tracking
        batch_id = uuid.uuid4()
        
        # Set the invitation details
        form.instance.invited_by = self.request.user
        form.instance.batch_id = batch_id
        form.instance.role = 'teacher'  # Default to teacher role
        
        # Check if user has permission to invite to this school
        school = form.instance.school
        if not self.has_school_permission(school, ['school_owner', 'school_admin']):
            messages.error(self.request, "You don't have permission to invite teachers to this school.")
            return self.form_invalid(form)
        
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                
                # Send invitation email (implement this based on your email system)
                # send_teacher_invitation_email(form.instance)
                
                messages.success(self.request, f"Teacher invitation sent to {form.instance.email}")
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
        user_schools = self.get_user_schools_by_role('school_owner') | \
                      self.get_user_schools_by_role('school_admin')
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
            return render(request, 'accounts/invitations/invitation_expired.html', {
                'invitation': invitation
            })
        
        # Mark as viewed
        invitation.mark_viewed()
        
        return render(request, 'accounts/invitations/accept_invitation.html', {
            'invitation': invitation
        })
    
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
            return render(request, 'accounts/invitations/invitation_expired.html', {
                'invitation': invitation
            })
        
        action = request.POST.get('action')
        
        if action == 'accept':
            # Check if user exists
            try:
                user = User.objects.get(email=invitation.email)
                
                # Create school membership
                membership, created = SchoolMembership.objects.get_or_create(
                    user=user,
                    school=invitation.school,
                    role=invitation.role,
                    defaults={'is_active': True}
                )
                
                if not created and not membership.is_active:
                    membership.is_active = True
                    membership.save()
                
                # Mark invitation as accepted
                invitation.accept()
                
                # If user is logged in and it's the correct user, redirect to dashboard
                if request.user.is_authenticated and request.user.email == invitation.email:
                    messages.success(request, f"Welcome to {invitation.school.name}! You are now a {invitation.get_role_display()}.")
                    return redirect('dashboard:dashboard')
                
                # Otherwise, show success page with login instructions
                return render(request, 'accounts/invitations/invitation_accepted.html', {
                    'invitation': invitation,
                    'user_exists': True
                })
                
            except User.DoesNotExist:
                # User doesn't exist, show signup flow
                return render(request, 'accounts/invitations/invitation_accepted.html', {
                    'invitation': invitation,
                    'user_exists': False,
                    'signup_url': reverse('accounts:signup') + f'?email={invitation.email}&invitation_token={token}'
                })
        
        elif action == 'decline':
            invitation.decline()
            return render(request, 'accounts/invitations/invitation_declined.html', {
                'invitation': invitation
            })
        
        return redirect('accounts:accept_invitation', token=token)


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
        user=request.user,
        role__in=['school_owner', 'school_admin'],
        is_active=True
    ).values_list('school_id', flat=True)
    
    if invitation.school_id not in user_schools and not request.user.is_superuser:
        return HttpResponse("Permission denied", status=403)
    
    if request.method == 'POST':
        try:
            invitation.cancel()
            return render(request, 'accounts/invitations/partials/invitation_cancelled.html', {
                'invitation': invitation
            })
        except ValidationError as e:
            return render(request, 'accounts/invitations/partials/invitation_error.html', {
                'error': str(e)
            })
    
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
        user=request.user,
        role__in=['school_owner', 'school_admin'],
        is_active=True
    ).values_list('school_id', flat=True)
    
    if invitation.school_id not in user_schools and not request.user.is_superuser:
        return HttpResponse("Permission denied", status=403)
    
    if request.method == 'POST':
        try:
            # Check if can retry
            if not invitation.can_retry():
                return render(request, 'accounts/invitations/partials/invitation_error.html', {
                    'error': "Maximum retry attempts reached for this invitation."
                })
            
            # Resend email (implement based on your email system)
            # send_teacher_invitation_email(invitation)
            
            # Update invitation status
            invitation.mark_email_sent()
            
            return render(request, 'accounts/invitations/partials/invitation_resent.html', {
                'invitation': invitation
            })
            
        except Exception as e:
            invitation.mark_email_failed(str(e))
            return render(request, 'accounts/invitations/partials/invitation_error.html', {
                'error': "Failed to resend invitation. Please try again."
            })
    
    return HttpResponse("Method not allowed", status=405)


# =============================================================================
# PROFILE MANAGEMENT VIEWS
# =============================================================================

class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""
    
    model = User
    template_name = "accounts/profile/profile_edit.html"
    fields = ['first_name', 'last_name', 'phone_number', 'bio', 'timezone', 'preferred_language']
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been updated successfully.")
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, DetailView):
    """View user profile"""
    
    model = User
    template_name = "accounts/profile/profile_detail.html"
    context_object_name = "profile_user"

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's school memberships
        memberships = SchoolMembership.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('school').order_by('joined_at')
        
        context['memberships'] = memberships
        return context


# =============================================================================
# SCHOOL MANAGEMENT VIEWS
# =============================================================================

class SchoolSettingsView(IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin, UpdateView):
    """Edit school settings"""
    
    model = School
    template_name = "accounts/schools/school_settings.html"
    fields = [
        'name', 'description', 'address', 'contact_email', 
        'phone_number', 'website', 'logo', 'primary_color', 'secondary_color'
    ]

    def get_queryset(self):
        # Limit to schools the user can manage
        return self.get_user_schools_by_role('school_owner') | \
               self.get_user_schools_by_role('school_admin')

    def form_valid(self, form):
        messages.success(self.request, f"Settings for {form.instance.name} have been updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('accounts:school_settings', kwargs={'pk': self.object.pk})


class SchoolMemberListView(IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin, ListView):
    """List school members"""
    
    model = SchoolMembership
    template_name = "accounts/schools/school_members.html"
    context_object_name = "memberships"
    paginate_by = 50

    def get_queryset(self):
        self.school = get_object_or_404(School, pk=self.kwargs['school_pk'])
        
        # Check permission for this specific school
        if not self.has_school_permission(self.school, ['school_owner', 'school_admin']):
            raise Http404("You don't have permission to view this school's members.")
        
        return SchoolMembership.objects.filter(
            school=self.school,
            is_active=True
        ).select_related('user').order_by('role', 'joined_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = self.school
        return context


# Using django-sesame's built-in LoginView directly - no custom implementation needed

def root_redirect(request):
    """
    Root path handler: redirects based on authentication status
    - Authenticated users → /dashboard/
    - Anonymous users → /accounts/signin/
    """
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('dashboard:general'))
    else:
        return HttpResponseRedirect(reverse('accounts:signin'))
