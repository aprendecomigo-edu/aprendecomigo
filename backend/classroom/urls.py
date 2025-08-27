from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .chat_views import (
    ChatUserSearchView,
    ChatChannelsView, 
    ChatMessagesView,
    chat_school_users
)

router = DefaultRouter()
router.register(r"channels", views.ChannelViewSet, basename="channel")
router.register(r"messages", views.MessageViewSet, basename="message")
router.register(r"users", views.UserSearchViewSet, basename="user")
router.register(r"session-booking", views.SessionBookingViewSet, basename="session-booking")

# Django views for chat (replacing DRF for chat functionality)
chat_patterns = [
    path("chat/users/search/", ChatUserSearchView.as_view(), name="chat_user_search"),
    path("chat/users/school/", chat_school_users, name="chat_school_users"),
    path("chat/channels/", ChatChannelsView.as_view(), name="chat_channels"),
    path("chat/channels/<int:channel_id>/messages/", ChatMessagesView.as_view(), name="chat_messages"),
]

urlpatterns = [
    path("", include(router.urls)),
] + chat_patterns
