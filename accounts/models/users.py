"""
User and authentication related models for the accounts app.

This module contains the core user model, custom user manager,
and authentication-related models like verification codes.
"""

from datetime import timedelta
import logging
from typing import Any, TypeVar

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import pyotp

from .enums import SchoolRole

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


class CustomUser(AbstractUser):
    """
    Custom User model with email as primary identifier

    Django's built-in permissions:
    - is_superuser: Can access Django admin and has all permissions
    - is_staff: Can access Django admin with limited permissions (admin-only)

    These are used for backend system administration, not for application roles.
    Application roles are managed through SchoolMembership model.
    """

    username: models.CharField = models.CharField(_("username"), max_length=150, blank=True, null=True)
    email: models.EmailField = models.EmailField(_("email address"), unique=True)
    name: models.CharField = models.CharField(_("name"), max_length=150)
    phone_number: models.CharField = models.CharField(_("phone number"), max_length=20, blank=True)

    # Profile information
    profile_photo: models.ImageField = models.ImageField(
        _("profile photo"), upload_to="profile_photos/", blank=True, null=True, help_text=_("User profile photo")
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
    first_login_completed: models.BooleanField = models.BooleanField(_("first login completed"), default=False)
    onboarding_completed: models.BooleanField = models.BooleanField(_("onboarding completed"), default=False)
    onboarding_progress: models.JSONField = models.JSONField(_("onboarding progress"), default=dict, blank=True)
    tutorial_preferences: models.JSONField = models.JSONField(_("tutorial preferences"), default=dict, blank=True)

    # user_type field is removed - roles are now in SchoolMembership

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    # Use a type annotation that doesn't conflict with the parent class
    # but allows us to provide our custom manager
    objects = CustomUserManager()  # type: ignore[misc]

    class Meta:
        ordering = ["name", "email"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["name"]),
            models.Index(fields=["email_verified"]),
            models.Index(fields=["onboarding_completed"]),
            models.Index(fields=["date_joined"]),
        ]

    def __str__(self) -> str:
        return str(self.email)

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role in any school"""
        return self.school_memberships.filter(
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
        ).exists()


class VerificationCode(models.Model):
    """
    Model for storing verification codes.
    """

    email: models.EmailField = models.EmailField()
    secret_key: models.CharField = models.CharField(max_length=32)  # For TOTP - unique for each instance, no default
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    last_code_generated_at: models.DateTimeField = models.DateTimeField(auto_now=True)
    is_used: models.BooleanField = models.BooleanField(default=False)
    failed_attempts: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(default=0)
    max_attempts: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(default=5)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "is_used"]),
            models.Index(fields=["email", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Verification code for {self.email} ({'used' if self.is_used else 'active'})"

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
            if not result:
                # Record failed attempt for wrong codes
                self.record_failed_attempt()
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
        return self.failed_attempts >= self.max_attempts  # type: ignore[no-any-return]
