from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

User = get_user_model()


@login_required
def dashboard_view(request):
    """Render the dashboard for authenticated users."""
    # Check if the user has connected their Google account
    has_google = SocialAccount.objects.filter(
        user=request.user, provider="google"
    ).exists()

    # Get user account information
    user_info = {
        "username": request.user.username,
        "email": request.user.email,
        "name": request.user.name,
        "date_joined": request.user.date_joined,
        "is_admin": request.user.is_staff or request.user.is_superuser,
        "has_google": has_google,
    }

    context = {
        "user_info": user_info,
    }

    # If Google connected, check token status
    if has_google:
        try:
            # Just check if token exists, we don't need the actual token
            SocialToken.objects.get(
                account__user=request.user, account__provider="google"
            )
            context["google_connected"] = True
        except SocialToken.DoesNotExist:
            context["google_connected"] = False

    return render(request, "dashboard.html", context)
