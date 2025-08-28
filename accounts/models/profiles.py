"""
User profile models for the accounts app.

This module contains specialized profile models for different user types:
teachers, students, and parents. Each profile provides additional information
and functionality specific to their role.
"""

import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .enums import RelationshipType

logger = logging.getLogger(__name__)


class TeacherProfile(models.Model):
    """
    Teacher profile with additional information.
    A user can have this profile regardless of which schools they belong to as a teacher.

    Enhanced with structured data fields for better profile management and completion tracking.
    """

    user: models.OneToOneField = models.OneToOneField(
        "CustomUser", on_delete=models.CASCADE, related_name="teacher_profile"
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
        help_text=_("Structured educational background data (degree, institution, field, year)"),
    )
    teaching_subjects: models.JSONField = models.JSONField(
        _("teaching subjects"), default=list, blank=True, help_text=_("List of subjects the teacher specializes in")
    )
    rate_structure: models.JSONField = models.JSONField(
        _("rate structure"), default=dict, blank=True, help_text=_("Detailed rate structure for different class types")
    )
    weekly_availability: models.JSONField = models.JSONField(
        _("weekly availability"), default=dict, blank=True, help_text=_("Structured weekly availability schedule")
    )

    # Enhanced profile fields for comprehensive teacher profile creation
    grade_level_preferences: models.JSONField = models.JSONField(
        _("grade level preferences"),
        default=list,
        blank=True,
        help_text=_("List of preferred grade levels (elementary, middle, high school, university)"),
    )
    teaching_experience: models.JSONField = models.JSONField(
        _("teaching experience"),
        default=dict,
        blank=True,
        help_text=_("Structured teaching experience data (years, institutions, specializations)"),
    )
    credentials_documents: models.JSONField = models.JSONField(
        _("credentials documents"),
        default=list,
        blank=True,
        help_text=_("List of uploaded credential document references"),
    )
    availability_schedule: models.JSONField = models.JSONField(
        _("availability schedule"),
        default=dict,
        blank=True,
        help_text=_("Detailed availability schedule with time slots and preferences"),
    )

    # Profile status tracking
    last_profile_update: models.DateTimeField = models.DateTimeField(
        _("last profile update"), auto_now=True, help_text=_("When the profile was last updated")
    )

    # Activity tracking for school administrators
    last_activity: models.DateTimeField = models.DateTimeField(
        _("last activity"), null=True, blank=True, help_text=_("When the teacher was last active in the system")
    )

    # Scheduling Rules - GitHub Issue #152
    minimum_notice_minutes: models.PositiveIntegerField = models.PositiveIntegerField(
        _("minimum notice minutes"),
        null=True,
        blank=True,
        help_text=_("Override minimum notice period in minutes (school default if null)"),
    )
    buffer_time_minutes: models.PositiveIntegerField = models.PositiveIntegerField(
        _("buffer time minutes"),
        null=True,
        blank=True,
        help_text=_("Buffer time between classes in minutes (school default if null)"),
    )
    max_daily_bookings: models.PositiveIntegerField = models.PositiveIntegerField(
        _("maximum daily bookings"),
        null=True,
        blank=True,
        help_text=_("Maximum classes per day (school default if null)"),
    )
    max_weekly_bookings: models.PositiveIntegerField = models.PositiveIntegerField(
        _("maximum weekly bookings"),
        null=True,
        blank=True,
        help_text=_("Maximum classes per week (school default if null)"),
    )

    class Meta:
        indexes = [
            models.Index(fields=["last_profile_update"]),
            models.Index(fields=["last_activity"]),
            # Indexes for tutor discovery optimization
            models.Index(fields=["specialty"]),
            models.Index(fields=["hourly_rate"]),
        ]

    def __str__(self) -> str:
        user_name = self.user.name if hasattr(self.user, "name") else str(self.user)
        return f"Teacher Profile: {user_name}"

    def get_school_memberships(self):
        """Get all school memberships for this teacher."""
        return self.user.school_memberships.filter(role=SchoolRole.TEACHER, is_active=True).select_related("school")

    def mark_activity(self) -> None:
        """Mark that the teacher was active."""
        from django.utils import timezone

        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])


class StudentProfile(models.Model):
    """
    Student profile with additional information.
    A user can have this profile regardless of which schools they belong to as a student.
    """

    user: models.OneToOneField = models.OneToOneField(
        "CustomUser", on_delete=models.CASCADE, related_name="student_profile"
    )
    educational_system: models.ForeignKey = models.ForeignKey(
        "EducationalSystem",
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

    class Meta:
        ordering = ["user__name", "birth_date"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["educational_system", "school_year"]),
            models.Index(fields=["birth_date"]),
        ]

    def __str__(self) -> str:
        user_name = self.user.name if hasattr(self.user, "name") else str(self.user)
        return f"Student Profile: {user_name}"

    def clean(self):
        """Validate that school_year is valid for the selected educational system"""
        super().clean()
        if (
            self.educational_system
            and self.school_year
            and not self.educational_system.validate_school_year(self.school_year)
        ):
            from django.core.exceptions import ValidationError

            valid_years = dict(self.educational_system.school_year_choices)
            raise ValidationError(
                {
                    "school_year": f"School year '{self.school_year}' is not valid for "
                    f"educational system '{self.educational_system.name}'. "
                    f"Valid options: {list(valid_years.keys())}"
                }
            )


class ParentProfile(models.Model):
    """
    Parent profile with additional information for managing child accounts.
    A user can have this profile regardless of which schools they belong to as a parent.
    """

    user: models.OneToOneField = models.OneToOneField(
        "CustomUser", on_delete=models.CASCADE, related_name="parent_profile"
    )

    # Notification preferences for parent communications
    notification_preferences: models.JSONField = models.JSONField(
        _("notification preferences"),
        default=dict,
        blank=True,
        help_text=_("Parent notification preferences (email, SMS, in-app)"),
    )

    # Default approval settings for all children
    default_approval_settings: models.JSONField = models.JSONField(
        _("default approval settings"),
        default=dict,
        blank=True,
        help_text=_("Default purchase approval settings for all children"),
    )

    # Communication preferences
    email_notifications_enabled: models.BooleanField = models.BooleanField(
        _("email notifications enabled"), default=True, help_text=_("Enable email notifications for parent alerts")
    )

    sms_notifications_enabled: models.BooleanField = models.BooleanField(
        _("SMS notifications enabled"), default=False, help_text=_("Enable SMS notifications for parent alerts")
    )

    # Audit timestamps
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Parent Profile")
        verbose_name_plural = _("Parent Profiles")
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["email_notifications_enabled"]),
        ]

    def __str__(self) -> str:
        user_name = self.user.name if hasattr(self.user, "name") else str(self.user)
        return f"Parent Profile: {user_name}"


class ParentChildRelationship(models.Model):
    """
    Model to represent parent-child relationships within the school system.
    Allows parents to manage their children's accounts with appropriate permissions.
    """

    parent: models.ForeignKey = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="children_relationships",
        verbose_name=_("parent"),
        help_text=_("Parent user who manages the child account"),
    )

    child: models.ForeignKey = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="parent_relationships",
        verbose_name=_("child"),
        help_text=_("Child user whose account is managed by the parent"),
    )

    relationship_type: models.CharField = models.CharField(
        _("relationship type"),
        max_length=20,
        choices=RelationshipType.choices,
        default=RelationshipType.PARENT,
        help_text=_("Type of relationship (parent, guardian, etc.)"),
    )

    school: models.ForeignKey = models.ForeignKey(
        "School",
        on_delete=models.CASCADE,
        verbose_name=_("school"),
        help_text=_("School where this relationship is established"),
    )

    is_active: models.BooleanField = models.BooleanField(
        _("is active"), default=True, help_text=_("Whether this relationship is currently active")
    )

    # Approval settings specific to this parent-child relationship
    requires_purchase_approval: models.BooleanField = models.BooleanField(
        _("requires purchase approval"), default=True, help_text=_("Whether parent approval is required for purchases")
    )

    requires_session_approval: models.BooleanField = models.BooleanField(
        _("requires session approval"),
        default=True,
        help_text=_("Whether parent approval is required for booking sessions"),
    )

    # Audit timestamps
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Parent-Child Relationship")
        verbose_name_plural = _("Parent-Child Relationships")
        unique_together = [["parent", "child", "school"]]
        indexes = [
            models.Index(fields=["parent", "is_active"]),
            models.Index(fields=["child", "is_active"]),
            models.Index(fields=["school", "is_active"]),
            models.Index(fields=["relationship_type"]),
        ]
        constraints = [models.CheckConstraint(check=~models.Q(parent=models.F("child")), name="parent_cannot_be_child")]

    def __str__(self) -> str:
        parent_name = self.parent.name if hasattr(self.parent, "name") else str(self.parent)
        child_name = self.child.name if hasattr(self.child, "name") else str(self.child)
        return f"{parent_name} -> {child_name} ({self.school.name})"

    def clean(self):
        """Validate the relationship data."""
        super().clean()

        # Ensure parent and child are different users
        if self.parent == self.child:
            raise ValidationError(_("Parent and child cannot be the same user"))

        # Ensure both parent and child have memberships at the school
        from .schools import SchoolMembership  # Avoid circular import

        if not SchoolMembership.objects.filter(user=self.parent, school=self.school, is_active=True).exists():
            raise ValidationError(_("Parent must be a member of the school"))

        if not SchoolMembership.objects.filter(user=self.child, school=self.school, is_active=True).exists():
            raise ValidationError(_("Child must be a member of the school"))
