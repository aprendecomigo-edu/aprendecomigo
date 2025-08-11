from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"channels", views.ChannelViewSet, basename="channel")
router.register(r"messages", views.MessageViewSet, basename="message")
router.register(r"users", views.UserSearchViewSet, basename="user")
router.register(r"session-booking", views.SessionBookingViewSet, basename="session-booking")

urlpatterns = [
    path("", include(router.urls)),
]
