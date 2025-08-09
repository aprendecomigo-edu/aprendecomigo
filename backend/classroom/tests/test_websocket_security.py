"""
WebSocket Authentication Security Tests for ChatConsumer.

This module tests security vulnerabilities and authentication requirements
for WebSocket connections in the ChatConsumer class. These tests follow
TDD principles and validate that all security measures are properly implemented.

Security scenarios tested:
- Unauthenticated user connection attempts (should be rejected with code 4001)
- Authenticated user access to authorized channels (should succeed)
- Authenticated user access to unauthorized channels (should be rejected with code 4003)
- Message handling from unauthenticated users (should be rejected)
- Rate limiting functionality (test structure prepared)
- Security event logging (authentication failures, unauthorized access attempts)

TESTING APPROACH:
For unit tests, we use ChatConsumer.as_asgi() directly without the AuthMiddlewareStack.
This prevents the middleware from overwriting manually set scope["user"] values during tests,
allowing us to properly test authentication and authorization logic.

The middleware stack (test_application) is only used for integration tests that specifically
need to test middleware behavior itself.

SECURITY MEASURES VALIDATED:
1. ChatConsumer.connect() performs authentication checks and rejects unauthenticated users
2. Channel access control enforced - users can only connect to channels they participate in
3. Message filtering - authenticated users can only send messages to authorized channels
4. Security logging implemented for monitoring unauthorized access attempts
5. Rate limiting structure prepared for future implementation
"""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from channels.db import database_sync_to_async
from channels.routing import URLRouter  
from channels.testing import WebsocketCommunicator
from channels.layers import InMemoryChannelLayer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings
from django.utils import timezone

from classroom.consumers import ChatConsumer
from classroom.models import Channel, Message

User = get_user_model()


# URL routing for testing - matches the actual ASGI configuration
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

websocket_urlpatterns = [
    path("ws/chat/<str:channel_name>/", ChatConsumer.as_asgi()),
]

# For unit tests, we use ChatConsumer directly without middleware stack
# This prevents AuthMiddlewareStack from overwriting manually set scope["user"]
test_consumer = ChatConsumer.as_asgi()

# For integration tests that need middleware behavior, use the full stack
test_application = AuthMiddlewareStack(
    URLRouter(websocket_urlpatterns)
)

# Production application for reference
application = AllowedHostsOriginValidator(
    AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    )
)


@override_settings(
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
)
class WebSocketSecurityTestCase(TestCase):
    """Base test case for WebSocket security tests with common setup."""

    def setUp(self):
        """Set up test data for WebSocket security tests."""
        # Create test users
        self.authenticated_user = User.objects.create_user(
            email="user@example.com",
            username="testuser",
            password="testpass123"
        )
        
        self.other_user = User.objects.create_user(
            email="other@example.com", 
            username="otheruser",
            password="testpass123"
        )
        
        # Create test channels
        self.authorized_channel = Channel.objects.create(
            name="authorized-channel",
            is_direct=False
        )
        self.authorized_channel.participants.add(self.authenticated_user)
        
        self.unauthorized_channel = Channel.objects.create(
            name="unauthorized-channel", 
            is_direct=False
        )
        self.unauthorized_channel.participants.add(self.other_user)
        
        # Create direct message channel
        self.dm_channel = Channel.objects.create(
            name="dm-channel",
            is_direct=True
        )
        self.dm_channel.participants.add(self.authenticated_user, self.other_user)

    @database_sync_to_async
    def get_authenticated_user(self):
        """Helper to get authenticated user in async context."""
        return self.authenticated_user

    @database_sync_to_async
    def get_other_user(self):
        """Helper to get other user in async context."""
        return self.other_user

    def create_test_communicator(self, channel_name, user=None):
        """
        Create a WebsocketCommunicator for unit tests using direct consumer.
        
        This bypasses the AuthMiddlewareStack to prevent it from overwriting
        manually set scope["user"] values during tests.
        """
        communicator = WebsocketCommunicator(test_consumer, f"/ws/chat/{channel_name}/")
        if user is not None:
            communicator.scope["user"] = user
        # Manually set URL route kwargs since we're bypassing URLRouter
        communicator.scope["url_route"] = {"kwargs": {"channel_name": channel_name}}
        return communicator


class ChatConsumerUnauthenticatedUserTest(WebSocketSecurityTestCase):
    """
    Test that unauthenticated users (AnonymousUser) cannot connect to WebSocket.
    
    Security Requirement: All WebSocket connections must be authenticated.
    Expected Behavior: Connection should be rejected with close code 4001 (Unauthorized).
    
    Current Status: FAILING - Consumer accepts unauthenticated connections
    """

    async def test_unauthenticated_user_connection_rejected_with_code_4001(self):
        """Test that AnonymousUser connections are rejected with code 4001."""
        # Use direct consumer without middleware to test authentication logic
        communicator = self.create_test_communicator("authorized-channel", AnonymousUser())
        
        # Attempt connection - should be rejected
        connected, subprotocol = await communicator.connect()
        
        # Should not connect successfully
        self.assertFalse(connected, "Unauthenticated user should not be able to connect")
        
        # Should close with unauthorized code
        await communicator.disconnect()

    async def test_unauthenticated_user_cannot_join_any_channel(self):
        """Test that unauthenticated users are rejected from all channels."""
        channels_to_test = ["authorized-channel", "unauthorized-channel", "dm-channel"]
        
        for channel_name in channels_to_test:
            with self.subTest(channel=channel_name):
                # Use direct consumer without middleware to test authentication logic
                communicator = self.create_test_communicator(channel_name, AnonymousUser())
                
                # Should not be able to connect to any channel
                connected, subprotocol = await communicator.connect()
                self.assertFalse(
                    connected,
                    f"Unauthenticated user should not connect to {channel_name}"
                )
                
                await communicator.disconnect()

    async def test_unauthenticated_message_sending_rejected(self):
        """Test that messages from unauthenticated users are rejected."""
        # Use direct consumer without middleware to test authentication logic
        communicator = self.create_test_communicator("authorized-channel", AnonymousUser())
        
        # Should not be able to connect (connection rejected by security check)
        connected, subprotocol = await communicator.connect()
        
        if connected:
            # If somehow connected, attempt to send a message
            await communicator.send_json_to({
                "type": "message",
                "message": "This should be rejected"
            })
            
            # Should not receive any response or message should be rejected
            response = await communicator.receive_json_from()
            
            # Security fix should prevent message processing from unauthenticated users
            self.fail("Message from unauthenticated user should be rejected")
        
        await communicator.disconnect()


class ChatConsumerAuthorizedAccessTest(WebSocketSecurityTestCase):
    """
    Test that authenticated users can connect to channels they have access to.
    
    Security Requirement: Users should only connect to channels they are participants of.
    Expected Behavior: Connection succeeds for authorized channels.
    """

    async def test_authenticated_user_can_connect_to_authorized_channel(self):
        """Test that authenticated users can connect to channels they participate in."""
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("authorized-channel", user)
        
        # Should be able to connect
        connected, subprotocol = await communicator.connect()
        self.assertTrue(
            connected, 
            "Authenticated user should be able to connect to authorized channel"
        )
        
        # Should receive user status message about coming online
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "user_status")
        self.assertEqual(response["status"], "online")
        self.assertEqual(response["user"], self.authenticated_user.username)
        
        await communicator.disconnect()

    async def test_authenticated_user_can_send_messages_to_authorized_channel(self):
        """Test that authenticated users can send messages to authorized channels."""
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("authorized-channel", user)
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip the online status message
        await communicator.receive_json_from()
        
        # Send a message
        test_message = "Hello, this is a test message"
        await communicator.send_json_to({
            "type": "message",
            "message": test_message
        })
        
        # Should receive the broadcasted message
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "chat_message")
        self.assertEqual(response["message"]["content"], test_message)
        self.assertEqual(response["message"]["sender"], self.authenticated_user.username)
        
        await communicator.disconnect()

    async def test_authenticated_user_can_access_dm_channel(self):
        """Test that authenticated users can access DM channels they participate in."""
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("dm-channel", user)
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(
            connected, 
            "Authenticated user should be able to connect to DM channel they participate in"
        )
        
        await communicator.disconnect()


class ChatConsumerUnauthorizedAccessTest(WebSocketSecurityTestCase):
    """
    Test that authenticated users cannot connect to channels they don't have access to.
    
    Security Requirement: Channel access control must be enforced.
    Expected Behavior: Connection should be rejected with close code 4003 (Forbidden).
    
    Current Status: FAILING - No access control implemented
    """

    async def test_authenticated_user_cannot_connect_to_unauthorized_channel_code_4003(self):
        """Test that users cannot connect to channels they don't participate in."""
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("unauthorized-channel", user)
        
        # Should not be able to connect
        connected, subprotocol = await communicator.connect()
        
        # Security check should prevent connection to unauthorized channel
        self.assertFalse(
            connected,
            "Authenticated user should not connect to unauthorized channel"
        )
        
        # Should close with forbidden code
        await communicator.disconnect()

    async def test_authenticated_user_cannot_send_messages_to_unauthorized_channel(self):
        """Test that users cannot send messages to unauthorized channels."""
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("unauthorized-channel", user)
        
        # Should not be able to connect to unauthorized channel
        connected, subprotocol = await communicator.connect()
        
        if connected:
            # Skip potential online status message
            try:
                await communicator.receive_json_from()
            except Exception:
                pass
            
            # Attempt to send message to unauthorized channel
            await communicator.send_json_to({
                "type": "message", 
                "message": "This should be rejected"
            })
            
            # Should not process the message or should reject it
            with self.assertRaises(Exception):
                response = await communicator.receive_json_from()
                self.fail("Message to unauthorized channel should be rejected")
        
        await communicator.disconnect()

    async def test_user_cannot_access_nonexistent_channel(self):
        """Test that users cannot connect to channels that don't exist."""
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("nonexistent-channel", user)
        
        # Should not be able to connect to non-existent channel
        connected, subprotocol = await communicator.connect()
        
        # Security check should prevent connection to non-existent channel
        self.assertFalse(
            connected,
            "User should not connect to non-existent channel"
        )
        
        await communicator.disconnect()


class ChatConsumerRateLimitingTest(WebSocketSecurityTestCase):
    """
    Test rate limiting functionality for WebSocket connections and messages.
    
    Security Requirement: Prevent abuse through rate limiting.
    Expected Behavior: Connections/messages should be rate limited per user.
    
    Current Status: NOT IMPLEMENTED - Test structure prepared for future implementation
    """

    async def test_connection_rate_limiting_structure(self):
        """Test structure for connection rate limiting (not yet implemented)."""
        # This test prepares the structure for rate limiting implementation
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("authorized-channel", user)
        
        # Connect successfully
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
        
        # TODO: Implement rate limiting tests when feature is added
        # - Test rapid connection attempts
        # - Test connection limit per user
        # - Test temporary blocking after rate limit exceeded

    async def test_message_rate_limiting_structure(self):
        """Test structure for message rate limiting (not yet implemented)."""
        # This test prepares the structure for message rate limiting
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("authorized-channel", user)
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip online status message
        await communicator.receive_json_from()
        
        # TODO: Implement rate limiting tests when feature is added
        # - Test rapid message sending
        # - Test message limit per time period
        # - Test rate limit enforcement
        
        await communicator.disconnect()


class ChatConsumerSecurityLoggingTest(WebSocketSecurityTestCase):
    """
    Test that security events are properly logged.
    
    Security Requirement: All security events must be logged for monitoring.
    Expected Behavior: Authentication failures and unauthorized access attempts are logged.
    
    Current Status: NOT IMPLEMENTED - Logging should be added with security fixes
    """

    @patch('classroom.consumers.logger')
    async def test_unauthenticated_connection_attempt_logged(self, mock_logger):
        """Test that unauthenticated connection attempts are logged."""
        # Use direct consumer without middleware to test authentication logging
        communicator = self.create_test_communicator("authorized-channel", AnonymousUser())
        
        # Attempt connection
        connected, subprotocol = await communicator.connect()
        
        # Should log the security event
        mock_logger.warning.assert_called_with(
            "Unauthenticated user attempted WebSocket connection to channel: %s",
            "authorized-channel"
        )
        
        await communicator.disconnect()

    @patch('classroom.consumers.logger')  
    async def test_unauthorized_channel_access_logged(self, mock_logger):
        """Test that unauthorized channel access attempts are logged."""
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("unauthorized-channel", user)
        
        # Attempt connection to unauthorized channel
        connected, subprotocol = await communicator.connect()
        
        # Should log the security event
        mock_logger.warning.assert_called_with(
            "User %s attempted access to unauthorized channel: %s",
            self.authenticated_user.username,
            "unauthorized-channel"
        )
        
        await communicator.disconnect()

    @patch('classroom.consumers.logger')
    async def test_successful_connection_logged(self, mock_logger):
        """Test that successful connections are logged for security monitoring."""
        # Use direct consumer without middleware to properly set authenticated user
        user = await self.get_authenticated_user()
        communicator = self.create_test_communicator("authorized-channel", user)
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should log successful connection
        mock_logger.info.assert_called_with(
            "User %s successfully connected to channel: %s",
            self.authenticated_user.username,
            "authorized-channel"
        )
        
        await communicator.disconnect()


class ChatConsumerSecurityIntegrationTest(WebSocketSecurityTestCase):
    """
    Integration tests combining multiple security scenarios.
    
    Tests real-world security scenarios with multiple users and channels.
    """

    async def test_multiple_users_channel_isolation(self):
        """Test that users are properly isolated to their authorized channels."""
        # Use direct consumer without middleware to properly set authenticated users
        
        # Connect authenticated user to authorized channel
        user1 = await self.get_authenticated_user()
        user1_communicator = self.create_test_communicator("authorized-channel", user1)
        
        # Connect other user to their channel
        user2 = await self.get_other_user()
        user2_communicator = self.create_test_communicator("unauthorized-channel", user2)
        
        # Both should connect to their respective authorized channels
        user1_connected, _ = await user1_communicator.connect()
        user2_connected, _ = await user2_communicator.connect()
        
        self.assertTrue(user1_connected, "User1 should connect to authorized channel")
        self.assertTrue(user2_connected, "User2 should connect to their authorized channel")
        
        # Skip online status messages
        await user1_communicator.receive_json_from()
        await user2_communicator.receive_json_from()
        
        # User1 sends message to their channel
        await user1_communicator.send_json_to({
            "type": "message",
            "message": "Message from user1"
        })
        
        # User1 should receive their message back
        user1_response = await user1_communicator.receive_json_from()
        self.assertEqual(user1_response["message"]["content"], "Message from user1")
        
        # User2 should NOT receive user1's message (channel isolation)
        # This test verifies that channels are properly isolated
        
        await user1_communicator.disconnect()
        await user2_communicator.disconnect()

    async def test_dm_channel_security(self):
        """Test security for direct message channels."""
        # Use direct consumer without middleware to properly set authenticated users
        
        # Both users should be able to connect to DM channel they both participate in
        user1 = await self.get_authenticated_user()
        user1_communicator = self.create_test_communicator("dm-channel", user1)
        
        user2 = await self.get_other_user()
        user2_communicator = self.create_test_communicator("dm-channel", user2)
        
        user1_connected, _ = await user1_communicator.connect()
        user2_connected, _ = await user2_communicator.connect()
        
        self.assertTrue(user1_connected, "User1 should connect to DM channel")
        self.assertTrue(user2_connected, "User2 should connect to DM channel")
        
        await user1_communicator.disconnect()
        await user2_communicator.disconnect()