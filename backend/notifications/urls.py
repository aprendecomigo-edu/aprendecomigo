"""
URL patterns for the notifications app - Issue #107: Student Balance Monitoring & Notification System
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # New notification endpoints
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('unread-count/', views.NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    
    # Legacy endpoint (kept for backward compatibility)
    path('counts/', views.notification_counts, name='counts'),
]