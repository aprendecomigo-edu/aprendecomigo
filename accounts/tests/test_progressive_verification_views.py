"""
Tests for Progressive Verification System Views

These tests validate the progressive verification system where users get
24 hours of immediate access after signup before being required to verify.
Tests cover signup flow, verification endpoints, and edge cases.
"""

import re
import secrets
from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import School, SchoolMembership, SchoolRole
from accounts.tests.test_base import BaseTestCase
from accounts.views import SignUpView, send_verification_email, send_verification_sms
from tasks.models import Task

User = get_user_model()


class SignUpViewTestCase(BaseTestCase):
    """Test the SignUpView with progressive verification functionality."""

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('accounts:signup')
        self.factory = RequestFactory()
        
        self.valid_signup_data = {
            'email': 'test@example.com',
            'full_name': 'John Doe',
            'phone_number': '+351987654321',
            'organization_name': 'Test School'
        }

    def test_signup_get_redirects_authenticated_users(self):
        """Test that authenticated users are redirected to dashboard."""
        # Create user with school and membership (required for dashboard access)
        user = User.objects.create_user(email='existing@example.com', name='Existing User')
        school = School.objects.create(name='Test School')
        SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.SCHOOL_OWNER)
        
        self.client.force_login(user)
        
        response = self.client.get(self.signup_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard:dashboard'))

    def test_signup_get_shows_form_for_anonymous_users(self):
        """Test that anonymous users see the signup form."""
        response = self.client.get(self.signup_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')

    def test_signup_post_missing_email_returns_error(self):
        """Test signup with missing email returns validation error."""
        data = self.valid_signup_data.copy()
        del data['email']
        
        response = self.client.post(self.signup_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email is required')

    def test_signup_post_missing_full_name_returns_error(self):
        """Test signup with missing full name returns validation error."""
        data = self.valid_signup_data.copy()
        del data['full_name']
        
        response = self.client.post(self.signup_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Full name is required')

    def test_signup_post_missing_phone_number_returns_error(self):
        """Test signup with missing phone number returns validation error."""
        data = self.valid_signup_data.copy()
        del data['phone_number']
        
        response = self.client.post(self.signup_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phone number is required')

    def test_signup_post_missing_organization_name_returns_error(self):
        """Test signup with missing organization name returns validation error."""
        data = self.valid_signup_data.copy()
        del data['organization_name']
        
        response = self.client.post(self.signup_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Organization name is required')

    def test_signup_post_invalid_email_returns_error(self):
        """Test signup with invalid email format returns validation error."""
        data = self.valid_signup_data.copy()
        data['email'] = 'invalid-email'
        
        response = self.client.post(self.signup_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a valid email address')

    def test_signup_post_existing_email_returns_error(self):
        """Test signup with existing email returns error."""
        # Create existing user
        User.objects.create_user(email=self.valid_signup_data['email'], name='Existing User')
        
        response = self.client.post(self.signup_url, self.valid_signup_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this email already exists')

    @patch('accounts.views.send_magic_link_email')
    @patch('accounts.views.send_sms_otp')
    @patch('tasks.services.TaskService.create_verification_tasks')
    def test_signup_post_successful_creates_user_with_progressive_verification(
        self, mock_create_tasks, mock_send_sms, mock_send_email
    ):
        """Test successful signup creates user with progressive verification settings."""
        # Mock task creation to return mock tasks
        mock_create_tasks.return_value = [Mock(), Mock()]
        
        response = self.client.post(self.signup_url, self.valid_signup_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Account created successfully')
        self.assertContains(response, 'dashboard')
        
        # Check user was created
        user = User.objects.get(email=self.valid_signup_data['email'])
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.phone_number, self.valid_signup_data['phone_number'])
        
        # Check progressive verification fields
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)
        self.assertIsNotNone(user.verification_required_after)
        
        # Check verification deadline is approximately 24 hours from now
        now = timezone.now()
        time_diff = user.verification_required_after - now
        self.assertGreaterEqual(time_diff, timedelta(hours=23, minutes=59))
        self.assertLessEqual(time_diff, timedelta(hours=24, minutes=1))
        
        # Check school and membership were created
        school = School.objects.get(name=self.valid_signup_data['organization_name'])
        membership = SchoolMembership.objects.get(user=user, school=school)
        self.assertEqual(membership.role, SchoolRole.SCHOOL_OWNER)
        
        # Check verification methods were called
        mock_send_email.assert_called_once()
        mock_send_sms.assert_called_once()
        mock_create_tasks.assert_called_once_with(user, user.email, user.phone_number)

    @patch('accounts.views.send_magic_link_email')
    @patch('accounts.views.send_sms_otp')
    @patch('tasks.services.TaskService.create_verification_tasks')
    def test_signup_post_successful_creates_unverified_session(
        self, mock_create_tasks, mock_send_sms, mock_send_email
    ):
        """Test successful signup creates session with unverified user markers."""
        mock_create_tasks.return_value = [Mock(), Mock()]
        
        response = self.client.post(self.signup_url, self.valid_signup_data)
        
        # Check session markers
        session = self.client.session
        self.assertTrue(session['is_unverified_user'])
        self.assertIsNotNone(session['unverified_until'])
        
        # Check session expiry (should be set to 24 hours)
        # Note: Django's test client doesn't expose get_expiry_age() so we check the marker
        unverified_until_timestamp = session['unverified_until']
        unverified_until = timezone.datetime.fromtimestamp(unverified_until_timestamp, tz=timezone.get_current_timezone())
        time_diff = unverified_until - timezone.now()
        self.assertGreaterEqual(time_diff, timedelta(hours=23, minutes=59))
        self.assertLessEqual(time_diff, timedelta(hours=24, minutes=1))

    @patch('accounts.views.send_magic_link_email', side_effect=Exception("Email failed"))
    @patch('accounts.views.send_sms_otp', side_effect=Exception("SMS failed"))
    @patch('tasks.services.TaskService.create_verification_tasks')
    def test_signup_post_continues_despite_verification_sending_failures(
        self, mock_create_tasks, mock_send_sms, mock_send_email
    ):
        """Test that signup completes even if verification sending fails."""
        mock_create_tasks.return_value = [Mock(), Mock()]
        
        response = self.client.post(self.signup_url, self.valid_signup_data)
        
        # Signup should still succeed
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Account created successfully')
        
        # User should still be created
        user = User.objects.get(email=self.valid_signup_data['email'])
        self.assertIsNotNone(user)
        
        # Tasks should still be created
        mock_create_tasks.assert_called_once()

    @patch('accounts.views.create_user_school_and_membership', side_effect=Exception("Database error"))
    def test_signup_post_database_error_returns_error_message(self, mock_create_school):
        """Test that database errors during signup return appropriate error message."""
        response = self.client.post(self.signup_url, self.valid_signup_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'There was an issue creating your account')
        
        # User should not be created due to transaction rollback
        self.assertFalse(User.objects.filter(email=self.valid_signup_data['email']).exists())

    def test_signup_post_name_parsing_handles_single_name(self):
        """Test that single names are handled correctly."""
        data = self.valid_signup_data.copy()
        data['full_name'] = 'Madonna'
        
        with patch('accounts.views.send_magic_link_email'), \
             patch('accounts.views.send_sms_otp'), \
             patch('tasks.services.TaskService.create_verification_tasks') as mock_create_tasks:
            mock_create_tasks.return_value = [Mock(), Mock()]
            
            response = self.client.post(self.signup_url, data)
            
            self.assertEqual(response.status_code, 200)
            user = User.objects.get(email=data['email'])
            self.assertEqual(user.first_name, 'Madonna')
            self.assertEqual(user.last_name, '')

    def test_signup_post_name_parsing_handles_multiple_names(self):
        """Test that multiple names are parsed correctly into first and last name."""
        data = self.valid_signup_data.copy()
        data['full_name'] = 'John Michael Smith Jr'
        
        with patch('accounts.views.send_magic_link_email'), \
             patch('accounts.views.send_sms_otp'), \
             patch('tasks.services.TaskService.create_verification_tasks') as mock_create_tasks:
            mock_create_tasks.return_value = [Mock(), Mock()]
            
            response = self.client.post(self.signup_url, data)
            
            self.assertEqual(response.status_code, 200)
            user = User.objects.get(email=data['email'])
            self.assertEqual(user.first_name, 'John')
            self.assertEqual(user.last_name, 'Michael Smith Jr')


class VerificationHTMXEndpointsTestCase(BaseTestCase):
    """Test HTMX endpoints for email and SMS verification."""

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            phone_number='+351987654321'
        )
        
        self.send_email_url = reverse('accounts:send_verification_email')
        self.send_sms_url = reverse('accounts:send_verification_sms')

    def test_send_verification_email_requires_authentication(self):
        """Test that verification email endpoint requires authentication."""
        response = self.client.post(self.send_email_url)
        
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_send_verification_email_already_verified_returns_info(self):
        """Test sending verification email when email is already verified."""
        self.user.email_verified = True
        self.user.save()
        self.client.force_login(self.user)
        
        response = self.client.post(self.send_email_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your email is already verified!')

    @patch('accounts.views.send_magic_link_email')
    def test_send_verification_email_success(self, mock_send_email):
        """Test successful verification email sending."""
        # Mock successful email sending
        mock_send_email.return_value = {"success": True}
        self.client.force_login(self.user)
        
        response = self.client.post(self.send_email_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Verification email sent!')
        mock_send_email.assert_called_once()

    @patch('accounts.views.send_magic_link_email', side_effect=Exception("Email service error"))
    def test_send_verification_email_handles_email_service_error(self, mock_send_email):
        """Test handling of email service errors."""
        self.client.force_login(self.user)
        
        response = self.client.post(self.send_email_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An error occurred. Please try again later.')
        mock_send_email.assert_called_once()

    def test_send_verification_sms_requires_authentication(self):
        """Test that verification SMS endpoint requires authentication."""
        response = self.client.post(self.send_sms_url)
        
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_send_verification_sms_missing_phone_number(self):
        """Test SMS verification when user has no phone number."""
        self.user.phone_number = ''
        self.user.save()
        self.client.force_login(self.user)
        
        response = self.client.post(self.send_sms_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No phone number on file')

    def test_send_verification_sms_already_verified_returns_info(self):
        """Test sending verification SMS when phone is already verified."""
        self.user.phone_verified = True
        self.user.save()
        self.client.force_login(self.user)
        
        response = self.client.post(self.send_sms_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your phone is already verified!')

    @patch('accounts.views.send_sms_otp')
    def test_send_verification_sms_success(self, mock_send_sms):
        """Test successful verification SMS sending."""
        # Mock successful SMS sending
        mock_send_sms.return_value = {"success": True}
        self.client.force_login(self.user)
        
        response = self.client.post(self.send_sms_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Verification code sent')
        mock_send_sms.assert_called_once()
        
        # Check that OTP was stored in session
        session_key = f'verify_otp_{self.user.id}'
        self.assertIn(session_key, self.client.session)
        
        # Verify OTP code format (6 digits)
        otp_code = self.client.session[session_key]
        self.assertTrue(re.match(r'^\d{6}$', otp_code))

    @patch('accounts.views.send_sms_otp', side_effect=Exception("SMS service error"))
    def test_send_verification_sms_handles_sms_service_error(self, mock_send_sms):
        """Test handling of SMS service errors."""
        self.client.force_login(self.user)
        
        response = self.client.post(self.send_sms_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An error occurred. Please try again later.')
        mock_send_sms.assert_called_once()

    def test_send_verification_sms_generates_different_codes(self):
        """Test that multiple SMS requests generate different OTP codes."""
        self.client.force_login(self.user)
        
        with patch('accounts.views.send_sms_otp') as mock_send_sms:
            mock_send_sms.return_value = {"success": True}
            # Send first SMS
            response1 = self.client.post(self.send_sms_url)
            otp1 = self.client.session[f'verify_otp_{self.user.id}']
            
            # Send second SMS
            response2 = self.client.post(self.send_sms_url)
            otp2 = self.client.session[f'verify_otp_{self.user.id}']
            
            # Codes should be different (highly likely with 6-digit random codes)
            self.assertNotEqual(otp1, otp2)
            
            # Both responses should be successful
            self.assertEqual(response1.status_code, 200)
            self.assertEqual(response2.status_code, 200)

    def test_send_verification_sms_sets_expiry_time(self):
        """Test that SMS verification sets proper expiry time in session."""
        self.client.force_login(self.user)
        
        with patch('accounts.views.send_sms_otp') as mock_send_sms:
            mock_send_sms.return_value = {"success": True}
            before_time = timezone.now()
            response = self.client.post(self.send_sms_url)
            after_time = timezone.now()
            
            # Check expiry was set
            expiry_key = f'verify_otp_expires_{self.user.id}'
            self.assertIn(expiry_key, self.client.session)
            
            # Check expiry time is approximately 30 minutes from now
            expiry_timestamp = self.client.session[expiry_key]
            expiry_time = timezone.datetime.fromtimestamp(expiry_timestamp, tz=timezone.get_current_timezone())
            
            expected_min = before_time + timedelta(minutes=29, seconds=59)
            expected_max = after_time + timedelta(minutes=30, seconds=1)
            
            self.assertGreaterEqual(expiry_time, expected_min)
            self.assertLessEqual(expiry_time, expected_max)


class VerificationEdgeCasesTestCase(BaseTestCase):
    """Test edge cases and boundary conditions for verification system."""

    def setUp(self):
        self.client = Client()
        
        # Create user with verification deadline in the past
        self.expired_user = User.objects.create_user(
            email='expired@example.com',
            name='Expired User',
            phone_number='+351987654321'
        )
        self.expired_user.email_verified = False
        self.expired_user.phone_verified = False
        self.expired_user.verification_required_after = timezone.now() - timedelta(hours=1)
        self.expired_user.save()
        
        # Create user with verification deadline in the future
        self.grace_period_user = User.objects.create_user(
            email='grace@example.com',
            name='Grace User',
            phone_number='+351987654321'
        )
        self.grace_period_user.email_verified = False
        self.grace_period_user.phone_verified = False
        self.grace_period_user.verification_required_after = timezone.now() + timedelta(hours=12)
        self.grace_period_user.save()

    def test_verification_required_after_field_nullable(self):
        """Test that verification_required_after field can be null for legacy users."""
        legacy_user = User.objects.create_user(
            email='legacy@example.com',
            name='Legacy User'
        )
        legacy_user.verification_required_after = None
        legacy_user.save()
        
        # Should save without error
        self.assertIsNone(legacy_user.verification_required_after)

    def test_partially_verified_user_email_only(self):
        """Test user with only email verified."""
        user = User.objects.create_user(
            email='partial@example.com',
            name='Partial User',
            phone_number='+351987654321'
        )
        user.email_verified = True
        user.phone_verified = False
        user.verification_required_after = timezone.now() - timedelta(hours=1)
        user.save()
        
        # User should be considered verified (either email OR phone is sufficient)
        # This is tested in middleware tests, but we verify the data setup here
        self.assertTrue(user.email_verified)
        self.assertFalse(user.phone_verified)

    def test_partially_verified_user_phone_only(self):
        """Test user with only phone verified."""
        user = User.objects.create_user(
            email='partial2@example.com',
            name='Partial User 2',
            phone_number='+351987654321'
        )
        user.email_verified = False
        user.phone_verified = True
        user.verification_required_after = timezone.now() - timedelta(hours=1)
        user.save()
        
        # User should be considered verified (either email OR phone is sufficient)
        # This is tested in middleware tests, but we verify the data setup here
        self.assertFalse(user.email_verified)
        self.assertTrue(user.phone_verified)

    def test_user_without_phone_number_can_signup(self):
        """Test that signup fails gracefully if phone number is missing (per current implementation)."""
        # Based on the SignUpView code, phone_number is required
        # This test documents that behavior
        data = {
            'email': 'no-phone@example.com',
            'full_name': 'No Phone User',
            'organization_name': 'Test Org'
            # phone_number intentionally missing
        }
        
        response = self.client.post(reverse('accounts:signup'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phone number is required')
        
        # User should not be created
        self.assertFalse(User.objects.filter(email=data['email']).exists())

    @patch('accounts.views.timezone.now')
    def test_verification_deadline_calculation_precision(self, mock_now):
        """Test that verification deadline is calculated with proper precision."""
        # Fix the current time for predictable testing
        fixed_time = timezone.datetime(2023, 10, 15, 12, 0, 0, tzinfo=timezone.get_current_timezone())
        mock_now.return_value = fixed_time
        
        with patch('accounts.views.send_magic_link_email'), \
             patch('accounts.views.send_sms_otp'), \
             patch('tasks.services.TaskService.create_verification_tasks') as mock_create_tasks:
            mock_create_tasks.return_value = [Mock(), Mock()]
            
            data = {
                'email': 'precision@example.com',
                'full_name': 'Precision Test',
                'phone_number': '+351987654321',
                'organization_name': 'Test Org'
            }
            
            response = self.client.post(reverse('accounts:signup'), data)
            
            user = User.objects.get(email=data['email'])
            expected_deadline = fixed_time + timedelta(hours=24)
            
            self.assertEqual(user.verification_required_after, expected_deadline)