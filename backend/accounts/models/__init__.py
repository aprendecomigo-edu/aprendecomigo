"""
Models package for the accounts app.

This __init__.py file imports all models from their respective modules
to maintain backward compatibility with the original models.py structure.
"""

# Import all enums
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

# Import user and authentication models
from .users import (
    CustomUser,
    CustomUserManager,
    VerificationCode,
)

# Import educational system models
from .educational import (
    Course,
    EducationalSystem,
    TeacherCourse,
)

# Import school models
from .schools import (
    School,
    SchoolActivity,
    SchoolMembership,
    SchoolSettings,
)

# Import profile models
from .profiles import (
    ParentChildRelationship,
    ParentProfile,
    StudentProfile,
    TeacherProfile,
)

# Import invitation models
from .invitations import (
    SchoolInvitation,
    SchoolInvitationLink,
    TeacherInvitation,
    TeacherInvitationManager,
)

# Import progress tracking models
from .progress import (
    ProgressAssessment,
    StudentProgress,
)

# Define __all__ for explicit exports
__all__ = [
    # Enums
    "ActivityType",
    "AssessmentType", 
    "BrazilianEducationLevel",
    "BrazilianSchoolYear",
    "CalendarIntegrationChoices",
    "CurrencyChoices",
    "CustomEducationLevel",
    "CustomSchoolYear",
    "DataRetentionChoices",
    "EducationalSystemType",
    "EmailDeliveryStatus",
    "EmailIntegrationChoices",
    "InvitationStatus",
    "LanguageChoices",
    "PortugueseEducationLevel",
    "PortugueseSchoolYear",
    "RelationshipType",
    "SchoolRole",
    "StudentProgressLevel",
    "TrialCostAbsorption",
    
    # User and authentication
    "CustomUser",
    "CustomUserManager",
    "VerificationCode",
    
    # Educational system
    "Course",
    "EducationalSystem",
    "TeacherCourse",
    
    # Schools
    "School",
    "SchoolActivity",
    "SchoolMembership", 
    "SchoolSettings",
    
    # Profiles
    "ParentChildRelationship",
    "ParentProfile",
    "StudentProfile",
    "TeacherProfile",
    
    # Invitations
    "SchoolInvitation",
    "SchoolInvitationLink",
    "TeacherInvitation",
    "TeacherInvitationManager",
    
    # Progress tracking
    "ProgressAssessment",
    "StudentProgress",
]