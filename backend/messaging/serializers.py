"""
Serializers for messaging API endpoints - Issue #107: Student Balance Monitoring & Notification System + Email Communication
"""

from rest_framework import serializers

from finances.models import PurchaseTransaction

from .models import Notification


class PurchaseTransactionSerializer(serializers.ModelSerializer):
    """Simple serializer for related purchase transactions in notifications."""

    class Meta:
        model = PurchaseTransaction
        fields = ["id", "transaction_type", "amount", "payment_status", "expires_at", "created_at"]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notification model.

    Used for listing notifications and providing full notification data.
    """

    related_transaction = PurchaseTransactionSerializer(read_only=True)
    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "message",
            "is_read",
            "read_at",
            "related_transaction",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for notification list view.

    Optimized for list performance with essential fields only.
    """

    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "message",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields


class NotificationUnreadCountSerializer(serializers.Serializer):
    """Serializer for unread notification count response."""

    unread_count = serializers.IntegerField(help_text="Number of unread notifications for the user")


class NotificationMarkReadResponseSerializer(serializers.Serializer):
    """Serializer for mark notification as read response."""

    message = serializers.CharField(help_text="Success message indicating notification was marked as read")


# =======================
# EMAIL COMMUNICATION SERIALIZERS (moved from accounts)
# =======================


class SchoolEmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for SchoolEmailTemplate model.
    Handles CRUD operations for email templates with school-level permissions.
    """

    created_by_name = serializers.SerializerMethodField()
    school_name = serializers.SerializerMethodField()
    template_variables = serializers.SerializerMethodField()

    class Meta:
        from messaging.models import SchoolEmailTemplate

        model = SchoolEmailTemplate
        fields = [
            "id",
            "school",
            "template_type",
            "name",
            "subject_template",
            "html_content",
            "text_content",
            "use_school_branding",
            "custom_css",
            "is_active",
            "is_default",
            "created_by",
            "created_by_name",
            "school_name",
            "template_variables",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_by_name",
            "school_name",
            "template_variables",
            "created_at",
            "updated_at",
        ]

    def get_created_by_name(self, obj):
        """Get the name of the user who created this template."""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_school_name(self, obj):
        """Get the school name."""
        return obj.school.name

    def get_template_variables(self, obj):
        """Extract template variables from content."""
        import re

        variables = set()
        # Find variables in subject, html, and text content
        for content in [obj.subject_template, obj.html_content, obj.text_content]:
            if content:
                variables.update(re.findall(r"\{\{(\w+)\}\}", content))
        return sorted(variables)

    def create(self, validated_data):
        """Create a new email template."""
        # Set the creating user
        request = self.context.get("request")
        if request and request.user:
            validated_data["created_by"] = request.user

        return super().create(validated_data)


class EmailSequenceStepSerializer(serializers.ModelSerializer):
    """
    Serializer for EmailSequenceStep model.
    """

    template_name = serializers.SerializerMethodField()

    class Meta:
        from messaging.models import EmailSequenceStep

        model = EmailSequenceStep
        fields = [
            "id",
            "sequence",
            "template",
            "template_name",
            "step_number",
            "delay_hours",
            "send_condition",
            "is_active",
        ]
        read_only_fields = ["id", "template_name"]

    def get_template_name(self, obj):
        """Get the name of the email template."""
        return obj.template.name if obj.template else None


class EmailSequenceSerializer(serializers.ModelSerializer):
    """
    Serializer for EmailSequence model.
    """

    steps = EmailSequenceStepSerializer(many=True, read_only=True)
    steps_count = serializers.SerializerMethodField()
    school_name = serializers.SerializerMethodField()

    class Meta:
        from messaging.models import EmailSequence

        model = EmailSequence
        fields = [
            "id",
            "school",
            "school_name",
            "name",
            "description",
            "trigger_event",
            "is_active",
            "max_emails",
            "steps",
            "steps_count",
        ]
        read_only_fields = ["id", "school_name", "steps", "steps_count"]

    def get_steps_count(self, obj):
        """Get the number of steps in this sequence."""
        return obj.steps.count()

    def get_school_name(self, obj):
        """Get the school name."""
        return obj.school.name


class EmailCommunicationSerializer(serializers.ModelSerializer):
    """
    Serializer for EmailCommunication model.
    Tracks email communications sent through the system.
    """

    sent_by_name = serializers.SerializerMethodField()
    school_name = serializers.SerializerMethodField()
    template_name = serializers.SerializerMethodField()
    sequence_name = serializers.SerializerMethodField()

    class Meta:
        from messaging.models import EmailCommunication

        model = EmailCommunication
        fields = [
            "id",
            "school",
            "school_name",
            "recipient_email",
            "communication_type",
            "template",
            "template_name",
            "template_type",
            "sequence",
            "sequence_name",
            "subject",
            "delivery_status",
            "queued_at",
            "sent_at",
            "delivered_at",
            "opened_at",
            "clicked_at",
            "failed_at",
            "failure_reason",
            "created_by",
            "sent_by_name",
            "retry_count",
            "max_retries",
        ]
        read_only_fields = [
            "id",
            "school_name",
            "template_name",
            "sequence_name",
            "sent_by_name",
            "delivery_status",
            "queued_at",
            "sent_at",
            "delivered_at",
            "opened_at",
            "clicked_at",
            "failed_at",
            "failure_reason",
        ]

    def get_sent_by_name(self, obj):
        """Get the name of the user who sent this communication."""
        if obj.created_by:
            return obj.created_by.name or obj.created_by.email
        return None

    def get_school_name(self, obj):
        """Get the school name."""
        return obj.school.name

    def get_template_name(self, obj):
        """Get the template name if used."""
        return obj.template.name if obj.template else None

    def get_sequence_name(self, obj):
        """Get the sequence name if part of a sequence."""
        return obj.sequence.name if obj.sequence else None


class EmailTemplatePreviewSerializer(serializers.Serializer):
    """
    Serializer for email template preview functionality.
    """

    template_variables = serializers.DictField(
        child=serializers.CharField(), help_text="Variables to substitute in the template"
    )

    def validate_template_variables(self, value):
        """Validate template variables."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Template variables must be a dictionary")

        # Check for common required variables
        template = self.context.get("template")
        if template:
            # Extract variables from template content
            import re

            required_vars = set()
            for content in [template.subject_template, template.html_content, template.text_content]:
                if content:
                    required_vars.update(re.findall(r"\{\{(\w+)\}\}", content))

            # Check if all required variables are provided
            missing_vars = required_vars - set(value.keys())
            if missing_vars:
                raise serializers.ValidationError(f"Missing required template variables: {', '.join(missing_vars)}")

        return value


class EmailAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for email analytics data.
    """

    total_sent = serializers.IntegerField()
    total_delivered = serializers.IntegerField()
    total_opened = serializers.IntegerField()
    total_clicked = serializers.IntegerField()
    total_bounced = serializers.IntegerField()

    delivery_rate = serializers.FloatField()
    open_rate = serializers.FloatField()
    click_rate = serializers.FloatField()
    bounce_rate = serializers.FloatField()
