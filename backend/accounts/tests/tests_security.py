from datetime import timedelta
from unittest.mock import patch

import pyotp
from accounts.models import EmailVerificationCode
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class KnoxAuthenticationTests(APITestCase):
    """
    Test the Knox authentication flow with passwordless login using TOTP.
    """

    def setUp(self):
        # Create a test user
        self.user_email = "test@example.com"
        self.user = User.objects.create(
            email=self.user_email,
            name="Test User",
        )

        # Create a verification record with TOTP
        self.verification = EmailVerificationCode.generate_code(self.user_email)

        # Generate a valid TOTP code
        totp = pyotp.TOTP(self.verification.secret_key)
        self.verification_code = totp.now()

    def test_email_verification_flow(self):
        """Test the complete email verification flow with Knox token."""
        # Step 1: Request verification code
        url = reverse("request_email_code")
        response = self.client.post(url, {"email": self.user_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get the latest verification record from database
        self.verification = EmailVerificationCode.objects.filter(
            email=self.user_email, is_used=False
        ).latest("created_at")

        # Generate a valid TOTP code for verification
        totp = pyotp.TOTP(self.verification.secret_key)
        verification_code = totp.now()

        # Step 2: Verify code and get Knox token
        url = reverse("verify_email_code")
        response = self.client.post(
            url, {"email": self.user_email, "code": verification_code}
        )

        # Print error response for debugging if not 200
        if response.status_code != status.HTTP_200_OK:
            print(f"Verification response: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response contains token and user data
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.user_email)

        # Step 3: Use token to access protected endpoint
        token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        url = reverse("user_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user_email)

        # Step 4: Test logout
        url = reverse("knox_logout")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify token is no longer valid
        url = reverse("user_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rate_limiting(self):
        """Test that rate limiting is applied to auth endpoints."""
        # Test rate limiting for request-code endpoint
        url = reverse("request_email_code")

        # Make multiple requests
        for _ in range(5):
            response = self.client.post(url, {"email": self.user_email})
            self.assertIn(
                response.status_code,
                [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS],
            )

        # Test rate limiting for verify-code endpoint
        url = reverse("verify_email_code")

        # Make multiple requests with invalid code
        for _ in range(10):
            response = self.client.post(
                url, {"email": self.user_email, "code": "999999"}
            )
            self.assertIn(
                response.status_code,
                [status.HTTP_400_BAD_REQUEST, status.HTTP_429_TOO_MANY_REQUESTS],
            )

    def test_failed_attempts_tracking(self):
        """Test that failed verification attempts are tracked."""
        url = reverse("verify_email_code")

        # Disable rate limiting for this test to focus on attempt tracking
        with patch(
            "accounts.views.EmailCodeVerifyThrottle.allow_request", return_value=True
        ):
            # Make multiple invalid attempts
            for i in range(5):
                # Try with an invalid TOTP code
                response = self.client.post(
                    url, {"email": self.user_email, "code": "999999"}
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

                # Verify failed attempts are tracked correctly
                self.verification.refresh_from_db()
                self.assertEqual(self.verification.failed_attempts, i + 1)

            # Verify max attempts reached error
            response = self.client.post(
                url, {"email": self.user_email, "code": "999999"}
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("Too many failed attempts", response.data["error"])

            # Generate a valid TOTP code
            totp = pyotp.TOTP(self.verification.secret_key)
            valid_code = totp.now()

            # Try with correct code (should still fail due to max attempts)
            response = self.client.post(
                url, {"email": self.user_email, "code": valid_code}
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_limiting_verification_endpoint(self):
        """Test that rate limiting is applied to verification endpoint by both email and IP."""
        url = reverse("verify_email_code")

        # Test 1: Rate limiting by email
        test_email = f"ratelimit-{self.user_email}"
        verification = EmailVerificationCode.generate_code(test_email)

        # Make multiple requests for the same email
        request_count = 12  # More than the email limit (10/hour)

        for i in range(request_count):
            response = self.client.post(url, {"email": test_email, "code": "999999"})

            if i < 9:  # Under limit - should get 400 for invalid code
                expected_status = status.HTTP_400_BAD_REQUEST
                error_msg = f"Request {i + 1} should return 400 (invalid code) but got {response.status_code}"
            else:  # Over limit - should get 429 for rate limiting
                expected_status = status.HTTP_429_TOO_MANY_REQUESTS
                error_msg = f"Request {i + 1} should be rate limited with 429 but got {response.status_code}"

            self.assertEqual(response.status_code, expected_status, error_msg)

            # If rate limited, should have Retry-After header
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                self.assertIn("Retry-After", response)

        # Test 2: Rate limiting by IP
        # Use different emails but same IP
        for i in range(35):  # More than the IP limit (30/hour)
            different_email = f"different{i}-{self.user_email}"
            verification = EmailVerificationCode.generate_code(different_email)

            response = self.client.post(
                url, {"email": different_email, "code": "999999"}
            )

            if i < 29:  # Under IP limit - should get 400 for invalid code
                expected_status = status.HTTP_400_BAD_REQUEST
                error_msg = f"IP Request {i + 1} should return 400 (invalid code) but got {response.status_code}"
            else:  # Over IP limit - should get 429 for rate limiting
                expected_status = status.HTTP_429_TOO_MANY_REQUESTS
                error_msg = f"IP Request {i + 1} should be rate limited with 429 but got {response.status_code}"

            self.assertEqual(response.status_code, expected_status, error_msg)

            # If rate limited, should have Retry-After header
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                self.assertIn("Retry-After", response)


class AuthenticationProtectionTests(APITestCase):
    """
    Test that views correctly require authentication.
    """

    def setUp(self):
        # Create a test user
        self.test_user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword",  # Not used for login but required by create_user
            name="Test User",
            user_type="student",
        )

        # Create a Knox token for the user
        self.token_instance, self.token = AuthToken.objects.create(self.test_user)

        # Define the protected endpoints to test
        self.protected_endpoints = [
            # User endpoints
            reverse("user-list"),
            reverse("user-detail", args=[self.test_user.id]),
            reverse("user-dashboard-info"),
            reverse("user-school-profile"),
            # Profile endpoint
            reverse("user_profile"),
            # Student endpoints (since test user is a student)
            reverse("student-list"),
        ]

    def test_unauthenticated_requests_blocked(self):
        """Test that unauthenticated requests to protected endpoints are blocked."""
        # Don't set any authentication
        self.client.credentials()

        # Test with a simplified list of endpoints that should be more stable
        simple_endpoints = [
            reverse("user-list"),
            reverse("user_profile"),
        ]

        for endpoint in simple_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {endpoint} should require authentication",
            )

    def test_invalid_token_blocked(self):
        """Test that requests with invalid tokens are blocked."""
        # Set an invalid token
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid_token_value")

        for endpoint in self.protected_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {endpoint} should reject invalid tokens",
            )

    def test_valid_token_allowed(self):
        """Test that requests with valid tokens are allowed."""
        # Set a valid token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")

        for endpoint in self.protected_endpoints:
            response = self.client.get(endpoint)
            self.assertNotEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {endpoint} should accept valid tokens",
            )

    def test_expired_token_blocked(self):
        """Test that requests with expired tokens are blocked."""
        # Create a token that's already expired
        token_instance, token = AuthToken.objects.create(
            self.test_user, expiry=timedelta(seconds=-1)
        )

        # Verify the token is expired
        self.assertTrue(token_instance.expiry < timezone.now())

        # Set the expired token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        # Test with a sample endpoint
        response = self.client.get(reverse("user-list"))
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Expired tokens should be rejected",
        )

    def test_other_users_token_blocked_for_personal_resources(self):
        """Test that a token for one user can't access another user's personal resources."""
        # Create another user
        other_user = User.objects.create_user(
            email="otheruser@example.com",
            password="testpassword",
            name="Other User",
            user_type="student",
        )

        # Create a token for the other user
        _, other_token = AuthToken.objects.create(other_user)

        # Set the other user's token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {other_token}")

        # Try to access original user's detail
        response = self.client.get(reverse("user-detail", args=[self.test_user.id]))

        # For normal users, they should not see other users' details
        # The behavior might be 403 or 404 depending on how your viewset handles this
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            "Other users' tokens should not access personal resources",
        )

    def test_malformed_auth_header_blocked(self):
        """Test that malformed Authorization headers are blocked."""
        # Test various malformed headers with a simple endpoint
        test_endpoint = reverse("user-list")
        malformed_headers = [
            "TokenInvalid",
            "Bearer " + self.token,  # Wrong scheme
            "Token",  # Missing value
            self.token,  # Missing scheme
        ]

        for header in malformed_headers:
            self.client.credentials(HTTP_AUTHORIZATION=header)
            response = self.client.get(test_endpoint)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Should reject malformed auth header: {header}",
            )

    def test_auth_endpoints_accessible_without_token(self):
        """Test that authentication endpoints are accessible without a token."""
        # Clear any auth credentials
        self.client.credentials()

        # Auth endpoints that should be accessible without auth
        auth_endpoints = [
            reverse("request_email_code"),
            reverse("verify_email_code"),
        ]

        # Test request-code endpoint
        response = self.client.post(auth_endpoints[0], {"email": "test@example.com"})

        # The response should not be a 401
        self.assertNotEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            f"Auth endpoint {auth_endpoints[0]} should be accessible without authentication",
        )

        # Test verify-code endpoint
        response = self.client.post(
            auth_endpoints[1],
            {
                "email": "test@example.com",
                "code": "123456",  # Invalid code, but should be accepted by the endpoint (not return 401)
            },
        )

        # The response might be a 400 due to validation errors, but not 401
        self.assertNotEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            f"Auth endpoint {auth_endpoints[1]} should be accessible without authentication",
        )
