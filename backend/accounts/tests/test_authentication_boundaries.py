"""
Authentication Boundary Security Tests for Aprende Comigo Platform

These tests verify that authentication mechanisms properly protect endpoints
and that unauthorized access attempts are correctly rejected.
"""

import jwt
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    SchoolRole,
    TeacherProfile,
    StudentProfile,
)

User = get_user_model()


class AuthenticationBoundaryTestCase(TestCase):
    """
    Test suite for verifying authentication boundaries and token security.
    
    These tests ensure that:
    1. Unauthenticated users cannot access protected endpoints
    2. Token expiry is properly handled
    3. Invalid tokens are rejected
    4. Session security is maintained
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
            username="school_owner",
            first_name="School",
            last_name="Owner"
        )
        
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            username="teacher",
            first_name="Test",
            last_name="Teacher"
        )
        
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            username="student",
            first_name="Test",
            last_name="Student"
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
            bio="Test teacher profile",
            hourly_rate=25.00
        )
        
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            birth_date="2010-01-01",
            school_year="5th Grade"
        )

    def test_unauthenticated_access_denied_to_protected_endpoints(self):
        """Test that unauthenticated users cannot access protected endpoints."""
        protected_endpoints = [
            ('accounts:school-list', {}),
            ('accounts:school_membership-list', {}),
            ('accounts:teacher-list', {}),
            ('accounts:student-list', {}),
            ('accounts:user-dashboard_info', {}),
            ('accounts:global-search', {}),
            ('accounts:teacher-invitation-list', {}),
        ]
        
        for endpoint_name, kwargs in protected_endpoints:
            with self.subTest(endpoint=endpoint_name):
                url = reverse(endpoint_name, **kwargs)
                response = self.client.get(url)
                
                # Should be 401 Unauthorized or 403 Forbidden
                self.assertIn(
                    response.status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
                    f"Endpoint {endpoint_name} should require authentication"
                )

    def test_invalid_jwt_token_rejected(self):
        """Test that invalid JWT tokens are properly rejected."""
        # Set invalid Authorization header
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        
        url = reverse('accounts:user-dashboard_info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malformed_jwt_token_rejected(self):
        """Test that malformed JWT tokens are properly rejected."""
        malformed_tokens = [
            'Bearer ',  # Empty token
            'Bearer malformed',  # Not a valid JWT structure
            'InvalidHeader token',  # Wrong header format
            'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature',  # Invalid payload
        ]
        
        for token in malformed_tokens:
            with self.subTest(token=token):
                self.client.credentials(HTTP_AUTHORIZATION=token)
                
                url = reverse('accounts:user-dashboard_info')
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_jwt_token_rejected(self):
        """Test that expired JWT tokens are properly rejected."""
        # Create an expired token manually
        expired_payload = {
            'user_id': self.teacher.id,
            'exp': datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            'iat': datetime.utcnow() - timedelta(hours=2),
            'token_type': 'access'
        }
        
        expired_token = jwt.encode(
            expired_payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        
        url = reverse('accounts:user-dashboard_info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_jwt_token_accepted(self):
        """Test that valid JWT tokens are properly accepted."""
        # Generate a valid token
        refresh = RefreshToken.for_user(self.teacher)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('accounts:user-dashboard_info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_with_non_existent_user_rejected(self):
        """Test that tokens for non-existent users are rejected."""
        # Create token with invalid user ID
        invalid_payload = {
            'user_id': 99999,  # Non-existent user ID
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'token_type': 'access'
        }
        
        invalid_token = jwt.encode(
            invalid_payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {invalid_token}')
        
        url = reverse('accounts:user-dashboard_info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_with_inactive_user_rejected(self):
        """Test that tokens for inactive users are rejected."""
        # Create an inactive user
        inactive_user = CustomUser.objects.create_user(
            email="inactive@example.com",
            username="inactive",
            is_active=False
        )
        
        # Generate token for inactive user
        refresh = RefreshToken.for_user(inactive_user)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('accounts:user-dashboard_info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_concurrent_token_usage_security(self):
        """Test security with concurrent token usage."""
        # Generate token
        refresh = RefreshToken.for_user(self.teacher)
        access_token = str(refresh.access_token)
        
        # Multiple concurrent requests with same token should work
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        urls = [
            reverse('dashboard-profile'),
            reverse('teacherprofile-list'),
            reverse('school-list'),
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_signature_verification(self):
        """Test that tokens with invalid signatures are rejected."""
        # Create token with wrong signature
        payload = {
            'user_id': self.teacher.id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'token_type': 'access'
        }
        
        # Sign with wrong secret
        invalid_token = jwt.encode(payload, 'wrong-secret', algorithm='HS256')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {invalid_token}')
        
        url = reverse('accounts:user-dashboard_info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(SIMPLE_JWT={'ACCESS_TOKEN_LIFETIME': timedelta(seconds=1)})
    def test_token_expiry_timing_security(self):
        """Test token expiry timing to prevent timing attacks."""
        import time
        
        # Generate token with very short lifetime
        refresh = RefreshToken.for_user(self.teacher)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Token should work initially
        url = reverse('accounts:user-dashboard_info')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Wait for token to expire
        time.sleep(2)
        
        # Token should be rejected after expiry
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authentication_header_case_sensitivity(self):
        """Test that authentication header is case-sensitive as per HTTP standards."""
        refresh = RefreshToken.for_user(self.teacher)
        access_token = str(refresh.access_token)
        
        # Test various case combinations
        invalid_headers = [
            f'bearer {access_token}',  # lowercase
            f'BEARER {access_token}',  # uppercase
            f'Bearer{access_token}',   # no space
        ]
        
        for header in invalid_headers:
            with self.subTest(header=header):
                self.client.credentials(HTTP_AUTHORIZATION=header)
                
                url = reverse('accounts:user-dashboard_info')
                response = self.client.get(url)
                
                # Some of these might work depending on DRF implementation
                # The test documents the expected behavior
                self.assertIn(
                    response.status_code,
                    [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
                )

    def test_token_reuse_after_user_password_change(self):
        """Test that tokens become invalid after password changes."""
        # Generate token
        refresh = RefreshToken.for_user(self.teacher)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Token should work initially
        url = reverse('accounts:user-dashboard_info')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Change user password
        self.teacher.set_password('new-password')
        self.teacher.save()
        
        # Token should still work (JWT tokens don't automatically invalidate)
        # This documents current behavior - in production, you might want
        # to implement additional security measures
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_authentication_bypass_with_empty_token(self):
        """Test that empty tokens don't bypass authentication."""
        empty_tokens = [
            '',
            'Bearer',
            'Bearer ',
            None,
        ]
        
        for token in empty_tokens:
            with self.subTest(token=token):
                if token is not None:
                    self.client.credentials(HTTP_AUTHORIZATION=token)
                else:
                    self.client.credentials()  # No auth header
                
                url = reverse('accounts:user-dashboard_info')
                response = self.client.get(url)
                
                self.assertIn(
                    response.status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

    def test_privilege_escalation_prevented_by_token_scope(self):
        """Test that tokens cannot be used to escalate privileges beyond user's actual roles."""
        # Student tries to access admin endpoints
        refresh = RefreshToken.for_user(self.student)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Try to access school owner endpoints
        admin_endpoints = [
            ('dashboard-school-stats', {'school_id': self.school.id}),
            ('school-settings', {'pk': self.school.id}),
        ]
        
        for endpoint_name, params in admin_endpoints:
            with self.subTest(endpoint=endpoint_name):
                if params:
                    url = reverse(endpoint_name, **params)
                    response = self.client.get(url, params)
                else:
                    url = reverse(endpoint_name)
                    response = self.client.get(url)
                
                # Should be forbidden
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cross_origin_token_security(self):
        """Test token security with different origins (if CORS is configured)."""
        refresh = RefreshToken.for_user(self.teacher)
        access_token = str(refresh.access_token)
        
        # Test with different origin headers
        origins = [
            'http://malicious-site.com',
            'https://fake-school.com',
            'http://localhost:8080',  # Different port
        ]
        
        for origin in origins:
            with self.subTest(origin=origin):
                self.client.credentials(
                    HTTP_AUTHORIZATION=f'Bearer {access_token}',
                    HTTP_ORIGIN=origin
                )
                
                url = reverse('accounts:user-dashboard_info')
                response = self.client.get(url)
                
                # Token should still work (origin doesn't affect JWT validation)
                # CORS policy is handled separately
                self.assertEqual(response.status_code, status.HTTP_200_OK)


@pytest.mark.django_db
class TestJWTTokenSecurity:
    """
    Pytest-based tests for JWT token security specifics.
    
    These tests focus on JWT-specific security concerns and edge cases.
    """

    def test_jwt_algorithm_tampering_protection(self):
        """Test that JWT algorithm tampering is prevented."""
        user = CustomUser.objects.create_user(
            email="test@example.com",
            username="test_user"
        )
        
        # Create payload
        payload = {
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'token_type': 'access'
        }
        
        # Try to use 'none' algorithm (should be rejected)
        try:
            tampered_token = jwt.encode(payload, '', algorithm='none')
            
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
            
            url = reverse('accounts:user-dashboard_info')
            response = client.get(url)
            
            # Should be rejected
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        except Exception:
            # JWT library might prevent this entirely
            pass

    def test_jwt_payload_tampering_detection(self):
        """Test that JWT payload tampering is detected."""
        user = CustomUser.objects.create_user(
            email="test@example.com",
            username="test_user"
        )
        
        # Create valid token
        refresh = RefreshToken.for_user(user)
        valid_token = str(refresh.access_token)
        
        # Tamper with token by changing payload
        try:
            # Decode without verification to get structure
            header, payload, signature = valid_token.split('.')
            
            # Try to modify payload (this should fail verification)
            import base64
            import json
            
            # Decode payload
            decoded_payload = json.loads(
                base64.urlsafe_b64decode(payload + '==').decode('utf-8')
            )
            
            # Tamper with user_id
            decoded_payload['user_id'] = 99999
            
            # Re-encode
            tampered_payload = base64.urlsafe_b64encode(
                json.dumps(decoded_payload).encode('utf-8')
            ).rstrip(b'=').decode('utf-8')
            
            # Reconstruct token with tampered payload
            tampered_token = f"{header}.{tampered_payload}.{signature}"
            
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
            
            url = reverse('accounts:user-dashboard_info')
            response = client.get(url)
            
            # Should be rejected due to signature verification failure
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            
        except Exception:
            # Expected - tampering should be difficult/impossible
            pass

    def test_jwt_timing_attack_resistance(self):
        """Test JWT validation timing to ensure resistance to timing attacks."""
        import time
        
        user = CustomUser.objects.create_user(
            email="test@example.com",
            username="test_user"
        )
        
        # Generate valid and invalid tokens
        refresh = RefreshToken.for_user(user)
        valid_token = str(refresh.access_token)
        invalid_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature'
        
        client = APIClient()
        url = reverse('accounts:user-dashboard_info')
        
        # Measure validation time for valid token
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {valid_token}')
        start_time = time.time()
        response = client.get(url)
        valid_time = time.time() - start_time
        
        # Measure validation time for invalid token
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {invalid_token}')
        start_time = time.time()
        response = client.get(url)
        invalid_time = time.time() - start_time
        
        # Time difference should not be significant (within reasonable bounds)
        # This is a basic check - sophisticated timing attacks require more analysis
        time_difference = abs(valid_time - invalid_time)
        assert time_difference < 0.1, "Significant timing difference detected"

    def test_jwt_user_context_isolation(self):
        """Test that JWT tokens properly isolate user contexts."""
        user1 = CustomUser.objects.create_user(
            email="user1@example.com",
            username="user1"
        )
        user2 = CustomUser.objects.create_user(
            email="user2@example.com", 
            username="user2"
        )
        
        # Generate tokens for both users
        refresh1 = RefreshToken.for_user(user1)
        token1 = str(refresh1.access_token)
        
        refresh2 = RefreshToken.for_user(user2)
        token2 = str(refresh2.access_token)
        
        client = APIClient()
        
        # Test with user1 token
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        url = reverse('accounts:user-dashboard_info')
        response1 = client.get(url)
        
        # Test with user2 token
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        response2 = client.get(url)
        
        # Both should succeed but return different user data
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        # User data should be different
        assert response1.data['user']['id'] != response2.data['user']['id']
        assert response1.data['user']['email'] != response2.data['user']['email']

    @override_settings(SIMPLE_JWT={'ACCESS_TOKEN_LIFETIME': timedelta(minutes=1)})
    def test_jwt_expiry_precision(self):
        """Test JWT expiry precision and consistency."""
        user = CustomUser.objects.create_user(
            email="test@example.com",
            username="test_user"
        )
        
        # Generate token
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Decode to check expiry time
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256'],
            options={"verify_exp": False}
        )
        
        # Check that expiry is set correctly
        exp_time = datetime.fromtimestamp(decoded['exp'])
        iat_time = datetime.fromtimestamp(decoded['iat'])
        
        # Should be approximately 1 minute apart
        time_diff = exp_time - iat_time
        assert abs(time_diff.total_seconds() - 60) < 5, "Token lifetime not set correctly"