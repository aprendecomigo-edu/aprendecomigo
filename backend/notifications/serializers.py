"""
Serializers for notification API endpoints - Issue #107: Student Balance Monitoring & Notification System
"""

from rest_framework import serializers
from finances.models import PurchaseTransaction
from .models import Notification, NotificationType


class PurchaseTransactionSerializer(serializers.ModelSerializer):
    """Simple serializer for related purchase transactions in notifications."""
    
    class Meta:
        model = PurchaseTransaction
        fields = [
            'id',
            'transaction_type',
            'amount',
            'payment_status',
            'expires_at',
            'created_at'
        ]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notification model.
    
    Used for listing notifications and providing full notification data.
    """
    
    related_transaction = PurchaseTransactionSerializer(read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'notification_type_display',
            'title',
            'message',
            'is_read',
            'read_at',
            'related_transaction',
            'metadata',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for notification list view.
    
    Optimized for list performance with essential fields only.
    """
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'notification_type_display',
            'title',
            'message',
            'is_read',
            'read_at',
            'created_at'
        ]
        read_only_fields = fields


class NotificationUnreadCountSerializer(serializers.Serializer):
    """Serializer for unread notification count response."""
    
    unread_count = serializers.IntegerField(
        help_text="Number of unread notifications for the user"
    )


class NotificationMarkReadResponseSerializer(serializers.Serializer):
    """Serializer for mark notification as read response."""
    
    message = serializers.CharField(
        help_text="Success message indicating notification was marked as read"
    )