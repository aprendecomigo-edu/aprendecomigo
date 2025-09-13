"""
Classroom app URLs - Chat functionality only (no DRF).
"""

from django.urls import path

from .views import (
    ChatChannelsView,
    ChatMessagesView,
    ChatUserSearchView,
    ChatView,
    MessageReactionsView,
    chat_school_users,
)

# Pure Django views for chat functionality and classroom management
urlpatterns = [
    # Chat endpoints
    path("chat/", ChatView.as_view(), name="chat"),
    path("chat/users/search/", ChatUserSearchView.as_view(), name="chat_user_search"),
    path("chat/users/school/", chat_school_users, name="chat_school_users"),
    path("chat/channels/", ChatChannelsView.as_view(), name="chat_channels"),
    path("chat/channels/<int:channel_id>/messages/", ChatMessagesView.as_view(), name="chat_messages"),
    path("chat/messages/<int:message_id>/reactions/", MessageReactionsView.as_view(), name="message_reactions"),
]
