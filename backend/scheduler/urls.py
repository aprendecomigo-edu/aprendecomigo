from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClassScheduleViewSet,
    RecurringClassScheduleViewSet,
    TeacherAvailabilityViewSet,
    TeacherUnavailabilityViewSet,
)

# Create a router and register the viewsets
router = DefaultRouter()
router.register(r"availability", TeacherAvailabilityViewSet, basename="teacher-availability")
router.register(r"unavailability", TeacherUnavailabilityViewSet, basename="teacher-unavailability")
router.register(r"schedules", ClassScheduleViewSet, basename="class-schedules")
router.register(r"recurring", RecurringClassScheduleViewSet, basename="recurring-schedules")

urlpatterns = [
    path("api/", include(router.urls)),
]
