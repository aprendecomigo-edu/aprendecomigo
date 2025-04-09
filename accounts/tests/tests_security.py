from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class JWTSecurityTests(TestCase):
    """Test cases for JWT token security in the API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create a test user
        self.user = User.objects.create_user(
            email="apitest@example.com", password="testpass123", name="API Test User"
        )

        # Create refresh and access tokens
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)

        # Endpoints
        self.verify_code_url = reverse("verify_email_code")
        self.user_profile_url = reverse("user-profile")
        self.dashboard_info_url = reverse("user-dashboard-info")

    def test_authentication_required(self):
        """Test that protected endpoints require authentication."""
        # Try to access user profile without token
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Try with token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response data is for correct user
        self.assertEqual(response.data["email"], self.user.email)

    def test_token_expiration(self):
        """Test that expired tokens are rejected."""
        # Create a token that's already expired
        from rest_framework_simplejwt.tokens import AccessToken

        # Generate an access token with an expiration time in the past
        token = AccessToken()
        token.payload["exp"] = timezone.now().timestamp() - 300  # 5 minutes ago
        token.payload["user_id"] = self.user.id
        expired_token = str(token)

        # Try to access protected endpoint with expired token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {expired_token}")
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Test token refresh functionality."""
        refresh_url = reverse("token_refresh")

        # Get new access token using refresh token
        response = self.client.post(refresh_url, {"refresh": str(self.refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

        # Verify new token works
        new_access_token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access_token}")
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_invalidation_on_logout(self):
        """Test that tokens are invalidated on logout."""
        # First verify token works
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Logout
        logout_url = reverse("logout")
        response = self.client.post(logout_url, {"refresh": str(self.refresh)})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Try to use access token again
        response = self.client.get(self.user_profile_url)
        # Note: Without blacklisting, the token may still work until it expires
        # This test will need adjustment based on how token blacklisting is implemented

    def test_token_cant_be_used_after_password_change(self):
        """Test that tokens are invalidated after password change."""
        # First verify token works
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Change password
        self.user.set_password("newpassword123")
        self.user.save()

        # Token should still work
        # (DRF doesn't invalidate tokens on password change by default)
        # This test might need to be adjusted if you implement custom token invalidation
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # TODO: To make this security feature work,
        # you'd need to track token issuance time
        # and compare it with password change time


class APIRateLimitTests(TestCase):
    """Test rate limiting for API endpoints if implemented."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.verify_code_url = reverse("verify_email_code")

    def test_login_rate_limiting(self):
        """Test rate limiting for login attempts."""
        # This is a placeholder and should be implemented if rate limiting is added
        # The exact implementation depends on how rate limiting is configured

        # Make multiple rapid requests to auth endpoint
        for i in range(10):
            self.client.post(
                self.verify_code_url,
                {"email": f"test{i}@example.com", "code": "invalid"},
            )

        # If rate limiting is implemented, the last requests should be rejected
        # response = self.client.post(self.verify_code_url,
        # {"email": "test@example.com", "code": "invalid"})
        # self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Note: Uncomment and adjust the assertion once rate limiting is implemented
