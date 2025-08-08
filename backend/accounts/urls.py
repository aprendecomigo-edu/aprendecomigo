from django.urls import include, path
from knox import views as knox_views
from rest_framework.routers import DefaultRouter

from .views import (
    BulkTeacherActionsView,
    CourseViewSet,
    EducationalSystemViewSet,
    GlobalSearchView,
    InvitationViewSet,
    ParentChildRelationshipViewSet,
    ParentProfileViewSet,
    RequestCodeView,
    SchoolDashboardViewSet,
    SchoolInvitationLinkView,
    SchoolMembershipViewSet,
    SchoolViewSet,
    StudentViewSet,
    # TeacherAnalyticsView,  # TODO: This view needs to be implemented
    TeacherCourseViewSet,
    TeacherInvitationViewSet,
    TeacherProfileCompletionStatusView,
    TeacherProfileStepValidationView,
    TeacherProfileWizardViewSet,
    TeacherViewSet,
    TutorDiscoveryAPIView,
    TutorOnboardingGuidanceView,
    TutorOnboardingSaveProgressView,
    TutorOnboardingStartView,
    TutorOnboardingValidateStepView,
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
router.register(r"educational-systems", EducationalSystemViewSet, basename="educational_system")
router.register(r"teacher-courses", TeacherCourseViewSet, basename="teacher_course")
router.register(r"invitations", InvitationViewSet, basename="invitation")
router.register(r"teacher-invitations", TeacherInvitationViewSet, basename="teacher-invitation")
router.register(r"school-dashboard", SchoolDashboardViewSet, basename="school-dashboard")

# Parent-child account management endpoints
router.register(r"parent-profiles", ParentProfileViewSet, basename="parent-profiles")
router.register(r"parent-child-relationships", ParentChildRelationshipViewSet, basename="parent-child-relationships")

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
    # Global search endpoint
    path(
        "search/global/",
        GlobalSearchView.as_view(),
        name="global-search",
    ),
    # Bulk teacher actions endpoint
    path(
        "teachers/bulk-actions/",
        BulkTeacherActionsView.as_view(),
        name="bulk-teacher-actions",
    ),
    # Teacher analytics endpoint - TODO: Implement TeacherAnalyticsView
    # path(
    #     "schools/<int:school_id>/teacher-analytics/",
    #     TeacherAnalyticsView.as_view(),
    #     name="teacher-analytics",
    # ),
    # Teacher Profile Wizard endpoints
    path(
        "teachers/profile-wizard/<str:action>/",
        TeacherProfileWizardViewSet.as_view(),
        name="teacher-profile-wizard",
    ),
    path(
        "teachers/profile-completion-score/",
        TeacherProfileWizardViewSet.as_view(),
        {'action': 'profile-completion-score'},
        name="teacher-profile-completion-score",
    ),
    path(
        "teachers/rate-suggestions/",
        TeacherProfileWizardViewSet.as_view(),
        {'action': 'rate-suggestions'},
        name="teacher-rate-suggestions",
    ),
    # Tutor Discovery endpoint (public)
    path(
        "tutors/discover/",
        TutorDiscoveryAPIView.as_view(),
        name="tutor-discovery",
    ),
    # Tutor Onboarding endpoints
    path(
        "tutors/onboarding/guidance/",
        TutorOnboardingGuidanceView.as_view(),
        name="tutor-onboarding-guidance",
    ),
    path(
        "tutors/onboarding/start/",
        TutorOnboardingStartView.as_view(),
        name="tutor-onboarding-start",
    ),
    path(
        "tutors/onboarding/validate-step/",
        TutorOnboardingValidateStepView.as_view(),
        name="tutor-onboarding-validate-step",
    ),
    path(
        "tutors/onboarding/save-progress/",
        TutorOnboardingSaveProgressView.as_view(),
        name="tutor-onboarding-save-progress",
    ),
    # Wizard Orchestration endpoints (GitHub Issue #95)
    path(
        "teacher-profile/validate-step/",
        TeacherProfileStepValidationView.as_view(),
        name="teacher-profile-validate-step",
    ),
    path(
        "teacher-profile/completion-status/",
        TeacherProfileCompletionStatusView.as_view(),
        name="teacher-profile-completion-status",
    ),
    # Knox authentication URLs
    path("auth/logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("auth/logoutall/", knox_views.LogoutAllView.as_view(), name="knox_logoutall"),
]
