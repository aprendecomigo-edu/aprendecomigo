"""
Comprehensive tests for classroom chat views.

This module tests all chat-related views with focus on:
- School-based permission testing
- HTMX integration and response formats
- File upload functionality
- Pagination and message loading
- JSON API responses
- Error handling and edge cases

Tests cover both authenticated and unauthenticated access patterns.
"""

import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from waffle.testutils import override_switch

from accounts.models import School, SchoolMembership
from classroom.models import Channel, Message, Reaction
from tests.test_waffle_switches import get_test_password

User = get_user_model()


class BaseViewTest(TestCase):
    """Base test class with common setup for school-based testing."""

    def setUp(self):
        """Set up test data for view tests with school-based permissions."""
        # Create schools
        self.school1 = School.objects.create(name="Test School 1", description="First test school")
        self.school2 = School.objects.create(name="Test School 2", description="Second test school")

        # Create users
        self.user1 = User.objects.create_user(username="user1", email="user1@example.com", password=get_test_password())
        self.user2 = User.objects.create_user(username="user2", email="user2@example.com", password=get_test_password())
        self.user3 = User.objects.create_user(username="user3", email="user3@example.com", password=get_test_password())

        # Create school memberships (user1 and user2 in school1, user3 in school2)
        SchoolMembership.objects.create(user=self.user1, school=self.school1, role="teacher")
        SchoolMembership.objects.create(user=self.user2, school=self.school1, role="student")
        SchoolMembership.objects.create(user=self.user3, school=self.school2, role="teacher")

        # Create test channels
        self.channel1 = Channel.objects.create(name="School 1 Channel", is_direct=False)
        self.channel1.participants.add(self.user1, self.user2)

        self.dm_channel = Channel.objects.create(name="DM_1_2", is_direct=True)
        self.dm_channel.participants.add(self.user1, self.user2)

        # Create test messages
        self.message1 = Message.objects.create(
            channel=self.channel1, sender=self.user1, content="Test message from user1"
        )
        self.message2 = Message.objects.create(
            channel=self.channel1, sender=self.user2, content="Test message from user2"
        )

        self.client = Client()

    def login_user(self, user):
        """Helper method to log in a user."""
        self.client.force_login(user)

    def assertJSONResponse(self, response, expected_keys=None):
        """Helper to assert JSON response structure."""
        self.assertEqual(response["Content-Type"], "application/json")
        if expected_keys:
            data = json.loads(response.content)
            for key in expected_keys:
                self.assertIn(key, data)


@override_switch("chat_feature", active=True)
class ChatViewTest(BaseViewTest):
    """Test the main ChatView (HTMX-enabled chat interface)."""

    def test_chat_view_requires_authentication(self):
        """Test that chat view requires user authentication."""
        response = self.client.get(reverse("chat"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_chat_view_renders_with_channels(self):
        """Test that authenticated user sees their channels."""
        self.login_user(self.user1)

        response = self.client.get(reverse("chat"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chat - Aprende Comigo")
        self.assertContains(response, self.channel1.name)

    def test_chat_view_send_message_htmx(self):
        """Test sending message via HTMX POST."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("chat"),
            {"action": "send_message", "channel_id": self.channel1.id, "content": "HTMX test message"},
            headers={"hx-request": "true"},
        )

        self.assertEqual(response.status_code, 200)

        # Verify message was created
        message = Message.objects.filter(content="HTMX test message").first()
        self.assertIsNotNone(message)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.channel, self.channel1)

    def test_chat_view_load_channel_htmx(self):
        """Test loading channel messages via HTMX."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("chat"), {"action": "load_channel", "channel_id": self.channel1.id}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.message1.content)
        self.assertContains(response, self.message2.content)

    def test_chat_view_search_users_htmx(self):
        """Test user search via HTMX."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("chat"), {"action": "search_users", "search": "user2"}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.username)
        self.assertNotContains(response, self.user3.username)  # Different school

    def test_chat_view_create_dm_channel_htmx(self):
        """Test creating DM channel via HTMX."""
        self.login_user(self.user1)

        # Create new user in same school
        new_user = User.objects.create_user(username="newuser", email="new@example.com", password="pass")
        SchoolMembership.objects.create(user=new_user, school=self.school1, role="student")

        response = self.client.post(
            reverse("chat"), {"action": "create_channel", "participant_id": new_user.id}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)

        # Verify DM channel was created
        dm_channel = (
            Channel.objects.filter(is_direct=True, participants=self.user1).filter(participants=new_user).first()
        )
        self.assertIsNotNone(dm_channel)

    def test_chat_view_invalid_action(self):
        """Test handling of invalid action."""
        self.login_user(self.user1)

        response = self.client.post(reverse("chat"), {"action": "invalid_action"})

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)


@override_switch("chat_feature", active=True)
class ChatChannelsViewTest(BaseViewTest):
    """Test ChatChannelsView for listing and creating channels."""

    def test_get_channels_requires_authentication(self):
        """Test that getting channels requires authentication."""
        response = self.client.get(reverse("chat_channels"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_channels_returns_user_channels(self):
        """Test that authenticated user gets their channels."""
        self.login_user(self.user1)

        response = self.client.get(reverse("chat_channels"))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn("channels", data)
        self.assertGreater(len(data["channels"]), 0)

        # Check that user1's channels are included
        channel_names = [ch["name"] for ch in data["channels"]]
        self.assertIn(self.channel1.name, channel_names)

    def test_get_channels_excludes_other_user_channels(self):
        """Test that user only sees channels they participate in."""
        # Create channel with only user3
        other_channel = Channel.objects.create(name="Other School Channel", is_direct=False)
        other_channel.participants.add(self.user3)

        self.login_user(self.user1)
        response = self.client.get(reverse("chat_channels"))

        data = json.loads(response.content)
        channel_names = [ch["name"] for ch in data["channels"]]
        self.assertNotIn(other_channel.name, channel_names)

    def test_create_direct_message_channel(self):
        """Test creating a direct message channel."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("chat_channels"),
            json.dumps({"is_direct": True, "participant_ids": [self.user2.id]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["is_direct"])
        self.assertEqual(len(data["participants"]), 2)

    def test_create_group_channel(self):
        """Test creating a group channel."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("chat_channels"),
            json.dumps({"is_direct": False, "name": "New Group Channel", "participant_ids": [self.user2.id]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertFalse(data["is_direct"])
        self.assertEqual(data["name"], "New Group Channel")

    def test_create_channel_school_permission_enforcement(self):
        """Test that users can only create channels with users from same schools."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("chat_channels"),
            json.dumps(
                {
                    "is_direct": True,
                    "participant_ids": [self.user3.id],  # Different school
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("Invalid participant", data["error"])

    def test_create_duplicate_dm_returns_existing(self):
        """Test that creating duplicate DM returns existing channel."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("chat_channels"),
            json.dumps(
                {
                    "is_direct": True,
                    "participant_ids": [self.user2.id],  # DM already exists
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["id"], self.dm_channel.id)

    def test_create_channel_invalid_json(self):
        """Test error handling for invalid JSON."""
        self.login_user(self.user1)

        response = self.client.post(reverse("chat_channels"), "invalid json", content_type="application/json")

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("Invalid JSON", data["error"])


@override_switch("chat_feature", active=True)
class ChatMessagesViewTest(BaseViewTest):
    """Test ChatMessagesView for retrieving and sending messages."""

    def test_get_messages_requires_authentication(self):
        """Test that getting messages requires authentication."""
        response = self.client.get(reverse("chat_messages", kwargs={"channel_id": self.channel1.id}))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_messages_requires_channel_participation(self):
        """Test that user must be channel participant to get messages."""
        # Create channel without user3
        private_channel = Channel.objects.create(name="Private Channel", is_direct=False)
        private_channel.participants.add(self.user1, self.user2)

        self.login_user(self.user3)
        response = self.client.get(reverse("chat_messages", kwargs={"channel_id": private_channel.id}))
        self.assertEqual(response.status_code, 404)

    def test_get_messages_returns_paginated_messages(self):
        """Test that messages are returned with pagination."""
        self.login_user(self.user1)

        response = self.client.get(reverse("chat_messages", kwargs={"channel_id": self.channel1.id}))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn("messages", data)
        self.assertIn("has_more", data)
        self.assertIn("page", data)
        self.assertIn("total_pages", data)

        # Check messages are present
        self.assertGreater(len(data["messages"]), 0)

    def test_get_messages_with_pagination(self):
        """Test message pagination functionality."""
        # Create many messages for pagination testing
        for i in range(60):  # More than page size of 50
            Message.objects.create(channel=self.channel1, sender=self.user1, content=f"Message {i}")

        self.login_user(self.user1)

        # Test first page
        response = self.client.get(reverse("chat_messages", kwargs={"channel_id": self.channel1.id}), {"page": 1})

        data = json.loads(response.content)
        self.assertTrue(data["has_more"])
        self.assertEqual(data["page"], 1)
        self.assertEqual(len(data["messages"]), 50)  # Page size

        # Test second page
        response = self.client.get(reverse("chat_messages", kwargs={"channel_id": self.channel1.id}), {"page": 2})

        data = json.loads(response.content)
        self.assertFalse(data["has_more"])
        self.assertEqual(data["page"], 2)
        self.assertGreater(len(data["messages"]), 0)

    def test_send_message_text_only(self):
        """Test sending text-only message."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("chat_messages", kwargs={"channel_id": self.channel1.id}),
            json.dumps({"content": "New test message"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["content"], "New test message")
        self.assertEqual(data["sender"]["id"], self.user1.id)

    def test_send_message_with_file(self):
        """Test sending message with file attachment."""
        self.login_user(self.user1)

        test_file = SimpleUploadedFile("test.pdf", b"PDF content", content_type="application/pdf")

        response = self.client.post(
            reverse("chat_messages", kwargs={"channel_id": self.channel1.id}),
            {"content": "Message with file", "file": test_file},
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["content"], "Message with file")
        self.assertIsNotNone(data["file"])

    def test_send_message_file_only(self):
        """Test sending file-only message (no text content)."""
        self.login_user(self.user1)

        test_file = SimpleUploadedFile("image.jpg", b"Image content", content_type="image/jpeg")

        response = self.client.post(
            reverse("chat_messages", kwargs={"channel_id": self.channel1.id}), {"content": "", "file": test_file}
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["content"], "")
        self.assertIsNotNone(data["file"])

    def test_send_empty_message_fails(self):
        """Test that empty message (no content, no file) fails."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("chat_messages", kwargs={"channel_id": self.channel1.id}),
            json.dumps({"content": ""}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("required", data["error"])

    def test_send_message_channel_participation_required(self):
        """Test that user must be channel participant to send messages."""
        # Create channel without user3
        private_channel = Channel.objects.create(name="Private Channel", is_direct=False)
        private_channel.participants.add(self.user1, self.user2)

        self.login_user(self.user3)
        response = self.client.post(
            reverse("chat_messages", kwargs={"channel_id": private_channel.id}),
            json.dumps({"content": "Unauthorized message"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)


@override_switch("chat_feature", active=True)
class ChatUserSearchViewTest(BaseViewTest):
    """Test ChatUserSearchView for searching users within same schools."""

    def test_user_search_requires_authentication(self):
        """Test that user search requires authentication."""
        response = self.client.get(reverse("chat_user_search"), {"search": "test"})
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_user_search_returns_school_users_only(self):
        """Test that search only returns users from same schools."""
        self.login_user(self.user1)

        response = self.client.get(reverse("chat_user_search"), {"search": "user"})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        usernames = [user["username"] for user in data["users"]]

        self.assertIn("user2", usernames)  # Same school
        self.assertNotIn("user3", usernames)  # Different school
        self.assertNotIn("user1", usernames)  # Current user excluded

    def test_user_search_minimum_query_length(self):
        """Test that search requires minimum query length."""
        self.login_user(self.user1)

        response = self.client.get(reverse("chat_user_search"), {"search": "u"})  # Too short
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data["users"]), 0)

    def test_user_search_filters_by_name_email_username(self):
        """Test that search filters by name, email, and username."""
        # Create user with specific attributes for testing
        test_user = User.objects.create_user(
            username="searchtest", email="search@example.com", first_name="Search", last_name="User", password="pass"
        )
        SchoolMembership.objects.create(user=test_user, school=self.school1, role="student")

        self.login_user(self.user1)

        # Search by username
        response = self.client.get(reverse("chat_user_search"), {"search": "searchtest"})
        data = json.loads(response.content)
        self.assertEqual(len(data["users"]), 1)
        self.assertEqual(data["users"][0]["username"], "searchtest")

        # Search by email
        response = self.client.get(reverse("chat_user_search"), {"search": "search@"})
        data = json.loads(response.content)
        self.assertEqual(len(data["users"]), 1)

        # Search by first name
        response = self.client.get(reverse("chat_user_search"), {"search": "Search"})
        data = json.loads(response.content)
        self.assertEqual(len(data["users"]), 1)

    def test_user_search_case_insensitive(self):
        """Test that search is case insensitive."""
        self.login_user(self.user1)

        response = self.client.get(reverse("chat_user_search"), {"search": "USER2"})
        data = json.loads(response.content)

        usernames = [user["username"] for user in data["users"]]
        self.assertIn("user2", usernames)

    def test_user_search_excludes_inactive_users(self):
        """Test that search excludes inactive users."""
        # Create inactive user
        inactive_user = User.objects.create_user(
            username="inactive", email="inactive@example.com", password="pass", is_active=False
        )
        SchoolMembership.objects.create(user=inactive_user, school=self.school1, role="student")

        self.login_user(self.user1)

        response = self.client.get(reverse("chat_user_search"), {"search": "inactive"})
        data = json.loads(response.content)

        usernames = [user["username"] for user in data["users"]]
        self.assertNotIn("inactive", usernames)


@override_switch("chat_feature", active=True)
class MessageReactionsViewTest(BaseViewTest):
    """Test MessageReactionsView for managing message reactions."""

    def test_get_reactions_requires_authentication(self):
        """Test that getting reactions requires authentication."""
        response = self.client.get(reverse("message_reactions", kwargs={"message_id": self.message1.id}))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_reactions_requires_channel_access(self):
        """Test that user must have channel access to get reactions."""
        self.login_user(self.user3)  # Different school

        response = self.client.get(reverse("message_reactions", kwargs={"message_id": self.message1.id}))
        self.assertEqual(response.status_code, 404)

    def test_get_reactions_returns_message_reactions(self):
        """Test that reactions are returned for accessible messages."""
        # Create reactions
        reaction1 = Reaction.objects.create(message=self.message1, user=self.user1, emoji="👍")
        reaction2 = Reaction.objects.create(message=self.message1, user=self.user2, emoji="❤️")

        self.login_user(self.user1)

        response = self.client.get(reverse("message_reactions", kwargs={"message_id": self.message1.id}))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data["reactions"]), 2)

        emojis = [r["emoji"] for r in data["reactions"]]
        self.assertIn("👍", emojis)
        self.assertIn("❤️", emojis)

    def test_add_reaction_to_message(self):
        """Test adding a reaction to a message."""
        self.login_user(self.user1)

        response = self.client.post(
            reverse("message_reactions", kwargs={"message_id": self.message1.id}),
            json.dumps({"emoji": "🎉"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["emoji"], "🎉")
        self.assertEqual(data["user"]["id"], self.user1.id)

        # Verify reaction was created
        reaction = Reaction.objects.get(message=self.message1, user=self.user1, emoji="🎉")
        self.assertIsNotNone(reaction)

    def test_add_duplicate_reaction_fails(self):
        """Test that adding duplicate reaction fails."""
        # Create existing reaction
        Reaction.objects.create(message=self.message1, user=self.user1, emoji="👍")

        self.login_user(self.user1)

        response = self.client.post(
            reverse("message_reactions", kwargs={"message_id": self.message1.id}),
            json.dumps({"emoji": "👍"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("already exists", data["error"])

    def test_remove_reaction_from_message(self):
        """Test removing a reaction from a message."""
        # Create reaction to remove
        reaction = Reaction.objects.create(message=self.message1, user=self.user1, emoji="👍")

        self.login_user(self.user1)

        response = self.client.delete(
            reverse("message_reactions", kwargs={"message_id": self.message1.id}),
            json.dumps({"emoji": "👍"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verify reaction was deleted
        with self.assertRaises(Reaction.DoesNotExist):
            Reaction.objects.get(id=reaction.id)

    def test_remove_nonexistent_reaction_fails(self):
        """Test that removing nonexistent reaction fails."""
        self.login_user(self.user1)

        response = self.client.delete(
            reverse("message_reactions", kwargs={"message_id": self.message1.id}),
            json.dumps({"emoji": "❌"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn("not found", data["error"])


@override_switch("chat_feature", active=True)
class ChatSchoolUsersViewTest(BaseViewTest):
    """Test chat_school_users function-based view."""

    def test_school_users_requires_authentication(self):
        """Test that school users endpoint requires authentication."""
        response = self.client.get(reverse("chat_school_users"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_school_users_returns_same_school_users(self):
        """Test that endpoint returns users from same schools."""
        self.login_user(self.user1)

        response = self.client.get(reverse("chat_school_users"))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn("users", data)
        self.assertIn("schools", data)

        usernames = [user["username"] for user in data["users"]]
        self.assertIn("user2", usernames)  # Same school
        self.assertNotIn("user3", usernames)  # Different school
        self.assertNotIn("user1", usernames)  # Current user excluded

    def test_school_users_includes_school_info(self):
        """Test that response includes school information."""
        self.login_user(self.user1)

        response = self.client.get(reverse("chat_school_users"))
        data = json.loads(response.content)

        school_names = [school["name"] for school in data["schools"]]
        self.assertIn(self.school1.name, school_names)
        self.assertNotIn(self.school2.name, school_names)  # Not user's school

    def test_staff_user_sees_all_schools(self):
        """Test that staff users see all schools."""
        # Make user1 staff
        self.user1.is_staff = True
        self.user1.save()

        self.login_user(self.user1)

        response = self.client.get(reverse("chat_school_users"))
        data = json.loads(response.content)

        school_names = [school["name"] for school in data["schools"]]
        self.assertIn(self.school1.name, school_names)
        self.assertIn(self.school2.name, school_names)  # Staff sees all
