from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.shortcuts import resolve_url


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter for allauth to handle onboarding redirects
    """

    def get_login_redirect_url(self, request):
        # Check if user_type was provided in the form
        user_type = request.POST.get("user_type")
        user = request.user

        # Update user_type if provided
        if user_type in ["student", "teacher"]:
            user.user_type = user_type
            user.save()

        # Otherwise use the default redirect
        return resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_signup_redirect_url(self, request):
        """
        Override to redirect to student onboarding after signup
        """
        # Check if user_type was provided in the form
        user_type = request.POST.get("user_type")
        user = request.user

        # Update user_type if provided
        if user_type in ["student", "teacher"]:
            user.user_type = user_type
            user.save()

        # If it's a student, redirect to onboarding
        if hasattr(user, "user_type") and user.user_type == "student":
            return resolve_url("student_onboarding")

        # Otherwise use the default redirect
        return resolve_url(settings.LOGIN_REDIRECT_URL)

    def save_user(self, request, user, form, commit=True):
        """
        Save user and set user_type if provided
        """
        user = super().save_user(request, user, form, commit=False)

        # Set user type if provided
        user_type = request.POST.get("user_type")
        if user_type in ["student", "teacher"]:
            user.user_type = user_type

        if commit:
            user.save()
        return user

    def get_login_template(self):
        return settings.ACCOUNT_LOGIN_TEMPLATE

    def get_signup_template(self):
        return settings.ACCOUNT_SIGNUP_TEMPLATE

    def get_logout_template(self):
        return settings.ACCOUNT_LOGOUT_TEMPLATE

    def get_password_reset_template(self):
        return settings.ACCOUNT_PASSWORD_RESET_TEMPLATE

    def get_password_change_template(self):
        return settings.ACCOUNT_PASSWORD_CHANGE_TEMPLATE

    def get_password_set_template(self):
        return settings.ACCOUNT_PASSWORD_SET_TEMPLATE


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for social auth to handle onboarding redirects
    """

    def get_connect_redirect_url(self, request, socialaccount):
        return resolve_url("dashboard")

    def get_login_redirect_url(self, request):
        # Check if user_type was provided in the request
        user_type = request.POST.get("user_type")
        user = request.user

        # Update user_type if provided
        if user_type in ["student", "teacher"]:
            user.user_type = user_type
            user.save()

        # If it's a student without a profile, redirect to onboarding
        if hasattr(user, "user_type") and user.user_type == "student":
            # Check if student profile exists using hasattr or checking the related object
            if not hasattr(user, "student_profile") or user.student_profile is None:
                # No profile, redirect to onboarding
                return resolve_url("student_onboarding")

        # Otherwise use the default redirect
        return resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_signup_redirect_url(self, request):
        """
        Override to redirect to student onboarding after social signup
        """
        user = request.user
        user_type = request.POST.get("user_type")

        # Update user_type if provided
        if user_type in ["student", "teacher"]:
            user.user_type = user_type
            user.save()

        # If it's a student, redirect to onboarding
        if hasattr(user, "user_type") and user.user_type == "student":
            return resolve_url("student_onboarding")

        # Otherwise use the default redirect
        return resolve_url(settings.LOGIN_REDIRECT_URL)

    def pre_social_login(self, request, sociallogin):
        """
        Process user_type from the form before social login completes
        """
        # Set user type from the form if provided
        user_type = request.POST.get("user_type")
        user = sociallogin.user

        if user_type in ["student", "teacher"]:
            user.user_type = user_type

        return super().pre_social_login(request, sociallogin)
