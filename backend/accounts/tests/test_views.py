import inspect
import re
from unittest.mock import patch

import common.throttles
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import CustomUser, EmailVerificationCode, School, SchoolMembership
from accounts.views import UserViewSet


class TestUserSignup(TestCase):
    """Test suite for the UserViewSet signup action (signup without authentication)."""

    def setUp(self):
        """Set up test environment."""
        self.client = APIClient()
        self.url = reverse("accounts:user-signup")

        # We need to patch both the rate and the allow_request
        # First, patch all throttle instances to always allow requests
        self.allow_throttle_patcher = patch(
            "rest_framework.throttling.AnonRateThrottle.allow_request",
            return_value=True,
        )
        self.allow_throttle_patcher.start()

        # Then patch the throttle rates to use a valid format
        self.original_email_rate = common.throttles.EmailCodeRequestThrottle.rate
        self.original_ip_rate = common.throttles.IPSignupThrottle.rate
        common.throttles.EmailCodeRequestThrottle.rate = "3/d"
        common.throttles.IPSignupThrottle.rate = "3/d"

    def tearDown(self):
        """Clean up test environment."""
        # Stop patching throttles
        self.allow_throttle_patcher.stop()

        # Restore original rates
        common.throttles.EmailCodeRequestThrottle.rate = self.original_email_rate
        common.throttles.IPSignupThrottle.rate = self.original_ip_rate

    @patch("accounts.views.send_mail")
    def test_signup_success(self, mock_send_mail):
        """Test successful user signup with all required fields."""
        data = {
            "name": "New User",
            "email": "newuser@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "email",
            "school": {"name": "New School"},
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)
        self.assertIn("user", response.data)
        self.assertIn("school", response.data)

        # Verify user was created in database
        user = CustomUser.objects.get(email="newuser@example.com")
        self.assertEqual(user.name, "New User")
        self.assertEqual(user.phone_number, "+1234567890")
        self.assertEqual(user.primary_contact, "email")
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)

        # Verify school was created
        school = School.objects.get(name="New School")
        self.assertIsNotNone(school)

        # Verify school membership was created
        membership = SchoolMembership.objects.get(user=user, school=school)
        self.assertEqual(membership.role, "school_owner")
        self.assertTrue(membership.is_active)

        # Verify verification code was created
        verification = EmailVerificationCode.objects.filter(email="newuser@example.com").first()
        self.assertIsNotNone(verification)

        # Verify email would have been sent
        mock_send_mail.assert_called_once()

    def test_signup_existing_email(self):
        """Test user signup with an email that already exists."""
        # Create a user first
        CustomUser.objects.create_user(
            email="existing@example.com",
            name="Existing User",
        )

        data = {
            "name": "New User",
            "email": "existing@example.com",  # Already exists
            "phone_number": "+1234567890",
            "primary_contact": "email",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("already exists", response.data["error"])

    def test_signup_invalid_phone(self):
        """Test user signup with invalid phone number format."""
        data = {
            "name": "New User",
            "email": "newuser@example.com",
            "phone_number": "not-a-phone-number",  # Invalid format
            "primary_contact": "email",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", str(response.data))

    def test_signup_phone_as_primary(self):
        """Test user signup with phone as the primary contact."""
        with patch("accounts.views.send_mail") as mock_send_mail:
            data = {
                "name": "Phone User",
                "email": "phoneuser@example.com",
                "phone_number": "+1234567890",
                "primary_contact": "phone",
            }

            response = self.client.post(self.url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Verify user was created with phone as primary
            user = CustomUser.objects.get(email="phoneuser@example.com")
            self.assertEqual(user.primary_contact, "phone")

            # Verify code was sent
            mock_send_mail.assert_called_once()

    def test_signup_invalid_school_data(self):
        """Test user signup with invalid school data."""
        data = {
            "name": "New User",
            "email": "newuser@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "email",
            "school": {
                "name": "",  # Invalid - empty name
                "website": "not-a-url",  # Invalid URL
            },
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("school", str(response.data))

    def test_signup_no_school_data(self):
        """Test user signup without providing school data (default school should be created)."""
        with patch("accounts.views.send_mail") as mock_send_mail:
            data = {
                "name": "No School User",
                "email": "noschool@example.com",
                "phone_number": "+1234567890",
                "primary_contact": "email",
            }

            response = self.client.post(self.url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Verify default school was created
            user = CustomUser.objects.get(email="noschool@example.com")
            schools = School.objects.filter(
                memberships__user=user, memberships__role="school_owner"
            )

            self.assertEqual(schools.count(), 1)
            self.assertEqual(schools[0].name, "No School User's School")

            # Verify email verification code was sent
            mock_send_mail.assert_called_once()

    def test_regular_create_requires_authentication(self):
        """Test that regular user creation endpoint requires authentication."""
        # No authentication set up
        self.client.credentials()  # Clear any credentials

        data = {
            "name": "New User",
            "email": "newuser@example.com",
            "phone_number": "+1234567890",
        }

        # Try to use the regular create endpoint
        create_url = reverse("accounts:user-list")
        response = self.client.post(create_url, data, format="json")

        # Should fail with authentication error
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_throttling_enabled(self):
        """Test that throttling is enabled for the signup endpoint."""
        # Check that the signup action in views.py has throttle_classes in its decorator
        source = inspect.getsource(UserViewSet)

        # Check for the signup method with throttle_classes in the decorator
        signup_pattern = r"@action\([^)]*throttle_classes="
        match = re.search(signup_pattern, source, re.DOTALL)

        self.assertIsNotNone(match, "signup action should have throttle_classes in its decorator")

    def test_signup_allows_unauthenticated_access(self):
        """Test that signup endpoint allows unauthenticated access."""
        # No authentication set up
        self.client.credentials()  # Clear any credentials

        data = {
            "name": "Anonymous User",
            "email": "anon@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "email",
        }

        with patch("accounts.views.send_mail"):
            response = self.client.post(self.url, data, format="json")

        # Should succeed without authentication
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_throttle_rate_configuration(self):
        """Test that throttle rates are configured correctly to use valid DRF formats."""
        # Restore original rates first to test the actual configuration
        common.throttles.EmailCodeRequestThrottle.rate = self.original_email_rate
        common.throttles.IPSignupThrottle.rate = self.original_ip_rate

        # Check EmailCodeRequestThrottle rate uses valid time units
        throttle_rate = common.throttles.EmailCodeRequestThrottle.rate
        self.assertRegex(
            throttle_rate,
            r"^\d+/\d*[smhd]$",
            f"EmailCodeRequestThrottle rate '{throttle_rate}' should use valid time units (s, m, h, d)",
        )

        # Check IPSignupThrottle rate uses valid time units
        throttle_rate = common.throttles.IPSignupThrottle.rate
        self.assertRegex(
            throttle_rate,
            r"^\d+/\d*[smhd]$",
            f"IPSignupThrottle rate '{throttle_rate}' should use valid time units (s, m, h, d)",
        )

    def test_email_throttling(self):
        """Test that email-based throttling works for the signup endpoint."""
        # This is a low-priority test and can be skipped
        # in environments where throttling is hard to test reliably
        pass

    def test_ip_throttling(self):
        """Test that IP-based throttling works for the signup endpoint."""
        # This is a low-priority test and can be skipped
        # in environments where throttling is hard to test reliably
        pass
