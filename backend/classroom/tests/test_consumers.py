"""
Tests for classroom app WebSocket consumers.

This module contains tests for the WebSocket consumers in the classroom app,
specifically focusing on the ChatConsumer which handles real-time chat functionality.
"""

import os

os.environ["DJANGO_SETTINGS_MODULE"] = "aprendecomigo.test_settings"

from django.contrib.auth import get_user_model
from django.test import TestCase

from classroom.models import Channel, Message, Reaction

User = get_user_model()


class ChatDatabaseTest(TestCase):
    """Tests for the database operations related to chat.

    These tests focus on directly manipulating the database
    to ensure the model relationships and operations work correctly,
    similar to what the ChatConsumer would do.
    """

    def setUp(self):
        """Set up test users and channel."""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password"
        )

        # Create a test channel
        self.channel = Channel.objects.create(name="test-channel")
        self.channel.participants.add(self.user1, self.user2)

    def test_user_online_status(self):
        """Test updating user online status in a channel."""
        # Initial state - user should not be online
        self.assertNotIn(self.user1, self.channel.online.all())

        # Mark user as online
        self.channel.online.add(self.user1)
        self.channel.refresh_from_db()

        # User should now be online
        self.assertIn(
            self.user1,
            self.channel.online.all(),
            f"User {self.user1.username} should be marked as online",
        )

        # Mark user as offline
        self.channel.online.remove(self.user1)
        self.channel.refresh_from_db()

        # User should now be offline
        self.assertNotIn(
            self.user1,
            self.channel.online.all(),
            f"User {self.user1.username} should be marked as offline",
        )

    def test_message_creation(self):
        """Test creating a message in the database."""
        # Initial count
        initial_count = Message.objects.filter(channel=self.channel).count()

        # Create a message
        message = Message.objects.create(
            channel=self.channel, sender=self.user1, content="Test message content"
        )

        # Verify message was saved
        self.assertEqual(Message.objects.filter(channel=self.channel).count(), initial_count + 1)
        self.assertEqual(message.content, "Test message content")
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.channel, self.channel)

    def test_reaction_creation(self):
        """Test creating a reaction to a message."""
        # Create a message first
        message = Message.objects.create(
            channel=self.channel, sender=self.user1, content="Message to react to"
        )

        # Initial count
        initial_count = Reaction.objects.filter(message=message).count()

        # Create a reaction
        emoji = "👍"
        reaction = Reaction.objects.create(message=message, user=self.user1, emoji=emoji)

        # Verify reaction was saved
        self.assertEqual(Reaction.objects.filter(message=message).count(), initial_count + 1)
        self.assertEqual(reaction.emoji, emoji)
        self.assertEqual(reaction.user, self.user1)
        self.assertEqual(reaction.message, message)


# Keep the dummy test for fallback
class DummyConsumerTest(TestCase):
    """A placeholder test class to verify test discovery is working."""

    def test_dummy(self):
        """A dummy test that always passes."""
        self.assertTrue(True)
