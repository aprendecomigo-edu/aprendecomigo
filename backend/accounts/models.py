import logging
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Any, ClassVar, TypeVar

import pyotp
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Define type variables
T = TypeVar("T", bound="CustomUser")

logger = logging.getLogger(__name__)


class CustomUserManager(UserManager[T]):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of username.
    """

    def _create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> T:
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)

        # Generate a username from email if not provided
        if "username" not in extra_fields or not extra_fields["username"]:
            # Use the part before @ in the email
            username = email.split("@")[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while self.model.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            extra_fields["username"] = username

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # We simplify to a single signature to avoid mypy issues with overloading
    def create_user(  # type: ignore[override]
        self,
        email: str,
        **extra_fields: Any,
    ) -> T:
        """Create and save a regular user with the given credentials."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, **extra_fields)

    # We simplify to a single signature to avoid mypy issues with overloading
    def create_superuser(  # type: ignore[override]
        self,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> T:
        """Create and save a superuser with the given credentials."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self._create_user(email, password=password, **extra_fields)


class School(models.Model):
    """
    School model representing an educational organization.
    Can be an individual tutor's "school" or an actual educational institution.
    """

    name: models.CharField = models.CharField(_("name"), max_length=150)
    description: models.TextField = models.TextField(_("description"), blank=True)
    address: models.TextField = models.TextField(_("address"), blank=True)
    contact_email: models.EmailField = models.EmailField(_("contact email"), blank=True)
    phone_number: models.CharField = models.CharField(_("phone number"), max_length=20, blank=True)
    website: models.URLField = models.URLField(_("website"), blank=True)
    
    # Branding and visual identity
    logo: models.ImageField = models.ImageField(
        _("logo"), 
        upload_to="school_logos/", 
        blank=True, 
        null=True,
        help_text=_("School logo image")
    )
    primary_color: models.CharField = models.CharField(
        _("primary color"),
        max_length=7,
        default="#3B82F6",
        blank=True,
        help_text=_("Primary brand color in hex format")
    )
    secondary_color: models.CharField = models.CharField(
        _("secondary color"),
        max_length=7,
        default="#1F2937",
        blank=True,
        help_text=_("Secondary brand color in hex format")
    )
    email_domain: models.CharField = models.CharField(
        _("email domain"),
        max_length=100,
        blank=True,
        help_text=_("Official email domain for the school")
    )
    
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)


class CustomUser(AbstractUser):
    """
    Custom User model with email as primary identifier

    Django's built-in permissions:
    - is_superuser: Can access Django admin and has all permissions
    - is_staff: Can access Django admin with limited permissions (admin-only)

    These are used for backend system administration, not for application roles.
    Application roles are managed through SchoolMembership model.
    """

    username: models.CharField = models.CharField(
        _("username"), max_length=150, blank=True, null=True
    )
    email: models.EmailField = models.EmailField(_("email address"), unique=True)
    name: models.CharField = models.CharField(_("name"), max_length=150)
    phone_number: models.CharField = models.CharField(_("phone number"), max_length=20, blank=True)
    
    # Profile information
    profile_photo: models.ImageField = models.ImageField(
        _("profile photo"),
        upload_to="profile_photos/",
        blank=True,
        null=True,
        help_text=_("User profile photo")
    )

    # Contact verification fields
    primary_contact: models.CharField = models.CharField(
        _("primary contact"),
        max_length=10,
        choices=[("email", _("Email")), ("phone", _("Phone"))],
        default="email",
    )
    email_verified: models.BooleanField = models.BooleanField(_("email verified"), default=False)
    phone_verified: models.BooleanField = models.BooleanField(_("phone verified"), default=False)

    # Tutorial and onboarding fields
    first_login_completed: models.BooleanField = models.BooleanField(
        _("first login completed"), default=False
    )
    onboarding_completed: models.BooleanField = models.BooleanField(
        _("onboarding completed"), default=False
    )
    onboarding_progress: models.JSONField = models.JSONField(
        _("onboarding progress"), default=dict, blank=True
    )
    tutorial_preferences: models.JSONField = models.JSONField(
        _("tutorial preferences"), default=dict, blank=True
    )

    # user_type field is removed - roles are now in SchoolMembership

    USERNAME_FIELD: str = "email"  # type: ignore[assignment]
    REQUIRED_FIELDS: ClassVar[list[str]] = ["name"]

    # Use a type annotation that doesn't conflict with the parent class
    # but allows us to provide our custom manager
    objects = CustomUserManager()  # type: ignore[misc]

    def __str__(self) -> str:
        return str(self.email)


class SchoolRole(models.TextChoices):
    SCHOOL_OWNER = (
        "school_owner",
        _("School Owner"),
    )  # Created the school, has full access
    SCHOOL_ADMIN = (
        "school_admin",
        _("School Administrator"),
    )  # Can manage all aspects of the school
    TEACHER = "teacher", _("Teacher")  # Can manage classes and students
    SCHOOL_STAFF = (
        "school_staff",
        _("School Staff"),
    )  # Limited access for administrative tasks
    STUDENT = "student", _("Student")  # Access to assigned classes


class SchoolMembership(models.Model):
    """
    Represents a user's membership in a school with specific role.
    Users can have multiple memberships across different schools with different roles.

    This replaces the previous user_type field and clearly separates application
    roles from Django's built-in permissions system.
    """

    user: models.ForeignKey = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="school_memberships"
    )
    school: models.ForeignKey = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="memberships"
    )
    role: models.CharField = models.CharField(_("role"), max_length=20, choices=SchoolRole.choices)
    is_active: models.BooleanField = models.BooleanField(_("is active"), default=True)
    joined_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together: ClassVar[list[str]] = ["user", "school", "role"]
        indexes = [
            models.Index(fields=['school', 'role', 'is_active']),
            models.Index(fields=['school', 'joined_at']),
        ]

    def __str__(self) -> str:
        user_name = self.user.name if hasattr(self.user, "name") else str(self.user)
        school_name = self.school.name if hasattr(self.school, "name") else str(self.school)
        return f"{user_name} as {self.get_role_display()} at {school_name}"

    def get_role_display(self) -> str:
        """Get the display value for the role."""
        role_display = dict(SchoolRole.choices).get(self.role, self.role)
        return str(role_display)  # Convert _StrPromise to str


# Educational System Enumerations
class PortugueseSchoolYear(models.TextChoices):
    """School years for Portuguese education system"""

    FIRST = "1", _("1º ano")
    SECOND = "2", _("2º ano")
    THIRD = "3", _("3º ano")
    FOURTH = "4", _("4º ano")
    FIFTH = "5", _("5º ano")
    SIXTH = "6", _("6º ano")
    SEVENTH = "7", _("7º ano")
    EIGHTH = "8", _("8º ano")
    NINTH = "9", _("9º ano")
    TENTH = "10", _("10º ano")
    ELEVENTH = "11", _("11º ano")
    TWELFTH = "12", _("12º ano")


class PortugueseEducationLevel(models.TextChoices):
    """Education levels for Portuguese system"""

    BASIC_1ST_CYCLE = "ensino_basico_1_ciclo", _("Ensino Básico 1º Ciclo")
    BASIC_2ND_CYCLE = "ensino_basico_2_ciclo", _("Ensino Básico 2º Ciclo")
    BASIC_3RD_CYCLE = "ensino_basico_3_ciclo", _("Ensino Básico 3º Ciclo")
    SECONDARY = "ensino_secundario", _("Ensino Secundário")


class CustomSchoolYear(models.TextChoices):
    """School years for custom/generic education system"""

    GRADE_1 = "1", _("Grade 1")
    GRADE_2 = "2", _("Grade 2")
    GRADE_3 = "3", _("Grade 3")
    GRADE_4 = "4", _("Grade 4")
    GRADE_5 = "5", _("Grade 5")
    GRADE_6 = "6", _("Grade 6")
    GRADE_7 = "7", _("Grade 7")
    GRADE_8 = "8", _("Grade 8")
    GRADE_9 = "9", _("Grade 9")
    GRADE_10 = "10", _("Grade 10")
    GRADE_11 = "11", _("Grade 11")
    GRADE_12 = "12", _("Grade 12")


class CustomEducationLevel(models.TextChoices):
    """Education levels for custom/generic system"""

    ELEMENTARY = "elementary", _("Elementary")
    MIDDLE_SCHOOL = "middle_school", _("Middle School")
    HIGH_SCHOOL = "high_school", _("High School")


class BrazilianSchoolYear(models.TextChoices):
    """School years for Brazilian education system"""

    # Elementary I (Ensino Fundamental I)
    FIRST_EF = "1ef", _("1º ano EF")
    SECOND_EF = "2ef", _("2º ano EF")
    THIRD_EF = "3ef", _("3º ano EF")
    FOURTH_EF = "4ef", _("4º ano EF")
    FIFTH_EF = "5ef", _("5º ano EF")
    # Elementary II (Ensino Fundamental II)
    SIXTH_EF = "6ef", _("6º ano EF")
    SEVENTH_EF = "7ef", _("7º ano EF")
    EIGHTH_EF = "8ef", _("8º ano EF")
    NINTH_EF = "9ef", _("9º ano EF")
    # High School (Ensino Médio)
    FIRST_EM = "1em", _("1º ano EM")
    SECOND_EM = "2em", _("2º ano EM")
    THIRD_EM = "3em", _("3º ano EM")


class BrazilianEducationLevel(models.TextChoices):
    """Education levels for Brazilian system"""

    FUNDAMENTAL_INITIAL = "ensino_fundamental_anos_iniciais", _("Ensino Fundamental Anos Iniciais")
    FUNDAMENTAL_FINAL = "ensino_fundamental_anos_finais", _("Ensino Fundamental Anos Finais")
    MEDIO = "ensino_medio", _("Ensino Médio")


class EducationalSystemType(models.TextChoices):
    """Types of educational systems"""

    PORTUGAL = "pt", _("Portugal")
    CUSTOM = "custom", _("Custom")
    BRAZIL = "br", _("Brazil")


class EducationalSystem(models.Model):
    """
    Educational system model representing different education systems and their school years.
    Now uses Django enumeration types for better type safety and validation.
    """

    name: models.CharField = models.CharField(
        _("system name"),
        max_length=100,
        help_text=_("Name of the educational system (e.g., 'Portugal', 'Brazil')"),
    )
    code: models.CharField = models.CharField(
        _("system code"),
        max_length=20,
        unique=True,
        choices=EducationalSystemType.choices,
        help_text=_("Unique code for the system (e.g., 'pt', 'br')"),
    )
    description: models.TextField = models.TextField(
        _("description"), blank=True, help_text=_("Description of the educational system")
    )
    is_active: models.BooleanField = models.BooleanField(_("is active"), default=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Educational System")
        verbose_name_plural = _("Educational Systems")

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def school_year_choices(self):
        """Get the appropriate school year choices for this educational system"""
        if self.code == EducationalSystemType.PORTUGAL:
            return PortugueseSchoolYear.choices
        elif self.code == EducationalSystemType.BRAZIL:
            return BrazilianSchoolYear.choices
        else:  # custom or any other system
            return CustomSchoolYear.choices

    @property
    def education_level_choices(self):
        """Get the appropriate education level choices for this educational system"""
        if self.code == EducationalSystemType.PORTUGAL:
            return PortugueseEducationLevel.choices
        elif self.code == EducationalSystemType.BRAZIL:
            return BrazilianEducationLevel.choices
        else:  # custom or any other system
            return CustomEducationLevel.choices

    def validate_school_year(self, school_year_value):
        """Validate that a school year is valid for this educational system"""
        valid_choices = dict(self.school_year_choices)
        return school_year_value in valid_choices

    def validate_education_level(self, education_level_value):
        """Validate that an education level is valid for this educational system"""
        valid_choices = dict(self.education_level_choices)
        return education_level_value in valid_choices

    def get_school_year_display(self, school_year_value):
        """Get the display name for a school year value"""
        choices_dict = dict(self.school_year_choices)
        return choices_dict.get(school_year_value, school_year_value)

    def get_education_level_display(self, education_level_value):
        """Get the display name for an education level value"""
        choices_dict = dict(self.education_level_choices)
        return choices_dict.get(education_level_value, education_level_value)


class StudentProfile(models.Model):
    """
    Student profile with additional information.
    A user can have this profile regardless of which schools they belong to as a student.
    """

    user: models.OneToOneField = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="student_profile"
    )
    educational_system: models.ForeignKey = models.ForeignKey(
        EducationalSystem,
        on_delete=models.CASCADE,
        related_name="students",
        help_text=_("Educational system this student belongs to"),
        default=1,  # Portugal system as default
    )
    school_year: models.CharField = models.CharField(
        _("school year"), max_length=50, help_text=_("School year within the educational system")
    )
    birth_date: models.DateField = models.DateField(_("birth date"))
    # Sensitive personal data fields
    address: models.TextField = models.TextField(
        _("address"), blank=True, help_text=_("Street, number, postal code and location")
    )
    cc_number: models.CharField = models.CharField(_("CC number"), max_length=20, blank=True)
    cc_photo: models.ImageField = models.ImageField(
        _("CC photo"),
        upload_to="cc_photos/",
        blank=True,
        null=True,
        help_text=_("Photo of CC front and back (only for in-person students)"),
    )
    calendar_iframe: models.TextField = models.TextField(_("calendar iframe"), blank=True)

    def __str__(self) -> str:
        user_name = self.user.name if hasattr(self.user, "name") else str(self.user)
        return f"Student Profile: {user_name}"

    def clean(self):
        """Validate that school_year is valid for the selected educational system"""
        super().clean()
        if self.educational_system and self.school_year:
            if not self.educational_system.validate_school_year(self.school_year):
                from django.core.exceptions import ValidationError

                valid_years = dict(self.educational_system.school_year_choices)
                raise ValidationError(
                    {
                        "school_year": f"School year '{self.school_year}' is not valid for "
                        f"educational system '{self.educational_system.name}'. "
                        f"Valid options: {list(valid_years.keys())}"
                    }
                )


class TeacherProfile(models.Model):
    """
    Teacher profile with additional information.
    A user can have this profile regardless of which schools they belong to as a teacher.
    
    Enhanced with structured data fields for better profile management and completion tracking.
    """

    user: models.OneToOneField = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="teacher_profile"
    )
    bio: models.TextField = models.TextField(
        _("biography"), blank=True, help_text=_("Teacher's professional biography")
    )
    specialty: models.CharField = models.CharField(_("specialty"), max_length=100, blank=True)
    education: models.TextField = models.TextField(
        _("education"),
        blank=True,
        help_text=_("Educational background and qualifications"),
    )
    hourly_rate: models.DecimalField = models.DecimalField(
        _("hourly rate"), max_digits=6, decimal_places=2, null=True, blank=True
    )
    availability: models.TextField = models.TextField(
        _("availability"),
        blank=True,
        help_text=_("Available days and times for lessons"),
    )
    # Sensitive personal data fields
    address: models.TextField = models.TextField(
        _("address"),
        blank=True,
        help_text=_("Street, number, postal code and location"),
    )
    phone_number: models.CharField = models.CharField(_("teacher phone"), max_length=20, blank=True)
    calendar_iframe: models.TextField = models.TextField(_("calendar iframe"), blank=True)
    
    # New structured data fields for enhanced profile management
    education_background: models.JSONField = models.JSONField(
        _("education background"),
        default=dict,
        blank=True,
        help_text=_("Structured educational background data (degree, institution, field, year)")
    )
    teaching_subjects: models.JSONField = models.JSONField(
        _("teaching subjects"),
        default=list,
        blank=True,
        help_text=_("List of subjects the teacher specializes in")
    )
    rate_structure: models.JSONField = models.JSONField(
        _("rate structure"),
        default=dict,
        blank=True,
        help_text=_("Detailed rate structure for different class types")
    )
    weekly_availability: models.JSONField = models.JSONField(
        _("weekly availability"),
        default=dict,
        blank=True,
        help_text=_("Structured weekly availability schedule")
    )
    
    # Enhanced profile fields for comprehensive teacher profile creation
    grade_level_preferences: models.JSONField = models.JSONField(
        _("grade level preferences"),
        default=list,
        blank=True,
        help_text=_("List of preferred grade levels (elementary, middle, high school, university)")
    )
    teaching_experience: models.JSONField = models.JSONField(
        _("teaching experience"),
        default=dict,
        blank=True,
        help_text=_("Structured teaching experience data (years, institutions, specializations)")
    )
    credentials_documents: models.JSONField = models.JSONField(
        _("credentials documents"),
        default=list,
        blank=True,
        help_text=_("List of uploaded credential document references")
    )
    availability_schedule: models.JSONField = models.JSONField(
        _("availability schedule"),
        default=dict,
        blank=True,
        help_text=_("Detailed availability schedule with time slots and preferences")
    )
    
    # Profile completion tracking fields
    profile_completion_score: models.DecimalField = models.DecimalField(
        _("profile completion score"),
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text=_("Calculated profile completion percentage (0-100)")
    )
    is_profile_complete: models.BooleanField = models.BooleanField(
        _("is profile complete"),
        default=False,
        help_text=_("Whether the profile meets completion requirements")
    )
    last_profile_update: models.DateTimeField = models.DateTimeField(
        _("last profile update"),
        auto_now=True,
        help_text=_("When the profile was last updated")
    )
    
    # Activity tracking for school administrators
    last_activity: models.DateTimeField = models.DateTimeField(
        _("last activity"),
        null=True,
        blank=True,
        help_text=_("When the teacher was last active in the system")
    )

    class Meta:
        indexes = [
            models.Index(fields=['profile_completion_score']),
            models.Index(fields=['is_profile_complete']),
            models.Index(fields=['last_profile_update']),
            models.Index(fields=['last_activity']),
            # Indexes for tutor discovery optimization
            models.Index(fields=['specialty']),
            models.Index(fields=['hourly_rate']),
            models.Index(fields=['is_profile_complete', '-profile_completion_score']),
            models.Index(fields=['is_profile_complete', 'hourly_rate']),
        ]

    def __str__(self) -> str:
        user_name = self.user.name if hasattr(self.user, "name") else str(self.user)
        return f"Teacher Profile: {user_name}"
    
    def update_completion_score(self) -> None:
        """Update the profile completion score using ProfileCompletionService."""
        from .services.profile_completion import ProfileCompletionService
        
        try:
            completion_data = ProfileCompletionService.calculate_completion(self)
            self.profile_completion_score = completion_data['completion_percentage']
            self.is_profile_complete = completion_data['is_complete']
            self.save(update_fields=['profile_completion_score', 'is_profile_complete', 'last_profile_update'])
        except Exception as e:
            logger.error(f"Failed to update completion score for teacher {self.id}: {e}")
    
    def get_school_memberships(self):
        """Get all school memberships for this teacher."""
        return self.user.school_memberships.filter(
            role=SchoolRole.TEACHER,
            is_active=True
        ).select_related('school')
    
    def get_completion_data(self) -> dict:
        """Get detailed completion data for this profile."""
        from .services.profile_completion import ProfileCompletionService
        return ProfileCompletionService.calculate_completion(self)
    
    def mark_activity(self) -> None:
        """Mark that the teacher was active."""
        from django.utils import timezone
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class Course(models.Model):
    """
    Course model representing a subject or course that can be taught.
    Independent of teachers - teachers can be associated through TeacherCourse.
    """

    name: models.CharField = models.CharField(_("course name"), max_length=150)
    code: models.CharField = models.CharField(
        _("course code"),
        max_length=20,
        help_text=_("Alphanumeric code for the course (e.g., educational system codes)"),
    )
    educational_system: models.ForeignKey = models.ForeignKey(
        EducationalSystem,
        on_delete=models.CASCADE,
        related_name="courses",
        help_text=_("Educational system this course belongs to"),
    )
    education_level: models.CharField = models.CharField(
        _("education level"),
        max_length=50,
        default="other",
        help_text=_("Education level within the educational system"),
    )
    description: models.TextField = models.TextField(
        _("course description"),
        blank=True,
        help_text=_("Detailed description of the course content and objectives"),
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together: ClassVar = ["code", "educational_system"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def clean(self):
        """Validate that education_level is valid for the selected educational system"""
        super().clean()
        if self.educational_system and self.education_level:
            if not self.educational_system.validate_education_level(self.education_level):
                from django.core.exceptions import ValidationError

                valid_levels = dict(self.educational_system.education_level_choices)
                raise ValidationError(
                    {
                        "education_level": f"Education level '{self.education_level}' is not valid for "
                        f"educational system '{self.educational_system.name}'. "
                        f"Valid options: {list(valid_levels.keys())}"
                    }
                )


class TeacherCourse(models.Model):
    """
    Many-to-Many relationship between Teacher and Course.
    Allows teachers to teach multiple courses and courses to be taught by multiple teachers.
    """

    teacher: models.ForeignKey = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name="teacher_courses"
    )
    course: models.ForeignKey = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="course_teachers"
    )
    # Optional fields for teacher-specific course information
    hourly_rate: models.DecimalField = models.DecimalField(
        _("hourly rate for this course"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Specific hourly rate for this course (overrides teacher's default rate)"),
    )
    is_active: models.BooleanField = models.BooleanField(_("is actively teaching"), default=True)
    started_teaching: models.DateField = models.DateField(
        _("started teaching date"), auto_now_add=True
    )

    class Meta:
        unique_together: ClassVar = ["teacher", "course"]
        indexes = [
            # Indexes for tutor discovery filtering
            models.Index(fields=['hourly_rate']),
            models.Index(fields=['is_active', 'hourly_rate']),
            models.Index(fields=['course', 'is_active']),
            models.Index(fields=['teacher', 'is_active']),
        ]

    def __str__(self) -> str:
        teacher_name = (
            self.teacher.user.name
            if hasattr(self.teacher, "user") and hasattr(self.teacher.user, "name")
            else str(self.teacher.user)
        )
        return f"{teacher_name} teaches {self.course.name}"


class SchoolInvitation(models.Model):
    """
    Invitation for a user to join a school with a specific role
    """

    school: models.ForeignKey = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="invitations"
    )
    email: models.EmailField = models.EmailField(_("email address"))
    invited_by: models.ForeignKey = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="sent_invitations"
    )
    role: models.CharField = models.CharField(_("role"), max_length=20, choices=SchoolRole.choices)
    token: models.CharField = models.CharField(_("token"), max_length=64, unique=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    expires_at: models.DateTimeField = models.DateTimeField()
    is_accepted: models.BooleanField = models.BooleanField(_("is accepted"), default=False)

    def __str__(self) -> str:
        school_name = self.school.name if hasattr(self.school, "name") else str(self.school)
        return f"Invitation to {self.email} for {school_name} as {self.get_role_display()}"

    def is_valid(self) -> bool:
        return not self.is_accepted and timezone.now() < self.expires_at

    def get_role_display(self) -> str:
        """Get the display value for the role."""
        role_display = dict(SchoolRole.choices).get(self.role, self.role)
        return str(role_display)  # Convert _StrPromise to str


class SchoolInvitationLink(models.Model):
    """
    Generic invitation link for a school - not tied to specific users.
    Anyone with the link can join the school in the specified role.
    """

    school: models.ForeignKey = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="invitation_links"
    )
    role: models.CharField = models.CharField(_("role"), max_length=20, choices=SchoolRole.choices)
    token: models.CharField = models.CharField(_("token"), max_length=64, unique=True)
    created_by: models.ForeignKey = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="created_invitation_links"
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    expires_at: models.DateTimeField = models.DateTimeField()
    is_active: models.BooleanField = models.BooleanField(_("is active"), default=True)
    usage_count: models.PositiveIntegerField = models.PositiveIntegerField(
        _("usage count"), default=0
    )
    max_uses: models.PositiveIntegerField = models.PositiveIntegerField(
        _("max uses"), null=True, blank=True, help_text=_("Leave blank for unlimited uses")
    )

    class Meta:
        unique_together: ClassVar = ["school", "role"]  # One active link per school per role

    def __str__(self) -> str:
        school_name = self.school.name if hasattr(self.school, "name") else str(self.school)
        return f"Invitation link for {school_name} as {self.get_role_display()}"

    def is_valid(self) -> bool:
        """Check if the invitation link is still valid."""
        if not self.is_active:
            return False
        if timezone.now() > self.expires_at:
            return False
        if self.max_uses and self.usage_count >= self.max_uses:
            return False
        return True

    def increment_usage(self) -> None:
        """Increment the usage count."""
        self.usage_count += 1
        self.save(update_fields=["usage_count"])

    def get_role_display(self) -> str:
        """Get the display value for the role."""
        role_display = dict(SchoolRole.choices).get(self.role, self.role)
        return str(role_display)  # Convert _StrPromise to str


class VerificationCode(models.Model):
    """
    Model for storing verification codes.
    """

    email: models.EmailField = models.EmailField()
    secret_key: models.CharField = models.CharField(
        max_length=32
    )  # For TOTP - unique for each instance, no default
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    last_code_generated_at: models.DateTimeField = models.DateTimeField(auto_now=True)
    is_used: models.BooleanField = models.BooleanField(default=False)
    failed_attempts: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(default=0)
    max_attempts: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(default=5)

    class Meta:
        indexes: ClassVar = [
            models.Index(fields=["email", "is_used"]),
            models.Index(fields=["email", "created_at"]),
        ]

    @classmethod
    def generate_code(cls, email: str) -> "VerificationCode":
        """Generate a TOTP secret for the given email"""
        # Delete any existing unused codes for this email
        cls.objects.filter(email=email, is_used=False).delete()

        # Generate a new secret key for TOTP
        secret = pyotp.random_base32()

        # Create and return a new verification object
        return cls.objects.create(email=email, secret_key=secret)

    def get_current_code(self) -> str:
        """Get the current TOTP code"""
        totp = pyotp.TOTP(self.secret_key, digits=6, interval=300)
        code = totp.now()
        return code

    def get_provisioning_uri(self, email: str | None = None) -> str:
        """Get the TOTP provisioning URI for QR codes"""
        email = email or self.email
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(name=email, issuer_name="Aprende Comigo")

    def is_valid(self, code: str | None = None, digits=6, interval=300) -> bool:
        """
        Check if the code is still valid (not used, not expired, and not too many failed attempts)

        If code is provided, also verify the TOTP code.
        """
        if self.is_used:
            return False

        if self.failed_attempts >= self.max_attempts:
            return False
        # Expire codes after 24 hours regardless of TOTP validity
        if timezone.now() - self.created_at > timedelta(hours=24):
            return False
        # If code is provided, verify it
        if code:
            totp = pyotp.TOTP(self.secret_key, digits=digits, interval=interval)
            result = totp.verify(code)
            return bool(result)

        return True

    def use(self) -> None:
        """Mark the code as used"""
        self.is_used = True
        self.save()

    def record_failed_attempt(self) -> bool:
        """Record a failed verification attempt"""
        self.failed_attempts += 1
        self.save()
        return self.failed_attempts >= self.max_attempts


class ActivityType(models.TextChoices):
    """Types of activities that can occur in a school"""
    
    INVITATION_SENT = "invitation_sent", _("Invitation Sent")
    INVITATION_ACCEPTED = "invitation_accepted", _("Invitation Accepted")
    INVITATION_DECLINED = "invitation_declined", _("Invitation Declined")
    STUDENT_JOINED = "student_joined", _("Student Joined")
    TEACHER_JOINED = "teacher_joined", _("Teacher Joined")
    CLASS_CREATED = "class_created", _("Class Created")
    CLASS_COMPLETED = "class_completed", _("Class Completed")
    CLASS_CANCELLED = "class_cancelled", _("Class Cancelled")
    SETTINGS_UPDATED = "settings_updated", _("Settings Updated")


class SchoolActivity(models.Model):
    """
    Model to track all school-related activities for admin dashboard
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="activities_performed")
    target_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities_targeted")
    target_class = models.ForeignKey('finances.ClassSession', on_delete=models.SET_NULL, null=True, blank=True)
    target_invitation = models.ForeignKey(SchoolInvitation, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    description = models.TextField()
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['school', '-timestamp']),
            models.Index(fields=['school', 'activity_type', '-timestamp']),
            models.Index(fields=['actor', '-timestamp']),
        ]
        
    def __str__(self) -> str:
        return f"{self.school.name}: {self.activity_type} at {self.timestamp}"


class TrialCostAbsorption(models.TextChoices):
    """Options for who absorbs trial class costs"""
    
    SCHOOL = "school", _("School")
    TEACHER = "teacher", _("Teacher")
    SPLIT = "split", _("Split")


class CurrencyChoices(models.TextChoices):
    """Currency options for school billing"""
    
    EUR = "EUR", _("Euro")
    USD = "USD", _("US Dollar")
    BRL = "BRL", _("Brazilian Real")
    GBP = "GBP", _("British Pound")


class LanguageChoices(models.TextChoices):
    """Language options for school interface"""
    
    PT = "pt", _("Portuguese")
    EN = "en", _("English")
    ES = "es", _("Spanish")
    FR = "fr", _("French")


class CalendarIntegrationChoices(models.TextChoices):
    """Calendar integration options"""
    
    GOOGLE = "google", _("Google Calendar")
    OUTLOOK = "outlook", _("Microsoft Outlook")
    CALDAV = "caldav", _("CalDAV")


class EmailIntegrationChoices(models.TextChoices):
    """Email integration options"""
    
    GMAIL = "gmail", _("Gmail")
    OUTLOOK = "outlook", _("Outlook")
    CUSTOM = "custom", _("Custom SMTP")


class DataRetentionChoices(models.TextChoices):
    """Data retention policy options"""
    
    ONE_YEAR = "1_year", _("1 Year")
    TWO_YEARS = "2_years", _("2 Years")
    FIVE_YEARS = "5_years", _("5 Years")
    INDEFINITE = "indefinite", _("Indefinite")


class SchoolSettings(models.Model):
    """
    Comprehensive settings for schools including operational, billing, and configuration options
    """
    
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name="settings")
    
    # Educational system configuration
    educational_system: models.ForeignKey = models.ForeignKey(
        EducationalSystem,
        on_delete=models.PROTECT,
        related_name="schools_using_system",
        help_text=_("Educational system used by this school"),
        verbose_name=_("educational system"),
        default=1  # Portugal system as default
    )
    grade_levels: models.JSONField = models.JSONField(
        _("grade levels"),
        default=list,
        blank=True,
        help_text=_("List of grade levels offered by this school")
    )
    
    # Operational settings
    trial_cost_absorption = models.CharField(
        max_length=20, 
        choices=TrialCostAbsorption.choices, 
        default=TrialCostAbsorption.SCHOOL
    )
    default_session_duration = models.PositiveIntegerField(
        default=60, 
        help_text="Default session duration in minutes"
    )
    timezone = models.CharField(max_length=50, default="UTC")
    
    # Billing configuration
    billing_contact_name: models.CharField = models.CharField(
        _("billing contact name"),
        max_length=100,
        blank=True,
        help_text=_("Name of billing contact person")
    )
    billing_contact_email: models.EmailField = models.EmailField(
        _("billing contact email"),
        blank=True,
        help_text=_("Email for billing-related communications")
    )
    billing_address: models.TextField = models.TextField(
        _("billing address"),
        blank=True,
        help_text=_("Billing address for invoices and payments")
    )
    tax_id: models.CharField = models.CharField(
        _("tax ID"),
        max_length=50,
        blank=True,
        help_text=_("Tax identification number for billing")
    )
    currency_code: models.CharField = models.CharField(
        _("currency"),
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.EUR,
        help_text=_("Default currency for pricing and billing")
    )
    
    # Localization settings
    language: models.CharField = models.CharField(
        _("language"),
        max_length=5,
        choices=LanguageChoices.choices,
        default=LanguageChoices.PT,
        help_text=_("Default language for the school interface")
    )
    
    # Schedule and availability settings
    working_hours_start: models.TimeField = models.TimeField(
        _("working hours start"),
        default="08:00",
        help_text=_("School working hours start time")
    )
    working_hours_end: models.TimeField = models.TimeField(
        _("working hours end"),
        default="18:00",
        help_text=_("School working hours end time")
    )
    working_days: models.JSONField = models.JSONField(
        _("working days"),
        default=list,
        help_text=_("List of working days (0=Monday, 6=Sunday)")
    )
    
    # Communication preferences
    email_notifications_enabled: models.BooleanField = models.BooleanField(
        _("email notifications enabled"),
        default=True,
        help_text=_("Enable email notifications for school events")
    )
    sms_notifications_enabled: models.BooleanField = models.BooleanField(
        _("SMS notifications enabled"),
        default=False,
        help_text=_("Enable SMS notifications for school events")
    )
    
    # User permissions and access control
    allow_student_self_enrollment: models.BooleanField = models.BooleanField(
        _("allow student self-enrollment"),
        default=False,
        help_text=_("Allow students to enroll themselves")
    )
    require_parent_approval: models.BooleanField = models.BooleanField(
        _("require parent approval"),
        default=True,
        help_text=_("Require parental approval for student actions")
    )
    auto_assign_teachers: models.BooleanField = models.BooleanField(
        _("auto assign teachers"),
        default=False,
        help_text=_("Automatically assign available teachers to classes")
    )
    class_reminder_hours: models.PositiveIntegerField = models.PositiveIntegerField(
        _("class reminder hours"),
        default=24,
        help_text=_("Hours before class to send reminder notifications")
    )
    
    # Integration settings
    enable_calendar_integration: models.BooleanField = models.BooleanField(
        _("enable calendar integration"),
        default=False,
        help_text=_("Enable integration with external calendar systems")
    )
    calendar_integration_type: models.CharField = models.CharField(
        _("calendar integration type"),
        max_length=20,
        choices=CalendarIntegrationChoices.choices,
        blank=True,
        help_text=_("Type of calendar integration")
    )
    enable_email_integration: models.BooleanField = models.BooleanField(
        _("enable email integration"),
        default=False,
        help_text=_("Enable integration with external email systems")
    )
    email_integration_provider: models.CharField = models.CharField(
        _("email integration provider"),
        max_length=20,
        choices=EmailIntegrationChoices.choices,
        blank=True,
        help_text=_("Email integration provider")
    )
    
    # Privacy and data handling
    data_retention_policy: models.CharField = models.CharField(
        _("data retention policy"),
        max_length=20,
        choices=DataRetentionChoices.choices,
        default=DataRetentionChoices.TWO_YEARS,
        help_text=_("How long to retain student and class data")
    )
    gdpr_compliance_enabled: models.BooleanField = models.BooleanField(
        _("GDPR compliance enabled"),
        default=True,
        help_text=_("Enable GDPR compliance features")
    )
    allow_data_export: models.BooleanField = models.BooleanField(
        _("allow data export"),
        default=True,
        help_text=_("Allow users to export their personal data")
    )
    require_data_processing_consent: models.BooleanField = models.BooleanField(
        _("require data processing consent"),
        default=True,
        help_text=_("Require explicit consent for data processing")
    )
    
    # Dashboard preferences
    dashboard_refresh_interval = models.PositiveIntegerField(
        default=30, 
        help_text="Dashboard refresh interval in seconds"
    )
    activity_retention_days = models.PositiveIntegerField(
        default=90, 
        help_text="Days to retain activity logs"
    )
    
    # Timestamps
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, null=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        verbose_name = _("School Settings")
        verbose_name_plural = _("School Settings")
        indexes = [
            models.Index(fields=['school']),
            models.Index(fields=['educational_system']),
            models.Index(fields=['language']),
            models.Index(fields=['timezone']),
        ]
    
    def __str__(self) -> str:
        return f"Settings for {self.school.name}"
    
    def save(self, *args, **kwargs):
        """Override save to set default working days if not provided"""
        if not self.working_days:
            # Default to Monday-Friday (0-4)
            self.working_days = [0, 1, 2, 3, 4]
        super().save(*args, **kwargs)
    
    def get_working_days_display(self) -> list[str]:
        """Get human-readable working days"""
        day_names = [
            _("Monday"), _("Tuesday"), _("Wednesday"), 
            _("Thursday"), _("Friday"), _("Saturday"), _("Sunday")
        ]
        return [str(day_names[day]) for day in self.working_days if 0 <= day <= 6]
    
    def is_working_day(self, weekday: int) -> bool:
        """Check if a given weekday (0=Monday) is a working day"""
        return weekday in self.working_days
    
    def get_grade_levels_display(self) -> list[str]:
        """Get human-readable grade levels"""
        if not self.grade_levels or not self.educational_system:
            return []
        
        choices_dict = dict(self.educational_system.school_year_choices)
        return [choices_dict.get(level, level) for level in self.grade_levels]


class InvitationStatus(models.TextChoices):
    """Status options for teacher invitations"""
    
    PENDING = "pending", _("Pending")
    SENT = "sent", _("Sent")
    DELIVERED = "delivered", _("Delivered")
    VIEWED = "viewed", _("Viewed")
    ACCEPTED = "accepted", _("Accepted")
    DECLINED = "declined", _("Declined")
    EXPIRED = "expired", _("Expired")
    CANCELLED = "cancelled", _("Cancelled")


class EmailDeliveryStatus(models.TextChoices):
    """Email delivery status options with comprehensive tracking"""
    
    NOT_SENT = "not_sent", _("Not Sent")
    QUEUED = "queued", _("Queued")
    SENDING = "sending", _("Sending")
    SENT = "sent", _("Sent")
    DELIVERED = "delivered", _("Delivered")
    OPENED = "opened", _("Opened")
    CLICKED = "clicked", _("Clicked")
    FAILED = "failed", _("Failed")
    BOUNCED = "bounced", _("Bounced")
    SPAM = "spam", _("Marked as Spam")


class TeacherInvitationManager(models.Manager):
    """Custom manager for TeacherInvitation model."""
    
    def active_invitations(self):
        """Return only active (valid) invitations."""
        return self.filter(
            is_accepted=False,
            expires_at__gt=timezone.now(),
            status__in=[
                InvitationStatus.PENDING,
                InvitationStatus.SENT,
                InvitationStatus.DELIVERED,
                InvitationStatus.VIEWED,
            ]
        )
    
    def for_school(self, school):
        """Return invitations for a specific school."""
        return self.filter(school=school)
    
    def for_batch(self, batch_id):
        """Return invitations for a specific batch."""
        return self.filter(batch_id=batch_id)


class TeacherInvitation(models.Model):
    """
    Enhanced teacher invitation model with bulk processing support,
    email delivery tracking, and real-time status updates.
    """
    
    # Core invitation fields
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE, 
        related_name="teacher_invitations"
    )
    email = models.EmailField(_("email address"))
    invited_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name="sent_teacher_invitations"
    )
    role = models.CharField(
        _("role"), 
        max_length=20, 
        choices=SchoolRole.choices,
        default=SchoolRole.TEACHER
    )
    
    # Enhanced invitation fields
    custom_message = models.TextField(
        _("custom message"),
        max_length=1000,
        blank=True,
        null=True,
        help_text=_("Personal message to include in the invitation")
    )
    batch_id = models.UUIDField(
        _("batch ID"),
        help_text=_("UUID to group related invitations together")
    )
    
    # Status tracking
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING
    )
    
    # Email delivery tracking
    email_delivery_status = models.CharField(
        _("email delivery status"),
        max_length=20,
        choices=EmailDeliveryStatus.choices,
        default=EmailDeliveryStatus.NOT_SENT
    )
    email_sent_at = models.DateTimeField(
        _("email sent at"),
        null=True,
        blank=True
    )
    email_delivered_at = models.DateTimeField(
        _("email delivered at"),
        null=True,
        blank=True
    )
    email_failure_reason = models.TextField(
        _("email failure reason"),
        blank=True,
        null=True
    )
    retry_count = models.PositiveSmallIntegerField(
        _("retry count"),
        default=0
    )
    max_retries = models.PositiveSmallIntegerField(
        _("max retries"),
        default=3
    )
    
    # Core invitation tracking
    token = models.CharField(
        _("token"), 
        max_length=64, 
        unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_accepted = models.BooleanField(
        _("is accepted"), 
        default=False
    )
    accepted_at = models.DateTimeField(
        _("accepted at"),
        null=True,
        blank=True
    )
    declined_at = models.DateTimeField(
        _("declined at"),
        null=True,
        blank=True,
        help_text=_("When the invitation was declined")
    )
    
    # Performance fields
    viewed_at = models.DateTimeField(
        _("viewed at"),
        null=True,
        blank=True,
        help_text=_("When the invitation was first viewed")
    )
    
    objects = TeacherInvitationManager()
    
    class Meta:
        verbose_name = _("Teacher Invitation")
        verbose_name_plural = _("Teacher Invitations")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "status", "-created_at"]),
            models.Index(fields=["batch_id", "-created_at"]),
            models.Index(fields=["email", "school", "is_accepted"]),
            models.Index(fields=["token"]),
            models.Index(fields=["expires_at", "is_accepted"]),
            models.Index(fields=["email_delivery_status", "retry_count"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["email", "school"],
                condition=models.Q(
                    is_accepted=False,
                    expires_at__gt=timezone.now(),
                    status__in=[
                        InvitationStatus.PENDING,
                        InvitationStatus.SENT,
                        InvitationStatus.DELIVERED,
                        InvitationStatus.VIEWED,
                    ]
                ),
                name="unique_active_teacher_invitation_per_school"
            )
        ]
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate token and expiry."""
        if not self.token:
            # Generate a cryptographically secure 64-character token
            import secrets
            self.token = secrets.token_hex(32)  # 32 bytes = 64 hex characters
        
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate the invitation."""
        super().clean()
        
        # Check for duplicate active invitations
        if not self.pk:  # Only check for new invitations
            existing = TeacherInvitation.objects.filter(
                email=self.email,
                school=self.school,
                is_accepted=False,
                expires_at__gt=timezone.now(),
                status__in=[
                    InvitationStatus.PENDING,
                    InvitationStatus.SENT,
                    InvitationStatus.DELIVERED,
                    InvitationStatus.VIEWED,
                ]
            ).exists()
            
            if existing:
                raise ValidationError(
                    "An active invitation already exists for this email and school"
                )
    
    def __str__(self) -> str:
        return f"Teacher invitation to {self.email} for {self.school.name}"
    
    def is_valid(self) -> bool:
        """Check if the invitation is still valid."""
        if self.is_accepted:
            return False
        
        if timezone.now() > self.expires_at:
            return False
        
        if self.status in [InvitationStatus.CANCELLED, InvitationStatus.EXPIRED, InvitationStatus.DECLINED]:
            return False
        
        return True
    
    def is_expired(self) -> bool:
        """Check if the invitation has expired."""
        return timezone.now() > self.expires_at
    
    def accept(self):
        """Mark invitation as accepted."""
        if not self.is_accepted:
            self.is_accepted = True
            self.status = InvitationStatus.ACCEPTED
            self.accepted_at = timezone.now()
            self.save(update_fields=["is_accepted", "status", "accepted_at", "updated_at"])
    
    def decline(self):
        """Mark invitation as declined."""
        if self.is_accepted:
            raise ValidationError("Cannot decline an already accepted invitation")
        
        if self.status == InvitationStatus.DECLINED:
            raise ValidationError("This invitation has already been declined")
        
        self.status = InvitationStatus.DECLINED
        self.declined_at = timezone.now()
        self.save(update_fields=["status", "declined_at", "updated_at"])
    
    def cancel(self):
        """Cancel the invitation."""
        if self.is_accepted:
            raise ValidationError("Cannot cancel an already accepted invitation")
        
        self.status = InvitationStatus.CANCELLED
        self.save(update_fields=["status", "updated_at"])
    
    def mark_email_sent(self):
        """Mark email as sent."""
        self.email_delivery_status = EmailDeliveryStatus.SENT
        self.email_sent_at = timezone.now()
        self.status = InvitationStatus.SENT
        self.save(update_fields=[
            "email_delivery_status", 
            "email_sent_at", 
            "status", 
            "updated_at"
        ])
    
    def mark_email_delivered(self):
        """Mark email as delivered."""
        self.email_delivery_status = EmailDeliveryStatus.DELIVERED
        self.email_delivered_at = timezone.now()
        self.status = InvitationStatus.DELIVERED
        self.save(update_fields=[
            "email_delivery_status", 
            "email_delivered_at", 
            "status", 
            "updated_at"
        ])
    
    def mark_email_failed(self, reason: str = None):
        """Mark email as failed and increment retry count."""
        self.email_delivery_status = EmailDeliveryStatus.FAILED
        self.email_failure_reason = reason
        self.retry_count += 1
        self.save(update_fields=[
            "email_delivery_status", 
            "email_failure_reason", 
            "retry_count", 
            "updated_at"
        ])
    
    def can_retry(self) -> bool:
        """Check if email sending can be retried."""
        return self.retry_count < self.max_retries
    
    def mark_viewed(self):
        """Mark invitation as viewed."""
        if not self.viewed_at:
            self.viewed_at = timezone.now()
            # Only update status to VIEWED if not already accepted
            if not self.is_accepted:
                self.status = InvitationStatus.VIEWED
            self.save(update_fields=["viewed_at", "status", "updated_at"])


class StudentProgressLevel(models.TextChoices):
    """Progress levels for student learning."""
    
    BEGINNER = "beginner", _("Beginner")
    ELEMENTARY = "elementary", _("Elementary")
    INTERMEDIATE = "intermediate", _("Intermediate")
    ADVANCED = "advanced", _("Advanced")
    EXPERT = "expert", _("Expert")


class StudentProgress(models.Model):
    """
    Student progress tracking model for individual learning progress.
    
    Tracks a student's progress in a specific course under a specific teacher,
    including skill mastery, completion percentage, and learning notes.
    """
    
    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="learning_progress",
        verbose_name=_("student"),
        help_text=_("Student whose progress is being tracked")
    )
    
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="student_progress_records",
        verbose_name=_("teacher"),
        help_text=_("Teacher tracking this student's progress")
    )
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="student_progress_records",
        verbose_name=_("school"),
        help_text=_("School where progress is being tracked")
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="student_progress_records",
        verbose_name=_("course"),
        help_text=_("Course for which progress is being tracked")
    )
    
    current_level = models.CharField(
        _("current level"),
        max_length=20,
        choices=StudentProgressLevel.choices,
        default=StudentProgressLevel.BEGINNER,
        help_text=_("Current learning level of the student")
    )
    
    completion_percentage = models.DecimalField(
        _("completion percentage"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Percentage of course completed (0-100)")
    )
    
    skills_mastered = models.JSONField(
        _("skills mastered"),
        default=list,
        blank=True,
        help_text=_("List of skills the student has mastered")
    )
    
    current_topics = models.JSONField(
        _("current topics"),
        default=list,
        blank=True,
        help_text=_("Topics currently being studied")
    )
    
    learning_goals = models.JSONField(
        _("learning goals"),
        default=list,
        blank=True,
        help_text=_("Specific learning goals for this student")
    )
    
    notes = models.TextField(
        _("progress notes"),
        blank=True,
        help_text=_("Teacher's notes about student progress")
    )
    
    last_assessment_date = models.DateField(
        _("last assessment date"),
        null=True,
        blank=True,
        help_text=_("Date of the most recent assessment")
    )
    
    created_at = models.DateTimeField(
        _("created at"), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("updated at"), 
        auto_now=True
    )
    
    class Meta:
        verbose_name = _("Student Progress")
        verbose_name_plural = _("Student Progress Records")
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "teacher", "course"],
                name="unique_student_teacher_course_progress"
            )
        ]
        indexes = [
            models.Index(fields=["student", "course"]),
            models.Index(fields=["teacher", "-updated_at"]),
            models.Index(fields=["school", "course"]),
            models.Index(fields=["completion_percentage"]),
            models.Index(fields=["current_level"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.student.name} - {self.course.name} (Teacher: {self.teacher.user.name})"
    
    def clean(self):
        """Validate the progress data."""
        super().clean()
        
        # Validate completion percentage is between 0 and 100
        if self.completion_percentage < Decimal("0.00") or self.completion_percentage > Decimal("100.00"):
            raise ValidationError(
                _("Completion percentage must be between 0 and 100")
            )
    
    @property
    def recent_assessments(self):
        """Get recent assessments for this progress record."""
        return self.assessments.order_by("-assessment_date")[:5]
    
    @property
    def average_assessment_score(self) -> Decimal | None:
        """Calculate average assessment score percentage."""
        assessments = self.assessments.filter(is_graded=True)
        if not assessments.exists():
            return None
        
        total_percentage = sum(assessment.percentage for assessment in assessments)
        return Decimal(str(total_percentage / assessments.count()))
    
    def update_completion_from_assessments(self):
        """Update completion percentage based on recent assessments."""
        avg_score = self.average_assessment_score
        if avg_score is not None:
            self.completion_percentage = avg_score
            self.save(update_fields=["completion_percentage", "updated_at"])


class AssessmentType(models.TextChoices):
    """Types of assessments that can be recorded."""
    
    QUIZ = "quiz", _("Quiz")
    TEST = "test", _("Test")
    HOMEWORK = "homework", _("Homework")
    PROJECT = "project", _("Project")
    ORAL_EXAM = "oral_exam", _("Oral Exam")
    PRACTICAL = "practical", _("Practical Exercise")
    PRESENTATION = "presentation", _("Presentation")
    OTHER = "other", _("Other")


class ProgressAssessment(models.Model):
    """
    Assessment records for student progress tracking.
    
    Records individual assessments, scores, and teacher feedback
    for specific students in their learning journey.
    """
    
    student_progress = models.ForeignKey(
        StudentProgress,
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("student progress"),
        help_text=_("Progress record this assessment belongs to")
    )
    
    assessment_type = models.CharField(
        _("assessment type"),
        max_length=20,
        choices=AssessmentType.choices,
        help_text=_("Type of assessment conducted")
    )
    
    title = models.CharField(
        _("assessment title"),
        max_length=200,
        help_text=_("Title or name of the assessment")
    )
    
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("Detailed description of the assessment")
    )
    
    score = models.DecimalField(
        _("score"),
        max_digits=6,
        decimal_places=2,
        help_text=_("Score achieved by the student")
    )
    
    max_score = models.DecimalField(
        _("maximum score"),
        max_digits=6,
        decimal_places=2,
        help_text=_("Maximum possible score for this assessment")
    )
    
    assessment_date = models.DateField(
        _("assessment date"),
        help_text=_("Date when the assessment was conducted")
    )
    
    skills_assessed = models.JSONField(
        _("skills assessed"),
        default=list,
        blank=True,
        help_text=_("List of specific skills that were assessed")
    )
    
    teacher_notes = models.TextField(
        _("teacher notes"),
        blank=True,
        help_text=_("Teacher's observations and feedback")
    )
    
    is_graded = models.BooleanField(
        _("is graded"),
        default=True,
        help_text=_("Whether this assessment contributes to grades")
    )
    
    improvement_areas = models.JSONField(
        _("improvement areas"),
        default=list,
        blank=True,
        help_text=_("Areas where the student needs improvement")
    )
    
    strengths = models.JSONField(
        _("strengths"),
        default=list,
        blank=True,
        help_text=_("Areas where the student performed well")
    )
    
    created_at = models.DateTimeField(
        _("created at"), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("updated at"), 
        auto_now=True
    )
    
    class Meta:
        verbose_name = _("Progress Assessment")
        verbose_name_plural = _("Progress Assessments")
        ordering = ["-assessment_date", "-created_at"]
        indexes = [
            models.Index(fields=["student_progress", "-assessment_date"]),
            models.Index(fields=["assessment_type", "-assessment_date"]),
            models.Index(fields=["is_graded", "-assessment_date"]),
            models.Index(fields=["assessment_date"]),
        ]
    
    def __str__(self) -> str:
        percentage = self.percentage
        return f"{self.title} - {self.student_progress.student.name} ({percentage:.2f}%)"
    
    @property
    def percentage(self) -> Decimal:
        """Calculate the percentage score for this assessment."""
        if self.max_score > 0:
            return (self.score / self.max_score) * Decimal("100.00")
        return Decimal("0.00")
    
    @property
    def grade_letter(self) -> str:
        """Convert percentage to letter grade."""
        percentage = self.percentage
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"
    
    def clean(self):
        """Validate the assessment data."""
        super().clean()
        
        # Validate score is not greater than max_score
        if self.score > self.max_score:
            raise ValidationError(
                _("Score cannot be greater than maximum score")
            )
        
        # Validate score is not negative
        if self.score < Decimal("0.00"):
            raise ValidationError(
                _("Score cannot be negative")
            )
        
        # Validate max_score is positive
        if self.max_score <= Decimal("0.00"):
            raise ValidationError(
                _("Maximum score must be greater than 0")
            )
    
    def save(self, *args, **kwargs):
        """Override save to update related progress record."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update the student progress last assessment date
        if is_new or self.assessment_date != self.__class__.objects.get(pk=self.pk).assessment_date:
            self.student_progress.last_assessment_date = self.assessment_date
            self.student_progress.save(update_fields=["last_assessment_date", "updated_at"])


# Email Communication System Models (Issues #99 & #100)

class EmailTemplateType(models.TextChoices):
    """
    Types of email templates for teacher communications.
    """
    INVITATION = "invitation", _("Invitation")
    REMINDER = "reminder", _("Reminder")
    WELCOME = "welcome", _("Welcome")
    PROFILE_REMINDER = "profile_reminder", _("Profile Reminder")
    COMPLETION_CELEBRATION = "completion_celebration", _("Completion Celebration")
    ONGOING_SUPPORT = "ongoing_support", _("Ongoing Support")


class EmailCommunicationType(models.TextChoices):
    """
    Types of email communications for tracking purposes.
    """
    MANUAL = "manual", _("Manual")
    AUTOMATED = "automated", _("Automated")
    SEQUENCE = "sequence", _("Sequence")


class SchoolEmailTemplate(models.Model):
    """
    Customizable email templates for schools with branding integration.
    Supports template variables and school-specific customization.
    """
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="email_templates",
        help_text=_("School this template belongs to")
    )
    template_type = models.CharField(
        _("template type"),
        max_length=50,
        choices=EmailTemplateType.choices,
        help_text=_("Type of email template")
    )
    name = models.CharField(
        _("template name"),
        max_length=200,
        help_text=_("Human-readable name for the template")
    )
    
    # Template content
    subject_template = models.CharField(
        _("subject template"),
        max_length=300,
        help_text=_("Email subject with template variables like {{teacher_name}}")
    )
    html_content = models.TextField(
        _("HTML content"),
        help_text=_("HTML email content with template variables")
    )
    text_content = models.TextField(
        _("text content"),
        help_text=_("Plain text email content with template variables")
    )
    
    # Branding and customization
    use_school_branding = models.BooleanField(
        _("use school branding"),
        default=True,
        help_text=_("Apply school colors and logo to template")
    )
    custom_css = models.TextField(
        _("custom CSS"),
        blank=True,
        null=True,
        help_text=_("Additional CSS for template customization")
    )
    
    # Metadata
    is_active = models.BooleanField(
        _("is active"),
        default=True,
        help_text=_("Whether this template is active and can be used")
    )
    is_default = models.BooleanField(
        _("is default"),
        default=False,
        help_text=_("Whether this is the default template for this type")
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_email_templates",
        help_text=_("User who created this template")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("School Email Template")
        verbose_name_plural = _("School Email Templates")
        ordering = ["school", "template_type", "name"]
        indexes = [
            models.Index(fields=["school", "template_type", "is_active"]),
            models.Index(fields=["template_type", "is_default"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "template_type"],
                condition=models.Q(is_default=True),
                name="unique_default_template_per_school_type"
            )
        ]
    
    def __str__(self):
        return f"{self.school.name} - {self.get_template_type_display()}: {self.name}"
    
    def clean(self):
        """Validate template constraints."""
        super().clean()
        
        # Ensure only one default template per school and type
        if self.is_default:
            existing_default = SchoolEmailTemplate.objects.filter(
                school=self.school,
                template_type=self.template_type,
                is_default=True
            ).exclude(pk=self.pk)
            
            if existing_default.exists():
                raise ValidationError(
                    _("Only one default template per school and type is allowed")
                )


class EmailSequence(models.Model):
    """
    Defines automated email sequences with timing and trigger conditions.
    """
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="email_sequences",
        help_text=_("School this sequence belongs to")
    )
    name = models.CharField(
        _("sequence name"),
        max_length=200,
        help_text=_("Human-readable name for the sequence")
    )
    description = models.TextField(
        _("description"),
        blank=True,
        null=True,
        help_text=_("Description of what this sequence does")
    )
    
    # Trigger configuration
    trigger_event = models.CharField(
        _("trigger event"),
        max_length=50,
        choices=[
            ("invitation_sent", _("Invitation Sent")),
            ("invitation_viewed", _("Invitation Viewed")),
            ("invitation_accepted", _("Invitation Accepted")),
            ("profile_incomplete", _("Profile Incomplete")),
            ("profile_completed", _("Profile Completed")),
        ],
        help_text=_("Event that triggers this sequence")
    )
    
    # Sequence configuration
    is_active = models.BooleanField(
        _("is active"),
        default=True,
        help_text=_("Whether this sequence is active")
    )
    max_emails = models.PositiveIntegerField(
        _("maximum emails"),
        default=5,
        help_text=_("Maximum number of emails to send in this sequence")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Email Sequence")
        verbose_name_plural = _("Email Sequences")
        ordering = ["school", "name"]
        indexes = [
            models.Index(fields=["school", "trigger_event", "is_active"]),
        ]
    
    def __str__(self):
        return f"{self.school.name} - {self.name}"


class EmailSequenceStep(models.Model):
    """
    Individual steps within an email sequence with timing and template.
    """
    
    sequence = models.ForeignKey(
        EmailSequence,
        on_delete=models.CASCADE,
        related_name="steps",
        help_text=_("Email sequence this step belongs to")
    )
    template = models.ForeignKey(
        SchoolEmailTemplate,
        on_delete=models.CASCADE,
        related_name="sequence_steps",
        help_text=_("Email template to use for this step")
    )
    
    # Step configuration
    step_number = models.PositiveIntegerField(
        _("step number"),
        help_text=_("Order of this step in the sequence")
    )
    delay_hours = models.PositiveIntegerField(
        _("delay hours"),
        default=24,
        help_text=_("Hours to wait before sending this email")
    )
    
    # Conditions
    send_condition = models.CharField(
        _("send condition"),
        max_length=50,
        choices=[
            ("always", _("Always Send")),
            ("if_no_response", _("If No Response")),
            ("if_not_accepted", _("If Not Accepted")),
            ("if_profile_incomplete", _("If Profile Incomplete")),
        ],
        default="always",
        help_text=_("Condition that must be met to send this email")
    )
    
    is_active = models.BooleanField(
        _("is active"),
        default=True,
        help_text=_("Whether this step is active")
    )
    
    class Meta:
        verbose_name = _("Email Sequence Step")
        verbose_name_plural = _("Email Sequence Steps")
        ordering = ["sequence", "step_number"]
        indexes = [
            models.Index(fields=["sequence", "step_number", "is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["sequence", "step_number"],
                name="unique_step_number_per_sequence"
            )
        ]
    
    def __str__(self):
        return f"{self.sequence.name} - Step {self.step_number}"


class EmailCommunication(models.Model):
    """
    Tracks individual email communications sent to teachers.
    Provides comprehensive tracking and analytics.
    """
    
    # Recipient information
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="received_emails",
        help_text=_("User who received the email (if registered)")
    )
    recipient_email = models.EmailField(
        _("recipient email"),
        help_text=_("Email address of the recipient")
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="sent_emails",
        help_text=_("School that sent the email")
    )
    
    # Email content and template
    template = models.ForeignKey(
        SchoolEmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_emails",
        help_text=_("Template used for this email")
    )
    template_type = models.CharField(
        _("template type"),
        max_length=50,
        choices=EmailTemplateType.choices,
        help_text=_("Type of email template used")
    )
    subject = models.CharField(
        _("email subject"),
        max_length=300,
        help_text=_("Rendered email subject")
    )
    
    # Communication tracking
    communication_type = models.CharField(
        _("communication type"),
        max_length=20,
        choices=EmailCommunicationType.choices,
        default=EmailCommunicationType.MANUAL,
        help_text=_("Type of communication")
    )
    
    # Sequence tracking (for automated emails)
    sequence = models.ForeignKey(
        EmailSequence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_emails",
        help_text=_("Email sequence this belongs to (if automated)")
    )
    sequence_step = models.ForeignKey(
        EmailSequenceStep,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_emails",
        help_text=_("Sequence step this email represents")
    )
    
    # Delivery tracking
    delivery_status = models.CharField(
        _("delivery status"),
        max_length=20,
        choices=EmailDeliveryStatus.choices,
        default=EmailDeliveryStatus.QUEUED,
        help_text=_("Current delivery status")
    )
    
    # Timestamps
    queued_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    failure_reason = models.TextField(
        _("failure reason"),
        blank=True,
        null=True,
        help_text=_("Reason for delivery failure")
    )
    retry_count = models.PositiveIntegerField(
        _("retry count"),
        default=0,
        help_text=_("Number of delivery attempts")
    )
    max_retries = models.PositiveIntegerField(
        _("maximum retries"),
        default=3,
        help_text=_("Maximum number of retry attempts")
    )
    
    # Related objects
    teacher_invitation = models.ForeignKey(
        TeacherInvitation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="email_communications",
        help_text=_("Related teacher invitation (if applicable)")
    )
    
    # Metadata
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_email_communications",
        help_text=_("User who initiated this communication")
    )
    
    class Meta:
        verbose_name = _("Email Communication")
        verbose_name_plural = _("Email Communications")
        ordering = ["-queued_at"]
        indexes = [
            models.Index(fields=["school", "delivery_status", "-queued_at"]),
            models.Index(fields=["recipient_email", "template_type", "-queued_at"]),
            models.Index(fields=["sequence", "delivery_status", "-queued_at"]),
            models.Index(fields=["teacher_invitation", "-queued_at"]),
            models.Index(fields=["delivery_status", "retry_count", "-queued_at"]),
        ]
    
    def __str__(self):
        return f"{self.template_type} to {self.recipient_email} ({self.delivery_status})"
    
    def can_retry(self):
        """Check if this email can be retried."""
        return (
            self.delivery_status == EmailDeliveryStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def mark_sent(self):
        """Mark email as sent."""
        self.delivery_status = EmailDeliveryStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=["delivery_status", "sent_at"])
    
    def mark_delivered(self):
        """Mark email as delivered."""
        self.delivery_status = EmailDeliveryStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=["delivery_status", "delivered_at"])
    
    def mark_opened(self):
        """Mark email as opened."""
        self.delivery_status = EmailDeliveryStatus.OPENED
        self.opened_at = timezone.now()
        self.save(update_fields=["delivery_status", "opened_at"])
    
    def mark_clicked(self):
        """Mark email as clicked."""
        self.delivery_status = EmailDeliveryStatus.CLICKED
        self.clicked_at = timezone.now()
        self.save(update_fields=["delivery_status", "clicked_at"])
    
    def mark_failed(self, reason=None):
        """Mark email as failed."""
        self.delivery_status = EmailDeliveryStatus.FAILED
        self.failed_at = timezone.now()
        self.retry_count += 1
        if reason:
            self.failure_reason = reason
        self.save(update_fields=["delivery_status", "failed_at", "retry_count", "failure_reason"])
