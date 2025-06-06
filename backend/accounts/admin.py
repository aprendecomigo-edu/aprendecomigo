from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Course,
    CustomUser,
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


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "secret_key", "created_at", "is_used", "failed_attempts")
    search_fields = ("email", "secret_key")
    fieldsets = (
        (None, {"fields": ("email", "secret_key", "created_at", "is_used", "failed_attempts")}),
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
