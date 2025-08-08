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

# Import all remaining views from the original views file (renamed to views_original.py)
from ..views_original import (
    # School Management
    SchoolViewSet,
    SchoolMembershipViewSet,
    SchoolDashboardViewSet,
    SchoolBrandingAPIView,
    CommunicationSettingsAPIView,
    SchoolInvitationLinkView,
    
    # Teacher Management  
    TeacherViewSet,
    TeacherProfileWizardViewSet,
    TeacherProfileStepValidationView,
    TeacherProfileCompletionStatusView,
    
    # Student Management
    StudentViewSet,
    
    # Course Management
    CourseViewSet,
    EducationalSystemViewSet,
    TeacherCourseViewSet,
    
    # Invitations
    InvitationViewSet,
    TeacherInvitationViewSet,
    
    # Search & Discovery
    GlobalSearchView,
    TutorDiscoveryAPIView,
    
    # Onboarding
    TutorOnboardingAPIView,
    TutorOnboardingGuidanceView,
    TutorOnboardingStartView,
    TutorOnboardingValidateStepView,
    TutorOnboardingSaveProgressView,
    
    # Bulk Operations
    BulkTeacherActionsView,
)

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
    
    # School Management (from original file)
    "SchoolViewSet",
    "SchoolMembershipViewSet", 
    "SchoolDashboardViewSet",
    "SchoolBrandingAPIView",
    "CommunicationSettingsAPIView",
    "SchoolInvitationLinkView",
    
    # Teacher Management (from original file)
    "TeacherViewSet",
    "TeacherProfileWizardViewSet",
    "TeacherProfileStepValidationView", 
    "TeacherProfileCompletionStatusView",
    
    # Student Management (from original file)
    "StudentViewSet",
    
    # Course Management (from original file)
    "CourseViewSet",
    "EducationalSystemViewSet",
    "TeacherCourseViewSet",
    
    # Invitations (from original file)
    "InvitationViewSet",
    "TeacherInvitationViewSet",
    
    # Search & Discovery (from original file)
    "GlobalSearchView",
    "TutorDiscoveryAPIView",
    
    # Onboarding (from original file)
    "TutorOnboardingAPIView",
    "TutorOnboardingGuidanceView",
    "TutorOnboardingStartView",
    "TutorOnboardingValidateStepView", 
    "TutorOnboardingSaveProgressView",
    
    # Bulk Operations (from original file)
    "BulkTeacherActionsView",
    
    # Utility functions for backward compatibility
    "send_email_verification_code",
]