from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TaskViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")

app_name = "tasks"

urlpatterns = [
    path("", include(router.urls)),
]
