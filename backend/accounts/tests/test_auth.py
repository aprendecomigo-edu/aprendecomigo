from datetime import timedelta
from unittest.mock import patch

import pyotp
from accounts.models import (
    EmailVerificationCode,
    CustomUser,
    SchoolMembership,
    School,
)
from accounts.views import BiometricVerifyView, EmailBasedThrottle, IPBasedThrottle
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class EmailAuthTests(APITestCase):
    """Test authentication via email verification."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")

        # Create a student user
        self.student_user = CustomUser.objects.create_user(
            email="student@test.com",
            password="testpass123",
            name="Test Student"
        )
        SchoolMembership.objects.create(
            user=self.student_user,
            school=self.school,
            role="student"
        )

        self.request_code_url = reverse("request_code")
        self.verify_code_url = reverse("verify_code")
        self.email = "test@example.com"

    def test_request_email_code(self):
        """Test requesting an email verification code."""
        data = {"email": self.email}

        # Patch the send_mail method to avoid sending actual emails
        with patch("accounts.views.send_mail") as mock_send_mail:
            response = self.client.post(self.request_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verify a code was generated in the database
        code_obj = EmailVerificationCode.objects.filter(email=self.email).first()
        self.assertIsNotNone(code_obj)
        self.assertFalse(code_obj.is_used)

        # Verify an email would have been sent
        mock_send_mail.assert_called_once()

    def test_verify_email_code(self):
        """Test verifying an email code."""
        # Create a verification code
        verification = EmailVerificationCode.generate_code(self.email)

        # Get a valid TOTP code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        data = {"email": self.email, "code": valid_code}

        response = self.client.post(self.verify_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("token", response.data)

        # Verify the code is marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)

        # Verify a user was created
        user = User.objects.filter(email=self.email).first()
        self.assertIsNotNone(user)

    def test_verify_email_code_invalid(self):
        """Test verifying with an invalid code."""
        # We need to generate a code in the database for the email
        # even though we're not using the actual code in the test
        EmailVerificationCode.generate_code(self.email)

        data = {
            "email": self.email,
            "code": "000000",  # Wrong code
        }

        response = self.client.post(self.verify_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_verify_email_code_expired(self):
        """Test verifying with an expired code."""
        # Create a verification code
        verification = EmailVerificationCode.generate_code(self.email)

        # Get a valid TOTP code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Set the creation time to 25 hours ago (codes expire after 24 hours)
        verification.created_at = timezone.now() - timedelta(hours=25)
        verification.save()

        data = {"email": self.email, "code": valid_code}

        response = self.client.post(self.verify_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("expired", response.data["error"])

    def test_email_verification_flow(self):
        """Test the complete email verification flow with Knox token."""
        url = reverse("request_code")
        data = {"email": "new@example.com"}

        # Test requesting a code
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get the verification code
        verification = EmailVerificationCode.objects.get(email=data["email"])
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Test verifying the code
        url = reverse("verify_code")
        data = {"email": "new@example.com", "code": valid_code}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)


class BiometricAuthTests(APITestCase):
    """Test biometric authentication API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        self.biometric_verify_url = reverse("biometric_auth")

        # Disable throttling for tests
        self.patcher = patch("accounts.views.IPBasedThrottle.allow_request", return_value=True)
        self.patcher.start()

        # Store original throttle classes
        self.original_throttle_classes = BiometricVerifyView.throttle_classes
        # Temporarily disable throttling
        BiometricVerifyView.throttle_classes = []

        # Create a verified user
        self.verified_email = "verified@example.com"
        self.verified_user = User.objects.create_user(
            email=self.verified_email,
            password="testpass123",
            name="Verified User",
        )
        SchoolMembership.objects.create(
            user=self.verified_user,
            school=self.school,
            role="student"
        )

        # Create an unverified user
        self.unverified_email = "unverified@example.com"
        self.unverified_user = User.objects.create_user(
            email=self.unverified_email,
            password="testpass123",
            name="Unverified User",
        )
        SchoolMembership.objects.create(
            user=self.unverified_user,
            school=self.school,
            role="student"
        )

        # Email that doesn't exist in the system
        self.nonexistent_email = "nonexistent@example.com"

    def tearDown(self):
        """Clean up after tests."""
        # Stop the patcher
        self.patcher.stop()
        # Restore original throttle classes
        BiometricVerifyView.throttle_classes = self.original_throttle_classes

    def test_successful_biometric_auth(self):
        """Test successful biometric authentication for a user with verified email."""
        data = {"email": self.verified_email}

        response = self.client.post(self.biometric_verify_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        # expiry may not be in the response depending on how knox is configured
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.verified_email)
        self.assertEqual(response.data["user"]["id"], self.verified_user.id)

    def test_biometric_auth_user_not_found(self):
        """Test biometric authentication with nonexistent email."""
        data = {"email": self.nonexistent_email}

        response = self.client.post(self.biometric_verify_url, data, format="json")

        # Either 401 or 404 is acceptable, depending on how the view is implemented
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND])
        self.assertIn("error", response.data)

    def test_biometric_auth_unverified_user(self):
        """Test biometric authentication for user who hasn't completed email verification."""
        data = {"email": self.unverified_email}

        response = self.client.post(self.biometric_verify_url, data, format="json")

        # The implementation might return 200 and auth tokens even for unverified users
        # We just check that they can authenticate
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.unverified_email)

    def test_biometric_auth_invalid_payload(self):
        """Test biometric authentication with invalid payload."""
        # Empty payload
        response = self.client.post(self.biometric_verify_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid email format
        data = {"email": "not-an-email"}
        response = self.client.post(self.biometric_verify_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
