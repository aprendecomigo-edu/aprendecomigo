from django.shortcuts import render
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def dashboard_view(request):
    """Render the dashboard for authenticated users."""
    # Check if the user has connected their Google account
    has_google = SocialAccount.objects.filter(
        user=request.user,
        provider='google'
    ).exists()
    
    context = {
        'has_google': has_google,
    }
    
    # If Google connected, add calendar information
    if has_google:
        # Get the Google tokens
        try:
            google_token = SocialToken.objects.get(
                account__user=request.user,
                account__provider='google'
            )
            context['google_connected'] = True
        except SocialToken.DoesNotExist:
            context['google_connected'] = False
    
    return render(request, 'dashboard.html', context)
