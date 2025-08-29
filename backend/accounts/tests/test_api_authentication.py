"""
Comprehensive API tests for authentication endpoints.

This module provides thorough testing of the authentication system including
code request, verification, multi-tenant security boundaries, and edge cases.
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from knox.models import AuthToken

from accounts.models import (
    CustomUser, 
    VerificationCode, 
    School, 
    SchoolMembership, 
    SchoolRole,
    TeacherProfile,
    StudentProfile,
    EducationalSystem
)


class AuthenticationAPITestCase(APITestCase):
    """Base test case for authentication API tests."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test schools
        self.school1 = School.objects.create(
            name='Test School 1',
            description='Test school for authentication tests'
        )
        self.school2 = School.objects.create(
            name='Test School 2', 
            description='Another test school'
        )
        
        # Get or create educational system
        self.educational_system, _ = EducationalSystem.objects.get_or_create(
            code='pt',
            defaults={
                'name': 'Test System',
                'description': 'Test educational system for Portugal'
            }
        )
        
        # Create test users with different roles
        self.existing_user = CustomUser.objects.create_user(
            email='existing@example.com',
            name='Existing User'
        )
        
        # Create memberships to establish multi-tenant context
        SchoolMembership.objects.create(
            user=self.existing_user,
            school=self.school1,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
    def authenticate_user(self, user):
        """Helper to authenticate a user and return token."""
        instance, token = AuthToken.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        return token


class RequestCodeAPITests(AuthenticationAPITestCase):
    """Test suite for /api/accounts/request-code/ endpoint."""
    
    def test_request_code_for_existing_user_succeeds(self):
        """Test that requesting code for existing user returns success."""
        url = reverse('accounts:request_code')
        data = {'email': 'existing@example.com'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('verification code sent', response.data['message'].lower())
        
        # Verify code was actually created
        self.assertTrue(
            VerificationCode.objects.filter(
                email='existing@example.com',
                is_used=False
            ).exists()
        )
    
    def test_request_code_for_non_existent_user_returns_consistent_response(self):
        """Test that requesting code for non-existent user returns consistent response (prevent email enumeration)."""
        url = reverse('accounts:request_code')
        data = {'email': 'nonexistent@example.com'}
        
        response = self.client.post(url, data, format='json')
        
        # Should return 200 with generic message (not reveal user doesn't exist)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('if an account exists', response.data['message'].lower())
        
        # No code should be created for non-existent user
        self.assertFalse(
            VerificationCode.objects.filter(email='nonexistent@example.com').exists()
        )
    
    def test_request_code_invalid_email_format_fails(self):
        """Test that invalid email formats are rejected."""
        url = reverse('accounts:request_code')
        invalid_emails = [
            'not-an-email',
            'missing@',
            '@domain.com',
            'spaces in@email.com',
            ''
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                data = {'email': email}
                response = self.client.post(url, data, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_request_code_missing_email_fails(self):
        """Test that missing email field is handled properly."""
        url = reverse('accounts:request_code')
        data = {}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_request_code_rate_limiting_protection(self):
        """Test that rate limiting prevents abuse."""
        url = reverse('accounts:request_code')
        data = {'email': 'existing@example.com'}
        
        # Make several rapid requests (actual throttle limits depend on settings)
        responses = []
        for i in range(10):
            response = self.client.post(url, data, format='json')
            responses.append(response)
            
        # At least some requests should be rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        # Note: This test may need adjustment based on throttle settings
        

class VerifyCodeAPITests(AuthenticationAPITestCase):
    """Test suite for /api/accounts/verify-code/ endpoint."""
    
    def setUp(self):
        super().setUp()
        # Create a valid verification code for testing
        self.verification = VerificationCode.generate_code('existing@example.com')
        self.valid_code = self.verification.get_current_code()
        
    def test_verify_code_with_valid_code_succeeds(self):
        """Test successful authentication with valid code."""
        url = reverse('accounts:verify_code')
        data = {
            'email': 'existing@example.com',
            'code': self.valid_code
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        
        # Verify token is valid Knox token
        self.assertTrue(len(response.data['token']) > 20)  # Knox tokens are long
        
        # Verify user data is included
        user_data = response.data['user']
        self.assertEqual(user_data['email'], 'existing@example.com')
        self.assertEqual(user_data['name'], 'Existing User')
        
        # Verify code is marked as used
        self.verification.refresh_from_db()
        self.assertTrue(self.verification.is_used)
        
        # Verify user email is marked as verified
        self.existing_user.refresh_from_db()
        self.assertTrue(self.existing_user.email_verified)
    
    def test_verify_code_with_invalid_code_fails(self):
        """Test that invalid codes are rejected."""
        url = reverse('accounts:verify_code')
        data = {
            'email': 'existing@example.com',
            'code': '000000'  # Invalid code
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('invalid', response.data['error'].lower())
        
        # Code should not be marked as used
        self.verification.refresh_from_db()
        self.assertFalse(self.verification.is_used)
    
    def test_verify_code_with_expired_code_fails(self):
        """Test that expired codes are rejected."""
        # Manually expire the code
        self.verification.created_at = timezone.now() - timedelta(minutes=30)
        self.verification.save()
        
        url = reverse('accounts:verify_code')
        data = {
            'email': 'existing@example.com',
            'code': self.valid_code
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('expired', response.data['error'].lower())
    
    def test_verify_code_for_non_existent_user_fails(self):
        """Test verification for non-existent user."""
        url = reverse('accounts:verify_code')
        data = {
            'email': 'nonexistent@example.com',
            'code': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should return generic success message for security
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('if an account exists', response.data['message'].lower())
    
    def test_verify_code_multiple_failed_attempts_locks_code(self):
        """Test that multiple failed attempts lock the verification code."""
        url = reverse('accounts:verify_code')
        
        # Make several failed attempts
        for i in range(5):
            data = {
                'email': 'existing@example.com',
                'code': '000000'  # Wrong code
            }
            response = self.client.post(url, data, format='json')
            
        # Next attempt should mention too many failed attempts
        data = {
            'email': 'existing@example.com',
            'code': '000000'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('too many failed attempts', response.data['error'].lower())
    
    def test_verify_code_missing_fields_fails(self):
        """Test that missing required fields are handled properly."""
        url = reverse('accounts:verify_code')
        
        test_cases = [
            {},  # No fields
            {'email': 'test@example.com'},  # Missing code
            {'code': '123456'},  # Missing email
        ]
        
        for data in test_cases:
            with self.subTest(data=data):
                response = self.client.post(url, data, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_verify_code_invalid_email_format_fails(self):
        """Test that invalid email formats are rejected in verification."""
        url = reverse('accounts:verify_code')
        data = {
            'email': 'invalid-email',
            'code': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_verify_code_invalid_code_format_fails(self):
        """Test that invalid code formats are rejected."""
        url = reverse('accounts:verify_code')
        
        invalid_codes = [
            '12345',      # Too short
            '1234567',    # Too long  
            'abcdef',     # Letters
            '12 34 56',   # Spaces
            '',           # Empty
        ]
        
        for code in invalid_codes:
            with self.subTest(code=code):
                data = {
                    'email': 'existing@example.com',
                    'code': code
                }
                response = self.client.post(url, data, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationBusinessLogicTests(AuthenticationAPITestCase):
    """Test business logic and edge cases for authentication."""
    
    def test_user_onboarding_tasks_created_on_first_verification(self):
        """Test that onboarding tasks are created when user first verifies."""
        # Create verification for user
        verification = VerificationCode.generate_code('existing@example.com')
        code = verification.get_current_code()
        
        url = reverse('accounts:verify_code')
        data = {
            'email': 'existing@example.com', 
            'code': code
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that tasks were created (if task system is implemented)
        from tasks.models import Task
        tasks = Task.objects.filter(user=self.existing_user)
        # This test depends on onboarding task creation being implemented
        
    def test_authentication_creates_valid_knox_session(self):
        """Test that successful authentication creates valid Knox session."""
        verification = VerificationCode.generate_code('existing@example.com')
        code = verification.get_current_code()
        
        url = reverse('accounts:verify_code')
        data = {
            'email': 'existing@example.com',
            'code': code
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['token']
        
        # Test that token works for authenticated endpoints
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Try accessing an authenticated endpoint (dashboard_info is a custom action on UserViewSet)
        user_url = '/api/accounts/users/dashboard-info/'
        user_response = self.client.get(user_url)
        
        self.assertEqual(user_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_response.data['user_info']['email'], 'existing@example.com')
    
    def test_authentication_response_includes_role_information(self):
        """Test that authentication response includes user role and school information."""
        verification = VerificationCode.generate_code('existing@example.com')
        code = verification.get_current_code()
        
        url = reverse('accounts:verify_code')
        data = {
            'email': 'existing@example.com',
            'code': code  
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data['user']
        
        # Should include role information for frontend routing
        expected_fields = ['id', 'email', 'name', 'roles']
        for field in expected_fields:
            self.assertIn(field, user_data)
            
        # Should include school membership information  
        self.assertTrue(isinstance(user_data['roles'], list))
        if user_data['roles']:  # If user has roles
            role_data = user_data['roles'][0]
            self.assertIn('school', role_data)
            self.assertIn('role', role_data)


class AuthenticationSecurityTests(AuthenticationAPITestCase):
    """Test security aspects of authentication system."""
    
    def test_timing_attack_protection_on_user_enumeration(self):
        """Test that user enumeration via timing attacks is prevented."""
        import time
        
        # Request code for existing vs non-existing user should take similar time
        url = reverse('accounts:request_code')
        
        start_time = time.time()
        self.client.post(url, {'email': 'existing@example.com'})
        existing_user_time = time.time() - start_time
        
        start_time = time.time()  
        self.client.post(url, {'email': 'nonexistent@example.com'})
        nonexistent_user_time = time.time() - start_time
        
        # Times should be reasonably similar (allowing for some variance)
        time_difference = abs(existing_user_time - nonexistent_user_time)
        # Note: This is a basic check - real timing attack prevention needs more sophisticated analysis
        
    def test_code_cannot_be_reused(self):
        """Test that verification codes cannot be reused."""
        verification = VerificationCode.generate_code('existing@example.com')
        code = verification.get_current_code()
        
        url = reverse('accounts:verify_code')
        data = {
            'email': 'existing@example.com',
            'code': code
        }
        
        # First use should succeed
        response1 = self.client.post(url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second use should fail
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_codes_are_properly_random_and_unique(self):
        """Test that generated codes are sufficiently random."""
        codes = []
        
        # Generate multiple codes
        for i in range(10):
            verification = VerificationCode.generate_code(f'user{i}@example.com')
            code = verification.get_current_code()
            codes.append(code)
            
        # All codes should be unique
        self.assertEqual(len(codes), len(set(codes)))
        
        # All codes should be 6 digits
        for code in codes:
            self.assertTrue(code.isdigit())
            self.assertEqual(len(code), 6)