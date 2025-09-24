"""
Integration tests for session persistence in OTP signin flow.

Tests cover the critical bug fix where users were successfully verifying OTP
but getting redirected back to signin due to unverified session markers not
being cleaned up in VerifyOTPView.

The bug fix ensures that after successful OTP verification:
1. Unverified user session markers are cleaned up
2. Session expiry is reset to default
3. User can reach the dashboard without redirect loops
4. ProgressiveVerificationMiddleware works correctly

These tests prevent regression of the session persistence bug.
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import School, SchoolMembership, SchoolRole
from accounts.services.otp_service import OTPService

User = get_user_model()


class SessionPersistenceSigninTest(TestCase):
    """Test session persistence in OTP signin flow with comprehensive coverage."""

    def setUp(self):
        """Set up test data for session persistence tests."""
        # Create test user with verified email for OTP
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

        self.dashboard_url = "/dashboard/"
        self.signin_url = reverse("accounts:signin")
        self.send_otp_url = reverse("accounts:send_otp_email")
        self.verify_otp_url = reverse("accounts:verify_otp")

    def _simulate_complete_otp_signin(self, with_unverified_markers=False):
        """
        Helper method to simulate complete OTP signin flow.

        Args:
            with_unverified_markers: If True, adds unverified session markers

        Returns:
            Final response from OTP verification
        """
        # Set up unverified session markers if requested (simulates signup flow)
        if with_unverified_markers:
            session = self.client.session
            session["is_unverified_user"] = True
            session["unverified_until"] = (timezone.now() + timedelta(hours=12)).timestamp()
            session.save()

        # Step 1: GET signin page
        get_response = self.client.get(self.signin_url)
        self.assertEqual(get_response.status_code, 200)

        # Step 2: POST email to signin form
        with (
            patch("accounts.views.user_exists", return_value=True),
            patch("accounts.db_queries.get_user_by_email", return_value=self.user),
        ):
            email_response = self.client.post(
                self.signin_url, {"email": self.user.email}, headers={"hx-request": "true"}
            )
            # Should show delivery options
            self.assertIn(email_response.status_code, [200, 302])

        # Step 3: Choose email delivery method and send OTP
        with patch("messaging.services.send_otp_email_message") as mock_send_email:
            mock_send_email.return_value = {"success": True}

            delivery_response = self.client.post(
                self.send_otp_url, {"email": self.user.email}, headers={"hx-request": "true"}
            )
            self.assertEqual(delivery_response.status_code, 200)

        # Step 4: Verify OTP (this is where the bug fix is applied)
        with patch.object(OTPService, "verify_otp") as mock_verify:
            # Mock successful OTP verification - returns (success, user)
            mock_verify.return_value = (True, self.user)

            otp_response = self.client.post(
                self.verify_otp_url, {"verification_code": "123456"}, headers={"hx-request": "true"}
            )

            return otp_response

    def test_successful_otp_signin_reaches_dashboard(self):
        """
        Test that complete OTP signin flow works end-to-end without redirect loops.

        This test verifies the bug fix works correctly:
        1. User can complete OTP signin flow
        2. Session markers are cleaned up
        3. User can reach dashboard after signin
        4. No redirect loops occur
        """
        # Simulate complete OTP signin with unverified markers (like after signup)
        otp_response = self._simulate_complete_otp_signin(with_unverified_markers=True)

        # Assert OTP verification succeeded
        self.assertEqual(otp_response.status_code, 200)

        # Assert user is now authenticated
        self.assertTrue(otp_response.wsgi_request.user.is_authenticated)
        self.assertEqual(otp_response.wsgi_request.user.id, self.user.id)

        # Assert HX-Redirect header points to dashboard
        self.assertEqual(otp_response.get("HX-Redirect"), self.dashboard_url)

        # CRITICAL: Follow the redirect and verify user can reach dashboard
        # This is where the bug would manifest - user would be redirected back to signin
        dashboard_response = self.client.get(self.dashboard_url)
        self.assertEqual(dashboard_response.status_code, 200)

        # Verify user is still authenticated after reaching dashboard
        self.assertTrue(dashboard_response.wsgi_request.user.is_authenticated)

        # Assert session cleanup occurred - no unverified markers remain
        session = self.client.session
        self.assertNotIn("is_unverified_user", session)
        self.assertNotIn("unverified_until", session)

        # OTP-specific session data should also be cleaned up
        self.assertNotIn("otp_token_id", session)
        self.assertNotIn("signin_email", session)

    def test_otp_signin_cleans_up_unverified_session_markers(self):
        """
        Test that OTP signin properly cleans up unverified session markers.

        This test specifically verifies the session cleanup in VerifyOTPView:
        1. Unverified session markers are present before verification
        2. All markers are removed after successful OTP verification
        3. Session expiry is reset appropriately
        """
        # Manually set up unverified session markers (simulating signup flow)
        session = self.client.session
        session["is_unverified_user"] = True
        session["unverified_until"] = (timezone.now() + timedelta(hours=12)).timestamp()
        session["signin_email"] = self.user.email
        session.save()

        # Verify markers are present before OTP flow
        session = self.client.session
        self.assertIn("is_unverified_user", session)
        self.assertIn("unverified_until", session)
        self.assertTrue(session["is_unverified_user"])

        # Complete OTP signin flow
        otp_response = self._simulate_complete_otp_signin(with_unverified_markers=False)

        # Assert OTP verification succeeded
        self.assertEqual(otp_response.status_code, 200)
        self.assertTrue(otp_response.wsgi_request.user.is_authenticated)

        # CRITICAL ASSERTIONS: Verify session markers are cleaned up
        session = self.client.session

        # Unverified user markers should be removed (this was the bug)
        self.assertNotIn("is_unverified_user", session)
        self.assertNotIn("unverified_until", session)

        # OTP-specific markers should also be removed
        self.assertNotIn("otp_token_id", session)
        self.assertNotIn("signin_email", session)

        # Signin-specific markers should be cleaned up
        self.assertNotIn("signin_user_id", session)
        self.assertNotIn("signin_next_url", session)

        # Verify user can access protected pages without being logged out
        dashboard_response = self.client.get(self.dashboard_url)
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertTrue(dashboard_response.wsgi_request.user.is_authenticated)

    def test_session_expiry_is_reset_after_otp_verification(self):
        """
        Test that session expiry is properly reset after successful OTP verification.

        This test ensures that the session expiry is reset to default Django
        session length after successful OTP verification, preventing premature
        session expiration.
        """
        # Set up session with short expiry and unverified markers
        session = self.client.session
        session["is_unverified_user"] = True
        session["unverified_until"] = (timezone.now() + timedelta(hours=1)).timestamp()
        session.set_expiry(300)  # 5 minutes
        session.save()

        original_expiry = session.get_expiry_age()
        self.assertEqual(original_expiry, 300)

        # Complete OTP signin flow
        otp_response = self._simulate_complete_otp_signin(with_unverified_markers=False)

        # Assert OTP verification succeeded
        self.assertEqual(otp_response.status_code, 200)

        # Check that session expiry was reset (0 means use default session timeout)
        session = self.client.session
        new_expiry = session.get_expiry_age()

        # Should be much longer than the 5 minutes we set (default is typically 1209600 seconds = 2 weeks)
        self.assertGreater(new_expiry, 3600)  # Should be at least 1 hour (default is much more)

        # Verify session cleanup occurred
        self.assertNotIn("is_unverified_user", session)
        self.assertNotIn("unverified_until", session)

    def test_progressive_verification_middleware_respects_cleanup(self):
        """
        Test that ProgressiveVerificationMiddleware works correctly after session cleanup.

        This test verifies the interaction between VerifyOTPView cleanup and
        ProgressiveVerificationMiddleware to ensure users aren't logged out
        after successful OTP verification.
        """
        # Set up expired unverified session markers (this would trigger middleware logout)
        session = self.client.session
        session["is_unverified_user"] = True
        # Set expiry in the past to trigger middleware logout
        session["unverified_until"] = (timezone.now() - timedelta(minutes=1)).timestamp()
        session.save()

        # Before OTP verification, user should be logged out by middleware
        # (if they were authenticated and tried to access protected page)

        # Complete OTP signin flow (this should clean up the markers)
        otp_response = self._simulate_complete_otp_signin(with_unverified_markers=False)

        # Assert OTP verification succeeded
        self.assertEqual(otp_response.status_code, 200)
        self.assertTrue(otp_response.wsgi_request.user.is_authenticated)

        # CRITICAL: Access dashboard - middleware should not log user out
        # because unverified_until marker was cleaned up
        dashboard_response = self.client.get(self.dashboard_url)
        self.assertEqual(dashboard_response.status_code, 200)

        # User should still be authenticated (not logged out by middleware)
        self.assertTrue(dashboard_response.wsgi_request.user.is_authenticated)
        self.assertEqual(dashboard_response.wsgi_request.user.id, self.user.id)

        # Verify session is clean
        session = self.client.session
        self.assertNotIn("is_unverified_user", session)
        self.assertNotIn("unverified_until", session)
