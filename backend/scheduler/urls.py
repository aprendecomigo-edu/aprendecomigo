from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClassReminderViewSet,
    ClassScheduleViewSet,
    RecurringClassScheduleViewSet,
    ReminderPreferenceViewSet,
    ReminderQueueViewSet,
    TeacherAvailabilityViewSet,
    TeacherUnavailabilityViewSet,
    UserRemindersViewSet,
)

# Create a router and register the viewsets
router = DefaultRouter()
router.register(r"availability", TeacherAvailabilityViewSet, basename="teacher-availability")
router.register(r"unavailability", TeacherUnavailabilityViewSet, basename="teacher-unavailability")
router.register(r"schedules", ClassScheduleViewSet, basename="class-schedules")
router.register(r"recurring-classes", RecurringClassScheduleViewSet, basename="recurring-classes")
router.register(r"reminder-preferences", ReminderPreferenceViewSet, basename="reminder-preferences")
router.register(r"class-reminders", ClassReminderViewSet, basename="class-reminders")
router.register(r"reminders", UserRemindersViewSet, basename="reminders")
router.register(r"reminder-queue", ReminderQueueViewSet, basename="reminder-queue-status")

urlpatterns = [
    path("", include(router.urls)),
]
