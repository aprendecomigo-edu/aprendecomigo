"""
Comprehensive Security Test Suite for Issue #46 Fixes

Tests all security vulnerabilities that were fixed:
1. Tutor detection vulnerability
2. Transaction rollback protection
3. Cache key security improvements  
4. Rate limiting verification
"""

import json
import time
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.core.cache import cache
from django.db import transaction
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole, TeacherProfile
from common.cache_utils import SecureCacheKeyGenerator
from finances.services.tutor_analytics_service import TutorAnalyticsService


class TutorDetectionSecurityTest(APITestCase):
    """Test the fix for tutor detection vulnerability."""
    
    def setUp(self):
        self.signup_url = reverse('accounts:user-signup')
        
    def test_explicit_tutor_type_creates_tutor(self):
        """Test that explicit tutor type creates tutor properly."""
        signup_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone_number': '+1234567890',
            'primary_contact': 'email',
            'user_type': 'tutor',  # Explicit tutor type
            'school': {
                'name': 'Regular School Name',  # No tutoring keywords
                'address': '123 Main St',
                'website': 'https://example.com'
            }
        }
        
        response = self.client.post(self.signup_url, signup_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created as tutor
        user = CustomUser.objects.get(email='john@example.com')
        
        # Check school owner membership
        owner_membership = SchoolMembership.objects.filter(
            user=user, 
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        ).first()
        self.assertIsNotNone(owner_membership)
        
        # Check teacher membership (should exist for tutors)
        teacher_membership = SchoolMembership.objects.filter(
            user=user, 
            role=SchoolRole.TEACHER,
            is_active=True
        ).first()
        self.assertIsNotNone(teacher_membership)
        
        # Check teacher profile was created
        teacher_profile = TeacherProfile.objects.filter(user=user).first()
        self.assertIsNotNone(teacher_profile)
        
    def test_explicit_school_type_creates_school_only(self):
        """Test that explicit school type creates school owner only."""
        signup_data = {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'phone_number': '+1234567891',
            'primary_contact': 'email',
            'user_type': 'school',  # Explicit school type
            'school': {
                'name': "Jane's Tutoring Practice",  # Contains tutoring keywords
                'address': '456 Oak Ave'
            }
        }
        
        response = self.client.post(self.signup_url, signup_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created as school owner only
        user = CustomUser.objects.get(email='jane@example.com')
        
        # Check school owner membership
        owner_membership = SchoolMembership.objects.filter(
            user=user, 
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        ).first()
        self.assertIsNotNone(owner_membership)
        
        # Check NO teacher membership (should not exist for schools)
        teacher_membership = SchoolMembership.objects.filter(
            user=user, 
            role=SchoolRole.TEACHER,
            is_active=True
        ).first()
        self.assertIsNone(teacher_membership)
        
        # Check NO teacher profile was created
        teacher_profile = TeacherProfile.objects.filter(user=user).first()
        self.assertIsNone(teacher_profile)
        
    def test_missing_user_type_field_returns_error(self):
        """Test that missing user_type field returns validation error."""
        signup_data = {
            'name': 'Bob Wilson',
            'email': 'bob@example.com',
            'phone_number': '+1234567892',
            'primary_contact': 'email',
            # Missing user_type field
            'school': {
                'name': 'Bob School',
                'address': '789 Pine St'
            }
        }
        
        response = self.client.post(self.signup_url, signup_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_type', response.data)
        
    def test_invalid_user_type_returns_error(self):
        """Test that invalid user_type value returns validation error."""
        signup_data = {
            'name': 'Alice Brown',
            'email': 'alice@example.com',
            'phone_number': '+1234567893',
            'primary_contact': 'email',
            'user_type': 'invalid_type',  # Invalid type
            'school': {
                'name': 'Alice School',
                'address': '101 Elm St'
            }
        }
        
        response = self.client.post(self.signup_url, signup_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_type', response.data)


class TransactionRollbackSecurityTest(TransactionTestCase):
    """Test transaction rollback protection."""
    
    def setUp(self):
        # Use TransactionTestCase for testing transaction rollback
        self.signup_url = reverse('accounts:user-signup')
        
    def test_email_failure_rolls_back_user_creation(self):
        """Test that email sending failure rolls back user and school creation."""
        signup_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone_number': '+1234567890',
            'primary_contact': 'email',
            'user_type': 'tutor',
            'school': {
                'name': 'Test School',
                'address': '123 Test St'
            }
        }
        
        # Mock email sending to fail
        with patch('accounts.views.send_email_verification_code') as mock_send_email:
            mock_send_email.side_effect = Exception("Email service unavailable")
            
            response = self.client.post(self.signup_url, signup_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('Failed to send verification code', response.data['error'])
            
            # Verify no user was created (rolled back)
            self.assertFalse(
                CustomUser.objects.filter(email='test@example.com').exists()
            )
            
            # Verify no school was created (rolled back)
            self.assertFalse(
                School.objects.filter(name='Test School').exists()
            )
            
    def test_database_error_rolls_back_creation(self):
        """Test that database errors during creation roll back properly."""
        signup_data = {
            'name': 'Test User 2',
            'email': 'test2@example.com',
            'phone_number': '+1234567891',
            'primary_contact': 'email',
            'user_type': 'school',
            'school': {
                'name': 'Test School 2',
                'address': '456 Test Ave'
            }
        }
        
        # Mock school creation to fail
        with patch('accounts.db_queries.School.objects.create') as mock_school_create:
            mock_school_create.side_effect = Exception("Database error")
            
            response = self.client.post(self.signup_url, signup_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verify no user was created (rolled back)
            self.assertFalse(
                CustomUser.objects.filter(email='test2@example.com').exists()
            )


class CacheKeySecurityTest(TestCase):
    """Test cache key security improvements."""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='teacher@example.com',
            name='Test Teacher',
            phone_number='+1234567890'
        )
        self.school = School.objects.create(
            name='Test School',
            contact_email='school@example.com'
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio='Test teacher'
        )
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
    def test_analytics_cache_key_is_secure(self):
        """Test that analytics cache keys are hash-based and secure."""
        # Generate cache key
        cache_key = SecureCacheKeyGenerator.generate_analytics_key(
            teacher_id=self.teacher_profile.id,
            school_id=self.school.id,
            time_range='30d',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )
        
        # Verify key format is secure (starts with secure_ and has hash)
        self.assertTrue(cache_key.startswith('secure_tutor_analytics_'))
        
        # Verify key doesn't contain obvious predictable patterns
        # (Note: Hash may coincidentally contain digits, but shouldn't be obviously structured)
        self.assertFalse(f"_{self.teacher_profile.id}_{self.school.id}_" in cache_key)
        self.assertFalse(f"teacher_{self.teacher_profile.id}" in cache_key)
        self.assertFalse(f"school_{self.school.id}" in cache_key)
        
        # Verify key is consistent for same inputs
        cache_key2 = SecureCacheKeyGenerator.generate_analytics_key(
            teacher_id=self.teacher_profile.id,
            school_id=self.school.id,
            time_range='30d',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )
        self.assertEqual(cache_key, cache_key2)
        
        # Verify key changes with different inputs
        cache_key3 = SecureCacheKeyGenerator.generate_analytics_key(
            teacher_id=self.teacher_profile.id,
            school_id=self.school.id,
            time_range='7d',  # Different time range
            start_date='2025-01-01',
            end_date='2025-01-31'
        )
        self.assertNotEqual(cache_key, cache_key3)
        
    def test_school_metrics_cache_key_is_secure(self):
        """Test that school metrics cache keys are hash-based and secure."""
        cache_key = SecureCacheKeyGenerator.generate_school_metrics_key(
            self.school.id
        )
        
        # Verify key format is secure
        self.assertTrue(cache_key.startswith('secure_school_metrics_'))
        
        # Verify key doesn't contain obvious predictable patterns
        self.assertFalse(f"school_{self.school.id}" in cache_key)
        self.assertFalse(f"metrics_{self.school.id}" in cache_key)
        
    def test_cache_poisoning_prevention(self):
        """Test that cache keys prevent poisoning attacks."""
        # Attempt to create predictable cache keys that might conflict
        malicious_teacher_id = 999999
        malicious_school_id = 999999
        
        # Generate keys with malicious IDs
        malicious_key = SecureCacheKeyGenerator.generate_analytics_key(
            teacher_id=malicious_teacher_id,
            school_id=malicious_school_id,
            time_range='30d',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )
        
        legitimate_key = SecureCacheKeyGenerator.generate_analytics_key(
            teacher_id=self.teacher_profile.id,
            school_id=self.school.id,
            time_range='30d',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )
        
        # Verify keys are different (preventing collision attacks)
        self.assertNotEqual(malicious_key, legitimate_key)
        
        # Set malicious data in cache
        cache.set(malicious_key, {'malicious': 'data'})
        
        # Verify legitimate key doesn't retrieve malicious data
        legitimate_data = cache.get(legitimate_key)
        self.assertIsNone(legitimate_data)  # Should be None, not malicious data


class RateLimitingSecurityTest(APITestCase):
    """Test that rate limiting is properly applied."""
    
    def setUp(self):
        self.signup_url = reverse('accounts:user-signup')
        cache.clear()  # Clear any existing rate limit cache
        
    def test_signup_rate_limiting_by_ip(self):
        """Test that signup endpoint has IP-based rate limiting."""
        signup_data = {
            'name': 'Rate Test User',
            'email': 'ratetest{}@example.com',  # Will be formatted per iteration
            'phone_number': '+123456789{}',      # Will be formatted per iteration
            'primary_contact': 'email',
            'user_type': 'tutor',
            'school': {
                'name': 'Rate Test School {}',   # Will be formatted per iteration
                'address': '123 Rate Test St'
            }
        }
        
        # IPSignupThrottle allows 3 requests per hour
        successful_requests = 0
        
        for i in range(5):  # Try 5 requests, expect only 3 to succeed
            data = signup_data.copy()
            data['email'] = signup_data['email'].format(i)
            data['phone_number'] = signup_data['phone_number'].format(i)
            data['school']['name'] = signup_data['school']['name'].format(i)
            
            with patch('accounts.views.send_email_verification_code'):
                response = self.client.post(self.signup_url, data, format='json')
                
                if response.status_code == status.HTTP_201_CREATED:
                    successful_requests += 1
                elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    # Rate limit hit
                    break
                    
        # Should hit rate limit before 5 requests
        self.assertLess(successful_requests, 5)
        self.assertGreaterEqual(successful_requests, 1)  # At least 1 should succeed
        
    def test_email_code_request_rate_limiting(self):
        """Test that email code requests have rate limiting."""
        url = reverse('accounts:request_code')
        data = {'email': 'test@example.com'}
        
        # EmailCodeRequestThrottle allows 5 requests per hour per email
        successful_requests = 0
        
        for i in range(7):  # Try 7 requests, expect only 5 to succeed
            response = self.client.post(url, data, format='json')
            
            if response.status_code == status.HTTP_200_OK:
                successful_requests += 1
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
                
        # Should hit rate limit before 7 requests
        self.assertLess(successful_requests, 7)
        self.assertGreaterEqual(successful_requests, 1)


class ComprehensiveSecurityTest(TestCase):
    """Integration tests for all security fixes together."""
    
    def setUp(self):
        cache.clear()
        
    def test_end_to_end_secure_tutor_signup_and_analytics(self):
        """Test complete secure flow from signup to analytics."""
        # 1. Secure tutor signup
        signup_data = {
            'name': 'Secure Tutor',
            'email': 'secure@example.com',
            'phone_number': '+1234567890',
            'primary_contact': 'email',
            'user_type': 'tutor',  # Explicit secure type
            'school': {
                'name': 'Secure Tutoring School',
                'address': '123 Secure St'
            }
        }
        
        signup_url = reverse('accounts:user-signup')
        
        with patch('accounts.views.send_email_verification_code'):
            response = self.client.post(signup_url, signup_data, format='json')
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 2. Verify secure entities created
        user = CustomUser.objects.get(email='secure@example.com')
        teacher_profile = TeacherProfile.objects.get(user=user)
        school = School.objects.get(name='Secure Tutoring School')
        
        # 3. Test secure analytics cache key generation
        with patch('finances.services.tutor_analytics_service.timezone') as mock_timezone:
            mock_timezone.now.return_value.date.return_value = '2025-01-31'
            
            # This should use secure cache keys internally
            analytics = TutorAnalyticsService.get_tutor_analytics(
                teacher=teacher_profile,
                school=school,
                time_range='30d'
            )
            
            # Verify analytics were generated (even if empty)
            self.assertIn('overview', analytics)
            self.assertIn('revenue', analytics)
            self.assertIn('sessions', analytics)
            self.assertIn('meta', analytics)
            
        # 4. Verify secure cache keys were used
        # Note: This is implicit since we updated the service to use SecureCacheKeyGenerator
        
    def test_transaction_rollback_with_rate_limiting(self):
        """Test that transaction rollback works correctly with rate limiting."""
        signup_data = {
            'name': 'Rollback Test',
            'email': 'rollback@example.com',
            'phone_number': '+1234567890',
            'primary_contact': 'email',
            'user_type': 'school',
            'school': {
                'name': 'Rollback Test School',
                'address': '123 Rollback St'
            }
        }
        
        signup_url = reverse('accounts:user-signup')
        
        # Mock email to fail after user creation starts
        with patch('accounts.views.send_email_verification_code') as mock_send:
            mock_send.side_effect = Exception("Email failed")
            
            response = self.client.post(signup_url, signup_data, format='json')
            
            # Should get error response
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verify rollback occurred
            self.assertFalse(
                CustomUser.objects.filter(email='rollback@example.com').exists()
            )
            self.assertFalse(
                School.objects.filter(name='Rollback Test School').exists()
            )
            
        # Test that rate limiting still works after rollback
        with patch('accounts.views.send_email_verification_code'):
            # This request should succeed (rate limit not affected by rollback)
            signup_data['email'] = 'rollback2@example.com'
            signup_data['school']['name'] = 'Rollback Test School 2'
            
            response = self.client.post(signup_url, signup_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)