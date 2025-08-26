from django.urls import path
from sesame.views import LoginView

# Import the Django web authentication views
from .views.auth_views import (
    SignInView,
    SignUpView,
    VerifyOTPView,
    DashboardView,
    resend_code,
)

app_name = "accounts"

# URL patterns for the accounts app - PWA migration (Django web views only)
urlpatterns = [
    # Django web authentication views
    path("signin/", SignInView.as_view(), name="signin"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("resend-code/", resend_code, name="resend_code"),
    
    # Magic link authentication
    path("magic-login/", LoginView.as_view(), name="magic_login"),
]
