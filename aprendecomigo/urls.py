"""
URL configuration for aprendecomigo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import include, path

from accounts.views import dashboard_view, student_onboarding_view, user_type_selection_view


def home_view(request):
    """Redirect to dashboard if logged in, otherwise to allauth login page."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("account_login")  # Use allauth's login URL


urlpatterns = [
    path("", home_view, name="home"),
    path("admin/", admin.site.urls),
    path("dashboard/", login_required(dashboard_view), name="dashboard"),
    path("onboarding/student/", login_required(student_onboarding_view), name="student_onboarding"),
    path("onboarding/select-type/", login_required(user_type_selection_view), name="select_user_type"),
    # Django AllAuth URLs - keep this first for proper URL resolution
    path("accounts/", include("allauth.urls")),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
