"""
Tests specifically targeting GitHub issue #311 - "403 Forbidden" errors with email verification links.

This test module focuses on edge cases and specific conditions that could cause 403 errors
during email verification that aren't covered by the existing comprehensive test suite.

The existing tests in test_authentication_flows.py cover the basic regression, but this
module addresses production-specific scenarios that could still cause 403 errors.
"""

import logging
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.base import UpdateError
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from sesame.utils import get_query_string

from accounts.tests.test_base import BaseTestCase
from accounts.tests.test_utils import get_unique_email, get_unique_phone_number

User = get_user_model()


class EmailVerification403RegressionTest(BaseTestCase):
    """
    Focused tests for GitHub issue #311: "403 Forbidden" errors with email verification.

    These tests target specific edge cases that could cause 403 errors beyond the
    basic regression covered in test_authentication_flows.py.
    """

    def setUp(self):
        """Set up test user for email verification testing."""
        self.client = Client()
        self.user = User.objects.create_user(
            email=get_unique_email("verification_403"),
            name="403 Test User",
            phone_number=get_unique_phone_number(),
            password="testpass123",
        )
        # Ensure user starts unverified
        self.user.email_verified = False
        self.user.email_verified_at = None
        self.user.save()

    def test_email_verification_with_corrupted_session_no_403(self):
        """
        Test that email verification handles corrupted/stale sessions without 403 errors.

        This addresses a potential cause of 403 errors where users might have
        corrupted session data that interferes with the verification process.
        """
        # Generate valid magic link
        verification_params = get_query_string(self.user)
        magic_login_url = reverse("accounts:verify_email") + verification_params

        # Simulate a corrupted session by manually setting invalid session data
        session = self.client.session
        session["_auth_user_id"] = "999999"  # Non-existent user ID
        session["_auth_user_backend"] = "invalid.backend"
        session.save()

        # Attempt verification with corrupted session
        response = self.client.get(magic_login_url)

        # CRITICAL: Must not return 403 even with corrupted session
        self.assertNotEqual(
            response.status_code,
            403,
            "Email verification must not return 403 even with corrupted session data. "
            f"Got status {response.status_code}",
        )

        # Should still succeed (200 or 302)
        self.assertIn(
            response.status_code,
            [200, 302],
            f"Email verification should succeed with corrupted session. Got {response.status_code}",
        )

        # Verify user gets properly authenticated (session should be cleaned up)
        user_id = self.client.session.get("_auth_user_id")
        if user_id:  # If session is set
            self.assertEqual(int(user_id), self.user.id, "Session should be corrected to proper user")

    @patch("django.contrib.sessions.backends.base.SessionBase.save")
    def test_email_verification_with_session_save_failure_no_403(self, mock_session_save):
        """
        Test that session save failures during verification don't cause 403 errors.

        This tests the scenario where session storage issues might cause
        verification to fail with 403 instead of handling gracefully.
        """
        # Make session save fail
        mock_session_save.side_effect = UpdateError("Session storage failure")

        # Generate valid magic link
        verification_params = get_query_string(self.user)
        magic_login_url = reverse("accounts:verify_email") + verification_params

        # Attempt verification with session save failure
        response = self.client.get(magic_login_url)

        # CRITICAL: Must not return 403 even if session can't be saved
        self.assertNotEqual(
            response.status_code,
            403,
            f"Email verification must not return 403 due to session save failures. Got status {response.status_code}",
        )

        # Should return some form of success (200, 302) or graceful error (not 403)
        self.assertIn(
            response.status_code,
            [200, 302, 500],  # 500 is acceptable for infrastructure failure
            f"Email verification should handle session failures gracefully. Got {response.status_code}",
        )

        # Even if session saving failed, the user should still be authenticated in the current request
        if hasattr(response, "wsgi_request") and hasattr(response.wsgi_request, "user"):
            self.assertTrue(
                response.wsgi_request.user.is_authenticated,
                "User should still be authenticated even if session save fails",
            )

    def test_email_verification_post_request_no_csrf_403(self):
        """
        Test that POST requests to email verification endpoint handle CSRF properly.

        This tests the scenario where users might accidentally POST to the verification
        endpoint instead of GET, which could trigger CSRF protection and cause 403.
        """
        # Generate valid magic link
        verification_params = get_query_string(self.user)
        magic_login_url = reverse("accounts:verify_email") + verification_params

        # Try POST instead of GET (could happen with form submissions or redirects)
        response = self.client.post(magic_login_url)

        # CRITICAL: Must not return 403 due to CSRF issues
        # POST might not be the intended method, but it shouldn't cause 403
        self.assertNotEqual(
            response.status_code,
            403,
            f"POST requests to email verification should not cause 403 CSRF errors. Got status {response.status_code}",
        )

        # Should either succeed or return method not allowed (405), but not 403
        self.assertIn(
            response.status_code,
            [200, 302, 405],  # 405 Method Not Allowed is acceptable
            f"POST to email verification should handle gracefully. Got {response.status_code}",
        )

    def test_email_verification_with_middleware_interference_no_403(self):
        """
        Test that custom middleware doesn't interfere with email verification causing 403.

        This simulates potential middleware that might interfere with the verification
        process and cause unexpected 403 responses.
        """
        # Generate valid magic link
        verification_params = get_query_string(self.user)
        magic_login_url = reverse("accounts:verify_email") + verification_params

        # Add custom headers that might interfere with middleware
        response = self.client.get(
            magic_login_url,
            headers={"x-forwarded-for": "192.168.1.1", "x-real-ip": "192.168.1.1", "user-agent": "TestBot/1.0"},
        )

        # CRITICAL: Must not return 403 regardless of headers/middleware
        self.assertNotEqual(
            response.status_code,
            403,
            f"Email verification must not return 403 due to middleware interference. Got status {response.status_code}",
        )

        # Should succeed normally
        self.assertIn(
            response.status_code,
            [200, 302],
            f"Email verification should work with custom headers. Got {response.status_code}",
        )

    def test_email_verification_template_rendering_no_403(self):
        """
        Test that template rendering issues don't cause 403 errors during verification.

        This ensures that if there are template issues, they result in proper
        error handling rather than 403 Forbidden responses.
        """
        # Generate valid magic link
        verification_params = get_query_string(self.user)
        magic_login_url = reverse("accounts:verify_email") + verification_params

        # Temporarily break the template path to simulate rendering issues
        with override_settings(
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": ["/nonexistent/path"],  # This will cause template loading issues
                    "APP_DIRS": True,
                    "OPTIONS": {
                        "context_processors": [
                            "django.template.context_processors.debug",
                            "django.template.context_processors.request",
                            "django.contrib.auth.context_processors.auth",
                            "django.contrib.messages.context_processors.messages",
                        ],
                    },
                }
            ]
        ):
            response = self.client.get(magic_login_url)

            # CRITICAL: Template issues should not cause 403
            self.assertNotEqual(
                response.status_code,
                403,
                f"Template rendering issues must not cause 403 errors. Got status {response.status_code}",
            )

            # Should return 500 (server error) or redirect, but not 403
            self.assertIn(
                response.status_code,
                [200, 302, 500],  # 500 is acceptable for template issues
                f"Template issues should be handled gracefully. Got {response.status_code}",
            )

    def test_email_verification_with_expired_token_no_403(self):
        """
        Test that expired/invalid sesame tokens return appropriate errors, not 403.

        This addresses the scenario where users might click old verification links
        that have expired, which could cause 403 errors in certain conditions.
        """
        # Use an invalid/expired token format
        expired_token = "?sesame=expired_or_tampered_token_12345"
        magic_login_url = reverse("accounts:verify_email") + expired_token

        # Attempt verification with expired token
        response = self.client.get(magic_login_url)

        # CRITICAL: Invalid tokens should not cause 403 errors
        # They should either redirect to signin or show appropriate error
        self.assertNotEqual(
            response.status_code,
            403,
            f"Expired/invalid tokens must not return 403 errors. Got status {response.status_code}",
        )

        # Should redirect to signin page (302) instead of 403
        self.assertEqual(
            response.status_code,
            302,
            f"Invalid tokens should redirect to signin, not return error codes. Got {response.status_code}",
        )

        # Should redirect to signin page
        self.assertRedirects(response, reverse("accounts:signin"), fetch_redirect_response=False)

        # User should NOT be authenticated with invalid token
        user_id = self.client.session.get("_auth_user_id")
        self.assertIsNone(user_id, "Invalid tokens must not authenticate users")

    def test_email_verification_production_scenario_no_403(self):
        """
        Test email verification under production-like conditions to catch 403 errors.

        This test simulates more realistic production conditions that might trigger
        the 403 error reported in GitHub issue #311.
        """
        # Generate valid magic link
        verification_params = get_query_string(self.user)
        magic_login_url = reverse("accounts:verify_email") + verification_params

        # Simulate production-like conditions with various headers and session state
        headers = {
            "HTTP_USER_AGENT": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
            "HTTP_ACCEPT": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "HTTP_ACCEPT_LANGUAGE": "pt-PT,pt;q=0.9,en;q=0.8",
            "HTTP_ACCEPT_ENCODING": "gzip, deflate, br",
            "HTTP_DNT": "1",
            "HTTP_CONNECTION": "keep-alive",
            "HTTP_UPGRADE_INSECURE_REQUESTS": "1",
        }

        # Test with fresh session (common in production when clicking email links)
        fresh_client = Client()
        response = fresh_client.get(magic_login_url, **headers)

        # CRITICAL: Must not return 403 in production-like conditions
        self.assertNotEqual(
            response.status_code,
            403,
            f"Production-like email verification must not return 403. "
            f"Got status {response.status_code}. This might be the issue #311 bug.",
        )

        # Should succeed with proper response
        self.assertIn(
            response.status_code,
            [200, 302],
            f"Production email verification should succeed. Got {response.status_code}",
        )

        # Verify user gets authenticated
        if response.status_code == 200:
            # If returning HTML template, user should be authenticated
            user_id = fresh_client.session.get("_auth_user_id")
            self.assertIsNotNone(user_id, "User should be authenticated after verification")
            self.assertEqual(int(user_id), self.user.id, "Correct user should be authenticated")
