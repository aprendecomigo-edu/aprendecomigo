"""
WebSocket consumers for school dashboard real-time updates.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from accounts.models import School, SchoolMembership, SchoolRole

User = get_user_model()


class SchoolDashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for school dashboard real-time updates"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.school_id = self.scope['url_route']['kwargs']['school_id']
        self.group_name = f'school_{self.school_id}_dashboard'
        self.user = self.scope.get('user')
        
        # Check authentication
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user has permission to access this school's dashboard
        has_permission = await self.check_dashboard_permission()
        if not has_permission:
            await self.close()
            return
        
        # Join the school dashboard group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the school dashboard group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # For now, we only send data from server to client
            # Could add client-to-server messages for interactive features
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Client messages not supported yet'
            }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    # Message handlers for different types of updates
    
    async def metrics_update(self, event):
        """Send metrics update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'metrics_update',
            'data': event['data']
        }))
    
    async def activity_new(self, event):
        """Send new activity to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'activity_new',
            'data': event['data']
        }))
    
    async def invitation_status_update(self, event):
        """Send invitation status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'invitation_status_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def check_dashboard_permission(self):
        """Check if user has permission to access dashboard for this school"""
        try:
            school = School.objects.get(id=self.school_id)
            membership = SchoolMembership.objects.filter(
                user=self.user,
                school=school,
                role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
                is_active=True
            ).exists()
            return membership
        except School.DoesNotExist:
            return False


class SchoolDashboardBroadcaster:
    """Utility class for broadcasting updates to school dashboard"""
    
    @staticmethod
    async def broadcast_metrics_update(school_id, metrics_data):
        """Broadcast metrics update to all connected dashboard users"""
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'school_{school_id}_dashboard',
            {
                'type': 'metrics_update',
                'data': metrics_data
            }
        )
    
    @staticmethod
    async def broadcast_new_activity(school_id, activity_data):
        """Broadcast new activity to all connected dashboard users"""
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'school_{school_id}_dashboard',
            {
                'type': 'activity_new',
                'data': activity_data
            }
        )
    
    @staticmethod
    async def broadcast_invitation_update(school_id, invitation_data):
        """Broadcast invitation status update to all connected dashboard users"""
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'school_{school_id}_dashboard',
            {
                'type': 'invitation_status_update',
                'data': invitation_data
            }
        )