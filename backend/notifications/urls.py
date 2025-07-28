"""
URL patterns for the notifications app.
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('counts/', views.notification_counts, name='counts'),
]