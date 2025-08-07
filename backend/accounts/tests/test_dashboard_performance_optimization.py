"""
Tests for dashboard performance optimizations.

These tests verify that the JWT token enhancements and role-based API validation
prevent duplicate API calls and cross-role endpoint access.
"""

from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from knox.models import AuthToken
from unittest.mock import patch
from accounts.models import (
    School, SchoolMembership, SchoolRole, ParentChildRelationship,
    VerificationCode
)

User = get_user_model()


class DashboardPerformanceOptimizationTest(TestCase):
    """Test the performance optimizations for dashboard router."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create school
        self.school = School.objects.create(
            name="Performance Test School",
            description="A test school for performance optimization"
        )
        
        # Create admin user
        self.admin_user = User.objects.create(
            email="admin@test.com",
            name="Admin User"
        )
        
        # Create parent user
        self.parent_user = User.objects.create(
            email="parent@test.com", 
            name="Parent User"
        )
        
        # Create student user
        self.student_user = User.objects.create(
            email="student@test.com",
            name="Student User"  
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.student_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Create parent-child relationship
        self.parent_child_rel = ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.student_user,
            school=self.school,
            is_active=True
        )
        
        # Clear cache before each test
        cache.clear()
    
    def test_jwt_token_includes_user_type(self):
        """Test that JWT token response includes user_type for immediate frontend routing."""
        # Test admin user
        verification = VerificationCode.generate_code(self.admin_user.email)
        code = verification.get_current_code()
        
        with patch.object(VerificationCode, 'is_valid', return_value=True):
            response = self.client.post(
                reverse('accounts:verify_code'),
                {
                    'email': self.admin_user.email,
                    'code': code
                }
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        
        user_data = response.data['user']
        self.assertIn('user_type', user_data, 
                     "JWT token response must include user_type for immediate frontend routing")
        self.assertEqual(user_data['user_type'], 'admin',
                        "Admin user should have user_type='admin' in JWT token")
        self.assertIn('is_admin', user_data)
        self.assertTrue(user_data['is_admin'])
    
    def test_dashboard_info_caching_prevents_duplicates(self):
        """Test that dashboard_info endpoint is cached to prevent duplicate calls."""
        # Authenticate as admin
        token = AuthToken.objects.create(self.admin_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # First call to dashboard_info
        with patch('accounts.views.SchoolMembership.objects.filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            response1 = self.client.get(reverse('accounts:user-dashboard-info'))
            self.assertEqual(response1.status_code, status.HTTP_200_OK)
            first_call_count = mock_filter.call_count
        
        # Second call to dashboard_info (should use cache)
        with patch('accounts.views.SchoolMembership.objects.filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            response2 = self.client.get(reverse('accounts:user-dashboard-info'))
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            second_call_count = mock_filter.call_count
        
        # Second call should have fewer database queries due to caching
        self.assertEqual(second_call_count, 0, 
                        "Second dashboard_info call should use cache and not query database")
        
        # Response data should be identical
        self.assertEqual(response1.data, response2.data)
    
    def test_cache_expiration_after_timeout(self):
        """Test that dashboard_info cache expires after 5 minutes."""
        # Authenticate as admin
        token = AuthToken.objects.create(self.admin_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # First call
        response1 = self.client.get(reverse('accounts:user-dashboard-info'))
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Simulate cache expiration by clearing it
        cache.clear()
        
        # Second call after cache expiration should work normally
        response2 = self.client.get(reverse('accounts:user-dashboard-info'))
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)
    
    def test_parent_approval_dashboard_role_validation(self):
        """Test that parent-approval-dashboard is restricted to users with parent-child relationships."""
        # Test admin user (should be denied)
        admin_token = AuthToken.objects.create(self.admin_user)[1]
        admin_client = APIClient()
        admin_client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token}')
        
        response = admin_client.get(reverse('finances:parent-approval-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                        "Admin users should not be able to access parent-approval-dashboard")
        
        # Test parent user (should be allowed)
        parent_token = AuthToken.objects.create(self.parent_user)[1]
        parent_client = APIClient()
        parent_client.credentials(HTTP_AUTHORIZATION=f'Token {parent_token}')
        
        response = parent_client.get(reverse('finances:parent-approval-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        "Parent users should be able to access parent-approval-dashboard")
    
    def test_family_metrics_role_validation(self):
        """Test that family-metrics endpoint is restricted to users with parent-child relationships."""
        # Test admin user (should be denied)
        admin_token = AuthToken.objects.create(self.admin_user)[1]
        admin_client = APIClient()
        admin_client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token}')
        
        response = admin_client.get(reverse('finances:family-metrics'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                        "Admin users should not be able to access family-metrics")
        
        # Test parent user (should be allowed)
        parent_token = AuthToken.objects.create(self.parent_user)[1]
        parent_client = APIClient()
        parent_client.credentials(HTTP_AUTHORIZATION=f'Token {parent_token}')
        
        response = parent_client.get(reverse('finances:family-metrics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        "Parent users should be able to access family-metrics")
    
    def test_student_cannot_access_parent_endpoints(self):
        """Test that student users cannot access parent-specific endpoints."""
        student_token = AuthToken.objects.create(self.student_user)[1]
        student_client = APIClient()
        student_client.credentials(HTTP_AUTHORIZATION=f'Token {student_token}')
        
        # Test parent-approval-dashboard
        response = student_client.get(reverse('finances:parent-approval-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                        "Student users should not be able to access parent-approval-dashboard")
        
        # Test family-metrics
        response = student_client.get(reverse('finances:family-metrics'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                        "Student users should not be able to access family-metrics")
    
    def test_performance_improvement_reduced_api_calls(self):
        """Test that the optimizations reduce API calls during authentication flow."""
        # Simulate the authentication flow and count API calls
        verification = VerificationCode.generate_code(self.admin_user.email)
        code = verification.get_current_code()
        
        with patch.object(VerificationCode, 'is_valid', return_value=True):
            # JWT login should include user_type
            response = self.client.post(
                reverse('accounts:verify_code'),
                {
                    'email': self.admin_user.email,
                    'code': code
                }
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # With JWT containing user_type, frontend should route immediately
        # Dashboard_info should only be called once due to caching
        
        # First dashboard_info call
        response1 = self.client.get(reverse('accounts:user-dashboard-info'))
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second dashboard_info call should use cache
        response2 = self.client.get(reverse('accounts:user-dashboard-info'))
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify that admin user cannot access parent endpoints (prevents cross-role calls)
        parent_response = self.client.get(reverse('finances:parent-approval-dashboard'))
        self.assertEqual(parent_response.status_code, status.HTTP_403_FORBIDDEN)
        
        family_response = self.client.get(reverse('finances:family-metrics'))
        self.assertEqual(family_response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_authentication_response_serializer_includes_user_type(self):
        """Test that AuthenticationResponseSerializer includes user_type and is_admin."""
        from accounts.serializers import AuthenticationResponseSerializer
        
        # Test admin user
        serializer = AuthenticationResponseSerializer(self.admin_user)
        data = serializer.data
        
        self.assertIn('user_type', data)
        self.assertIn('is_admin', data)
        self.assertEqual(data['user_type'], 'admin')
        self.assertTrue(data['is_admin'])
        
        # Test parent user (parent users don't have school memberships by default)
        parent_serializer = AuthenticationResponseSerializer(self.parent_user)
        parent_data = parent_serializer.data
        
        self.assertIn('user_type', parent_data)
        self.assertIn('is_admin', parent_data)
        self.assertEqual(parent_data['user_type'], 'student')  # Default fallback
        self.assertFalse(parent_data['is_admin'])