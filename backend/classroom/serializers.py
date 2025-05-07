from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Attachment, Channel, Message, Reaction

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class ReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Reaction
        fields = ["id", "user", "emoji", "created_at"]
        read_only_fields = ["user", "created_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "file", "filename", "file_type", "size", "uploaded_at"]
        read_only_fields = ["filename", "file_type", "size", "uploaded_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reactions = ReactionSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    file = serializers.FileField(required=False)

    class Meta:
        model = Message
        fields = [
            "id",
            "channel",
            "sender",
            "content",
            "timestamp",
            "file",
            "reactions",
            "attachments",
        ]
        read_only_fields = ["sender", "timestamp"]


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
        fields = [
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
        read_only_fields = ["created_at", "updated_at", "online"]

    def get_last_message(self, obj):
        last_message = obj.messages.order_by("-timestamp").first()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def validate(self, data):
        if data.get("is_direct", False):
            participant_ids = data.get("participant_ids", [])
            if len(participant_ids) != 2:
                raise serializers.ValidationError(
                    "Direct messages must have exactly two participants"
                )
        return data

    def create(self, validated_data):
        participant_ids = validated_data.pop("participant_ids", [])
        channel = Channel.objects.create(**validated_data)

        # Add participants
        if participant_ids:
            channel.participants.set(participant_ids)

        return channel
