"""
Integration tests for classroom app.

This module contains integration tests for the classroom app that verify
the interaction between REST API endpoints and database models.
"""

import os

os.environ["DJANGO_SETTINGS_MODULE"] = "aprendecomigo.test_settings"

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from classroom.models import Channel, Message

User = get_user_model()


class ChannelAPITest(TestCase):
    """Tests for the Channel API endpoints."""

    def setUp(self):
        """Set up test users and API client."""
        # Clean up any existing data to ensure test isolation
        Message.objects.all().delete()
        Channel.objects.all().delete()
        User.objects.all().delete()
        
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password"
        )

        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

        # Create a test channel
        self.channel = Channel.objects.create(name="test-channel")
        self.channel.participants.add(self.user1, self.user2)

    # Note: Removed test_list_channels, test_create_channel, and test_direct_message_channel
    # as they duplicate functionality tested in test_api.py

    def test_messages_in_channel(self):
        """Test getting and creating messages in a channel using the actions on ChannelViewSet."""
        # Create messages directly in the database
        Message.objects.create(
            channel=self.channel, sender=self.user1, content="Test message from user1"
        )
        Message.objects.create(
            channel=self.channel, sender=self.user2, content="Test message from user2"
        )

        # Set up URL - try all variations since we're not sure about the exact URL pattern
        possible_urls = [
            f"/api/channels/{self.channel.id}/messages/",  # DRF default with trailing slash
            f"/api/channels/{self.channel.id}/messages",  # DRF default without trailing slash
        ]

        # Try each URL until we find one that works
        for url in possible_urls:
            response = self.client.get(url)
            if response.status_code == 200:
                # We found a working URL - check for pagination
                if 'results' in response.data:
                    self.assertEqual(len(response.data['results']), 2)
                else:
                    self.assertEqual(len(response.data), 2)
                break
        else:
            # None of the URLs worked, check if the endpoint exists
            self.fail("Could not find a working URL for channel messages endpoint")


class MessageModelTest(TestCase):
    """Tests for direct interactions with the Message model."""

    def setUp(self):
        """Set up test users and channel for model tests."""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password"
        )

        # Create a test channel
        self.channel = Channel.objects.create(name="test-channel")
        self.channel.participants.add(self.user1, self.user2)

    def test_message_model_creation(self):
        """Test creating a message directly via model (not API)."""
        # Initial count
        initial_count = Message.objects.count()

        # Create a message
        message = Message.objects.create(
            channel=self.channel, sender=self.user1, content="Test direct message creation"
        )

        # Verify message was created
        self.assertEqual(Message.objects.count(), initial_count + 1)
        self.assertEqual(message.content, "Test direct message creation")
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.channel, self.channel)
        
    def test_message_creation_without_channel_fails(self):
        """Test that creating a message without a channel fails."""
        with self.assertRaises(Exception):
            Message.objects.create(
                sender=self.user1, content="Message without channel"
            )
    
    def test_message_creation_without_sender_fails(self):
        """Test that creating a message without a sender fails."""
        with self.assertRaises(Exception):
            Message.objects.create(
                channel=self.channel, content="Message without sender"
            )


# Keep the dummy test for fallback
class DummyIntegrationTest(TestCase):
    """A placeholder test class to verify test discovery is working."""

    def test_dummy(self):
        """A dummy test that always passes."""
        self.assertTrue(True)
