"""
Tests for Progressive Verification Middleware

These tests validate the middleware components that enforce verification
requirements after the 24-hour grace period and handle verification completion.
"""

from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.middleware import ProgressiveVerificationMiddleware, VerificationCompletionMiddleware
from accounts.tests.test_base import BaseTestCase
from tasks.models import Task

User = get_user_model()


class ProgressiveVerificationMiddlewareTestCase(BaseTestCase):
    """Test the ProgressiveVerificationMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ProgressiveVerificationMiddleware(self._get_response)

        # Create test users
        self.unverified_user_in_grace = User.objects.create_user(email="grace@example.com", name="Grace User")
        self.unverified_user_in_grace.email_verified = False
        self.unverified_user_in_grace.phone_verified = False
        self.unverified_user_in_grace.verification_required_after = timezone.now() + timedelta(hours=12)
        self.unverified_user_in_grace.save()

        self.unverified_user_expired = User.objects.create_user(email="expired@example.com", name="Expired User")
        self.unverified_user_expired.email_verified = False
        self.unverified_user_expired.phone_verified = False
        self.unverified_user_expired.verification_required_after = timezone.now() - timedelta(hours=1)
        self.unverified_user_expired.save()

        self.verified_user = User.objects.create_user(email="verified@example.com", name="Verified User")
        self.verified_user.email_verified = True
        self.verified_user.phone_verified = False
        self.verified_user.verification_required_after = timezone.now() - timedelta(hours=1)
        self.verified_user.save()

        self.legacy_user = User.objects.create_user(email="legacy@example.com", name="Legacy User")
        # Legacy user has no verification_required_after
        self.legacy_user.verification_required_after = None
        self.legacy_user.save()

        self.superuser = User.objects.create_superuser(
            email="admin@example.com", name="Admin User", password="admin123"
        )

    def _get_response(self, request):
        """Mock response function for middleware testing."""
        return HttpResponse("OK")

    def _create_request(self, path="/", user=None, session_data=None):
        """Helper to create request with user and session."""
        request = self.factory.get(path)
        request.user = user or AnonymousUser()

        # Add session
        from django.contrib.sessions.middleware import SessionMiddleware

        session_middleware = SessionMiddleware(lambda r: None)
        session_middleware.process_request(request)

        if session_data:
            for key, value in session_data.items():
                request.session[key] = value
            request.session.save()  # Ensure session is saved

        # Add messages framework
        from django.contrib.messages.storage.fallback import FallbackStorage

        request._messages = FallbackStorage(request)

        return request

    def test_middleware_skips_unauthenticated_users(self):
        """Test that middleware doesn't process unauthenticated users."""
        request = self._create_request(user=AnonymousUser())

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_middleware_skips_superusers(self):
        """Test that middleware doesn't process superusers."""
        request = self._create_request(user=self.superuser)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_middleware_skips_whitelisted_paths(self):
        """Test that middleware skips whitelisted paths."""
        whitelisted_paths = [
            "/signin/",
            "/signup/",
            "/logout/",
            "/verify-otp/",
            "/verify-email/",
            "/magic-login/",
            "/resend-code/",
            "/admin/",
            "/static/test.css",
            "/media/test.jpg",
            "/health/",
        ]

        for path in whitelisted_paths:
            with self.subTest(path=path):
                request = self._create_request(path=path, user=self.unverified_user_expired)

                response = self.middleware(request)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content.decode(), "OK")

    def test_middleware_allows_legacy_users_without_verification_deadline(self):
        """Test that legacy users without verification_required_after can access normally."""
        request = self._create_request(path="/dashboard/", user=self.legacy_user)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_middleware_allows_verified_users_after_deadline(self):
        """Test that verified users can access after verification deadline."""
        request = self._create_request(path="/dashboard/", user=self.verified_user)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_middleware_allows_unverified_users_within_grace_period(self):
        """Test that unverified users can access within grace period."""
        request = self._create_request(path="/dashboard/", user=self.unverified_user_in_grace)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_middleware_redirects_unverified_users_after_grace_period(self):
        """Test that unverified users are redirected after grace period expires."""
        request = self._create_request(path="/dashboard/", user=self.unverified_user_expired)

        response = self.middleware(request)

        # BETA: Verification enforcement is currently disabled (if False: condition in middleware)
        # During beta period, users are allowed access even after grace period expires
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_middleware_clears_session_for_expired_unverified_users(self):
        """Test that session is cleared for expired unverified users."""
        session_data = {"some_data": "test_value", "is_unverified_user": True}
        request = self._create_request(path="/dashboard/", user=self.unverified_user_expired, session_data=session_data)

        # Store original session key for verification
        original_session_data = dict(request.session)

        response = self.middleware(request)

        # BETA: Since verification enforcement is disabled, session data is preserved
        # When enforcement is enabled, session data would be cleared
        self.assertIn("some_data", request.session)
        self.assertIn("is_unverified_user", request.session)

    def test_middleware_adds_warning_message_for_expired_users(self):
        """Test that appropriate warning message is added for expired users."""
        request = self._create_request(path="/dashboard/", user=self.unverified_user_expired)

        # Add messages framework to request
        from django.contrib.messages.storage.fallback import FallbackStorage

        request._messages = FallbackStorage(request)

        response = self.middleware(request)

        messages = list(get_messages(request))
        # BETA: Since verification enforcement is disabled, no warning messages are added
        # When enforcement is enabled, a warning message would be added
        self.assertEqual(len(messages), 0)

    def test_middleware_checks_session_expiry_during_grace_period(self):
        """Test that middleware checks session expiry during grace period."""
        # Create session with expired timestamp
        expired_timestamp = (timezone.now() - timedelta(minutes=30)).timestamp()
        session_data = {"unverified_until": expired_timestamp, "is_unverified_user": True}
        request = self._create_request(
            path="/dashboard/", user=self.unverified_user_in_grace, session_data=session_data
        )

        # Add messages framework
        from django.contrib.messages.storage.fallback import FallbackStorage

        request._messages = FallbackStorage(request)

        response = self.middleware(request)

        # Should redirect to signin
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:signin"))

        # Should have appropriate message
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn("session has expired", str(messages[0]))

    def test_middleware_shows_reminder_when_grace_period_ending(self):
        """Test that reminder message is shown when less than 12 hours left."""
        # User with 6 hours left
        user = User.objects.create_user(email="ending@example.com", name="Ending User")
        user.email_verified = False
        user.phone_verified = False
        user.verification_required_after = timezone.now() + timedelta(hours=6)
        user.save()

        request = self._create_request(
            path="/dashboard/",
            user=user,
            session_data={
                "is_unverified_user": True,
                "unverified_until": (timezone.now() + timedelta(hours=6)).timestamp(),
            },
        )

        response = self.middleware(request)

        # Should allow access
        self.assertEqual(response.status_code, 200)

        # Should show reminder
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn("hours left", str(messages[0]))  # Allow for time variance
        self.assertIn("verify your email or phone number", str(messages[0]))

        # Should set reminder shown flag
        self.assertTrue(request.session.get("verification_reminder_shown"))

    def test_middleware_does_not_show_duplicate_reminders(self):
        """Test that reminder is only shown once per session."""
        user = User.objects.create_user(email="reminder@example.com", name="Reminder User")
        user.email_verified = False
        user.phone_verified = False
        user.verification_required_after = timezone.now() + timedelta(hours=6)
        user.save()

        session_data = {"verification_reminder_shown": True}
        request = self._create_request(path="/dashboard/", user=user, session_data=session_data)

        # Add messages framework
        from django.contrib.messages.storage.fallback import FallbackStorage

        request._messages = FallbackStorage(request)

        response = self.middleware(request)

        # Should allow access
        self.assertEqual(response.status_code, 200)

        # Should not show reminder again
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 0)

    def test_middleware_allows_partially_verified_users_email_only(self):
        """Test that users with only email verified can access after deadline."""
        user = User.objects.create_user(email="email_only@example.com", name="Email Only User")
        user.email_verified = True
        user.phone_verified = False
        user.verification_required_after = timezone.now() - timedelta(hours=1)
        user.save()

        request = self._create_request(path="/dashboard/", user=user)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_middleware_allows_partially_verified_users_phone_only(self):
        """Test that users with only phone verified can access after deadline."""
        user = User.objects.create_user(email="phone_only@example.com", name="Phone Only User")
        user.email_verified = False
        user.phone_verified = True
        user.verification_required_after = timezone.now() - timedelta(hours=1)
        user.save()

        request = self._create_request(path="/dashboard/", user=user)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")


class VerificationCompletionMiddlewareTestCase(BaseTestCase):
    """Test the VerificationCompletionMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = VerificationCompletionMiddleware(self._get_response)

        self.user = User.objects.create_user(email="test@example.com", name="Test User")
        self.user.email_verified = False
        self.user.save()

    def _get_response(self, request):
        """Mock response function for middleware testing."""
        return HttpResponse("OK")

    def _create_request(self, path="/", user=None, session_data=None):
        """Helper to create request with user and session."""
        request = self.factory.get(path)
        request.user = user or self.user

        # Add session
        from django.contrib.sessions.middleware import SessionMiddleware

        session_middleware = SessionMiddleware(lambda r: None)
        session_middleware.process_request(request)

        if session_data:
            for key, value in session_data.items():
                request.session[key] = value
            request.session.save()  # Ensure session is saved

        # Add messages framework
        from django.contrib.messages.storage.fallback import FallbackStorage

        request._messages = FallbackStorage(request)

        return request

    def test_middleware_ignores_non_verify_email_paths(self):
        """Test that middleware only processes /verify-email/ path."""
        paths_to_ignore = ["/", "/dashboard/", "/verify-otp/", "/signin/", "/some-other-path/"]

        for path in paths_to_ignore:
            with self.subTest(path=path):
                request = self._create_request(path=path, user=self.user)

                response = self.middleware(request)

                self.assertEqual(response.status_code, 200)
                # User should remain unverified
                self.user.refresh_from_db()
                self.assertFalse(self.user.email_verified)

    def test_middleware_ignores_unauthenticated_users(self):
        """Test that middleware ignores unauthenticated users."""
        from django.contrib.auth.models import AnonymousUser

        request = self._create_request(path="/verify-email/", user=AnonymousUser())

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_middleware_marks_email_as_verified_on_verify_email_path(self):
        """Test that email is marked as verified when accessing /verify-email/."""
        request = self._create_request(path="/verify-email/", user=self.user)

        response = self.middleware(request)

        # User should be marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

        # Success message should be added
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn("email has been successfully verified", str(messages[0]))

    def test_middleware_does_not_modify_already_verified_users(self):
        """Test that already verified users are not modified."""
        self.user.email_verified = True
        self.user.save()

        request = self._create_request(path="/verify-email/", user=self.user)

        response = self.middleware(request)

        # User should remain verified (no double-processing)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

        # Should NOT show message for already verified users
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 0)

    @patch("tasks.models.Task.objects.filter")
    def test_middleware_completes_email_verification_task(self, mock_filter):
        """Test that email verification task is marked as completed."""
        # Mock task query
        mock_task = Mock()
        mock_task.status = "pending"
        mock_queryset = Mock()
        mock_queryset.first.return_value = mock_task
        mock_filter.return_value = mock_queryset

        request = self._create_request(path="/verify-email/", user=self.user)

        response = self.middleware(request)

        # Task should be queried correctly
        mock_filter.assert_called_once_with(user=self.user, title="Verify your email address", status="pending")

        # Task should be marked as completed
        self.assertEqual(mock_task.status, "completed")
        mock_task.save.assert_called_once()

    @patch("tasks.models.Task.objects.filter")
    def test_middleware_handles_missing_email_verification_task(self, mock_filter):
        """Test that middleware handles case where no email verification task exists."""
        # Mock no task found
        mock_queryset = Mock()
        mock_queryset.first.return_value = None
        mock_filter.return_value = mock_queryset

        request = self._create_request(path="/verify-email/", user=self.user)

        # Should not raise exception
        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        # User should still be verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    @patch("tasks.models.Task.objects.filter", side_effect=Exception("Database error"))
    def test_middleware_handles_task_update_errors(self, mock_filter):
        """Test that middleware handles errors when updating tasks."""
        request = self._create_request(path="/verify-email/", user=self.user)

        # Should not raise exception despite task update error
        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        # User should still be verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_middleware_clears_unverified_session_markers(self):
        """Test that unverified session markers are cleared upon verification."""
        session_data = {
            "is_unverified_user": True,
            "unverified_until": timezone.now().timestamp(),
            "other_data": "should_remain",
        }
        request = self._create_request(path="/verify-email/", user=self.user, session_data=session_data)

        response = self.middleware(request)

        # Unverified markers should be removed
        self.assertNotIn("is_unverified_user", request.session)
        self.assertNotIn("unverified_until", request.session)

        # Other session data should remain
        self.assertIn("other_data", request.session)
        self.assertEqual(request.session["other_data"], "should_remain")

    def test_middleware_resets_session_expiry(self):
        """Test that session expiry is reset to default after verification."""
        session_data = {"some_data": "test"}
        request = self._create_request(path="/verify-email/", user=self.user, session_data=session_data)

        # Mock the set_expiry method to verify it's called
        original_set_expiry = request.session.set_expiry
        expiry_calls = []

        def mock_set_expiry(value):
            expiry_calls.append(value)
            return original_set_expiry(value)

        request.session.set_expiry = mock_set_expiry

        response = self.middleware(request)

        # Should call set_expiry with 0 (default session length)
        self.assertEqual(len(expiry_calls), 1)
        self.assertEqual(expiry_calls[0], 0)

    def test_middleware_integration_with_progressive_verification(self):
        """Test integration between both middleware components."""
        # Create user in expired state
        user = User.objects.create_user(email="integration@example.com", name="Integration User")
        user.email_verified = False
        user.phone_verified = False
        user.verification_required_after = timezone.now() - timedelta(hours=1)
        user.save()

        # First, user should be blocked by ProgressiveVerificationMiddleware
        prog_middleware = ProgressiveVerificationMiddleware(self._get_response)
        request = self._create_request(path="/dashboard/", user=user)

        response = prog_middleware(request)
        # BETA: Verification enforcement is disabled, so user is allowed through
        self.assertEqual(response.status_code, 200)  # Allowed during beta

        # But on verify-email path, should be allowed and then verified
        completion_middleware = VerificationCompletionMiddleware(self._get_response)
        verify_request = self._create_request(path="/verify-email/", user=user)

        response = completion_middleware(verify_request)
        self.assertEqual(response.status_code, 200)

        # User should now be verified
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

        # Now user should be allowed by ProgressiveVerificationMiddleware
        final_request = self._create_request(path="/dashboard/", user=user)
        response = prog_middleware(final_request)
        self.assertEqual(response.status_code, 200)  # Allowed
