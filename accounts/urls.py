from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Create a router for API viewsets
router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"teachers", views.TeacherViewSet, basename="teacher")
router.register(r"students", views.StudentViewSet, basename="student")

# URL patterns for the accounts app
urlpatterns = [
    # ViewSet URLs - remove the 'api/' prefix, it should be added in the main urls.py
    path("", include(router.urls)),
    path(
        "auth/request-code/",
        views.RequestEmailCodeView.as_view(),
        name="request_email_code",
    ),
    path(
        "auth/verify-code/",
        views.VerifyEmailCodeView.as_view(),
        name="verify_email_code",
    ),
    path("auth/profile/", views.UserProfileView.as_view(), name="user_profile"),
]
