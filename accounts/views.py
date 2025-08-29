"""
Authentication views for Django web interface (PWA Migration)
Consolidated authentication using email magic links + SMS OTP
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
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from sesame.utils import get_query_string

from messaging.services import send_magic_link_email, send_sms_otp

from .db_queries import get_user_by_email, user_exists
from .models import School, SchoolMembership, TeacherInvitation
from .permissions import IsSchoolOwnerOrAdminMixin, SchoolPermissionMixin

User = get_user_model()
logger = logging.getLogger(__name__)


class SignInView(View):
    """Sign in page view - SMS OTP for existing users"""

    def get(self, request):
        """Render sign in page"""
        if request.user.is_authenticated:
            return redirect("/dashboard/")

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
            return redirect("/dashboard/")

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
    def post(self, request):
        """Handle OTP verification"""
        otp_code = request.POST.get("verification_code", "").strip()

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
                "accounts/partials/verify_form.html",
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
                "accounts/partials/verify_form.html",
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

                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    logger.info(f"Signup verification completed for new user: {user.email}")

                    # Clear session data
                    self._clear_verification_session(request)

                    return render(
                        request,
                        "accounts/partials/verify_success.html",
                        {
                            "message": "Account verified! Welcome to Aprende Comigo.",
                            "redirect_url": "/dashboard/",
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
                        {"message": "Welcome back!", "redirect_url": "/dashboard/"},
                    )

            else:
                return render(
                    request,
                    "accounts/partials/verify_form.html",
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
                "accounts/partials/verify_form.html",
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
        logger.error(f"Resend code error for {email}: {e}")
        return render(
            request,
            "accounts/partials/resend_error.html",
            {"error": "There was an issue resending the login link. Please try again."},
        )


class LogoutView(View):
    """Handle user logout"""

    def get(self, request):
        """Handle GET logout request"""
        return self.post(request)

    def post(self, request):
        """Handle POST logout request"""
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
    """List all teacher invitations for schools the user manages"""
    
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
    """Create new teacher invitation"""
    
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
    """View teacher invitation details"""
    
    model = TeacherInvitation
    template_name = "accounts/invitations/invitation_detail.html"
    context_object_name = "invitation"

    def get_queryset(self):
        # Limit to invitations for schools the user can manage
        user_schools = self.get_user_schools_by_role('school_owner') | \
                      self.get_user_schools_by_role('school_admin')
        return TeacherInvitation.objects.filter(school__in=user_schools)


class AcceptTeacherInvitationView(View):
    """Accept a teacher invitation (public view accessible by token)"""
    
    def get(self, request, token):
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
    def post(self, request, token):
        """Process invitation acceptance"""
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
                    return redirect('/dashboard/')
                
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
def cancel_teacher_invitation(request, invitation_id):
    """Cancel a teacher invitation (HTMX endpoint)"""
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
def resend_teacher_invitation(request, invitation_id):
    """Resend a teacher invitation (HTMX endpoint)"""
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
