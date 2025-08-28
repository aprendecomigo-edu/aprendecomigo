from django.urls import path

from .views import (
    ClassReminderView,
    ClassScheduleView,
    RecurringClassScheduleView,
    ReminderPreferenceView,
    ReminderQueueView,
    TeacherAvailabilityView,
    TeacherUnavailabilityView,
    UserRemindersView,
    class_schedule_cancel,
    class_schedule_complete,
    class_schedule_confirm,
    class_schedule_no_show,
)

app_name = "scheduler"

# Django URL patterns for scheduler views (migrated from DRF)
urlpatterns = [
    # Teacher availability management
    path("availability/", TeacherAvailabilityView.as_view(), name="availability-list"),
    path("availability/<int:availability_id>/", TeacherAvailabilityView.as_view(), name="availability-detail"),

    # Teacher unavailability management
    path("unavailability/", TeacherUnavailabilityView.as_view(), name="unavailability-list"),
    path("unavailability/<int:unavailability_id>/", TeacherUnavailabilityView.as_view(), name="unavailability-detail"),

    # Reminder preferences
    path("reminder-preferences/", ReminderPreferenceView.as_view(), name="reminder-preferences-list"),
    path("reminder-preferences/<int:preference_id>/", ReminderPreferenceView.as_view(), name="reminder-preferences-detail"),

    # Class reminders
    path("class-reminders/", ClassReminderView.as_view(), name="class-reminders-list"),
    path("class-reminders/<int:reminder_id>/", ClassReminderView.as_view(), name="class-reminders-detail"),

    # User reminders
    path("reminders/", UserRemindersView.as_view(), name="user-reminders"),
    
    # === NEWLY MIGRATED VIEWS (Phase 1-3) ===
    
    # Reminder queue management (admin only) - Phase 1
    path("reminder-queue/", ReminderQueueView.as_view(), name="reminder-queue"),
    
    # Recurring class schedules - Phase 2
    path("recurring-classes/", RecurringClassScheduleView.as_view(), name="recurring-classes-list"),
    path("recurring-classes/<int:schedule_id>/", RecurringClassScheduleView.as_view(), name="recurring-classes-detail"),
    
    # Class schedules (CRITICAL - used by calendar) - Phase 3
    path("schedules/", ClassScheduleView.as_view(), name="schedules-list"),
    path("schedules/<int:schedule_id>/", ClassScheduleView.as_view(), name="schedules-detail"),
    
    # Class schedule actions - Phase 3
    path("schedules/<int:schedule_id>/cancel/", class_schedule_cancel, name="schedule-cancel"),
    path("schedules/<int:schedule_id>/confirm/", class_schedule_confirm, name="schedule-confirm"),
    path("schedules/<int:schedule_id>/complete/", class_schedule_complete, name="schedule-complete"),
    path("schedules/<int:schedule_id>/no-show/", class_schedule_no_show, name="schedule-no-show"),
]

# All ViewSets have been successfully migrated to Django views!
