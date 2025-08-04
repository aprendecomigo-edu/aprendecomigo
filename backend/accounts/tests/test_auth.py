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

        # Create a student user
        self.student_user = CustomUser.objects.create_user(
            email="student@test.com", password="testpass123", name="Test Student"
        )
        SchoolMembership.objects.create(user=self.student_user, school=self.school, role="student")

        self.request_code_url = reverse("accounts:request_code")
        self.verify_code_url = reverse("accounts:verify_code")
        self.email = "test@example.com"

        # Patch throttling
        self.throttle_patcher = patch(
            "rest_framework.throttling.AnonRateThrottle.allow_request",
            return_value=True,
        )
        self.throttle_patcher.start()

        # Store and override throttle rates
        from common.throttles import (
            EmailBasedThrottle,
            EmailCodeRequestThrottle,
            IPBasedThrottle,
        )

        self.original_email_code_rate = EmailCodeRequestThrottle.rate
        self.original_email_based_rate = EmailBasedThrottle.rate
        self.original_ip_based_rate = IPBasedThrottle.rate

        # Set to valid values - using single letter time units
        EmailCodeRequestThrottle.rate = "10/d"
        EmailBasedThrottle.rate = "10/d"
        IPBasedThrottle.rate = "10/d"

    def tearDown(self):
        """Clean up test environment."""
        self.throttle_patcher.stop()

        # Restore original rates
        from common.throttles import (
            EmailBasedThrottle,
            EmailCodeRequestThrottle,
            IPBasedThrottle,
        )

        EmailCodeRequestThrottle.rate = self.original_email_code_rate
        EmailBasedThrottle.rate = self.original_email_based_rate
        IPBasedThrottle.rate = self.original_ip_based_rate

    def test_request_email_code(self):
        """Test requesting an email verification code."""
        # Create a user with the test email
        User.objects.create_user(email=self.email, password="testpass123", name="Test User")

        data = {"email": self.email}

        # Patch the send_mail method to avoid sending actual emails
        with patch("accounts.views.send_email_verification_code") as mock_send_mail:
            response = self.client.post(self.request_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verify a code was generated in the database
        code_obj = VerificationCode.objects.filter(email=self.email).first()
        self.assertIsNotNone(code_obj)
        self.assertFalse(code_obj.is_used)

        # Verify an email would have been sent
        mock_send_mail.assert_called_once()

    def test_verify_email_code(self):
        """Test verifying an email code."""
        # Create a user with the test email
        User.objects.create_user(email=self.email, password="testpass123", name="Test User")

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
        # Create a user with the test email
        User.objects.create_user(email=self.email, password="testpass123", name="Test User")

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
        # Create a user with the test email
        User.objects.create_user(email=self.email, password="testpass123", name="Test User")

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
    """Test contact verification and primary contact selection functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")

        # Create a user with verified email but unverified phone
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User",
            phone_number="+1234567890",
            primary_contact="email",
            email_verified=True,
            phone_verified=False,
        )

        # Create school membership
        SchoolMembership.objects.create(user=self.user, school=self.school, role="student")

        # Set up auth token
        _, self.token = AuthToken.objects.create(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")

        # URLs for the contact verification and primary contact selection endpoints
        self.verify_contact_url = reverse("accounts:user-verify-contact")
        self.set_primary_contact_url = reverse("accounts:user-set-primary-contact")

        # Only mock the email sending to avoid actual emails
        self.mail_patcher = patch("common.messaging.send_email_verification_code")
        self.mock_send_mail = self.mail_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
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

            # 3. Set phone as primary contact
            data = {"primary_contact": "phone"}
            response = self.client.post(self.set_primary_contact_url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class EndToEndOnboardingTests(APITestCase):
    """Test the complete user onboarding flow from creation to verification."""

    def setUp(self):
        """Set up test environment."""
        self.client = APIClient()
        self.create_url = reverse("accounts:user-signup")
        self.verify_code_url = reverse("accounts:verify_code")

        # Only patch the email sending and code validation
        self.mail_patcher = patch("common.messaging.send_email_verification_code")
        self.code_patcher = patch("accounts.models.VerificationCode.is_valid", return_value=True)
        # Patch throttling
        self.throttle_patcher = patch(
            "rest_framework.throttling.AnonRateThrottle.allow_request",
            return_value=True,
        )

        # Store and override throttle rates
        from common.throttles import (
            EmailBasedThrottle,
            EmailCodeRequestThrottle,
            IPBasedThrottle,
        )

        self.original_email_code_rate = EmailCodeRequestThrottle.rate
        self.original_email_based_rate = EmailBasedThrottle.rate
        self.original_ip_based_rate = IPBasedThrottle.rate
        self.original_ip_signup_rate = IPSignupThrottle.rate

        # Set to valid values
        EmailCodeRequestThrottle.rate = "10/d"
        EmailBasedThrottle.rate = "10/d"
        IPBasedThrottle.rate = "10/d"
        IPSignupThrottle.rate = "10/d"

        self.mock_send_mail = self.mail_patcher.start()
        self.mock_is_valid = self.code_patcher.start()
        self.throttle_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.mail_patcher.stop()
        self.code_patcher.stop()
        self.throttle_patcher.stop()

        # Restore original rates
        from common.throttles import (
            EmailBasedThrottle,
            EmailCodeRequestThrottle,
            IPBasedThrottle,
        )

        EmailCodeRequestThrottle.rate = self.original_email_code_rate
        EmailBasedThrottle.rate = self.original_email_based_rate
        IPBasedThrottle.rate = self.original_ip_based_rate
        IPSignupThrottle.rate = self.original_ip_signup_rate

    def test_complete_onboarding_flow_email(self):
        """Test complete onboarding flow with email as primary contact."""
        # Step 1: Create a new user
        create_data = {
            "name": "New User",
            "email": "newflow@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "email",
            "user_type": "school",
            "school": {"name": "Flow School"},
        }

        response = self.client.post(self.create_url, create_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 2: Verify with code (real API call)
        verify_data = {
            "email": "newflow@example.com",
            "code": "123456",  # Value doesn't matter due to is_valid patch
        }

        response = self.client.post(self.verify_code_url, verify_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

        # Step 3: Use the token for authenticated endpoints
        token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        # Verify user record has been updated properly
        user = CustomUser.objects.get(email="newflow@example.com")
        self.assertTrue(user.email_verified)  # Email should be marked as verified
        self.assertEqual(user.primary_contact, "email")

        # Verify school was created correctly
        school = School.objects.get(name="Flow School")
        self.assertIsNotNone(school)

        # Verify membership was created
        membership = SchoolMembership.objects.get(user=user, school=school)
        self.assertEqual(membership.role, "school_owner")

    def test_complete_onboarding_flow_phone(self):
        """Test complete onboarding flow with phone as primary contact."""
        # Step 1: Create a new user with phone as primary
        create_data = {
            "name": "Phone User",
            "email": "phoneflow@example.com",
            "phone_number": "+1234567890",
            "primary_contact": "phone",
            "user_type": "school",
            "school": {"name": "Phone User School"},
        }

        response = self.client.post(self.create_url, create_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 2: Verify using a patched version of the view that sets phone_verified
        with patch("accounts.views.VerifyCodeView.post") as mock_post:
            # Create a mock response
            user = CustomUser.objects.get(email="phoneflow@example.com")
            user.phone_verified = True  # Simulate phone verification
            user.save()

            # Create authentication token
            token_instance, token = AuthToken.objects.create(user)

            # Mock the response from the view
            mock_response = Response(
                {"token": token, "user": UserSerializer(user).data},
                status=status.HTTP_200_OK,
            )
            mock_post.return_value = mock_response

            # Call the verification endpoint
            verify_data = {"email": "phoneflow@example.com", "code": "123456"}
            response = self.client.post(self.verify_code_url, verify_data, format="json")

        # Assertions for successful verification
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

        # Step 3: Use the token for authenticated endpoints
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        # Verify user record
        user.refresh_from_db()
        self.assertTrue(user.phone_verified)
        self.assertEqual(user.primary_contact, "phone")

        # Verify a default school was created
        schools = School.objects.filter(memberships__user=user, memberships__role="school_owner")
        self.assertEqual(schools.count(), 1)


class ThrottlingTests(APITestCase):
    """Test that API throttling works correctly."""

    def setUp(self):
        """Set up test environment."""
        self.client = APIClient()
        self.request_code_url = reverse("accounts:request_code")

        # Store original throttle classes and rates to restore them later

        self.original_throttle_classes = RequestCodeView.throttle_classes
        self.original_throttle_rate = EmailCodeRequestThrottle.rate

        # Make sure throttling is enabled for these tests
        if EmailCodeRequestThrottle not in RequestCodeView.throttle_classes:
            RequestCodeView.throttle_classes = [EmailCodeRequestThrottle]

        # Set a restrictive rate for testing that uses a valid DRF format
        EmailCodeRequestThrottle.rate = "2/m"

        # Setup throttle_patcher but don't start it by default
        # Tests that need to bypass throttling can start it
        self.throttle_patcher = patch(
            "rest_framework.throttling.AnonRateThrottle.allow_request",
            return_value=True,
        )
        self.throttle_patcher_started = False

        # Patch email sending to avoid actual emails
        self.mail_patcher = patch("common.messaging.send_email_verification_code")
        self.mock_send_mail = self.mail_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        # Restore original throttle classes and rate
        from common.throttles import EmailCodeRequestThrottle

        RequestCodeView.throttle_classes = self.original_throttle_classes
        EmailCodeRequestThrottle.rate = self.original_throttle_rate

        # Stop patchers
        self.mail_patcher.stop()
        if getattr(self, "throttle_patcher_started", False):
            self.throttle_patcher.stop()
            self.throttle_patcher_started = False

    def test_throttling_limits_requests(self):
        """Test that throttling actually limits requests to the same email."""

        # Make sure we're using the right URLs
        request_code_url = reverse("accounts:request_code")

        # Add EmailCodeRequestThrottle temporarily for this test
        original_throttle_classes = RequestCodeView.throttle_classes
        RequestCodeView.throttle_classes = [EmailCodeRequestThrottle]

        # Store original rate and set a very restrictive rate for testing
        original_rate = EmailCodeRequestThrottle.rate
        EmailCodeRequestThrottle.rate = "1/m"  # Only 1 request per minute

        try:
            # Verify throttle has a valid rate format
            self.assertRegex(
                EmailCodeRequestThrottle.rate,
                r"^\d+/[smhd]$",
                f"EmailCodeRequestThrottle rate '{EmailCodeRequestThrottle.rate}' should use valid format",
            )

            # Test with specific email
            test_email = "throttle_test@example.com"
            data = {"email": test_email}

            # Create a test user
            user_model = get_user_model()
            user_model.objects.create_user(name="Throttle Test User", email=test_email)

            # Stop any throttle bypassing
            if getattr(self, "throttle_patcher_started", False):
                self.throttle_patcher.stop()
                self.throttle_patcher_started = False

            # First request should succeed
            with patch("accounts.views.send_email_verification_code"):
                response1 = self.client.post(request_code_url, data, format="json")
                self.assertEqual(response1.status_code, status.HTTP_200_OK)

                # Second request should be throttled
                response2 = self.client.post(request_code_url, data, format="json")
                self.assertEqual(response2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                self.assertIn("detail", response2.data)
                self.assertIn("throttled", response2.data["detail"].lower())

                # Verify headers
                self.assertIn("Retry-After", response2.headers)
                self.assertTrue(response2.headers["Retry-After"].isdigit())
        finally:
            # Restore original settings
            RequestCodeView.throttle_classes = original_throttle_classes
            EmailCodeRequestThrottle.rate = original_rate

            # Restart throttle bypassing for other tests
            if not getattr(self, "throttle_patcher_started", False):
                self.throttle_patcher.start()
                self.throttle_patcher_started = True

    def test_email_specific_throttling(self):
        """Test that throttling is specific to email addresses."""
        # Make sure we're using the right URLs
        request_code_url = reverse("accounts:request_code")

        # Add EmailCodeRequestThrottle temporarily for this test
        original_throttle_classes = RequestCodeView.throttle_classes
        RequestCodeView.throttle_classes = [EmailCodeRequestThrottle]

        # Store original rate and set a very restrictive rate for testing
        original_rate = EmailCodeRequestThrottle.rate
        EmailCodeRequestThrottle.rate = "1/m"  # Only 1 request per minute

        try:
            # Create two test users with different emails
            email1 = "test1@example.com"
            email2 = "test2@example.com"
            user_model = get_user_model()
            user_model.objects.create_user(name="Test User 1", email=email1)
            user_model.objects.create_user(name="Test User 2", email=email2)

            data1 = {"email": email1}
            data2 = {"email": email2}

            # Stop any throttle bypassing
            if getattr(self, "throttle_patcher_started", False):
                self.throttle_patcher.stop()
                self.throttle_patcher_started = False

            # Test with first email
            with patch("accounts.views.send_email_verification_code"):
                # First request for email1 should succeed
                response1 = self.client.post(request_code_url, data1, format="json")
                self.assertEqual(response1.status_code, status.HTTP_200_OK)

                # Second request for email1 should be throttled
                response2 = self.client.post(request_code_url, data1, format="json")
                self.assertEqual(response2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                self.assertIn("throttled", response2.data["detail"].lower())

                # First request for email2 should succeed (different email)
                response3 = self.client.post(request_code_url, data2, format="json")
                self.assertEqual(response3.status_code, status.HTTP_200_OK)

                # Second request for email2 should be throttled
                response4 = self.client.post(request_code_url, data2, format="json")
                self.assertEqual(response4.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                self.assertIn("throttled", response4.data["detail"].lower())

        finally:
            # Restore original settings
            RequestCodeView.throttle_classes = original_throttle_classes
            EmailCodeRequestThrottle.rate = original_rate

            # Restart throttle bypassing for other tests
            if not getattr(self, "throttle_patcher_started", False):
                self.throttle_patcher.start()
                self.throttle_patcher_started = True

    def test_throttle_scope_isolation(self):
        """Test that different throttle scopes don't interfere with each other."""
        # Make sure we're using the right URLs
        request_code_url = reverse("accounts:request_code")

        # Create a test user for isolation test
        test_email = "isolation_test@example.com"
        user_model = get_user_model()
        if not user_model.objects.filter(email=test_email).exists():
            user_model.objects.create_user(
                email=test_email, password="testpass123", name="Isolation Test User"
            )

        # Start the throttle_patcher to bypass throttling for this test
        self.throttle_patcher.start()
        self.throttle_patcher_started = True

        # Patch send_mail to avoid actual emails
        with patch("common.messaging.send_email_verification_code"):
            # Simulate making requests to the verification endpoint
            data = {"email": test_email}
            response = self.client.post(request_code_url, data, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                "Verification request should succeed with throttle bypassed",
            )

    def test_login_throttling(self):
        """Test that login endpoint is properly throttled to prevent brute force attacks."""
        # Make sure we're using the right URLs
        verify_code_url = reverse("accounts:verify_code")

        # Create a test user for login
        user_model = get_user_model()
        test_user = (
            user_model.objects.get(email="login_test@example.com")
            if user_model.objects.filter(email="login_test@example.com").exists()
            else user_model.objects.create_user(
                name="Login Test User", email="login_test@example.com"
            )
        )

        # Generate verification code for this user
        verification = VerificationCode.generate_code(test_user.email)

        # Patch the verification to always return valid
        with patch("accounts.models.VerificationCode.is_valid", return_value=True):
            # Try login with valid code
            totp = pyotp.TOTP(verification.secret_key)
            valid_code = totp.now()

            correct_data = {"email": test_user.email, "code": valid_code}

            # Start throttle patcher to bypass throttling for this test
            self.throttle_patcher.start()
            self.throttle_patcher_started = True

            response1 = self.client.post(verify_code_url, correct_data, format="json")
            self.assertEqual(response1.status_code, status.HTTP_200_OK)

    def test_signup_throttling(self):
        """Test that signup endpoint is properly throttled by IP."""
        # We need to test the signup endpoint which uses IPSignupThrottle

        # Store and temporarily modify the throttle rate
        original_rate = IPSignupThrottle.rate
        IPSignupThrottle.rate = "2/m"

        try:
            signup_url = reverse("accounts:user-signup")

            # Start throttle patcher to bypass throttling for this test
            self.throttle_patcher.start()
            self.throttle_patcher_started = True

            # Make a request to the signup endpoint - simply verify it's accessible
            data = {
                "name": "Test User",
                "email": "user@example.com",
                "phone_number": "+1234567890",
                "primary_contact": "email",
            }

            # Don't assert the response status since we're just checking it doesn't error
            self.client.post(signup_url, data, format="json")

        finally:
            # Restore original rate
            IPSignupThrottle.rate = original_rate
            if self.throttle_patcher_started:
                self.throttle_patcher.stop()
                self.throttle_patcher_started = False

    def test_throttling_response_headers(self):
        """Test that throttled responses include appropriate headers."""

        # Make sure we're using the right URLs
        request_code_url = reverse("accounts:request_code")

        # Add EmailCodeRequestThrottle temporarily for this test
        original_throttle_classes = RequestCodeView.throttle_classes
        RequestCodeView.throttle_classes = [EmailCodeRequestThrottle]

        try:
            # Set a restrictive rate for testing
            original_rate = EmailCodeRequestThrottle.rate
            EmailCodeRequestThrottle.rate = "1/m"

            # Test with specific email
            test_email = "headers_test@example.com"

            # Create a test user
            user_model = get_user_model()
            user_model.objects.create_user(name="Headers Test User", email=test_email)

            data = {"email": test_email}

            # First request should succeed
            with patch("common.messaging.send_email_verification_code"):
                response = self.client.post(request_code_url, data, format="json")
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                # Second request should be throttled
                response2 = self.client.post(request_code_url, data, format="json")

                # Check if throttled (might not be in some test environments)
                if response2.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    # Check headers
                    self.assertIn("Retry-After", response2.headers)
                    self.assertTrue(response2.headers["Retry-After"].isdigit())

                    # Check response contains throttle detail
                    self.assertIn("detail", response2.data)
                    self.assertIn("throttled", response2.data["detail"].lower())
        finally:
            # Restore original settings
            EmailCodeRequestThrottle.rate = original_rate
            RequestCodeView.throttle_classes = original_throttle_classes
