import logging
import uuid
from datetime import timedelta
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
    """Email delivery status options"""
    
    NOT_SENT = "not_sent", _("Not Sent")
    SENT = "sent", _("Sent")
    DELIVERED = "delivered", _("Delivered")
    FAILED = "failed", _("Failed")
    BOUNCED = "bounced", _("Bounced")


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
    
    def accept(self):
        """Mark invitation as accepted."""
        if not self.is_accepted:
            self.is_accepted = True
            self.status = InvitationStatus.ACCEPTED
            self.accepted_at = timezone.now()
            self.save(update_fields=["is_accepted", "status", "accepted_at", "updated_at"])
    
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
            self.status = InvitationStatus.VIEWED
            self.save(update_fields=["viewed_at", "status", "updated_at"])
