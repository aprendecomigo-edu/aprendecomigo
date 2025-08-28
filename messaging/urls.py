"""
URL patterns for the messaging app - Converted to Django views with HTMX for PWA migration.
"""

from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    # =======================
    # NOTIFICATION URLS
    # =======================
    
    # Notification list and filtering
    path("notifications/", views.NotificationListView.as_view(), name="notification-list"),
    
    # Notification detail
    path("notifications/<int:pk>/", views.NotificationDetailView.as_view(), name="notification-detail"),
    
    # Mark notification as read (HTMX endpoint)
    path("notifications/<int:pk>/mark-read/", views.NotificationMarkReadView.as_view(), name="notification-mark-read"),
    
    # Unread count badge (HTMX polling endpoint)
    path("notifications/unread-count/", views.NotificationUnreadCountView.as_view(), name="notification-unread-count"),
    

    # =======================
    # EMAIL TEMPLATE URLS
    # =======================
    
    # Email template management
    path("email-templates/", views.SchoolEmailTemplateListView.as_view(), name="template-list"),
    path("email-templates/create/", views.SchoolEmailTemplateCreateView.as_view(), name="template-create"),
    path("email-templates/<int:pk>/", views.SchoolEmailTemplateDetailView.as_view(), name="template-detail"),
    path("email-templates/<int:pk>/edit/", views.SchoolEmailTemplateEditView.as_view(), name="template-edit"),
    
    # Template preview (HTMX endpoint)
    path("email-templates/<int:pk>/preview/", views.SchoolEmailTemplatePreviewView.as_view(), name="template-preview"),

    # =======================
    # EMAIL COMMUNICATION URLS
    # =======================
    
    # Email communications list and analytics
    path("communications/", views.EmailCommunicationListView.as_view(), name="communication-list"),
    path("communications/analytics/", views.EmailAnalyticsView.as_view(), name="email-analytics"),

]