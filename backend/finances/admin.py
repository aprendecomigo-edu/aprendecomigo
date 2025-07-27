from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ClassSession,
    SchoolBillingSettings,
    StudentAccountBalance,
    TeacherCompensationRule,
    TeacherPaymentEntry,
)
from .services import TeacherPaymentCalculator


@admin.register(SchoolBillingSettings)
class SchoolBillingSettingsAdmin(admin.ModelAdmin):
    """Admin interface for school billing settings."""

    list_display = [
        "school",
        "trial_cost_absorption",
        "teacher_payment_frequency",
        "payment_day_of_month",
        "updated_at",
    ]
    list_filter = [
        "trial_cost_absorption",
        "teacher_payment_frequency",
        "payment_day_of_month",
    ]
    search_fields = ["school__name"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
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

    list_display = [
        "teacher_name",
        "school",
        "rule_type",
        "grade_level",
        "rate_display",
        "is_active",
        "effective_from",
    ]
    list_filter = [
        "rule_type",
        "grade_level",
        "is_active",
        "school",
        "effective_from",
    ]
    search_fields = [
        "teacher__user__name",
        "teacher__user__email",
        "school__name",
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "effective_from"

    fieldsets = (
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


    @admin.display(
        description="Rate"
    )
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

    list_display = [
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
    list_filter = [
        "status",
        "session_type",
        "grade_level",
        "is_trial",
        "is_makeup",
        "school",
        "date",
    ]
    search_fields = [
        "teacher__user__name",
        "teacher__user__email",
        "school__name",
        "students__name",
        "students__email",
    ]
    readonly_fields = ["created_at", "updated_at", "duration_display"]
    date_hierarchy = "date"
    filter_horizontal = ["students"]

    fieldsets = (
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


    @admin.display(
        description="Time"
    )
    def time_range(self, obj):
        """Display session time range."""
        return f"{obj.start_time} - {obj.end_time}"


    @admin.display(
        description="Duration"
    )
    def duration_display(self, obj):
        """Display session duration."""
        return f"{obj.duration_hours} hours"


    @admin.display(
        description="Payment"
    )
    def payment_status(self, obj):
        """Display payment calculation status."""
        if hasattr(obj, "payment_entry"):
            return format_html(
                '<span style="color: green;">€{}</span>', obj.payment_entry.amount_earned
            )
        elif obj.status == "completed":
            return format_html('<span style="color: orange;">Pending</span>')
        else:
            return "-"


    @admin.action(
        description="Mark selected sessions as completed"
    )
    def mark_completed(self, request, queryset):
        """Mark selected sessions as completed."""
        updated = queryset.update(status="completed")
        self.message_user(request, f"{updated} sessions marked as completed.")


    @admin.action(
        description="Calculate payments for completed sessions"
    )
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

    list_display = [
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
    list_filter = [
        "payment_status",
        "billing_period",
        "school",
        "session__date",
        "session__session_type",
        "session__is_trial",
    ]
    search_fields = [
        "teacher__user__name",
        "teacher__user__email",
        "school__name",
        "billing_period",
    ]
    readonly_fields = [
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
    date_hierarchy = "session__date"

    fieldsets = (
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


    @admin.action(
        description="Mark selected payments as paid"
    )
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

    list_display = [
        "student_name",
        "student_email",
        "hours_purchased",
        "hours_consumed",
        "remaining_hours_display",
        "balance_amount_display",
        "updated_at",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "student__name",
        "student__email",
    ]
    readonly_fields = ["created_at", "updated_at", "remaining_hours_display"]

    fieldsets = (
        (
            "Student Information",
            {
                "fields": ("student",)
            },
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
            {
                "fields": ("balance_amount",)
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            }
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

    @admin.display(
        description="Remaining Hours"
    )
    def remaining_hours_display(self, obj):
        """Display remaining hours with color coding."""
        remaining = obj.remaining_hours
        if remaining < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} hours (overdraft)</span>',
                remaining
            )
        elif remaining < 2:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{} hours (low balance)</span>',
                remaining
            )
        else:
            return format_html(
                '<span style="color: green;">{} hours</span>',
                remaining
            )

    @admin.display(
        description="Balance Amount"
    )
    def balance_amount_display(self, obj):
        """Display balance amount with color coding."""
        if obj.balance_amount < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">€{}</span>',
                obj.balance_amount
            )
        else:
            return format_html(
                '<span style="color: green;">€{}</span>',
                obj.balance_amount
            )
