from typing import ClassVar

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Course,
    CustomUser,
    ParentChildRelationship,
    ParentProfile,
    School,
    SchoolMembership,
    StudentProfile,
    TeacherCourse,
    TeacherProfile,
    VerificationCode,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display: ClassVar = ("email", "name", "is_staff")
    list_filter: ClassVar = ("is_staff", "is_superuser", "is_active")
    fieldsets: ClassVar = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name", "phone_number")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "password1", "password2"),
            },
        ),
    )
    search_fields: ClassVar = ("email", "name")
    ordering: ClassVar = ("email",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("get_name", "get_email", "school_year", "birth_date")
    list_filter: ClassVar = ("school_year",)
    search_fields: ClassVar = ("user__name", "user__email", "school_year")

    # Different fieldsets for add and change
    fieldsets: ClassVar = (
        (None, {"fields": ("user",)}),
        (
            "Student Information",
            {
                "fields": (
                    "school_year",
                    "birth_date",
                    "address",
                    "cc_number",
                    "cc_photo",
                    "calendar_iframe",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            "User Account",
            {"fields": ("email", "name", "phone_number", "password1", "password2")},
        ),
        (
            "Student Information",
            {
                "fields": (
                    "school_year",
                    "birth_date",
                    "address",
                    "cc_number",
                    "cc_photo",
                    "calendar_iframe",
                )
            },
        ),
    )

    @admin.display(
        description="Name",
        ordering="user__name",
    )
    def get_name(self, obj):
        return obj.user.name

    @admin.display(
        description="Email",
        ordering="user__email",
    )
    def get_email(self, obj):
        return obj.user.email

    def get_fieldsets(self, request, obj=None):
        """Use different fieldsets for add and change forms"""
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """Use different form for add and change pages"""
        defaults = {}
        if obj is None:
            defaults["form"] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("get_name", "get_email", "specialty", "hourly_rate")
    search_fields: ClassVar = ("user__name", "user__email", "specialty")
    fieldsets: ClassVar = (
        (None, {"fields": ("user",)}),
        (
            "Teacher Information",
            {
                "fields": (
                    "bio",
                    "specialty",
                    "education",
                    "hourly_rate",
                    "availability",
                    "address",
                    "phone_number",
                    "calendar_iframe",
                )
            },
        ),
    )

    @admin.display(
        description="Name",
        ordering="user__name",
    )
    def get_name(self, obj):
        return obj.user.name

    @admin.display(
        description="Email",
        ordering="user__email",
    )
    def get_email(self, obj):
        return obj.user.email


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("name", "description", "address", "contact_email", "phone_number", "website")
    search_fields: ClassVar = ("name", "description", "address", "contact_email", "phone_number", "website")
    fieldsets: ClassVar = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "address",
                    "contact_email",
                    "phone_number",
                    "website",
                )
            },
        ),
    )


@admin.register(SchoolMembership)
class SchoolMembershipAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("user", "school", "role", "is_active")
    search_fields: ClassVar = ("user__name", "user__email", "school__name", "role")
    fieldsets: ClassVar = ((None, {"fields": ("user", "school", "role", "is_active")}),)


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("email", "secret_key", "created_at", "is_used", "failed_attempts")
    search_fields: ClassVar = ("email", "secret_key")
    fieldsets: ClassVar = ((None, {"fields": ("email", "secret_key", "created_at", "is_used", "failed_attempts")}),)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("name", "code", "educational_system", "education_level", "created_at")
    list_filter: ClassVar = ("educational_system", "education_level", "created_at", "updated_at")
    search_fields: ClassVar = ("name", "code", "educational_system", "education_level", "description")
    fieldsets: ClassVar = (
        (
            None,
            {"fields": ("name", "code", "educational_system", "education_level", "description")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields: ClassVar = ("created_at", "updated_at")


@admin.register(TeacherCourse)
class TeacherCourseAdmin(admin.ModelAdmin):
    list_display: ClassVar = (
        "get_teacher_name",
        "get_course_name",
        "hourly_rate",
        "is_active",
        "started_teaching",
    )
    list_filter: ClassVar = (
        "is_active",
        "started_teaching",
        "course__educational_system",
        "course__education_level",
    )
    search_fields: ClassVar = ("teacher__user__name", "teacher__user__email", "course__name", "course__code")
    fieldsets: ClassVar = (
        (None, {"fields": ("teacher", "course", "hourly_rate", "is_active")}),
        ("Timestamps", {"fields": ("started_teaching",), "classes": ("collapse",)}),
    )
    readonly_fields: ClassVar = ("started_teaching",)

    @admin.display(
        description="Teacher",
        ordering="teacher__user__name",
    )
    def get_teacher_name(self, obj):
        return obj.teacher.user.name

    @admin.display(
        description="Course",
        ordering="course__name",
    )
    def get_course_name(self, obj):
        return f"{obj.course.name} ({obj.course.code})"


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    """Admin interface for ParentProfile model."""

    list_display: ClassVar = (
        "get_name",
        "get_email",
        "email_notifications_enabled",
        "sms_notifications_enabled",
        "created_at",
    )
    list_filter: ClassVar = ("email_notifications_enabled", "sms_notifications_enabled", "created_at")
    search_fields: ClassVar = ("user__name", "user__email")
    readonly_fields: ClassVar = ("created_at", "updated_at")

    fieldsets: ClassVar = (
        (None, {"fields": ("user",)}),
        (
            "Notification Settings",
            {
                "fields": (
                    "email_notifications_enabled",
                    "sms_notifications_enabled",
                    "notification_preferences",
                )
            },
        ),
        (
            "Approval Settings",
            {"fields": ("default_approval_settings",)},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(
        description="Name",
        ordering="user__name",
    )
    def get_name(self, obj):
        return obj.user.name

    @admin.display(
        description="Email",
        ordering="user__email",
    )
    def get_email(self, obj):
        return obj.user.email


@admin.register(ParentChildRelationship)
class ParentChildRelationshipAdmin(admin.ModelAdmin):
    """Admin interface for ParentChildRelationship model."""

    list_display: ClassVar = (
        "get_parent_name",
        "get_child_name",
        "relationship_type",
        "school",
        "is_active",
        "requires_purchase_approval",
        "created_at",
    )
    list_filter: ClassVar = (
        "relationship_type",
        "is_active",
        "requires_purchase_approval",
        "requires_session_approval",
        "school",
        "created_at",
    )
    search_fields: ClassVar = ("parent__name", "parent__email", "child__name", "child__email", "school__name")
    readonly_fields: ClassVar = ("created_at", "updated_at")

    fieldsets: ClassVar = (
        ("Relationship Details", {"fields": ("parent", "child", "relationship_type", "school", "is_active")}),
        (
            "Permissions & Approval Settings",
            {"fields": ("requires_purchase_approval", "requires_session_approval", "permissions")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    # Filters for easier navigation
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent", "child", "school")

    @admin.display(
        description="Parent",
        ordering="parent__name",
    )
    def get_parent_name(self, obj):
        return f"{obj.parent.name} ({obj.parent.email})"

    @admin.display(
        description="Child",
        ordering="child__name",
    )
    def get_child_name(self, obj):
        return f"{obj.child.name} ({obj.child.email})"
