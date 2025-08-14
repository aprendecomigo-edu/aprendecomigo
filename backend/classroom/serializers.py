from typing import ClassVar

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Attachment, Channel, Message, Reaction

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields: ClassVar = ["id", "username", "email", "first_name", "last_name"]


class ReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Reaction
        fields: ClassVar = ["id", "user", "emoji", "created_at"]
        read_only_fields: ClassVar = ["user", "created_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields: ClassVar = ["id", "file", "filename", "file_type", "size", "uploaded_at"]
        read_only_fields: ClassVar = ["filename", "file_type", "size", "uploaded_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reactions = ReactionSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    file = serializers.FileField(required=False)

    class Meta:
        model = Message
        fields: ClassVar = [
            "id",
            "channel",
            "sender",
            "content",
            "timestamp",
            "file",
            "reactions",
            "attachments",
        ]
        read_only_fields: ClassVar = ["sender", "timestamp"]


class ChannelSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    online = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Channel
        fields: ClassVar = [
            "id",
            "name",
            "is_direct",
            "participants",
            "online",
            "created_at",
            "updated_at",
            "last_message",
            "participant_ids",
        ]
        read_only_fields: ClassVar = ["created_at", "updated_at", "online"]

    def get_last_message(self, obj):
        last_message = obj.messages.order_by("-timestamp").first()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def validate(self, data):
        if data.get("is_direct", False):
            participant_ids = data.get("participant_ids", [])
            if len(participant_ids) != 1:
                raise serializers.ValidationError("Direct messages must have exactly one other participant")
        return data

    def create(self, validated_data):
        participant_ids = validated_data.pop("participant_ids", [])
        current_user = validated_data.pop("current_user", None)
        is_direct = validated_data.get("is_direct", False)

        # Check for duplicate DM before creating
        if is_direct and participant_ids and current_user:
            from django.contrib.auth import get_user_model

            User = get_user_model()

            target_user_id = participant_ids[0]
            target_user = User.objects.get(id=target_user_id)

            # Check if a DM already exists between current user and target user
            # Simple approach: get all DMs and check participants manually
            existing_dms = Channel.objects.filter(is_direct=True)
            existing_dm = None

            for dm in existing_dms:
                participants = set(dm.participants.all())
                expected_participants = {current_user, target_user}
                if participants == expected_participants:
                    existing_dm = dm
                    break

            if existing_dm:
                # Return the existing DM instead of creating a new one
                return existing_dm

        # Create new channel if not a duplicate DM
        channel = Channel.objects.create(**validated_data)

        # Add participants including the current user for DMs
        if participant_ids:
            if is_direct and current_user:
                # For DMs, add both current user and target user
                channel.participants.set([current_user.id, *participant_ids])
            else:
                # For group channels, just add the specified participants
                channel.participants.set(participant_ids)

        return channel
