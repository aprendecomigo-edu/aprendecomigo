import json

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth import get_user_model

from .models import Channel, Message, Reaction

User = get_user_model()


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        """Handle WebSocket connection."""
        self.channel_name_param = self.scope["url_route"]["kwargs"]["channel_name"]
        self.group_name = f"chat_{self.channel_name_param}"
        self.user = self.scope["user"]

        # Accept the connection
        self.accept()

        # Add to channel group
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)

        # Mark user as online in the channel
        self.mark_user_online()

        # Notify others about the new online user
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                "type": "user_status",
                "user": self.user.username,
                "status": "online",
            },
        )

    def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Remove from channel group
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

        # Mark user as offline
        self.mark_user_offline()

        # Notify others about the offline user
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                "type": "user_status",
                "user": self.user.username,
                "status": "offline",
            },
        )

    def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        data = json.loads(text_data)
        message_type = data.get("type")

        if message_type == "message":
            # Save message to database
            message = self.save_message(data["message"])

            # Broadcast to group
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "chat_message",
                    "message": {
                        "id": message.id,
                        "content": message.content,
                        "sender": message.sender.username,
                        "timestamp": message.timestamp.isoformat(),
                        "file": message.file.url if message.file else None,
                    },
                },
            )

        elif message_type == "reaction":
            # Save reaction to database
            reaction = self.save_reaction(data["message_id"], data["emoji"])

            # Broadcast to group
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "reaction_added",
                    "reaction": {
                        "id": reaction.id,
                        "emoji": reaction.emoji,
                        "user": reaction.user.username,
                        "message_id": reaction.message.id,
                        "created_at": reaction.created_at.isoformat(),
                    },
                },
            )

    def chat_message(self, event):
        """Send chat message to WebSocket."""
        self.send(text_data=json.dumps(event))

    def reaction_added(self, event):
        """Send reaction to WebSocket."""
        self.send(text_data=json.dumps(event))

    def user_status(self, event):
        """Send user status update to WebSocket."""
        self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def mark_user_online(self):
        """Mark user as online in the channel."""
        try:
            channel = Channel.objects.get(name=self.channel_name_param)
            channel.online.add(self.user)
        except Channel.DoesNotExist:
            pass

    @database_sync_to_async
    def mark_user_offline(self):
        """Mark user as offline in the channel."""
        try:
            channel = Channel.objects.get(name=self.channel_name_param)
            channel.online.remove(self.user)
        except Channel.DoesNotExist:
            pass

    @database_sync_to_async
    def save_message(self, content):
        """Save message to database."""
        channel = Channel.objects.get(name=self.channel_name_param)
        return Message.objects.create(
            channel=channel,
            sender=self.user,
            content=content,
        )

    @database_sync_to_async
    def save_reaction(self, message_id, emoji):
        """Save reaction to database."""
        message = Message.objects.get(id=message_id)
        return Reaction.objects.create(
            message=message,
            user=self.user,
            emoji=emoji,
        )
