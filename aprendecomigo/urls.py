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

from classroom.views import ChatView

# Dashboard views
from dashboard.views import CalendarView, InvitationsView, PeopleView, StudentsView, TeachersView

urlpatterns = [
    # Admin route
    path("admin/", admin.site.urls),
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
    path("invitations/", InvitationsView.as_view(), name="invitations"),
    path("people/", PeopleView.as_view(), name="people"),

    # API routes for DRF endpoints
    path("api/accounts/", include("accounts.api_urls")),  # Account management APIs
    path("api/classroom/", include("classroom.urls")),  # Chat functionality (Django views)
    path("api/finances/", include("finances.urls")),  # Financial operations
    path("api/scheduler/", include("scheduler.urls")),  # Scheduling + Session booking
    path("api/", include("tasks.urls")),  # Task management
    path("api/messaging/", include("messaging.urls", namespace="messaging")),  # Messaging
    # Education routes (Milestone 3 - Core Educational Features)???
    path("education/", include("education.urls", namespace="education")),
    # Push notification endpoints
    path("webpush/", include("webpush.urls")),  # Push notification endpoints
]
