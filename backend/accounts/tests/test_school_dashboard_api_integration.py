"""
Integration tests for School Dashboard APIs.
Tests the complete implementation of School Metrics and Activity Feed APIs.
"""
import json
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from knox.models import AuthToken

from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole, SchoolActivity, 
    ActivityType, SchoolSettings
)


class SchoolDashboardAPIIntegrationTest(TestCase):
    """Integration tests for School Dashboard APIs."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test users
        self.school_owner = CustomUser.objects.create_user(
            email="owner@school.com",
            name="School Owner",
            password="testpass"
        )
        
        self.teacher = CustomUser.objects.create_user(
            email="teacher@school.com", 
            name="Test Teacher",
            password="testpass"
        )
        
        self.student = CustomUser.objects.create_user(
            email="student@school.com",
            name="Test Student", 
            password="testpass"
        )
        
        self.other_user = CustomUser.objects.create_user(
            email="other@school.com",
            name="Other User",
            password="testpass"
        )
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            contact_email="info@testschool.com"
        )
        
        # Create school settings
        self.school_settings = SchoolSettings.objects.create(
            school=self.school,
            default_session_duration=60,
            timezone="UTC"
        )
        
        # Create another school for authorization testing
        self.other_school = School.objects.create(
            name="Other School",
            description="Another test school"
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.teacher,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.student,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Create membership for other user in other school
        SchoolMembership.objects.create(
            user=self.other_user,
            school=self.other_school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
        # Create some test activities
        self.create_test_activities()
        
        # Get authentication tokens
        self.owner_token = AuthToken.objects.create(self.school_owner)[1]
        self.teacher_token = AuthToken.objects.create(self.teacher)[1]
        self.other_user_token = AuthToken.objects.create(self.other_user)[1]
    
    def create_test_activities(self):
        """Create test school activities."""
        now = timezone.now()
        
        # Create activities for the last few days
        for i in range(5):
            timestamp = now - timedelta(days=i)
            
            SchoolActivity.objects.create(
                school=self.school,
                activity_type=ActivityType.TEACHER_JOINED,
                timestamp=timestamp,
                actor=self.school_owner,
                target_user=self.teacher,
                description=f"Teacher joined the school {i} days ago",
                metadata={"day": i}
            )
            
            SchoolActivity.objects.create(
                school=self.school,
                activity_type=ActivityType.STUDENT_JOINED,
                timestamp=timestamp,
                actor=self.school_owner,
                target_user=self.student,
                description=f"Student joined the school {i} days ago",
                metadata={"day": i}
            )
    
    


class SchoolMetricsAPITest(SchoolDashboardAPIIntegrationTest):
    """Tests for the School Metrics API endpoint."""
    
    def test_metrics_endpoint_url_resolution(self):
        """Test that the metrics endpoint URL resolves correctly."""
        url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        self.assertEqual(url, f'/api/accounts/schools/{self.school.id}/metrics/')
    
    def test_metrics_requires_authentication(self):
        """Test that metrics endpoint requires authentication."""
        url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_metrics_requires_proper_authorization(self):
        """Test that users can only access metrics for their own schools."""
        # Try to access with other user's token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_user_token}')
        url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_metrics_returns_correct_structure(self):
        """Test that metrics endpoint returns the correct data structure."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check top-level structure
        self.assertIn('student_count', data)
        self.assertIn('teacher_count', data)
        self.assertIn('class_metrics', data)
        self.assertIn('engagement_metrics', data)
        
        # Check student_count structure
        student_count = data['student_count']
        self.assertIn('total', student_count)
        self.assertIn('active', student_count)
        self.assertIn('inactive', student_count)
        self.assertIn('trend', student_count)
        
        # Check teacher_count structure
        teacher_count = data['teacher_count']
        self.assertIn('total', teacher_count)
        self.assertIn('active', teacher_count)
        self.assertIn('inactive', teacher_count)
        self.assertIn('trend', teacher_count)
        
        # Check class_metrics structure
        class_metrics = data['class_metrics']
        self.assertIn('active_classes', class_metrics)
        self.assertIn('completed_today', class_metrics)
        self.assertIn('scheduled_today', class_metrics)
        self.assertIn('completion_rate', class_metrics)
        self.assertIn('trend', class_metrics)
        
        # Check engagement_metrics structure
        engagement_metrics = data['engagement_metrics']
        self.assertIn('invitations_sent', engagement_metrics)
        self.assertIn('invitations_accepted', engagement_metrics)
        self.assertIn('acceptance_rate', engagement_metrics)
        self.assertIn('avg_time_to_accept', engagement_metrics)
    
    def test_metrics_returns_correct_counts(self):
        """Test that metrics returns accurate counts."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify student counts
        self.assertEqual(data['student_count']['total'], 1)
        self.assertEqual(data['student_count']['active'], 1)
        self.assertEqual(data['student_count']['inactive'], 0)
        
        # Verify teacher counts
        self.assertEqual(data['teacher_count']['total'], 1)
        self.assertEqual(data['teacher_count']['active'], 1)
        self.assertEqual(data['teacher_count']['inactive'], 0)
        
        # Verify engagement metrics (will be 0 since we don't have invitations in this simplified test)
        self.assertEqual(data['engagement_metrics']['invitations_sent'], 0)
        self.assertEqual(data['engagement_metrics']['invitations_accepted'], 0)
        self.assertEqual(data['engagement_metrics']['acceptance_rate'], 0.0)
    
    def test_metrics_response_performance(self):
        """Test that metrics API responds within acceptable time limits."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        
        start_time = timezone.now()
        response = self.client.get(url)
        end_time = timezone.now()
        
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response should be under 200ms as per requirements
        self.assertLess(response_time_ms, 200)
    
    @patch('accounts.services.metrics_service.cache')
    def test_metrics_caching_behavior(self, mock_cache):
        """Test that metrics are properly cached."""
        mock_cache.get.return_value = None  # First call - no cache
        mock_cache.set.return_value = None
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        
        # First request should calculate and cache
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cache.set was called
        self.assertTrue(mock_cache.set.called)
        
        # Second request should use cache
        mock_cache.get.return_value = {
            'student_count': {'total': 1, 'active': 1, 'inactive': 0, 'trend': {}},
            'teacher_count': {'total': 1, 'active': 1, 'inactive': 0, 'trend': {}},
            'class_metrics': {'active_classes': 0, 'completed_today': 0, 'scheduled_today': 0, 'completion_rate': 0, 'trend': {}},
            'engagement_metrics': {'invitations_sent': 0, 'invitations_accepted': 0, 'acceptance_rate': 0, 'avg_time_to_accept': '00:00:00'}
        }
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_metrics_nonexistent_school(self):
        """Test metrics endpoint for non-existent school."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-dashboard-metrics', kwargs={'pk': 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_metrics_teacher_access(self):
        """Test that teachers can access metrics for their school."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        # Teachers should have read access to metrics
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SchoolActivityAPITest(SchoolDashboardAPIIntegrationTest):
    """Tests for the School Activity Feed API endpoint."""
    
    def test_activity_endpoint_url_resolution(self):
        """Test that the activity endpoint URL resolves correctly."""
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        self.assertEqual(url, f'/api/accounts/schools/{self.school.id}/activity/')
    
    def test_activity_requires_authentication(self):
        """Test that activity endpoint requires authentication."""
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_activity_requires_proper_authorization(self):
        """Test that users can only access activity for their own schools."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_user_token}')
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_activity_returns_paginated_response(self):
        """Test that activity endpoint returns properly paginated data."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check pagination structure
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('results', data)
        
        # Should have activities we created
        self.assertGreater(data['count'], 0)
        self.assertIsInstance(data['results'], list)
    
    def test_activity_returns_correct_structure(self):
        """Test that activity items have the correct structure."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        if data['results']:
            activity = data['results'][0]
            
            # Check required fields
            self.assertIn('id', activity)
            self.assertIn('activity_type', activity)
            self.assertIn('timestamp', activity)
            self.assertIn('description', activity)
            self.assertIn('actor', activity)
            self.assertIn('metadata', activity)
    
    def test_activity_pagination_parameters(self):
        """Test activity endpoint pagination parameters."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        
        # Test page size parameter
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url, {'page_size': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should respect page_size parameter
        self.assertLessEqual(len(data['results']), 5)
    
    def test_activity_type_filtering(self):
        """Test activity endpoint filtering by activity type."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        
        # Filter by teacher activities only
        response = self.client.get(url, {'activity_types': 'teacher_joined'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # All results should be teacher_joined activities
        for activity in data['results']:
            self.assertEqual(activity['activity_type'], 'teacher_joined')
    
    def test_activity_date_filtering(self):
        """Test activity endpoint filtering by date range."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        
        # Get today's date for filtering
        today = timezone.now().date().isoformat()
        
        response = self.client.get(url, {'date_from': today})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # All results should be from today or later
        for activity in data['results']:
            activity_date = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00')).date()
            self.assertGreaterEqual(activity_date, timezone.now().date())
    
    def test_activity_ordering(self):
        """Test that activities are ordered by timestamp (newest first)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        if len(data['results']) > 1:
            # Check that activities are ordered by timestamp (newest first)
            for i in range(len(data['results']) - 1):
                current_time = datetime.fromisoformat(data['results'][i]['timestamp'].replace('Z', '+00:00'))
                next_time = datetime.fromisoformat(data['results'][i+1]['timestamp'].replace('Z', '+00:00'))
                self.assertGreaterEqual(current_time, next_time)
    
    def test_activity_teacher_access(self):
        """Test that teachers can access activity feed for their school."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        # Teachers should have read access to activity feed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_activity_invalid_parameters(self):
        """Test activity endpoint with invalid parameters."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        
        # Test with invalid page parameter
        response = self.client.get(url, {'page': 'invalid'})
        # Should return 400 or gracefully handle with default page
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        
        # Test with invalid date format
        response = self.client.get(url, {'date_from': 'invalid-date'})
        # Should return 400 or ignore invalid date
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


class SchoolDashboardPermissionsTest(SchoolDashboardAPIIntegrationTest):
    """Test permissions and authorization for school dashboard APIs."""
    
    def test_school_owner_full_access(self):
        """Test that school owners have full access to dashboard APIs."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
        
        # Test metrics access
        metrics_url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(metrics_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test activity access
        activity_url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_teacher_read_access(self):
        """Test that teachers have read access to dashboard APIs."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        # Test metrics access
        metrics_url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(metrics_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test activity access
        activity_url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cross_school_access_denied(self):
        """Test that users cannot access other schools' dashboard data."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_user_token}')
        
        # Try to access our school's metrics
        metrics_url = reverse('accounts:school-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(metrics_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try to access our school's activity
        activity_url = reverse('accounts:school-activity', kwargs={'pk': self.school.id})
        response = self.client.get(activity_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)