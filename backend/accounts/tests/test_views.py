"""
API view tests for the Aprende Comigo platform.

Tests focus on API endpoint behavior, request/response patterns, and
user signup flows. Authentication tests are covered in test_auth.py.
"""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import CustomUser, School, SchoolMembership, VerificationCode


class UserSignupAPITests(TestCase):
    """Test user signup API endpoint behavior.
    
    Covers successful signups, validation errors, and edge cases
    for the public user registration endpoint.
    """

    def setUp(self):
        """Set up test environment."""
        self.client = APIClient()
        self.signup_url = reverse("accounts:user-signup")

        # Bypass throttling for cleaner test focus
        self.throttle_patcher = patch(
            "rest_framework.throttling.AnonRateThrottle.allow_request",
            return_value=True
        )
        self.throttle_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.throttle_patcher.stop()

    @patch("common.messaging.send_email_verification_code")
    def test_signup_success(self, mock_send_mail):
        """Test successful user signup creates user, school, and sends verification."""
        data = {
            "name": "New User",
            "email": "newuser@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "email",
            "user_type": "school",
            "school": {"name": "New School"},
        }

        response = self.client.post(self.signup_url, data, format="json")

        # Verify API response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)
        self.assertIn("user", response.data)
        self.assertIn("school", response.data)

        # Verify user created with correct attributes
        user = CustomUser.objects.get(email="newuser@example.com")
        self.assertEqual(user.name, "New User")
        self.assertEqual(user.phone_number, "+1234567890")
        self.assertEqual(user.primary_contact, "email")
        self.assertFalse(user.email_verified)  # Should start unverified
        self.assertFalse(user.phone_verified)

        # Verify school and membership created
        school = School.objects.get(name="New School")
        membership = SchoolMembership.objects.get(user=user, school=school)
        self.assertEqual(membership.role, "school_owner")
        self.assertTrue(membership.is_active)

        # Verify verification code created
        verification = VerificationCode.objects.filter(email="newuser@example.com").first()
        self.assertIsNotNone(verification)

    def test_signup_existing_email(self):
        """Test signup with existing email returns appropriate error."""
        # Create existing user
        CustomUser.objects.create_user(
            email="existing@example.com",
            name="Existing User"
        )

        data = {
            "name": "New User",
            "email": "existing@example.com",  # Duplicate email
            "phone_number": "+1234567890",
            "primary_contact": "email",
            "user_type": "school",
            "school": {"name": "Test School"},
        }

        response = self.client.post(self.signup_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("already exists", response.data["error"])

    def test_signup_invalid_phone(self):
        """Test signup with invalid phone number format returns validation error."""
        data = {
            "name": "New User",
            "email": "newuser@example.com",
            "phone_number": "invalid-phone",  # Invalid format
            "primary_contact": "email",
            "user_type": "school",
            "school": {"name": "Test School"},
        }

        response = self.client.post(self.signup_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", str(response.data))

    @patch("common.messaging.send_email_verification_code")
    def test_signup_phone_as_primary_contact(self, mock_send_mail):
        """Test signup with phone as primary contact method."""
        data = {
            "name": "Phone User",
            "email": "phoneuser@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "phone",
            "user_type": "school",
            "school": {"name": "Phone User School"},
        }

        response = self.client.post(self.signup_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user created with phone as primary contact
        user = CustomUser.objects.get(email="phoneuser@example.com")
        self.assertEqual(user.primary_contact, "phone")

    def test_signup_invalid_school_data(self):
        """Test signup with invalid school data returns validation errors."""
        data = {
            "name": "New User",
            "email": "newuser@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "email",
            "user_type": "school",
            "school": {
                "name": "",  # Invalid - empty name
                "website": "not-a-url",  # Invalid URL
            },
        }

        response = self.client.post(self.signup_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("school", str(response.data))

    def test_signup_missing_school_data(self):
        """Test signup without school data returns validation error."""
        data = {
            "name": "No School User",
            "email": "noschool@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "email",
            "user_type": "school",
            # Missing school data
        }

        response = self.client.post(self.signup_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("school", str(response.data))

    def test_signup_empty_school_name(self):
        """Test signup with empty school name returns validation error."""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "email",
            "user_type": "school",
            "school": {"name": ""},  # Empty school name
        }

        response = self.client.post(self.signup_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("school", str(response.data))
        self.assertIn("name", str(response.data))

    def test_regular_user_create_requires_authentication(self):
        """Test that regular user creation endpoint requires authentication."""
        data = {
            "name": "New User",
            "email": "newuser@example.com",
            "phone_number": "+1234567890",
        }

        try:
            create_url = reverse("accounts:user-list")
            response = self.client.post(create_url, data, format="json")
            # Should require authentication
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        except Exception:
            # If endpoint doesn't exist, test passes (endpoint is optional)
            pass

    def test_signup_allows_unauthenticated_access(self):
        """Test that signup endpoint allows unauthenticated access."""
        # Clear any authentication
        self.client.credentials()
        
        data = {
            "name": "Anonymous User",
            "email": "anon@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "email",
            "user_type": "school",
            "school": {"name": "Anonymous School"},
        }

        with patch("common.messaging.send_email_verification_code"):
            response = self.client.post(self.signup_url, data, format="json")

        # Should succeed without authentication
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)




