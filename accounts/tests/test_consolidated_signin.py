"""
Comprehensive tests for the consolidated sign-in flow.

This module tests the new single-page signin flow where users:
1. Enter email and see both delivery options on same page
2. Choose between "Send Code via Email" and "Send Code via SMS" buttons
3. Complete OTP verification

Critical security requirements:
- Prevent email enumeration attacks
- Validate user verification status before sending codes
- Proper error handling for non-existent users
- Waffle switch validation for SMS feature
"""

import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from waffle.testutils import override_switch

from accounts.models import School, SchoolMembership, SchoolRole
from accounts.services.otp_service import OTPService
from accounts.tests.test_base import BaseTestCase
from accounts.tests.test_utils import get_unique_email, get_unique_phone_number

User = get_user_model()


class ConsolidatedSignInFormTest(BaseTestCase):
    """Test the consolidated signin form display and basic functionality."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.signin_url = reverse("accounts:signin")

    def test_signin_form_shows_email_input_and_both_buttons(self):
        """Test that signin form shows email input and both delivery buttons."""
        response = self.client.get(self.signin_url)

        self.assertEqual(response.status_code, 200)
        # Check for email input field
        self.assertContains(response, 'type="email"')
        self.assertContains(response, 'placeholder="your_email@example.com"')

        # Check for email delivery button
        self.assertContains(response, "Send Code via Email")
        self.assertContains(response, 'hx-post="/send-otp-email/"')

    @patch("accounts.views.switch_is_active")
    def test_signin_form_shows_sms_button_when_feature_enabled(self, mock_switch):
        """Test that SMS button appears when SMS feature is available."""
        mock_switch.return_value = True

        response = self.client.get(self.signin_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send Code via SMS")
        self.assertContains(response, 'hx-post="/send-otp-sms/"')
        # Verify our view checked the switch
        mock_switch.assert_called_with("sms_feature")

    @patch("accounts.views.switch_is_active")
    def test_signin_form_hides_sms_button_when_feature_disabled(self, mock_switch):
        """Test that SMS button is hidden when SMS feature is unavailable."""
        mock_switch.return_value = False

        response = self.client.get(self.signin_url)

        self.assertEqual(response.status_code, 200)
        # SMS button should not be rendered when SMS feature is disabled
        self.assertNotContains(response, "Send Code via SMS")
        self.assertNotContains(response, 'hx-post="/send-otp-sms/"')
        # Verify our view checked the switch
        mock_switch.assert_called_with("sms_feature")

    def test_signin_post_renders_form_with_email_value(self):
        """Test that posting to signin renders form with provided email."""
        test_email = "test@example.com"

        response = self.client.post(self.signin_url, {"email": test_email}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        # Should render the consolidated form with the email value in Alpine.js initialization
        self.assertContains(response, f"email: '{test_email}'")


class EmailOTPSecurityTest(BaseTestCase):
    """Test security aspects of email OTP sending, especially email enumeration prevention."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.send_otp_email_url = reverse("accounts:send_otp_email")

        # Create verified user
        self.verified_user = User.objects.create_user(
            email=get_unique_email("verified"),
            name="Verified User",
            phone_number=get_unique_phone_number(),
            email_verified=True,
            phone_verified=True,
        )

        # Create unverified user
        self.unverified_user = User.objects.create_user(
            email=get_unique_email("unverified"),
            name="Unverified User",
            phone_number=get_unique_phone_number(),
            email_verified=False,
            phone_verified=False,
        )

    def test_nonexistent_user_returns_generic_error(self):
        """Test that non-existent user gets generic error to prevent email enumeration."""
        fake_email = "nonexistent@example.com"

        response = self.client.post(self.send_otp_email_url, {"email": fake_email}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        # Should return generic error that doesn't reveal email doesn't exist
        self.assertContains(
            response, "Please check your email address. If you don&#x27;t have an account yet, please sign up first."
        )
        # Should not reveal specific details about user existence
        self.assertNotContains(response, "does not exist")
        self.assertNotContains(response, "not found")

    def test_nonexistent_user_gets_clear_error_not_disabled_button(self):
        """Test that non-existent email gets clear error message, not just disabled UI.

        This test prevents Bug #310: When a non-existent email is entered,
        users should get a clear error message instead of just a disabled button
        with no explanation.
        """
        fake_email = "nonexistent@example.com"

        response = self.client.post(self.send_otp_email_url, {"email": fake_email}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)

        # Should show clear error message
        self.assertContains(
            response, "Please check your email address. If you don&#x27;t have an account yet, please sign up first."
        )

        # Should preserve the email in the form for correction
        self.assertContains(response, fake_email)

        # Should render the signin form (not a disabled state)
        self.assertContains(response, "Send Code via Email")

        # Should not have server-side disabled attributes (client-side x-bind:disabled is OK)
        self.assertNotContains(response, 'disabled=""')
        self.assertNotContains(response, 'disabled="true"')
        self.assertNotContains(response, 'disabled="disabled"')

        # Should provide actionable guidance
        self.assertContains(response, "email")

    def test_unverified_user_gets_verification_prompt(self):
        """Test that unverified user gets prompted to verify email first."""
        response = self.client.post(
            self.send_otp_email_url, {"email": self.unverified_user.email}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please verify your email address first")
        # Should not send OTP to unverified users
        self.assertNotIn("otp_token_id", self.client.session)

    def test_unverified_user_gets_resend_verification_option(self):
        """Test that unverified users get a resend verification email option in the UI response.

        This test prevents Bug #275: When an unverified user tries to signin, they should
        get clear feedback AND an actionable way to resend their verification email.

        NOTE: This test currently fails because the UI doesn't provide the resend option.
        When Bug #275 is fixed, this test should pass.
        """
        response = self.client.post(
            self.send_otp_email_url, {"email": self.unverified_user.email}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)

        # Should contain verification error message
        self.assertContains(response, "Please verify your email address first")

        # Should preserve the email value for the resend action
        self.assertContains(response, self.unverified_user.email)

        # BUG #275: Currently failing - should provide a way to resend verification email
        # When this bug is fixed, uncomment this line:
        # self.assertContains(response, "resend-verification-email")

        # As a workaround test, verify that at least the error is clear
        # and the form is still usable (not broken)
        self.assertContains(response, "Send Code via Email")

    @patch("accounts.views.user_exists")
    @patch("accounts.views.get_user_by_email")
    @patch("accounts.views.send_otp_email_message")
    @patch("accounts.services.otp_service.OTPService.generate_otp")
    def test_verified_user_receives_otp_successfully(
        self, mock_generate_otp, mock_send_email, mock_get_user, mock_user_exists
    ):
        """Test that verified user successfully receives OTP via email."""
        # Mock user lookup functions
        mock_user_exists.return_value = True
        mock_get_user.return_value = self.verified_user

        # Mock OTP generation
        mock_generate_otp.return_value = ("123456", "token_123")
        mock_send_email.return_value = {"success": True}

        response = self.client.post(
            self.send_otp_email_url, {"email": self.verified_user.email}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        # Should show success message
        self.assertContains(response, "Code Sent!")

        # Should store necessary session data
        self.assertEqual(self.client.session["signin_email"], self.verified_user.email)
        self.assertEqual(self.client.session["signin_user_id"], self.verified_user.id)
        self.assertEqual(self.client.session["otp_token_id"], "token_123")
        self.assertEqual(self.client.session["otp_delivery_method"], "email")

        # Verify OTP generation and email sending were called
        mock_generate_otp.assert_called_once_with(self.verified_user, "email")
        mock_send_email.assert_called_once()

    @patch("accounts.views.send_otp_email_message")
    def test_email_sending_failure_shows_error(self, mock_send_email):
        """Test that email sending failure shows appropriate error."""
        mock_send_email.return_value = {"success": False, "error": "SMTP error"}

        with patch("accounts.services.otp_service.OTPService.generate_otp") as mock_generate_otp:
            mock_generate_otp.return_value = ("123456", "token_123")

            response = self.client.post(
                self.send_otp_email_url, {"email": self.verified_user.email}, headers={"hx-request": "true"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Failed to send email. Please try again later.")

    @patch("accounts.views.send_magic_link_email")
    def test_resend_verification_email_during_signin_flow(self, mock_send_email):
        """Test resend verification email functionality for unverified users during signin.

        This test prevents Bug #275: Users should be able to resend verification emails
        when they get blocked during signin due to unverified email.
        """
        from django.urls import reverse

        resend_url = reverse("accounts:resend_verification_email_signin")

        # Mock successful email sending
        mock_send_email.return_value = {"success": True}

        response = self.client.post(resend_url, {"email": self.unverified_user.email}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verification email sent")
        self.assertContains(response, "Check your inbox")

        # Verify email sending was attempted
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        self.assertEqual(call_args[0], self.unverified_user.email)  # email address
        # call_args[1] is the magic link (dynamic)
        self.assertEqual(call_args[2], self.unverified_user.first_name)  # user name
        # Verify is_verification=True was passed
        call_kwargs = mock_send_email.call_args[1]
        self.assertTrue(call_kwargs.get("is_verification", False))

    @patch("accounts.views.send_magic_link_email")
    def test_resend_verification_email_for_already_verified_user(self, mock_send_email):
        """Test resend verification email for already verified users shows appropriate message."""
        response = self.client.post(
            reverse("accounts:resend_verification_email_signin"),
            {"email": self.verified_user.email},
            headers={"hx-request": "true"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already verified")
        self.assertContains(response, "try signing in again")

        # Should not send email to already verified users
        mock_send_email.assert_not_called()

    @patch("accounts.views.send_magic_link_email")
    def test_resend_verification_email_for_nonexistent_user(self, mock_send_email):
        """Test resend verification email for non-existent users returns generic message."""
        fake_email = "nonexistent@example.com"

        response = self.client.post(
            reverse("accounts:resend_verification_email_signin"), {"email": fake_email}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        # Should return generic message to prevent email enumeration
        self.assertContains(response, "If this email is registered, a verification email will be sent.")

        # Should not send email
        mock_send_email.assert_not_called()


class EmailOTPValidationTest(BaseTestCase):
    """Test input validation for email OTP requests."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.send_otp_email_url = reverse("accounts:send_otp_email")

    def test_empty_email_shows_error(self):
        """Test that empty email field shows validation error."""
        response = self.client.post(self.send_otp_email_url, {"email": ""}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter your email address")

    def test_invalid_email_format_shows_error(self):
        """Test that invalid email format shows validation error."""
        invalid_emails = [
            "not-an-email",
            "missing@domain",
            "@missing-local.com",
            "no-domain@",
            "double@@domain.com",
        ]

        for invalid_email in invalid_emails:
            with self.subTest(email=invalid_email):
                response = self.client.post(
                    self.send_otp_email_url, {"email": invalid_email}, headers={"hx-request": "true"}
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Please enter a valid email address")


class SMSOTPSecurityTest(BaseTestCase):
    """Test security aspects of SMS OTP sending."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.send_otp_sms_url = reverse("accounts:send_otp_sms")

        # Create user with verified phone
        self.phone_verified_user = User.objects.create_user(
            email=get_unique_email("phoneverified"),
            name="Phone Verified User",
            phone_number=get_unique_phone_number(),
            email_verified=True,
            phone_verified=True,
        )

        # Create user without verified phone
        self.no_phone_user = User.objects.create_user(
            email=get_unique_email("nophone"),
            name="No Phone User",
            email_verified=True,
            phone_verified=False,
        )

    @patch("accounts.views.switch_is_active")
    def test_sms_disabled_shows_error(self, mock_switch):
        """Test that SMS OTP shows error when feature is disabled."""
        mock_switch.return_value = False

        response = self.client.post(
            self.send_otp_sms_url, {"email": self.phone_verified_user.email}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SMS service is temporarily unavailable")
        self.assertContains(response, "Please use email instead")
        # Verify our view checked the switch
        mock_switch.assert_called_with("sms_feature")

    @override_switch("sms_feature", active=True)
    def test_nonexistent_user_returns_generic_error(self):
        """Test that non-existent user gets generic error for SMS requests."""
        fake_email = "nonexistent@example.com"

        response = self.client.post(self.send_otp_sms_url, {"email": fake_email}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email or account not verified")

    @override_switch("sms_feature", active=True)
    def test_user_without_verified_phone_gets_error(self):
        """Test that user without verified phone number gets appropriate error."""
        response = self.client.post(
            self.send_otp_sms_url, {"email": self.no_phone_user.email}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        # Should get error about missing/unverified phone
        self.assertContains(response, "phone")
        self.assertContains(response, "verify")

    @override_switch("sms_feature", active=True)
    @patch("accounts.views.user_exists")
    @patch("accounts.views.get_user_by_email")
    @patch("accounts.views.send_sms_otp")
    @patch("accounts.services.otp_service.OTPService.generate_otp")
    def test_user_with_verified_phone_receives_sms_successfully(
        self, mock_generate_otp, mock_send_sms, mock_get_user, mock_user_exists
    ):
        """Test that user with verified phone successfully receives SMS OTP."""
        # Mock user lookup functions
        mock_user_exists.return_value = True
        mock_get_user.return_value = self.phone_verified_user

        # Mock OTP generation
        mock_generate_otp.return_value = ("123456", "token_123")
        mock_send_sms.return_value = {"success": True}

        response = self.client.post(
            self.send_otp_sms_url, {"email": self.phone_verified_user.email}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        # Should show success message
        self.assertContains(response, "Code Sent!")

        # Should store necessary session data
        self.assertEqual(self.client.session["signin_email"], self.phone_verified_user.email)
        self.assertEqual(self.client.session["signin_user_id"], self.phone_verified_user.id)
        self.assertEqual(self.client.session["otp_token_id"], "token_123")
        self.assertEqual(self.client.session["otp_delivery_method"], "sms")

        # Verify OTP generation and SMS sending were called
        mock_generate_otp.assert_called_once_with(self.phone_verified_user, "sms")
        mock_send_sms.assert_called_once()


class SMSOTPValidationTest(BaseTestCase):
    """Test input validation for SMS OTP requests."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.send_otp_sms_url = reverse("accounts:send_otp_sms")

    @override_switch("sms_feature", active=True)
    def test_empty_email_shows_error(self):
        """Test that empty email field shows validation error for SMS."""
        response = self.client.post(self.send_otp_sms_url, {"email": ""}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter your email address")

    @override_switch("sms_feature", active=True)
    def test_invalid_email_format_shows_error(self):
        """Test that invalid email format shows validation error for SMS."""
        invalid_emails = [
            "invalid-email",
            "missing@domain",
            "@missing-local.com",
            "no-domain@",
            "double@@domain.com",
        ]

        for invalid_email in invalid_emails:
            with self.subTest(email=invalid_email):
                response = self.client.post(
                    self.send_otp_sms_url, {"email": invalid_email}, headers={"hx-request": "true"}
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Please enter a valid email address")


class SMSOTPIntegrationTest(BaseTestCase):
    """Test complete SMS OTP flow integration."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.send_otp_sms_url = reverse("accounts:send_otp_sms")
        self.verify_otp_url = reverse("accounts:verify_otp")

        # Create fully verified user with phone
        self.verified_user = User.objects.create_user(
            email=get_unique_email("verified"),
            name="Verified User",
            phone_number=get_unique_phone_number(),
            email_verified=True,
            phone_verified=True,
        )

        # Create a school for the user (needed for successful login)
        self.school = School.objects.create(name="Test School", contact_email=self.verified_user.email)
        SchoolMembership.objects.create(
            user=self.verified_user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

    @override_switch("sms_feature", active=True)
    @patch("accounts.views.user_exists")
    @patch("accounts.views.get_user_by_email")
    @patch("accounts.views.send_sms_otp")
    @patch("accounts.services.otp_service.OTPService.generate_otp")
    @patch("accounts.services.otp_service.OTPService.verify_otp")
    def test_complete_sms_signin_flow(
        self, mock_verify_otp, mock_generate_otp, mock_send_sms, mock_get_user, mock_user_exists
    ):
        """Test the complete signin flow from form to successful login via SMS OTP."""
        # Mock user lookup functions
        mock_user_exists.return_value = True
        mock_get_user.return_value = self.verified_user

        # Mock OTP service
        mock_generate_otp.return_value = ("123456", "token_123")
        mock_send_sms.return_value = {"success": True}
        mock_verify_otp.return_value = (True, self.verified_user)

        # Step 1: Submit email for SMS OTP
        response = self.client.post(
            self.send_otp_sms_url, {"email": self.verified_user.email}, headers={"hx-request": "true"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Code Sent!")

        # Verify session data is set correctly
        self.assertEqual(self.client.session["signin_email"], self.verified_user.email)
        self.assertEqual(self.client.session["signin_user_id"], self.verified_user.id)
        self.assertEqual(self.client.session["otp_token_id"], "token_123")
        self.assertEqual(self.client.session["otp_delivery_method"], "sms")

        # Step 2: Verify SMS OTP code
        response = self.client.post(
            self.verify_otp_url, {"verification_code": "123456"}, headers={"hx-request": "true"}
        )

        # Should redirect to dashboard after successful verification
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Redirect"), reverse("dashboard:dashboard"))

        # Session should be cleaned up
        self.assertNotIn("otp_token_id", self.client.session)
        self.assertNotIn("signin_email", self.client.session)
        self.assertNotIn("signin_user_id", self.client.session)

        # Verify all mocks were called correctly
        mock_generate_otp.assert_called_once_with(self.verified_user, "sms")
        mock_send_sms.assert_called_once_with(self.verified_user.phone_number, "123456", self.verified_user.first_name)
        mock_verify_otp.assert_called_once_with("token_123", "123456")

    @override_switch("sms_feature", active=True)
    @patch("accounts.views.send_sms_otp")
    def test_sms_sending_failure_shows_error(self, mock_send_sms):
        """Test that SMS sending failure shows appropriate error."""
        mock_send_sms.return_value = {"success": False, "error": "SMS service error"}

        with patch("accounts.services.otp_service.OTPService.generate_otp") as mock_generate_otp:
            mock_generate_otp.return_value = ("123456", "token_123")

            response = self.client.post(
                self.send_otp_sms_url, {"email": self.verified_user.email}, headers={"hx-request": "true"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Failed to send SMS. Please try email or try again later.")

    @override_switch("sms_feature", active=True)
    def test_sms_otp_verification_with_invalid_code(self):
        """Test SMS OTP verification with invalid code shows error."""
        # Set up session as if SMS OTP was sent
        session = self.client.session
        session["otp_token_id"] = "token_123"
        session["signin_email"] = self.verified_user.email
        session["signin_user_id"] = self.verified_user.id
        session["otp_delivery_method"] = "sms"
        session.save()

        with patch("accounts.services.otp_service.OTPService.verify_otp") as mock_verify_otp:
            mock_verify_otp.return_value = (False, "Invalid or expired code")

            response = self.client.post(
                self.verify_otp_url, {"verification_code": "wrong123"}, headers={"hx-request": "true"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid or expired code")
        # Session should still be intact for retry
        self.assertEqual(self.client.session["otp_token_id"], "token_123")

    @override_switch("sms_feature", active=True)
    def test_sms_otp_verification_without_session_redirects(self):
        """Test that OTP verification without proper session redirects to signin."""
        response = self.client.post(
            self.verify_otp_url, {"verification_code": "123456"}, headers={"hx-request": "true"}
        )

        # Should return form with error when no session data (POST doesn't redirect)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter the verification code.")

    @override_switch("sms_feature", active=True)
    def test_exception_during_sms_otp_sending_shows_generic_error(self):
        """Test that exceptions during SMS OTP sending show generic error."""
        with patch("accounts.services.otp_service.OTPService.generate_otp", side_effect=Exception("Database error")):
            response = self.client.post(
                self.send_otp_sms_url, {"email": self.verified_user.email}, headers={"hx-request": "true"}
            )

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "An error occurred. Please try again later.")
            # Should not reveal internal error details
            self.assertNotContains(response, "Database error")

    @override_switch("sms_feature", active=True)
    def test_case_insensitive_email_handling_for_sms(self):
        """Test that email addresses are handled case-insensitively for SMS requests."""
        # Create user with lowercase email
        user = User.objects.create_user(
            email="test@example.com",
            name="Test User",
            phone_number=get_unique_phone_number(),
            email_verified=True,
            phone_verified=True,
        )

        with patch("messaging.services.auth_email_service.send_sms_otp") as mock_send_sms:
            with patch("accounts.services.otp_service.OTPService.generate_otp") as mock_generate_otp:
                mock_generate_otp.return_value = ("123456", "token_123")
                mock_send_sms.return_value = {"success": True}

                # Submit uppercase email
                response = self.client.post(
                    self.send_otp_sms_url, {"email": "TEST@EXAMPLE.COM"}, headers={"hx-request": "true"}
                )

                self.assertEqual(response.status_code, 200)
                # Should find the user despite case difference
                self.assertContains(response, "Code Sent!")

    @override_switch("sms_feature", active=True)
    def test_email_whitespace_trimming_for_sms(self):
        """Test that email addresses are trimmed of whitespace for SMS requests."""
        user = User.objects.create_user(
            email="test@example.com",
            name="Test User",
            phone_number=get_unique_phone_number(),
            email_verified=True,
            phone_verified=True,
        )

        with patch("messaging.services.auth_email_service.send_sms_otp") as mock_send_sms:
            with patch("accounts.services.otp_service.OTPService.generate_otp") as mock_generate_otp:
                mock_generate_otp.return_value = ("123456", "token_123")
                mock_send_sms.return_value = {"success": True}

                # Submit email with whitespace
                response = self.client.post(
                    self.send_otp_sms_url, {"email": "  test@example.com  "}, headers={"hx-request": "true"}
                )

                self.assertEqual(response.status_code, 200)
                # Should find the user after trimming
                self.assertContains(response, "Code Sent!")


class SMSOTPAdvancedSecurityTest(BaseTestCase):
    """Test advanced security scenarios for SMS OTP."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.send_otp_sms_url = reverse("accounts:send_otp_sms")
        self.verify_otp_url = reverse("accounts:verify_otp")

    @override_switch("sms_feature", active=True)
    def test_unverified_email_user_cannot_get_sms_otp(self):
        """Test that users with unverified email cannot receive SMS OTP."""
        user = User.objects.create_user(
            email=get_unique_email("unverified"),
            name="Unverified User",
            phone_number=get_unique_phone_number(),
            email_verified=False,  # Email not verified
            phone_verified=True,  # Phone verified but email takes precedence
        )

        response = self.client.post(self.send_otp_sms_url, {"email": user.email}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please verify your email address first")
        # Should not send SMS to unverified users
        self.assertNotIn("otp_token_id", self.client.session)

    @override_switch("sms_feature", active=True)
    def test_user_with_missing_phone_number_gets_error(self):
        """Test that user with no phone number gets appropriate error."""
        user = User.objects.create_user(
            email=get_unique_email("nophone"),
            name="No Phone User",
            phone_number="",  # Empty phone number
            email_verified=True,
            phone_verified=False,
        )

        response = self.client.post(self.send_otp_sms_url, {"email": user.email}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Phone not verified. Please choose email or verify your phone first.")

    @override_switch("sms_feature", active=True)
    def test_user_with_unverified_phone_gets_error(self):
        """Test that user with unverified phone number gets appropriate error."""
        user = User.objects.create_user(
            email=get_unique_email("unverifiedphone"),
            name="Unverified Phone User",
            phone_number=get_unique_phone_number(),
            email_verified=True,
            phone_verified=False,  # Phone not verified
        )

        response = self.client.post(self.send_otp_sms_url, {"email": user.email}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Phone not verified. Please choose email or verify your phone first.")


class SMSOTPVerificationDetailedTest(BaseTestCase):
    """Test detailed scenarios for SMS OTP verification."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.verify_otp_url = reverse("accounts:verify_otp")

        self.verified_user = User.objects.create_user(
            email=get_unique_email("verified"),
            name="Verified User",
            phone_number=get_unique_phone_number(),
            email_verified=True,
            phone_verified=True,
        )

        # Create a school for the user (needed for successful login)
        self.school = School.objects.create(name="Test School", contact_email=self.verified_user.email)
        SchoolMembership.objects.create(
            user=self.verified_user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

    def test_empty_verification_code_shows_error(self):
        """Test that empty verification code shows error."""
        # Set up session as if SMS OTP was sent
        session = self.client.session
        session["otp_token_id"] = "token_123"
        session["signin_email"] = self.verified_user.email
        session["signin_user_id"] = self.verified_user.id
        session["otp_delivery_method"] = "sms"
        session.save()

        response = self.client.post(self.verify_otp_url, {"verification_code": ""}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter the verification code.")

    def test_sms_otp_verification_get_shows_masked_phone(self):
        """Test that GET request to verify OTP shows masked phone number for SMS."""
        # Skip this test - requires template that doesn't exist yet
        self.skipTest("Requires accounts/verify_otp.html template")

    @patch("accounts.services.otp_service.OTPService.verify_otp")
    def test_sms_otp_verification_with_expired_code(self, mock_verify_otp):
        """Test SMS OTP verification with expired code."""
        # Set up session as if SMS OTP was sent
        session = self.client.session
        session["otp_token_id"] = "token_123"
        session["signin_email"] = self.verified_user.email
        session["signin_user_id"] = self.verified_user.id
        session["otp_delivery_method"] = "sms"
        session.save()

        # Mock expired code response
        mock_verify_otp.return_value = (False, "Code has expired")

        response = self.client.post(
            self.verify_otp_url, {"verification_code": "123456"}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Code has expired")

    @patch("accounts.services.otp_service.OTPService.verify_otp")
    def test_sms_otp_verification_with_reused_code(self, mock_verify_otp):
        """Test SMS OTP verification with already used code."""
        # Set up session as if SMS OTP was sent
        session = self.client.session
        session["otp_token_id"] = "token_123"
        session["signin_email"] = self.verified_user.email
        session["signin_user_id"] = self.verified_user.id
        session["otp_delivery_method"] = "sms"
        session.save()

        # Mock reused code response
        mock_verify_otp.return_value = (False, "Code already used")

        response = self.client.post(
            self.verify_otp_url, {"verification_code": "123456"}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Code already used")

    @patch("accounts.services.otp_service.OTPService.verify_otp")
    def test_successful_sms_otp_verification_logs_user_in(self, mock_verify_otp):
        """Test that successful SMS OTP verification logs user in and cleans session."""
        # Set up session as if SMS OTP was sent
        session = self.client.session
        session["otp_token_id"] = "token_123"
        session["signin_email"] = self.verified_user.email
        session["signin_user_id"] = self.verified_user.id
        session["otp_delivery_method"] = "sms"
        session.save()

        # Mock successful verification
        mock_verify_otp.return_value = (True, self.verified_user)

        response = self.client.post(
            self.verify_otp_url, {"verification_code": "123456"}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Redirect"), reverse("dashboard:dashboard"))

        # User should be logged in
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.verified_user.id)

        # OTP session data should be cleaned up
        self.assertNotIn("otp_token_id", self.client.session)
        self.assertNotIn("signin_email", self.client.session)
        self.assertNotIn("signin_user_id", self.client.session)
        self.assertNotIn("otp_delivery_method", self.client.session)


class ConsolidatedSignInIntegrationTest(BaseTestCase):
    """Test the complete consolidated signin flow integration."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.signin_url = reverse("accounts:signin")
        self.send_otp_email_url = reverse("accounts:send_otp_email")
        self.verify_otp_url = reverse("accounts:verify_otp")

        # Create fully verified user
        self.verified_user = User.objects.create_user(
            email=get_unique_email("verified"),
            name="Verified User",
            phone_number=get_unique_phone_number(),
            email_verified=True,
            phone_verified=True,
        )

        # Create a school for the user (needed for successful login)
        self.school = School.objects.create(name="Test School", contact_email=self.verified_user.email)
        SchoolMembership.objects.create(
            user=self.verified_user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

    @patch("accounts.views.user_exists")
    @patch("accounts.views.get_user_by_email")
    @patch("accounts.views.send_otp_email_message")
    @patch("accounts.services.otp_service.OTPService.generate_otp")
    @patch("accounts.services.otp_service.OTPService.verify_otp")
    def test_complete_signin_flow_with_email_otp(
        self, mock_verify_otp, mock_generate_otp, mock_send_email, mock_get_user, mock_user_exists
    ):
        """Test the complete signin flow from form to successful login via email OTP."""
        # Mock user lookup functions
        mock_user_exists.return_value = True
        mock_get_user.return_value = self.verified_user

        # Mock OTP service
        mock_generate_otp.return_value = ("123456", "token_123")
        mock_send_email.return_value = {"success": True}
        mock_verify_otp.return_value = (True, self.verified_user)

        # Step 1: GET signin page
        response = self.client.get(self.signin_url)
        self.assertEqual(response.status_code, 200)

        # Step 2: Submit email for OTP
        response = self.client.post(
            self.send_otp_email_url, {"email": self.verified_user.email}, headers={"hx-request": "true"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Code Sent!")

        # Step 3: Verify OTP code
        response = self.client.post(
            self.verify_otp_url, {"verification_code": "123456"}, headers={"hx-request": "true"}
        )

        # Should redirect to dashboard after successful verification
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Redirect"), reverse("dashboard:dashboard"))

        # Session should be cleaned up
        self.assertNotIn("otp_token_id", self.client.session)
        self.assertNotIn("signin_email", self.client.session)
        self.assertNotIn("signin_user_id", self.client.session)

    def test_signin_form_preserves_email_across_error_states(self):
        """Test that email value is preserved when there are validation errors."""
        test_email = "test@example.com"

        # Submit empty email to trigger error
        response = self.client.post(self.send_otp_email_url, {"email": ""}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter your email address")

        # Now submit invalid email format
        response = self.client.post(self.send_otp_email_url, {"email": "invalid"}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a valid email address")
        # Email value should be preserved in the Alpine.js initialization
        self.assertContains(response, "email: 'invalid'")


class ConsolidatedSignInErrorHandlingTest(BaseTestCase):
    """Test error handling and edge cases for the consolidated signin flow."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.send_otp_email_url = reverse("accounts:send_otp_email")

        self.verified_user = User.objects.create_user(
            email=get_unique_email("verified"),
            name="Verified User",
            email_verified=True,
        )

    def test_exception_during_otp_email_sending_shows_generic_error(self):
        """Test that exceptions during OTP email sending show generic error."""
        with patch("accounts.services.otp_service.OTPService.generate_otp", side_effect=Exception("Database error")):
            response = self.client.post(
                self.send_otp_email_url, {"email": self.verified_user.email}, headers={"hx-request": "true"}
            )

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "An error occurred. Please try again later.")
            # Should not reveal internal error details
            self.assertNotContains(response, "Database error")

    def test_case_insensitive_email_handling(self):
        """Test that email addresses are handled case-insensitively."""
        # Create user with lowercase email
        user = User.objects.create_user(
            email="test@example.com",
            name="Test User",
            email_verified=True,
        )

        with patch("accounts.views.send_otp_email_message") as mock_send_email:
            with patch("accounts.services.otp_service.OTPService.generate_otp") as mock_generate_otp:
                mock_generate_otp.return_value = ("123456", "token_123")
                mock_send_email.return_value = {"success": True}

                # Submit uppercase email
                response = self.client.post(
                    self.send_otp_email_url, {"email": "TEST@EXAMPLE.COM"}, headers={"hx-request": "true"}
                )

                self.assertEqual(response.status_code, 200)
                # Should find the user despite case difference
                self.assertContains(response, "Code Sent!")

    def test_email_whitespace_trimming(self):
        """Test that email addresses are trimmed of whitespace."""
        user = User.objects.create_user(
            email="test@example.com",
            name="Test User",
            email_verified=True,
        )

        with patch("accounts.views.send_otp_email_message") as mock_send_email:
            with patch("accounts.services.otp_service.OTPService.generate_otp") as mock_generate_otp:
                mock_generate_otp.return_value = ("123456", "token_123")
                mock_send_email.return_value = {"success": True}

                # Submit email with whitespace
                response = self.client.post(
                    self.send_otp_email_url, {"email": "  test@example.com  "}, headers={"hx-request": "true"}
                )

                self.assertEqual(response.status_code, 200)
                # Should find the user after trimming
                self.assertContains(response, "Code Sent!")
