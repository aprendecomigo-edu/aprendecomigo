"""
User and authentication related models for the accounts app.

This module contains the core user model, custom user manager,
and authentication-related models like verification codes.
"""

import logging
from typing import Any, TypeVar

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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

    # Enhanced verification tracking
    email_verified_at: models.DateTimeField = models.DateTimeField(
        _("email verified at"), null=True, blank=True, help_text=_("Timestamp when email was verified")
    )
    phone_verified_at: models.DateTimeField = models.DateTimeField(
        _("phone verified at"), null=True, blank=True, help_text=_("Timestamp when phone was verified")
    )

    # Normalized phone storage for duplicate checking
    phone_number_normalized: models.CharField = models.CharField(
        _("normalized phone number"),
        max_length=20,
        blank=True,
        db_index=True,
        help_text=_("E.164 format phone number for duplicate checking"),
    )

    # Authentication preferences
    preferred_otp_method: models.CharField = models.CharField(
        _("preferred OTP method"),
        max_length=10,
        choices=[("email", _("Email")), ("sms", _("SMS"))],
        default="email",
        help_text=_("User's preferred method for receiving OTP codes"),
    )

    # Session tracking
    last_activity: models.DateTimeField = models.DateTimeField(
        _("last activity"), auto_now=True, help_text=_("Last time user was active on the platform")
    )

    # Progressive verification tracking
    verification_required_after: models.DateTimeField = models.DateTimeField(
        _("verification required after"),
        null=True,
        blank=True,
        help_text=_("After this time, user must verify email/phone to continue accessing the platform"),
    )

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
            models.Index(fields=["phone_verified"]),
            models.Index(fields=["verification_required_after"]),
            models.Index(fields=["onboarding_completed"]),
            models.Index(fields=["date_joined"]),
            # New indexes for enhanced verification tracking
            models.Index(fields=["email_verified_at"]),
            models.Index(fields=["phone_verified_at"]),
            models.Index(fields=["phone_number_normalized"]),
            models.Index(fields=["last_activity"]),
        ]
        constraints = [
            # Constraint for phone uniqueness
            models.UniqueConstraint(
                fields=["phone_number_normalized"],
                condition=~models.Q(phone_number_normalized=""),
                name="unique_normalized_phone_number",
            )
        ]

    def __str__(self) -> str:
        return str(self.email)

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role in any school"""
        return self.school_memberships.filter(
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
        ).exists()

    def clean(self):
        """Enhanced validation for user model"""
        super().clean()

        # Skip validation for new users (they don't have PKs yet)
        if not self.pk:
            return

        # Skip validation for superusers
        if self.is_superuser:
            return

        # Check if user has at least one active school membership
        if not self.school_memberships.filter(is_active=True).exists():
            raise ValidationError(
                "Non-superuser must have at least one active school membership. "
                "This is a fundamental business rule of the application."
            )

        # Add phone number validation if provided
        if self.phone_number and not self.phone_number_normalized:
            from accounts.services.phone_validation import PhoneValidationService

            try:
                self.phone_number_normalized = PhoneValidationService.validate_and_normalize(self.phone_number)
            except ValidationError:
                raise ValidationError({"phone_number": _("Please enter a valid phone number with country code")})

    def save(self, *args, **kwargs):
        """Enhanced save method with phone normalization"""
        # Normalize phone number before saving - always check if phone_number has changed
        if self.phone_number:
            from accounts.services.phone_validation import PhoneValidationService

            try:
                normalized = PhoneValidationService.validate_and_normalize(self.phone_number)
                # Only update if the normalized version is different
                if self.phone_number_normalized != normalized:
                    self.phone_number_normalized = normalized
            except ValidationError as e:
                # If phone normalization fails, raise a clear error
                raise ValidationError(
                    {
                        "phone_number": f"Invalid phone number format: {e.messages[0] if e.messages else 'Please provide a valid phone number with country code'}"
                    }
                )

        super().save(*args, **kwargs)


class VerificationToken(models.Model):
    """
    Enhanced model for storing verification tokens with better security.

    Supports multiple token types:
    - email_verify: Email verification magic links
    - phone_verify: Phone verification magic links
    - signin_otp: OTP codes for signin
    """

    TOKEN_TYPES = [
        ("email_verify", _("Email Verification")),
        ("phone_verify", _("Phone Verification")),
        ("signin_otp", _("Signin OTP")),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
        help_text=_("User this token belongs to"),
    )
    token_type = models.CharField(
        _("token type"), max_length=20, choices=TOKEN_TYPES, help_text=_("Type of verification this token is for")
    )
    token_value = models.CharField(_("token value"), max_length=255, help_text=_("Hashed token value for security"))
    expires_at = models.DateTimeField(_("expires at"), help_text=_("When this token expires"))
    used_at = models.DateTimeField(
        _("used at"), null=True, blank=True, help_text=_("When this token was successfully used")
    )
    attempts = models.PositiveSmallIntegerField(
        _("attempts"), default=0, help_text=_("Number of failed verification attempts")
    )
    max_attempts = models.PositiveSmallIntegerField(
        _("max attempts"), default=5, help_text=_("Maximum allowed attempts before token is locked")
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Verification Token")
        verbose_name_plural = _("Verification Tokens")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "token_type", "expires_at"]),
            models.Index(fields=["token_value", "used_at"]),
            models.Index(fields=["expires_at", "used_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.get_token_type_display()} for {self.user.email}"

    def is_expired(self):
        """Check if token has expired"""
        return timezone.now() > self.expires_at

    def is_used(self):
        """Check if token has been used"""
        return self.used_at is not None

    def is_locked(self):
        """Check if token is locked due to too many attempts"""
        return self.attempts >= self.max_attempts

    def is_valid(self):
        """Check if token is valid (not expired, used, or locked)"""
        return not (self.is_expired() or self.is_used() or self.is_locked())

    def record_attempt(self):
        """Record a failed attempt"""
        self.attempts += 1
        self.save(update_fields=["attempts"])
        return self.attempts >= self.max_attempts

    def mark_used(self):
        """Mark token as successfully used"""
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
