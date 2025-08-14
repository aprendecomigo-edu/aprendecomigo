from django.contrib import admin

from .models import (
    EmailCommunication,
    EmailSequence,
    EmailSequenceStep,
    Notification,
    SchoolEmailTemplate,
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model."""

    list_display = ("user", "notification_type", "title", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("user__name", "user__email", "title", "message")
    readonly_fields = ("created_at", "updated_at", "read_at")

    fieldsets = (
        (None, {"fields": ("user", "notification_type", "title", "message")}),
        ("Status", {"fields": ("is_read", "read_at")}),
        ("Related", {"fields": ("related_transaction", "metadata")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "related_transaction")


@admin.register(SchoolEmailTemplate)
class SchoolEmailTemplateAdmin(admin.ModelAdmin):
    """Admin interface for SchoolEmailTemplate model."""

    list_display = ("name", "school", "template_type", "is_active", "is_default", "created_at")
    list_filter = ("template_type", "is_active", "is_default", "use_school_branding", "created_at")
    search_fields = ("name", "school__name", "template_type", "subject_template")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("school", "template_type", "name", "created_by")}),
        ("Template Content", {"fields": ("subject_template", "html_content", "text_content")}),
        ("Branding", {"fields": ("use_school_branding", "custom_css")}),
        ("Settings", {"fields": ("is_active", "is_default")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("school", "created_by")


@admin.register(EmailSequence)
class EmailSequenceAdmin(admin.ModelAdmin):
    """Admin interface for EmailSequence model."""

    list_display = ("name", "school", "trigger_event", "is_active", "max_emails", "created_at")
    list_filter = ("trigger_event", "is_active", "created_at")
    search_fields = ("name", "school__name", "description")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("school", "name", "description")}),
        ("Configuration", {"fields": ("trigger_event", "is_active", "max_emails")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("school")


@admin.register(EmailSequenceStep)
class EmailSequenceStepAdmin(admin.ModelAdmin):
    """Admin interface for EmailSequenceStep model."""

    list_display = ("sequence", "step_number", "template", "delay_hours", "send_condition", "is_active")
    list_filter = ("send_condition", "is_active", "delay_hours")
    search_fields = ("sequence__name", "template__name", "sequence__school__name")

    fieldsets = (
        (None, {"fields": ("sequence", "template", "step_number")}),
        ("Configuration", {"fields": ("delay_hours", "send_condition", "is_active")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("sequence", "template", "sequence__school")


@admin.register(EmailCommunication)
class EmailCommunicationAdmin(admin.ModelAdmin):
    """Admin interface for EmailCommunication model."""

    list_display = ("recipient_email", "school", "template_type", "delivery_status", "queued_at", "retry_count")
    list_filter = ("template_type", "communication_type", "delivery_status", "queued_at")
    search_fields = ("recipient_email", "school__name", "subject", "recipient__name")
    readonly_fields = ("queued_at", "sent_at", "delivered_at", "opened_at", "clicked_at", "failed_at")

    fieldsets = (
        ("Recipient", {"fields": ("recipient", "recipient_email", "school")}),
        ("Email Details", {"fields": ("template", "template_type", "subject")}),
        ("Communication", {"fields": ("communication_type", "sequence", "sequence_step", "teacher_invitation")}),
        ("Delivery", {"fields": ("delivery_status", "retry_count", "max_retries", "failure_reason")}),
        ("Metadata", {"fields": ("created_by",)}),
        (
            "Timestamps",
            {
                "fields": ("queued_at", "sent_at", "delivered_at", "opened_at", "clicked_at", "failed_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "recipient", "school", "template", "sequence", "sequence_step", "teacher_invitation", "created_by"
            )
        )
