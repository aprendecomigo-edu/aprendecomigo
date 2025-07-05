from django.contrib import admin

from .models import (
    ClassSchedule,
    RecurringClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
)


@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("teacher", "school", "day_of_week", "start_time", "end_time", "is_active")
    list_filter = ("day_of_week", "is_active", "school")
    search_fields = ("teacher__user__name", "teacher__user__email")
    ordering = ("teacher", "day_of_week", "start_time")


@admin.register(TeacherUnavailability)
class TeacherUnavailabilityAdmin(admin.ModelAdmin):
    list_display = ("teacher", "school", "date", "start_time", "end_time", "is_all_day", "reason")
    list_filter = ("is_all_day", "school", "date")
    search_fields = ("teacher__user__name", "teacher__user__email", "reason")
    ordering = ("-date", "start_time")


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "teacher",
        "student",
        "school",
        "scheduled_date",
        "start_time",
        "status",
    )
    list_filter = ("status", "class_type", "school", "scheduled_date")
    search_fields = ("title", "teacher__user__name", "student__name", "student__email")
    ordering = ("-scheduled_date", "start_time")
    readonly_fields = ("booked_at", "cancelled_at", "completed_at")

    fieldsets = (
        ("Class Information", {"fields": ("title", "description", "class_type", "status")}),
        ("Participants", {"fields": ("teacher", "student", "additional_students")}),
        (
            "Schedule",
            {"fields": ("school", "scheduled_date", "start_time", "end_time", "duration_minutes")},
        ),
        ("Booking Information", {"fields": ("booked_by", "booked_at")}),
        ("Status Information", {"fields": ("cancelled_at", "cancellation_reason", "completed_at")}),
        ("Notes", {"fields": ("teacher_notes", "student_notes")}),
    )


@admin.register(RecurringClassSchedule)
class RecurringClassScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "teacher",
        "student",
        "school",
        "day_of_week",
        "start_time",
        "is_active",
    )
    list_filter = ("day_of_week", "is_active", "school", "class_type")
    search_fields = ("title", "teacher__user__name", "student__name", "student__email")
    ordering = ("day_of_week", "start_time")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Class Information", {"fields": ("title", "description", "class_type")}),
        ("Participants", {"fields": ("teacher", "student")}),
        (
            "Schedule Pattern",
            {"fields": ("school", "day_of_week", "start_time", "end_time", "duration_minutes")},
        ),
        ("Period", {"fields": ("start_date", "end_date", "is_active")}),
        ("Metadata", {"fields": ("created_by", "created_at", "updated_at")}),
    )
