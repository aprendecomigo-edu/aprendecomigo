from django.contrib import admin

from .models import Attachment, Channel, Message, Reaction


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "is_direct", "created_at", "updated_at")
    list_filter = ("is_direct",)
    search_fields = ("name",)
    filter_horizontal = ("participants", "online")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "channel", "content", "timestamp")
    list_filter = ("channel", "sender")
    search_fields = ("content", "sender__username")
    date_hierarchy = "timestamp"


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "emoji", "created_at")
    list_filter = ("emoji",)
    search_fields = ("user__username", "message__content")
    date_hierarchy = "created_at"


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("filename", "file_type", "size", "uploaded_at")
    list_filter = ("file_type",)
    search_fields = ("filename",)
    date_hierarchy = "uploaded_at"
