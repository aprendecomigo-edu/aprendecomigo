from django.urls import path
from sesame.views import LoginView

# Import the Django web authentication views
from .views import (
    # Invitation management views
    AcceptTeacherInvitationView,
    # Authentication views
    LogoutView,
    # Profile management views
    ProfileEditView,
    ProfileView,
    # School management views
    SchoolMemberListView,
    SchoolSettingsView,
    SignInView,
    SignUpView,
    TeacherInvitationCreateView,
    TeacherInvitationDetailView,
    TeacherInvitationListView,
    VerifyOTPView,
    cancel_teacher_invitation,
    resend_code,
    resend_teacher_invitation,
    root_redirect,
    send_verification_email,
    send_verification_sms,
)

app_name = "accounts"

# URL patterns for the accounts app - PWA migration (Django web views only)
urlpatterns = [
    # Root redirect function
    path("", root_redirect, name="root_redirect"),
    # Django web authentication views
    path("signin/", SignInView.as_view(), name="signin"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("resend-code/", resend_code, name="resend_code"),
    # Magic link authentication using django-sesame's built-in LoginView
    path("magic-login/", LoginView.as_view(), name="magic_login"),
    # Email verification using magic link (progressive verification)
    path("verify-email/", LoginView.as_view(), name="verify_email"),
    # Verification actions from profile page
    path("send-verification-email/", send_verification_email, name="send_verification_email"),
    path("send-verification-sms/", send_verification_sms, name="send_verification_sms"),

    # Teacher Invitation Management
    path("invitations/", TeacherInvitationListView.as_view(), name="invitation_list"),
    path("invitations/create/", TeacherInvitationCreateView.as_view(), name="invitation_create"),
    path("invitations/<int:pk>/", TeacherInvitationDetailView.as_view(), name="invitation_detail"),
    path("invitations/<int:invitation_id>/cancel/", cancel_teacher_invitation, name="cancel_invitation"),
    path("invitations/<int:invitation_id>/resend/", resend_teacher_invitation, name="resend_invitation"),
    # Public invitation acceptance (no login required)
    path("invitations/accept/<str:token>/", AcceptTeacherInvitationView.as_view(), name="accept_invitation"),

    # Profile Management
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),

    # School Management
    path("schools/<int:pk>/settings/", SchoolSettingsView.as_view(), name="school_settings"),
    path("schools/<int:school_pk>/members/", SchoolMemberListView.as_view(), name="school_members"),
]
