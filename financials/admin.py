from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import PaymentPlan, StudentPayment, TeacherCompensation


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "plan_type",
        "rate",
        "hours_included",
        "expiration_period",
        "class_type",
    )
    list_filter = ("plan_type", "class_type")
    search_fields = ("name", "description")
    fieldsets = (
        (None, {"fields": ("name", "description", "plan_type", "rate")}),
        (
            _("Package Details"),
            {
                "fields": ("hours_included", "expiration_period"),
                "classes": ("collapse",),
                "description": _("Only applicable for package plans"),
            },
        ),
        (
            _("Class Type"),
            {
                "fields": ("class_type",),
                "description": _("Link payment plan to a specific class type"),
            },
        ),
    )


@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "payment_plan",
        "amount_paid",
        "payment_date",
        "status",
        "remaining_hours",
        "is_expired",
    )
    list_filter = ("status", "payment_date", "payment_plan__plan_type")
    search_fields = ("student__name", "student__email", "notes")
    date_hierarchy = "payment_date"
    readonly_fields = ("remaining_hours", "is_expired")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "student",
                    "payment_plan",
                    "amount_paid",
                    "payment_date",
                    "status",
                    "notes",
                )
            },
        ),
        (
            _("Monthly Plan Details"),
            {
                "fields": ("period_start", "period_end"),
                "classes": ("collapse",),
                "description": _("Only applicable for monthly plans"),
            },
        ),
        (
            _("Package Plan Details"),
            {
                "fields": (
                    "hours_purchased",
                    "hours_used",
                    "remaining_hours",
                    "is_expired",
                ),
                "classes": ("collapse",),
                "description": _("Only applicable for package plans"),
            },
        ),
    )

    @admin.display(description=_("Remaining Hours"))
    def remaining_hours(self, obj):
        return obj.remaining_hours

    @admin.display(
        description=_("Expired"),
        boolean=True,
    )
    def is_expired(self, obj):
        return obj.is_expired


@admin.register(TeacherCompensation)
class TeacherCompensationAdmin(admin.ModelAdmin):
    list_display = (
        "teacher",
        "period_start",
        "period_end",
        "hours_taught",
        "amount_owed",
        "amount_paid",
        "status",
        "is_fully_paid",
    )
    list_filter = ("status", "period_start", "teacher")
    search_fields = ("teacher__name", "teacher__email", "notes")
    date_hierarchy = "period_start"
    readonly_fields = ("is_fully_paid",)
    filter_horizontal = ("class_sessions",)

    fieldsets = (
        (None, {"fields": ("teacher", "period_start", "period_end", "status")}),
        (
            _("Financial Information"),
            {
                "fields": (
                    "hours_taught",
                    "amount_owed",
                    "amount_paid",
                    "payment_date",
                    "is_fully_paid",
                )
            },
        ),
        (_("Class Sessions"), {"fields": ("class_sessions",)}),
        (_("Additional Information"), {"fields": ("notes",), "classes": ("collapse",)}),
    )

    @admin.display(
        description=_("Fully Paid"),
        boolean=True,
    )
    def is_fully_paid(self, obj):
        return obj.is_fully_paid
