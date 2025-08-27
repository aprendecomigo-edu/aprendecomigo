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
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


# Dashboard views
from dashboard.views import (
    CalendarView, ChatView, TeachersView, StudentsView, 
    AnalyticsView, InvitationsView, PeopleView
)

# API Documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Aprende Comigo API",
        default_version="v1",
        description="API for Aprende Comigo platform",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)



urlpatterns = [
    # Admin route
    path("admin/", admin.site.urls),
    # API Documentation
    path("api/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    
    # PWA infrastructure (django-pwa)
    path("", include("pwa.urls")),
    
    # Authentication and dashboard routes (HTML interface)
    path("accounts/", include("accounts.urls")),
    
    # Clean dashboard routes at root level
    path("dashboard/", include("dashboard.urls")),
    path("calendar/", CalendarView.as_view(), name="calendar"),
    path("chat/", ChatView.as_view(), name="chat"),
    path("teachers/", TeachersView.as_view(), name="teachers"),
    path("students/", StudentsView.as_view(), name="students"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("invitations/", InvitationsView.as_view(), name="invitations"),
    path("people/", PeopleView.as_view(), name="people"),
    
    # App routes for API - use api/ prefix for all API endpoints
    # TODO: Create separate API views for accounts when needed
    path("api/classroom/", include("classroom.urls")),  # Add classroom URLs
    path("api/finances/", include("finances.urls")),  # Add finances URLs
    path("api/scheduler/", include("scheduler.urls")),  # Add scheduler URLs
    path("api/", include("tasks.urls")),  # Add tasks URLs
    path("api/messaging/", include("messaging.urls", namespace="messaging")),  # Add messaging URLs
    # Education routes (Milestone 3 - Core Educational Features)
    path("education/", include("education.urls", namespace="education")),
    # Push notification endpoints
    path("webpush/", include("webpush.urls")),  # Push notification endpoints
]

# In development, serve static files for Swagger UI and media files for uploads
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
