"""
Test fixtures and utilities for classroom tests.

This module provides reusable test data creation utilities and fixtures
for consistent testing across different test modules.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import School, SchoolMembership
from classroom.models import Attachment, Channel, Message, Reaction

User = get_user_model()


class TestDataFactory:
    """Factory class for creating test data consistently across tests."""

    @staticmethod
    def create_school(name="Test School", **kwargs):
        """Create a school with default or custom attributes."""
        defaults = {
            'description': f'{name} description',
            'address': f'{name} address',
            'contact_email': f'contact@{name.lower().replace(" ", "")}.com',
        }
        defaults.update(kwargs)
        return School.objects.create(name=name, **defaults)

    @staticmethod
    def create_user(username="testuser", email=None, **kwargs):
        """Create a user with default or custom attributes."""
        if email is None:
            email = f"{username}@example.com"

        defaults = {
            'first_name': username.title(),
            'last_name': 'User',
            'password': 'testpass123',
        }
        defaults.update(kwargs)
        return User.objects.create_user(username=username, email=email, **defaults)

    @staticmethod
    def create_school_membership(user, school, role="student"):
        """Create a school membership for a user."""
        return SchoolMembership.objects.create(user=user, school=school, role=role)

    @staticmethod
    def create_channel(name="Test Channel", is_direct=False, participants=None):
        """Create a channel with optional participants."""
        channel = Channel.objects.create(name=name, is_direct=is_direct)
        if participants:
            channel.participants.add(*participants)
        return channel

    @staticmethod
    def create_dm_channel(user1, user2):
        """Create a direct message channel between two users."""
        channel_name = f"DM_{min(user1.id, user2.id)}_{max(user1.id, user2.id)}"
        channel = Channel.objects.create(name=channel_name, is_direct=True)
        channel.participants.add(user1, user2)
        return channel

    @staticmethod
    def create_message(channel, sender, content="Test message", file=None):
        """Create a message in a channel."""
        return Message.objects.create(
            channel=channel,
            sender=sender,
            content=content,
            file=file
        )

    @staticmethod
    def create_reaction(message, user, emoji="👍"):
        """Create a reaction to a message."""
        return Reaction.objects.create(message=message, user=user, emoji=emoji)

    @staticmethod
    def create_attachment(message, filename="test.pdf", file_type="application/pdf", size=1024):
        """Create an attachment for a message."""
        test_file = SimpleUploadedFile(filename, b"file content", content_type=file_type)
        return Attachment.objects.create(
            message=message,
            file=test_file,
            filename=filename,
            file_type=file_type,
            size=size
        )

    @staticmethod
    def create_test_file(filename="test.pdf", content=b"test content", content_type="application/pdf"):
        """Create a test uploaded file."""
        return SimpleUploadedFile(filename, content, content_type=content_type)


class SchoolBasedTestMixin:
    """Mixin class providing school-based test setup for permission testing."""

    def setUp(self):
        """Set up school-based test environment."""
        super().setUp()

        # Create schools
        self.school1 = TestDataFactory.create_school("School One")
        self.school2 = TestDataFactory.create_school("School Two")

        # Create users
        self.teacher1 = TestDataFactory.create_user("teacher1")
        self.teacher2 = TestDataFactory.create_user("teacher2")
        self.student1 = TestDataFactory.create_user("student1")
        self.student2 = TestDataFactory.create_user("student2")
        self.outsider = TestDataFactory.create_user("outsider")

        # Create school memberships
        TestDataFactory.create_school_membership(self.teacher1, self.school1, "teacher")
        TestDataFactory.create_school_membership(self.student1, self.school1, "student")
        TestDataFactory.create_school_membership(self.teacher2, self.school2, "teacher")
        TestDataFactory.create_school_membership(self.student2, self.school2, "student")
        # outsider has no school membership

        # Create channels
        self.school1_channel = TestDataFactory.create_channel(
            "School 1 Channel",
            participants=[self.teacher1, self.student1]
        )
        self.school2_channel = TestDataFactory.create_channel(
            "School 2 Channel",
            participants=[self.teacher2, self.student2]
        )
        self.dm_channel = TestDataFactory.create_dm_channel(self.teacher1, self.student1)

        # Create messages
        self.message1 = TestDataFactory.create_message(
            self.school1_channel,
            self.teacher1,
            "Message from teacher1"
        )
        self.message2 = TestDataFactory.create_message(
            self.school1_channel,
            self.student1,
            "Message from student1"
        )

    def get_school1_users(self):
        """Get all users from school1."""
        return [self.teacher1, self.student1]

    def get_school2_users(self):
        """Get all users from school2."""
        return [self.teacher2, self.student2]

    def get_users_with_school_access(self, user):
        """Get users that the given user should be able to see (same schools)."""
        if user == self.teacher1 or user == self.student1:
            return [u for u in self.get_school1_users() if u != user]
        elif user == self.teacher2 or user == self.student2:
            return [u for u in self.get_school2_users() if u != user]
        else:
            return []  # Outsider sees no one


class MessageTestMixin:
    """Mixin for tests that need multiple messages for testing."""

    def create_test_messages(self, channel, count=10, sender=None):
        """Create multiple test messages for pagination testing."""
        if sender is None:
            sender = getattr(self, 'teacher1', None)
            if sender is None:
                raise ValueError("No sender provided and no default teacher1 available")

        messages = []
        for i in range(count):
            message = TestDataFactory.create_message(
                channel,
                sender,
                f"Test message {i+1}"
            )
            messages.append(message)
        return messages

    def create_messages_with_reactions(self, channel, sender, count=5):
        """Create messages with various reactions for testing."""
        messages = []
        emojis = ["👍", "❤️", "😂", "😮", "😢"]

        for i in range(count):
            message = TestDataFactory.create_message(
                channel,
                sender,
                f"Message with reactions {i+1}"
            )

            # Add reaction with corresponding emoji
            if i < len(emojis):
                TestDataFactory.create_reaction(message, sender, emojis[i])

            messages.append(message)

        return messages


class FileTestMixin:
    """Mixin for tests involving file uploads."""

    def create_test_files(self):
        """Create various test files for upload testing."""
        return {
            'pdf': TestDataFactory.create_test_file("document.pdf", b"PDF content", "application/pdf"),
            'image': TestDataFactory.create_test_file("image.jpg", b"JPEG content", "image/jpeg"),
            'doc': TestDataFactory.create_test_file("document.doc", b"DOC content", "application/msword"),
            'large': TestDataFactory.create_test_file("large.pdf", b"x" * 1024 * 1024, "application/pdf"),  # 1MB
            'invalid': TestDataFactory.create_test_file("script.exe", b"executable", "application/exe"),
        }

    def create_message_with_file(self, channel, sender, file_type='pdf'):
        """Create a message with a file attachment."""
        test_files = self.create_test_files()
        file = test_files.get(file_type, test_files['pdf'])

        return TestDataFactory.create_message(
            channel,
            sender,
            f"Message with {file_type} file",
            file=file
        )


class WebSocketTestMixin:
    """Mixin for WebSocket testing utilities."""

    def create_websocket_test_data(self):
        """Create test data specifically for WebSocket testing."""
        # Create user and channel
        self.ws_user = TestDataFactory.create_user("websocket_user")
        self.ws_channel = TestDataFactory.create_channel(
            "WebSocket Test Channel",
            participants=[self.ws_user]
        )

        # Create some messages for testing
        self.ws_messages = [
            TestDataFactory.create_message(self.ws_channel, self.ws_user, "WS Message 1"),
            TestDataFactory.create_message(self.ws_channel, self.ws_user, "WS Message 2"),
            TestDataFactory.create_message(self.ws_channel, self.ws_user, "WS Message 3"),
        ]

        return self.ws_user, self.ws_channel, self.ws_messages


class PermissionTestMixin:
    """Mixin for testing permission-based scenarios."""

    def assert_user_has_channel_access(self, user, channel):
        """Assert that user has access to channel."""
        self.assertIn(user, channel.participants.all())

    def assert_user_lacks_channel_access(self, user, channel):
        """Assert that user lacks access to channel."""
        self.assertNotIn(user, channel.participants.all())

    def assert_users_in_same_school(self, user1, user2):
        """Assert that two users belong to at least one common school."""
        user1_schools = set(SchoolMembership.objects.filter(user=user1).values_list('school_id', flat=True))
        user2_schools = set(SchoolMembership.objects.filter(user=user2).values_list('school_id', flat=True))
        self.assertTrue(bool(user1_schools & user2_schools), "Users should be in same school")

    def assert_users_in_different_schools(self, user1, user2):
        """Assert that two users belong to no common schools."""
        user1_schools = set(SchoolMembership.objects.filter(user=user1).values_list('school_id', flat=True))
        user2_schools = set(SchoolMembership.objects.filter(user=user2).values_list('school_id', flat=True))
        self.assertFalse(bool(user1_schools & user2_schools), "Users should be in different schools")


# Convenience functions for quick test data creation
def create_test_school_environment():
    """Create a complete test environment with schools, users, and channels."""
    factory = TestDataFactory()

    # Schools
    school1 = factory.create_school("Test High School")
    school2 = factory.create_school("Community College")

    # Users
    teacher1 = factory.create_user("teacher1")
    student1 = factory.create_user("student1")
    teacher2 = factory.create_user("teacher2")
    student2 = factory.create_user("student2")

    # School memberships
    factory.create_school_membership(teacher1, school1, "teacher")
    factory.create_school_membership(student1, school1, "student")
    factory.create_school_membership(teacher2, school2, "teacher")
    factory.create_school_membership(student2, school2, "student")

    # Channels
    channel1 = factory.create_channel("School 1 General", participants=[teacher1, student1])
    channel2 = factory.create_channel("School 2 General", participants=[teacher2, student2])
    dm_channel = factory.create_dm_channel(teacher1, student1)

    return {
        'schools': [school1, school2],
        'users': [teacher1, student1, teacher2, student2],
        'channels': [channel1, channel2, dm_channel],
        'school1': {'school': school1, 'users': [teacher1, student1], 'channel': channel1},
        'school2': {'school': school2, 'users': [teacher2, student2], 'channel': channel2},
    }
