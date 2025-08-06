"""
Security-focused tests for Teacher Profile Wizard implementation.
These tests ensure all critical security vulnerabilities are addressed.
"""

import json
import tempfile
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from knox.models import AuthToken
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import School, SchoolMembership, SchoolRole, TeacherProfile
from accounts.serializers import ProfileWizardDataSerializer

User = get_user_model()


class TeacherProfileWizardSecurityTestCase(TestCase):
    """Test security aspects of the Teacher Profile Wizard."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user and school
        self.user = User.objects.create_user(
            username="teacher@test.com",
            email="teacher@test.com",
            name="Test Teacher"
        )
        
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        # Create teacher profile and membership
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio="Initial bio",
            specialty="Mathematics",
            hourly_rate=Decimal('25.00')
        )
        
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Create authentication token
        self.token_instance, self.token = AuthToken.objects.create(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        
        self.save_progress_url = reverse('accounts:teacher-profile-wizard', kwargs={'action': 'save-progress'})
        self.validate_step_url = reverse('accounts:teacher-profile-wizard', kwargs={'action': 'validate-step'})

    def test_input_validation_prevents_malicious_data(self):
        """Test that input validation prevents malicious data injection."""
        malicious_payloads = [
            # XSS attempts
            {
                'profile_data': {
                    'first_name': '<script>alert("xss")</script>',
                    'last_name': 'Test',
                    'professional_bio': '<img src=x onerror=alert("xss")>',
                }
            },
            # SQL injection attempts
            {
                'profile_data': {
                    'first_name': "'; DROP TABLE users; --",
                    'last_name': "' OR '1'='1",
                }
            },
            # Oversized data
            {
                'profile_data': {
                    'first_name': 'A' * 1000,  # Too long
                    'professional_bio': 'A' * 10000,  # Too long
                }
            },
            # Invalid data types
            {
                'profile_data': {
                    'first_name': 123,
                    'years_experience': 'not_a_number',
                    'rate_structure': 'not_a_dict',
                }
            },
        ]
        
        for payload in malicious_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(self.save_progress_url, payload, format='json')
                # Should return validation error, not 500 or success
                self.assertIn(response.status_code, [400, 422])
                self.assertIn('error', response.data)

    def test_phone_number_validation(self):
        """Test phone number validation against malicious inputs."""
        invalid_phones = [
            '+' * 100,  # Too long
            '<script>alert("xss")</script>',
            '../../etc/passwd',
            'javascript:alert("xss")',
            "'; DROP TABLE users; --",
        ]
        
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                payload = {
                    'profile_data': {
                        'phone_number': phone,
                    }
                }
                response = self.client.post(self.save_progress_url, payload, format='json')
                self.assertIn(response.status_code, [400, 422])

    def test_bio_html_sanitization(self):
        """Test that HTML content in bio is properly sanitized."""
        malicious_bio = """
        <script>alert('xss')</script>
        <img src=x onerror=alert('xss')>
        <iframe src="javascript:alert('xss')"></iframe>
        <style>body{background:url('javascript:alert(1)')}</style>
        <p onclick="alert('xss')">Click me</p>
        """
        
        payload = {
            'profile_data': {
                'professional_bio': malicious_bio,
            }
        }
        
        response = self.client.post(self.save_progress_url, payload, format='json')
        
        # Check that bio was sanitized (should not contain script tags)
        self.teacher_profile.refresh_from_db()
        sanitized_bio = self.teacher_profile.bio
        
        self.assertNotIn('<script>', sanitized_bio)
        self.assertNotIn('onerror=', sanitized_bio)
        self.assertNotIn('<iframe>', sanitized_bio)
        self.assertNotIn('javascript:', sanitized_bio)

    @override_settings(
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': (
                'knox.auth.TokenAuthentication',
                'rest_framework_simplejwt.authentication.JWTAuthentication',
            ),
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.IsAuthenticated',
            ],
            'DEFAULT_THROTTLE_CLASSES': [
                'accounts.throttles.ProfileWizardThrottle',
            ],
            'DEFAULT_THROTTLE_RATES': {
                'profile_wizard': '10/min',
            },
        }
    )
    def test_rate_limiting_protection(self):
        """Test that rate limiting prevents abuse."""
        payload = {
            'profile_data': {
                'first_name': 'Test',
                'last_name': 'User',
            }
        }
        
        # Make multiple rapid requests
        responses = []
        for i in range(20):  # More than the expected rate limit
            response = self.client.post(self.save_progress_url, payload, format='json')
            responses.append(response)
        
        # At least some requests should be rate limited
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        self.assertGreater(rate_limited_count, 0, "Rate limiting should kick in after multiple requests")

    def test_file_upload_security(self):
        """Test that file uploads are properly validated and secured."""
        # Test with various malicious file types
        malicious_files = [
            # Executable disguised as image
            ('malware.exe', b'MZ\x90\x00', 'image/jpeg'),
            # PHP script
            ('script.php', b'<?php system($_GET["cmd"]); ?>', 'image/png'),
            # SVG with JavaScript
            ('malicious.svg', b'<svg><script>alert("xss")</script></svg>', 'image/svg+xml'),
            # Oversized file
            ('huge.jpg', b'A' * (10 * 1024 * 1024), 'image/jpeg'),  # 10MB
        ]
        
        for filename, content, content_type in malicious_files:
            with self.subTest(filename=filename):
                uploaded_file = SimpleUploadedFile(filename, content, content_type=content_type)
                
                payload = {
                    'profile_photo': uploaded_file,
                }
                
                # Assuming there's a profile photo upload endpoint
                upload_url = reverse('accounts:teacher-profile-wizard', kwargs={'action': 'upload-photo'})
                response = self.client.post(upload_url, payload, format='multipart')
                
                # Should reject malicious files
                self.assertIn(response.status_code, [400, 422, 413])

    def test_valid_image_upload_accepted(self):
        """Test that valid images are accepted."""
        # Create a valid test image
        image = Image.new('RGB', (100, 100), color='red')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            'profile.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )
        
        payload = {
            'profile_photo': uploaded_file,
        }
        
        upload_url = reverse('accounts:teacher-profile-wizard', kwargs={'action': 'upload-photo'})
        response = self.client.post(upload_url, payload, format='multipart')
        
        # Should accept valid image
        self.assertEqual(response.status_code, 200)


class TeacherProfileWizardTransactionTestCase(TransactionTestCase):
    """Test transaction management in Teacher Profile Wizard."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username="teacher@test.com",
            email="teacher@test.com",
            name="Test Teacher"
        )
        
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio="Initial bio",
            specialty="Mathematics"
        )
        
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        self.token_instance, self.token = AuthToken.objects.create(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        
        self.save_progress_url = reverse('accounts:teacher-profile-wizard', kwargs={'action': 'save-progress'})

    def test_transaction_rollback_on_error(self):
        """Test that database changes are rolled back when an error occurs."""
        original_bio = self.teacher_profile.bio
        original_name = self.user.name
        
        # Mock an error during profile save
        with patch.object(TeacherProfile, 'update_completion_score', side_effect=Exception("Database error")):
            payload = {
                'profile_data': {
                    'first_name': 'NewFirst',
                    'last_name': 'NewLast',
                    'professional_bio': 'New bio content',
                }
            }
            
            response = self.client.post(self.save_progress_url, payload, format='json')
            self.assertEqual(response.status_code, 500)
            
            # Check that no changes were persisted
            self.user.refresh_from_db()
            self.teacher_profile.refresh_from_db()
            
            self.assertEqual(self.teacher_profile.bio, original_bio)
            self.assertEqual(self.user.name, original_name)

    def test_atomic_updates_success(self):
        """Test that all updates happen atomically on success."""
        payload = {
            'profile_data': {
                'first_name': 'NewFirst',
                'last_name': 'NewLast',
                'professional_bio': 'New bio content',
                'phone_number': '+1234567890',
            }
        }
        
        response = self.client.post(self.save_progress_url, payload, format='json')
        self.assertEqual(response.status_code, 200)
        
        # Check that all changes were persisted
        self.user.refresh_from_db()
        self.teacher_profile.refresh_from_db()
        
        self.assertEqual(self.user.name, 'NewFirst NewLast')
        self.assertEqual(self.teacher_profile.bio, 'New bio content')
        self.assertEqual(self.teacher_profile.phone_number, '+1234567890')


class ProfileWizardDataSerializerTestCase(TestCase):
    """Test the ProfileWizardDataSerializer for comprehensive validation."""

    def test_valid_data_serialization(self):
        """Test that valid data passes serialization."""
        valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '+1234567890',
            'professional_bio': 'I am a mathematics teacher with 5 years of experience.',
            'years_experience': 5,
            'rate_structure': {
                'individual_rate': 25.00,
                'group_rate': 15.00,
            }
        }
        
        serializer = ProfileWizardDataSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), f"Errors: {serializer.errors}")

    def test_invalid_data_rejection(self):
        """Test that invalid data is properly rejected."""
        invalid_data_sets = [
            # Missing required fields
            {
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
            },
            # Invalid email
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'invalid-email',
            },
            # Negative experience
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'years_experience': -1,
            },
            # Too long bio
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'professional_bio': 'A' * 3000,  # Too long
            },
        ]
        
        for invalid_data in invalid_data_sets:
            with self.subTest(data=invalid_data):
                serializer = ProfileWizardDataSerializer(data=invalid_data)
                self.assertFalse(serializer.is_valid())

    def test_html_sanitization_in_bio(self):
        """Test that HTML in bio is properly sanitized."""
        data_with_html = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'professional_bio': '<script>alert("xss")</script><p>Safe content</p>',
        }
        
        serializer = ProfileWizardDataSerializer(data=data_with_html)
        self.assertTrue(serializer.is_valid())
        
        # Check that dangerous HTML is removed but safe HTML is preserved
        sanitized_bio = serializer.validated_data['professional_bio']
        self.assertNotIn('<script>', sanitized_bio)
        self.assertIn('<p>Safe content</p>', sanitized_bio)

    def test_phone_number_validation(self):
        """Test phone number validation."""
        valid_phones = ['+1234567890', '123-456-7890', '(123) 456-7890']
        invalid_phones = ['abc', '123', '+' * 100, '<script>']
        
        for phone in valid_phones:
            with self.subTest(phone=phone):
                data = {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john.doe@example.com',
                    'phone_number': phone,
                }
                serializer = ProfileWizardDataSerializer(data=data)
                self.assertTrue(serializer.is_valid(), f"Valid phone {phone} should pass")
        
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                data = {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john.doe@example.com',
                    'phone_number': phone,
                }
                serializer = ProfileWizardDataSerializer(data=data)
                self.assertFalse(serializer.is_valid(), f"Invalid phone {phone} should fail")


class SecurityLoggingTestCase(TestCase):
    """Test security event logging."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username="teacher@test.com",
            email="teacher@test.com",
            name="Test Teacher"
        )
        
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio="Initial bio",
            specialty="Mathematics"
        )
        
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        self.token_instance, self.token = AuthToken.objects.create(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        
        self.save_progress_url = reverse('accounts:teacher-profile-wizard', kwargs={'action': 'save-progress'})

    @patch('accounts.views.logger')
    def test_security_events_logged(self, mock_logger):
        """Test that security events are properly logged."""
        # Test malicious input logging
        malicious_payload = {
            'profile_data': {
                'first_name': '<script>alert("xss")</script>',
                'professional_bio': '<img src=x onerror=alert("xss")>',
            }
        }
        
        response = self.client.post(self.save_progress_url, malicious_payload, format='json')
        
        # Check that security event was logged
        self.assertTrue(mock_logger.warning.called or mock_logger.error.called)
        
        # Verify log message contains security-relevant information
        log_calls = mock_logger.warning.call_args_list + mock_logger.error.call_args_list
        security_logged = any('security' in str(call).lower() or 'malicious' in str(call).lower() 
                            for call in log_calls)
        self.assertTrue(security_logged, "Security event should be logged")

    @override_settings(
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': (
                'knox.auth.TokenAuthentication',
                'rest_framework_simplejwt.authentication.JWTAuthentication',
            ),
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.IsAuthenticated',
            ],
            'DEFAULT_THROTTLE_CLASSES': [
                'accounts.throttles.ProfileWizardThrottle',
            ],
            'DEFAULT_THROTTLE_RATES': {
                'profile_wizard': '10/min',
            },
        }
    )
    @patch('accounts.views.logger')
    def test_rate_limit_events_logged(self, mock_logger):
        """Test that rate limiting events are logged."""
        payload = {
            'profile_data': {
                'first_name': 'Test',
                'last_name': 'User',
            }
        }
        
        # Make multiple requests to trigger rate limiting
        for i in range(15):
            self.client.post(self.save_progress_url, payload, format='json')
        
        # Check that rate limiting was logged
        log_calls = mock_logger.warning.call_args_list + mock_logger.info.call_args_list
        rate_limit_logged = any('rate' in str(call).lower() or 'throttle' in str(call).lower() 
                              for call in log_calls)
        self.assertTrue(rate_limit_logged, "Rate limiting should be logged")