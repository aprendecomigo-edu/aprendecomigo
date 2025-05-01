from datetime import timedelta
from unittest.mock import patch

import pyotp
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import EmailVerificationCode

User = get_user_model()


class VerificationCodeTests(APITestCase):
    """Test verification code generation, validation, and API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.request_code_url = reverse("accounts:request_code")
        self.verify_code_url = reverse("accounts:verify_code")
        self.email = "testuser@example.com"

        # Patch throttling to avoid rate limiting in tests
        self.throttle_patcher = patch(
            "rest_framework.throttling.AnonRateThrottle.allow_request",
            return_value=True,
        )
        self.throttle_patcher.start()

        # Patch email sending
        self.mail_patcher = patch("accounts.views.send_mail")
        self.mock_send_mail = self.mail_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.throttle_patcher.stop()
        self.mail_patcher.stop()

    def test_successful_verification(self):
        """Test successful code verification within the 5-minute window."""
        # Step 1: Request a verification code
        self.client.post(self.request_code_url, {"email": self.email}, format="json")

        # Step 2: Get the verification code from the database
        verification = EmailVerificationCode.objects.get(email=self.email)
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Step 3: Verify the code
        response = self.client.post(
            self.verify_code_url, {"email": self.email, "code": valid_code}, format="json"
        )

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)

        # Check that verification is marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)

    def test_invalid_code(self):
        """Test that an incorrect code is rejected."""
        # Generate a verification code for the email
        EmailVerificationCode.generate_code(self.email)

        # Attempt to verify with a wrong code
        response = self.client.post(
            self.verify_code_url, {"email": self.email, "code": "000000"}, format="json"
        )

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Invalid", response.data["error"])

    def test_expired_verification_code(self):
        """Test that a code expired after 5 minutes is rejected."""
        # Generate a verification code for the email
        verification = EmailVerificationCode.generate_code(self.email)

        # Get a valid code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Set the creation time to 6 minutes ago (codes now expire after 5 minutes)
        verification.created_at = timezone.now() - timedelta(minutes=6)
        verification.save()

        # Attempt to verify with the expired code
        response = self.client.post(
            self.verify_code_url, {"email": self.email, "code": valid_code}, format="json"
        )

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("expired", response.data["error"].lower())

    def test_code_just_before_expiration(self):
        """Test that a code just before the 5-minute expiration works."""
        # Generate a verification code for the email
        verification = EmailVerificationCode.generate_code(self.email)

        # Get a valid code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Set the creation time to 4 minutes 59 seconds ago (just under 5 minutes)
        verification.created_at = timezone.now() - timedelta(minutes=4, seconds=59)
        verification.save()

        # Attempt to verify with the almost-expired code
        response = self.client.post(
            self.verify_code_url, {"email": self.email, "code": valid_code}, format="json"
        )

        # Assert response - should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_max_failed_attempts(self):
        """Test that maximum failed attempts locks the code."""
        # Generate a verification code for the email
        verification = EmailVerificationCode.generate_code(self.email)

        # Track the max attempts from the model
        max_attempts = verification.max_attempts

        # Simulate multiple failed attempts
        for i in range(max_attempts):
            response = self.client.post(
                self.verify_code_url, {"email": self.email, "code": "000000"}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Get a valid code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Try with the correct code after max attempts - should still fail
        response = self.client.post(
            self.verify_code_url, {"email": self.email, "code": valid_code}, format="json"
        )

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("too many", response.data["error"].lower())

        # Verify attempts are recorded
        verification.refresh_from_db()
        self.assertEqual(verification.failed_attempts, max_attempts + 1)

    def test_used_code_rejected(self):
        """Test that a used code is rejected."""
        # Generate a verification code for the email
        verification = EmailVerificationCode.generate_code(self.email)

        # Get a valid code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Mark the code as used
        verification.use()

        # Attempt to verify with the used code
        response = self.client.post(
            self.verify_code_url, {"email": self.email, "code": valid_code}, format="json"
        )

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_new_code_invalidates_old_one(self):
        """Test that requesting a new code invalidates any existing unused codes."""
        # Generate a verification code
        verification1 = EmailVerificationCode.generate_code(self.email)

        # Get a valid code for the first verification
        totp1 = pyotp.TOTP(verification1.secret_key)
        valid_code1 = totp1.now()

        # Request a new code
        self.client.post(self.request_code_url, {"email": self.email}, format="json")

        # Get the new verification code
        verification2 = EmailVerificationCode.objects.get(email=self.email)
        totp2 = pyotp.TOTP(verification2.secret_key)
        valid_code2 = totp2.now()

        # Verify the keys are different
        self.assertNotEqual(verification1.secret_key, verification2.secret_key)

        # Try to use the first code - should fail because it was deleted when requesting the second code
        response = self.client.post(
            self.verify_code_url, {"email": self.email, "code": valid_code1}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try to use the new code - should succeed
        response = self.client.post(
            self.verify_code_url, {"email": self.email, "code": valid_code2}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_message_shows_correct_expiration(self):
        """Test that the email message shows the correct 5-minute expiration."""
        # Request a verification code
        self.client.post(self.request_code_url, {"email": self.email}, format="json")

        # Verify the email message
        self.assertTrue(self.mock_send_mail.called)
        _, kwargs = self.mock_send_mail.call_args
        self.assertIn("5 minutes", kwargs["message"])


class EmailVerificationCodeModelTests(APITestCase):
    """Test the EmailVerificationCode model methods directly."""

    def setUp(self):
        """Set up test data."""
        self.email = "modeltest@example.com"

    def test_is_valid_method_with_expiration(self):
        """Test the is_valid method with different expiration scenarios."""
        # Create a verification code
        verification = EmailVerificationCode.generate_code(self.email)
        verification.get_current_code()

        # Test with code within 5 minutes
        verification.created_at = timezone.now() - timedelta(minutes=4)
        verification.save()

        # Check that the code is still valid (no code provided = just checking expiration)
        self.assertTrue(verification.is_valid())

        # Test with code just over 5 minutes
        verification.created_at = timezone.now() - timedelta(minutes=5, seconds=1)
        verification.save()

        # Code should be invalid just after 5 minutes
        self.assertFalse(verification.is_valid())
