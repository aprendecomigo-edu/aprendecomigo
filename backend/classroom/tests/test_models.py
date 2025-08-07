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

    def test_group_channel_creation(self):
        """Test creating a group channel with name and participants."""
        channel = Channel.objects.create(name="Study Group", is_direct=False)
        channel.participants.add(self.user1, self.user2, self.user3)
        
        self.assertEqual(channel.name, "Study Group")
        self.assertFalse(channel.is_direct)
        self.assertEqual(channel.participants.count(), 3)
        self.assertIn(self.user1, channel.participants.all())
        self.assertIn(self.user2, channel.participants.all())
        self.assertIn(self.user3, channel.participants.all())

    def test_direct_message_channel_creation(self):
        """Test creating a direct message channel between two users."""
        channel = Channel.objects.create(name="", is_direct=True)
        channel.participants.add(self.user1, self.user2)
        
        self.assertTrue(channel.is_direct)
        self.assertEqual(channel.participants.count(), 2)
        self.assertIn(self.user1, channel.participants.all())
        self.assertIn(self.user2, channel.participants.all())

    def test_channel_string_representation_group(self):
        """Test string representation of a group channel."""
        channel = Channel.objects.create(name="Math Tutoring", is_direct=False)
        self.assertEqual(str(channel), "Math Tutoring")

    def test_channel_string_representation_direct(self):
        """Test string representation of a direct message channel."""
        channel = Channel.objects.create(name="", is_direct=True)
        channel.participants.add(self.user1, self.user2)
        
        # Should show usernames of participants
        expected = f"DM: {self.user1.username}, {self.user2.username}"
        self.assertEqual(str(channel), expected)

    def test_direct_channel_name_generation(self):
        """Test consistent naming for direct message channels."""
        channel = Channel()
        name1 = channel.get_direct_channel_name(self.user1, self.user2)
        name2 = channel.get_direct_channel_name(self.user2, self.user1)
        
        # Should be the same regardless of user order
        self.assertEqual(name1, name2)
        self.assertIn(self.user1.username, name1)
        self.assertIn(self.user2.username, name1)


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


    def test_message_creation_text_only(self):
        """Test creating a text-only message."""
        message = Message.objects.create(
            channel=self.channel, sender=self.user, content="Hello world!"
        )
        
        self.assertEqual(message.content, "Hello world!")
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.channel, self.channel)
        self.assertIsNotNone(message.timestamp)
        self.assertFalse(bool(message.file))  # No file attached

    def test_message_with_file(self):
        """Test creating a message with a file attachment."""
        message = Message.objects.create(
            channel=self.channel, sender=self.user, content="File message", file=self.test_file
        )

        self.assertEqual(message.content, "File message")
        self.assertIsNotNone(message.file)
        self.assertTrue(message.file.name.endswith(".txt"))

    def test_message_string_representation(self):
        """Test message string representation truncates long content."""
        long_content = "This is a very long message that should be truncated in the string representation" * 2
        message = Message.objects.create(
            channel=self.channel, sender=self.user, content=long_content
        )
        
        str_repr = str(message)
        self.assertIn(self.user.username, str_repr)
        self.assertTrue(len(str_repr) < len(long_content))  # Should be truncated
        self.assertIn(long_content[:50], str_repr)  # First 50 chars should be present


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
        """Test creating a reaction to a message."""
        reaction = Reaction.objects.create(
            message=self.message, user=self.user, emoji="👍"
        )
        
        self.assertEqual(reaction.message, self.message)
        self.assertEqual(reaction.user, self.user)
        self.assertEqual(reaction.emoji, "👍")
        self.assertIsNotNone(reaction.created_at)

    def test_multiple_reactions_same_user(self):
        """Test that a user can add different emojis to the same message."""
        Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        Reaction.objects.create(message=self.message, user=self.user, emoji="❤️")
        
        # User can have different emojis on same message
        self.assertEqual(Reaction.objects.filter(user=self.user).count(), 2)

    def test_multiple_users_same_emoji(self):
        """Test that different users can use the same emoji on a message."""
        Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        Reaction.objects.create(message=self.message, user=self.user2, emoji="👍")
        
        # Different users can use same emoji
        self.assertEqual(Reaction.objects.filter(emoji="👍").count(), 2)

    def test_reaction_unique_constraint(self):
        """Test that duplicate reactions (same user, message, emoji) are prevented."""
        # Create first reaction
        Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        
        # Attempting to create duplicate should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Reaction.objects.create(message=self.message, user=self.user, emoji="👍")

    def test_reaction_string_representation(self):
        """Test reaction string representation includes user and emoji."""
        reaction = Reaction.objects.create(
            message=self.message, user=self.user, emoji="🎉"
        )
        
        str_repr = str(reaction)
        self.assertIn(self.user.username, str_repr)
        self.assertIn("🎉", str_repr)
        self.assertIn(str(self.message.id), str_repr)


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
        from classroom.models import Attachment
        
        attachment = Attachment.objects.create(
            message=self.message,
            file=self.test_file,
            filename="document.pdf",
            file_type="application/pdf",
            size=len(self.test_file_content)
        )
        
        self.assertEqual(attachment.message, self.message)
        self.assertEqual(attachment.filename, "document.pdf")
        self.assertEqual(attachment.file_type, "application/pdf")
        self.assertEqual(attachment.size, len(self.test_file_content))
        self.assertIsNotNone(attachment.uploaded_at)

    def test_attachment_string_representation(self):
        """Test attachment string representation shows filename and type."""
        from classroom.models import Attachment
        
        attachment = Attachment.objects.create(
            message=self.message,
            file=self.test_file,
            filename="important_document.pdf",
            file_type="application/pdf",
            size=1024
        )
        
        str_repr = str(attachment)
        self.assertIn("important_document.pdf", str_repr)
        self.assertIn("application/pdf", str_repr)

