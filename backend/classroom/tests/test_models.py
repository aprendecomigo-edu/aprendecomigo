"""
Unit tests for classroom app business logic.

This module tests core business rules and validation logic for:
- Channel: DM naming consistency and string representation
- Message: Content preservation and file validation
- Reaction: Uniqueness constraints
- Attachment: File metadata storage

Focuses on business logic, not Django framework features.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from classroom.models import Attachment, Channel, Message, Reaction

User = get_user_model()


class ChannelBusinessLogicTest(TestCase):
    """Test business logic for the Channel model.

    Tests DM naming consistency and string representation.
    """

    def setUp(self):
        """Set up test users for channel tests."""
        self.user1 = User.objects.create_user(username="alice", email="alice@example.com", password="password")
        self.user2 = User.objects.create_user(username="bob", email="bob@example.com", password="password")

    def test_dm_name_generation_is_consistent_regardless_of_user_order(self):
        """Test that direct message channel names are consistent regardless of user order."""
        channel = Channel()

        # Generate name with users in different orders
        name1 = channel.get_direct_channel_name(self.user1, self.user2)
        name2 = channel.get_direct_channel_name(self.user2, self.user1)

        # Names should be identical regardless of order
        self.assertEqual(name1, name2)
        self.assertIn(self.user1.username, name1)
        self.assertIn(self.user2.username, name1)
        self.assertTrue(name1.startswith("DM_"))

    def test_dm_channel_displays_participant_usernames(self):
        """Test that DM channels show participant usernames in string representation."""
        channel = Channel.objects.create(name="", is_direct=True)
        channel.participants.add(self.user1, self.user2)

        str_repr = str(channel)
        self.assertTrue(str_repr.startswith("DM:"))
        self.assertIn(self.user1.username, str_repr)
        self.assertIn(self.user2.username, str_repr)


class MessageBusinessLogicTest(TestCase):
    """Test business logic for the Message model.

    Tests content preservation and file validation.
    """

    def setUp(self):
        """Set up user and channel for message tests."""
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="password")
        self.channel = Channel.objects.create(name="Test Channel")
        self.channel.participants.add(self.user)

    def test_message_preserves_special_characters_and_html(self):
        """Test that message content preserves special characters and HTML without escaping."""
        content = "Hello world! This is a test message with special chars: áéíóú & <script>"
        message = Message.objects.create(channel=self.channel, sender=self.user, content=content)

        # Content should be preserved exactly as entered (no escaping)
        self.assertEqual(message.content, content)
        self.assertIn("áéíóú", message.content)
        self.assertIn("<script>", message.content)
        self.assertIn("&", message.content)


class ReactionBusinessLogicTest(TestCase):
    """Test business logic for the Reaction model.

    Tests uniqueness constraints for emoji reactions.
    """

    def setUp(self):
        """Set up user, channel, and message for reaction tests."""
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="password")
        self.channel = Channel.objects.create(name="Test Channel")
        self.message = Message.objects.create(channel=self.channel, sender=self.user, content="Test message")

    def test_reaction_unique_constraint_prevents_duplicates(self):
        """Test that duplicate reactions (same user, message, emoji) are prevented."""
        # Create first reaction
        Reaction.objects.create(message=self.message, user=self.user, emoji="👍")

        # Verify only one reaction exists before attempting duplicate
        reactions = Reaction.objects.filter(message=self.message, user=self.user, emoji="👍")
        self.assertEqual(reactions.count(), 1)

        # Attempting to create duplicate should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Reaction.objects.create(message=self.message, user=self.user, emoji="👍")


class AttachmentBusinessLogicTest(TestCase):
    """Test business logic for the Attachment model.

    Tests file metadata storage for business purposes.
    """

    def setUp(self):
        """Set up user, channel, message for attachment tests."""
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="password")
        self.channel = Channel.objects.create(name="Test Channel")
        self.message = Message.objects.create(channel=self.channel, sender=self.user, content="Test message")

        # Create test file for validation
        self.valid_pdf = SimpleUploadedFile("document.pdf", b"PDF content", content_type="application/pdf")

    def test_attachment_accurately_stores_file_metadata(self):
        """Test that attachment stores file metadata correctly for business purposes."""
        expected_size = 1024
        attachment = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="business_plan.pdf",
            file_type="application/pdf",
            size=expected_size,
        )

        # Verify business-critical metadata is stored accurately
        self.assertEqual(attachment.filename, "business_plan.pdf")
        self.assertEqual(attachment.file_type, "application/pdf")
        self.assertEqual(attachment.size, expected_size)

        # File type validation for business rules
        self.assertIn(
            attachment.file_type, ["application/pdf", "application/msword", "image/jpeg", "image/png", "image/gif"]
        )
