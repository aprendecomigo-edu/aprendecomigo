from django.urls import path
from sesame.views import LoginView

# Import the Django web authentication views
from .views import (
    LogoutView,
    SignInView,
    SignUpView,
    VerifyOTPView,
    resend_code,
)

app_name = "accounts"

# URL patterns for the accounts app - PWA migration (Django web views only)
urlpatterns = [
    # Django web authentication views
    path("signin/", SignInView.as_view(), name="signin"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("resend-code/", resend_code, name="resend_code"),
    # Magic link authentication using django-sesame's built-in LoginView
    path("magic-login/", LoginView.as_view(), name="magic_login"),
]
