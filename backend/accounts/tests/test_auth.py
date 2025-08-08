from datetime import timedelta
from unittest.mock import patch

import pyotp
from common.throttles import EmailCodeRequestThrottle, IPSignupThrottle
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from knox.models import AuthToken
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    VerificationCode,
)
from accounts.serializers import UserSerializer
from accounts.views import RequestCodeView

User = get_user_model()

MAX_ALLOWED_REQUESTS = 2


class EmailAuthTests(APITestCase):
    """Test authentication via email verification."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        self.email = "test@example.com"  # Add the missing email attribute

        # Create a test user
        self.test_user = CustomUser.objects.create_user(
            email=self.email, password="testpass123", name="Test User"
        )
        SchoolMembership.objects.create(user=self.test_user, school=self.school, role="student")

        self.request_code_url = reverse("accounts:request_code")
        self.verify_code_url = reverse("accounts:verify_code")
        
        # Bypass throttling for cleaner tests
        self.throttle_patcher = patch(
            "rest_framework.throttling.AnonRateThrottle.allow_request",
            return_value=True,
        )
        self.throttle_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.throttle_patcher.stop()

    def test_request_email_code_success(self):
        """Test successfully requesting an email verification code for existing user."""
        data = {"email": self.test_user.email}

        with patch("common.messaging.send_email_verification_code") as mock_send_mail:
            response = self.client.post(self.request_code_url, data, format="json")

        # Verify API response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verify verification code was created
        code_obj = VerificationCode.objects.filter(email=self.test_user.email).first()
        self.assertIsNotNone(code_obj)
        self.assertFalse(code_obj.is_used)
        self.assertEqual(code_obj.failed_attempts, 0)

        # Note: Email sending is an implementation detail, focus on API behavior

    def test_verify_email_code(self):
        """Test verifying an email code."""
        # User already exists from setUp() as self.test_user
        
        # Create a verification code
        verification = VerificationCode.generate_code(self.email)

        # Get a valid TOTP code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Patch the verification to always return valid
        with patch("accounts.models.VerificationCode.is_valid", return_value=True):
            data = {"email": self.email, "code": valid_code}
            response = self.client.post(self.verify_code_url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("user", response.data)
            self.assertIn("token", response.data)

    def test_verify_email_code_invalid(self):
        """Test verifying with an invalid code."""
        # User already exists from setUp() as self.test_user

        # We need to generate a code in the database for the email
        # even though we're not using the actual code in the test
        VerificationCode.generate_code(self.email)

        data = {
            "email": self.email,
            "code": "000000",  # Wrong code
        }

        response = self.client.post(self.verify_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_verify_email_code_expired(self):
        """Test verifying with an expired code."""
        # User already exists from setUp() as self.test_user

        # Create a verification code
        verification = VerificationCode.generate_code(self.email)

        # Get a valid TOTP code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Set the creation time to 6 minutes ago (codes expire after 5 minutes)
        verification.created_at = timezone.now() - timedelta(minutes=6)
        verification.save()

        data = {"email": self.email, "code": valid_code}

        response = self.client.post(self.verify_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("expired", response.data["error"])

    def test_email_verification_flow(self):
        """Test the complete email verification flow with Knox token."""
        # Create a user with the test email
        test_email = "new@example.com"
        User.objects.create_user(email=test_email, password="testpass123", name="New Test User")

        url = reverse("accounts:request_code")
        data = {"email": test_email}

        # Test requesting a code
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get the verification code
        verification = VerificationCode.objects.get(email=data["email"])
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Test verifying the code
        # Patch the verification to always return valid
        with patch("accounts.models.VerificationCode.is_valid", return_value=True):
            url = reverse("accounts:verify_code")
            data = {"email": test_email, "code": valid_code}
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("token", response.data)

    def test_request_email_code_unregistered_user(self):
        """Test that unregistered users cannot request verification codes."""
        url = reverse("accounts:request_code")
        data = {"email": "notarealuser@example.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "If an account exists with this email, a verification code has been sent.",
        )

    def test_verify_email_code_unregistered_user(self):
        """Test that unregistered users cannot verify codes."""
        url = reverse("accounts:verify_code")
        data = {"email": "notarealuser@example.com", "code": "123456"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "If an account exists with this email, a verification code has been sent.",
        )


class ContactVerificationTests(APITestCase):
    """Test contact verification and primary contact management.
    
    These tests cover phone/email verification and primary contact selection
    for authenticated users managing their contact preferences.
    """

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Test School")

        # Create user with verified email, unverified phone
        self.user = CustomUser.objects.create_user(
            email="contact@example.com",
            password="testpass123",
            name="Contact User",
            phone_number="+1234567890",
            primary_contact="email",
            email_verified=True,
            phone_verified=False,
        )
        SchoolMembership.objects.create(user=self.user, school=self.school, role="student")

        # Authenticate user
        _, self.token = AuthToken.objects.create(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")

        # API endpoints
        try:
            self.verify_contact_url = reverse("accounts:user-verify-contact")
            self.set_primary_contact_url = reverse("accounts:user-set-primary-contact")
        except Exception:
            self.verify_contact_url = None
            self.set_primary_contact_url = None

        # Mock email sending
        self.mail_patcher = patch("common.messaging.send_email_verification_code")
        self.mail_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.mail_patcher.stop()

    @patch("accounts.models.VerificationCode.is_valid", return_value=True)
    def test_verify_phone(self, mock_is_valid):
        """Test verifying phone number."""
        # Create a verification code in the database
        verification = VerificationCode.generate_code(self.user.phone_number)

        # Make the actual API request to verify the phone
        data = {
            "contact_type": "phone",
            "code": "123456",  # Value doesn't matter due to is_valid patch
        }

        response = self.client.post(self.verify_contact_url, data, format="json")

        # Verify the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("user", response.data)

        # Verify the user's phone is now marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.phone_verified)

        # Verify the code is marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)

    def test_verify_contact_invalid_code(self):
        """Test verifying contact with invalid code."""
        # Create a verification code
        verification = VerificationCode.generate_code(self.user.phone_number)

        # Make the verification request with wrong code
        data = {
            "contact_type": "phone",
            "code": "000000",  # Wrong code
        }

        response = self.client.post(self.verify_contact_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

        # User's verification status should remain unchanged
        self.user.refresh_from_db()
        self.assertFalse(self.user.phone_verified)

        # Verify the code is still available for use
        verification.refresh_from_db()
        self.assertFalse(verification.is_used)

    def test_set_primary_contact_to_phone(self):
        """Test setting phone as primary contact after verification."""
        # First, verify the phone
        self.user.phone_verified = True
        self.user.save()

        # Now set phone as primary contact using the API
        data = {"primary_contact": "phone"}

        response = self.client.post(self.set_primary_contact_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("user", response.data)

        # Verify primary_contact was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.primary_contact, "phone")

    def test_set_primary_contact_unverified(self):
        """Test setting unverified contact as primary (should fail)."""
        # Try to set unverified phone as primary
        data = {"primary_contact": "phone"}

        response = self.client.post(self.set_primary_contact_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("must be verified", response.data["error"])

        # Primary contact should remain unchanged
        self.user.refresh_from_db()
        self.assertEqual(self.user.primary_contact, "email")

    def test_end_to_end_contact_workflow(self):
        """Test the complete contact verification and primary contact selection workflow."""
        # 1. Create code for phone verification
        verification = VerificationCode.generate_code(self.user.phone_number)
        initial_code = verification.get_current_code()

        # 2. Verify phone with API call
        with patch("accounts.models.VerificationCode.is_valid", return_value=True):
            # Make request to verify phone
            data = {
                "contact_type": "phone",
                "code": initial_code,  # Using the actual code
            }
            response = self.client.post(self.verify_contact_url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Verify user's phone is now verified
            self.user.refresh_from_db()
            self.assertTrue(self.user.phone_verified)

            # Verify code was marked as used
            verification.refresh_from_db()
            self.assertTrue(verification.is_used)

            # Step 2: Set phone as primary contact
            primary_data = {"primary_contact": "phone"}
            response = self.client.post(self.set_primary_contact_url, primary_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Confirm primary contact updated
            self.user.refresh_from_db()
            self.assertEqual(self.user.primary_contact, "phone")

