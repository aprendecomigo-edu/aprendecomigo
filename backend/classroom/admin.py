from typing import ClassVar

from django.contrib import admin

from .models import Attachment, Channel, Message, Reaction


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("name", "is_direct", "created_at", "updated_at")
    list_filter: ClassVar = ("is_direct",)
    search_fields: ClassVar = ("name",)
    filter_horizontal = ("participants", "online")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("sender", "channel", "content", "timestamp")
    list_filter: ClassVar = ("channel", "sender")
    search_fields: ClassVar = ("content", "sender__username")
    date_hierarchy: ClassVar = "timestamp"


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("user", "message", "emoji", "created_at")
    list_filter: ClassVar = ("emoji",)
    search_fields: ClassVar = ("user__username", "message__content")
    date_hierarchy: ClassVar = "created_at"


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("filename", "file_type", "size", "uploaded_at")
    list_filter: ClassVar = ("file_type",)
    search_fields: ClassVar = ("filename",)
    date_hierarchy: ClassVar = "uploaded_at"
