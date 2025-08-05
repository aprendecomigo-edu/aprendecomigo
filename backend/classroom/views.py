from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Channel, Message, Reaction
from .serializers import (
    ChannelSerializer,
    MessageSerializer,
    ReactionSerializer,
    UserSerializer,
)

User = get_user_model()


class ChannelViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return channels where the user is a participant."""
        return Channel.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        """Create a channel and add the current user as a participant."""
        # Pass the current user to the serializer for duplicate DM checking
        channel = serializer.save(current_user=self.request.user)

        # Only add current user if they're not already a participant
        # (DMs add the current user automatically, group channels need it added)
        if not channel.participants.filter(id=self.request.user.id).exists():
            channel.participants.add(self.request.user)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        """List messages in a channel with pagination."""
        channel = self.get_object()
        messages = channel.messages.all().order_by("-timestamp")
        page = self.paginate_queryset(messages)

        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """Create a new message in the channel."""
        channel = self.get_object()

        # Check if user is a participant
        if not channel.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You must be a participant to send messages"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = MessageSerializer(data=request.data)

        if serializer.is_valid():
            message = serializer.save(channel=channel, sender=request.user)

            # Broadcast to WebSocket (skip during tests)
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    # Create a safe group name for WebSocket (use channel ID instead of name)
                    safe_group_name = f"chat_{channel.id}"
                    async_to_sync(channel_layer.group_send)(
                        safe_group_name,
                        {"type": "chat_message", "message": MessageSerializer(message).data},
                    )
            except Exception:
                # Ignore WebSocket errors during tests
                pass

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return messages from channels where the user is a participant."""
        return Message.objects.filter(channel__participants=self.request.user).order_by(
            "-timestamp"
        )

    @action(detail=True, methods=["get", "post", "delete"])
    def reactions(self, request, pk=None):
        """Handle reactions for a message - list, add, or remove."""
        message = self.get_object()
        
        if request.method == "GET":
            # List reactions for a message
            reactions = message.reactions.all()
            serializer = ReactionSerializer(reactions, many=True)
            return Response(serializer.data)
            
        elif request.method == "POST":
            # Add a reaction to a message
            serializer = ReactionSerializer(data=request.data)
            if serializer.is_valid():
                reaction = serializer.save(message=message, user=request.user)

                # Broadcast to WebSocket (skip during tests)
                try:
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        # Create a safe group name for WebSocket (use channel ID instead of name)
                        safe_group_name = f"chat_{message.channel.id}"
                        async_to_sync(channel_layer.group_send)(
                            safe_group_name,
                            {"type": "reaction_added", "reaction": ReactionSerializer(reaction).data},
                        )
                except Exception:
                    # Ignore WebSocket errors during tests
                    pass

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == "DELETE":
            # Remove a reaction from a message
            emoji = request.data.get("emoji")
            
            try:
                reaction = message.reactions.get(user=request.user, emoji=emoji)
                reaction.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Reaction.DoesNotExist:
                return Response({"error": "Reaction not found"}, status=status.HTTP_404_NOT_FOUND)


class UserSearchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Search users by username, first name, or last name."""
        query = self.request.query_params.get("search", "")
        if not query:
            return User.objects.none()

        return User.objects.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        ).exclude(id=self.request.user.id)
