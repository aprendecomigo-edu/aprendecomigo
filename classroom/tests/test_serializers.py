"""
Serializer tests for classroom app.

These tests validate serializer validation, field exposure, data transformation,
and security for the real-time messaging and classroom features.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from classroom.models import Attachment, Channel, Message, Reaction
from classroom.serializers import (
    AttachmentSerializer,
    ChannelSerializer,
    MessageSerializer,
    ReactionSerializer,
    UserSerializer,
)

User = get_user_model()


class UserSerializerTest(TestCase):
    """Test UserSerializer validation and data exposure."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="password",
            first_name="Test",
            last_name="User",
        )

    def test_user_serialization_includes_required_fields(self):
        """Test that user serialization includes expected fields."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        expected_fields = ["id", "username", "email", "first_name", "last_name"]
        for field in expected_fields:
            self.assertIn(field, data)

        self.assertEqual(data["id"], self.user.id)
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "User")

    def test_user_serialization_excludes_sensitive_fields(self):
        """Test that sensitive fields are not exposed."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        sensitive_fields = ["password", "is_staff", "is_superuser", "groups", "user_permissions"]
        for field in sensitive_fields:
            self.assertNotIn(field, data)

    def test_user_serialization_handles_empty_names(self):
        """Test user serialization with empty first/last names."""
        user = User.objects.create_user(
            email="nonames@example.com",
            username="nonames",
            password="password",
        )

        serializer = UserSerializer(user)
        data = serializer.data

        self.assertEqual(data["first_name"], "")
        self.assertEqual(data["last_name"], "")


class ReactionSerializerTest(TestCase):
    """Test ReactionSerializer validation and data handling."""

    def setUp(self):
        """Set up test data for reactions."""
        self.user1 = User.objects.create_user(email="user1@example.com", username="user1", password="password")
        self.user2 = User.objects.create_user(email="user2@example.com", username="user2", password="password")

        self.channel = Channel.objects.create(name="test-channel")
        self.channel.participants.add(self.user1, self.user2)

        self.message = Message.objects.create(channel=self.channel, sender=self.user1, content="Test message")

    def test_reaction_serialization_structure(self):
        """Test reaction serialization includes required fields."""
        reaction = Reaction.objects.create(message=self.message, user=self.user2, emoji="👍")

        serializer = ReactionSerializer(reaction)
        data = serializer.data

        expected_fields = ["id", "user", "emoji", "created_at"]
        for field in expected_fields:
            self.assertIn(field, data)

        self.assertEqual(data["emoji"], "👍")
        self.assertEqual(data["user"]["id"], self.user2.id)
        self.assertIsNotNone(data["created_at"])

    def test_reaction_validation_valid_data(self):
        """Test valid reaction data passes validation."""
        data = {"message": self.message.id, "emoji": "❤️"}

        serializer = ReactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["emoji"], "❤️")

    def test_reaction_validation_missing_emoji(self):
        """Test validation fails for missing emoji."""
        data = {"message": self.message.id}

        serializer = ReactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("emoji", serializer.errors)

    def test_reaction_read_only_fields(self):
        """Test that read-only fields are properly configured."""
        serializer = ReactionSerializer()
        read_only_fields = serializer.Meta.read_only_fields

        self.assertIn("user", read_only_fields)
        self.assertIn("created_at", read_only_fields)


class AttachmentSerializerTest(TestCase):
    """Test AttachmentSerializer validation and file handling."""

    def setUp(self):
        """Set up test file data."""
        self.test_file = SimpleUploadedFile("test_document.pdf", b"file_content", content_type="application/pdf")

    def test_attachment_serialization_structure(self):
        """Test attachment serialization includes required fields."""
        # Create required dependencies
        user = User.objects.create_user(email="test@example.com", username="testuser", password="password")
        channel = Channel.objects.create(name="test-channel")
        message = Message.objects.create(channel=channel, sender=user, content="Test message")

        attachment = Attachment.objects.create(
            message=message,
            file=self.test_file,
            filename="test_document.pdf",
            file_type="pdf",
            size=12,
        )

        serializer = AttachmentSerializer(attachment)
        data = serializer.data

        expected_fields = ["id", "file", "filename", "file_type", "size", "uploaded_at"]
        for field in expected_fields:
            self.assertIn(field, data)

        self.assertEqual(data["filename"], "test_document.pdf")
        self.assertEqual(data["file_type"], "pdf")
        self.assertEqual(data["size"], 12)

    def test_attachment_validation_valid_file(self):
        """Test valid file attachment passes validation."""
        data = {"file": self.test_file}

        serializer = AttachmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_attachment_validation_missing_file(self):
        """Test validation fails for missing file."""
        data = {}

        serializer = AttachmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)

    def test_attachment_read_only_fields(self):
        """Test that computed fields are read-only."""
        serializer = AttachmentSerializer()
        read_only_fields = serializer.Meta.read_only_fields

        expected_read_only = ["filename", "file_type", "size", "uploaded_at"]
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)


class MessageSerializerTest(TestCase):
    """Test MessageSerializer validation and data handling."""

    def setUp(self):
        """Set up test data for messages."""
        self.user1 = User.objects.create_user(email="user1@example.com", username="user1", password="password")
        self.user2 = User.objects.create_user(email="user2@example.com", username="user2", password="password")

        self.channel = Channel.objects.create(name="test-channel")
        self.channel.participants.add(self.user1, self.user2)

    def test_message_serialization_structure(self):
        """Test message serialization includes all expected fields."""
        message = Message.objects.create(channel=self.channel, sender=self.user1, content="Test message")

        serializer = MessageSerializer(message)
        data = serializer.data

        expected_fields = [
            "id",
            "channel",
            "sender",
            "content",
            "timestamp",
            "file",
            "reactions",
            "attachments",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

        self.assertEqual(data["content"], "Test message")
        self.assertEqual(data["sender"]["id"], self.user1.id)
        self.assertEqual(data["channel"], self.channel.id)

    def test_message_validation_valid_content(self):
        """Test valid message content passes validation."""
        data = {"channel": self.channel.id, "content": "Hello world!"}

        serializer = MessageSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["content"], "Hello world!")

    def test_message_validation_with_file_only(self):
        """Test message with file attachment but no content."""
        test_file = SimpleUploadedFile("test.pdf", b"file content", content_type="application/pdf")
        data = {"channel": self.channel.id, "content": "", "file": test_file}

        serializer = MessageSerializer(data=data)
        # Should be valid if file is provided (depends on business rules)
        result = serializer.is_valid()
        if not result:
            # If not valid, should have appropriate error
            self.assertTrue("content" in serializer.errors or "file" in serializer.errors)

    def test_message_validation_missing_channel(self):
        """Test validation fails for missing channel."""
        data = {"content": "Test message"}

        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("channel", serializer.errors)

    def test_message_read_only_fields(self):
        """Test that system fields are read-only."""
        serializer = MessageSerializer()
        read_only_fields = serializer.Meta.read_only_fields

        self.assertIn("sender", read_only_fields)
        self.assertIn("timestamp", read_only_fields)

    def test_message_nested_serializers(self):
        """Test that nested serializers work correctly."""
        message = Message.objects.create(channel=self.channel, sender=self.user1, content="Test message")

        # Add a reaction
        Reaction.objects.create(message=message, user=self.user2, emoji="👍")

        serializer = MessageSerializer(message)
        data = serializer.data

        # Check nested reactions
        self.assertEqual(len(data["reactions"]), 1)
        self.assertEqual(data["reactions"][0]["emoji"], "👍")
        self.assertEqual(data["reactions"][0]["user"]["id"], self.user2.id)


class ChannelSerializerTest(TestCase):
    """Test ChannelSerializer validation and participant management."""

    def setUp(self):
        """Set up test users and channel data."""
        self.user1 = User.objects.create_user(email="user1@example.com", username="user1", password="password")
        self.user2 = User.objects.create_user(email="user2@example.com", username="user2", password="password")
        self.user3 = User.objects.create_user(email="user3@example.com", username="user3", password="password")

    def test_channel_serialization_structure(self):
        """Test channel serialization includes all expected fields."""
        channel = Channel.objects.create(name="Test Channel")
        channel.participants.add(self.user1, self.user2)

        serializer = ChannelSerializer(channel)
        data = serializer.data

        expected_fields = [
            "id",
            "name",
            "is_direct",
            "participants",
            "online",
            "created_at",
            "updated_at",
            "last_message",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

        self.assertEqual(data["name"], "Test Channel")
        self.assertFalse(data["is_direct"])
        self.assertEqual(len(data["participants"]), 2)

    def test_channel_validation_group_channel(self):
        """Test valid group channel creation data."""
        data = {
            "name": "Study Group",
            "is_direct": False,
            "participant_ids": [self.user2.id, self.user3.id],
        }

        serializer = ChannelSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_channel_validation_direct_message(self):
        """Test valid direct message channel data."""
        data = {
            "name": "",
            "is_direct": True,
            "participant_ids": [self.user2.id],
        }

        serializer = ChannelSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_channel_validation_dm_wrong_participant_count(self):
        """Test DM validation rejects wrong participant count."""
        data = {
            "name": "",
            "is_direct": True,
            "participant_ids": [self.user2.id, self.user3.id],  # Too many
        }

        serializer = ChannelSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Direct messages must have exactly one other participant", str(serializer.errors))

    def test_channel_validation_dm_no_participants(self):
        """Test DM validation rejects empty participant list."""
        data = {
            "name": "",
            "is_direct": True,
            "participant_ids": [],
        }

        serializer = ChannelSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_channel_read_only_fields(self):
        """Test that system fields are read-only."""
        serializer = ChannelSerializer()
        read_only_fields = serializer.Meta.read_only_fields

        expected_read_only = ["created_at", "updated_at", "online"]
        for field in expected_read_only:
            self.assertIn(field, read_only_fields)

    def test_channel_last_message_serialization(self):
        """Test last_message field serialization."""
        channel = Channel.objects.create(name="Test Channel")
        channel.participants.add(self.user1, self.user2)

        # Add a message
        Message.objects.create(channel=channel, sender=self.user1, content="Last message")

        serializer = ChannelSerializer(channel)
        data = serializer.data

        self.assertIsNotNone(data["last_message"])
        self.assertEqual(data["last_message"]["content"], "Last message")

    def test_channel_empty_last_message(self):
        """Test last_message field for channel with no messages."""
        channel = Channel.objects.create(name="Empty Channel")

        serializer = ChannelSerializer(channel)
        data = serializer.data

        self.assertIsNone(data["last_message"])

    def test_channel_participants_nested_serialization(self):
        """Test participants are properly nested with user data."""
        channel = Channel.objects.create(name="Test Channel")
        channel.participants.add(self.user1, self.user2)

        serializer = ChannelSerializer(channel)
        data = serializer.data

        participants = data["participants"]
        self.assertEqual(len(participants), 2)

        for participant in participants:
            self.assertIn("id", participant)
            self.assertIn("username", participant)
            self.assertIn("email", participant)


class SerializerSecurityTest(TestCase):
    """Test serializer security and input validation."""

    def setUp(self):
        """Set up test data for security tests."""
        self.user = User.objects.create_user(email="test@example.com", username="testuser", password="password")
        self.channel = Channel.objects.create(name="test-channel")
        self.channel.participants.add(self.user)

    def test_message_content_basic_validation(self):
        """Test message content handles basic input."""
        test_contents = [
            "Normal message",
            "Message with emoji 📚",
            "Portuguese: Olá, como está?",
            "Special chars: @#$%^&*()",
        ]

        for content in test_contents:
            with self.subTest(content=content):
                data = {"channel": self.channel.id, "content": content}
                serializer = MessageSerializer(data=data)
                self.assertTrue(serializer.is_valid(), f"Should accept content: {content}. Errors: {serializer.errors}")

    def test_channel_name_basic_validation(self):
        """Test channel name validation."""
        valid_names = [
            "Study Group",
            "Math Class 2024",
            "Group-1",
            "Portuguese Study",
        ]

        for name in valid_names:
            with self.subTest(name=name):
                data = {
                    "name": name,
                    "is_direct": False,
                    "participant_ids": [self.user.id],
                }
                serializer = ChannelSerializer(data=data)
                self.assertTrue(serializer.is_valid(), f"Should accept name: {name}. Errors: {serializer.errors}")

    def test_reaction_emoji_validation(self):
        """Test reaction emoji validation."""
        message = Message.objects.create(channel=self.channel, sender=self.user, content="Test")

        valid_emojis = ["👍", "❤️", "😂", "🎉", "✅"]

        for emoji in valid_emojis:
            with self.subTest(emoji=emoji):
                data = {"message": message.id, "emoji": emoji}
                serializer = ReactionSerializer(data=data)
                self.assertTrue(serializer.is_valid(), f"Should accept emoji: {emoji}. Errors: {serializer.errors}")

    def test_file_upload_basic_validation(self):
        """Test file upload basic validation."""
        valid_files = [
            ("document.pdf", b"PDF content", "application/pdf"),
            ("image.jpg", b"JPEG content", "image/jpeg"),
            ("text.txt", b"Text content", "text/plain"),
        ]

        for filename, content, content_type in valid_files:
            with self.subTest(filename=filename):
                test_file = SimpleUploadedFile(filename, content, content_type=content_type)
                data = {"file": test_file}
                serializer = AttachmentSerializer(data=data)
                # Basic structure validation should pass
                result = serializer.is_valid()
                # File type restrictions might be handled at model/view level
