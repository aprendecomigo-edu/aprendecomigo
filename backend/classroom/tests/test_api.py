"""
Tests for classroom app API endpoints.

This module contains tests for the REST API endpoints and serializers in the classroom app,
specifically focusing on:
- Channel API (listing, creation, details)
- Message API (sending, listing)
- Reaction API (adding, removing)
- User search API
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from classroom.models import Channel, Message, Reaction

User = get_user_model()


class ChannelAPITest(APITestCase):
    """Test cases for Channel API endpoints.

    Tests listing, creation, and retrieval of channels, with validation
    rules for direct messages and participant management.
    """

    def setUp(self):
        """Set up test users and authenticate client."""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password"
        )
        self.user3 = User.objects.create_user(
            username="user3", email="user3@example.com", password="password"
        )

        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

    def test_channel_list(self):
        """Test listing channels where user is a participant."""
        # Create a channel where user1 is a participant
        channel1 = Channel.objects.create(name="Test Channel 1")
        channel1.participants.add(self.user1)

        # Create a channel where user1 is not a participant
        channel2 = Channel.objects.create(name="Test Channel 2")
        channel2.participants.add(self.user2)

        # Create a direct message channel
        dm_channel = Channel.objects.create(name="", is_direct=True)
        dm_channel.participants.add(self.user1, self.user3)

        url = reverse("channel-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Handle paginated response
        if "results" in response.data:
            channels = response.data["results"]
        else:
            channels = response.data

        self.assertEqual(len(channels), 2)  # Only channels with user1 should be returned

        # Validate channel names
        channel_names = [channel["name"] for channel in channels]
        self.assertIn("Test Channel 1", channel_names)

    def test_channel_detail(self):
        """Test retrieving a single channel's details."""
        channel = Channel.objects.create(name="Test Channel")
        channel.participants.add(self.user1, self.user2)

        url = reverse("channel-detail", args=[channel.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Channel")
        self.assertEqual(len(response.data["participants"]), 2)

    def test_channel_creation_group(self):
        """Test creating a group channel with multiple participants."""
        url = reverse("channel-list")
        data = {
            "name": "New Group Channel",
            "is_direct": False,
            "participant_ids": [self.user2.id, self.user3.id],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Group Channel")

        # Verify participants include all three users (including creator)
        channel = Channel.objects.get(id=response.data["id"])
        self.assertEqual(channel.participants.count(), 3)
        self.assertIn(self.user1, channel.participants.all())
        self.assertIn(self.user2, channel.participants.all())
        self.assertIn(self.user3, channel.participants.all())

    def test_channel_creation_direct(self):
        """Test creating a direct message channel between two users."""
        url = reverse("channel-list")
        data = {"name": "", "is_direct": True, "participant_ids": [self.user2.id]}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_direct"])

        # Verify participants include exactly two users
        channel = Channel.objects.get(id=response.data["id"])
        self.assertEqual(channel.participants.count(), 2)
        self.assertIn(self.user1, channel.participants.all())
        self.assertIn(self.user2, channel.participants.all())

    def test_direct_message_validation(self):
        """Test validation for direct messages requiring exactly two participants."""
        url = reverse("channel-list")
        data = {"name": "", "is_direct": True, "participant_ids": [self.user2.id, self.user3.id]}

        response = self.client.post(url, data, format="json")

        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_dm_prevention(self):
        """Test that duplicate DMs return the existing channel instead of creating a new one."""
        url = reverse("channel-list")
        data = {"name": "", "is_direct": True, "participant_ids": [self.user2.id]}

        # Create first DM
        response1 = self.client.post(url, data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response1.data["is_direct"])
        dm1_id = response1.data["id"]

        # Try to create duplicate DM with same user
        response2 = self.client.post(url, data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response2.data["is_direct"])
        dm2_id = response2.data["id"]

        # Should return the same channel ID (duplicate prevention)
        self.assertEqual(
            dm1_id,
            dm2_id,
            "Duplicate DM should return existing channel instead of creating new one",
        )

        # Verify only one DM exists between these users
        dm_count = (
            Channel.objects.filter(is_direct=True, participants=self.user1)
            .filter(participants=self.user2)
            .count()
        )
        self.assertEqual(dm_count, 1, "Only one DM should exist between the same users")

    def test_unauthorized_channel_access(self):
        """Test that users cannot access channels they don't belong to."""
        # Create a channel for user2 only
        channel = Channel.objects.create(name="Private Channel")
        channel.participants.add(self.user2)

        url = reverse("channel-detail", args=[channel.id])
        response = self.client.get(url)

        # user1 should not be able to access user2's channel
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MessageAPITest(APITestCase):
    """Test cases for Message API endpoints.

    Tests sending, listing, and retrieving messages within channels,
    including file attachments.
    """

    def setUp(self):
        """Set up test users, channels, and messages."""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password"
        )

        # Create a channel with both users
        self.channel = Channel.objects.create(name="Test Channel")
        self.channel.participants.add(self.user1, self.user2)

        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

        # Create some test messages
        self.message1 = Message.objects.create(
            channel=self.channel, sender=self.user1, content="Message 1 from user1"
        )

        self.message2 = Message.objects.create(
            channel=self.channel, sender=self.user2, content="Message 2 from user2"
        )

    def test_message_list(self):
        """Test listing messages in a channel."""
        url = reverse("channel-messages", args=[self.channel.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Verify message content and senders
        contents = [msg["content"] for msg in response.data]
        self.assertIn("Message 1 from user1", contents)
        self.assertIn("Message 2 from user2", contents)

    def test_message_creation(self):
        """Test creating a new message in a channel."""
        url = reverse("channel-messages", args=[self.channel.id])
        data = {"content": "New test message"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "New test message")
        self.assertEqual(response.data["sender"]["username"], "user1")

        # Verify message was saved in database
        self.assertEqual(
            Message.objects.filter(channel=self.channel, content="New test message").count(), 1
        )

    def test_message_with_file(self):
        """Test sending a message with a file attachment."""
        url = reverse("channel-messages", args=[self.channel.id])

        # Create test file
        test_file = SimpleUploadedFile(
            "test_attachment.txt", b"Test file content", content_type="text/plain"
        )

        data = {"content": "Message with attachment", "file": test_file}

        response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "Message with attachment")
        self.assertIsNotNone(response.data["file"])

        # Verify file was saved
        message = Message.objects.get(id=response.data["id"])
        self.assertTrue(message.file.name.endswith("test_attachment.txt"))


class ReactionAPITest(APITestCase):
    """Test cases for Reaction API endpoints.

    Tests adding, listing, and removing emoji reactions to messages.
    """

    def setUp(self):
        """Set up test users, channel, and message for reaction tests."""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password"
        )

        # Create channel and message
        self.channel = Channel.objects.create(name="Test Channel")
        self.channel.participants.add(self.user1, self.user2)

        self.message = Message.objects.create(
            channel=self.channel, sender=self.user2, content="Test message for reactions"
        )

        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

    def test_add_reaction(self):
        """Test adding an emoji reaction to a message."""
        url = reverse("message-reactions", args=[self.message.id])
        data = {"emoji": "👍"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["emoji"], "👍")

        # Verify reaction was saved in database
        reaction = Reaction.objects.get(message=self.message, user=self.user1)
        self.assertEqual(reaction.emoji, "👍")

    def test_list_reactions(self):
        """Test listing all reactions for a message."""
        # Add some reactions first
        Reaction.objects.create(message=self.message, user=self.user1, emoji="👍")
        Reaction.objects.create(message=self.message, user=self.user2, emoji="❤️")

        url = reverse("message-reactions", args=[self.message.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Verify reaction data
        emojis = [reaction["emoji"] for reaction in response.data]
        self.assertIn("👍", emojis)
        self.assertIn("❤️", emojis)

    def test_delete_reaction(self):
        """Test removing a user's reaction from a message."""
        # Add a reaction first
        Reaction.objects.create(message=self.message, user=self.user1, emoji="👍")

        url = reverse("message-reactions", args=[self.message.id])
        data = {"emoji": "👍"}

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify reaction was deleted
        self.assertEqual(Reaction.objects.filter(message=self.message, user=self.user1).count(), 0)

    def test_delete_nonexistent_reaction(self):
        """Test attempting to delete a reaction that doesn't exist."""
        url = reverse("message-reactions", args=[self.message.id])
        data = {"emoji": "🎉"}  # No such reaction exists

        response = self.client.delete(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserSearchAPITest(APITestCase):
    """Test cases for User Search API endpoint.

    Tests searching for users by name or username for mention suggestions.
    """

    def setUp(self):
        """Set up test users with various names for search tests."""
        # Create test users
        self.user1 = User.objects.create_user(
            username="user1",
            email="john.smith@example.com",
            password="password",
            first_name="John",
            last_name="Smith",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="jane.doe@example.com",
            password="password",
            first_name="Jane",
            last_name="Doe",
        )
        self.user3 = User.objects.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password",
            first_name="John",
            last_name="Doe",
        )
        self.user4 = User.objects.create_user(
            username="smithy",
            email="alice.smith@example.com",
            password="password",
            first_name="Alice",
            last_name="Smith",
        )

        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

    def test_search_by_username(self):
        """Test searching users by username."""
        url = reverse("user-list") + "?search=john"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should find johndoe only
        self.assertEqual(response.data[0]["username"], "johndoe")

    def test_search_by_first_name(self):
        """Test searching users by first name."""
        url = reverse("user-list") + "?search=john"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should find user3 (johndoe), but not user1 (as it's the authenticated user)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["first_name"], "John")

    def test_search_by_last_name(self):
        """Test searching users by last name."""
        url = reverse("user-list") + "?search=smith"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should find smithy only (not user1)
        self.assertEqual(response.data[0]["last_name"], "Smith")

    def test_empty_search(self):
        """Test that empty search returns no results."""
        url = reverse("user-list") + "?search="
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Empty result set

    def test_multiple_results(self):
        """Test search that matches multiple users."""
        url = reverse("user-list") + "?search=doe"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should find user2 and user3

        usernames = [user["username"] for user in response.data]
        self.assertIn("user2", usernames)
        self.assertIn("johndoe", usernames)
