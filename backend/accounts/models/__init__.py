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
    AssessmentType,
    BrazilianEducationLevel,
    BrazilianSchoolYear,
    CalendarIntegrationChoices,
    CurrencyChoices,
    CustomEducationLevel,
    CustomSchoolYear,
    DataRetentionChoices,
    EducationalSystemType,
    EmailDeliveryStatus,
    EmailIntegrationChoices,
    InvitationStatus,
    LanguageChoices,
    PortugueseEducationLevel,
    PortugueseSchoolYear,
    RelationshipType,
    SchoolRole,
    StudentProgressLevel,
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
from .profiles import (
    ParentChildRelationship,
    ParentProfile,
    StudentProfile,
    TeacherProfile,
)

# Import progress tracking models
from .progress import (
    ProgressAssessment,
    StudentProgress,
)

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
__all__ = [
    # Enums
    "ActivityType",
    "AssessmentType",
    "BrazilianEducationLevel",
    "BrazilianSchoolYear",
    "CalendarIntegrationChoices",
    # Educational system
    "Course",
    "CurrencyChoices",
    "CustomEducationLevel",
    "CustomSchoolYear",
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
    "ParentChildRelationship",
    "ParentProfile",
    "PortugueseEducationLevel",
    "PortugueseSchoolYear",
    # Progress tracking
    "ProgressAssessment",
    "RelationshipType",
    # Schools
    "School",
    "SchoolActivity",
    # Invitations
    "SchoolInvitation",
    "SchoolInvitationLink",
    "SchoolMembership",
    "SchoolRole",
    "SchoolSettings",
    "StudentProfile",
    "StudentProgress",
    "StudentProgressLevel",
    "TeacherCourse",
    "TeacherInvitation",
    "TeacherInvitationManager",
    "TeacherProfile",
    "TrialCostAbsorption",
    "VerificationCode",
]
