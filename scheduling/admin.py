from django.contrib import admin

from .models import ClassSession, ClassType, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "description")


@admin.register(ClassType)
class ClassTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "hourly_rate")
    search_fields = ("name",)


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "teacher",
        "subject",
        "class_type",
        "start_time",
        "end_time",
        "attended",
    )
    list_filter = ("attended", "subject", "class_type", "teacher")
    search_fields = ("title",)
    filter_horizontal = ("students",)
    date_hierarchy = "start_time"
