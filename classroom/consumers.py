import json
import logging

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache

from .models import Channel, Message, Reaction

User = get_user_model()

# Security logging
logger = logging.getLogger("security.websocket")


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        """Handle WebSocket connection with security checks."""
        self.channel_name_param = self.scope["url_route"]["kwargs"]["channel_name"]
        self.group_name = f"chat_{self.channel_name_param}"
        self.user = self.scope.get("user")

        # If no user in scope, create an anonymous user
        if not self.user:
            from django.contrib.auth.models import AnonymousUser

            self.user = AnonymousUser()

        # Security Check 1: Authentication required
        if not self.user.is_authenticated:
            logger.warning(
                "Unauthenticated user attempted WebSocket connection to channel: %s", self.channel_name_param
            )
            self.close(code=4001)  # Unauthorized
            return

        # Security Check 2: Rate limiting
        # Skip rate limiting in test environment
        import os

        is_testing = getattr(settings, "TESTING", False) or os.getenv("DJANGO_TESTING") == "true"
        if not is_testing and not self.check_rate_limit():
            logger.warning(
                "Rate limit exceeded for user %s attempting connection to channel: %s",
                self.user.username,
                self.channel_name_param,
            )
            self.close(code=4029)  # Too Many Requests
            return

        # Security Check 3: Channel access authorization
        has_access = async_to_sync(self.user_has_channel_access)()
        if not has_access:
            logger.warning(
                "User %s attempted access to unauthorized channel: %s", self.user.username, self.channel_name_param
            )
            self.close(code=4003)  # Forbidden
            return

        # Accept the connection after all security checks pass
        self.accept()

        # Log successful connection for security monitoring
        logger.info("User %s successfully connected to channel: %s", self.user.username, self.channel_name_param)

        # Add to channel group
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)

        # Mark user as online in the channel
        async_to_sync(self.mark_user_online)()

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
        async_to_sync(self.mark_user_offline)()

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
        """Handle incoming WebSocket messages with security checks."""
        # Security Check 1: Double-check authentication on every message
        if not self.user.is_authenticated:
            logger.warning("Unauthenticated user attempted to send message to channel: %s", self.channel_name_param)
            self.close(code=4001)  # Unauthorized
            return

        # Security Check 2: Verify channel access is still valid
        if not async_to_sync(self.user_has_channel_access)():
            logger.warning(
                "User %s attempted to send message to unauthorized channel: %s",
                self.user.username,
                self.channel_name_param,
            )
            self.close(code=4003)  # Forbidden
            return

        # Security Check 3: Rate limiting for messages
        # Skip rate limiting in test environment
        if not getattr(settings, "TESTING", False) and not self.check_rate_limit(action="message"):
            logger.warning(
                "Rate limit exceeded for user %s sending message to channel: %s",
                self.user.username,
                self.channel_name_param,
            )
            self.close(code=4029)  # Too Many Requests
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning(
                "Invalid JSON received from user %s in channel: %s", self.user.username, self.channel_name_param
            )
            return

        message_type = data.get("type")

        if message_type == "message":
            # Validate message data
            if "message" not in data:
                logger.warning(
                    "Missing 'message' field from user %s in channel: %s", self.user.username, self.channel_name_param
                )
                return

            # Save message to database
            message = async_to_sync(self.save_message)(data["message"])

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
            reaction = async_to_sync(self.save_reaction)(data["message_id"], data["emoji"])

            # Only broadcast if reaction was successfully saved
            if reaction:
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
            logger.info("Channel '%s' does not exist while marking user online", self.channel_name_param)
        except Channel.MultipleObjectsReturned:
            # Handle multiple channels with same name - mark online in all that user participates in
            channels = Channel.objects.filter(name=self.channel_name_param)
            for channel in channels:
                if channel.participants.filter(id=self.user.id).exists():
                    channel.online.add(self.user)
        except Exception as e:
            logger.warning("Failed to mark user online in WebSocket channel: %s", str(e))

    @database_sync_to_async
    def mark_user_offline(self):
        """Mark user as offline in the channel."""
        try:
            channel = Channel.objects.get(name=self.channel_name_param)
            channel.online.remove(self.user)
        except Channel.DoesNotExist:
            logger.info("Channel '%s' does not exist while marking user offline", self.channel_name_param)
        except Channel.MultipleObjectsReturned:
            # Handle multiple channels with same name - mark offline in all that user participates in
            channels = Channel.objects.filter(name=self.channel_name_param)
            for channel in channels:
                if channel.participants.filter(id=self.user.id).exists():
                    channel.online.remove(self.user)
        except Exception as e:
            logger.warning("Failed to mark user offline in WebSocket channel: %s", str(e))

    @database_sync_to_async
    def save_message(self, content):
        """Save message to database."""
        try:
            channel = Channel.objects.get(name=self.channel_name_param)
        except Channel.MultipleObjectsReturned:
            # Use the first channel the user participates in
            channels = Channel.objects.filter(name=self.channel_name_param)
            channel = None
            for ch in channels:
                if ch.participants.filter(id=self.user.id).exists():
                    channel = ch
                    break
            if not channel:
                raise Channel.DoesNotExist(f"User has no access to channel {self.channel_name_param}")

        return Message.objects.create(
            channel=channel,
            sender=self.user,
            content=content,
        )

    @database_sync_to_async
    def user_has_channel_access(self):
        """Check if user has access to the channel."""
        try:
            channel = Channel.objects.get(name=self.channel_name_param)
            return channel.participants.filter(id=self.user.id).exists()
        except Channel.DoesNotExist:
            logger.warning(
                "User %s attempted to access non-existent channel: %s", self.user.username, self.channel_name_param
            )
            return False
        except Channel.MultipleObjectsReturned:
            # Handle multiple channels with same name - this can happen in test environments
            logger.warning(
                "Multiple channels found with name %s for user %s", self.channel_name_param, self.user.username
            )
            # Check if user has access to any channel with this name
            channels = Channel.objects.filter(name=self.channel_name_param)
            return any(channel.participants.filter(id=self.user.id).exists() for channel in channels)
        except Exception as e:
            logger.error(
                "Error checking channel access for user %s, channel %s: %s",
                self.user.username,
                self.channel_name_param,
                str(e),
            )
            return False

    def check_rate_limit(self, action="connection"):
        """Check if user has exceeded rate limits."""
        if not self.user or not self.user.is_authenticated:
            return False

        # Rate limiting configuration
        limits = {
            "connection": {"count": 10, "window": 60},  # 10 connections per minute
            "message": {"count": 30, "window": 60},  # 30 messages per minute
        }

        limit_config = limits.get(action, limits["connection"])
        cache_key = f"websocket_rate_limit_{action}_{self.user.id}"

        try:
            # Get current count from cache
            current_count = cache.get(cache_key, 0)

            if current_count >= limit_config["count"]:
                return False

            # Increment counter with expiration
            cache.set(cache_key, current_count + 1, limit_config["window"])
            return True

        except Exception as e:
            logger.error("Error checking rate limit for user %s, action %s: %s", self.user.username, action, str(e))
            # In case of cache error, allow the request but log it
            return True

    @database_sync_to_async
    def save_reaction(self, message_id, emoji):
        """Save reaction to database."""
        try:
            message = Message.objects.get(id=message_id)
            return Reaction.objects.create(
                message=message,
                user=self.user,
                emoji=emoji,
            )
        except Message.DoesNotExist:
            # Log and return None if message doesn't exist
            logger.warning("User %s attempted to react to nonexistent message: %s", self.user.username, message_id)
            return None
