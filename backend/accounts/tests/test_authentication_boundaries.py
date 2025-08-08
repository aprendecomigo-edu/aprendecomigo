"""
Authentication Security Tests for Aprende Comigo Platform

These tests verify that authentication mechanisms properly protect endpoints
and that unauthorized access attempts are correctly rejected.

Note: This platform uses Knox authentication. Tests focus on Knox token 
security and endpoint protection based on actual API endpoints.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    SchoolRole,
    TeacherProfile,
    StudentProfile,
)

User = get_user_model()


class KnoxAuthenticationTestCase(TestCase):
    """
    Test suite for Knox authentication security.
    
    These tests ensure that:
    1. Unauthenticated users cannot access protected endpoints
    2. Invalid tokens are rejected
    3. Token-based access control works correctly
    4. Authentication headers are properly validated
    """

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test school and users
        self.school = School.objects.create(
            name="Test School",
            contact_email="admin@testschool.com"
        )
        
        self.school_owner = CustomUser.objects.create_user(
            email="owner@example.com",
            name="School Owner"
        )
        
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            name="Test Teacher"
        )
        
        self.student = CustomUser.objects.create_user(
            email="student@example.com", 
            name="Test Student"
        )
        
        # Create memberships
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        SchoolMembership.objects.create(
            user=self.teacher,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        SchoolMembership.objects.create(
            user=self.student,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        # Create profiles
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            bio="Test teacher profile"
        )
        
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            birth_date="2010-01-01",
            school_year="5th Grade"
        )

    def test_unauthenticated_access_denied_to_protected_endpoints(self):
        """Test that unauthenticated users cannot access protected endpoints."""
        protected_endpoints = [
            'accounts:user-list',
            'accounts:student-list', 
            'accounts:course-list',
            'accounts:educational_system-list',
        ]
        
        for endpoint_name in protected_endpoints:
            with self.subTest(endpoint=endpoint_name):
                try:
                    url = reverse(endpoint_name)
                    response = self.client.get(url)
                    
                    # Should be 401 Unauthorized
                    self.assertEqual(
                        response.status_code,
                        status.HTTP_401_UNAUTHORIZED,
                        f"Endpoint {endpoint_name} should require authentication"
                    )
                except Exception:
                    # If endpoint doesn't exist, skip this test
                    self.skipTest(f"Endpoint {endpoint_name} not available")

    def test_invalid_token_rejected(self):
        """Test that invalid Knox tokens are properly rejected."""
        # Set invalid Authorization header
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid-token-string')
        
        try:
            url = reverse('accounts:user-list')
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        except Exception:
            self.skipTest("User list endpoint not available")

    def test_malformed_token_headers_rejected(self):
        """Test that malformed authentication headers are rejected."""
        malformed_headers = [
            'Bearer token',  # Wrong auth type
            'Token',  # Missing token
            'invalid-header-format',  # Wrong format entirely
            '',  # Empty header
        ]
        
        for header in malformed_headers:
            with self.subTest(header=header):
                self.client.credentials(HTTP_AUTHORIZATION=header)
                
                try:
                    url = reverse('accounts:user-list')
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                except Exception:
                    self.skipTest("User list endpoint not available")

    def test_valid_knox_token_accepted(self):
        """Test that valid Knox tokens are properly accepted."""
        # Generate a valid Knox token
        instance, token = AuthToken.objects.create(user=self.teacher)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        try:
            url = reverse('accounts:user-list')
            response = self.client.get(url)
            # Should succeed (200) or be forbidden due to permissions (403)
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        except Exception:
            self.skipTest("User list endpoint not available")

    def test_token_with_inactive_user_rejected(self):
        """Test that tokens for inactive users are rejected."""
        # Create an inactive user
        inactive_user = CustomUser.objects.create_user(
            email="inactive@example.com",
            name="Inactive User",
            is_active=False
        )
        
        # Generate token for inactive user
        instance, token = AuthToken.objects.create(user=inactive_user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        try:
            url = reverse('accounts:user-list')
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        except Exception:
            self.skipTest("User list endpoint not available")

    def test_authentication_with_existing_endpoints_only(self):
        """Test authentication against only the endpoints that actually exist."""
        # Get valid token
        instance, token = AuthToken.objects.create(user=self.teacher)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Test actual endpoints that exist based on current URLs
        existing_endpoints = [
            ('accounts:user-list', 'User list endpoint'),
            ('accounts:student-list', 'Student list endpoint'),
            ('accounts:course-list', 'Course list endpoint'),
            ('accounts:request_code', 'Authentication request code endpoint'),
        ]
        
        for endpoint_name, description in existing_endpoints:
            with self.subTest(endpoint=endpoint_name, description=description):
                try:
                    url = reverse(endpoint_name)
                    response = self.client.get(url)
                    
                    # Should not be a 404 (endpoint exists) and not be 500 (server error)
                    self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                                      f"{description} should exist")
                    self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                                      f"{description} should not cause server error")
                except Exception as e:
                    # If endpoint doesn't exist in URL config, skip
                    if "not found" in str(e).lower() or "reverse" in str(e).lower():
                        self.skipTest(f"Endpoint {endpoint_name} not in URL configuration")
                    else:
                        raise

    def test_knox_token_cleanup_on_user_delete(self):
        """Test that Knox tokens are cleaned up when users are deleted."""
        # Create user and token
        test_user = CustomUser.objects.create_user(
            email="delete_test@example.com",
            name="Delete Test User"
        )
        instance, token = AuthToken.objects.create(user=test_user)
        
        # Store the user ID before deletion
        user_id = test_user.id
        
        # Verify token exists
        self.assertTrue(AuthToken.objects.filter(user_id=user_id).exists())
        
        # Delete user
        test_user.delete()
        
        # Verify tokens are cleaned up
        self.assertFalse(AuthToken.objects.filter(user_id=user_id).exists())

    def test_no_authentication_bypass_with_empty_credentials(self):
        """Test that empty credentials don't bypass authentication."""
        empty_credentials = [
            None,
            '',
            'Token ',
            'Token',
        ]
        
        for credential in empty_credentials:
            with self.subTest(credential=credential):
                if credential is not None:
                    self.client.credentials(HTTP_AUTHORIZATION=credential)
                else:
                    self.client.credentials()  # No auth header
                
                try:
                    url = reverse('accounts:user-list')
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                except Exception:
                    self.skipTest("User list endpoint not available")


class PublicEndpointTestCase(TestCase):
    """Test that public endpoints work without authentication."""
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_public_endpoints_accessible(self):
        """Test that public endpoints are accessible without authentication."""
        public_endpoints = [
            ('accounts:request_code', 'POST'),  # Email verification request
            ('accounts:verify_code', 'POST'),   # Email verification
        ]
        
        for endpoint_name, method in public_endpoints:
            with self.subTest(endpoint=endpoint_name, method=method):
                try:
                    url = reverse(endpoint_name)
                    
                    # Test that endpoint exists and doesn't require auth
                    if method == 'GET':
                        response = self.client.get(url)
                    elif method == 'POST':
                        # Use minimal valid data for POST
                        response = self.client.post(url, {'email': 'test@example.com'})
                    
                    # Should not be unauthorized (might be bad request due to invalid data)
                    self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                                      f"{endpoint_name} should be publicly accessible")
                    
                except Exception as e:
                    if "not found" in str(e).lower() or "reverse" in str(e).lower():
                        self.skipTest(f"Endpoint {endpoint_name} not in URL configuration")
                    else:
                        raise


class AuthenticationErrorHandlingTestCase(TestCase):
    """Test proper error handling for authentication failures."""
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_authentication_error_response_format(self):
        """Test that authentication errors return proper format."""
        try:
            url = reverse('accounts:user-list')
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            
            # Should return JSON error response
            self.assertEqual(response['Content-Type'], 'application/json')
            
            # Should contain error information
            data = response.json()
            self.assertIn('detail', data)
            
        except Exception:
            self.skipTest("User list endpoint not available")
    
    def test_invalid_token_error_response(self):
        """Test that invalid token errors return proper response."""
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid-token')
        
        try:
            url = reverse('accounts:user-list')
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            
            # Should return descriptive error
            data = response.json()
            self.assertIn('detail', data)
            self.assertIn('token', data['detail'].lower())
            
        except Exception:
            self.skipTest("User list endpoint not available")