"""
Models package for the accounts app.

This __init__.py file imports all models from their respective modules
to maintain backward compatibility with the original models.py structure.
"""

# Import all enums
# Import educational system models
from .educational import (
    Course,
    EducationalSystem,
    TeacherCourse,
)
from .enums import (
    ActivityType,
    CalendarIntegrationChoices,
    CurrencyChoices,
    DataRetentionChoices,
    EducationalSystemType,
    EmailDeliveryStatus,
    EmailIntegrationChoices,
    InvitationStatus,
    LanguageChoices,
    SchoolRole,
    TrialCostAbsorption,
)

# Import invitation models
from .invitations import (
    SchoolInvitation,
    SchoolInvitationLink,
    TeacherInvitation,
    TeacherInvitationManager,
)

# Import profile models
from .permissions import (
    StudentPermission,
)
from .profiles import (
    GuardianStudentRelationship,
    GuardianProfile,
    StudentProfile,
    TeacherProfile,
)

# Progress tracking models removed
# Import school models
from .schools import (
    School,
    SchoolActivity,
    SchoolMembership,
    SchoolSettings,
)

# Import user and authentication models
from .users import (
    CustomUser,
    CustomUserManager,
    VerificationCode,
)

# Define __all__ for explicit exports
# Define __all__ for explicit exports
__all__ = [
    # Enums
    "ActivityType",
    "CalendarIntegrationChoices",
    # Educational system
    "Course",
    "CurrencyChoices",
    # User and authentication
    "CustomUser",
    "CustomUserManager",
    "DataRetentionChoices",
    "EducationalSystem",
    "EducationalSystemType",
    "EmailDeliveryStatus",
    "EmailIntegrationChoices",
    "InvitationStatus",
    "LanguageChoices",
    # Profiles
    "GuardianStudentRelationship",
    "GuardianProfile",
    # Schools
    "School",
    "SchoolActivity",
    # Invitations
    "SchoolInvitation",
    "SchoolInvitationLink",
    "SchoolMembership",
    "SchoolRole",
    "SchoolSettings",
    "StudentPermission",
    "StudentProfile",
    "TeacherCourse",
    "TeacherInvitation",
    "TeacherInvitationManager",
    "TeacherProfile",
    "TrialCostAbsorption",
    "VerificationCode",
]
