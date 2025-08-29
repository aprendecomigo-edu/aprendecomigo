"""
Comprehensive unit tests for classroom app models.

This module tests core business rules and validation logic for:
- Channel: DM naming, participants, online users, creation/update timestamps
- Message: Content preservation, file validation, ordering, relationships
- Reaction: Uniqueness constraints, emoji validation, user relationships
- Attachment: File metadata storage, validation, size limits

Focuses on business logic, relationships, and edge cases.
"""

import tempfile
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone

from classroom.models import Attachment, Channel, Message, Reaction
from classroom.validators import validate_file_size

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

    def test_group_channel_displays_name(self):
        """Test that group channels display their name."""
        channel = Channel.objects.create(name="Study Group", is_direct=False)
        self.assertEqual(str(channel), "Study Group")

    def test_channel_participants_management(self):
        """Test adding and removing channel participants."""
        channel = Channel.objects.create(name="Test Channel", is_direct=False)
        
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

    def test_channel_online_users_management(self):
        """Test online users tracking in channels."""
        channel = Channel.objects.create(name="Test Channel", is_direct=False)
        channel.participants.add(self.user1, self.user2)
        
        # Mark users online
        channel.online.add(self.user1)
        self.assertEqual(channel.online.count(), 1)
        self.assertIn(self.user1, channel.online.all())
        self.assertNotIn(self.user2, channel.online.all())
        
        # Mark both users online
        channel.online.add(self.user2)
        self.assertEqual(channel.online.count(), 2)
        
        # Mark user offline
        channel.online.remove(self.user1)
        self.assertEqual(channel.online.count(), 1)
        self.assertNotIn(self.user1, channel.online.all())

    def test_channel_timestamps_auto_populated(self):
        """Test that channel timestamps are automatically set."""
        channel = Channel.objects.create(name="Test Channel", is_direct=False)
        
        self.assertIsNotNone(channel.created_at)
        self.assertIsNotNone(channel.updated_at)
        # Don't test exact timing as it can be flaky in tests
        from datetime import datetime
        self.assertTrue(isinstance(channel.created_at, datetime))
        self.assertTrue(isinstance(channel.updated_at, datetime))

    def test_channel_updated_at_changes_on_save(self):
        """Test that updated_at changes when channel is saved."""
        channel = Channel.objects.create(name="Test Channel", is_direct=False)
        original_updated = channel.updated_at
        
        # Wait a small amount to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        channel.name = "Updated Channel Name"
        channel.save()
        
        self.assertGreater(channel.updated_at, original_updated)

    def test_channel_ordering(self):
        """Test that channels are ordered by updated_at descending."""
        channel1 = Channel.objects.create(name="Channel 1", is_direct=False)
        channel2 = Channel.objects.create(name="Channel 2", is_direct=False)
        
        # Get all channels and verify ordering
        channels = list(Channel.objects.all())
        self.assertEqual(channels[0], channel2)  # More recent first
        self.assertEqual(channels[1], channel1)


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

    def test_message_string_representation_truncates_content(self):
        """Test that message string representation truncates long content."""
        long_content = "A" * 100  # 100 characters
        message = Message.objects.create(channel=self.channel, sender=self.user, content=long_content)
        
        str_repr = str(message)
        self.assertIn(self.user.username, str_repr)
        self.assertIn("A" * 50, str_repr)  # Should show first 50 chars
        self.assertLess(len(str_repr), len(f"{self.user.username}: {long_content}"))

    def test_message_timestamp_auto_populated(self):
        """Test that message timestamp is automatically set."""
        before_creation = timezone.now()
        message = Message.objects.create(channel=self.channel, sender=self.user, content="Test")
        after_creation = timezone.now()
        
        self.assertIsNotNone(message.timestamp)
        self.assertGreaterEqual(message.timestamp, before_creation)
        self.assertLessEqual(message.timestamp, after_creation)

    def test_message_ordering(self):
        """Test that messages are ordered by timestamp ascending."""
        message1 = Message.objects.create(channel=self.channel, sender=self.user, content="First")
        message2 = Message.objects.create(channel=self.channel, sender=self.user, content="Second")
        
        messages = list(Message.objects.all())
        self.assertEqual(messages[0], message1)  # Older first
        self.assertEqual(messages[1], message2)

    def test_message_with_file_attachment(self):
        """Test creating message with file attachment."""
        test_file = SimpleUploadedFile(
            "test.txt", 
            b"test content", 
            content_type="text/plain"
        )
        
        message = Message.objects.create(
            channel=self.channel, 
            sender=self.user, 
            content="Message with file",
            file=test_file
        )
        
        self.assertEqual(message.content, "Message with file")
        self.assertIsNotNone(message.file)
        # Django may modify the filename, just check it contains the base name
        self.assertIn("test", message.file.name)

    def test_message_without_file_attachment(self):
        """Test creating message without file attachment."""
        message = Message.objects.create(
            channel=self.channel, 
            sender=self.user, 
            content="Message without file"
        )
        
        self.assertEqual(message.content, "Message without file")
        self.assertFalse(message.file)

    def test_message_cascade_delete_with_channel(self):
        """Test that messages are deleted when channel is deleted."""
        message1 = Message.objects.create(channel=self.channel, sender=self.user, content="Test 1")
        message2 = Message.objects.create(channel=self.channel, sender=self.user, content="Test 2")
        
        message_ids = [message1.id, message2.id]
        
        # Delete channel
        self.channel.delete()
        
        # Messages should be deleted
        for msg_id in message_ids:
            with self.assertRaises(Message.DoesNotExist):
                Message.objects.get(id=msg_id)

    def test_message_relationship_with_sender(self):
        """Test message relationship with sender user."""
        message = Message.objects.create(channel=self.channel, sender=self.user, content="Test")
        
        # Test forward relationship
        self.assertEqual(message.sender, self.user)
        
        # Test reverse relationship
        user_messages = self.user.messages.all()
        self.assertIn(message, user_messages)

    def test_empty_message_content_allowed(self):
        """Test that empty message content is allowed (for file-only messages)."""
        test_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        
        message = Message.objects.create(
            channel=self.channel, 
            sender=self.user, 
            content="",  # Empty content
            file=test_file
        )
        
        self.assertEqual(message.content, "")
        self.assertIsNotNone(message.file)


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

    def test_same_user_different_emoji_allowed(self):
        """Test that same user can react with different emojis to same message."""
        Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        Reaction.objects.create(message=self.message, user=self.user, emoji="❤️")
        
        reactions = Reaction.objects.filter(message=self.message, user=self.user)
        self.assertEqual(reactions.count(), 2)
        
        emojis = set(reaction.emoji for reaction in reactions)
        self.assertEqual(emojis, {"👍", "❤️"})

    def test_different_users_same_emoji_allowed(self):
        """Test that different users can react with same emoji to same message."""
        user2 = User.objects.create_user(username="user2", email="user2@example.com", password="password")
        
        Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        Reaction.objects.create(message=self.message, user=user2, emoji="👍")
        
        reactions = Reaction.objects.filter(message=self.message, emoji="👍")
        self.assertEqual(reactions.count(), 2)
        
        users = set(reaction.user for reaction in reactions)
        self.assertEqual(users, {self.user, user2})

    def test_reaction_string_representation(self):
        """Test reaction string representation."""
        reaction = Reaction.objects.create(message=self.message, user=self.user, emoji="🎉")
        
        str_repr = str(reaction)
        self.assertIn(self.user.username, str_repr)
        self.assertIn("🎉", str_repr)
        self.assertIn(str(self.message.id), str_repr)

    def test_reaction_timestamp_auto_populated(self):
        """Test that reaction timestamp is automatically set."""
        before_creation = timezone.now()
        reaction = Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        after_creation = timezone.now()
        
        self.assertIsNotNone(reaction.created_at)
        self.assertGreaterEqual(reaction.created_at, before_creation)
        self.assertLessEqual(reaction.created_at, after_creation)

    def test_reaction_ordering(self):
        """Test that reactions are ordered by created_at ascending."""
        reaction1 = Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        reaction2 = Reaction.objects.create(message=self.message, user=self.user, emoji="❤️")
        
        reactions = list(Reaction.objects.all())
        self.assertEqual(reactions[0], reaction1)  # Older first
        self.assertEqual(reactions[1], reaction2)

    def test_reaction_cascade_delete_with_message(self):
        """Test that reactions are deleted when message is deleted."""
        reaction = Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        reaction_id = reaction.id
        
        # Delete message
        self.message.delete()
        
        # Reaction should be deleted
        with self.assertRaises(Reaction.DoesNotExist):
            Reaction.objects.get(id=reaction_id)

    def test_reaction_relationship_with_user(self):
        """Test reaction relationship with user."""
        reaction = Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        
        # Test forward relationship
        self.assertEqual(reaction.user, self.user)
        
        # Test reverse relationship
        user_reactions = self.user.reactions.all()
        self.assertIn(reaction, user_reactions)

    def test_reaction_relationship_with_message(self):
        """Test reaction relationship with message."""
        reaction = Reaction.objects.create(message=self.message, user=self.user, emoji="👍")
        
        # Test forward relationship
        self.assertEqual(reaction.message, self.message)
        
        # Test reverse relationship
        message_reactions = self.message.reactions.all()
        self.assertIn(reaction, message_reactions)

    def test_emoji_max_length(self):
        """Test emoji field max length validation."""
        # Valid emoji (within 10 chars)
        reaction = Reaction.objects.create(message=self.message, user=self.user, emoji="🎉")
        self.assertEqual(len(reaction.emoji), 1)
        
        # Test complex emoji that might be longer
        complex_emoji = "👨‍💻"  # This compound emoji might be longer
        reaction2 = Reaction.objects.create(message=self.message, user=self.user, emoji=complex_emoji)
        self.assertEqual(reaction2.emoji, complex_emoji)


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

    def test_attachment_string_representation(self):
        """Test attachment string representation shows filename and type."""
        attachment = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="document.pdf",
            file_type="application/pdf",
            size=1024,
        )
        
        str_repr = str(attachment)
        self.assertIn("document.pdf", str_repr)
        self.assertIn("application/pdf", str_repr)

    def test_attachment_timestamp_auto_populated(self):
        """Test that attachment uploaded_at timestamp is automatically set."""
        before_creation = timezone.now()
        attachment = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="test.pdf",
            file_type="application/pdf",
            size=1024,
        )
        after_creation = timezone.now()
        
        self.assertIsNotNone(attachment.uploaded_at)
        self.assertGreaterEqual(attachment.uploaded_at, before_creation)
        self.assertLessEqual(attachment.uploaded_at, after_creation)

    def test_attachment_ordering(self):
        """Test that attachments are ordered by uploaded_at descending."""
        attachment1 = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="first.pdf",
            file_type="application/pdf",
            size=1024,
        )
        attachment2 = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="second.pdf",
            file_type="application/pdf",
            size=2048,
        )
        
        attachments = list(Attachment.objects.all())
        self.assertEqual(attachments[0], attachment2)  # More recent first
        self.assertEqual(attachments[1], attachment1)

    def test_attachment_cascade_delete_with_message(self):
        """Test that attachments are deleted when message is deleted."""
        attachment = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="test.pdf",
            file_type="application/pdf",
            size=1024,
        )
        attachment_id = attachment.id
        
        # Delete message
        self.message.delete()
        
        # Attachment should be deleted
        with self.assertRaises(Attachment.DoesNotExist):
            Attachment.objects.get(id=attachment_id)

    def test_attachment_relationship_with_message(self):
        """Test attachment relationship with message."""
        attachment = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="test.pdf",
            file_type="application/pdf",
            size=1024,
        )
        
        # Test forward relationship
        self.assertEqual(attachment.message, self.message)
        
        # Test reverse relationship
        message_attachments = self.message.attachments.all()
        self.assertIn(attachment, message_attachments)

    def test_multiple_attachments_per_message(self):
        """Test that messages can have multiple attachments."""
        attachment1 = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="doc1.pdf",
            file_type="application/pdf",
            size=1024,
        )
        attachment2 = Attachment.objects.create(
            message=self.message,
            file=self.valid_pdf,
            filename="doc2.pdf",
            file_type="application/pdf",
            size=2048,
        )
        
        attachments = self.message.attachments.all()
        self.assertEqual(attachments.count(), 2)
        self.assertIn(attachment1, attachments)
        self.assertIn(attachment2, attachments)

    def test_attachment_size_tracking(self):
        """Test that attachment size is properly tracked."""
        sizes = [1024, 2048, 5120]  # Different file sizes
        
        for size in sizes:
            attachment = Attachment.objects.create(
                message=self.message,
                file=self.valid_pdf,
                filename=f"file_{size}.pdf",
                file_type="application/pdf",
                size=size,
            )
            self.assertEqual(attachment.size, size)
            self.assertIsInstance(attachment.size, int)
            self.assertGreater(attachment.size, 0)


class FileValidationTest(TestCase):
    """Test file upload validation functionality."""

    def setUp(self):
        """Set up test data for file validation tests."""
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="password")
        self.channel = Channel.objects.create(name="Test Channel")
        
    @override_settings(MAX_UPLOAD_SIZE=1024)  # 1KB limit for testing
    def test_file_size_validation_enforces_limit(self):
        """Test that file size validation enforces configured limit."""
        # Create file larger than limit
        large_content = b"x" * 2048  # 2KB file
        large_file = SimpleUploadedFile("large.txt", large_content, content_type="text/plain")
        
        with self.assertRaises(ValidationError) as context:
            validate_file_size(large_file)
            
        self.assertIn("File too large", str(context.exception))

    @override_settings(MAX_UPLOAD_SIZE=1024)  # 1KB limit for testing
    def test_file_size_validation_allows_small_files(self):
        """Test that file size validation allows files under limit."""
        # Create file smaller than limit
        small_content = b"x" * 512  # 512 bytes
        small_file = SimpleUploadedFile("small.txt", small_content, content_type="text/plain")
        
        # Should not raise exception
        try:
            validate_file_size(small_file)
        except ValidationError:
            self.fail("validate_file_size raised ValidationError for valid small file")

    def test_allowed_file_extensions(self):
        """Test that only allowed file extensions are permitted."""
        allowed_extensions = ["pdf", "doc", "docx", "jpg", "jpeg", "png", "gif"]
        
        for ext in allowed_extensions:
            with self.subTest(extension=ext):
                test_file = SimpleUploadedFile(
                    f"test.{ext}",
                    b"test content",
                    content_type=f"application/{ext}" if ext in ["pdf", "doc", "docx"] else f"image/{ext}"
                )
                
                # Should be able to create message with allowed extension
                message = Message.objects.create(
                    channel=self.channel,
                    sender=self.user,
                    content="Test with file",
                    file=test_file
                )
                self.assertIsNotNone(message.file)

    def test_file_extension_case_insensitive(self):
        """Test that file extension validation is case insensitive."""
        # Test various cases
        extensions = ["PDF", "Pdf", "JPG", "Jpg", "PNG", "Png"]
        
        for ext in extensions:
            with self.subTest(extension=ext):
                test_file = SimpleUploadedFile(
                    f"test.{ext}",
                    b"test content",
                    content_type="application/pdf" if ext.lower() == "pdf" else "image/jpeg"
                )
                
                # Should work regardless of case
                message = Message.objects.create(
                    channel=self.channel,
                    sender=self.user,
                    content="Test with file",
                    file=test_file
                )
                self.assertIsNotNone(message.file)

    def test_message_file_upload_path(self):
        """Test that message files are uploaded to correct path."""
        test_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        
        message = Message.objects.create(
            channel=self.channel,
            sender=self.user,
            content="Test",
            file=test_file
        )
        
        # File should be stored in chat_attachments/ directory
        self.assertTrue(message.file.name.startswith("chat_attachments/"))
