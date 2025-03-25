from django.contrib import admin
from .models import Subject, ClassType, ClassSession


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')


@admin.register(ClassType)
class ClassTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'group_class', 'default_duration')
    list_filter = ('group_class',)
    search_fields = ('name', 'description')


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'subject', 'class_type', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'subject', 'class_type', 'teacher')
    search_fields = ('title', 'notes')
    date_hierarchy = 'start_time'
    filter_horizontal = ('students',)
