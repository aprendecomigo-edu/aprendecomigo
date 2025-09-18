from django.urls import path

# Import the Django web authentication views
from .views import (
    # Invitation management views
    AcceptTeacherInvitationView,
    # Authentication views
    CustomMagicLoginView,
    EmailVerificationView,
    LogoutView,
    PhoneVerificationView,
    # Profile management views
    ProfileEditView,
    ProfileView,
    # School management views
    SchoolMemberListView,
    SchoolSettingsView,
    SignInView,
    SignUpView,
    StudentAdultCreateView,
    StudentGuardianOnlyCreateView,
    # Student creation views
    StudentSeparateCreateView,
    TeacherInvitationCreateView,
    TeacherInvitationDetailView,
    TeacherInvitationListView,
    VerifyOTPView,
    cancel_teacher_invitation,
    resend_code,
    resend_teacher_invitation,
    resend_verification_email_signin,
    root_redirect,
    send_otp_email,
    send_otp_sms,
    send_verification_email,
    send_verification_sms,
)
from .views_i18n import set_language

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
    path("send-otp-email/", send_otp_email, name="send_otp_email"),
    path("send-otp-sms/", send_otp_sms, name="send_otp_sms"),
    path("resend-code/", resend_code, name="resend_code"),
    # Email verification using NEW view with verification completion
    path("verify-email/", EmailVerificationView.as_view(), name="verify_email"),
    # Phone verification using NEW view with verification completion
    path("verify-phone/", PhoneVerificationView.as_view(), name="verify_phone"),
    # Magic link authentication using existing view (for signin, not verification)
    path("magic-login/", CustomMagicLoginView.as_view(), name="magic_login"),
    # Verification actions from profile page
    path("send-verification-email/", send_verification_email, name="send_verification_email"),
    path("send-verification-sms/", send_verification_sms, name="send_verification_sms"),
    # Verification resend for signin flow (for unverified users)
    path(
        "resend-verification-email-signin/", resend_verification_email_signin, name="resend_verification_email_signin"
    ),
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
    # Student Creation (Account Management)
    path("students/create/separate/", StudentSeparateCreateView.as_view(), name="student_create_separate"),
    path(
        "students/create/guardian-only/", StudentGuardianOnlyCreateView.as_view(), name="student_create_guardian_only"
    ),
    path("students/create/adult/", StudentAdultCreateView.as_view(), name="student_create_adult"),
    # Internationalization
    path("set-language/", set_language, name="set_language"),
]
