from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from allauth.socialaccount.models import SocialAccount, SocialToken
from . import google_calendar

@login_required
def google_calendar_status(request):
    """API endpoint to check Google Calendar connection status."""
    has_google = SocialAccount.objects.filter(
        user=request.user,
        provider='google'
    ).exists()
    
    if has_google:
        # Check if we have a valid token
        try:
            token = SocialToken.objects.get(
                account__user=request.user,
                account__provider='google'
            )
            credentials = google_calendar.get_credentials(request.user)
            return JsonResponse({
                'connected': bool(credentials),
                'message': 'Google Calendar is connected' if credentials else 'Google Calendar token needs refresh'
            })
        except SocialToken.DoesNotExist:
            return JsonResponse({
                'connected': False,
                'message': 'Google Calendar authentication token missing'
            })
    else:
        return JsonResponse({
            'connected': False,
            'message': 'Google account not connected'
        })


@login_required
def connect_google_calendar(request):
    """View to guide users through connecting their Google Calendar."""
    has_google = SocialAccount.objects.filter(
        user=request.user,
        provider='google'
    ).exists()
    
    if request.method == 'POST' and not has_google:
        # User wants to connect - this will just display a message to use the Google login
        messages.info(request, 'Please sign in with your Google account to connect your calendar.')
        return redirect('google_login')
    
    context = {
        'has_google': has_google,
        'page_title': 'Connect Google Calendar',
    }
    
    # If they're already connected, show calendar fetch button
    if has_google:
        # Check if we have a valid token
        try:
            events = google_calendar.fetch_events(request.user, max_results=5)
            context['events'] = events
            context['has_events'] = len(events) > 0
        except Exception as e:
            context['error'] = str(e)
    
    return render(request, 'scheduling/connect_google.html', context)
