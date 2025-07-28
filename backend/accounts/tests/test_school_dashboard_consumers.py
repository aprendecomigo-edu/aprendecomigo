"""
Test suite for School Dashboard WebSocket consumers following TDD methodology.
Tests for real-time dashboard updates via WebSocket.
"""
import json
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from accounts.models import School, SchoolMembership, SchoolRole
from aprendecomigo.asgi import application

User = get_user_model()


class SchoolDashboardConsumerTest(TransactionTestCase):
    """Test cases for School Dashboard WebSocket consumer"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.school_owner = User.objects.create_user(
            email='owner@test.com',
            name='School Owner'
        )
        self.school_admin = User.objects.create_user(
            email='admin@test.com',
            name='School Admin'
        )
        self.teacher = User.objects.create_user(
            email='teacher@test.com',
            name='Teacher User'
        )
        self.unauthorized_user = User.objects.create_user(
            email='unauthorized@test.com',
            name='Unauthorized User'
        )
        
        # Create test school
        self.school = School.objects.create(
            name='Test School',
            description='A test school'
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        SchoolMembership.objects.create(
            user=self.school_admin,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        SchoolMembership.objects.create(
            user=self.teacher,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
    async def test_connect_authorized_owner(self):
        """Test WebSocket connection for school owner"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator.scope['user'] = self.school_owner
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Disconnect
        await communicator.disconnect()
        
    async def test_connect_authorized_admin(self):
        """Test WebSocket connection for school admin"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator.scope['user'] = self.school_admin
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Disconnect
        await communicator.disconnect()
        
    async def test_connect_unauthorized_teacher(self):
        """Test WebSocket connection denied for regular teacher"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator.scope['user'] = self.teacher
        
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        
    async def test_connect_unauthorized_user(self):
        """Test WebSocket connection denied for user not in school"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator.scope['user'] = self.unauthorized_user
        
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        
    async def test_connect_unauthenticated(self):
        """Test WebSocket connection denied for unauthenticated user"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        # No user in scope
        
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        
    async def test_receive_metrics_update(self):
        """Test receiving metrics update message"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator.scope['user'] = self.school_owner
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Simulate metrics update from server
        # This would normally be triggered by a signal or background task
        from accounts.consumers import SchoolDashboardConsumer
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"school_{self.school.id}_dashboard",
            {
                "type": "metrics_update",
                "data": {
                    "student_count": {"total": 25, "change": 1},
                    "teacher_count": {"total": 5, "change": 0},
                    "active_classes": {"total": 3, "change": -1}
                }
            }
        )
        
        # Receive message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'metrics_update')
        self.assertEqual(response['data']['student_count']['total'], 25)
        self.assertEqual(response['data']['student_count']['change'], 1)
        
        await communicator.disconnect()
        
    async def test_receive_activity_new(self):
        """Test receiving new activity message"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator.scope['user'] = self.school_owner
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Simulate new activity
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"school_{self.school.id}_dashboard",
            {
                "type": "activity_new",
                "data": {
                    "id": "test-uuid",
                    "activity_type": "student_joined",
                    "timestamp": "2024-01-20T10:30:00Z",
                    "actor": {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "role": "student"
                    },
                    "description": "John Doe joined as a student"
                }
            }
        )
        
        # Receive message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'activity_new')
        self.assertEqual(response['data']['activity_type'], 'student_joined')
        self.assertEqual(response['data']['actor']['name'], 'John Doe')
        
        await communicator.disconnect()
        
    async def test_receive_invitation_status_update(self):
        """Test receiving invitation status update"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator.scope['user'] = self.school_admin
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Simulate invitation status update
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"school_{self.school.id}_dashboard",
            {
                "type": "invitation_status_update",
                "data": {
                    "invitation_id": "inv-uuid",
                    "old_status": "pending",
                    "new_status": "accepted",
                    "accepted_by": {
                        "id": 2,
                        "name": "Jane Smith",
                        "email": "jane@example.com"
                    }
                }
            }
        )
        
        # Receive message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'invitation_status_update')
        self.assertEqual(response['data']['new_status'], 'accepted')
        self.assertEqual(response['data']['accepted_by']['name'], 'Jane Smith')
        
        await communicator.disconnect()
        
    async def test_multiple_admins_receive_updates(self):
        """Test that multiple admins receive the same updates"""
        # Connect first admin
        communicator1 = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator1.scope['user'] = self.school_owner
        connected1, _ = await communicator1.connect()
        self.assertTrue(connected1)
        
        # Connect second admin
        communicator2 = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator2.scope['user'] = self.school_admin
        connected2, _ = await communicator2.connect()
        self.assertTrue(connected2)
        
        # Send update
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"school_{self.school.id}_dashboard",
            {
                "type": "metrics_update",
                "data": {
                    "student_count": {"total": 30, "change": 5}
                }
            }
        )
        
        # Both should receive the message
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()
        
        self.assertEqual(response1['type'], 'metrics_update')
        self.assertEqual(response2['type'], 'metrics_update')
        self.assertEqual(response1['data']['student_count']['total'], 30)
        self.assertEqual(response2['data']['student_count']['total'], 30)
        
        await communicator1.disconnect()
        await communicator2.disconnect()
        
    async def test_disconnect_removes_from_group(self):
        """Test that disconnecting removes user from group"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/schools/{self.school.id}/dashboard/"
        )
        communicator.scope['user'] = self.school_owner
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Disconnect
        await communicator.disconnect()
        
        # Send a message to the group - user should not receive it
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"school_{self.school.id}_dashboard",
            {
                "type": "metrics_update",
                "data": {"test": "data"}
            }
        )
        
        # Should not receive anything (connection is closed)
        with self.assertRaises(Exception):
            await communicator.receive_json_from()