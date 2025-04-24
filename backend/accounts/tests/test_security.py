from datetime import timedelta
from unittest.mock import patch

from accounts.models import SchoolMembership, School
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class KnoxAuthenticationTests(APITestCase):
    """
    Test the Knox authentication flow.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User",
        )

        # Create a token for this user
        _, self.token = AuthToken.objects.create(self.user)

    def test_valid_token_allowed(self):
        """Test that a valid token grants access to protected resources."""
        # Set the authorization header with a valid token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")

        # Try to access a protected endpoint
        url = reverse("user_profile")
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expired_token_blocked(self):
        """Test that an expired token is rejected."""
        # Create a token
        instance, token = AuthToken.objects.create(self.user)

        # Set the token's expiry to the past
        instance.expiry = timezone.now() - timedelta(hours=1)
        instance.save()

        # Set the authorization header with the expired token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        # Try to access a protected endpoint
        url = reverse("user_profile")
        response = self.client.get(url)

        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_other_users_token_blocked_for_personal_resources(self):
        """Test that a user cannot access another user's resources with their token."""
        # Create another user
        other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass123",
            name="Other User",
        )

        # Create a token for the other user
        _, other_token = AuthToken.objects.create(other_user)

        # Set the authorization header with the other user's token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {other_token}")

        # Try to access the first user's profile using the second user's token
        url = reverse("user-detail", kwargs={"pk": self.user.pk})
        response = self.client.get(url)

        # Should return 404 Not Found (as if the resource doesn't exist)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_malformed_auth_header_blocked(self):
        """Test that malformed authorization headers are rejected."""
        # Set a malformed authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Token malformed-token")

        # Try to access a protected endpoint
        url = reverse("user_profile")
        response = self.client.get(url)

        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Try with a completely wrong format
        self.client.credentials(HTTP_AUTHORIZATION=f"Basic some-basic-auth")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Try with empty token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token ")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_endpoints_accessible_without_token(self):
        """Test that authentication endpoints are accessible without a token."""
        # Clear any authorization headers
        self.client.credentials()

        # Try to access the token login endpoint
        url = reverse("request_code")
        response = self.client.post(url, {"email": "new@example.com"})

        # Should not return 401 (it might return 200 or 429 depending on rate limiting)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticationProtectionTests(APITestCase):
    """
    Test that views correctly require authentication.
    """

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_unauthenticated_requests_blocked(self):
        """Test that unauthenticated requests are blocked for protected endpoints."""
        # List of protected URLs to test
        protected_urls = [
            reverse("user-list"),
            reverse("school-list"),
            reverse("student-list"),
            reverse("teacher-list"),
            reverse("user_profile"),
            # Add more protected endpoints here
        ]

        # Try to access each protected endpoint without authentication
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"URL {url} should require authentication but returned {response.status_code}"
            )

        # Also test a POST request to a protected endpoint
        url = reverse("school-list")
        data = {"name": "Test School"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
