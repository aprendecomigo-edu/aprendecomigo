from django.urls import include, path
from knox import views as knox_views
from rest_framework.routers import DefaultRouter

from .views import (
    BiometricVerifyView,
    RequestEmailCodeView,
    SchoolInvitationViewSet,
    SchoolMembershipViewSet,
    SchoolViewSet,
    StudentViewSet,
    TeacherViewSet,
    UserViewSet,
    VerifyEmailCodeView,
)


app_name = "accounts"
# Create a router for API viewsets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"teachers", TeacherViewSet, basename="teacher")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"schools", SchoolViewSet, basename="school")
router.register(r"school-memberships", SchoolMembershipViewSet, basename="school_membership")
router.register(r"school-invitations", SchoolInvitationViewSet, basename="school_invitation")

# URL patterns for the accounts app
urlpatterns = [
    # ViewSet URLs - remove the 'api/' prefix, it should be added in the main urls.py
    path("", include(router.urls)),

    # Auth endpoints
    path(
        "auth/request-code/",
        RequestEmailCodeView.as_view(),
        name="request_code",
    ),
    path(
        "auth/verify-code/",
        VerifyEmailCodeView.as_view(),
        name="verify_code",
    ),
    path(
        "auth/biometric/",
        BiometricVerifyView.as_view(),
        name="biometric_auth",
    ),

    # Knox authentication URLs
    path("auth/logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("auth/logoutall/", knox_views.LogoutAllView.as_view(), name="knox_logoutall"),
]
