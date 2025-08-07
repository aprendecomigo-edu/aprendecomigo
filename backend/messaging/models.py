"""
Notification models for student balance monitoring and notification system.

Issue #107: Student Balance Monitoring & Notification System
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


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
        "accounts.CustomUser",
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
        "finances.PurchaseTransaction",
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


# Email Communication System Models (moved from accounts app)

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


class EmailTemplateType(models.TextChoices):
    """
    Types of email templates for teacher communications and student notifications.
    """
    INVITATION = "invitation", _("Invitation")
    REMINDER = "reminder", _("Reminder")
    WELCOME = "welcome", _("Welcome")
    PROFILE_REMINDER = "profile_reminder", _("Profile Reminder")
    COMPLETION_CELEBRATION = "completion_celebration", _("Completion Celebration")
    ONGOING_SUPPORT = "ongoing_support", _("Ongoing Support")
    
    # Student balance monitoring templates (Issue #107)
    LOW_BALANCE_ALERT = "low_balance_alert", _("Low Balance Alert")
    PACKAGE_EXPIRING_ALERT = "package_expiring_alert", _("Package Expiring Alert")


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
        "accounts.School",
        on_delete=models.CASCADE,
        related_name="messaging_email_templates",
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
        "accounts.CustomUser",
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
                name="messaging_unique_default_template_per_school_type"
            )
        ]
    
    def __str__(self):
        return f"{self.school.name} - {self.get_template_type_display()}: {self.name}"
    
    def clean(self):
        """Validate template constraints and security."""
        super().clean()
        
        # Ensure only one default template per school and type
        if self.is_default:
            existing_default = self.__class__.objects.filter(
                school=self.school,
                template_type=self.template_type,
                is_default=True
            ).exclude(pk=self.pk)
            
            if existing_default.exists():
                raise ValidationError(
                    _("Only one default template per school and type is allowed")
                )
        
        # Security validation for template content
        self._validate_template_security()
    
    def _validate_template_security(self):
        """
        Validate template content for security vulnerabilities.
        
        Raises:
            ValidationError: If template contains security vulnerabilities
        """
        from .services.secure_template_engine import SecureTemplateEngine
        
        try:
            # Validate subject template
            if self.subject_template:
                SecureTemplateEngine.validate_template_content(self.subject_template)
                
            # Validate HTML content
            if self.html_content:
                SecureTemplateEngine.validate_template_content(self.html_content)
                
            # Validate text content  
            if self.text_content:
                SecureTemplateEngine.validate_template_content(self.text_content)
                
            # Validate custom CSS if present
            if self.custom_css:
                self._validate_custom_css_security()
                
        except Exception as e:
            raise ValidationError(
                _("Template security validation failed: %(error)s") % {'error': str(e)}
            )
    
    def _validate_custom_css_security(self):
        """
        Validate custom CSS for security vulnerabilities.
        
        Raises:
            ValidationError: If CSS contains dangerous patterns
        """
        import re
        
        if not self.custom_css:
            return
        
        # Check for dangerous CSS patterns
        dangerous_patterns = [
            r'@import\s+url\s*\(',
            r'javascript\s*:',
            r'expression\s*\(',
            r'behavior\s*:',
            r'-moz-binding\s*:',
            r'binding\s*:',
            r'<script',
            r'</script>',
            r'alert\s*\(',
            r'eval\s*\(',
            r'document\.',
            r'window\.',
        ]
        
        css_lower = self.custom_css.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, css_lower):
                raise ValidationError(
                    _("Custom CSS contains dangerous pattern: %(pattern)s") % {'pattern': pattern}
                )
        
        # Check CSS size
        if len(self.custom_css) > 10000:  # 10KB limit
            raise ValidationError(_("Custom CSS too large. Maximum size is 10KB"))


class EmailSequence(models.Model):
    """
    Defines automated email sequences with timing and trigger conditions.
    """
    
    school = models.ForeignKey(
        "accounts.School",
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
        "messaging.SchoolEmailTemplate",
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
        "accounts.CustomUser",
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
        "accounts.School",
        on_delete=models.CASCADE,
        related_name="sent_emails",
        help_text=_("School that sent the email")
    )
    
    # Email content and template
    template = models.ForeignKey(
        "messaging.SchoolEmailTemplate",
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
        "accounts.TeacherInvitation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="email_communications",
        help_text=_("Related teacher invitation (if applicable)")
    )
    
    # Metadata
    created_by = models.ForeignKey(
        "accounts.CustomUser",
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
