"""
API URL patterns for the accounts app - Django views for API endpoints
"""

from django.urls import path

from .api_views import StudentAPIView, TeacherAPIView

app_name = "accounts_api"

urlpatterns = [
    # Teacher and Student management APIs
    path("teachers/", TeacherAPIView.as_view(), name="teacher_api"),
    path("students/", StudentAPIView.as_view(), name="student_api"),
]