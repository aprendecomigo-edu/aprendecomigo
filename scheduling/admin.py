from django.contrib import admin

from .models import ClassSession, ClassType

@admin.register(ClassType)
class ClassTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "hourly_rate")
    search_fields = ("name",)


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "teacher",
        "class_type",
        "start_time",
        "end_time",
        "attended",
    )
    list_filter = ("attended", "class_type", "teacher")
    search_fields = ("title",)
    filter_horizontal = ("students",)
    date_hierarchy = "start_time"
