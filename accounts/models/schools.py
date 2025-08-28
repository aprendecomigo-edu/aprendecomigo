"""
School related models for the accounts app.

This module contains models related to schools, school memberships,
school settings, and school activities.
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models.educational import EducationalSystemType

from .enums import (
    ActivityType,
    CalendarIntegrationChoices,
    CurrencyChoices,
    DataRetentionChoices,
    EmailIntegrationChoices,
    LanguageChoices,
    TrialCostAbsorption,
)


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
    STUDENT = "student", _("Student")  # Access to assigned classes
    PARENT = "parent", _("Parent")  # Can manage child accounts and approve purchases



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
        _("logo"), upload_to="school_logos/", blank=True, null=True, help_text=_("School logo image")
    )
    primary_color: models.CharField = models.CharField(
        _("primary color"),
        max_length=7,
        default="#3B82F6",
        blank=True,
        help_text=_("Primary brand color in hex format"),
    )
    secondary_color: models.CharField = models.CharField(
        _("secondary color"),
        max_length=7,
        default="#1F2937",
        blank=True,
        help_text=_("Secondary brand color in hex format"),
    )
    email_domain: models.CharField = models.CharField(
        _("email domain"), max_length=100, blank=True, help_text=_("Official email domain for the school")
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)


class SchoolMembership(models.Model):
    """
    Represents a user's membership in a school with specific role.
    Users can have multiple memberships across different schools with different roles.
    At the same school a user can be in different roles, such as owner and teacher.
    """

    user: models.ForeignKey = models.ForeignKey(
        "CustomUser", on_delete=models.CASCADE, related_name="school_memberships"
    )
    school: models.ForeignKey = models.ForeignKey(School, on_delete=models.CASCADE, related_name="memberships")
    role: models.CharField = models.CharField(_("role"), max_length=20, choices=SchoolRole.choices)
    is_active: models.BooleanField = models.BooleanField(_("is active"), default=True)
    joined_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "school", "role"]]
        indexes = [
            models.Index(fields=["school", "role", "is_active"]),
            models.Index(fields=["school", "joined_at"]),
        ]

    def __str__(self) -> str:
        user_name = self.user.name if hasattr(self.user, "name") else str(self.user)
        school_name = self.school.name if hasattr(self.school, "name") else str(self.school)
        return f"{user_name} as {self.get_role_display()} at {school_name}"

    def get_role_display(self) -> str:  # type: ignore[no-redef]
        """Get the display value for the role."""
        role_display = dict(SchoolRole.choices).get(self.role, self.role)
        return str(role_display)  # Convert _StrPromise to str


class SchoolActivity(models.Model):
    """
    Model to track all school-related activities for admin dashboard
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey("CustomUser", on_delete=models.SET_NULL, null=True, related_name="activities_performed")
    target_user = models.ForeignKey(
        "CustomUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="activities_targeted"
    )
    target_class = models.ForeignKey("finances.ClassSession", on_delete=models.SET_NULL, null=True, blank=True)
    target_invitation = models.ForeignKey("SchoolInvitation", on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    description = models.TextField()

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["school", "-timestamp"]),
            models.Index(fields=["school", "activity_type", "-timestamp"]),
            models.Index(fields=["actor", "-timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.school.name}: {self.activity_type} at {self.timestamp}"


class SchoolSettings(models.Model):
    """
    Comprehensive settings for schools including operational, billing, and configuration options
    """

    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name="settings")

    # Educational system configuration
    educational_system: models.ForeignKey = models.ForeignKey(
        "EducationalSystem",
        on_delete=models.PROTECT,
        related_name="schools_using_system",
        help_text=_("Educational system used by this school"),
        verbose_name=_("educational system"),
        default=EducationalSystemType.PORTUGAL,  # Portugal system as default
    )
    grade_levels: models.JSONField = models.JSONField(
        _("grade levels"), default=list, blank=True, help_text=_("List of grade levels offered by this school")
    )

    # Operational settings
    trial_cost_absorption = models.CharField(
        max_length=20, choices=TrialCostAbsorption.choices, default=TrialCostAbsorption.SCHOOL
    )
    default_session_duration = models.PositiveIntegerField(default=60, help_text="Default session duration in minutes")
    timezone = models.CharField(max_length=50, default="UTC")

    # Billing configuration
    billing_contact_name: models.CharField = models.CharField(
        _("billing contact name"), max_length=100, blank=True, help_text=_("Name of billing contact person")
    )
    billing_contact_email: models.EmailField = models.EmailField(
        _("billing contact email"), blank=True, help_text=_("Email for billing-related communications")
    )
    billing_address: models.TextField = models.TextField(
        _("billing address"), blank=True, help_text=_("Billing address for invoices and payments")
    )
    tax_id: models.CharField = models.CharField(
        _("tax ID"), max_length=50, blank=True, help_text=_("Tax identification number for billing")
    )
    currency_code: models.CharField = models.CharField(
        _("currency"),
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.EUR,
        help_text=_("Default currency for pricing and billing"),
    )

    # Localization settings
    language: models.CharField = models.CharField(
        _("language"),
        max_length=5,
        choices=LanguageChoices.choices,
        default=LanguageChoices.PT,
        help_text=_("Default language for the school interface"),
    )

    # Schedule and availability settings
    working_hours_start: models.TimeField = models.TimeField(
        _("working hours start"), default="08:00", help_text=_("School working hours start time")
    )
    working_hours_end: models.TimeField = models.TimeField(
        _("working hours end"), default="18:00", help_text=_("School working hours end time")
    )
    working_days: models.JSONField = models.JSONField(
        _("working days"), default=list, help_text=_("List of working days (0=Monday, 6=Sunday)")
    )

    # Communication preferences
    email_notifications_enabled: models.BooleanField = models.BooleanField(
        _("email notifications enabled"), default=True, help_text=_("Enable email notifications for school events")
    )
    sms_notifications_enabled: models.BooleanField = models.BooleanField(
        _("SMS notifications enabled"), default=False, help_text=_("Enable SMS notifications for school events")
    )

    # User permissions and access control
    allow_student_self_enrollment: models.BooleanField = models.BooleanField(
        _("allow student self-enrollment"), default=False, help_text=_("Allow students to enroll themselves")
    )
    require_parent_approval: models.BooleanField = models.BooleanField(
        _("require parent approval"), default=True, help_text=_("Require parental approval for student actions")
    )
    auto_assign_teachers: models.BooleanField = models.BooleanField(
        _("auto assign teachers"), default=False, help_text=_("Automatically assign available teachers to classes")
    )
    class_reminder_hours: models.PositiveIntegerField = models.PositiveIntegerField(
        _("class reminder hours"), default=24, help_text=_("Hours before class to send reminder notifications")
    )

    # Integration settings
    enable_calendar_integration: models.BooleanField = models.BooleanField(
        _("enable calendar integration"),
        default=False,
        help_text=_("Enable integration with external calendar systems"),
    )
    calendar_integration_type: models.CharField = models.CharField(
        _("calendar integration type"),
        max_length=20,
        choices=CalendarIntegrationChoices.choices,
        blank=True,
        help_text=_("Type of calendar integration"),
    )
    enable_email_integration: models.BooleanField = models.BooleanField(
        _("enable email integration"), default=False, help_text=_("Enable integration with external email systems")
    )
    email_integration_provider: models.CharField = models.CharField(
        _("email integration provider"),
        max_length=20,
        choices=EmailIntegrationChoices.choices,
        blank=True,
        help_text=_("Email integration provider"),
    )

    # Privacy and data handling
    data_retention_policy: models.CharField = models.CharField(
        _("data retention policy"),
        max_length=20,
        choices=DataRetentionChoices.choices,
        default=DataRetentionChoices.TWO_YEARS,
        help_text=_("How long to retain student and class data"),
    )
    gdpr_compliance_enabled: models.BooleanField = models.BooleanField(
        _("GDPR compliance enabled"), default=True, help_text=_("Enable GDPR compliance features")
    )
    allow_data_export: models.BooleanField = models.BooleanField(
        _("allow data export"), default=True, help_text=_("Allow users to export their personal data")
    )
    require_data_processing_consent: models.BooleanField = models.BooleanField(
        _("require data processing consent"), default=True, help_text=_("Require explicit consent for data processing")
    )

    # Dashboard preferences
    dashboard_refresh_interval = models.PositiveIntegerField(
        default=30, help_text="Dashboard refresh interval in seconds"
    )
    activity_retention_days = models.PositiveIntegerField(default=90, help_text="Days to retain activity logs")

    # Scheduling Rules Defaults - GitHub Issue #152
    default_minimum_notice_minutes: models.PositiveIntegerField = models.PositiveIntegerField(
        _("default minimum notice minutes"),
        default=120,
        help_text=_("Default minimum notice period in minutes (2 hours)"),
    )
    default_buffer_time_minutes: models.PositiveIntegerField = models.PositiveIntegerField(
        _("default buffer time minutes"), default=15, help_text=_("Default buffer time between classes in minutes")
    )
    default_max_daily_bookings: models.PositiveIntegerField = models.PositiveIntegerField(
        _("default max daily bookings"), default=8, help_text=_("Default maximum classes per day for teachers")
    )
    default_max_weekly_bookings: models.PositiveIntegerField = models.PositiveIntegerField(
        _("default max weekly bookings"), default=30, help_text=_("Default maximum classes per week for teachers")
    )
    student_max_daily_bookings: models.PositiveIntegerField = models.PositiveIntegerField(
        _("student max daily bookings"), default=3, help_text=_("Maximum classes per day for students")
    )
    student_max_weekly_bookings: models.PositiveIntegerField = models.PositiveIntegerField(
        _("student max weekly bookings"), default=10, help_text=_("Maximum classes per week for students")
    )

    # Class-type specific buffer times
    buffer_time_group: models.PositiveIntegerField = models.PositiveIntegerField(
        _("buffer time for group classes"), default=20, help_text=_("Buffer time in minutes for group classes")
    )
    buffer_time_trial: models.PositiveIntegerField = models.PositiveIntegerField(
        _("buffer time for trial classes"), default=10, help_text=_("Buffer time in minutes for trial classes")
    )

    # Timestamps
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, null=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = _("School Settings")
        verbose_name_plural = _("School Settings")
        indexes = [
            models.Index(fields=["school"]),
            models.Index(fields=["educational_system"]),
            models.Index(fields=["language"]),
            models.Index(fields=["timezone"]),
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
        day_names = [_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"), _("Sunday")]
        return [str(day_names[day]) for day in self.working_days if 0 <= day <= 6]

    def is_working_day(self, weekday: int) -> bool:
        """Check if a given weekday (0=Monday) is a working day"""
        return weekday in self.working_days

    def get_grade_levels_display(self) -> list[str]:
        """Get human-readable grade levels"""
        if not self.grade_levels or not self.educational_system:
            return []

        choices_dict = dict(self.educational_system.school_year_choices)  # type: ignore[attr-defined]
        return [choices_dict.get(level, level) for level in self.grade_levels]
