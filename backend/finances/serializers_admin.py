"""
Serializers for administrative payment monitoring API endpoints.

This module provides serializers for payment analytics, transaction history,
and webhook monitoring functionality for administrative dashboard interfaces.
"""

from typing import ClassVar

from django.contrib.auth import get_user_model
from rest_framework import serializers

from finances.models import PurchaseTransaction, WebhookEventLog

User = get_user_model()


class PaymentMetricsSerializer(serializers.Serializer):
    """Serializer for comprehensive payment metrics."""

    generated_at = serializers.DateTimeField(read_only=True)
    time_period = serializers.DictField(read_only=True)

    # Payment success rate metrics
    payment_success_rate = serializers.DictField(read_only=True)

    # Revenue summary
    revenue_summary = serializers.DictField(read_only=True)

    # Transaction metrics
    transaction_metrics = serializers.DictField(read_only=True)

    # Webhook metrics
    webhook_metrics = serializers.DictField(read_only=True)

    # Failure analysis
    failure_analysis = serializers.DictField(read_only=True)

    # Recent activity
    recent_activity = serializers.DictField(read_only=True)

    # Optional revenue trends (only present for multi-day periods)
    revenue_trends = serializers.DictField(read_only=True, required=False)


class StudentBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for student information in transaction history."""

    class Meta:
        model = User
        fields: ClassVar = ["id", "name", "email"]


class AdminTransactionSerializer(serializers.ModelSerializer):
    """Serializer for transaction data in admin interface."""

    student = StudentBasicSerializer(read_only=True)
    amount_formatted = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_payment_status_display", read_only=True)
    type_display = serializers.CharField(source="get_transaction_type_display", read_only=True)

    class Meta:
        model = PurchaseTransaction
        fields: ClassVar = [
            "id",
            "student",
            "amount",
            "amount_formatted",
            "payment_status",
            "status_display",
            "transaction_type",
            "type_display",
            "stripe_payment_intent_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_amount_formatted(self, obj):
        """Get formatted amount with currency symbol."""
        return f"€{obj.amount:.2f}"


class AdminWebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for webhook event data in admin interface."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    processing_time_seconds = serializers.ReadOnlyField()
    is_recent = serializers.ReadOnlyField()
    is_retryable = serializers.SerializerMethodField()

    class Meta:
        model = WebhookEventLog
        fields: ClassVar = [
            "id",
            "stripe_event_id",
            "event_type",
            "status",
            "status_display",
            "retry_count",
            "error_message",
            "processing_time_seconds",
            "is_recent",
            "is_retryable",
            "created_at",
            "processed_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_is_retryable(self, obj):
        """Check if the webhook event can be retried."""
        return obj.is_retryable()


class WebhookStatusSummarySerializer(serializers.Serializer):
    """Serializer for webhook status summary."""

    total_events = serializers.IntegerField()
    processed_events = serializers.IntegerField()
    failed_events = serializers.IntegerField()
    retrying_events = serializers.IntegerField()
    pending_events = serializers.IntegerField()
    success_rate = serializers.FloatField()
    average_processing_time = serializers.FloatField(required=False)


class WebhookStatusResponseSerializer(serializers.Serializer):
    """Serializer for webhook status endpoint response."""

    count = serializers.IntegerField()
    next = serializers.URLField(required=False, allow_null=True)
    previous = serializers.URLField(required=False, allow_null=True)
    results = AdminWebhookEventSerializer(many=True)
    summary = WebhookStatusSummarySerializer()


class TransactionHistoryQuerySerializer(serializers.Serializer):
    """Serializer for transaction history query parameters."""

    payment_status = serializers.CharField(required=False, help_text="Filter by payment status")

    transaction_type = serializers.CharField(required=False, help_text="Filter by transaction type")

    student = serializers.IntegerField(required=False, help_text="Filter by student ID")

    search = serializers.CharField(
        required=False, max_length=255, help_text="Search in payment intent ID, charge ID, or student name"
    )

    ordering = serializers.CharField(required=False, help_text="Order by field (e.g., 'created_at', '-amount')")

    date_from = serializers.DateTimeField(required=False, help_text="Filter transactions from this date")

    date_to = serializers.DateTimeField(required=False, help_text="Filter transactions up to this date")


class WebhookStatusQuerySerializer(serializers.Serializer):
    """Serializer for webhook status query parameters."""

    status = serializers.CharField(required=False, help_text="Filter by webhook processing status")

    event_type = serializers.CharField(required=False, max_length=100, help_text="Filter by event type")

    search = serializers.CharField(required=False, max_length=255, help_text="Search in event ID or event type")

    ordering = serializers.CharField(required=False, help_text="Order by field (e.g., 'created_at', '-retry_count')")

    date_from = serializers.DateTimeField(required=False, help_text="Filter events from this date")

    date_to = serializers.DateTimeField(required=False, help_text="Filter events up to this date")


class PaymentMetricsQuerySerializer(serializers.Serializer):
    """Serializer for payment metrics query parameters."""

    hours = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=8760,  # 1 year
        help_text="Limit analysis to last N hours",
    )

    days = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=365,  # 1 year
        help_text="Limit analysis to last N days",
    )

    def validate(self, data):
        """Validate that only one time filter is provided."""
        if "hours" in data and "days" in data:
            raise serializers.ValidationError("Provide either 'hours' or 'days', not both.")
        return data


class StudentAnalyticsSerializer(serializers.Serializer):
    """Serializer for individual student payment analytics."""

    student_id = serializers.IntegerField()
    period_days = serializers.IntegerField()
    total_transactions = serializers.IntegerField()
    successful_transactions = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    account_balance = serializers.DictField()
    transaction_history = serializers.ListField()


class RevenueAnalyticsSerializer(serializers.Serializer):
    """Serializer for revenue analytics data."""

    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    daily_revenue = serializers.ListField()
    period_days = serializers.IntegerField()
    average_daily_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class FailureAnalyticsSerializer(serializers.Serializer):
    """Serializer for payment failure analytics."""

    total_failures = serializers.IntegerField()
    total_transactions = serializers.IntegerField()
    overall_failure_rate = serializers.FloatField()
    daily_failures = serializers.ListField()
    period_days = serializers.IntegerField()
    common_failure_reasons = serializers.DictField(required=False)


class ProcessingMetricsSerializer(serializers.Serializer):
    """Serializer for webhook processing performance metrics."""

    total_processed = serializers.IntegerField()
    average_processing_time = serializers.FloatField()
    max_processing_time = serializers.FloatField()
    min_processing_time = serializers.FloatField()
