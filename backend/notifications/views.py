"""
Notifications API views.
"""
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole,
    TeacherInvitation, InvitationStatus
)
from accounts.db_queries import list_school_ids_owned_or_managed
from tasks.models import Task


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_counts(request):
    """
    GET /api/notifications/counts/
    
    Returns notification counts for the current user:
    - pending_invitations: Number of pending teacher invitations
    - new_registrations: Number of users who haven't completed first login
    - incomplete_profiles: Number of users with incomplete profile tasks
    - overdue_tasks: Number of overdue tasks
    - total_unread: Total count of all notifications
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
    
    # Calculate total
    total_unread = pending_invitations + new_registrations + incomplete_profiles + overdue_tasks
    
    return Response({
        "pending_invitations": pending_invitations,
        "new_registrations": new_registrations,
        "incomplete_profiles": incomplete_profiles,
        "overdue_tasks": overdue_tasks,
        "total_unread": total_unread
    }, status=status.HTTP_200_OK)
