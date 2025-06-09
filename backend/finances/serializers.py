"""
Serializers for the finances app.
"""

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from .models import (
    ClassSession,
    SchoolBillingSettings,
    TeacherCompensationRule,
    TeacherPaymentEntry,
)


class SchoolBillingSettingsSerializer(serializers.ModelSerializer):
    """Serializer for school billing settings."""

    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = SchoolBillingSettings
        fields = [
            "id",
            "school",
            "school_name",
            "trial_cost_absorption",
            "teacher_payment_frequency",
            "payment_day_of_month",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school_name", "created_at", "updated_at"]


class TeacherCompensationRuleSerializer(serializers.ModelSerializer):
    """Serializer for teacher compensation rules."""

    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    teacher_email = serializers.CharField(source="teacher.user.email", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    rule_type_display = serializers.CharField(source="get_rule_type_display", read_only=True)

    class Meta:
        model = TeacherCompensationRule
        fields = [
            "id",
            "teacher",
            "teacher_name",
            "teacher_email",
            "school",
            "school_name",
            "rule_type",
            "rule_type_display",
            "grade_level",
            "rate_per_hour",
            "fixed_amount",
            "conditions",
            "is_active",
            "effective_from",
            "effective_until",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "teacher_name",
            "teacher_email",
            "school_name",
            "rule_type_display",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate compensation rule data."""
        rule_type = attrs.get("rule_type")
        grade_level = attrs.get("grade_level")
        rate_per_hour = attrs.get("rate_per_hour")
        fixed_amount = attrs.get("fixed_amount")

        if rule_type == "grade_specific":
            if not grade_level:
                raise serializers.ValidationError(
                    {"grade_level": "Grade level is required for grade-specific rules."}
                )
            if not rate_per_hour:
                raise serializers.ValidationError(
                    {"rate_per_hour": "Rate per hour is required for grade-specific rules."}
                )
        elif rule_type == "group_class":
            if not rate_per_hour:
                raise serializers.ValidationError(
                    {"rate_per_hour": "Rate per hour is required for group class rules."}
                )
        elif rule_type == "fixed_salary":
            if not fixed_amount:
                raise serializers.ValidationError(
                    {"fixed_amount": "Fixed amount is required for fixed salary rules."}
                )

        return attrs


class ClassSessionSerializer(serializers.ModelSerializer):
    """Serializer for class sessions."""

    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    session_type_display = serializers.CharField(source="get_session_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_hours = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)
    payment_calculated = serializers.SerializerMethodField()
    payment_amount = serializers.SerializerMethodField()

    class Meta:
        model = ClassSession
        fields = [
            "id",
            "teacher",
            "teacher_name",
            "school",
            "school_name",
            "date",
            "start_time",
            "end_time",
            "duration_hours",
            "session_type",
            "session_type_display",
            "grade_level",
            "student_count",
            "students",
            "is_trial",
            "is_makeup",
            "status",
            "status_display",
            "notes",
            "payment_calculated",
            "payment_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "teacher_name",
            "school_name",
            "session_type_display",
            "status_display",
            "duration_hours",
            "payment_calculated",
            "payment_amount",
            "created_at",
            "updated_at",
        ]

    def get_payment_calculated(self, obj: ClassSession) -> bool:
        """Check if payment has been calculated for this session."""
        return hasattr(obj, "payment_entry")

    def get_payment_amount(self, obj: ClassSession) -> Decimal | None:
        """Get the calculated payment amount if available."""
        if hasattr(obj, "payment_entry"):
            return obj.payment_entry.amount_earned
        return None


class TeacherPaymentEntrySerializer(serializers.ModelSerializer):
    """Serializer for teacher payment entries."""

    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    teacher_email = serializers.CharField(source="teacher.user.email", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    session_date = serializers.DateField(source="session.date", read_only=True)
    session_type = serializers.CharField(source="session.session_type", read_only=True)
    is_trial = serializers.BooleanField(source="session.is_trial", read_only=True)
    payment_status_display = serializers.CharField(
        source="get_payment_status_display", read_only=True
    )
    compensation_rule_display = serializers.SerializerMethodField()

    class Meta:
        model = TeacherPaymentEntry
        fields = [
            "id",
            "session",
            "session_date",
            "session_type",
            "is_trial",
            "teacher",
            "teacher_name",
            "teacher_email",
            "school",
            "school_name",
            "billing_period",
            "hours_taught",
            "rate_applied",
            "amount_earned",
            "compensation_rule",
            "compensation_rule_display",
            "payment_status",
            "payment_status_display",
            "calculation_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "session",
            "session_date",
            "session_type",
            "is_trial",
            "teacher_name",
            "teacher_email",
            "school_name",
            "billing_period",
            "hours_taught",
            "rate_applied",
            "amount_earned",
            "compensation_rule",
            "compensation_rule_display",
            "calculation_notes",
            "created_at",
            "updated_at",
        ]

    def get_compensation_rule_display(self, obj: TeacherPaymentEntry) -> str | None:
        """Get the display name of the compensation rule."""
        if obj.compensation_rule:
            return str(obj.compensation_rule)
        return None


class MonthlyPaymentSummarySerializer(serializers.Serializer):
    """Serializer for monthly payment summaries."""

    billing_period = serializers.CharField()
    teacher_id = serializers.IntegerField()
    teacher_name = serializers.CharField()
    teacher_email = serializers.CharField()
    school_id = serializers.IntegerField()
    school_name = serializers.CharField()
    total_hours = serializers.DecimalField(max_digits=6, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    session_count = serializers.IntegerField()
    individual_sessions = serializers.DictField()
    group_sessions = serializers.DictField()
    trial_sessions = serializers.DictField()

    # Breakdown by payment status
    pending_amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    calculated_amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=8, decimal_places=2)


class BulkPaymentProcessorSerializer(serializers.Serializer):
    """Serializer for bulk payment processing requests."""

    start_date = serializers.DateField(
        required=False,
        help_text="Start date for processing sessions (YYYY-MM-DD). If not provided, processes all unpaid sessions.",
    )
    end_date = serializers.DateField(
        required=False,
        help_text="End date for processing sessions (YYYY-MM-DD). If not provided, processes up to today.",
    )

    def validate(self, data):
        """Validate date range."""
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date must be before end_date")

        return data


class PaymentCalculationSerializer(serializers.Serializer):
    """Serializer for payment calculation responses."""

    session_id = serializers.IntegerField()
    payment_entry_id = serializers.IntegerField()
    amount_calculated = serializers.DecimalField(max_digits=8, decimal_places=2)
    rate_applied = serializers.DecimalField(max_digits=6, decimal_places=2)
    hours = serializers.DecimalField(max_digits=4, decimal_places=2)
    notes = serializers.CharField()
