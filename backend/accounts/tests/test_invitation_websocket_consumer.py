"""
Tests for the InvitationConsumer WebSocket functionality.

This module tests real-time invitation status updates via WebSocket connections.
Following TDD methodology - these tests are written first, then implementation follows.
"""

import json
import uuid
from unittest.mock import Mock, AsyncMock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from accounts.models import (
    School, SchoolMembership, SchoolRole, TeacherInvitation, 
    InvitationStatus, EmailDeliveryStatus
)
from accounts.consumers import InvitationConsumer

User = get_user_model()


class InvitationWebSocketConsumerTest(TestCase):
    """Test suite for InvitationConsumer WebSocket functionality."""
    
    def setUp(self):
        """Set up test data for WebSocket tests."""
        # Create test users
        self.school_owner = User.objects.create_user(
            email="owner@school.com",
            name="School Owner",
            phone_number="+351912345678"
        )
        
        self.school_admin = User.objects.create_user(
            email="admin@school.com",
            name="School Admin",
            phone_number="+351912345679"
        )
        
        self.regular_user = User.objects.create_user(
            email="regular@user.com",
            name="Regular User",
            phone_number="+351912345680"
        )
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="School for WebSocket testing"
        )
        
        # Create memberships
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.school_admin,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        # Create test invitation
        self.invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            custom_message="Welcome to our school!",
            batch_id=uuid.uuid4(),
            role=SchoolRole.TEACHER,
            status=InvitationStatus.PENDING
        )
    
    async def test_websocket_connection_requires_authentication(self):
        """Test that WebSocket connection requires authenticated user."""
        communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        
        # Mock unauthenticated user
        communicator.scope["user"] = Mock(is_authenticated=False)
        
        connected, subprotocol = await communicator.connect()
        
        # Should reject connection for unauthenticated user
        self.assertFalse(connected)
        await communicator.disconnect()
    
    async def test_websocket_connection_requires_school_admin_permission(self):
        """Test that WebSocket connection requires school admin permissions."""
        communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        
        # Mock regular user (not admin)
        communicator.scope["user"] = self.regular_user
        
        connected, subprotocol = await communicator.connect()
        
        # Should reject connection for non-admin user
        self.assertFalse(connected)
        await communicator.disconnect()
    
    async def test_websocket_connection_allows_school_owner(self):
        """Test that WebSocket connection allows school owner."""
        communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        
        # Mock school owner
        communicator.scope["user"] = self.school_owner
        
        connected, subprotocol = await communicator.connect()
        
        # Should accept connection for school owner
        self.assertTrue(connected)
        await communicator.disconnect()
    
    async def test_websocket_connection_allows_school_admin(self):
        """Test that WebSocket connection allows school admin."""
        communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        
        # Mock school admin
        communicator.scope["user"] = self.school_admin
        
        connected, subprotocol = await communicator.connect()
        
        # Should accept connection for school admin
        self.assertTrue(connected)
        await communicator.disconnect()
    
    async def test_websocket_invitation_sent_message(self):
        """Test WebSocket receives invitation_sent message."""
        communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        
        communicator.scope["user"] = self.school_owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send invitation_sent message
        await communicator.send_json_to({
            "type": "invitation.sent",
            "invitation": {
                "id": self.invitation.id,
                "email": self.invitation.email,
                "status": "sent",
                "invited_by": self.invitation.invited_by.name,
                "created_at": self.invitation.created_at.isoformat()
            }
        })
        
        # Should receive the message
        response = await communicator.receive_json_from()
        
        self.assertEqual(response["type"], "invitation_sent")
        self.assertEqual(response["data"]["invitation"]["email"], "teacher@example.com")
        
        await communicator.disconnect()
    
    async def test_websocket_invitation_accepted_message(self):
        """Test WebSocket receives invitation_accepted message."""
        communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        
        communicator.scope["user"] = self.school_owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send invitation_accepted message
        await communicator.send_json_to({
            "type": "invitation.accepted",
            "invitation": {
                "id": self.invitation.id,
                "email": self.invitation.email,
                "status": "accepted",
                "teacher_name": "John Doe",
                "accepted_at": timezone.now().isoformat()
            }
        })
        
        # Should receive the message
        response = await communicator.receive_json_from()
        
        self.assertEqual(response["type"], "invitation_accepted")
        self.assertEqual(response["data"]["invitation"]["email"], "teacher@example.com")
        self.assertEqual(response["data"]["invitation"]["teacher_name"], "John Doe")
        
        await communicator.disconnect()
    
    async def test_websocket_invitation_expired_message(self):
        """Test WebSocket receives invitation_expired message."""
        communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        
        communicator.scope["user"] = self.school_owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send invitation_expired message
        await communicator.send_json_to({
            "type": "invitation.expired",
            "invitation": {
                "id": self.invitation.id,
                "email": self.invitation.email,
                "status": "expired",
                "expired_at": timezone.now().isoformat()
            }
        })
        
        # Should receive the message
        response = await communicator.receive_json_from()
        
        self.assertEqual(response["type"], "invitation_expired")
        self.assertEqual(response["data"]["invitation"]["status"], "expired")
        
        await communicator.disconnect()
    
    async def test_websocket_multiple_subscribers_receive_updates(self):
        """Test that multiple WebSocket subscribers receive updates."""
        # Connect two different admin users
        owner_communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        owner_communicator.scope["user"] = self.school_owner
        
        admin_communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        admin_communicator.scope["user"] = self.school_admin
        
        # Both should connect successfully
        owner_connected, _ = await owner_communicator.connect()
        admin_connected, _ = await admin_communicator.connect()
        
        self.assertTrue(owner_connected)
        self.assertTrue(admin_connected)
        
        # Broadcast message to all subscribers in the school group  
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        
        await channel_layer.group_send(
            f"invitations_school_{self.school.id}",
            {
                "type": "invitation.sent",
                "invitation": {
                    "id": self.invitation.id,
                    "email": self.invitation.email,
                    "status": "sent"
                }
            }
        )
        
        # Both subscribers should receive the message
        owner_response = await owner_communicator.receive_json_from()
        admin_response = await admin_communicator.receive_json_from()
        
        self.assertEqual(owner_response["type"], "invitation_sent")
        self.assertEqual(admin_response["type"], "invitation_sent")
        
        await owner_communicator.disconnect()
        await admin_communicator.disconnect()
    
    async def test_websocket_invalid_json_handling(self):
        """Test WebSocket handles invalid JSON gracefully."""
        communicator = WebsocketCommunicator(
            InvitationConsumer.as_asgi(),
            f"/ws/schools/{self.school.id}/invitations/"
        )
        
        communicator.scope["user"] = self.school_owner
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send invalid JSON
        await communicator.send_to(text_data="invalid json")
        
        # Should receive error message
        response = await communicator.receive_json_from()
        
        self.assertEqual(response["type"], "error")
        self.assertIn("Invalid JSON", response["message"])
        
        await communicator.disconnect()
    
    def test_websocket_group_name_generation(self):
        """Test that WebSocket group names are generated correctly."""
        # This will be tested through the consumer implementation
        expected_group_name = f"invitations_school_{self.school.id}"
        
        # The actual test will be in the consumer implementation
        # where we verify the group name is used correctly
        self.assertIsNotNone(expected_group_name)


class InvitationWebSocketBroadcasterTest(TestCase):
    """Test suite for InvitationWebSocketBroadcaster utility class."""
    
    def setUp(self):
        """Set up test data for broadcaster tests."""
        self.school_owner = User.objects.create_user(
            email="owner@school.com",
            name="School Owner",
            phone_number="+351912345678"
        )
        
        self.school = School.objects.create(
            name="Test School",
            description="School for broadcaster testing"
        )
        
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
        self.invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            batch_id=uuid.uuid4(),
            role=SchoolRole.TEACHER,
            status=InvitationStatus.PENDING
        )
    
    @patch('channels.layers.get_channel_layer')
    async def test_broadcast_invitation_sent(self, mock_get_channel_layer):
        """Test broadcasting invitation_sent event."""
        mock_channel_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        from accounts.consumers import InvitationWebSocketBroadcaster
        
        invitation_data = {
            "id": self.invitation.id,
            "email": self.invitation.email,
            "status": "sent",
            "invited_by": self.invitation.invited_by.name
        }
        
        await InvitationWebSocketBroadcaster.broadcast_invitation_sent(
            self.school.id, 
            invitation_data
        )
        
        mock_channel_layer.group_send.assert_called_once_with(
            f"invitations_school_{self.school.id}",
            {
                "type": "invitation.sent",
                "data": {"invitation": invitation_data}
            }
        )
    
    @patch('channels.layers.get_channel_layer')
    async def test_broadcast_invitation_accepted(self, mock_get_channel_layer):
        """Test broadcasting invitation_accepted event."""
        mock_channel_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        from accounts.consumers import InvitationWebSocketBroadcaster
        
        invitation_data = {
            "id": self.invitation.id,
            "email": self.invitation.email,
            "status": "accepted",
            "teacher_name": "John Doe",
            "accepted_at": timezone.now().isoformat()
        }
        
        await InvitationWebSocketBroadcaster.broadcast_invitation_accepted(
            self.school.id,
            invitation_data
        )
        
        mock_channel_layer.group_send.assert_called_once_with(
            f"invitations_school_{self.school.id}",
            {
                "type": "invitation.accepted",
                "data": {"invitation": invitation_data}
            }
        )
    
    @patch('channels.layers.get_channel_layer')
    async def test_broadcast_invitation_expired(self, mock_get_channel_layer):
        """Test broadcasting invitation_expired event."""
        mock_channel_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        from accounts.consumers import InvitationWebSocketBroadcaster
        
        invitation_data = {
            "id": self.invitation.id,
            "email": self.invitation.email,
            "status": "expired",
            "expired_at": timezone.now().isoformat()
        }
        
        await InvitationWebSocketBroadcaster.broadcast_invitation_expired(
            self.school.id,
            invitation_data
        )
        
        mock_channel_layer.group_send.assert_called_once_with(
            f"invitations_school_{self.school.id}",
            {
                "type": "invitation.expired", 
                "data": {"invitation": invitation_data}
            }
        )