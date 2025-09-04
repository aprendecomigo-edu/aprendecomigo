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

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

# Dashboard views
from dashboard.views import InvitationsView, PeopleView, StudentsView, TeachersView

# Scheduler views
from scheduler.views import CalendarView


# Health check for Railway deployment
def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    # Railway health check
    path("health/", health_check, name="health_check"),

    # Admin route
    path("admin/", admin.site.urls),
    # PWA infrastructure (django-pwa)
    path("", include("pwa.urls")),

    # Authentication and dashboard routes (HTML interface)
    path("", include("accounts.urls", namespace="accounts")),

    # Clean dashboard routes at root level
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
    path("calendar/", CalendarView.as_view(), name="calendar"),  # Calendar is now handled by scheduler
    path("teachers/", TeachersView.as_view(), name="teachers"),
    path("students/", StudentsView.as_view(), name="students"),
    path("invitations/", InvitationsView.as_view(), name="invitations"),
    path("people/", PeopleView.as_view(), name="people"),

    # PWA Routes
    path("classroom/", include("classroom.urls")),  # Chat functionality (Django views)
    path("finances/", include("finances.urls", namespace="finances")),  # Financial operations - Converted to Django views with HTMX
    path("messaging/", include("messaging.urls", namespace="messaging")),  # Messaging - Converted to Django views with HTMX
    # Education routes (Milestone 3 - Core Educational Features) - TODO: Create education app
    # path("education/", include("education.urls", namespace="education")),
    # Push notification endpoints
    path("webpush/", include("webpush.urls")),  # Push notification endpoints
]
