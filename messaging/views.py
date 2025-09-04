"""
Messaging views converted to Django CBVs with HTMX for PWA migration.

Key Features:
1. Notifications System (list, detail, mark read, unread count)
2. Email Communications (tracking and analytics)
3. School Email Templates (CRUD operations)
"""

import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from accounts.db_queries import list_school_ids_owned_or_managed
from accounts.models import School
from accounts.permissions import IsSchoolOwnerOrAdminMixin

from .models import (
    EmailCommunication,
    EmailCommunicationType,
    EmailDeliveryStatus,
    EmailTemplateType,
    Notification,
    SchoolEmailTemplate,
)

logger = logging.getLogger(__name__)


# =======================
# NOTIFICATION VIEWS
# =======================


# =======================
# NOTIFICATION VIEWS
# =======================


class NotificationListView(LoginRequiredMixin, ListView):
    """
    List notifications for the authenticated user with pagination and filtering.

    GET /notifications/
    GET /notifications/?notification_type=low_balance
    GET /notifications/?is_read=false

    HTMX: Returns partial template for dynamic updates
    """
    model = Notification
    template_name = 'messaging/notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        """Return notifications for the authenticated user with filtering support."""
        queryset = (
            Notification.objects.filter(user=self.request.user)
            .select_related("related_transaction")
            .order_by("-created_at")
        )

        # Apply filters based on query parameters
        notification_type = self.request.GET.get("notification_type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        is_read = self.request.GET.get("is_read")
        if is_read is not None:
            is_read_bool = is_read.lower() in ("true", "1", "yes")
            queryset = queryset.filter(is_read=is_read_bool)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter options for template
        context['notification_types'] = [
            ('low_balance', 'Low Balance'),
            ('package_expiring', 'Package Expiring'),
            ('balance_depleted', 'Balance Depleted'),
        ]

        # Current filter values
        context['current_type'] = self.request.GET.get('notification_type', '')
        context['current_read_status'] = self.request.GET.get('is_read', '')

        # Unread count for badge
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user, is_read=False
        ).count()

        return context

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if self.request.htmx:
            return ['messaging/notifications/partials/notification_list_content.html']
        return [self.template_name]


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """
    Get detailed information about a specific notification.

    GET /notifications/{id}/

    Users can only access their own notifications.
    """
    model = Notification
    template_name = 'messaging/notifications/notification_detail.html'
    context_object_name = 'notification'

    def get_queryset(self):
        """Return notifications for the authenticated user only."""
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(LoginRequiredMixin, View):
    """
    Mark a specific notification as read.

    POST /notifications/{id}/mark-read/

    HTMX: Returns updated notification item or unread count
    """

    def post(self, request, pk):
        """Mark notification as read."""
        notification = get_object_or_404(
            Notification, pk=pk, user=request.user
        )

        # Mark as read if not already read
        if not notification.is_read:
            notification.mark_as_read()

        # Return appropriate response based on request type
        if request.htmx:
            # Return updated notification item for HTMX
            return render(request, 'messaging/notifications/partials/notification_item.html', {
                'notification': notification
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'Notification marked as read'
            })


class NotificationUnreadCountView(LoginRequiredMixin, View):
    """
    Get the count of unread notifications for the authenticated user.

    GET /notifications/unread-count/

    Used for UI badge display with HTMX polling.
    """

    def get(self, request):
        """Return unread notification count."""
        unread_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

        if request.htmx:
            # Return badge partial for HTMX updates
            return render(request, 'messaging/notifications/partials/unread_count.html', {
                'unread_count': unread_count
            })
        else:
            return JsonResponse({'unread_count': unread_count})




# =======================
# EMAIL TEMPLATE VIEWS
# =======================


class SchoolEmailTemplateListView(IsSchoolOwnerOrAdminMixin, ListView):
    """
    List email templates for user's schools.

    GET /email-templates/
    """
    model = SchoolEmailTemplate
    template_name = 'messaging/email_templates/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20

    def get_queryset(self):
        """Filter templates by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        if not school_ids:
            return SchoolEmailTemplate.objects.none()

        return (
            SchoolEmailTemplate.objects.filter(school_id__in=school_ids)
            .select_related("school", "created_by")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add template type options
        context['template_types'] = EmailTemplateType.choices

        # Current user's schools
        school_ids = list_school_ids_owned_or_managed(self.request.user)
        context['user_schools'] = School.objects.filter(id__in=school_ids)

        return context

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if self.request.htmx:
            return ['messaging/email_templates/partials/template_list_content.html']
        return [self.template_name]


class SchoolEmailTemplateDetailView(IsSchoolOwnerOrAdminMixin, DetailView):
    """
    View email template details.

    GET /email-templates/{id}/
    """
    model = SchoolEmailTemplate
    template_name = 'messaging/email_templates/template_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        """Filter templates by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        return SchoolEmailTemplate.objects.filter(school_id__in=school_ids)


class SchoolEmailTemplateCreateView(IsSchoolOwnerOrAdminMixin, TemplateView):
    """
    Create new email template.

    GET /email-templates/create/ - Show form
    POST /email-templates/create/ - Create template
    """
    template_name = 'messaging/email_templates/template_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Template type options
        context['template_types'] = EmailTemplateType.choices

        # Current user's schools
        school_ids = list_school_ids_owned_or_managed(self.request.user)
        context['user_schools'] = School.objects.filter(id__in=school_ids)

        return context

    def post(self, request):
        """Create new email template."""
        try:
            # Validate user has permission to manage schools
            school_ids = list_school_ids_owned_or_managed(request.user)
            if not school_ids:
                raise PermissionDenied("You don't manage any schools")

            # Get school from form data
            school_id = request.POST.get('school')
            if not school_id or int(school_id) not in school_ids:
                raise PermissionDenied("Invalid school selection")

            school = School.objects.get(id=school_id)

            # Create template
            template = SchoolEmailTemplate.objects.create(
                school=school,
                template_type=request.POST.get('template_type'),
                name=request.POST.get('name'),
                subject_template=request.POST.get('subject_template'),
                html_content=request.POST.get('html_content'),
                text_content=request.POST.get('text_content'),
                use_school_branding=request.POST.get('use_school_branding') == 'on',
                custom_css=request.POST.get('custom_css', ''),
                created_by=request.user,
            )

            if request.htmx:
                # Return success partial for HTMX
                return render(request, 'messaging/email_templates/partials/create_success.html', {
                    'template': template
                })
            else:
                return JsonResponse({
                    'success': True,
                    'template_id': template.id,
                    'message': 'Template created successfully'
                })

        except Exception as e:
            logger.error(f"Failed to create template: {e}")

            if request.htmx:
                return render(request, 'messaging/email_templates/partials/create_error.html', {
                    'error': str(e)
                })
            else:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)


class SchoolEmailTemplateEditView(IsSchoolOwnerOrAdminMixin, DetailView):
    """
    Edit email template.

    GET /email-templates/{id}/edit/ - Show edit form
    POST /email-templates/{id}/edit/ - Update template
    """
    model = SchoolEmailTemplate
    template_name = 'messaging/email_templates/template_edit.html'
    context_object_name = 'template'

    def get_queryset(self):
        """Filter templates by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        return SchoolEmailTemplate.objects.filter(school_id__in=school_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Template type options
        context['template_types'] = EmailTemplateType.choices

        # Current user's schools
        school_ids = list_school_ids_owned_or_managed(self.request.user)
        context['user_schools'] = School.objects.filter(id__in=school_ids)

        return context

    def post(self, request, pk):
        """Update email template."""
        template = self.get_object()

        try:
            # Update template fields
            template.name = request.POST.get('name', template.name)
            template.subject_template = request.POST.get('subject_template', template.subject_template)
            template.html_content = request.POST.get('html_content', template.html_content)
            template.text_content = request.POST.get('text_content', template.text_content)
            template.use_school_branding = request.POST.get('use_school_branding') == 'on'
            template.custom_css = request.POST.get('custom_css', '')
            template.is_active = request.POST.get('is_active') == 'on'

            template.save()

            if request.htmx:
                # Return success partial for HTMX
                return render(request, 'messaging/email_templates/partials/edit_success.html', {
                    'template': template
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': 'Template updated successfully'
                })

        except Exception as e:
            logger.error(f"Failed to update template {pk}: {e}")

            if request.htmx:
                return render(request, 'messaging/email_templates/partials/edit_error.html', {
                    'error': str(e)
                })
            else:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)


class SchoolEmailTemplatePreviewView(IsSchoolOwnerOrAdminMixin, DetailView):
    """
    Preview email template with variables.

    POST /email-templates/{id}/preview/
    """
    model = SchoolEmailTemplate
    template_name = 'messaging/email_templates/partials/template_preview.html'

    def get_queryset(self):
        """Filter templates by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        return SchoolEmailTemplate.objects.filter(school_id__in=school_ids)

    def post(self, request, pk):
        """Generate template preview with provided variables."""
        template = self.get_object()

        try:
            # Get template variables from request
            variables = json.loads(request.POST.get('variables', '{}'))

            # Render template with variables using secure service
            from messaging.services.email_template_service import EmailTemplateRenderingService

            subject, html_content, text_content = EmailTemplateRenderingService.render_template(
                template, variables, request=request
            )

            context = {
                'template': template,
                'rendered_subject': subject,
                'rendered_html': html_content,
                'rendered_text': text_content,
                'variables': variables,
            }

            return render(request, self.template_name, context)

        except Exception as e:
            logger.error(f"Failed to preview template {pk}: {e}")
            return render(request, 'messaging/email_templates/partials/preview_error.html', {
                'error': str(e)
            })


# =======================
# EMAIL COMMUNICATION VIEWS
# =======================


class EmailCommunicationListView(IsSchoolOwnerOrAdminMixin, ListView):
    """
    List email communications with filtering.

    GET /communications/
    """
    model = EmailCommunication
    template_name = 'messaging/communications/email_list.html'
    context_object_name = 'communications'
    paginate_by = 20

    def get_queryset(self):
        """Filter communications by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        if not school_ids:
            return EmailCommunication.objects.none()

        queryset = (
            EmailCommunication.objects.filter(school_id__in=school_ids)
            .select_related("school", "template", "sequence", "created_by")
            .order_by("-queued_at")
        )

        # Filter by date range if provided
        sent_after = self.request.GET.get("sent_after")
        sent_before = self.request.GET.get("sent_before")

        if sent_after:
            queryset = queryset.filter(sent_at__gte=sent_after)
        if sent_before:
            queryset = queryset.filter(sent_at__lte=sent_before)

        # Filter by communication type
        comm_type = self.request.GET.get("communication_type")
        if comm_type:
            queryset = queryset.filter(communication_type=comm_type)

        # Filter by recipient email
        recipient = self.request.GET.get("recipient_email")
        if recipient:
            queryset = queryset.filter(recipient_email__icontains=recipient)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter options
        context['communication_types'] = EmailCommunicationType.choices
        context['delivery_statuses'] = EmailDeliveryStatus.choices

        return context

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if self.request.htmx:
            return ['messaging/communications/partials/email_list_content.html']
        return [self.template_name]


class EmailAnalyticsView(IsSchoolOwnerOrAdminMixin, TemplateView):
    """
    Display email analytics dashboard.

    GET /communications/analytics/
    """
    template_name = 'messaging/communications/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)

        if school_ids:
            from datetime import timedelta

            from django.utils import timezone

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

            context.update({
                'period_start': start_date.date(),
                'period_end': end_date.date(),
                'total_sent': total_sent,
                'delivery_rate': round(delivery_rate, 2),
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'recent_communications': communications.order_by("-sent_at")[:10],
            })

        return context


