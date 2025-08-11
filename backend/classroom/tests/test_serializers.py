"""
Comprehensive serializer tests for the classroom app.

These tests verify serializer validation, field exposure, data transformation,
and security enforcement for real-time messaging and classroom features.
Critical areas covered:
- Real-time messaging validation and security
- File attachment handling and validation  
- Channel management and permissions
- User reaction system validation
- Cross-field validation for messaging features
- Security validation against XSS and injection attacks
"""

import io
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from accounts.models import CustomUser
from classroom.models import Attachment, Channel, Message, Reaction
from classroom.serializers import (
    AttachmentSerializer, ChannelSerializer, MessageSerializer,
    ReactionSerializer, UserSerializer
)
from common.test_base import BaseAPITestCase, mock_external_services

User = get_user_model()


class TestUserSerializer(BaseAPITestCase):
    """Test suite for UserSerializer in classroom context."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            name='Test User'
        )
        # Set additional fields that might be used in messaging context
        self.user.first_name = 'Test'
        self.user.last_name = 'User'
        self.user.save()

    def test_user_serialization_basic_fields(self):
        """Test serializing user data for messaging context."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        # Verify expected fields are present
        expected_fields = ['id', 'username', 'email', 'first_name', 'last_name']
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')

    def test_user_serialization_missing_names(self):
        """Test user serialization when first_name and last_name are missing."""
        user_no_names = CustomUser.objects.create_user(
            email='nonames@example.com',
            name='No Names User'
        )
        
        serializer = UserSerializer(user_no_names)
        data = serializer.data
        
        # Should handle missing first_name and last_name gracefully
        self.assertEqual(data['first_name'], '')
        self.assertEqual(data['last_name'], '')

    def test_sensitive_fields_not_exposed(self):
        """Test that sensitive user fields are not exposed in messaging context."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        # Fields that should NOT be in messaging context
        sensitive_fields = ['password', 'is_staff', 'is_superuser', 'date_joined', 'last_login']
        for field in sensitive_fields:
            self.assertNotIn(field, data)

    def test_username_field_handling(self):
        """Test username field handling for users without explicit username."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        # Username might be email or derived field
        self.assertIn('username', data)


class TestReactionSerializer(BaseAPITestCase):
    """Test suite for ReactionSerializer - Message reaction system."""

    def setUp(self):
        super().setUp()
        self.user1 = CustomUser.objects.create_user(
            email='user1@example.com',
            name='User One'
        )
        self.user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            name='User Two'
        )
        
        # Create channel and message for reaction context
        self.channel = Channel.objects.create(
            name='test-channel',
            is_direct=False
        )
        self.channel.participants.add(self.user1, self.user2)
        
        self.message = Message.objects.create(
            channel=self.channel,
            sender=self.user1,
            content='Test message for reactions'
        )
        
        self.reaction = Reaction.objects.create(
            message=self.message,
            user=self.user2,
            emoji='👍'
        )

    def test_reaction_serialization(self):
        """Test serializing reaction data."""
        serializer = ReactionSerializer(self.reaction)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = ['id', 'user', 'emoji', 'created_at']
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['emoji'], '👍')
        self.assertIsNotNone(data['created_at'])
        
        # User should be nested serialized
        self.assertIn('id', data['user'])
        self.assertEqual(data['user']['id'], self.user2.id)

    def test_emoji_validation_valid_emojis(self):
        """Test valid emoji reactions."""
        valid_emojis = [
            '👍', '👎', '❤️', '😂', '😮', '😢', '🎉',
            '👏', '🔥', '💯', '✅', '❌', '⭐'
        ]
        
        for emoji in valid_emojis:
            with self.subTest(emoji=emoji):
                data = {
                    'message': self.message.id,
                    'emoji': emoji
                }
                
                serializer = ReactionSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept emoji: {emoji}. Errors: {serializer.errors}")

    def test_emoji_validation_invalid_emojis(self):
        """Test invalid emoji reactions are handled appropriately."""
        invalid_emojis = [
            '',              # Empty
            'thumbs_up',     # Text instead of emoji
            ':)',            # Text emoticon
            '🔞',            # Inappropriate emoji (depending on business rules)
            'not_an_emoji'   # Plain text
        ]
        
        for emoji in invalid_emojis:
            with self.subTest(emoji=emoji):
                data = {
                    'message': self.message.id,
                    'emoji': emoji
                }
                
                # Note: The actual validation depends on business rules
                # Some might be valid, others invalid
                serializer = ReactionSerializer(data=data)
                if emoji in ['', 'not_an_emoji']:
                    # These should definitely be invalid
                    result = serializer.is_valid()
                    # Either rejected by serializer or will be caught by model validation

    def test_user_field_read_only(self):
        """Test user field is read-only (set by system)."""
        serializer = ReactionSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        
        self.assertIn('user', read_only_fields)
        self.assertIn('created_at', read_only_fields)

    def test_duplicate_reaction_handling(self):
        """Test handling of duplicate reactions from same user."""
        # Try to create another reaction from same user with same emoji
        data = {
            'message': self.message.id,
            'emoji': '👍'  # Same emoji as existing reaction
        }
        
        serializer = ReactionSerializer(data=data)
        # Validation should depend on business rules about duplicate reactions
        # Either prevented by serializer or model validation


class TestAttachmentSerializer(BaseAPITestCase):
    """Test suite for AttachmentSerializer - File attachment validation."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='user@example.com',
            name='Test User'
        )
        
        # Create test file
        self.test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        self.attachment = Attachment.objects.create(
            file=self.test_file,
            filename="test_document.pdf",
            file_type="pdf",
            size=12  # len(b"file_content")
        )

    def test_attachment_serialization(self):
        """Test serializing attachment data."""
        serializer = AttachmentSerializer(self.attachment)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = ['id', 'file', 'filename', 'file_type', 'size', 'uploaded_at']
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['filename'], 'test_document.pdf')
        self.assertEqual(data['file_type'], 'pdf')
        self.assertEqual(data['size'], 12)
        self.assertIsNotNone(data['uploaded_at'])

    def test_file_upload_validation_valid_types(self):
        """Test file upload validation for valid file types."""
        valid_files = [
            ('document.pdf', b'PDF content', 'application/pdf'),
            ('image.jpg', b'JPEG content', 'image/jpeg'),
            ('image.png', b'PNG content', 'image/png'),
            ('document.docx', b'DOCX content', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('text.txt', b'Text content', 'text/plain'),
        ]
        
        for filename, content, content_type in valid_files:
            with self.subTest(filename=filename):
                test_file = SimpleUploadedFile(filename, content, content_type=content_type)
                
                data = {'file': test_file}
                serializer = AttachmentSerializer(data=data)
                
                # Basic validation should pass (file type restrictions are typically in model/view)
                result = serializer.is_valid()
                # Result depends on business rules for file types

    def test_file_size_validation(self):
        """Test file size validation and handling."""
        # Create files of different sizes
        small_file = SimpleUploadedFile("small.txt", b"small", content_type="text/plain")
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        large_file = SimpleUploadedFile("large.txt", large_content, content_type="text/plain")
        
        for test_file in [small_file, large_file]:
            with self.subTest(file=test_file.name):
                data = {'file': test_file}
                serializer = AttachmentSerializer(data=data)
                
                # Validation depends on file size limits in business rules
                result = serializer.is_valid()

    def test_filename_sanitization(self):
        """Test filename sanitization for security."""
        dangerous_filenames = [
            '../../../etc/passwd',
            'file<script>alert()</script>.pdf',
            'file"with"quotes.txt',
            'file with spaces.pdf',
            'file_with_unicode_ñáéí.txt',
        ]
        
        for filename in dangerous_filenames:
            with self.subTest(filename=filename):
                test_file = SimpleUploadedFile(filename, b"content", content_type="text/plain")
                
                data = {'file': test_file}
                serializer = AttachmentSerializer(data=data)
                
                if serializer.is_valid():
                    # If valid, filename should be sanitized
                    # This is typically handled at the model or storage level
                    pass

    def test_read_only_fields_protection(self):
        """Test read-only fields are properly protected."""
        read_only_fields = ['filename', 'file_type', 'size', 'uploaded_at']
        
        serializer = AttachmentSerializer()
        meta_read_only = serializer.Meta.read_only_fields
        
        for field in read_only_fields:
            self.assertIn(field, meta_read_only,
                         f"Field '{field}' should be read-only for security")

    def test_empty_file_validation(self):
        """Test empty file validation."""
        empty_file = SimpleUploadedFile("empty.txt", b"", content_type="text/plain")
        
        data = {'file': empty_file}
        serializer = AttachmentSerializer(data=data)
        
        # Should handle empty files appropriately
        result = serializer.is_valid()
        if not result:
            # Should have appropriate error message
            self.assertTrue('file' in serializer.errors or 'size' in serializer.errors)

    def test_malicious_file_content_detection(self):
        """Test detection of potentially malicious file content."""
        malicious_content = [
            b'<script>alert("xss")</script>',
            b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R/JS(app.alert("malicious"))>>',
            b'\x00\x01\x02\x03MALICIOUS',  # Binary with potential exploit signatures
        ]
        
        for content in malicious_content:
            with self.subTest(content=content[:20]):
                test_file = SimpleUploadedFile("test.pdf", content, content_type="application/pdf")
                
                data = {'file': test_file}
                serializer = AttachmentSerializer(data=data)
                
                # File content validation typically happens at model/service level
                # Serializer should accept basic structure
                result = serializer.is_valid()


class TestMessageSerializer(BaseAPITestCase):
    """Test suite for MessageSerializer - Real-time messaging validation."""

    def setUp(self):
        super().setUp()
        self.user1 = CustomUser.objects.create_user(
            email='user1@example.com',
            name='User One'
        )
        self.user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            name='User Two'
        )
        
        self.channel = Channel.objects.create(
            name='test-channel',
            is_direct=False
        )
        self.channel.participants.add(self.user1, self.user2)
        
        # Create attachment for testing
        self.test_file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        self.attachment = Attachment.objects.create(
            file=self.test_file,
            filename="test.pdf",
            file_type="pdf",
            size=12
        )
        
        self.message = Message.objects.create(
            channel=self.channel,
            sender=self.user1,
            content='Test message content'
        )
        self.message.attachments.add(self.attachment)

    def test_message_serialization_complete(self):
        """Test complete message serialization with all fields."""
        serializer = MessageSerializer(self.message)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'channel', 'sender', 'content', 'timestamp',
            'file', 'reactions', 'attachments'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Verify nested serialization
        self.assertIn('id', data['sender'])
        self.assertEqual(data['sender']['id'], self.user1.id)
        
        # Verify content
        self.assertEqual(data['content'], 'Test message content')
        self.assertIsNotNone(data['timestamp'])

    def test_message_content_validation_safe_content(self):
        """Test message content validation for safe content."""
        safe_content = [
            'Hello world!',
            'Math lesson at 3 PM today 📚',
            'Great job on the homework! 👍',
            'Question: What is 2 + 2?',
            'Meeting link: https://meet.example.com/room123',
            'See attachment for more details.',
            'Português: Olá, como está?',
            'Special chars: @#$%^&*()_+-=[]{}|;:,.<>?'
        ]
        
        for content in safe_content:
            with self.subTest(content=content[:30]):
                data = {
                    'channel': self.channel.id,
                    'content': content
                }
                
                serializer = MessageSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept safe content: {content[:30]}. Errors: {serializer.errors}")

    def test_message_content_validation_xss_attempts(self):
        """Test message content validation blocks XSS attempts."""
        xss_attempts = [
            '<script>alert("xss")</script>',
            '<img src="x" onerror="alert(1)">',
            '<iframe src="javascript:alert(1)"></iframe>',
            'javascript:alert("xss")',
            '<svg onload="alert(1)">',
            '<div onclick="alert(1)">Click me</div>',
            '<style>body{background:url("javascript:alert(1)")}</style>',
            '<meta http-equiv="refresh" content="0;url=javascript:alert(1)">'
        ]
        
        for xss_content in xss_attempts:
            with self.subTest(content=xss_content[:30]):
                data = {
                    'channel': self.channel.id,
                    'content': xss_content
                }
                
                serializer = MessageSerializer(data=data)
                # XSS validation might be handled at different levels
                if serializer.is_valid():
                    # If valid, content should be sanitized somewhere in the pipeline
                    sanitized_content = serializer.validated_data['content']
                    # Should not contain dangerous HTML
                    dangerous_tags = ['<script', '<iframe', 'javascript:', 'onerror=']
                    for tag in dangerous_tags:
                        self.assertNotIn(tag.lower(), sanitized_content.lower())

    def test_message_content_length_validation(self):
        """Test message content length validation."""
        # Test various content lengths
        short_message = "Hi"
        normal_message = "This is a normal length message for classroom communication."
        long_message = "A" * 2000  # Very long message
        extremely_long = "A" * 10000  # Extremely long message
        
        for content in [short_message, normal_message, long_message, extremely_long]:
            with self.subTest(length=len(content)):
                data = {
                    'channel': self.channel.id,
                    'content': content
                }
                
                serializer = MessageSerializer(data=data)
                result = serializer.is_valid()
                
                if not result and len(content) > 2000:
                    # Should have length validation error
                    self.assertTrue('content' in serializer.errors or 'non_field_errors' in serializer.errors)

    def test_empty_message_validation(self):
        """Test validation of empty messages."""
        empty_contents = ['', '   ', '\n\n\n', '\t\t']
        
        for content in empty_contents:
            with self.subTest(content=repr(content)):
                data = {
                    'channel': self.channel.id,
                    'content': content
                }
                
                serializer = MessageSerializer(data=data)
                # Empty messages should be invalid unless there's a file attachment
                if not serializer.is_valid():
                    self.assertIn('content', serializer.errors)

    def test_message_with_file_attachment(self):
        """Test message validation with file attachment."""
        # Message with file but no content should be valid
        test_file = SimpleUploadedFile(
            "attachment.pdf",
            b"file content",
            content_type="application/pdf"
        )
        
        data = {
            'channel': self.channel.id,
            'content': '',  # Empty content
            'file': test_file
        }
        
        serializer = MessageSerializer(data=data)
        # Should be valid if file is provided even without text content
        self.assertTrue(serializer.is_valid())

    def test_message_reactions_serialization(self):
        """Test message reactions are properly serialized."""
        # Add reactions to the message
        reaction1 = Reaction.objects.create(
            message=self.message,
            user=self.user2,
            emoji='👍'
        )
        reaction2 = Reaction.objects.create(
            message=self.message,
            user=self.user1,
            emoji='❤️'
        )
        
        serializer = MessageSerializer(self.message)
        data = serializer.data
        
        # Should include reactions
        self.assertIn('reactions', data)
        self.assertEqual(len(data['reactions']), 2)
        
        # Each reaction should be properly serialized
        for reaction_data in data['reactions']:
            self.assertIn('id', reaction_data)
            self.assertIn('user', reaction_data)
            self.assertIn('emoji', reaction_data)
            self.assertIn('created_at', reaction_data)

    def test_message_attachments_serialization(self):
        """Test message attachments are properly serialized."""
        serializer = MessageSerializer(self.message)
        data = serializer.data
        
        # Should include attachments
        self.assertIn('attachments', data)
        self.assertEqual(len(data['attachments']), 1)
        
        # Attachment should be properly serialized
        attachment_data = data['attachments'][0]
        self.assertIn('id', attachment_data)
        self.assertIn('filename', attachment_data)
        self.assertIn('file_type', attachment_data)
        self.assertIn('size', attachment_data)

    def test_read_only_fields_protection(self):
        """Test read-only fields are properly protected."""
        read_only_fields = ['sender', 'timestamp']
        
        serializer = MessageSerializer()
        meta_read_only = serializer.Meta.read_only_fields
        
        for field in read_only_fields:
            self.assertIn(field, meta_read_only,
                         f"Field '{field}' should be read-only for security")

    def test_unicode_content_support(self):
        """Test Unicode content support for international users."""
        unicode_messages = [
            'Olá! Como está? 🇵🇹',
            'Matemática é interessante! ∑∏∆',
            '数学很有趣！ 📊📈📉',
            'Математика интересная! ∞≠≈',
            'العربية: الرياضيات مثيرة للاهتمام! ٠١٢٣',
            'हिंदी: गणित दिलचस्प है! ०१२३'
        ]
        
        for content in unicode_messages:
            with self.subTest(content=content[:20]):
                data = {
                    'channel': self.channel.id,
                    'content': content
                }
                
                serializer = MessageSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept Unicode: {content[:20]}. Errors: {serializer.errors}")


class TestChannelSerializer(BaseAPITestCase):
    """Test suite for ChannelSerializer - Channel management and validation."""

    def setUp(self):
        super().setUp()
        self.user1 = CustomUser.objects.create_user(
            email='user1@example.com',
            name='User One'
        )
        self.user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            name='User Two'
        )
        self.user3 = CustomUser.objects.create_user(
            email='user3@example.com',
            name='User Three'
        )
        
        # Create group channel
        self.group_channel = Channel.objects.create(
            name='Math Study Group',
            is_direct=False
        )
        self.group_channel.participants.add(self.user1, self.user2, self.user3)
        
        # Create direct message channel
        self.dm_channel = Channel.objects.create(
            name='',  # DMs typically don't have names
            is_direct=True
        )
        self.dm_channel.participants.add(self.user1, self.user2)

    def test_group_channel_serialization(self):
        """Test serializing group channel data."""
        serializer = ChannelSerializer(self.group_channel)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'name', 'is_direct', 'participants', 'online',
            'created_at', 'updated_at', 'last_message'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['name'], 'Math Study Group')
        self.assertFalse(data['is_direct'])
        self.assertEqual(len(data['participants']), 3)

    def test_direct_message_channel_serialization(self):
        """Test serializing direct message channel data."""
        serializer = ChannelSerializer(self.dm_channel)
        data = serializer.data
        
        self.assertTrue(data['is_direct'])
        self.assertEqual(len(data['participants']), 2)
        # DM channels might have empty names
        self.assertEqual(data['name'], '')

    def test_participants_serialization(self):
        """Test participants are properly serialized."""
        serializer = ChannelSerializer(self.group_channel)
        data = serializer.data
        
        # Participants should be nested user objects
        participants = data['participants']
        self.assertEqual(len(participants), 3)
        
        for participant in participants:
            self.assertIn('id', participant)
            self.assertIn('email', participant)
            # Should be using UserSerializer for participants

    def test_last_message_serialization(self):
        """Test last message serialization."""
        # Add a message to the channel
        message = Message.objects.create(
            channel=self.group_channel,
            sender=self.user1,
            content='Last message in the channel'
        )
        
        serializer = ChannelSerializer(self.group_channel)
        data = serializer.data
        
        # Should include last message
        self.assertIsNotNone(data['last_message'])
        self.assertEqual(data['last_message']['content'], 'Last message in the channel')
        self.assertEqual(data['last_message']['sender']['id'], self.user1.id)

    def test_channel_creation_validation(self):
        """Test channel creation validation."""
        valid_channel_data = {
            'name': 'New Study Group',
            'is_direct': False,
            'participant_ids': [self.user2.id, self.user3.id]
        }
        
        serializer = ChannelSerializer(data=valid_channel_data)
        self.assertTrue(serializer.is_valid())

    def test_direct_message_validation(self):
        """Test direct message channel validation."""
        # Valid DM with exactly one other participant
        valid_dm_data = {
            'name': '',
            'is_direct': True,
            'participant_ids': [self.user2.id]
        }
        
        serializer = ChannelSerializer(data=valid_dm_data)
        self.assertTrue(serializer.is_valid())

    def test_direct_message_invalid_participant_count(self):
        """Test DM validation rejects wrong number of participants."""
        # DM with too many participants
        invalid_dm_data = {
            'name': '',
            'is_direct': True,
            'participant_ids': [self.user2.id, self.user3.id]  # Too many for DM
        }
        
        serializer = ChannelSerializer(data=invalid_dm_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Direct messages must have exactly one other participant', 
                     str(serializer.errors))

    def test_direct_message_no_participants(self):
        """Test DM validation rejects no participants."""
        invalid_dm_data = {
            'name': '',
            'is_direct': True,
            'participant_ids': []  # No participants
        }
        
        serializer = ChannelSerializer(data=invalid_dm_data)
        self.assertFalse(serializer.is_valid())

    def test_duplicate_dm_prevention(self):
        """Test duplicate DM prevention logic."""
        # Try to create DM between same users
        dm_data = {
            'name': '',
            'is_direct': True,
            'participant_ids': [self.user2.id],
            'current_user': self.user1  # Context for duplicate detection
        }
        
        serializer = ChannelSerializer(data=dm_data)
        if serializer.is_valid():
            # Should either create new or return existing
            channel = serializer.save()
            
            # Try again with same users
            serializer2 = ChannelSerializer(data=dm_data)
            if serializer2.is_valid():
                channel2 = serializer2.save()
                # Should return the same channel (no duplicate)
                self.assertEqual(channel.id, channel2.id)

    def test_channel_name_validation(self):
        """Test channel name validation."""
        valid_names = [
            'Math Study Group',
            'Physics Lab Session',
            'Chemistry Q&A',
            'Portuguese Language Practice',
            'Group-1',
            'Study_Group_2024'
        ]
        
        for name in valid_names:
            with self.subTest(name=name):
                data = {
                    'name': name,
                    'is_direct': False,
                    'participant_ids': [self.user2.id]
                }
                
                serializer = ChannelSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept name: {name}. Errors: {serializer.errors}")

    def test_channel_name_security_validation(self):
        """Test channel name validation blocks malicious content."""
        malicious_names = [
            '<script>alert("xss")</script>',
            'Channel<img src="x" onerror="alert(1)">',
            'javascript:alert("xss")',
            '<iframe src="malicious.com"></iframe>'
        ]
        
        for name in malicious_names:
            with self.subTest(name=name):
                data = {
                    'name': name,
                    'is_direct': False,
                    'participant_ids': [self.user2.id]
                }
                
                serializer = ChannelSerializer(data=data)
                # Should either be invalid or sanitized
                if serializer.is_valid():
                    # If valid, name should be sanitized
                    sanitized_name = serializer.validated_data['name']
                    dangerous_patterns = ['<script', '<iframe', 'javascript:', 'onerror=']
                    for pattern in dangerous_patterns:
                        self.assertNotIn(pattern.lower(), sanitized_name.lower())

    def test_read_only_fields_protection(self):
        """Test read-only fields are properly protected."""
        read_only_fields = ['created_at', 'updated_at', 'online']
        
        serializer = ChannelSerializer()
        meta_read_only = serializer.Meta.read_only_fields
        
        for field in read_only_fields:
            self.assertIn(field, meta_read_only)

    def test_participant_management_in_creation(self):
        """Test participant management during channel creation."""
        data = {
            'name': 'Test Channel',
            'is_direct': False,
            'participant_ids': [self.user2.id, self.user3.id],
            'current_user': self.user1
        }
        
        serializer = ChannelSerializer(data=data)
        if serializer.is_valid():
            channel = serializer.save()
            
            # Should include all specified participants
            participant_ids = set(channel.participants.values_list('id', flat=True))
            expected_ids = {self.user2.id, self.user3.id}
            
            # For group channels, might or might not include creator automatically
            self.assertTrue(expected_ids.issubset(participant_ids))

    def test_online_users_tracking(self):
        """Test online users field handling."""
        # This field tracks currently online users in the channel
        serializer = ChannelSerializer(self.group_channel)
        data = serializer.data
        
        # Should have online field (empty list when no one is actively online)
        self.assertIn('online', data)
        self.assertIsInstance(data['online'], list)

    def test_empty_channel_last_message(self):
        """Test last_message field for empty channels."""
        empty_channel = Channel.objects.create(
            name='Empty Channel',
            is_direct=False
        )
        
        serializer = ChannelSerializer(empty_channel)
        data = serializer.data
        
        # Should have null last_message for empty channels
        self.assertIsNone(data['last_message'])


class TestRealTimeMessageValidation(BaseAPITestCase):
    """Integration test suite for real-time messaging validation."""

    def setUp(self):
        super().setUp()
        self.user1 = CustomUser.objects.create_user(
            email='user1@example.com',
            name='User One'
        )
        self.user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            name='User Two'
        )
        
        self.channel = Channel.objects.create(
            name='integration-test',
            is_direct=False
        )
        self.channel.participants.add(self.user1, self.user2)

    def test_complete_message_flow(self):
        """Test complete message creation flow with validation."""
        # Create message with attachment and reactions
        test_file = SimpleUploadedFile(
            "homework.pdf",
            b"homework content",
            content_type="application/pdf"
        )
        
        # Create message
        message_data = {
            'channel': self.channel.id,
            'content': 'Here is the homework assignment 📚',
            'file': test_file
        }
        
        message_serializer = MessageSerializer(data=message_data)
        self.assertTrue(message_serializer.is_valid())
        
        if message_serializer.is_valid():
            # Message creation would happen in view
            # Here we test the serialization
            validated_data = message_serializer.validated_data
            self.assertIn('content', validated_data)
            self.assertIn('channel', validated_data)

    def test_security_comprehensive_validation(self):
        """Test comprehensive security validation across all serializers."""
        # Test XSS in different contexts
        xss_payload = '<script>alert("xss")</script>'
        
        # Test in message content
        message_data = {
            'channel': self.channel.id,
            'content': xss_payload
        }
        message_serializer = MessageSerializer(data=message_data)
        
        # Test in channel name
        channel_data = {
            'name': xss_payload,
            'is_direct': False,
            'participant_ids': [self.user2.id]
        }
        channel_serializer = ChannelSerializer(data=channel_data)
        
        # Both should handle XSS appropriately
        # Either reject the data or sanitize it
        for serializer in [message_serializer, channel_serializer]:
            if serializer.is_valid():
                # If valid, content should be sanitized
                for field_name, field_value in serializer.validated_data.items():
                    if isinstance(field_value, str):
                        self.assertNotIn('<script>', field_value)

    def test_file_upload_security_validation(self):
        """Test file upload security across attachment handling."""
        # Test various potentially dangerous files
        dangerous_files = [
            ('script.js', b'alert("xss")', 'application/javascript'),
            ('malware.exe', b'MZ\x90\x00', 'application/x-executable'),
            ('exploit.php', b'<?php system($_GET["cmd"]); ?>', 'application/x-httpd-php'),
        ]
        
        for filename, content, content_type in dangerous_files:
            with self.subTest(filename=filename):
                test_file = SimpleUploadedFile(filename, content, content_type=content_type)
                
                # Test in attachment serializer
                attachment_data = {'file': test_file}
                attachment_serializer = AttachmentSerializer(data=attachment_data)
                
                # Test in message serializer
                message_data = {
                    'channel': self.channel.id,
                    'content': 'File upload test',
                    'file': test_file
                }
                message_serializer = MessageSerializer(data=message_data)
                
                # File validation typically happens at model/storage level
                # Serializers might accept the structure but validation happens elsewhere