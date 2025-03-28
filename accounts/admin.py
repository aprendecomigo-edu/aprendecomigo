from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, StudentCreationForm
from .models import CustomUser, Student


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = CustomUser
    list_display = ("email", "name", "user_type", "is_staff", "is_admin")
    list_filter = ("user_type", "is_staff", "is_admin")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name", "phone_number")}),
        ("Type", {"fields": ("user_type",)}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "is_admin")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "phone_number", "user_type", "password1", "password2"),
            },
        ),
    )
    search_fields = ("email", "name")
    ordering = ("email",)


class StudentAdmin(admin.ModelAdmin):
    form = StudentCreationForm
    add_form = StudentCreationForm
    list_display = ("get_name", "get_email", "school_year", "birth_date")
    list_filter = ("school_year",)
    search_fields = ("user__name", "user__email", "school_year")
    
    # Different fieldsets for add and change
    fieldsets = (
        (None, {"fields": ("user",)}),
        ("Student Information", {"fields": ("school_year", "birth_date", "address", "cc_number", "cc_photo", "calendar_url")}),
    )
    add_fieldsets = (
        ("User Account", {"fields": ("email", "name", "phone_number", "password1", "password2")}),
        ("Student Information", {"fields": ("school_year", "birth_date", "address", "cc_number", "cc_photo", "calendar_url")}),
    )
    
    def get_name(self, obj):
        return obj.user.name
    get_name.short_description = "Name"
    get_name.admin_order_field = "user__name"
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"
    
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


admin.site.register(Student, StudentAdmin)
