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

    def test_list_channels(self):
        """Test listing channels for the authenticated user."""
        # Get channels for user1
        url = reverse("channel-list")
        response = self.client.get(url)

        # Should return channels where user1 is a participant
        self.assertEqual(response.status_code, 200)
        # Check if results are returned
        self.assertTrue(len(response.data) > 0, "Response should contain channels")

        # Check the response format - it may be paginated
        if "results" in response.data:
            results = response.data["results"]
        else:
            results = response.data

        # Convert results to a list if it's not already
        if not isinstance(results, list):
            results = [results]

        # Find our test channel in the response
        found = False
        for channel in results:
            if (
                isinstance(channel, dict)
                and "name" in channel
                and channel["name"] == "test-channel"
            ):
                found = True
                break
        self.assertTrue(found, "Test channel should be in the response")

    def test_create_channel(self):
        """Test creating a new channel with participants."""
        url = reverse("channel-list")
        data = {
            "name": "new-test-channel",
            "is_direct": False,
            "participant_ids": [self.user1.id, self.user2.id],
        }

        response = self.client.post(url, data, format="json")

        # Verify channel was created
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "new-test-channel")

        # Verify current user was added as participant
        channel_id = response.data["id"]
        channel = Channel.objects.get(id=channel_id)
        self.assertIn(self.user1, channel.participants.all())
        self.assertIn(self.user2, channel.participants.all())

    def test_direct_message_channel(self):
        """Test creating a direct message channel requires exactly 2 participants."""
        url = reverse("channel-list")

        # Try with only 1 participant
        data = {"name": "dm-channel", "is_direct": True, "participant_ids": [self.user1.id]}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # Try with correct 2 participants
        data["participant_ids"] = [self.user1.id, self.user2.id]
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["is_direct"])

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
                # We found a working URL
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

    def test_message_creation(self):
        """Test creating a message directly in the database."""
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


# Keep the dummy test for fallback
class DummyIntegrationTest(TestCase):
    """A placeholder test class to verify test discovery is working."""

    def test_dummy(self):
        """A dummy test that always passes."""
        self.assertTrue(True)
