"""
Serializers for the finances app.
"""

import re
from decimal import Decimal
from typing import Any

from django.core.validators import EmailValidator
from rest_framework import serializers

from common.security_utils import sanitize_name_field, sanitize_multiline_text
from .models import (
    ClassSession,
    FamilyBudgetControl,
    HourConsumption,
    PricingPlan,
    PurchaseApprovalRequest,
    PurchaseTransaction,
    Receipt,
    SchoolBillingSettings,
    StoredPaymentMethod,
    StudentAccountBalance,
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
        
        errors = {}

        if rule_type == "grade_specific":
            if not grade_level:
                errors["grade_level"] = "Grade level is required for grade-specific rules."
            if not rate_per_hour:
                errors["rate_per_hour"] = "Rate per hour is required for grade-specific rules."
        elif rule_type == "group_class":
            if not rate_per_hour:
                errors["rate_per_hour"] = "Rate per hour is required for group class rules."
        elif rule_type == "fixed_salary":
            if not fixed_amount:
                errors["fixed_amount"] = "Fixed amount is required for fixed salary rules."
        
        if errors:
            raise serializers.ValidationError(errors)

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


class PricingPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for PricingPlan model.
    
    Provides public API representation of pricing plans with calculated
    price_per_hour field and proper formatting for frontend consumption.
    """
    
    price_per_hour = serializers.SerializerMethodField()
    plan_type_display = serializers.CharField(source="get_plan_type_display", read_only=True)
    
    class Meta:
        model = PricingPlan
        fields = [
            "id",
            "name", 
            "description",
            "plan_type",
            "plan_type_display",
            "hours_included",
            "price_eur",
            "validity_days",
            "display_order",
            "is_featured",
            "price_per_hour",
        ]
        read_only_fields = [
            "id",
            "plan_type_display", 
            "price_per_hour",
        ]
    
    def get_price_per_hour(self, obj: PricingPlan) -> str | None:
        """
        Calculate and format price per hour.
        
        Returns:
            Formatted decimal string or None if hours_included is zero
        """
        price_per_hour = obj.price_per_hour
        if price_per_hour is not None:
            return f"{price_per_hour:.2f}"
        return None


class StudentInfoSerializer(serializers.Serializer):
    """
    Serializer for student information in purchase initiation requests.
    
    Validates and sanitizes student data for both authenticated users and guests.
    Includes comprehensive validation for name and email fields.
    """
    
    name = serializers.CharField(
        max_length=150,
        help_text="Student's full name"
    )
    email = serializers.EmailField(
        help_text="Student's email address"
    )
    
    def validate_name(self, value: str) -> str:
        """
        Validate and sanitize student name.
        
        Args:
            value: The name to validate
            
        Returns:
            Sanitized name string
            
        Raises:
            ValidationError: If name is invalid
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        
        # Use smart sanitization from security utils
        sanitized_name = sanitize_name_field(value)
        
        if not sanitized_name:
            raise serializers.ValidationError("Name cannot be empty after sanitization")
        
        # Limit length after sanitization
        if len(sanitized_name) > 150:
            sanitized_name = sanitized_name[:150].strip()
        
        # Basic pattern validation - allow international characters including Cyrillic, Arabic, etc.
        if not re.match(r"^[\w\sÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u0400-\u04FF\u0370-\u03FF\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\u1100-\u11FF\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\-'\.]+$", sanitized_name):
            raise serializers.ValidationError(
                "Name contains invalid characters. Only letters, spaces, hyphens, "
                "apostrophes, and dots are allowed."
            )
        
        return sanitized_name
    
    def validate_email(self, value: str) -> str:
        """
        Validate student email address.
        
        Args:
            value: The email to validate
            
        Returns:
            Normalized email string
            
        Raises:
            ValidationError: If email is invalid
        """
        if not value:
            raise serializers.ValidationError("Email address is required")
        
        # Normalize email to lowercase
        normalized_email = value.lower().strip()
        
        # Use Django's EmailValidator for comprehensive validation
        email_validator = EmailValidator()
        try:
            email_validator(normalized_email)
        except Exception:
            raise serializers.ValidationError("Please provide a valid email address")
        
        return normalized_email


class PurchaseInitiationRequestSerializer(serializers.Serializer):
    """
    Serializer for purchase initiation API requests.
    
    Handles validation of plan selection and student information for both
    authenticated users and guest purchases. Ensures data integrity and
    security through comprehensive field validation.
    """
    
    plan_id = serializers.IntegerField(
        min_value=1,
        help_text="ID of the pricing plan to purchase"
    )
    student_info = StudentInfoSerializer(
        help_text="Student information including name and email"
    )
    
    def validate_plan_id(self, value: int) -> int:
        """
        Validate that the pricing plan exists and is active.
        
        Args:
            value: The plan ID to validate
            
        Returns:
            Validated plan ID
            
        Raises:
            ValidationError: If plan doesn't exist or is not active
        """
        try:
            plan = PricingPlan.objects.get(id=value)
        except PricingPlan.DoesNotExist:
            raise serializers.ValidationError(
                f"Pricing plan with ID {value} not found"
            )
        
        if not plan.is_active:
            raise serializers.ValidationError(
                f"Pricing plan '{plan.name}' is not currently active"
            )
        
        return value
    
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Perform cross-field validation.
        
        Args:
            attrs: Dictionary of validated attributes
            
        Returns:
            Validated attributes dictionary
            
        Raises:
            ValidationError: If cross-field validation fails
        """
        # Additional business logic validation can be added here
        # For example, checking if user already has an active subscription
        # when trying to purchase another subscription
        
        return attrs


class PurchaseInitiationResponseSerializer(serializers.Serializer):
    """
    Serializer for purchase initiation API responses.
    
    Provides consistent response format for successful purchase initiations,
    including all necessary data for frontend payment completion.
    """
    
    success = serializers.BooleanField(
        help_text="Whether the purchase initiation was successful"
    )
    client_secret = serializers.CharField(
        help_text="Stripe payment intent client secret for frontend"
    )
    transaction_id = serializers.IntegerField(
        help_text="Internal transaction ID for tracking"
    )
    payment_intent_id = serializers.CharField(
        help_text="Stripe payment intent ID"
    )
    plan_details = serializers.DictField(
        help_text="Details of the purchased plan"
    )
    message = serializers.CharField(
        required=False,
        help_text="Optional success message"
    )


class PurchaseInitiationErrorSerializer(serializers.Serializer):
    """
    Serializer for purchase initiation API error responses.
    
    Provides consistent error format with detailed information for debugging
    and user feedback.
    """
    
    success = serializers.BooleanField(
        default=False,
        help_text="Always false for error responses"
    )
    error_type = serializers.CharField(
        help_text="Type of error that occurred"
    )
    message = serializers.CharField(
        help_text="Human-readable error message"
    )
    details = serializers.DictField(
        required=False,
        help_text="Additional error details"
    )
    field_errors = serializers.DictField(
        required=False,
        help_text="Field-specific validation errors"
    )


class StudentInfoDisplaySerializer(serializers.Serializer):
    """Serializer for student information in balance responses."""
    
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.CharField()


class BalanceSummarySerializer(serializers.Serializer):
    """Serializer for student account balance summary."""
    
    hours_purchased = serializers.DecimalField(max_digits=5, decimal_places=2)
    hours_consumed = serializers.DecimalField(max_digits=5, decimal_places=2)
    remaining_hours = serializers.DecimalField(max_digits=5, decimal_places=2)
    balance_amount = serializers.DecimalField(max_digits=6, decimal_places=2)


class PackageDetailsSerializer(serializers.Serializer):
    """Serializer for package details in balance responses."""
    
    transaction_id = serializers.IntegerField()
    plan_name = serializers.CharField(allow_null=True)
    hours_included = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    hours_consumed = serializers.DecimalField(max_digits=5, decimal_places=2)
    hours_remaining = serializers.DecimalField(max_digits=5, decimal_places=2)
    expires_at = serializers.DateTimeField(allow_null=True)
    days_until_expiry = serializers.IntegerField(allow_null=True)
    is_expired = serializers.BooleanField()


class PackageStatusSerializer(serializers.Serializer):
    """Serializer for package status information."""
    
    active_packages = PackageDetailsSerializer(many=True)
    expired_packages = PackageDetailsSerializer(many=True)


class UpcomingExpirationSerializer(serializers.Serializer):
    """Serializer for upcoming package expirations."""
    
    transaction_id = serializers.IntegerField()
    plan_name = serializers.CharField(allow_null=True)
    hours_remaining = serializers.DecimalField(max_digits=5, decimal_places=2)
    expires_at = serializers.DateTimeField()
    days_until_expiry = serializers.IntegerField()


class StudentBalanceSummarySerializer(serializers.Serializer):
    """Main serializer for student balance summary endpoint."""
    
    student_info = StudentInfoDisplaySerializer()
    balance_summary = BalanceSummarySerializer()
    package_status = PackageStatusSerializer()
    upcoming_expirations = UpcomingExpirationSerializer(many=True)


class TransactionHistorySerializer(serializers.ModelSerializer):
    """Serializer for transaction history."""
    
    transaction_type_display = serializers.CharField(source="get_transaction_type_display", read_only=True)
    payment_status_display = serializers.CharField(source="get_payment_status_display", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PurchaseTransaction
        fields = [
            "id",
            "transaction_type",
            "transaction_type_display",
            "amount",
            "payment_status",
            "payment_status_display",
            "expires_at",
            "is_expired",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HourConsumptionSerializer(serializers.ModelSerializer):
    """Serializer for hour consumption details."""
    
    class_session_id = serializers.IntegerField(source="class_session.id", read_only=True)
    class_session_date = serializers.DateField(source="class_session.date", read_only=True)
    
    class Meta:
        model = HourConsumption
        fields = [
            "id",
            "hours_consumed",
            "hours_originally_reserved",
            "consumed_at",
            "class_session_id",
            "class_session_date",
            "is_refunded",
            "refund_reason",
        ]
        read_only_fields = ["id", "consumed_at"]


class PlanDetailsSerializer(serializers.Serializer):
    """Serializer for plan details in purchase history."""
    
    id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField(allow_null=True)
    plan_type = serializers.CharField(allow_null=True)
    hours_included = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    price_eur = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    validity_days = serializers.IntegerField(allow_null=True)


class PurchaseHistorySerializer(serializers.ModelSerializer):
    """Serializer for purchase history with plan details."""
    
    transaction_type_display = serializers.CharField(source="get_transaction_type_display", read_only=True)
    payment_status_display = serializers.CharField(source="get_payment_status_display", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    plan_details = serializers.SerializerMethodField()
    hours_remaining = serializers.SerializerMethodField()
    consumption_details = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseTransaction
        fields = [
            "id",
            "transaction_type",
            "transaction_type_display",
            "amount",
            "payment_status",
            "payment_status_display",
            "expires_at",
            "is_expired",
            "plan_details",
            "hours_remaining",
            "consumption_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_plan_details(self, obj):
        """Get plan details from metadata."""
        metadata = obj.metadata or {}
        plan_id = metadata.get('plan_id')
        
        if plan_id:
            try:
                plan = PricingPlan.objects.get(id=plan_id)
                return {
                    'id': plan.id,
                    'name': plan.name,
                    'plan_type': plan.plan_type,
                    'hours_included': plan.hours_included,
                    'price_eur': plan.price_eur,
                    'validity_days': plan.validity_days,
                }
            except PricingPlan.DoesNotExist:
                pass
        
        # Fallback to metadata
        return {
            'id': plan_id,
            'name': metadata.get('plan_name'),
            'plan_type': metadata.get('plan_type'),
            'hours_included': Decimal(metadata.get('hours_included', '0')) if metadata.get('hours_included') else None,
            'price_eur': Decimal(metadata.get('price_eur', '0')) if metadata.get('price_eur') else None,
            'validity_days': metadata.get('validity_days'),
        }
    
    def get_hours_remaining(self, obj):
        """Calculate hours remaining for this purchase."""
        plan_details = self.get_plan_details(obj)
        hours_included = plan_details.get('hours_included') or Decimal('0')
        
        # Calculate hours consumed from this specific transaction
        total_consumed = sum(
            consumption.hours_consumed 
            for consumption in obj.hour_consumptions.filter(is_refunded=False)
        )
        
        return max(hours_included - total_consumed, Decimal('0'))
    
    def get_consumption_details(self, obj):
        """Get consumption details if requested."""
        request = self.context.get('request')
        if request and request.query_params.get('include_consumption'):
            consumptions = obj.hour_consumptions.select_related('class_session').order_by('-consumed_at')
            return HourConsumptionSerializer(consumptions, many=True).data
        return []


class ReceiptSerializer(serializers.ModelSerializer):
    """Serializer for Receipt model."""
    
    student_name = serializers.CharField(source="student.name", read_only=True)
    transaction_amount = serializers.DecimalField(
        source="transaction.amount", 
        max_digits=8, 
        decimal_places=2, 
        read_only=True
    )
    transaction_type = serializers.CharField(
        source="transaction.get_transaction_type_display", 
        read_only=True
    )
    plan_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Receipt
        fields = [
            "id",
            "receipt_number",
            "amount",
            "generated_at",
            "is_valid",
            "student_name",
            "transaction_amount",
            "transaction_type",
            "plan_name",
            "pdf_file",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "receipt_number",
            "generated_at",
            "student_name",
            "transaction_amount",
            "transaction_type",
            "plan_name",
            "created_at",
            "updated_at",
        ]
    
    def get_plan_name(self, obj):
        """Get plan name from transaction metadata."""
        if obj.transaction and obj.transaction.metadata:
            return obj.transaction.metadata.get("plan_name", "Unknown Plan")
        return "Unknown Plan"


class ReceiptGenerationRequestSerializer(serializers.Serializer):
    """Serializer for receipt generation requests."""
    
    transaction_id = serializers.IntegerField(
        help_text="ID of the transaction to generate receipt for"
    )
    
    def validate_transaction_id(self, value):
        """Basic validation for transaction ID format."""
        # Only validate the format, let the view handle existence and ownership checks
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("Transaction ID must be a positive integer")
        
        return value


class StoredPaymentMethodSerializer(serializers.ModelSerializer):
    """PCI-compliant serializer for StoredPaymentMethod model."""
    
    student_name = serializers.CharField(source="student.name", read_only=True)
    card_display = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = StoredPaymentMethod
        fields = [
            "id",
            "card_brand",
            "card_exp_month",
            "card_exp_year",
            "is_default",
            "is_active",
            "is_expired",
            "student_name",
            "card_display",
            "stripe_customer_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "student_name",
            "card_display",
            "is_expired",
            "stripe_customer_id",
            "created_at",
            "updated_at",
        ]
    
    def get_card_display(self, obj):
        """Get PCI-compliant formatted card display string."""
        # Use the model's card_display property which is now PCI-compliant
        return obj.card_display
    
    def to_representation(self, instance):
        """Override to ensure PCI-compliant API responses."""
        data = super().to_representation(instance)
        
        # Ensure no raw card data is exposed in API responses
        # card_last4 is intentionally excluded from fields for PCI compliance
        # Card information is available through the secure card_display field only
        
        return data


class PaymentMethodCreationRequestSerializer(serializers.Serializer):
    """Serializer for payment method creation requests."""
    
    stripe_payment_method_id = serializers.CharField(
        max_length=255,
        help_text="Stripe PaymentMethod ID from frontend tokenization"
    )
    
    is_default = serializers.BooleanField(
        default=False,
        help_text="Whether to set this as the default payment method"
    )
    
    def validate_stripe_payment_method_id(self, value):
        """Validate Stripe payment method ID format."""
        # Check for proper Stripe payment method ID format
        if not value or not isinstance(value, str):
            raise serializers.ValidationError("Payment method ID is required")
        
        if not value.startswith('pm_'):
            raise serializers.ValidationError("Invalid Stripe payment method ID format")
        
        # Stripe payment method IDs should be at least 'pm_' + 24 characters
        if len(value) < 27:
            raise serializers.ValidationError("Invalid Stripe payment method ID format")
        
        # Check for reasonable length limit (Stripe IDs are typically ~30 characters)
        if len(value) > 50:
            raise serializers.ValidationError("Payment method ID too long")
        
        # Check if payment method already exists
        from .models import StoredPaymentMethod
        if StoredPaymentMethod.objects.filter(stripe_payment_method_id=value).exists():
            raise serializers.ValidationError("This payment method is already stored")
        
        return value


class EnhancedSubscriptionInfoSerializer(serializers.Serializer):
    """Serializer for enhanced subscription information."""
    
    is_active = serializers.BooleanField()
    next_billing_date = serializers.DateField(allow_null=True)
    billing_cycle = serializers.CharField(allow_null=True)
    subscription_status = serializers.CharField(allow_null=True)
    cancel_at_period_end = serializers.BooleanField()
    current_period_start = serializers.DateField(allow_null=True)
    current_period_end = serializers.DateField(allow_null=True)


class EnhancedStudentBalanceSummarySerializer(StudentBalanceSummarySerializer):
    """Enhanced student balance summary with subscription information."""
    
    subscription_info = EnhancedSubscriptionInfoSerializer(allow_null=True)


class SubscriptionRenewalRequestSerializer(serializers.Serializer):
    """Serializer for subscription renewal requests."""
    
    original_transaction_id = serializers.IntegerField(
        min_value=1,
        help_text="ID of the original transaction to renew"
    )
    payment_method_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Optional payment method ID (uses default if not provided)"
    )
    
    def validate_original_transaction_id(self, value):
        """Validate that the original transaction exists and can be renewed."""
        from .models import PurchaseTransaction, TransactionType, TransactionPaymentStatus
        
        try:
            transaction = PurchaseTransaction.objects.get(id=value)
        except PurchaseTransaction.DoesNotExist:
            raise serializers.ValidationError("Original transaction not found")
        
        # Validate transaction is renewable
        if transaction.payment_status != TransactionPaymentStatus.COMPLETED:
            raise serializers.ValidationError("Only completed transactions can be renewed")
        
        if transaction.transaction_type != TransactionType.SUBSCRIPTION:
            raise serializers.ValidationError("Only subscription transactions can be renewed")
        
        return value
    
    def validate_payment_method_id(self, value):
        """Validate that the payment method exists and belongs to the user."""
        if value is None:
            return value
            
        # This validation will be performed in the view with user context
        return value


class QuickTopupRequestSerializer(serializers.Serializer):
    """Serializer for quick top-up purchase requests."""
    
    hours = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Number of hours to purchase"
    )
    payment_method_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Optional payment method ID (uses default if not provided)"
    )
    
    def validate_hours(self, value):
        """Validate that the hours value matches available packages."""
        from .services.renewal_payment_service import RenewalPaymentService
        
        service = RenewalPaymentService()
        available_packages = service.QUICK_TOPUP_PACKAGES
        
        if value not in available_packages:
            available_hours = list(available_packages.keys())
            raise serializers.ValidationError(
                f"Invalid hours package. Available options: {[float(h) for h in available_hours]}"
            )
        
        return value


class QuickTopupPackageSerializer(serializers.Serializer):
    """Serializer for quick top-up package information."""
    
    hours = serializers.DecimalField(max_digits=5, decimal_places=2)
    price = serializers.DecimalField(max_digits=6, decimal_places=2)
    price_per_hour = serializers.DecimalField(max_digits=6, decimal_places=2)
    savings_percent = serializers.FloatField()


class RenewalResponseSerializer(serializers.Serializer):
    """Serializer for renewal operation responses."""
    
    success = serializers.BooleanField()
    transaction_id = serializers.IntegerField(required=False)
    payment_intent_id = serializers.CharField(required=False)
    hours_purchased = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        required=False,
        help_text="Hours purchased (for quick top-ups)"
    )
    amount_paid = serializers.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        required=False,
        help_text="Amount paid for the transaction"
    )
    message = serializers.CharField()
    error_type = serializers.CharField(required=False)


class PaymentMethodResponseSerializer(serializers.Serializer):
    """Serializer for payment method operation responses."""
    
    success = serializers.BooleanField()
    payment_method_id = serializers.IntegerField(required=False)
    card_display = serializers.CharField(required=False)
    is_default = serializers.BooleanField(required=False)
    stripe_customer_id = serializers.CharField(required=False)
    message = serializers.CharField()
    error_type = serializers.CharField(required=False)
    was_default = serializers.BooleanField(
        required=False,
        help_text="Whether the removed payment method was default (for removal responses)"
    )


# =======================
# PARENT-CHILD PURCHASE APPROVAL SERIALIZERS (Issues #111 & #112)
# =======================

class FamilyBudgetControlSerializer(serializers.ModelSerializer):
    """
    Serializer for FamilyBudgetControl model.
    Handles budget limits and approval settings for parent-child relationships.
    """
    
    parent_name = serializers.CharField(source='parent_child_relationship.parent.name', read_only=True)
    child_name = serializers.CharField(source='parent_child_relationship.child.name', read_only=True)
    school_name = serializers.CharField(source='parent_child_relationship.school.name', read_only=True)
    current_monthly_spending = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    current_weekly_spending = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = FamilyBudgetControl
        fields = [
            'id', 'parent_child_relationship', 'parent_name', 'child_name', 'school_name',
            'monthly_budget_limit', 'weekly_budget_limit', 'auto_approval_threshold',
            'require_approval_for_sessions', 'require_approval_for_packages',
            'current_monthly_spending', 'current_weekly_spending', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'parent_name', 'child_name', 'school_name',
            'current_monthly_spending', 'current_weekly_spending',
            'created_at', 'updated_at'
        ]
    
    def check_budget_limits(self, amount):
        """Check if a purchase amount would exceed budget limits."""
        if self.instance:
            return self.instance.check_budget_limits(amount)
        return {'allowed': True, 'can_auto_approve': True, 'reasons': []}


class PurchaseApprovalRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for PurchaseApprovalRequest model.
    Handles purchase approval workflow between parents and children.
    """
    
    student_name = serializers.CharField(source='student.name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    pricing_plan_name = serializers.CharField(source='pricing_plan.name', read_only=True)
    class_session_info = serializers.SerializerMethodField()
    time_remaining_hours = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PurchaseApprovalRequest
        fields = [
            'id', 'student', 'student_name', 'parent', 'parent_name',
            'parent_child_relationship', 'amount', 'description', 'request_type',
            'status', 'pricing_plan', 'pricing_plan_name', 'class_session',
            'class_session_info', 'request_metadata', 'requested_at', 'responded_at',
            'expires_at', 'time_remaining_hours', 'is_expired', 'parent_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'student_name', 'parent_name', 'pricing_plan_name',
            'class_session_info', 'time_remaining_hours', 'is_expired',
            'requested_at', 'responded_at', 'expires_at', 'created_at', 'updated_at'
        ]
    
    def get_class_session_info(self, obj):
        """Get basic info about the class session if applicable."""
        if obj.class_session:
            return {
                'id': obj.class_session.id,
                'date': obj.class_session.date,
                'start_time': obj.class_session.start_time,
                'duration_hours': float(obj.class_session.duration_hours),
                'teacher_name': obj.class_session.teacher.user.name
            }
        return None
    
    def get_time_remaining_hours(self, obj):
        """Get time remaining until expiration in hours."""
        if obj.is_expired:
            return 0
        
        remaining = obj.time_remaining
        return round(remaining.total_seconds() / 3600, 1)
    
    def validate(self, data):
        """Validate the approval request data."""
        # Ensure student and parent are different users
        if data.get('student') == data.get('parent'):
            raise serializers.ValidationError("Student and parent cannot be the same user")
        
        # Validate parent-child relationship matches
        relationship = data.get('parent_child_relationship')
        if relationship:
            if (data.get('parent') and relationship.parent != data['parent']):
                raise serializers.ValidationError("Parent must match the parent-child relationship")
            
            if (data.get('student') and relationship.child != data['student']):
                raise serializers.ValidationError("Student must match the parent-child relationship")
        
        return data


class PurchaseApprovalActionSerializer(serializers.Serializer):
    """
    Serializer for parent approval actions (approve/deny).
    """
    
    action = serializers.ChoiceField(
        choices=['approve', 'deny'],
        help_text="Action to take on the approval request"
    )
    parent_notes = serializers.CharField(
        max_length=1000,
        required=False,  
        allow_blank=True,
        help_text="Optional notes from the parent about their decision"
    )
    
    def validate_parent_notes(self, value):
        """Validate and sanitize parent notes."""
        if not value:
            return value
        
        # Use smart sanitization from security utils
        sanitized_notes = sanitize_multiline_text(value)
        
        if not sanitized_notes:
            return ""  # Return empty string if nothing remains after sanitization
        
        # Ensure maximum length
        if len(sanitized_notes) > 1000:
            sanitized_notes = sanitized_notes[:1000].strip()
        
        return sanitized_notes


class StudentPurchaseRequestSerializer(serializers.Serializer):
    """
    Serializer for student-initiated purchase requests.
    """
    
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Amount of the purchase request"
    )
    description = serializers.CharField(
        max_length=500,
        help_text="Description of what the student wants to purchase"
    )
    request_type = serializers.ChoiceField(
        choices=['hours', 'session', 'subscription'],
        help_text="Type of purchase being requested"
    )
    pricing_plan_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID of the pricing plan being requested (if applicable)"
    )
    class_session_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID of the class session being requested (if applicable)" 
    )
    parent_id = serializers.IntegerField(
        help_text="ID of the parent who should approve this request"
    )
    
    def validate_description(self, value):
        """Validate and sanitize description."""
        # Use smart sanitization from security utils
        sanitized_description = sanitize_multiline_text(value)
        
        if not sanitized_description:
            raise serializers.ValidationError("Description cannot be empty after sanitization")
        
        # Ensure maximum length
        if len(sanitized_description) > 500:
            sanitized_description = sanitized_description[:500].strip()
        
        return sanitized_description
    
    def validate(self, data):
        """Validate the request data."""
        request_type = data.get('request_type')
        pricing_plan_id = data.get('pricing_plan_id')
        class_session_id = data.get('class_session_id')
        
        # Validate that required fields are provided based on request type
        if request_type == 'hours' and not pricing_plan_id:
            raise serializers.ValidationError("pricing_plan_id is required for hour package requests")
        
        if request_type == 'session' and not class_session_id:
            raise serializers.ValidationError("class_session_id is required for session requests")
        
        # Validate pricing plan exists if provided
        if pricing_plan_id:
            try:
                pricing_plan = PricingPlan.objects.get(id=pricing_plan_id, is_active=True)
                # Validate amount matches pricing plan
                if data['amount'] != pricing_plan.price_eur:
                    raise serializers.ValidationError("Amount must match the pricing plan price")
            except PricingPlan.DoesNotExist:
                raise serializers.ValidationError("Invalid or inactive pricing plan")
        
        # Validate class session exists if provided
        if class_session_id:
            try:
                from .models import ClassSession
                ClassSession.objects.get(id=class_session_id)
            except ClassSession.DoesNotExist:
                raise serializers.ValidationError("Invalid class session")
        
        return data


class ParentDashboardSerializer(serializers.Serializer):
    """
    Serializer for parent approval dashboard data.
    """
    
    pending_requests = PurchaseApprovalRequestSerializer(many=True, read_only=True)
    children_summary = serializers.ListField(
        child=serializers.DictField(),
        read_only=True,
        help_text="Summary of spending for each child"
    )
    recent_transactions = serializers.ListField(
        child=serializers.DictField(),
        read_only=True,
        help_text="Recent approved transactions"
    )
    budget_alerts = serializers.ListField(
        child=serializers.DictField(),
        read_only=True,
        help_text="Budget alerts and warnings"
    )
    monthly_spending_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        help_text="Total spending across all children this month"
    )
    
    def to_representation(self, instance):
        """Custom representation to ensure proper data structure."""
        return {
            'pending_requests': instance.get('pending_requests', []),
            'children_summary': instance.get('children_summary', []),
            'recent_transactions': instance.get('recent_transactions', []),
            'budget_alerts': instance.get('budget_alerts', []),
            'monthly_spending_total': instance.get('monthly_spending_total', Decimal('0.00')),
        }
