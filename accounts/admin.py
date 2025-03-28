from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = CustomUser
    list_display = ("email", "name", "is_staff", "is_admin")
    list_filter = ("is_staff", "is_admin")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name", "phone_number")}),
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
                "fields": ("email", "name", "phone_number", "password1", "password2"),
            },
        ),
    )
    search_fields = ("email", "name")
    ordering = ("email",)
