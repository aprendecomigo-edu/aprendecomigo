"""
Messaging API views - Issue #107: Student Balance Monitoring & Notification System + Email Communication
"""

import logging
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from knox.auth import TokenAuthentication

from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole,
    TeacherInvitation, InvitationStatus, SchoolSettings
)
from .models import (
    SchoolEmailTemplate, EmailSequence, EmailCommunication,
    EmailTemplateType, EmailCommunicationType, EmailDeliveryStatus
)
from accounts.db_queries import list_school_ids_owned_or_managed
from accounts.permissions import IsSchoolOwnerOrAdmin
from tasks.models import Task
from .models import Notification, NotificationType
from .serializers import (
    NotificationSerializer, NotificationListSerializer,
    NotificationUnreadCountSerializer, NotificationMarkReadResponseSerializer,
    SchoolEmailTemplateSerializer, EmailSequenceSerializer, 
    EmailCommunicationSerializer, EmailTemplatePreviewSerializer,
    EmailAnalyticsSerializer
)

logger = logging.getLogger(__name__)


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


# =======================
# EMAIL COMMUNICATION VIEWS (moved from accounts)
# =======================


class SchoolEmailTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing school email templates.
    Provides CRUD operations with school-level permissions.
    """
    
    serializer_class = SchoolEmailTemplateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get_queryset(self):
        """Filter templates by user's schools."""
        user = self.request.user
        # Get schools where user is owner or admin
        school_ids = list_school_ids_owned_or_managed(user)
        return SchoolEmailTemplate.objects.filter(
            school_id__in=school_ids
        ).select_related('school', 'created_by').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the school and created_by fields when creating a template with security validation."""
        # Determine the school - use the school from request data or user's default school
        school_id = self.request.data.get('school')
        if school_id:
            # Verify user can manage this school
            school_ids = list_school_ids_owned_or_managed(self.request.user)
            if int(school_id) not in school_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to create templates for this school")
            school = School.objects.get(id=school_id)
        else:
            # Use user's first manageable school
            school_ids = list_school_ids_owned_or_managed(self.request.user)
            if not school_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't manage any schools")
            school = School.objects.get(id=school_ids[0])
        
        # Additional security validation for template content
        self._validate_template_content_security(serializer.validated_data)
        
        serializer.save(school=school, created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Update template with security validation."""
        # Additional security validation for template content
        self._validate_template_content_security(serializer.validated_data)
        serializer.save()
    
    def _validate_template_content_security(self, validated_data):
        """
        Validate template content for security vulnerabilities.
        
        Args:
            validated_data: Dictionary of validated data from serializer
            
        Raises:
            ValidationError: If template content contains security vulnerabilities
        """
        from messaging.services.secure_template_engine import SecureTemplateEngine
        from django.core.exceptions import ValidationError
        from rest_framework.exceptions import ValidationError as DRFValidationError
        
        try:
            # Validate subject template
            if 'subject_template' in validated_data:
                SecureTemplateEngine.validate_template_content(validated_data['subject_template'])
            
            # Validate HTML content
            if 'html_content' in validated_data:
                SecureTemplateEngine.validate_template_content(validated_data['html_content'])
            
            # Validate text content
            if 'text_content' in validated_data:
                SecureTemplateEngine.validate_template_content(validated_data['text_content'])
            
            # Validate custom CSS
            if 'custom_css' in validated_data and validated_data['custom_css']:
                self._validate_custom_css_security(validated_data['custom_css'])
                
        except ValidationError as e:
            raise DRFValidationError(f"Template security validation failed: {str(e)}")
    
    def _validate_custom_css_security(self, css_content):
        """
        Validate custom CSS for security vulnerabilities.
        
        Args:
            css_content: CSS content to validate
            
        Raises:
            ValidationError: If CSS contains dangerous patterns
        """
        import re
        from django.core.exceptions import ValidationError
        
        if not css_content:
            return
        
        # Check for dangerous CSS patterns
        dangerous_patterns = [
            r'@import\s+url\s*\(',
            r'javascript\s*:',
            r'expression\s*\(',
            r'behavior\s*:',
            r'-moz-binding\s*:',
            r'binding\s*:',
            r'<script',
            r'</script>',
            r'alert\s*\(',
            r'eval\s*\(',
            r'document\.',
            r'window\.',
        ]
        
        css_lower = css_content.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, css_lower):
                raise ValidationError(f"Custom CSS contains dangerous pattern: {pattern}")
        
        # Check CSS size
        if len(css_content) > 10000:  # 10KB limit
            raise ValidationError("Custom CSS too large. Maximum size is 10KB")
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Preview an email template with provided variables.
        """
        template = self.get_object()
        
        serializer = EmailTemplatePreviewSerializer(
            data=request.data,
            context={'template': template}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        variables = serializer.validated_data['template_variables']
        
        # Validate template variables for security
        from messaging.services.secure_template_engine import TemplateVariableValidator
        from django.core.exceptions import ValidationError
        
        try:
            TemplateVariableValidator.validate_context(variables)
        except ValidationError as e:
            return Response(
                {"error": f"Template variables validation failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Render the template with variables using secure service
        from messaging.services.email_template_service import EmailTemplateRenderingService
        
        try:
            subject, html_content, text_content = EmailTemplateRenderingService.render_template(
                template, variables, request=self.request
            )
            
            return Response({
                'rendered_subject': subject,
                'rendered_html': html_content,
                'rendered_text': text_content,
                'template_variables': variables,
                'template_id': template.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to preview template {template.id}: {e}")
            return Response(
                {"error": f"Failed to render template preview: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        """
        Get available filter options for templates.
        """
        return Response({
            'template_types': [
                {'value': choice[0], 'label': choice[1]}
                for choice in EmailTemplateType.choices
            ]
        }, status=status.HTTP_200_OK)


class EmailSequenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing email sequences.
    Provides CRUD operations with school-level permissions.
    """
    
    serializer_class = EmailSequenceSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get_queryset(self):
        """Filter sequences by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        return EmailSequence.objects.filter(
            school_id__in=school_ids
        ).select_related('school').prefetch_related('steps__template').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the school field when creating a sequence."""
        school_id = self.request.data.get('school')
        if school_id:
            school_ids = list_school_ids_owned_or_managed(self.request.user)
            if int(school_id) not in school_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to create sequences for this school")
            school = School.objects.get(id=school_id)
        else:
            school_ids = list_school_ids_owned_or_managed(self.request.user)
            if not school_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't manage any schools")
            school = School.objects.get(id=school_ids[0])
        
        serializer.save(school=school)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate or deactivate an email sequence.
        """
        sequence = self.get_object()
        is_active = request.data.get('is_active', True)
        
        sequence.is_active = is_active
        sequence.save(update_fields=['is_active', 'updated_at'])
        
        serializer = self.get_serializer(sequence)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='trigger-events')
    def trigger_events(self, request):
        """
        Get available trigger events for sequences.
        """
        trigger_choices = [
            ("invitation_sent", "Invitation Sent"),
            ("invitation_viewed", "Invitation Viewed"),
            ("invitation_accepted", "Invitation Accepted"),
            ("profile_incomplete", "Profile Incomplete"),
            ("profile_completed", "Profile Completed"),
        ]
        
        return Response({
            'trigger_events': [
                {'value': choice[0], 'label': choice[1]}
                for choice in trigger_choices
            ]
        }, status=status.HTTP_200_OK)


class EmailCommunicationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing email communications.
    Read-only access to communication history with analytics.
    """
    
    serializer_class = EmailCommunicationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get_queryset(self):
        """Filter communications by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        queryset = EmailCommunication.objects.filter(
            school_id__in=school_ids
        ).select_related('school', 'template', 'sequence', 'created_by').order_by('-queued_at')
        
        # Filter by date range if provided
        sent_after = self.request.query_params.get('sent_after')
        sent_before = self.request.query_params.get('sent_before')
        
        if sent_after:
            queryset = queryset.filter(sent_at__gte=sent_after)
        if sent_before:
            queryset = queryset.filter(sent_at__lte=sent_before)
        
        # Filter by communication type
        comm_type = self.request.query_params.get('communication_type')
        if comm_type:
            queryset = queryset.filter(communication_type=comm_type)
        
        # Filter by recipient email
        recipient = self.request.query_params.get('recipient_email')
        if recipient:
            queryset = queryset.filter(recipient_email__icontains=recipient)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get email communication analytics for the user's schools.
        """
        from messaging.services.enhanced_email_service import EmailAnalyticsService
        
        user = request.user
        school_ids = list_school_ids_owned_or_managed(user)
        
        if not school_ids:
            return Response(
                {"error": "You don't manage any schools"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            analytics_service = EmailAnalyticsService()
            
            # Get analytics for all user's schools and aggregate
            total_sent = total_delivered = total_opened = total_clicked = total_bounced = 0
            
            for school_id in school_ids:
                school = School.objects.get(id=school_id)
                school_analytics = analytics_service.get_school_email_stats(school)
                
                # Aggregate the metrics
                total_sent += school_analytics.get('sent_emails', 0)
                total_delivered += school_analytics.get('delivered_emails', 0) 
                total_opened += school_analytics.get('opened_emails', 0)
                total_clicked += school_analytics.get('clicked_emails', 0)
                total_bounced += school_analytics.get('bounced_emails', 0)
            
            # Calculate rates
            delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
            open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
            click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
            bounce_rate = (total_bounced / total_sent * 100) if total_sent > 0 else 0
            
            total_analytics = {
                'total_sent': total_sent,
                'total_delivered': total_delivered,
                'total_opened': total_opened,
                'total_clicked': total_clicked,
                'total_bounced': total_bounced,
                'delivery_rate': round(delivery_rate, 2),
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'bounce_rate': round(bounce_rate, 2)
            }
            
            serializer = EmailAnalyticsSerializer(total_analytics)
            
            return Response({
                'analytics': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get analytics for user {user.id}: {e}")
            return Response(
                {"error": "Failed to retrieve analytics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='communication-types')
    def communication_types(self, request):
        """
        Get available communication types.
        """
        return Response({
            'communication_types': [
                {'value': choice[0], 'label': choice[1]}
                for choice in EmailCommunicationType.choices
            ]
        }, status=status.HTTP_200_OK)


class EnhancedSchoolEmailTemplateViewSet(viewsets.ModelViewSet):
    """
    Enhanced ViewSet for managing school email templates with additional frontend features.
    Extends the existing SchoolEmailTemplateViewSet with preview and testing capabilities.
    """
    
    serializer_class = SchoolEmailTemplateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get_queryset(self):
        """Filter templates by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        return SchoolEmailTemplate.objects.filter(
            school_id__in=school_ids
        ).select_related('school', 'created_by').order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Generate template preview with provided variables."""
        from messaging.services.email_template_service import EmailTemplateRenderingService
        from rest_framework.exceptions import ValidationError as DRFValidationError
        
        template = self.get_object()
        variables = request.data.get('variables', {})
        
        try:
            # Merge with default variables
            rendering_service = EmailTemplateRenderingService()
            context_variables = {**rendering_service.DEFAULT_VARIABLES, **variables}
            
            # Add school-specific variables
            context_variables.update({
                'school_name': template.school.name,
                'school_email': template.school.contact_email,
                'school_primary_color': template.school.primary_color,
                'school_secondary_color': template.school.secondary_color,
            })
            
            # Render the template
            rendered = rendering_service.render_template(template, context_variables)
            
            return Response({
                'subject': rendered['subject'],
                'html_content': rendered['html_content'],
                'text_content': rendered['text_content'],
                'variables_used': list(context_variables.keys())
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Template preview error for template {pk}: {str(e)}")
            return Response({
                'error': 'Failed to generate preview',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        """Send test email with template."""
        from messaging.services.enhanced_email_service import EnhancedEmailService
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        template = self.get_object()
        test_email = request.data.get('test_email')
        variables = request.data.get('variables', {})
        
        # Validate test email
        if not test_email:
            return Response({
                'error': 'test_email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_email(test_email)
        except ValidationError:
            return Response({
                'error': 'Invalid email address'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Prepare context variables
            context_variables = {
                'teacher_name': 'Test User',
                'school_name': template.school.name,
                'school_email': template.school.contact_email,
                **variables
            }
            
            # Send test email
            email_service = EnhancedEmailService()
            success = email_service.send_template_email(
                template=template,
                recipient_email=test_email,
                context_variables=context_variables,
                sender_user=request.user
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Test email sent successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to send test email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Test email send error for template {pk}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to send test email',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommunicationAnalyticsAPIView(APIView):
    """
    API for communication analytics and performance metrics.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get(self, request, *args, **kwargs):
        """Get email performance metrics for user's schools."""
        from django.db.models import Count, Q, Avg
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate date range (last 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Get communications for user's schools
        communications = EmailCommunication.objects.filter(
            school_id__in=school_ids,
            sent_at__gte=start_date,
            sent_at__lte=end_date
        )
        
        # Calculate metrics
        total_sent = communications.count()
        delivered_count = communications.filter(
            delivery_status=EmailDeliveryStatus.DELIVERED
        ).count()
        opened_count = communications.filter(opened_at__isnull=False).count()
        clicked_count = communications.filter(clicked_at__isnull=False).count()
        
        # Calculate rates
        delivery_rate = (delivered_count / total_sent * 100) if total_sent > 0 else 0
        open_rate = (opened_count / delivered_count * 100) if delivered_count > 0 else 0
        click_rate = (clicked_count / opened_count * 100) if opened_count > 0 else 0
        
        # Get recent communications
        recent_communications = communications.order_by('-sent_at')[:10].values(
            'id', 'recipient_email', 'subject', 'delivery_status', 'sent_at'
        )
        
        return Response({
            'period': {
                'start_date': start_date.date(),
                'end_date': end_date.date(),
                'days': 30
            },
            'total_sent': total_sent,
            'delivery_rate': round(delivery_rate, 2),
            'open_rate': round(open_rate, 2),
            'click_rate': round(click_rate, 2),
            'recent_communications': list(recent_communications)
        }, status=status.HTTP_200_OK)


class TemplateAnalyticsAPIView(APIView):
    """
    API for template-specific analytics and usage statistics.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get(self, request, *args, **kwargs):
        """Get template usage and performance statistics."""
        from django.db.models import Count, Q, Avg
        from datetime import datetime, timedelta
        
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get templates for user's schools
        templates = SchoolEmailTemplate.objects.filter(school_id__in=school_ids)
        
        # Calculate analytics for each template
        template_stats = []
        for template in templates:
            communications = template.sent_emails.all()
            
            total_uses = communications.count()
            successful_deliveries = communications.filter(
                delivery_status=EmailDeliveryStatus.DELIVERED
            ).count()
            
            success_rate = (successful_deliveries / total_uses * 100) if total_uses > 0 else 0
            
            template_stats.append({
                'template_id': template.id,
                'template_name': template.name,
                'template_type': template.template_type,
                'usage_count': total_uses,
                'success_rate': round(success_rate, 2),
                'last_used': communications.order_by('-sent_at').first().sent_at if total_uses > 0 else None
            })
        
        # Sort by usage count
        template_stats.sort(key=lambda x: x['usage_count'], reverse=True)
        
        return Response(template_stats, status=status.HTTP_200_OK)


class CommunicationSettingsAPIView(APIView):
    """
    API for managing communication settings and preferences.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get(self, request, *args, **kwargs):
        """Get communication settings for user's school."""
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        school = School.objects.get(id=school_ids[0])
        
        # Get or create school settings
        settings, created = SchoolSettings.objects.get_or_create(
            school=school,
            defaults={
                'communication_settings': {
                    'default_from_email': school.contact_email,
                    'email_signature': f'Best regards,\n{school.name} Team',
                    'auto_sequence_enabled': True,
                    'notification_preferences': {
                        'email_delivery_notifications': True,
                        'bounce_notifications': True
                    }
                }
            }
        )
        
        comm_settings = settings.communication_settings or {}
        
        return Response({
            'default_from_email': comm_settings.get('default_from_email', school.contact_email),
            'email_signature': comm_settings.get('email_signature', f'Best regards,\n{school.name} Team'),
            'auto_sequence_enabled': comm_settings.get('auto_sequence_enabled', True),
            'notification_preferences': comm_settings.get('notification_preferences', {
                'email_delivery_notifications': True,
                'bounce_notifications': True
            })
        }, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        """Update communication settings."""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        school = School.objects.get(id=school_ids[0])
        
        # Validate email if provided
        default_from_email = request.data.get('default_from_email')
        if default_from_email:
            try:
                validate_email(default_from_email)
            except ValidationError:
                return Response({
                    'error': 'Invalid default_from_email format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create school settings
        settings, created = SchoolSettings.objects.get_or_create(
            school=school,
            defaults={'communication_settings': {}}
        )
        
        # Update communication settings
        comm_settings = settings.communication_settings or {}
        
        if 'default_from_email' in request.data:
            comm_settings['default_from_email'] = request.data['default_from_email']
        
        if 'email_signature' in request.data:
            comm_settings['email_signature'] = request.data['email_signature']
        
        if 'auto_sequence_enabled' in request.data:
            comm_settings['auto_sequence_enabled'] = request.data['auto_sequence_enabled']
        
        if 'notification_preferences' in request.data:
            comm_settings['notification_preferences'] = request.data['notification_preferences']
        
        settings.communication_settings = comm_settings
        settings.save()
        
        return Response({
            'message': 'Communication settings updated successfully',
            'settings': comm_settings
        }, status=status.HTTP_200_OK)
