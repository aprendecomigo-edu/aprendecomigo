from typing import ClassVar

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Channel(models.Model):
    """A chat channel that can be either a group chat or direct message."""

    name = models.CharField(max_length=255, blank=True)
    is_direct = models.BooleanField(default=False)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="channels",
        help_text="Users who are members of this channel",
    )
    online = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="online_channels",
        blank=True,
        help_text="Users who are currently connected to this channel",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar = ["-updated_at"]

    def __str__(self):
        if self.is_direct:
            return f"DM: {', '.join(user.username for user in self.participants.all()[:2])}"
        return self.name

    def get_direct_channel_name(self, user1, user2):
        """Generate a consistent name for direct message channels."""
        usernames = sorted([user1.username, user2.username])
        return f"DM_{usernames[0]}_{usernames[1]}"


class Message(models.Model):
    """A message in a channel."""

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    file = models.FileField(
        upload_to="chat_attachments/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx", "jpg", "jpeg", "png", "gif"])],
    )

    class Meta:
        ordering: ClassVar = ["timestamp"]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class Reaction(models.Model):
    """A reaction (emoji) to a message."""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reactions")
    emoji = models.CharField(max_length=10)  # Most emojis are 2-4 bytes
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together: ClassVar = ["message", "user", "emoji"]
        ordering: ClassVar = ["created_at"]

    def __str__(self):
        return f"{self.user.username} reacted with {self.emoji} to message {self.message.id}"


class Attachment(models.Model):
    """A separate model for large files or images."""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(
        upload_to="chat_attachments/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx", "jpg", "jpeg", "png", "gif"])],
    )
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    size = models.PositiveIntegerField()  # Size in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar = ["-uploaded_at"]

    def __str__(self):
        return f"{self.filename} ({self.file_type})"
