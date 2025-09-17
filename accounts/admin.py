from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Course,
    CustomUser,
    GuardianProfile,
    GuardianStudentRelationship,
    School,
    SchoolMembership,
    StudentProfile,
    TeacherCourse,
    TeacherProfile,
    VerificationToken,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active")
    fieldsets = (
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
    search_fields = ("email", "name")
    ordering = ("email",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("get_name", "get_email", "school_year", "birth_date")
    list_filter = ("school_year",)
    search_fields = ("user__name", "user__email", "school_year")

    # Different fieldsets for add and change
    fieldsets = (
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
    list_display = ("get_name", "get_email", "specialty", "hourly_rate")
    search_fields = ("user__name", "user__email", "specialty")
    fieldsets = (
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
    list_display = ("name", "description", "address", "contact_email", "phone_number", "website")
    search_fields = ("name", "description", "address", "contact_email", "phone_number", "website")
    fieldsets = (
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
    list_display = ("user", "school", "role", "is_active")
    search_fields = ("user__name", "user__email", "school__name", "role")
    fieldsets = ((None, {"fields": ("user", "school", "role", "is_active")}),)


@admin.register(VerificationToken)
class VerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token_type", "expires_at", "used_at", "attempts", "created_at")
    list_filter = ("token_type", "used_at", "expires_at", "created_at")
    search_fields = ("user__email", "user__name", "token_type")
    readonly_fields = ("created_at", "used_at")
    fieldsets = (
        (None, {"fields": ("user", "token_type", "token_value")}),
        ("Expiry & Usage", {"fields": ("expires_at", "used_at", "attempts", "max_attempts")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "educational_system", "education_level", "created_at")
    list_filter = ("educational_system", "education_level", "created_at", "updated_at")
    search_fields = ("name", "code", "educational_system", "education_level", "description")
    fieldsets = (
        (
            None,
            {"fields": ("name", "code", "educational_system", "education_level", "description")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(TeacherCourse)
class TeacherCourseAdmin(admin.ModelAdmin):
    list_display = (
        "get_teacher_name",
        "get_course_name",
        "hourly_rate",
        "is_active",
        "started_teaching",
    )
    list_filter = (
        "is_active",
        "started_teaching",
        "course__educational_system",
        "course__education_level",
    )
    search_fields = ("teacher__user__name", "teacher__user__email", "course__name", "course__code")
    fieldsets = (
        (None, {"fields": ("teacher", "course", "hourly_rate", "is_active")}),
        ("Timestamps", {"fields": ("started_teaching",), "classes": ("collapse",)}),
    )
    readonly_fields = ("started_teaching",)

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


@admin.register(GuardianProfile)
class GuardianProfileAdmin(admin.ModelAdmin):
    """Admin interface for GuardianProfile model."""

    list_display = (
        "get_name",
        "get_email",
        "email_notifications_enabled",
        "sms_notifications_enabled",
        "created_at",
    )
    list_filter = ("email_notifications_enabled", "sms_notifications_enabled", "created_at")
    search_fields = ("user__name", "user__email")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
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


@admin.register(GuardianStudentRelationship)
class GuardianStudentRelationshipAdmin(admin.ModelAdmin):
    """Admin interface for GuardianStudentRelationship model."""

    list_display = (
        "get_guardian_name",
        "get_student_name",
        "school",
        "is_active",
        "requires_purchase_approval",
        "created_at",
    )
    list_filter = (
        "is_active",
        "requires_purchase_approval",
        "requires_session_approval",
        "school",
        "created_at",
    )
    search_fields = ("guardian__name", "guardian__email", "student__name", "student__email", "school__name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Relationship Details", {"fields": ("guardian", "student", "school", "is_active")}),
        (
            "Permissions & Approval Settings",
            {"fields": ("requires_purchase_approval", "requires_session_approval")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    # Filters for easier navigation
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("guardian", "student", "school")

    @admin.display(
        description="Guardian",
        ordering="guardian__name",
    )
    def get_guardian_name(self, obj):
        return f"{obj.guardian.name} ({obj.guardian.email})"

    @admin.display(
        description="Student",
        ordering="student__name",
    )
    def get_student_name(self, obj):
        return f"{obj.student.name} ({obj.student.email})"
