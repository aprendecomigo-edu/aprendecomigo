from django.urls import path

from .views import (
    # Template-based views (HTMX/PWA)
    ClassScheduleTemplateView,
    TeacherAvailabilityTemplateView,
    # Action views
    class_schedule_cancel,
    class_schedule_complete,
    class_schedule_confirm,
    class_schedule_no_show,
)

app_name = "scheduler"

# PWA URL patterns - all API endpoints removed
urlpatterns = [
    # === MAIN PWA VIEWS (HTMX/Server-side rendering) ===
    # Note: Calendar view is now accessed via main URLs at /calendar/
    # Class scheduling - main interface
    path("", ClassScheduleTemplateView.as_view(), name="schedule-home"),
    # Teacher availability - main interface
    path("availability/", TeacherAvailabilityTemplateView.as_view(), name="availability-home"),
    # Class schedule actions - HTMX endpoints
    path("schedules/<int:schedule_id>/cancel/", class_schedule_cancel, name="schedule-cancel"),
    path("schedules/<int:schedule_id>/confirm/", class_schedule_confirm, name="schedule-confirm"),
    path("schedules/<int:schedule_id>/complete/", class_schedule_complete, name="schedule-complete"),
    path("schedules/<int:schedule_id>/no-show/", class_schedule_no_show, name="schedule-no-show"),
]

# All ViewSets have been successfully migrated to Django views!
