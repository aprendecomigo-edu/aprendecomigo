from django.contrib import admin

from .models import (
    Assignment,
    AssignmentSubmission,
    Course,
    Enrollment,
    Lesson,
    Payment,
    Subject,
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "code"]
    ordering = ["name"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "teacher",
        "subject",
        "course_type",
        "status",
        "price_per_hour",
        "enrolled_students_count",
        "start_date",
        "end_date",
    ]
    list_filter = ["status", "course_type", "subject", "start_date"]
    search_fields = ["title", "teacher__user__first_name", "teacher__user__last_name"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "subject", "teacher")}),
        ("Course Settings", {"fields": ("course_type", "status", "max_students")}),
        ("Pricing", {"fields": ("price_per_hour", "total_hours")}),
        ("Schedule", {"fields": ("start_date", "end_date")}),
        ("Additional Info", {"fields": ("learning_objectives", "prerequisites", "materials_needed")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "course",
        "status",
        "progress_percentage",
        "hours_completed",
        "is_paid",
        "enrollment_date",
    ]
    list_filter = ["status", "is_paid", "is_active", "enrollment_date"]
    search_fields = ["student__user__first_name", "student__user__last_name", "course__title"]
    ordering = ["-enrollment_date"]
    readonly_fields = ["enrollment_date"]

    actions = ["mark_as_paid", "update_progress"]

    def mark_as_paid(self, request, queryset):
        queryset.update(is_paid=True)
        self.message_user(request, f"{queryset.count()} enrollments marked as paid.")

    mark_as_paid.short_description = "Mark selected enrollments as paid"

    def update_progress(self, request, queryset):
        for enrollment in queryset:
            enrollment.update_progress()
        self.message_user(request, f"Progress updated for {queryset.count()} enrollments.")

    update_progress.short_description = "Update progress for selected enrollments"


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "scheduled_date", "status", "duration_minutes", "students_count"]
    list_filter = ["status", "scheduled_date", "course__subject"]
    search_fields = ["title", "course__title"]
    ordering = ["scheduled_date"]
    filter_horizontal = ["students_present"]

    def students_count(self, obj):
        return obj.students_present.count()

    students_count.short_description = "Students Present"


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "assignment_type", "due_date", "max_points", "submissions_count", "is_active"]
    list_filter = ["assignment_type", "due_date", "is_active"]
    search_fields = ["title", "course__title"]
    ordering = ["due_date"]

    def submissions_count(self, obj):
        return obj.submissions.count()

    submissions_count.short_description = "Submissions"


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ["student", "assignment", "submitted_at", "grade_percentage", "is_late", "is_draft"]
    list_filter = ["is_late", "is_draft", "submitted_at", "graded_at"]
    search_fields = ["student__user__first_name", "student__user__last_name", "assignment__title"]
    ordering = ["-submitted_at"]
    readonly_fields = ["submitted_at", "is_late", "grade_percentage"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "teacher",
        "amount",
        "teacher_amount",
        "platform_fee",
        "status",
        "payment_type",
        "created_at",
    ]
    list_filter = ["status", "payment_type", "created_at", "processed_at"]
    search_fields = [
        "student__user__first_name",
        "student__user__last_name",
        "teacher__user__first_name",
        "teacher__user__last_name",
        "stripe_payment_intent_id",
    ]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "processed_at", "platform_fee", "teacher_amount"]

    actions = ["calculate_teacher_amounts"]

    def calculate_teacher_amounts(self, request, queryset):
        for payment in queryset:
            payment.calculate_teacher_amount()
            payment.save()
        self.message_user(request, f"Teacher amounts calculated for {queryset.count()} payments.")

    calculate_teacher_amounts.short_description = "Recalculate teacher amounts"
