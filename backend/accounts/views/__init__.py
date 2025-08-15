"""
Views package for the accounts app.

This __init__.py file imports all views to maintain backward compatibility
with the original views.py structure while we complete the refactoring.

For now, we import from the parent views.py file to ensure nothing breaks.
As we complete the refactoring, we'll update these imports.
"""

# Import utility functions that were available in the original views module for backwards compatibility
from common.messaging import send_email_verification_code

from .auth import (
    KnoxAuthenticatedAPIView,
    KnoxAuthenticatedViewSet,
    RequestCodeView,
    VerifyCodeView,
)

# Import course management views
from .courses import (
    CourseViewSet,
    EducationalSystemViewSet,
    TeacherCourseViewSet,
)

# Import invitation views
from .invitations import (
    InvitationViewSet,
    SchoolInvitationLinkView,
    TeacherInvitationViewSet,
)

# Import onboarding and discovery views
from .onboarding import (
    BulkTeacherActionsView,
    GlobalSearchView,
    TutorDiscoveryAPIView,
    TutorOnboardingAPIView,
    TutorOnboardingGuidanceView,
    TutorOnboardingSaveProgressView,
    TutorOnboardingStartView,
    TutorOnboardingValidateStepView,
)

# Import remaining views from schools and teachers modules (not yet created)
# These imports are commented out until the remaining views are refactored:
from .schools import (
    CommunicationSettingsAPIView,
    SchoolBrandingAPIView,
    SchoolDashboardViewSet,
    SchoolMembershipViewSet,
    SchoolViewSet,
)

# Import student management views
from .students import StudentViewSet
from .teachers import (
    TeacherProfileCompletionStatusView,
    TeacherProfileStepValidationView,
    TeacherProfileWizardViewSet,
    TeacherViewSet,
)

# Import user management classes we've already refactored
from .users import (
    ParentChildRelationshipViewSet,
    ParentProfileViewSet,
    UserViewSet,
)

# For now, we'll keep these views in the existing schools.py and teachers.py files
# But they are not yet implemented - this is marked as TODO for future refactoring

# Export all views for backward compatibility
__all__ = [
    # Bulk Operations (refactored)
    "BulkTeacherActionsView",
    "CommunicationSettingsAPIView",
    # Course Management (refactored)
    "CourseViewSet",
    "EducationalSystemViewSet",
    # Search & Discovery (refactored)
    "GlobalSearchView",
    # Invitations (refactored)
    "InvitationViewSet",
    # Auth views (refactored)
    "KnoxAuthenticatedAPIView",
    "KnoxAuthenticatedViewSet",
    "ParentChildRelationshipViewSet",
    "ParentProfileViewSet",
    "RequestCodeView",
    "SchoolBrandingAPIView",
    "SchoolDashboardViewSet",
    "SchoolInvitationLinkView",
    "SchoolMembershipViewSet",
    # School Management
    "SchoolViewSet",
    # Student Management (refactored)
    "StudentViewSet",
    "TeacherCourseViewSet",
    "TeacherInvitationViewSet",
    "TeacherProfileCompletionStatusView",
    "TeacherProfileStepValidationView",
    "TeacherProfileWizardViewSet",
    # Teacher Management
    "TeacherViewSet",
    "TutorDiscoveryAPIView",
    # Onboarding (refactored)
    "TutorOnboardingAPIView",
    "TutorOnboardingGuidanceView",
    "TutorOnboardingSaveProgressView",
    "TutorOnboardingStartView",
    "TutorOnboardingValidateStepView",
    # User management (refactored)
    "UserViewSet",
    "VerifyCodeView",
    # Utility functions for backward compatibility
    "send_email_verification_code",
]
