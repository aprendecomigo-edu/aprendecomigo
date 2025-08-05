"""
URL patterns for the messaging app - Issue #107: Student Balance Monitoring & Notification System
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'messaging'

# Router for ViewSets
router = DefaultRouter()
router.register(r'email-templates', views.SchoolEmailTemplateViewSet, basename='email-template')
router.register(r'email-sequences', views.EmailSequenceViewSet, basename='email-sequence')
router.register(r'email-communications', views.EmailCommunicationViewSet, basename='email-communication')
router.register(r'enhanced-email-templates', views.EnhancedSchoolEmailTemplateViewSet, basename='enhanced-email-template')

urlpatterns = [
    # Email communication endpoints (moved from accounts)
    path('api/', include(router.urls)),
    
    # Email communication analytics and settings
    path('api/communication-analytics/', views.CommunicationAnalyticsAPIView.as_view(), name='communication-analytics'),
    path('api/template-analytics/', views.TemplateAnalyticsAPIView.as_view(), name='template-analytics'),
    path('api/communication-settings/', views.CommunicationSettingsAPIView.as_view(), name='communication-settings'),
    
    # Notification endpoints
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('unread-count/', views.NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    
    # Legacy endpoint (kept for backward compatibility)
    path('counts/', views.notification_counts, name='counts'),
]