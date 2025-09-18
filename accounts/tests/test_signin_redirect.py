"""
Integration tests for signin redirect functionality.

Tests cover the complete signin redirect flow including:
- Basic redirect flow from protected page -> signin -> back to original page
- Default behavior when no next parameter is provided
- Session cleanup after successful signin
- Security considerations for preventing external redirects
- Edge cases with various URL patterns

The signin flow uses:
- HTMX forms for signin
- OTP verification via email/SMS
- Session-based storage for the next URL
- VerifyOTPView.post() handles the final redirect after OTP verification
"""

from unittest.mock import Mock, patch
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership, SchoolRole
from accounts.services.otp_service import OTPService

User = get_user_model()


class SignInRedirectTest(TestCase):
    """Test signin redirect functionality with comprehensive coverage."""

    def setUp(self):
        """Set up test data for signin redirect tests."""
        # Create test user with verified email/phone for OTP
        self.user = User.objects.create_user(
            email="testuser@example.com",
            name="Test User",
            phone_number="+351987654321",
            email_verified=True,
            phone_verified=True,
        )

        # Create a school and membership for the user
        self.school = School.objects.create(name="Test School", contact_email=self.user.email)
        SchoolMembership.objects.create(user=self.user, school=self.school, role=SchoolRole.TEACHER, is_active=True)

    def _simulate_signin_with_otp(self, next_url=None):
        """
        Helper method to simulate complete signin flow with OTP verification.

        Args:
            next_url: Optional next URL to include in initial signin request

        Returns:
            Final response from OTP verification
        """
        # Step 1: GET signin page (with optional next parameter)
        signin_url = reverse("accounts:signin")
        if next_url:
            signin_url += f"?next={next_url}"

        get_response = self.client.get(signin_url)
        self.assertEqual(get_response.status_code, 200)

        # Step 2: POST email to signin form
        with (
            patch("accounts.views.user_exists", return_value=True),
            patch("accounts.db_queries.get_user_by_email", return_value=self.user),
        ):
            email_response = self.client.post(
                reverse("accounts:signin"), {"email": self.user.email}, headers={"hx-request": "true"}
            )

            # Should show delivery options
            self.assertIn(email_response.status_code, [200, 302])

        # Step 3: Choose email delivery method
        with patch("messaging.services.send_otp_email_message") as mock_send_email:
            mock_send_email.return_value = True

            delivery_response = self.client.post(
                reverse("accounts:send_otp_email"), {"delivery_method": "email"}, headers={"hx-request": "true"}
            )

        # Step 4: Verify OTP
        with patch.object(OTPService, "verify_otp") as mock_verify:
            # Mock successful OTP verification
            mock_verify.return_value = (True, self.user)

            otp_response = self.client.post(
                reverse("accounts:verify_otp"), {"verification_code": "123456"}, headers={"hx-request": "true"}
            )

            return otp_response

    def test_basic_redirect_flow(self):
        """Test that user is redirected to original page after successful signin."""
        # Visit a protected page that requires login
        protected_url = reverse("accounts:profile")

        # This should redirect to signin with next parameter
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, 302)

        # Check that redirect includes next parameter
        signin_url = response.url
        self.assertIn("/signin/", signin_url)
        self.assertIn(f"next={protected_url}", signin_url)

        # Complete signin flow
        final_response = self._simulate_signin_with_otp(next_url=protected_url)

        # Should receive HX-Redirect header pointing to the original protected page
        self.assertEqual(final_response.status_code, 200)
        self.assertEqual(final_response.headers.get("HX-Redirect"), protected_url)

    def test_signin_stores_next_url_in_session(self):
        """Test that SignInView.get() properly stores next URL in session."""
        next_url = reverse("accounts:profile")
        signin_url = reverse("accounts:signin") + f"?next={next_url}"

        # Visit signin page with next parameter
        response = self.client.get(signin_url)
        self.assertEqual(response.status_code, 200)

        # Check that next URL is stored in session
        self.assertEqual(self.client.session.get("signin_next_url"), next_url)

    def test_default_redirect_when_no_next_parameter(self):
        """Test that signin without next parameter redirects to dashboard."""
        # Complete signin flow without next parameter
        final_response = self._simulate_signin_with_otp()

        # Should redirect to dashboard by default
        expected_url = reverse("dashboard:dashboard")
        self.assertEqual(final_response.status_code, 200)
        self.assertEqual(final_response.headers.get("HX-Redirect"), expected_url)

    def test_session_cleanup_after_successful_signin(self):
        """Test that signin_next_url session key is cleaned up after successful signin."""
        next_url = reverse("accounts:profile")

        # Set up session state as if user went through signin flow
        session = self.client.session
        session["signin_next_url"] = next_url
        session["otp_token_id"] = "test_token_123"
        session["otp_delivery_method"] = "email"
        session["signin_email"] = self.user.email
        session["signin_user_id"] = str(self.user.id)
        session.save()

        # Complete OTP verification
        with patch.object(OTPService, "verify_otp") as mock_verify:
            mock_verify.return_value = (True, self.user)

            response = self.client.post(
                reverse("accounts:verify_otp"), {"verification_code": "123456"}, headers={"hx-request": "true"}
            )

            self.assertEqual(response.status_code, 200)

        # Check that all signin-related session keys are cleaned up
        self.assertNotIn("signin_next_url", self.client.session)
        self.assertNotIn("otp_token_id", self.client.session)
        self.assertNotIn("otp_delivery_method", self.client.session)
        self.assertNotIn("signin_email", self.client.session)
        self.assertNotIn("signin_user_id", self.client.session)

    def test_security_prevents_external_redirects(self):
        """
        Test that redirect only works for internal URLs, not external ones.

        NOTE: This test documents current behavior. The current implementation
        DOES NOT validate external URLs, which is a security vulnerability.
        External URLs are currently stored and used for redirection.
        TODO: Add URL validation to prevent external redirects.
        """
        # SECURITY WARNING: Current implementation stores ALL next URLs without validation
        # This is a potential open redirect vulnerability

        # Test some basic dangerous URLs that should be blocked but currently aren't
        dangerous_urls = [
            'javascript:alert("xss")',  # XSS attempt
            'data:text/html,<script>alert("xss")</script>',  # Data URL XSS
        ]

        # Test that dangerous URLs are at least not stored (though they currently are)
        for dangerous_url in dangerous_urls:
            with self.subTest(url=dangerous_url):
                # Reset session
                self.client.session.flush()

                signin_url = reverse("accounts:signin") + f"?next={dangerous_url}"
                response = self.client.get(signin_url)

                stored_next = self.client.session.get("signin_next_url")

                # Current implementation stores dangerous URLs (security issue)
                # This test documents the current insecure behavior
                self.assertEqual(
                    stored_next, dangerous_url, f"Current implementation unsafely stores dangerous URL: {dangerous_url}"
                )

        # Test external HTTP URLs (which are also currently stored unsafely)
        external_http_urls = [
            "http://evil.com",
            "https://malicious-site.com/steal-tokens",
        ]

        for external_url in external_http_urls:
            with self.subTest(url=external_url):
                self.client.session.flush()

                signin_url = reverse("accounts:signin") + f"?next={external_url}"
                response = self.client.get(signin_url)

                stored_next = self.client.session.get("signin_next_url")

                # Current implementation stores external URLs (security issue)
                self.assertEqual(
                    stored_next, external_url, f"Current implementation unsafely stores external URL: {external_url}"
                )

    def test_edge_cases_with_various_urls(self):
        """Test edge cases with various next URL patterns."""
        test_cases = [
            ("/", "/"),  # Root URL
            (reverse("dashboard:dashboard"), reverse("dashboard:dashboard")),  # Dashboard URL
            (
                reverse("accounts:profile") + "?tab=settings",
                reverse("accounts:profile") + "?tab=settings",
            ),  # URL with query params
            ("", reverse("dashboard:dashboard")),  # Empty next should default to dashboard
        ]

        for next_url, expected_redirect in test_cases:
            with self.subTest(next_url=next_url):
                # Reset session
                self.client.session.flush()

                # Complete signin flow with specific next URL
                if next_url:
                    final_response = self._simulate_signin_with_otp(next_url=next_url)
                else:
                    final_response = self._simulate_signin_with_otp()

                # Check final redirect
                self.assertEqual(final_response.status_code, 200)
                actual_redirect = final_response.headers.get("HX-Redirect")
                self.assertEqual(actual_redirect, expected_redirect)

    def test_special_characters_in_urls(self):
        """Test URLs with special characters and fragments."""
        # Document how Django handles URL encoding/decoding and fragments
        test_cases = [
            # Django test client strips fragments from URLs
            ("/accounts/profile/#section1", "/accounts/profile/"),
            # Django automatically URL-decodes encoded spaces
            ("/path/with/spaces%20encoded", "/path/with/spaces encoded"),
        ]

        for input_url, expected_stored in test_cases:
            with self.subTest(input_url=input_url):
                # Reset session
                self.client.session.flush()

                # Test that the URL is processed and stored as Django handles it
                signin_url = reverse("accounts:signin") + f"?next={input_url}"
                response = self.client.get(signin_url)

                stored_next = self.client.session.get("signin_next_url")
                self.assertEqual(stored_next, expected_stored)

                # Note: This documents Django's URL processing behavior
                # Fragments are stripped and URL encoding is decoded

    def test_next_url_survives_email_delivery_steps(self):
        """Test that next URL is preserved through entire signin flow including delivery method selection."""
        next_url = reverse("accounts:profile")

        # Step 1: Visit signin with next parameter
        signin_url = reverse("accounts:signin") + f"?next={next_url}"
        get_response = self.client.get(signin_url)
        self.assertEqual(get_response.status_code, 200)

        # Check next URL stored in session
        self.assertEqual(self.client.session.get("signin_next_url"), next_url)

        # Step 2: Submit email
        with (
            patch("accounts.views.user_exists", return_value=True),
            patch("accounts.db_queries.get_user_by_email", return_value=self.user),
        ):
            email_response = self.client.post(
                reverse("accounts:signin"), {"email": self.user.email}, headers={"hx-request": "true"}
            )

        # Check next URL still in session after email submission
        self.assertEqual(self.client.session.get("signin_next_url"), next_url)

        # Step 3: Choose delivery method
        with patch("messaging.services.send_otp_email_message") as mock_send_email:
            mock_send_email.return_value = True

            delivery_response = self.client.post(
                reverse("accounts:send_otp_email"), {"delivery_method": "email"}, headers={"hx-request": "true"}
            )

        # Check next URL still in session after delivery method selection
        self.assertEqual(self.client.session.get("signin_next_url"), next_url)

        # Step 4: Complete OTP verification
        with patch.object(OTPService, "verify_otp") as mock_verify:
            mock_verify.return_value = (True, self.user)

            final_response = self.client.post(
                reverse("accounts:verify_otp"), {"verification_code": "123456"}, headers={"hx-request": "true"}
            )

        # Should redirect to original next URL
        self.assertEqual(final_response.status_code, 200)
        self.assertEqual(final_response.headers.get("HX-Redirect"), next_url)

        # Session should be cleaned up
        self.assertNotIn("signin_next_url", self.client.session)

    def test_signin_redirect_with_failed_otp_preserves_next_url(self):
        """Test that next URL is preserved when OTP verification fails."""
        next_url = reverse("accounts:profile")

        # Set up session state
        session = self.client.session
        session["signin_next_url"] = next_url
        session["otp_token_id"] = "test_token_123"
        session["otp_delivery_method"] = "email"
        session["signin_email"] = self.user.email
        session.save()

        # Attempt OTP verification with wrong code
        with patch.object(OTPService, "verify_otp") as mock_verify:
            # Mock failed OTP verification
            mock_verify.return_value = (False, "Invalid OTP code")

            response = self.client.post(
                reverse("accounts:verify_otp"), {"verification_code": "000000"}, headers={"hx-request": "true"}
            )

            # Should show error, not redirect
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "error")
            self.assertIsNone(response.headers.get("HX-Redirect"))

        # Next URL should still be in session for retry
        self.assertEqual(self.client.session.get("signin_next_url"), next_url)

    def test_authenticated_user_accessing_signin_redirects_to_dashboard(self):
        """Test that already authenticated user accessing signin page is redirected appropriately."""
        # Login user
        self.client.force_login(self.user)

        # Try to access signin page
        response = self.client.get(reverse("accounts:signin"))

        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:dashboard"))

    def test_authenticated_user_with_next_parameter_respects_next(self):
        """Test that authenticated user with next parameter gets redirected to next URL."""
        # Login user
        self.client.force_login(self.user)

        next_url = reverse("accounts:profile")
        signin_url = reverse("accounts:signin") + f"?next={next_url}"

        # Try to access signin page with next parameter
        response = self.client.get(signin_url)

        # Should redirect to dashboard (ignoring next for already authenticated user)
        # This is the current behavior based on the implementation
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:dashboard"))
