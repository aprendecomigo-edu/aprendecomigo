"""
API endpoint tests for classroom app.

These tests validate the REST API contracts for real-time messaging functionality,
focusing on HTTP responses, status codes, authentication, and data validation.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from classroom.models import Channel, Message, Reaction

User = get_user_model()


class ChannelAPITest(APITestCase):
    """Test Channel API endpoints - channel management and messaging."""

    def setUp(self):
        """Set up test users and authentication."""
        self.user1 = User.objects.create_user(username="user1", email="user1@example.com", password="password")
        self.user2 = User.objects.create_user(username="user2", email="user2@example.com", password="password")
        self.user3 = User.objects.create_user(username="user3", email="user3@example.com", password="password")
        self.client.force_authenticate(user=self.user1)

    def test_channel_list_authentication_required(self):
        """Test that channel list requires authentication."""
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("channel-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_channel_list_returns_user_channels_only(self):
        """Test that user can only see channels where they are participants."""
        # Create channels
        channel1 = Channel.objects.create(name="User1 Channel")
        channel1.participants.add(self.user1)

        channel2 = Channel.objects.create(name="Other User Channel")
        channel2.participants.add(self.user2)

        response = self.client.get(reverse("channel-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("results", response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "User1 Channel")

    def test_channel_detail_access_control(self):
        """Test channel detail access is restricted to participants."""
        # Create channel for user2 only
        channel = Channel.objects.create(name="Private Channel")
        channel.participants.add(self.user2)

        response = self.client.get(reverse("channel-detail", args=[channel.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_group_channel_success(self):
        """Test creating a group channel with multiple participants."""
        data = {
            "name": "Math Study Group",
            "is_direct": False,
            "participant_ids": [self.user2.id, self.user3.id],
        }

        response = self.client.post(reverse("channel-list"), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Math Study Group")
        self.assertFalse(response.data["is_direct"])

        # Verify participants in database
        channel = Channel.objects.get(id=response.data["id"])
        participant_ids = set(channel.participants.values_list("id", flat=True))
        self.assertIn(self.user1.id, participant_ids)  # Creator added
        self.assertIn(self.user2.id, participant_ids)
        self.assertIn(self.user3.id, participant_ids)

    def test_create_direct_message_success(self):
        """Test creating a direct message channel."""
        data = {
            "name": "",
            "is_direct": True,
            "participant_ids": [self.user2.id],
        }

        response = self.client.post(reverse("channel-list"), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_direct"])

        # Verify exactly 2 participants
        channel = Channel.objects.get(id=response.data["id"])
        self.assertEqual(channel.participants.count(), 2)

    def test_create_direct_message_validation_error(self):
        """Test DM creation rejects invalid participant count."""
        data = {
            "name": "",
            "is_direct": True,
            "participant_ids": [self.user2.id, self.user3.id],  # Too many
        }

        response = self.client.post(reverse("channel-list"), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Direct messages must have exactly one other participant", str(response.data))

    def test_duplicate_dm_returns_existing(self):
        """Test that duplicate DM requests return the existing channel."""
        data = {
            "name": "",
            "is_direct": True,
            "participant_ids": [self.user2.id],
        }

        # Create first DM
        response1 = self.client.post(reverse("channel-list"), data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        first_id = response1.data["id"]

        # Try to create duplicate
        response2 = self.client.post(reverse("channel-list"), data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        second_id = response2.data["id"]

        self.assertEqual(first_id, second_id)


class ChannelMessagesAPITest(APITestCase):
    """Test Channel messages action endpoint."""

    def setUp(self):
        """Set up test data for message testing."""
        self.user1 = User.objects.create_user(username="user1", email="user1@example.com", password="password")
        self.user2 = User.objects.create_user(username="user2", email="user2@example.com", password="password")

        self.channel = Channel.objects.create(name="Test Channel")
        self.channel.participants.add(self.user1, self.user2)

        self.client.force_authenticate(user=self.user1)

    def test_channel_messages_authentication_required(self):
        """Test that listing messages requires authentication."""
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("channel-messages", args=[self.channel.id]))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_channel_messages_list_success(self):
        """Test listing messages in a channel."""
        Message.objects.create(channel=self.channel, sender=self.user1, content="Test message")

        response = self.client.get(reverse("channel-messages", args=[self.channel.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("results", response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["content"], "Test message")
        self.assertEqual(data[0]["sender"]["id"], self.user1.id)

    def test_send_message_success(self):
        """Test sending a message to a channel."""
        data = {"content": "Hello world!"}

        response = self.client.post(reverse("channel-send-message", args=[self.channel.id]), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "Hello world!")

        # Verify message was created in database
        message = Message.objects.get(id=response.data["id"])
        self.assertEqual(message.content, "Hello world!")
        self.assertEqual(message.sender, self.user1)

    def test_send_message_with_file_attachment(self):
        """Test sending a message with file attachment."""
        test_file = SimpleUploadedFile("test.pdf", b"file content", content_type="application/pdf")
        data = {"content": "Check this file", "file": test_file}

        response = self.client.post(reverse("channel-send-message", args=[self.channel.id]), data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "Check this file")

        # Verify file was attached
        message = Message.objects.get(id=response.data["id"])
        self.assertTrue(message.file)

    def test_send_message_non_participant_forbidden(self):
        """Test that non-participants cannot send messages."""
        user3 = User.objects.create_user(username="user3", email="user3@example.com", password="password")
        self.client.force_authenticate(user=user3)

        data = {"content": "Unauthorized message"}
        response = self.client.post(reverse("channel-send-message", args=[self.channel.id]), data, format="json")

        # Non-participants get 404 (not found) due to queryset filtering
        # This is actually better for security - don't reveal channel existence
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MessageReactionsAPITest(APITestCase):
    """Test Message reactions API endpoints."""

    def setUp(self):
        """Set up test data for reaction testing."""
        self.user1 = User.objects.create_user(username="user1", email="user1@example.com", password="password")
        self.user2 = User.objects.create_user(username="user2", email="user2@example.com", password="password")

        self.channel = Channel.objects.create(name="Test Channel")
        self.channel.participants.add(self.user1, self.user2)

        self.message = Message.objects.create(channel=self.channel, sender=self.user2, content="React to this!")

        self.client.force_authenticate(user=self.user1)

    def test_list_message_reactions_success(self):
        """Test listing reactions for a message."""
        Reaction.objects.create(message=self.message, user=self.user1, emoji="👍")

        response = self.client.get(reverse("message-reactions", args=[self.message.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["emoji"], "👍")
        self.assertEqual(response.data[0]["user"]["id"], self.user1.id)

    def test_add_reaction_success(self):
        """Test adding a reaction to a message."""
        data = {"emoji": "❤️"}

        response = self.client.post(reverse("message-reactions", args=[self.message.id]), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["emoji"], "❤️")

        # Verify reaction was created
        reaction = Reaction.objects.get(message=self.message, user=self.user1)
        self.assertEqual(reaction.emoji, "❤️")

    def test_remove_reaction_success(self):
        """Test removing a reaction from a message."""
        Reaction.objects.create(message=self.message, user=self.user1, emoji="👍")

        data = {"emoji": "👍"}
        response = self.client.delete(reverse("message-reactions", args=[self.message.id]), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify reaction was deleted
        self.assertFalse(Reaction.objects.filter(message=self.message, user=self.user1, emoji="👍").exists())

    def test_remove_nonexistent_reaction_not_found(self):
        """Test removing a reaction that doesn't exist."""
        data = {"emoji": "👎"}

        response = self.client.delete(reverse("message-reactions", args=[self.message.id]), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Reaction not found", str(response.data))


class UserSearchAPITest(APITestCase):
    """Test User search API endpoint."""

    def setUp(self):
        """Set up test users for search testing."""
        self.user1 = User.objects.create_user(
            username="john_doe",
            email="john@example.com",
            password="password",
            first_name="John",
            last_name="Doe",
        )
        self.user2 = User.objects.create_user(
            username="jane_smith",
            email="jane@example.com",
            password="password",
            first_name="Jane",
            last_name="Smith",
        )
        self.client.force_authenticate(user=self.user1)

    def test_user_search_authentication_required(self):
        """Test that user search requires authentication."""
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("user-list") + "?search=john")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_search_by_username(self):
        """Test searching users by username."""
        response = self.client.get(reverse("user-list") + "?search=jane")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("results", response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["username"], "jane_smith")

    def test_user_search_by_first_name(self):
        """Test searching users by first name."""
        response = self.client.get(reverse("user-list") + "?search=Jane")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("results", response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["first_name"], "Jane")

    def test_user_search_excludes_current_user(self):
        """Test that search results exclude the current user."""
        response = self.client.get(reverse("user-list") + "?search=john")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("results", response.data)
        # Should not include current user (john_doe)
        user_ids = [user["id"] for user in data]
        self.assertNotIn(self.user1.id, user_ids)

    def test_user_search_empty_query(self):
        """Test search with empty query returns no results."""
        response = self.client.get(reverse("user-list") + "?search=")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("results", response.data)
        self.assertEqual(len(data), 0)

    def test_user_search_response_structure(self):
        """Test that user search returns proper data structure."""
        response = self.client.get(reverse("user-list") + "?search=jane")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("results", response.data)

        if data:
            user_data = data[0]
            expected_fields = ["id", "username", "email", "first_name", "last_name"]
            for field in expected_fields:
                self.assertIn(field, user_data)
