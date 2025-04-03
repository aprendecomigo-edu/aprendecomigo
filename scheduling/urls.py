from django.urls import path

from . import views

urlpatterns = [
    # Class Type Management
    path("class-types/", views.manage_class_types, name="manage_class_types"),
    path(
        "class-types/<int:class_type_id>/edit/",
        views.edit_class_type,
        name="edit_class_type",
    ),
    path(
        "class-types/<int:class_type_id>/delete/",
        views.delete_class_type,
        name="delete_class_type",
    ),
    # Class Sessions
    path("sessions/", views.view_sessions, name="view_sessions"),
    path("sessions/<int:session_id>/edit/", views.edit_session, name="edit_session"),
    # Calendar Sync
    path("sync-calendar/", views.calendar_sync, name="calendar_sync"),
    # API Endpoints (for HTMX)
    path("api/sessions/filter/", views.filter_sessions, name="filter_sessions"),
    path(
        "api/student/upcoming-classes/", views.upcoming_classes, name="upcoming_classes"
    ),
    path("api/teacher/today-schedule/", views.today_schedule, name="today_schedule"),
]
