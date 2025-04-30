from datetime import timedelta
from typing import Any, ClassVar, TypeVar

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Define type variables
T = TypeVar("T", bound="CustomUser")


class CustomUserManager(UserManager[T]):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of username.
    """

    def _create_user(self, email: str, password: str | None, **extra_fields: Any) -> T:
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
        username_or_email: str,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ) -> T:
        """Create and save a regular user with the given credentials."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        if email is None:
            # First form: create_user(email, password, **extra_fields)
            return self._create_user(username_or_email, password, **extra_fields)
        else:
            # Second form: create_user(username, email, password, **extra_fields)
            extra_fields["username"] = username_or_email
            return self._create_user(email, password, **extra_fields)

    # We simplify to a single signature to avoid mypy issues with overloading
    def create_superuser(  # type: ignore[override]
        self,
        username_or_email: str,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ) -> T:
        """Create and save a superuser with the given credentials."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        if email is None:
            # First form: create_superuser(email, password, **extra_fields)
            return self._create_user(username_or_email, password, **extra_fields)
        else:
            # Second form: create_superuser(username, email, password, **extra_fields)
            extra_fields["username"] = username_or_email
            return self._create_user(email, password, **extra_fields)


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

    def __str__(self) -> str:
        user_name = self.user.name if hasattr(self.user, "name") else str(self.user)
        school_name = self.school.name if hasattr(self.school, "name") else str(self.school)
        return f"{user_name} as {self.get_role_display()} at {school_name}"

    def get_role_display(self) -> str:
        """Get the display value for the role."""
        role_display = dict(SchoolRole.choices).get(self.role, self.role)
        return str(role_display)  # Convert _StrPromise to str


class StudentProfile(models.Model):
    """
    Student profile with additional information.
    A user can have this profile regardless of which schools they belong to as a student.
    """

    user: models.OneToOneField = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="student_profile"
    )
    school_year: models.CharField = models.CharField(_("school year"), max_length=50)
    birth_date: models.DateField = models.DateField(_("birth date"))
    # Sensitive personal data fields
    address: models.TextField = models.TextField(
        _("address"), help_text=_("Street, number, postal code and location")
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


class TeacherProfile(models.Model):
    """
    Teacher profile with additional information.
    A user can have this profile regardless of which schools they belong to as a teacher.
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

    def __str__(self) -> str:
        user_name = self.user.name if hasattr(self.user, "name") else str(self.user)
        return f"Teacher Profile: {user_name}"


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


class EmailVerificationCode(models.Model):
    """
    Model for storing email verification codes.
    """

    email: models.EmailField = models.EmailField()
    code: models.CharField = models.CharField(
        max_length=6, blank=True
    )  # Kept for backwards compatibility
    secret_key: models.CharField = models.CharField(
        max_length=32
    )  # For TOTP - unique for each instance, no default
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    is_used: models.BooleanField = models.BooleanField(default=False)
    failed_attempts: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(default=0)
    max_attempts: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(default=5)

    @classmethod
    def generate_code(cls, email: str) -> "EmailVerificationCode":
        """Generate a TOTP secret for the given email"""
        import pyotp  # type: ignore

        # Delete any existing unused codes for this email
        cls.objects.filter(email=email, is_used=False).delete()

        # Generate a new secret key for TOTP
        secret = pyotp.random_base32()

        # Create and return a new verification object
        return cls.objects.create(email=email, secret_key=secret)

    def get_current_code(self) -> str:
        """Get the current TOTP code"""
        import pyotp  # type: ignore

        totp = pyotp.TOTP(self.secret_key)
        return totp.now()

    def get_provisioning_uri(self, email: str | None = None) -> str:
        """Get the TOTP provisioning URI for QR codes"""
        import pyotp  # type: ignore

        email = email or self.email
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(name=email, issuer_name="Aprende Comigo")

    def is_valid(self, code: str | None = None) -> bool:
        """
        Check if the code is still valid (not used, not expired, and not too many failed attempts)

        If code is provided, also verify the TOTP code.
        """
        import pyotp  # type: ignore

        if self.is_used:
            return False

        if self.failed_attempts >= self.max_attempts:
            return False

        # Code expires after 24 hours (extended from 10 minutes since TOTP is more secure)
        expiration_time = self.created_at + timedelta(hours=24)
        if timezone.now() > expiration_time:
            return False

        # If code is provided, verify it
        if code:
            totp = pyotp.TOTP(self.secret_key)
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
