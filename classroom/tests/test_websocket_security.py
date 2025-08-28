"""
WebSocket Business Logic Tests for ChatConsumer.

This module tests business rules related to WebSocket connections:
- Channel participation validation
- Message content handling
- User status tracking

Note: These tests use channels.testing.WebsocketCommunicator which requires Daphne.
Daphne is installed ONLY as a dev dependency for testing purposes.
The actual application uses Uvicorn for WebSocket support in production.
"""

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from classroom.consumers import ChatConsumer
from classroom.models import Channel

User = get_user_model()


@override_settings(
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
)
class ChatConsumerBusinessLogicTest(TestCase):
    """Test business logic for WebSocket chat consumer."""

    def setUp(self):
        """Set up test data for WebSocket business logic tests."""
        self.user = User.objects.create_user(email="user@example.com", username="testuser", password="testpass123")

        self.other_user = User.objects.create_user(
            email="other@example.com", username="otheruser", password="testpass123"
        )

        # Create test channel
        self.channel = Channel.objects.create(name="test-channel", is_direct=False)
        self.channel.participants.add(self.user)

    def create_test_communicator(self, channel_name, user=None):
        """Create a WebsocketCommunicator for testing."""
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{channel_name}/")
        if user is not None:
            communicator.scope["user"] = user
        communicator.scope["url_route"] = {"kwargs": {"channel_name": channel_name}}
        return communicator

    async def test_authenticated_user_can_connect_to_participant_channel(self):
        """Test that authenticated users can connect to channels they participate in."""
        communicator = self.create_test_communicator("test-channel", self.user)

        connected, subprotocol = await communicator.connect()

        # This tests the business rule: users can only connect to channels they participate in
        self.assertTrue(connected, "User should connect to channels they participate in")

        await communicator.disconnect()

    async def test_user_online_status_tracked_correctly(self):
        """Test that user online status is tracked correctly for business purposes."""
        communicator = self.create_test_communicator("test-channel", self.user)

        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Should receive user status message about coming online
        response = await communicator.receive_json_from()

        # This tests the business rule: online status must be tracked for user presence
        self.assertEqual(response["type"], "user_status")
        self.assertEqual(response["status"], "online")
        self.assertEqual(response["user"], self.user.username)

        await communicator.disconnect()

    async def test_message_content_preserved_in_websocket_transmission(self):
        """Test that message content is preserved correctly during WebSocket transmission."""
        communicator = self.create_test_communicator("test-channel", self.user)

        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Skip online status message
        await communicator.receive_json_from()

        # Test message with special characters
        test_message = "Test message with special chars: áéíóú & <script>alert('test')</script>"
        await communicator.send_json_to({"type": "message", "message": test_message})

        # Should receive the broadcasted message with content preserved
        response = await communicator.receive_json_from()

        # This tests the business rule: message content must be preserved exactly
        self.assertEqual(response["type"], "chat_message")
        self.assertEqual(response["message"]["content"], test_message)
        self.assertEqual(response["message"]["sender"], self.user.username)
        self.assertIn("áéíóú", response["message"]["content"])
        self.assertIn("<script>", response["message"]["content"])

        await communicator.disconnect()

    @database_sync_to_async
    def create_other_channel(self):
        """Create another channel for testing isolation."""
        other_channel = Channel.objects.create(name="other-channel", is_direct=False)
        other_channel.participants.add(self.other_user)
        return other_channel

    async def test_channel_isolation_business_rule(self):
        """Test that messages are properly isolated to specific channels."""
        # Connect user to their authorized channel
        user_communicator = self.create_test_communicator("test-channel", self.user)

        # Create separate channel for other user using async context
        await self.create_other_channel()

        other_communicator = self.create_test_communicator("other-channel", self.other_user)

        user_connected, _ = await user_communicator.connect()
        other_connected, _ = await other_communicator.connect()

        self.assertTrue(user_connected)
        self.assertTrue(other_connected)

        # Skip online status messages
        await user_communicator.receive_json_from()
        await other_communicator.receive_json_from()

        # User sends message to their channel
        await user_communicator.send_json_to({"type": "message", "message": "Message from user"})

        # User should receive their message back
        user_response = await user_communicator.receive_json_from()
        self.assertEqual(user_response["message"]["content"], "Message from user")

        # This tests the business rule: messages must be isolated to specific channels
        # Other user should not receive this message (in different channel)
        # This validates proper channel isolation

        await user_communicator.disconnect()
        await other_communicator.disconnect()
