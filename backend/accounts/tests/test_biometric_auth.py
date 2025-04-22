from accounts.models import EmailVerificationCode
from accounts.views import BiometricVerifyView, EmailBasedThrottle, IPBasedThrottle
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class BiometricAuthTests(APITestCase):
    """Test biometric authentication API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.biometric_verify_url = reverse("biometric_verify")

        # Disable throttling for tests
        self.original_throttle_classes = BiometricVerifyView.throttle_classes
        BiometricVerifyView.throttle_classes = []

        # Create user that has previously verified their email
        self.verified_email = "verified@example.com"
        self.verified_user = User.objects.create_user(
            email=self.verified_email,
            password="password123",
            name="Verified User",
            user_type="student",
        )

        # Create verification code and mark it as used
        self.verification = EmailVerificationCode.generate_code(self.verified_email)
        self.verification.use()

        # Create an unverified user with no verification code
        self.unverified_email = "unverified@example.com"
        self.unverified_user = User.objects.create_user(
            email=self.unverified_email,
            password="password123",
            name="Unverified User",
            user_type="student",
        )

        # Email that doesn't exist in the system
        self.nonexistent_email = "nonexistent@example.com"

    def tearDown(self):
        """Clean up after tests."""
        # Restore original throttle classes
        BiometricVerifyView.throttle_classes = self.original_throttle_classes

    def test_successful_biometric_auth(self):
        """Test successful biometric authentication for a user with verified email."""
        data = {"email": self.verified_email}

        response = self.client.post(self.biometric_verify_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("expiry", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.verified_email)
        self.assertEqual(response.data["user"]["id"], self.verified_user.id)

    def test_biometric_auth_user_not_found(self):
        """Test biometric authentication with nonexistent email."""
        data = {"email": self.nonexistent_email}

        response = self.client.post(self.biometric_verify_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
        self.assertEqual(
            response.data["error"],
            "User not found or biometric authentication not allowed",
        )

    def test_biometric_auth_unverified_user(self):
        """Test biometric authentication for user who hasn't completed email verification."""
        data = {"email": self.unverified_email}

        response = self.client.post(self.biometric_verify_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
        self.assertEqual(
            response.data["error"],
            "Email verification required before using biometric login",
        )

    def test_biometric_auth_invalid_payload(self):
        """Test biometric authentication with invalid payload."""
        # Empty payload
        response = self.client.post(self.biometric_verify_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid email format
        data = {"email": "not-an-email"}
        response = self.client.post(self.biometric_verify_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_limiting(self):
        """Test rate limiting for biometric authentication."""
        # Since we've disabled throttling for tests, we'll just verify
        # that the throttle classes are configured properly in the view

        # Restore throttle classes temporarily for this test
        BiometricVerifyView.throttle_classes = self.original_throttle_classes

        # Check that the throttle classes are properly configured
        self.assertIn(EmailBasedThrottle, BiometricVerifyView.throttle_classes)
        self.assertIn(IPBasedThrottle, BiometricVerifyView.throttle_classes)

        # Disable throttling again
        BiometricVerifyView.throttle_classes = []

    def test_auth_token_in_response(self):
        """
        Test that the authentication token in the response is valid and can be used for
        authenticated requests.
        """
        # First, authenticate with biometrics
        data = {"email": self.verified_email}
        auth_response = self.client.post(self.biometric_verify_url, data, format="json")

        # Get the token from the response
        token = auth_response.data["token"]

        # Use the token to access a protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        # Try to access the user profile endpoint (which requires authentication)
        profile_url = reverse("user_profile")
        profile_response = self.client.get(profile_url)

        # Verify we can access the protected endpoint
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["email"], self.verified_email)

    def test_user_needs_to_verify_first(self):
        """Test that a user must complete email verification before using biometric auth."""
        # First, create a new user through the email verification process
        new_email = "new_user@example.com"

        # Create a verification code
        verification = EmailVerificationCode.generate_code(new_email)

        # Manually create a user without going through verification
        User.objects.create_user(
            email=new_email,
            password="password123",
            name="New User",
            user_type="student",
        )

        # Try biometric auth without having verified the email first
        data = {"email": new_email}
        response = self.client.post(self.biometric_verify_url, data, format="json")

        # Should be rejected
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Now mark the verification as used
        verification.use()

        # Try again - should work now
        response = self.client.post(self.biometric_verify_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_biometric_auth_security(self):
        """Test that the biometric auth endpoint has appropriate security measures."""
        # Check that the response contains no sensitive data beyond what's expected
        data = {"email": self.verified_email}
        response = self.client.post(self.biometric_verify_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get the actual fields in the user data
        user_fields = set(response.data["user"].keys())

        # Check that the required fields are present
        required_fields = {"id", "email", "name", "phone_number", "user_type"}
        for field in required_fields:
            self.assertIn(field, user_fields)

        # Response should only contain expected fields
        expected_response_fields = {"token", "expiry", "user"}
        self.assertEqual(set(response.data.keys()), expected_response_fields)


class BiometricSerializerTests(APITestCase):
    """Test the BiometricVerifySerializer."""

    def test_serializer_valid_data(self):
        """Test serializer with valid data."""
        from accounts.serializers import BiometricVerifySerializer

        data = {"email": "test@example.com"}
        serializer = BiometricVerifySerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], "test@example.com")

    def test_serializer_invalid_email(self):
        """Test serializer with invalid email."""
        from accounts.serializers import BiometricVerifySerializer

        # Test with missing email
        data = {}
        serializer = BiometricVerifySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

        # Test with invalid email format
        data = {"email": "not-an-email"}
        serializer = BiometricVerifySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
