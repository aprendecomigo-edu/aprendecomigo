"""
Invitation models for the accounts app.

This module contains models related to various types of invitations:
school invitations, school invitation links, and teacher invitations.
"""

import secrets
from datetime import timedelta
from typing import ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .enums import SchoolRole, EmailDeliveryStatus, InvitationStatus


class SchoolInvitation(models.Model):
    """
    Invitation for a user to join a school with a specific role
    """

    school: models.ForeignKey = models.ForeignKey(
        "School", on_delete=models.CASCADE, related_name="invitations"
    )
    email: models.EmailField = models.EmailField(_("email address"))
    invited_by: models.ForeignKey = models.ForeignKey(
        "CustomUser", on_delete=models.CASCADE, related_name="sent_invitations"
    )
    role: models.CharField = models.CharField(_("role"), max_length=20, choices=SchoolRole.choices)
    token: models.CharField = models.CharField(_("token"), max_length=64, unique=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    expires_at: models.DateTimeField = models.DateTimeField()
    is_accepted: models.BooleanField = models.BooleanField(_("is accepted"), default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "is_accepted", "-created_at"]),
            models.Index(fields=["email", "is_accepted"]),
            models.Index(fields=["token"]),
            models.Index(fields=["expires_at", "is_accepted"]),
        ]

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
        "School", on_delete=models.CASCADE, related_name="invitation_links"
    )
    role: models.CharField = models.CharField(_("role"), max_length=20, choices=SchoolRole.choices)
    token: models.CharField = models.CharField(_("token"), max_length=64, unique=True)
    created_by: models.ForeignKey = models.ForeignKey(
        "CustomUser", on_delete=models.CASCADE, related_name="created_invitation_links"
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
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "role", "is_active"]),
            models.Index(fields=["token"]),
            models.Index(fields=["expires_at", "is_active"]),
            models.Index(fields=["created_by", "-created_at"]),
        ]

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
        "School", 
        on_delete=models.CASCADE, 
        related_name="teacher_invitations"
    )
    email = models.EmailField(_("email address"))
    invited_by = models.ForeignKey(
        "CustomUser", 
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
            "retry_count",
            "email_failure_reason",
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