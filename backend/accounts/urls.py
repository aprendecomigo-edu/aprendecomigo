from django.urls import include, path
from knox import views as knox_views
from rest_framework.routers import DefaultRouter

from .views import (
    CourseViewSet,
    InvitationViewSet,
    RequestCodeView,
    SchoolInvitationLinkView,
    SchoolMembershipViewSet,
    SchoolViewSet,
    StudentViewSet,
    TeacherCourseViewSet,
    TeacherViewSet,
    UserViewSet,
    VerifyCodeView,
)

app_name = "accounts"
# Create a router for API viewsets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"teachers", TeacherViewSet, basename="teacher")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"schools", SchoolViewSet, basename="school")
router.register(r"school-memberships", SchoolMembershipViewSet, basename="school_membership")
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"teacher-courses", TeacherCourseViewSet, basename="teacher_course")
router.register(r"invitations", InvitationViewSet, basename="invitation")

# URL patterns for the accounts app
urlpatterns = [
    # ViewSet URLs - remove the 'api/' prefix, it should be added in the main urls.py
    path("", include(router.urls)),
    # Auth endpoints
    path(
        "auth/request-code/",
        RequestCodeView.as_view(),
        name="request_code",
    ),
    path(
        "auth/verify-code/",
        VerifyCodeView.as_view(),
        name="verify_code",
    ),
    # Invitation link endpoint (public)
    path(
        "invitation-links/<str:token>/",
        SchoolInvitationLinkView.as_view(),
        name="invitation_link_details",
    ),
    # Knox authentication URLs
    path("auth/logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("auth/logoutall/", knox_views.LogoutAllView.as_view(), name="knox_logoutall"),
]
