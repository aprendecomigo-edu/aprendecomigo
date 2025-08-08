"""
Views package for the accounts app.

This __init__.py file imports all views to maintain backward compatibility
with the original views.py structure while we complete the refactoring.

For now, we import from the parent views.py file to ensure nothing breaks.
As we complete the refactoring, we'll update these imports.
"""

# Import the base authentication classes we've already refactored
from .auth import (
    KnoxAuthenticatedAPIView,
    KnoxAuthenticatedViewSet,
    RequestCodeView,
    VerifyCodeView,
)

# Import user management classes we've already refactored
from .users import (
    UserViewSet,
    ParentProfileViewSet,
    ParentChildRelationshipViewSet,
)

# Import utility functions that were available in the original views module for backwards compatibility
from common.messaging import send_email_verification_code

# Import student management views
from .students import StudentViewSet

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
# from .schools import (
#     SchoolViewSet,
#     SchoolMembershipViewSet,
#     SchoolDashboardViewSet,
#     SchoolBrandingAPIView,
#     CommunicationSettingsAPIView,
# )
# from .teachers import (
#     TeacherViewSet,
#     TeacherProfileWizardViewSet,
#     TeacherProfileStepValidationView,
#     TeacherProfileCompletionStatusView,
# )

# For now, we'll keep these views in the existing schools.py and teachers.py files
# But they are not yet implemented - this is marked as TODO for future refactoring

# Export all views for backward compatibility
__all__ = [
    # Auth views (refactored)
    "KnoxAuthenticatedAPIView",
    "KnoxAuthenticatedViewSet", 
    "RequestCodeView",
    "VerifyCodeView",
    
    # User management (refactored)
    "UserViewSet",
    "ParentProfileViewSet",
    "ParentChildRelationshipViewSet",
    
    # School Management - TODO: Move remaining views to schools.py
    # "SchoolViewSet",
    # "SchoolMembershipViewSet", 
    # "SchoolDashboardViewSet",
    # "SchoolBrandingAPIView",
    # "CommunicationSettingsAPIView",
    
    # Teacher Management - TODO: Move remaining views to teachers.py
    # "TeacherViewSet",
    # "TeacherProfileWizardViewSet",
    # "TeacherProfileStepValidationView", 
    # "TeacherProfileCompletionStatusView",
    
    # Student Management (refactored)
    "StudentViewSet",
    
    # Course Management (refactored)
    "CourseViewSet",
    "EducationalSystemViewSet",
    "TeacherCourseViewSet",
    
    # Invitations (refactored)
    "InvitationViewSet",
    "SchoolInvitationLinkView",
    "TeacherInvitationViewSet",
    
    # Search & Discovery (refactored)
    "GlobalSearchView",
    "TutorDiscoveryAPIView",
    
    # Onboarding (refactored)
    "TutorOnboardingAPIView",
    "TutorOnboardingGuidanceView",
    "TutorOnboardingStartView",
    "TutorOnboardingValidateStepView", 
    "TutorOnboardingSaveProgressView",
    
    # Bulk Operations (refactored)
    "BulkTeacherActionsView",
    
    # Utility functions for backward compatibility
    "send_email_verification_code",
]