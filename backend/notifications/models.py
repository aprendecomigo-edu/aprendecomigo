"""
Notification models for student balance monitoring and notification system.

Issue #107: Student Balance Monitoring & Notification System
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from accounts.models import CustomUser
from finances.models import PurchaseTransaction


class NotificationType(models.TextChoices):
    """Types of notifications for student balance monitoring."""
    
    LOW_BALANCE = "low_balance", _("Low Balance")
    PACKAGE_EXPIRING = "package_expiring", _("Package Expiring")
    BALANCE_DEPLETED = "balance_depleted", _("Balance Depleted")


class Notification(models.Model):
    """
    Notification model for in-app notifications.
    
    Stores notifications with type, title, message, read status, and optional metadata.
    Supports relationship to transactions for package expiration tracking.
    """
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("user"),
        help_text=_("User who will receive this notification")
    )
    
    notification_type = models.CharField(
        _("notification type"),
        max_length=20,
        choices=NotificationType.choices,
        help_text=_("Type of notification")
    )
    
    title = models.CharField(
        _("title"),
        max_length=200,
        help_text=_("Notification title")
    )
    
    message = models.TextField(
        _("message"),
        help_text=_("Notification message content")
    )
    
    is_read = models.BooleanField(
        _("is read"),
        default=False,
        help_text=_("Whether the notification has been read")
    )
    
    read_at = models.DateTimeField(
        _("read at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when notification was read")
    )
    
    related_transaction = models.ForeignKey(
        PurchaseTransaction,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        verbose_name=_("related transaction"),
        help_text=_("Purchase transaction related to this notification (for package expiration)")
    )
    
    metadata = models.JSONField(
        _("metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional notification data in JSON format")
    )
    
    # Audit timestamps
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("updated at"),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]  # Newest first
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.notification_type.upper()} notification for {self.user.name}: {self.title}"
    
    def mark_as_read(self) -> None:
        """Mark notification as read and save to database."""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at", "updated_at"])
    
    def mark_as_unread(self) -> None:
        """Mark notification as unread and save to database."""
        self.is_read = False
        self.read_at = None
        self.save(update_fields=["is_read", "read_at", "updated_at"])
