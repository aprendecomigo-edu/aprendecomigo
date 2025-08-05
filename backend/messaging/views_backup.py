"""
Notifications API views - Issue #107: Student Balance Monitoring & Notification System
"""

from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from knox.auth import TokenAuthentication

from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole,
    TeacherInvitation, InvitationStatus
)
from accounts.db_queries import list_school_ids_owned_or_managed
from tasks.models import Task
from .models import Notification, NotificationType
from .serializers import (
    NotificationSerializer, NotificationListSerializer,
    NotificationUnreadCountSerializer, NotificationMarkReadResponseSerializer
)


class NotificationListView(generics.ListAPIView):
    """
    GET /api/notifications/
    
    List notifications for the authenticated user with pagination and filtering.
    
    Query Parameters:
    - notification_type: Filter by notification type (low_balance, package_expiring, balance_depleted)
    - is_read: Filter by read status (true/false)
    - page: Page number for pagination
    - page_size: Number of items per page (default: 20)
    """
    
    serializer_class = NotificationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the authenticated user with filtering support."""
        queryset = Notification.objects.filter(user=self.request.user).select_related('related_transaction').order_by('-created_at')
        
        # Apply filters based on query parameters
        notification_type = self.request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
            
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            is_read_bool = is_read.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_read=is_read_bool)
            
        return queryset


class NotificationDetailView(generics.RetrieveAPIView):
    """
    GET /api/notifications/{id}/
    
    Get detailed information about a specific notification.
    Users can only access their own notifications.
    """
    
    serializer_class = NotificationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the authenticated user only."""
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(APIView):
    """
    POST /api/notifications/{id}/read/
    
    Mark a specific notification as read.
    Users can only mark their own notifications as read.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Mark notification as read."""
        try:
            notification = Notification.objects.get(
                pk=pk, 
                user=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Mark as read if not already read
        if not notification.is_read:
            notification.mark_as_read()
        
        serializer = NotificationMarkReadResponseSerializer({
            'message': 'Notification marked as read'
        })
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationUnreadCountView(APIView):
    """
    GET /api/notifications/unread-count/
    
    Get the count of unread notifications for the authenticated user.
    Used for UI badge display.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return unread notification count."""
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        serializer = NotificationUnreadCountSerializer({
            'unread_count': unread_count
        })
        
        return Response(serializer.data, status=status.HTTP_200_OK)


# Legacy notification counts endpoint - kept for backward compatibility
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_counts(request):
    """
    GET /api/notifications/counts/
    
    Legacy endpoint - Returns notification counts for the current user:
    - pending_invitations: Number of pending teacher invitations
    - new_registrations: Number of users who haven't completed first login
    - incomplete_profiles: Number of users with incomplete profile tasks
    - overdue_tasks: Number of overdue tasks
    - total_unread: Total count of all notifications
    
    Note: This endpoint is kept for backward compatibility. New implementations
    should use the dedicated notification endpoints.
    """
    user = request.user
    
    # Get schools this user can manage (for admin-level notifications)
    admin_school_ids = list_school_ids_owned_or_managed(user)
    
    # Initialize counts
    pending_invitations = 0
    new_registrations = 0
    incomplete_profiles = 0
    overdue_tasks = 0
    
    # Count pending invitations (only for school admins)
    if admin_school_ids:
        pending_invitations = TeacherInvitation.objects.filter(
            school_id__in=admin_school_ids,
            status__in=[
                InvitationStatus.PENDING,
                InvitationStatus.SENT,
                InvitationStatus.DELIVERED,
                InvitationStatus.VIEWED,
            ],
            is_accepted=False,
            expires_at__gt=timezone.now()
        ).count()
        
        # Count new registrations (users who haven't completed first login)
        new_registrations = CustomUser.objects.filter(
            school_memberships__school_id__in=admin_school_ids,
            first_login_completed=False
        ).distinct().count()
        
        # Count incomplete profiles (users with pending profile completion tasks)
        incomplete_profiles = Task.objects.filter(
            user__school_memberships__school_id__in=admin_school_ids,
            title__icontains="Complete Your Profile",
            status="pending",
            task_type="onboarding",
            is_system_generated=True
        ).values('user').distinct().count()
    
    # Count overdue tasks for current user and their managed schools
    overdue_tasks_query = Task.objects.filter(
        status="pending",
        due_date__lt=timezone.now()
    )
    
    if admin_school_ids:
        # Include tasks from users in managed schools
        overdue_tasks_query = overdue_tasks_query.filter(
            Q(user=user) |  # User's own tasks
            Q(user__school_memberships__school_id__in=admin_school_ids)  # Tasks from managed schools
        )
    else:
        # Only user's own tasks
        overdue_tasks_query = overdue_tasks_query.filter(user=user)
    
    overdue_tasks = overdue_tasks_query.distinct().count()
    
    # Add student balance notifications count
    student_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()
    
    # Calculate total
    total_unread = pending_invitations + new_registrations + incomplete_profiles + overdue_tasks + student_notifications
    
    return Response({
        "pending_invitations": pending_invitations,
        "new_registrations": new_registrations,
        "incomplete_profiles": incomplete_profiles,
        "overdue_tasks": overdue_tasks,
        "student_notifications": student_notifications,
        "total_unread": total_unread
    }, status=status.HTTP_200_OK)
