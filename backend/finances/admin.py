from typing import ClassVar

from django.contrib import admin
from django.db import models
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    ClassSession,
    FamilyBudgetControl,
    HourConsumption,
    PricingPlan,
    PurchaseApprovalRequest,
    PurchaseTransaction,
    SchoolBillingSettings,
    StudentAccountBalance,
    TeacherCompensationRule,
    TeacherPaymentEntry,
)
from .services import TeacherPaymentCalculator


@admin.register(SchoolBillingSettings)
class SchoolBillingSettingsAdmin(admin.ModelAdmin):
    """Admin interface for school billing settings."""

    list_display: ClassVar = [
        "school",
        "trial_cost_absorption",
        "teacher_payment_frequency",
        "payment_day_of_month",
        "updated_at",
    ]
    list_filter: ClassVar = [
        "trial_cost_absorption",
        "teacher_payment_frequency",
        "payment_day_of_month",
    ]
    search_fields: ClassVar = ["school__name"]
    readonly_fields: ClassVar = ["created_at", "updated_at"]

    fieldsets: ClassVar = (
        (None, {"fields": ("school",)}),
        (
            "Payment Settings",
            {
                "fields": (
                    "trial_cost_absorption",
                    "teacher_payment_frequency",
                    "payment_day_of_month",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(TeacherCompensationRule)
class TeacherCompensationRuleAdmin(admin.ModelAdmin):
    """Admin interface for teacher compensation rules."""

    list_display: ClassVar = [
        "teacher_name",
        "school",
        "rule_type",
        "grade_level",
        "rate_display",
        "is_active",
        "effective_from",
    ]
    list_filter: ClassVar = [
        "rule_type",
        "grade_level",
        "is_active",
        "school",
        "effective_from",
    ]
    search_fields: ClassVar = [
        "teacher__user__name",
        "teacher__user__email",
        "school__name",
    ]
    readonly_fields: ClassVar = ["created_at", "updated_at"]
    date_hierarchy: ClassVar = "effective_from"

    fieldsets: ClassVar = (
        (None, {"fields": ("teacher", "school", "rule_type")}),
        (
            "Rule Configuration",
            {
                "fields": (
                    "grade_level",
                    "rate_per_hour",
                    "fixed_amount",
                    "conditions",
                )
            },
        ),
        (
            "Status & Dates",
            {
                "fields": (
                    "is_active",
                    "effective_from",
                    "effective_until",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(
        description="Teacher",
        ordering="teacher__user__name",
    )
    def teacher_name(self, obj):
        """Display teacher name."""
        return obj.teacher.user.name

    @admin.display(description="Rate")
    def rate_display(self, obj):
        """Display the relevant rate based on rule type."""
        if obj.rate_per_hour:
            return format_html("€{}/hour", obj.rate_per_hour)
        elif obj.fixed_amount:
            return format_html("€{}/month", obj.fixed_amount)
        return "-"


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    """Admin interface for class sessions."""

    list_display: ClassVar = [
        "teacher_name",
        "school",
        "date",
        "time_range",
        "session_type",
        "grade_level",
        "student_count",
        "duration_display",
        "status",
        "is_trial",
        "payment_status",
    ]
    list_filter: ClassVar = [
        "status",
        "session_type",
        "grade_level",
        "is_trial",
        "is_makeup",
        "school",
        "date",
    ]
    search_fields: ClassVar = [
        "teacher__user__name",
        "teacher__user__email",
        "school__name",
        "students__name",
        "students__email",
    ]
    readonly_fields: ClassVar = ["created_at", "updated_at", "duration_display"]
    date_hierarchy: ClassVar = "date"
    filter_horizontal = ["students"]

    fieldsets: ClassVar = (
        (None, {"fields": ("teacher", "school")}),
        (
            "Session Details",
            {
                "fields": (
                    "date",
                    "start_time",
                    "end_time",
                    "duration_display",
                    "session_type",
                    "grade_level",
                )
            },
        ),
        (
            "Students",
            {
                "fields": (
                    "student_count",
                    "students",
                )
            },
        ),
        (
            "Flags & Status",
            {
                "fields": (
                    "status",
                    "is_trial",
                    "is_makeup",
                )
            },
        ),
        ("Additional Information", {"fields": ("notes",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    actions = ["mark_completed", "calculate_payments"]

    @admin.display(
        description="Teacher",
        ordering="teacher__user__name",
    )
    def teacher_name(self, obj):
        """Display teacher name."""
        return obj.teacher.user.name

    @admin.display(description="Time")
    def time_range(self, obj):
        """Display session time range."""
        return f"{obj.start_time} - {obj.end_time}"

    @admin.display(description="Duration")
    def duration_display(self, obj):
        """Display session duration."""
        return f"{obj.duration_hours} hours"

    @admin.display(description="Payment")
    def payment_status(self, obj):
        """Display payment calculation status."""
        if hasattr(obj, "payment_entry"):
            return format_html('<span style="color: green;">€{}</span>', obj.payment_entry.amount_earned)
        elif obj.status == "completed":
            return format_html('<span style="color: orange;">Pending</span>')
        else:
            return "-"

    @admin.action(description="Mark selected sessions as completed")
    def mark_completed(self, request, queryset):
        """Mark selected sessions as completed."""
        updated = queryset.update(status="completed")
        self.message_user(request, f"{updated} sessions marked as completed.")

    @admin.action(description="Calculate payments for completed sessions")
    def calculate_payments(self, request, queryset):
        """Calculate payments for completed sessions."""
        completed_sessions = queryset.filter(status="completed")
        calculated_count = 0

        for session in completed_sessions:
            if not hasattr(session, "payment_entry"):
                try:
                    TeacherPaymentCalculator.calculate_session_payment(session)
                    calculated_count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error calculating payment for session {session.id}: {e}",
                        level="ERROR",
                    )

        if calculated_count > 0:
            self.message_user(request, f"Calculated payments for {calculated_count} sessions.")
        else:
            self.message_user(
                request,
                "No payments calculated. Sessions must be completed and not already calculated.",
            )


@admin.register(TeacherPaymentEntry)
class TeacherPaymentEntryAdmin(admin.ModelAdmin):
    """Admin interface for teacher payment entries."""

    list_display: ClassVar = [
        "teacher_name",
        "school",
        "session_date",
        "billing_period",
        "hours_taught",
        "rate_applied",
        "amount_earned",
        "payment_status",
        "created_at",
    ]
    list_filter: ClassVar = [
        "payment_status",
        "billing_period",
        "school",
        "session__date",
        "session__session_type",
        "session__is_trial",
    ]
    search_fields: ClassVar = [
        "teacher__user__name",
        "teacher__user__email",
        "school__name",
        "billing_period",
    ]
    readonly_fields: ClassVar = [
        "session",
        "teacher",
        "school",
        "billing_period",
        "hours_taught",
        "rate_applied",
        "amount_earned",
        "compensation_rule",
        "calculation_notes",
        "created_at",
        "updated_at",
    ]
    date_hierarchy: ClassVar = "session__date"

    fieldsets: ClassVar = (
        (
            "Basic Information",
            {
                "fields": (
                    "session",
                    "teacher",
                    "school",
                    "billing_period",
                )
            },
        ),
        (
            "Payment Calculation",
            {
                "fields": (
                    "hours_taught",
                    "rate_applied",
                    "amount_earned",
                    "compensation_rule",
                )
            },
        ),
        (
            "Status & Notes",
            {
                "fields": (
                    "payment_status",
                    "calculation_notes",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    actions = ["mark_paid"]

    @admin.display(
        description="Teacher",
        ordering="teacher__user__name",
    )
    def teacher_name(self, obj):
        """Display teacher name."""
        return obj.teacher.user.name

    @admin.display(
        description="Session Date",
        ordering="session__date",
    )
    def session_date(self, obj):
        """Display session date."""
        return obj.session.date

    @admin.action(description="Mark selected payments as paid")
    def mark_paid(self, request, queryset):
        """Mark selected payment entries as paid."""
        updated = queryset.update(payment_status="paid")
        self.message_user(request, f"{updated} payment entries marked as paid.")

    def has_add_permission(self, request):
        """Disable manual creation of payment entries."""
        return False

    def has_change_permission(self, request, obj=None):
        """Only allow changing payment status."""
        return True

    def get_readonly_fields(self, request, obj=None):
        """Make most fields readonly, allow changing only payment status."""
        readonly = list(self.readonly_fields)
        if obj:
            # For existing objects, only allow changing payment status
            readonly.remove("payment_status") if "payment_status" in readonly else None
            return readonly
        return readonly


@admin.register(StudentAccountBalance)
class StudentAccountBalanceAdmin(admin.ModelAdmin):
    """Admin interface for student account balances."""

    list_display: ClassVar = [
        "student_name",
        "student_email",
        "hours_purchased",
        "hours_consumed",
        "remaining_hours_display",
        "balance_amount_display",
        "updated_at",
    ]
    list_filter: ClassVar = [
        "created_at",
        "updated_at",
    ]
    search_fields: ClassVar = [
        "student__name",
        "student__email",
    ]
    readonly_fields: ClassVar = ["created_at", "updated_at", "remaining_hours_display"]

    fieldsets: ClassVar = (
        (
            "Student Information",
            {"fields": ("student",)},
        ),
        (
            "Hours Tracking",
            {
                "fields": (
                    "hours_purchased",
                    "hours_consumed",
                    "remaining_hours_display",
                )
            },
        ),
        (
            "Financial Information",
            {"fields": ("balance_amount",)},
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(
        description="Student Name",
        ordering="student__name",
    )
    def student_name(self, obj):
        """Display student name."""
        return obj.student.name

    @admin.display(
        description="Student Email",
        ordering="student__email",
    )
    def student_email(self, obj):
        """Display student email."""
        return obj.student.email

    @admin.display(description="Remaining Hours")
    def remaining_hours_display(self, obj):
        """Display remaining hours with color coding."""
        remaining = obj.remaining_hours
        if remaining < 0:
            return format_html('<span style="color: red; font-weight: bold;">{} hours (overdraft)</span>', remaining)
        elif remaining < 2:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{} hours (low balance)</span>', remaining
            )
        else:
            return format_html('<span style="color: green;">{} hours</span>', remaining)

    @admin.display(description="Balance Amount")
    def balance_amount_display(self, obj):
        """Display balance amount with color coding."""
        if obj.balance_amount < 0:
            return format_html('<span style="color: red; font-weight: bold;">€{}</span>', obj.balance_amount)
        else:
            return format_html('<span style="color: green;">€{}</span>', obj.balance_amount)


@admin.register(PurchaseTransaction)
class PurchaseTransactionAdmin(admin.ModelAdmin):
    """Admin interface for purchase transactions."""

    list_display: ClassVar = [
        "transaction_id",
        "student_name",
        "student_email",
        "transaction_type",
        "amount_display",
        "payment_status",
        "stripe_payment_intent_id",
        "expires_at_display",
        "is_expired_display",
        "created_at",
    ]
    list_filter: ClassVar = [
        "transaction_type",
        "payment_status",
        "created_at",
        "expires_at",
    ]
    search_fields: ClassVar = [
        "student__name",
        "student__email",
        "stripe_payment_intent_id",
        "stripe_customer_id",
    ]
    readonly_fields: ClassVar = [
        "created_at",
        "updated_at",
        "is_expired_display",
    ]
    date_hierarchy: ClassVar = "created_at"

    fieldsets: ClassVar = (
        (
            "Transaction Information",
            {
                "fields": (
                    "student",
                    "transaction_type",
                    "amount",
                    "payment_status",
                )
            },
        ),
        (
            "Stripe Integration",
            {
                "fields": (
                    "stripe_payment_intent_id",
                    "stripe_customer_id",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Package Management",
            {
                "fields": (
                    "expires_at",
                    "is_expired_display",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_completed", "mark_failed", "mark_refunded"]

    @admin.display(
        description="Transaction ID",
        ordering="id",
    )
    def transaction_id(self, obj):
        """Display transaction ID."""
        return f"#{obj.id}"

    @admin.display(
        description="Student Name",
        ordering="student__name",
    )
    def student_name(self, obj):
        """Display student name."""
        return obj.student.name

    @admin.display(
        description="Student Email",
        ordering="student__email",
    )
    def student_email(self, obj):
        """Display student email."""
        return obj.student.email

    @admin.display(description="Amount")
    def amount_display(self, obj):
        """Display amount with currency formatting."""
        return format_html("€{}", obj.amount)

    @admin.display(description="Expires")
    def expires_at_display(self, obj):
        """Display expiration date or subscription indicator."""
        if obj.expires_at:
            return obj.expires_at.strftime("%Y-%m-%d %H:%M")
        else:
            return "Subscription (no expiration)"

    @admin.display(description="Status")
    def is_expired_display(self, obj):
        """Display expiration status with color coding."""
        if obj.transaction_type == "subscription":
            return format_html('<span style="color: blue;">Subscription</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red; font-weight: bold;">Expired</span>')
        elif obj.expires_at:
            return format_html('<span style="color: green;">Active</span>')
        else:
            return "-"

    @admin.action(description="Mark selected transactions as completed")
    def mark_completed(self, request, queryset):
        """Mark selected transactions as completed."""
        updated = 0
        for transaction in queryset:
            if transaction.payment_status != "completed":
                transaction.mark_completed()
                updated += 1

        self.message_user(request, f"{updated} transactions marked as completed.")

    @admin.action(description="Mark selected transactions as failed")
    def mark_failed(self, request, queryset):
        """Mark selected transactions as failed."""
        updated = queryset.update(payment_status="failed")
        self.message_user(request, f"{updated} transactions marked as failed.")

    @admin.action(description="Mark selected transactions as refunded")
    def mark_refunded(self, request, queryset):
        """Mark selected transactions as refunded."""
        updated = queryset.update(payment_status="refunded")
        self.message_user(request, f"{updated} transactions marked as refunded.")

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("student")


@admin.register(HourConsumption)
class HourConsumptionAdmin(admin.ModelAdmin):
    """Admin interface for hour consumption tracking."""

    list_display: ClassVar = [
        "consumption_id",
        "student_name",
        "session_date",
        "session_time_range",
        "hours_consumed",
        "hours_originally_reserved",
        "hours_difference_display",
        "is_refunded",
        "consumed_at",
    ]
    list_filter: ClassVar = [
        "is_refunded",
        "consumed_at",
        "class_session__date",
        "class_session__session_type",
        "class_session__status",
        "student_account__student",
    ]
    search_fields: ClassVar = [
        "student_account__student__name",
        "student_account__student__email",
        "class_session__teacher__user__name",
        "purchase_transaction__stripe_payment_intent_id",
    ]
    readonly_fields: ClassVar = [
        "consumed_at",
        "created_at",
        "updated_at",
        "hours_difference_display",
        "student_balance_display",
    ]
    date_hierarchy: ClassVar = "consumed_at"

    fieldsets: ClassVar = (
        (
            "Consumption Information",
            {
                "fields": (
                    "student_account",
                    "class_session",
                    "purchase_transaction",
                )
            },
        ),
        (
            "Hours Tracking",
            {
                "fields": (
                    "hours_consumed",
                    "hours_originally_reserved",
                    "hours_difference_display",
                    "consumed_at",
                )
            },
        ),
        (
            "Student Balance",
            {
                "fields": ("student_balance_display",),
                "classes": ("collapse",),
            },
        ),
        (
            "Refund Information",
            {
                "fields": (
                    "is_refunded",
                    "refund_reason",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["process_refunds"]

    @admin.display(
        description="Consumption ID",
        ordering="id",
    )
    def consumption_id(self, obj):
        """Display consumption ID."""
        return f"#{obj.id}"

    @admin.display(
        description="Student",
        ordering="student_account__student__name",
    )
    def student_name(self, obj):
        """Display student name."""
        return obj.student_account.student.name

    @admin.display(
        description="Session Date",
        ordering="class_session__date",
    )
    def session_date(self, obj):
        """Display session date."""
        return obj.class_session.date

    @admin.display(description="Session Time")
    def session_time_range(self, obj):
        """Display session time range."""
        return f"{obj.class_session.start_time} - {obj.class_session.end_time}"

    @admin.display(description="Hours Difference")
    def hours_difference_display(self, obj):
        """Display hours difference with color coding."""
        difference = obj.hours_difference
        if difference > 0:
            return format_html(
                '<span style="color: orange; font-weight: bold;">+{} hours (refund due)</span>', difference
            )
        elif difference < 0:
            return format_html('<span style="color: red;">-{} hours (overtime)</span>', abs(difference))
        else:
            return format_html('<span style="color: green;">Exact match</span>')

    @admin.display(description="Student Balance")
    def student_balance_display(self, obj):
        """Display current student balance information."""
        balance = obj.student_account
        remaining = balance.remaining_hours
        if remaining < 0:
            hours_info = format_html(
                '<span style="color: red; font-weight: bold;">{} hours (overdraft)</span>', remaining
            )
        elif remaining < 2:
            hours_info = format_html(
                '<span style="color: orange; font-weight: bold;">{} hours (low balance)</span>', remaining
            )
        else:
            hours_info = format_html('<span style="color: green;">{} hours</span>', remaining)

        return format_html("{} | €{}", hours_info, balance.balance_amount)

    @admin.action(description="Process refunds for early session endings")
    def process_refunds(self, request, queryset):
        """Process refunds for consumptions with early session endings."""
        refund_candidates = queryset.filter(is_refunded=False, hours_consumed__lt=models.F("hours_originally_reserved"))

        refunded_count = 0
        total_refunded_hours = 0

        for consumption in refund_candidates:
            refund_hours = consumption.process_refund("Admin bulk refund process")
            if refund_hours > 0:
                refunded_count += 1
                total_refunded_hours += refund_hours

        if refunded_count > 0:
            self.message_user(request, f"Processed {refunded_count} refunds totaling {total_refunded_hours} hours.")
        else:
            self.message_user(
                request,
                "No refunds processed. Selected consumptions either have no refund due or are already refunded.",
            )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("student_account__student", "class_session__teacher__user", "purchase_transaction")
        )


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    """
    Comprehensive Django Admin interface for PricingPlan model.

    Provides business users with full control over pricing plan configuration
    including bulk actions for managing plan status and advanced filtering.
    """

    list_display: ClassVar = [
        "name",
        "plan_type_display",
        "hours_included",
        "price_display",
        "price_per_hour_display",
        "validity_display",
        "display_order",
        "is_featured_display",
        "is_active_display",
        "created_at",
    ]

    list_filter: ClassVar = [
        "plan_type",
        "is_active",
        "is_featured",
        "created_at",
        "updated_at",
    ]

    search_fields: ClassVar = [
        "name",
        "description",
    ]

    readonly_fields: ClassVar = [
        "created_at",
        "updated_at",
        "price_per_hour_display",
    ]

    ordering: ClassVar = ["display_order", "name"]

    fieldsets: ClassVar = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "description",
                    "plan_type",
                )
            },
        ),
        (
            "Pricing Configuration",
            {
                "fields": (
                    "hours_included",
                    "price_eur",
                    "price_per_hour_display",
                    "validity_days",
                )
            },
        ),
        (
            "Display Settings",
            {
                "fields": (
                    "display_order",
                    "is_featured",
                    "is_active",
                )
            },
        ),
        (
            "Audit Information",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = [
        "activate_plans",
        "deactivate_plans",
        "mark_as_featured",
        "remove_featured_status",
    ]

    @admin.display(description="Plan Type", ordering="plan_type")
    def plan_type_display(self, obj):
        """Display plan type with visual indicator."""
        if obj.plan_type == "package":
            return format_html('<span style="color: blue; font-weight: bold;">📦 Package</span>')
        else:
            return format_html('<span style="color: green; font-weight: bold;">🔄 Subscription</span>')

    @admin.display(description="Price")
    def price_display(self, obj):
        """Display price with currency formatting."""
        return format_html("€{}", obj.price_eur)

    @admin.display(description="Price/Hour")
    def price_per_hour_display(self, obj):
        """Display calculated price per hour."""
        price_per_hour = obj.price_per_hour
        if price_per_hour:
            return format_html("€{:.2f}", price_per_hour)
        return "-"

    @admin.display(description="Validity")
    def validity_display(self, obj):
        """Display validity period with appropriate formatting."""
        if obj.validity_days:
            return format_html('<span style="color: orange;">{} days</span>', obj.validity_days)
        else:
            return format_html('<span style="color: green;">Subscription</span>')

    @admin.display(description="Featured", boolean=True)
    def is_featured_display(self, obj):
        """Display featured status with visual indicator."""
        return obj.is_featured

    @admin.display(description="Active", boolean=True)
    def is_active_display(self, obj):
        """Display active status with visual indicator."""
        return obj.is_active

    @admin.action(description="Activate selected pricing plans")
    def activate_plans(self, request, queryset):
        """Bulk action to activate pricing plans."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {updated} pricing plan(s).")

    @admin.action(description="Deactivate selected pricing plans")
    def deactivate_plans(self, request, queryset):
        """Bulk action to deactivate pricing plans."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {updated} pricing plan(s).")

    @admin.action(description="Mark selected plans as featured")
    def mark_as_featured(self, request, queryset):
        """Bulk action to mark plans as featured."""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"Successfully marked {updated} pricing plan(s) as featured.")

    @admin.action(description="Remove featured status from selected plans")
    def remove_featured_status(self, request, queryset):
        """Bulk action to remove featured status."""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"Successfully removed featured status from {updated} pricing plan(s).")

    def save_model(self, request, obj, form, change):
        """Override save to provide user feedback on validation."""
        try:
            super().save_model(request, obj, form, change)
            if not change:  # Creating new object
                self.message_user(request, f"Pricing plan '{obj.name}' created successfully.", level="SUCCESS")
        except Exception as e:
            self.message_user(request, f"Error saving pricing plan: {e}", level="ERROR")

    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request)


# =======================
# PARENT-CHILD PURCHASE APPROVAL ADMIN (Issues #111 & #112)
# =======================


@admin.register(FamilyBudgetControl)
class FamilyBudgetControlAdmin(admin.ModelAdmin):
    """Admin interface for family budget controls."""

    list_display: ClassVar = [
        "parent_name",
        "child_name",
        "school_name",
        "monthly_limit_display",
        "weekly_limit_display",
        "auto_approval_display",
        "sessions_approval",
        "packages_approval",
        "is_active",
        "updated_at",
    ]
    list_filter: ClassVar = [
        "require_approval_for_sessions",
        "require_approval_for_packages",
        "is_active",
        "parent_child_relationship__school",
        "created_at",
        "updated_at",
    ]
    search_fields: ClassVar = [
        "parent_child_relationship__parent__name",
        "parent_child_relationship__parent__email",
        "parent_child_relationship__child__name",
        "parent_child_relationship__child__email",
        "parent_child_relationship__school__name",
    ]
    readonly_fields: ClassVar = ["current_monthly_spending", "current_weekly_spending", "created_at", "updated_at"]

    fieldsets: ClassVar = (
        ("Relationship Information", {"fields": ("parent_child_relationship",)}),
        (
            "Budget Limits",
            {
                "fields": (
                    "monthly_budget_limit",
                    "weekly_budget_limit",
                    "current_monthly_spending",
                    "current_weekly_spending",
                )
            },
        ),
        (
            "Approval Settings",
            {
                "fields": (
                    "auto_approval_threshold",
                    "require_approval_for_sessions",
                    "require_approval_for_packages",
                )
            },
        ),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(
        description="Parent",
        ordering="parent_child_relationship__parent__name",
    )
    def parent_name(self, obj):
        """Display parent name."""
        return obj.parent_child_relationship.parent.name

    @admin.display(
        description="Child",
        ordering="parent_child_relationship__child__name",
    )
    def child_name(self, obj):
        """Display child name."""
        return obj.parent_child_relationship.child.name

    @admin.display(
        description="School",
        ordering="parent_child_relationship__school__name",
    )
    def school_name(self, obj):
        """Display school name."""
        return obj.parent_child_relationship.school.name

    @admin.display(description="Monthly Limit")
    def monthly_limit_display(self, obj):
        """Display monthly budget limit."""
        if obj.monthly_budget_limit:
            return format_html("€{}", obj.monthly_budget_limit)
        return format_html('<span style="color: gray;">No limit</span>')

    @admin.display(description="Weekly Limit")
    def weekly_limit_display(self, obj):
        """Display weekly budget limit."""
        if obj.weekly_budget_limit:
            return format_html("€{}", obj.weekly_budget_limit)
        return format_html('<span style="color: gray;">No limit</span>')

    @admin.display(description="Auto Approval")
    def auto_approval_display(self, obj):
        """Display auto approval threshold."""
        if obj.auto_approval_threshold > 0:
            return format_html("€{}", obj.auto_approval_threshold)
        return format_html('<span style="color: red;">Manual only</span>')

    @admin.display(description="Sessions", boolean=True)
    def sessions_approval(self, obj):
        """Display session approval requirement."""
        return obj.require_approval_for_sessions

    @admin.display(description="Packages", boolean=True)
    def packages_approval(self, obj):
        """Display package approval requirement."""
        return obj.require_approval_for_packages

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "parent_child_relationship__parent",
                "parent_child_relationship__child",
                "parent_child_relationship__school",
            )
        )


@admin.register(PurchaseApprovalRequest)
class PurchaseApprovalRequestAdmin(admin.ModelAdmin):
    """Admin interface for purchase approval requests."""

    list_display: ClassVar = [
        "request_id",
        "student_name",
        "parent_name",
        "amount_display",
        "request_type_display",
        "status_display",
        "requested_at",
        "time_remaining_display",
        "is_expired_display",
    ]
    list_filter: ClassVar = [
        "status",
        "request_type",
        "requested_at",
        "expires_at",
        "parent_child_relationship__school",
    ]
    search_fields: ClassVar = [
        "student__name",
        "student__email",
        "parent__name",
        "parent__email",
        "description",
    ]
    readonly_fields: ClassVar = [
        "time_remaining_display",
        "is_expired_display",
        "requested_at",
        "responded_at",
        "created_at",
        "updated_at",
    ]
    date_hierarchy: ClassVar = "requested_at"
    ordering: ClassVar = ["-requested_at"]

    fieldsets: ClassVar = (
        (
            "Request Information",
            {
                "fields": (
                    "student",
                    "parent",
                    "parent_child_relationship",
                    "amount",
                    "description",
                    "request_type",
                )
            },
        ),
        (
            "Related Items",
            {
                "fields": (
                    "pricing_plan",
                    "class_session",
                    "request_metadata",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Approval Status",
            {
                "fields": (
                    "status",
                    "parent_notes",
                    "responded_at",
                )
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    "requested_at",
                    "expires_at",
                    "time_remaining_display",
                    "is_expired_display",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["approve_requests", "deny_requests", "mark_expired"]

    @admin.display(
        description="Request ID",
        ordering="id",
    )
    def request_id(self, obj):
        """Display request ID."""
        return f"#{obj.id}"

    @admin.display(
        description="Student",
        ordering="student__name",
    )
    def student_name(self, obj):
        """Display student name."""
        return obj.student.name

    @admin.display(
        description="Parent",
        ordering="parent__name",
    )
    def parent_name(self, obj):
        """Display parent name."""
        return obj.parent.name

    @admin.display(description="Amount")
    def amount_display(self, obj):
        """Display amount with currency formatting."""
        return format_html("€{}", obj.amount)

    @admin.display(description="Type")
    def request_type_display(self, obj):
        """Display request type with icon."""
        type_icons = {"hours": "📚", "session": "👨‍🏫", "subscription": "🔄"}
        icon = type_icons.get(obj.request_type, "📋")
        return format_html("{} {}", icon, obj.get_request_type_display())

    @admin.display(description="Status")
    def status_display(self, obj):
        """Display status with color coding."""
        status_colors = {
            "pending": "orange",
            "approved": "green",
            "denied": "red",
            "expired": "gray",
            "cancelled": "purple",
        }
        color = status_colors.get(obj.status, "black")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())

    @admin.display(description="Time Remaining")
    def time_remaining_display(self, obj):
        """Display time remaining until expiration."""
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.status != "pending":
            return format_html('<span style="color: gray;">N/A</span>')
        else:
            remaining = obj.time_remaining
            hours = remaining.total_seconds() / 3600
            if hours < 1:
                return format_html(
                    '<span style="color: red; font-weight: bold;">{:.0f} min</span>', remaining.total_seconds() / 60
                )
            elif hours < 6:
                return format_html('<span style="color: orange; font-weight: bold;">{:.1f} hours</span>', hours)
            else:
                return format_html('<span style="color: green;">{:.1f} hours</span>', hours)

    @admin.display(description="Expired", boolean=True)
    def is_expired_display(self, obj):
        """Display expiration status."""
        return obj.is_expired

    @admin.action(description="Approve selected requests")
    def approve_requests(self, request, queryset):
        """Bulk approve requests."""
        pending_requests = queryset.filter(status="pending")
        approved_count = 0

        for approval_request in pending_requests:
            if not approval_request.is_expired:
                try:
                    approval_request.approve("Bulk approved by admin")
                    approved_count += 1
                except Exception as e:
                    self.message_user(request, f"Error approving request {approval_request.id}: {e}", level="ERROR")

        if approved_count > 0:
            self.message_user(request, f"Successfully approved {approved_count} request(s).")
        else:
            self.message_user(request, "No requests were approved. Requests must be pending and not expired.")

    @admin.action(description="Deny selected requests")
    def deny_requests(self, request, queryset):
        """Bulk deny requests."""
        pending_requests = queryset.filter(status="pending")
        denied_count = 0

        for approval_request in pending_requests:
            try:
                approval_request.deny("Bulk denied by admin")
                denied_count += 1
            except Exception as e:
                self.message_user(request, f"Error denying request {approval_request.id}: {e}", level="ERROR")

        if denied_count > 0:
            self.message_user(request, f"Successfully denied {denied_count} request(s).")
        else:
            self.message_user(request, "No requests were denied. Requests must be pending.")

    @admin.action(description="Mark expired requests as expired")
    def mark_expired(self, request, queryset):
        """Mark expired pending requests as expired."""
        expired_requests = queryset.filter(status="pending").filter(expires_at__lt=timezone.now())

        expired_count = 0
        for approval_request in expired_requests:
            approval_request.mark_expired()
            expired_count += 1

        if expired_count > 0:
            self.message_user(request, f"Successfully marked {expired_count} request(s) as expired.")
        else:
            self.message_user(request, "No expired requests found.")

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("student", "parent", "parent_child_relationship__school", "pricing_plan", "class_session")
        )


# Register admin for related models from other apps in AppConfig.ready()
# Payment = apps.get_model('finances', 'Payment')
# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display: ClassVar = ['id', 'user', 'amount', 'status', 'created_at']
#
#     def get_queryset(self, request):
#         # Use select_related with string references
#         return super().get_queryset(request).select_related('user', 'lesson')
