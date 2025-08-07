"""
Unit tests for classroom app business logic.

This module tests business rules and validation logic for:
- Channel: DM naming consistency, participant management
- Message: File validation, content handling, ordering
- Reaction: Uniqueness constraints, emoji handling
- Attachment: File validation, metadata storage, ordering
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from classroom.models import Attachment, Channel, Message, Reaction

User = get_user_model()


class ChannelBusinessLogicTest(TestCase):
    """Test business logic for the Channel model.

    Tests DM naming consistency, participant management, and online status tracking.
    """

    def setUp(self):
        """Set up test users for channel tests."""
        self.user1 = User.objects.create_user(
            username="alice", email="alice@example.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="bob", email="bob@example.com", password="password"
        )
        self.user3 = User.objects.create_user(
            username="charlie", email="charlie@example.com", password="password"
        )

    def test_participants_can_be_added_and_removed(self):
        """Test that channel participants can be managed."""
        channel = Channel.objects.create(name="Study Group", is_direct=False)
        
        # Add participants
        channel.participants.add(self.user1, self.user2)
        self.assertEqual(channel.participants.count(), 2)
        self.assertIn(self.user1, channel.participants.all())
        self.assertIn(self.user2, channel.participants.all())
        
        # Remove participant
        channel.participants.remove(self.user1)
        self.assertEqual(channel.participants.count(), 1)
        self.assertNotIn(self.user1, channel.participants.all())
        self.assertIn(self.user2, channel.participants.all())

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

    def test_online_status_can_be_tracked_for_participants(self):
        """Test that online status can be tracked for channel participants."""
        channel = Channel.objects.create(name="Test Channel")
        channel.participants.add(self.user1, self.user2)
        
        # Initially no one is online
        self.assertEqual(channel.online.count(), 0)

        # User comes online
        channel.online.add(self.user1)
        self.assertEqual(channel.online.count(), 1)
        self.assertIn(self.user1, channel.online.all())

        # Second user comes online
        channel.online.add(self.user2)
        self.assertEqual(channel.online.count(), 2)

        # First user goes offline
        channel.online.remove(self.user1)
        self.assertEqual(channel.online.count(), 1)
        self.assertNotIn(self.user1, channel.online.all())
        self.assertIn(self.user2, channel.online.all())


class MessageBusinessLogicTest(TestCase):
    """Test business logic for the Message model.

    Tests file validation, content handling, and chronological ordering.
    """

    def setUp(self):
        """Set up user, channel, and test files for message tests."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password"
        )
        self.channel = Channel.objects.create(name="Test Channel")
        self.channel.participants.add(self.user)

        # Set up test files for validation tests
        self.valid_file = SimpleUploadedFile(
            "document.pdf", b"Valid PDF content", content_type="application/pdf"
        )
        self.invalid_file = SimpleUploadedFile(
            "malicious.exe", b"Executable content", content_type="application/x-executable"
        )

    def test_message_content_is_preserved_correctly(self):
        """Test that message content is stored and retrieved accurately."""
        content = "Hello world! This is a test message with special chars: áéíóú & <script>"
        message = Message.objects.create(
            channel=self.channel, sender=self.user, content=content
        )
        
        # Content should be preserved exactly
        self.assertEqual(message.content, content)
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.channel, self.channel)
        self.assertIsNotNone(message.timestamp)

    def test_message_accepts_files_with_valid_extensions(self):
        """Test that messages accept files with valid extensions."""
        message = Message.objects.create(
            channel=self.channel, 
            sender=self.user, 
            content="File with valid extension", 
            file=self.valid_file
        )

        self.assertEqual(message.content, "File with valid extension")
        self.assertIsNotNone(message.file)
        self.assertTrue(message.file.name.endswith(".pdf"))
        
    def test_messages_are_ordered_chronologically(self):
        """Test that messages are ordered by timestamp (oldest first)."""
        # Create messages in sequence
        msg1 = Message.objects.create(
            channel=self.channel, sender=self.user, content="First message"
        )
        msg2 = Message.objects.create(
            channel=self.channel, sender=self.user, content="Second message"
        )
        msg3 = Message.objects.create(
            channel=self.channel, sender=self.user, content="Third message"
        )
        
        # Query messages and verify ordering
        messages = list(Message.objects.filter(channel=self.channel))
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0].content, "First message")
        self.assertEqual(messages[1].content, "Second message") 
        self.assertEqual(messages[2].content, "Third message")
        
        # Verify timestamps are in ascending order
        self.assertLessEqual(messages[0].timestamp, messages[1].timestamp)
        self.assertLessEqual(messages[1].timestamp, messages[2].timestamp)

    def test_message_can_be_created_without_file(self):
        """Test that messages can be created with text only, no file required."""
        message = Message.objects.create(
            channel=self.channel, 
            sender=self.user, 
            content="Text only message"
        )
        
        self.assertEqual(message.content, "Text only message")
        self.assertFalse(bool(message.file))  # No file should be attached
        self.assertIsNotNone(message.timestamp)


class ReactionBusinessLogicTest(TestCase):
    """Test business logic for the Reaction model.

    Tests uniqueness constraints and emoji reaction handling.
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

    def test_user_can_add_multiple_different_reactions_to_same_message(self):
        """Test that a user can add different emoji reactions to the same message."""
        Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        Reaction.objects.create(message=self.message, user=self.user, emoji="❤️")
        
        user_reactions = Reaction.objects.filter(user=self.user, message=self.message)
        self.assertEqual(user_reactions.count(), 2)
        
        emojis = [r.emoji for r in user_reactions]
        self.assertIn("👍", emojis)
        self.assertIn("❤️", emojis)

    def test_multiple_users_can_react_with_same_emoji(self):
        """Test that different users can use the same emoji on a message."""
        Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        Reaction.objects.create(message=self.message, user=self.user2, emoji="👍")
        
        thumbs_up_reactions = Reaction.objects.filter(emoji="👍", message=self.message)
        self.assertEqual(thumbs_up_reactions.count(), 2)
        
        users = [r.user for r in thumbs_up_reactions]
        self.assertIn(self.user, users)
        self.assertIn(self.user2, users)

    def test_reaction_unique_constraint_prevents_duplicates(self):
        """Test that duplicate reactions (same user, message, emoji) are prevented."""
        # Create first reaction
        Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        
        # Verify only one reaction exists before attempting duplicate
        reactions = Reaction.objects.filter(
            message=self.message, user=self.user, emoji="👍"
        )
        self.assertEqual(reactions.count(), 1)
        
        # Attempting to create duplicate should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Reaction.objects.create(message=self.message, user=self.user, emoji="👍")

    def test_reactions_are_ordered_chronologically(self):
        """Test that reactions are ordered by creation time."""
        # Create reactions in sequence
        reaction1 = Reaction.objects.create(
            message=self.message, user=self.user, emoji="👍"
        )
        reaction2 = Reaction.objects.create(
            message=self.message, user=self.user2, emoji="❤️"
        )
        
        # Query reactions and verify ordering
        reactions = list(Reaction.objects.filter(message=self.message))
        self.assertEqual(len(reactions), 2)
        
        # First reaction should come first (oldest first)
        self.assertEqual(reactions[0].emoji, "👍")
        self.assertEqual(reactions[1].emoji, "❤️")
        self.assertLessEqual(reactions[0].created_at, reactions[1].created_at)


class AttachmentBusinessLogicTest(TestCase):
    """Test business logic for the Attachment model.

    Tests file validation, metadata storage, and ordering behavior.
    """

    def setUp(self):
        """Set up user, channel, message, and test files for attachment tests."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password"
        )
        self.channel = Channel.objects.create(name="Test Channel")
        self.message = Message.objects.create(
            channel=self.channel, sender=self.user, content="Test message"
        )

        # Create test files for validation
        self.valid_pdf = SimpleUploadedFile(
            "document.pdf", b"PDF content", content_type="application/pdf"
        )
        self.valid_image = SimpleUploadedFile(
            "image.jpg", b"JPEG content", content_type="image/jpeg"
        )

    def test_attachment_stores_file_metadata_correctly(self):
        """Test that attachment stores complete file metadata."""
        file_content = b"This is a test PDF document content"
        attachment = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="business_plan.pdf",
            file_type="application/pdf",
            size=len(file_content)
        )
        
        self.assertEqual(attachment.message, self.message)
        self.assertEqual(attachment.filename, "business_plan.pdf")
        self.assertEqual(attachment.file_type, "application/pdf")
        self.assertEqual(attachment.size, len(file_content))
        self.assertIsNotNone(attachment.uploaded_at)
        self.assertIsNotNone(attachment.file)
        
    def test_attachments_are_ordered_by_upload_time_newest_first(self):
        """Test that attachments are ordered by upload time (newest first)."""
        # Create attachments in sequence
        attachment1 = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="first.pdf",
            file_type="application/pdf",
            size=100
        )
        attachment2 = Attachment.objects.create(
            message=self.message,
            file=self.valid_image,
            filename="second.jpg",
            file_type="image/jpeg",
            size=200
        )
        
        # Query attachments and verify ordering (newest first)
        attachments = list(Attachment.objects.filter(message=self.message))
        self.assertEqual(len(attachments), 2)
        
        # Second attachment should come first (newest first ordering)
        self.assertEqual(attachments[0].filename, "second.jpg")
        self.assertEqual(attachments[1].filename, "first.pdf")
        self.assertGreaterEqual(attachments[0].uploaded_at, attachments[1].uploaded_at)

    def test_attachment_supports_various_valid_file_types(self):
        """Test that attachments support all valid file extensions defined in model."""
        # Test different valid file types that should be accepted
        valid_files = [
            ("document.pdf", "application/pdf"),
            ("document.doc", "application/msword"), 
            ("image.jpg", "image/jpeg"),
            ("image.png", "image/png"),
            ("image.gif", "image/gif"),
        ]
        
        for filename, content_type in valid_files:
            with self.subTest(filename=filename):
                test_file = SimpleUploadedFile(filename, b"content", content_type=content_type)
                attachment = Attachment.objects.create(
                    message=self.message,
                    file=test_file,
                    filename=filename,
                    file_type=content_type,
                    size=100
                )
                
                self.assertEqual(attachment.filename, filename)
                self.assertEqual(attachment.file_type, content_type)
                self.assertIsNotNone(attachment.file)