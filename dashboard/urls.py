"""
Dashboard URLs with clean routes
"""

from django.urls import path

from .views import DashboardView

app_name = "dashboard"

urlpatterns = [
    # Main dashboard  - renders correct template based on user role
    path("", DashboardView.as_view(), name="dashboard"),
]
