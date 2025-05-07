"""
Tests for classroom app models.

This module contains tests for the following models:
- Channel: Group chats and direct messages
- Message: Text content and file attachments
- Reaction: Emoji reactions to messages
- Attachment: File uploads associated with messages
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from classroom.models import Attachment, Channel, Message, Reaction

User = get_user_model()


class ChannelModelTest(TestCase):
    """Test cases for the Channel model.

    Tests channel creation, participant management, online status tracking,
    and special handling for direct messages vs group channels.
    """

    def setUp(self):
        """Set up test users for channel tests."""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password"
        )
        self.user3 = User.objects.create_user(
            username="user3", email="user3@example.com", password="password"
        )

    def test_direct_channel_creation(self):
        """Test creation of a direct message channel between two users."""
        channel = Channel.objects.create(name="", is_direct=True)
        channel.participants.add(self.user1, self.user2)

        self.assertEqual(channel.participants.count(), 2)
        self.assertTrue(channel.is_direct)
        self.assertIn("DM:", str(channel))

        # Test the direct channel name generation method
        dm_name = channel.get_direct_channel_name(self.user1, self.user2)
        self.assertEqual(
            dm_name,
            f"DM_{self.user1.username}_{self.user2.username}"
            if self.user1.username < self.user2.username
            else f"DM_{self.user2.username}_{self.user1.username}",
        )

    def test_group_channel_creation(self):
        """Test creation of a group channel with multiple participants."""
        channel = Channel.objects.create(name="Test Group", is_direct=False)
        channel.participants.add(self.user1, self.user2, self.user3)

        self.assertEqual(channel.participants.count(), 3)
        self.assertFalse(channel.is_direct)
        self.assertEqual(str(channel), "Test Group")

    def test_online_status_tracking(self):
        """Test adding and removing users from the online list."""
        channel = Channel.objects.create(name="Test Group")
        self.assertEqual(channel.online.count(), 0)

        # Add a user to online list
        channel.online.add(self.user1)
        self.assertEqual(channel.online.count(), 1)
        self.assertIn(self.user1, channel.online.all())

        # Add another user to online list
        channel.online.add(self.user2)
        self.assertEqual(channel.online.count(), 2)

        # Remove a user from online list
        channel.online.remove(self.user1)
        self.assertEqual(channel.online.count(), 1)
        self.assertNotIn(self.user1, channel.online.all())
        self.assertIn(self.user2, channel.online.all())


class MessageModelTest(TestCase):
    """Test cases for the Message model.

    Tests message creation with text content and file attachments.
    """

    def setUp(self):
        """Set up user, channel, and test files for message tests."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password"
        )
        self.channel = Channel.objects.create(name="Test Channel")
        self.channel.participants.add(self.user)

        # Set up a test file for file attachment tests
        self.test_file_content = b"This is a test file content"
        self.test_file = SimpleUploadedFile(
            "test.txt", self.test_file_content, content_type="text/plain"
        )

    def test_message_creation(self):
        """Test creating a basic text message."""
        message = Message.objects.create(
            channel=self.channel, sender=self.user, content="Test message"
        )

        self.assertEqual(message.content, "Test message")
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.channel, self.channel)
        self.assertFalse(bool(message.file))  # File should be empty

        # Test string representation
        self.assertIn("Test message", str(message))
        self.assertIn(self.user.username, str(message))

    def test_message_with_file(self):
        """Test creating a message with a file attachment."""
        message = Message.objects.create(
            channel=self.channel, sender=self.user, content="File message", file=self.test_file
        )

        self.assertEqual(message.content, "File message")
        self.assertIsNotNone(message.file)
        self.assertTrue(message.file.name.endswith(".txt"))


class ReactionModelTest(TestCase):
    """Test cases for the Reaction model.

    Tests emoji reactions to messages, including creating,
    retrieving, and unique constraints.
    """

    def setUp(self):
        """Set up user, channel, and message for reaction tests."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="anotheruser", email="anotheruser@example.com", password="password"
        )
        self.channel = Channel.objects.create(name="Test Channel")
        self.message = Message.objects.create(
            channel=self.channel, sender=self.user, content="Test message"
        )

    def test_reaction_creation(self):
        """Test creating an emoji reaction to a message."""
        reaction = Reaction.objects.create(message=self.message, user=self.user, emoji="👍")

        self.assertEqual(reaction.emoji, "👍")
        self.assertEqual(reaction.user, self.user)
        self.assertEqual(reaction.message, self.message)
        self.assertIsNotNone(reaction.created_at)

        # Test string representation
        self.assertIn(self.user.username, str(reaction))
        self.assertIn("👍", str(reaction))

    def test_multiple_reactions(self):
        """Test multiple reactions from different users."""
        reaction1 = Reaction.objects.create(message=self.message, user=self.user, emoji="👍")

        reaction2 = Reaction.objects.create(message=self.message, user=self.user2, emoji="👍")

        reaction3 = Reaction.objects.create(message=self.message, user=self.user, emoji="❤️")

        # User can have different emojis on same message
        self.assertEqual(Reaction.objects.filter(user=self.user).count(), 2)

        # Different users can use same emoji
        self.assertEqual(Reaction.objects.filter(emoji="👍").count(), 2)


class AttachmentModelTest(TestCase):
    """Test cases for the Attachment model.

    Tests file uploads and metadata storage.
    """

    def setUp(self):
        """Set up user, channel, message, and test file for attachment tests."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password"
        )
        self.channel = Channel.objects.create(name="Test Channel")
        self.message = Message.objects.create(
            channel=self.channel, sender=self.user, content="Test message"
        )

        # Create a test file
        self.test_file_content = b"This is a test attachment"
        self.test_file = SimpleUploadedFile(
            "document.pdf", self.test_file_content, content_type="application/pdf"
        )

    def test_attachment_creation(self):
        """Test creating an attachment with file metadata."""
        attachment = Attachment.objects.create(
            message=self.message,
            file=self.test_file,
            filename="document.pdf",
            file_type="application/pdf",
            size=len(self.test_file_content),
        )

        self.assertEqual(attachment.message, self.message)
        self.assertEqual(attachment.filename, "document.pdf")
        self.assertEqual(attachment.file_type, "application/pdf")
        self.assertEqual(attachment.size, len(self.test_file_content))
        self.assertIsNotNone(attachment.uploaded_at)

        # Test string representation
        self.assertIn("document.pdf", str(attachment))
        self.assertIn("application/pdf", str(attachment))
