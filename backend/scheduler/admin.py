from typing import ClassVar

from django.contrib import admin

from .models import (
    ClassSchedule,
    RecurringClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
)


@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("teacher", "school", "day_of_week", "start_time", "end_time", "is_active")
    list_filter: ClassVar = ("day_of_week", "is_active", "school")
    search_fields: ClassVar = ("teacher__user__name", "teacher__user__email")
    ordering: ClassVar = ("teacher", "day_of_week", "start_time")


@admin.register(TeacherUnavailability)
class TeacherUnavailabilityAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("teacher", "school", "date", "start_time", "end_time", "is_all_day", "reason")
    list_filter: ClassVar = ("is_all_day", "school", "date")
    search_fields: ClassVar = ("teacher__user__name", "teacher__user__email", "reason")
    ordering: ClassVar = ("-date", "start_time")


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display: ClassVar = (
        "title",
        "teacher",
        "student",
        "school",
        "scheduled_date",
        "start_time",
        "status",
    )
    list_filter: ClassVar = ("status", "class_type", "school", "scheduled_date")
    search_fields: ClassVar = ("title", "teacher__user__name", "student__name", "student__email")
    ordering: ClassVar = ("-scheduled_date", "start_time")
    readonly_fields: ClassVar = ("booked_at", "cancelled_at", "completed_at")

    fieldsets: ClassVar = (
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
    list_display: ClassVar = (
        "title",
        "teacher",
        "get_students_display",
        "school",
        "frequency_type",
        "status",
        "day_of_week",
        "start_time",
        "is_active",
    )
    list_filter: ClassVar = ("day_of_week", "status", "frequency_type", "is_active", "school", "class_type")
    search_fields: ClassVar = ("title", "teacher__user__name", "students__name", "students__email")
    ordering: ClassVar = ("day_of_week", "start_time")
    readonly_fields: ClassVar = ("created_at", "updated_at", "cancelled_at", "paused_at")
    filter_horizontal = ("students",)

    def get_students_display(self, obj):
        """Display students in a readable format"""
        student_names = [student.name for student in obj.students.all()[:3]]
        if obj.students.count() > 3:
            student_names.append(f"... (+{obj.students.count() - 3} more)")
        return ", ".join(student_names) if student_names else "No students"

    get_students_display.short_description = "Students"

    fieldsets: ClassVar = (
        ("Class Information", {"fields": ("title", "description", "class_type", "max_participants")}),
        ("Participants", {"fields": ("teacher", "students")}),
        (
            "Schedule Pattern",
            {"fields": ("school", "frequency_type", "day_of_week", "start_time", "end_time", "duration_minutes")},
        ),
        ("Status & Period", {"fields": ("status", "start_date", "end_date", "is_active")}),
        ("Status Changes", {"fields": ("cancelled_at", "cancelled_by", "paused_at", "paused_by")}),
        ("Metadata", {"fields": ("created_by", "created_at", "updated_at")}),
    )
