"""
E2E Tests for User Sign-In Flows

Tests both email and SMS authentication flows for existing users.
Follows best practices using data-test attributes with fallback strategies.

NOTE: These tests verify the flow up to OTP entry. Full end-to-end testing
would require either:
1. A test mode with fixed OTP codes
2. Email/SMS interception to capture the actual OTP
3. Database access to retrieve or set OTP codes
"""

from collections.abc import Generator
import re
import time

from playwright.sync_api import Page, expect
import pytest


class TestSignInFlows:
    """Test sign-in flows for existing users via email and SMS OTP."""

    @pytest.fixture
    def existing_user_email(self) -> str:
        """Return email of a known existing user in the test database."""
        # The admin@example.com user should exist in the development database
        return "admin@example.com"

    @pytest.fixture
    def existing_user_phone(self) -> str:
        """Return phone number of a known existing user in the test database."""
        return "+351912345678"

    def test_email_signin_flow_to_otp(self, page: Page, base_url: str, existing_user_email: str):
        """
        Test email sign-in flow up to OTP form display.

        User Journey:
        1. Navigate to signin page
        2. Enter existing user email
        3. Request OTP via email
        4. Verify OTP form appears with correct elements

        NOTE: Does not test actual OTP verification as codes are dynamically generated.
        """
        # Navigate to signin page
        page.goto(f"{base_url}/signin/")
        expect(page).to_have_title(re.compile("Sign In.*Aprende Comigo"))

        # Enter email address
        try:
            # Try data-test attribute first
            email_input = page.locator('[data-test="signin-email-input"]')
            email_input.fill(existing_user_email)
        except Exception:
            # Fallback to placeholder selector
            email_input = page.locator('[placeholder="your_email@example.com"]')
            email_input.fill(existing_user_email)

        # Small delay to ensure Alpine.js updates the form state
        page.wait_for_timeout(500)

        # Request OTP via Email
        try:
            # Try data-test attribute first
            email_button = page.locator('[data-test="send-code-email"]')
            expect(email_button).to_be_enabled()
            email_button.click()
        except Exception:
            # Fallback to text selector
            email_button = page.get_by_role("button", name="Send Code via Email")
            # Wait for button to be enabled after entering email
            expect(email_button).to_be_enabled(timeout=5000)
            email_button.click()

        # Wait for the HTMX response and OTP form to appear
        # The signin form should be replaced with the OTP verification form

        # Verify success message appears
        expect(page.locator('text="Code Sent!"')).to_be_visible(timeout=10000)

        # Verify email is shown in the confirmation
        expect(page.locator(f'text="{existing_user_email}"')).to_be_visible()

        # Verify OTP input fields are visible (6 separate inputs)
        otp_inputs = page.locator(".otp-input")
        expect(otp_inputs).to_have_count(6)

        # Verify first input is focused
        expect(otp_inputs.first).to_be_focused()

        # Verify Verify Code button is present
        try:
            verify_button = page.locator('[data-test="verify-code"]')
            expect(verify_button).to_be_visible()
        except Exception:
            verify_button = page.get_by_role("button", name="Verify Code")
            expect(verify_button).to_be_visible()

        # Verify Resend link is present
        expect(page.locator('text="Resend"')).to_be_visible()

    @pytest.mark.skip(reason="SMS flow requires phone number collection step - TODO: implement phone verification")
    def test_sms_signin_flow_to_otp(
        self, page: Page, base_url: str, existing_user_email: str, existing_user_phone: str
    ):
        """
        Test SMS sign-in flow up to OTP form display.

        User Journey:
        1. Navigate to signin page
        2. Enter existing user email (required to identify user)
        3. Request OTP via SMS
        4. Verify OTP form appears with correct elements

        NOTE: Does not test actual OTP verification as codes are dynamically generated.
        """
        # Navigate to signin page
        page.goto(f"{base_url}/signin/")
        expect(page).to_have_title(re.compile("Sign In.*Aprende Comigo"))

        # Enter email address (required to identify the user account)
        # Even for SMS flow, email is needed to identify which user is signing in
        try:
            # Try data-test attribute first
            email_input = page.locator('[data-test="signin-email-input"]')
            email_input.fill(existing_user_email)
        except Exception:
            # Fallback to placeholder selector
            email_input = page.locator('[placeholder="your_email@example.com"]')
            email_input.fill(existing_user_email)

        # Small delay to ensure Alpine.js updates the form state
        page.wait_for_timeout(500)

        # Request OTP via SMS
        try:
            # Try data-test attribute first
            sms_button = page.locator('[data-test="send-code-sms"]')
            expect(sms_button).to_be_enabled()
            sms_button.click()
        except Exception:
            # Fallback to text selector
            sms_button = page.get_by_role("button", name="Send Code via SMS")
            # Wait for button to be enabled after entering email
            expect(sms_button).to_be_enabled(timeout=5000)
            sms_button.click()

        # Wait for HTMX response
        # Check if phone number prompt appears (for users without phone on file)
        # or if we go directly to OTP entry (for users with phone on file)
        page.wait_for_timeout(1000)  # Wait for HTMX to process

        try:
            # Check if phone input appears
            phone_input = page.locator('[data-test="phone-input"]')
            if phone_input.is_visible(timeout=2000):
                # Enter phone number if prompted
                phone_input.fill(existing_user_phone)
                # Submit phone number
                try:
                    submit_phone = page.locator('[data-test="submit-phone"]')
                    submit_phone.click()
                except Exception:
                    page.get_by_role("button", name="Send Code").click()
        except Exception:
            # Phone already on file, proceed to OTP entry
            pass

        # Wait for success message indicating OTP was sent
        expect(page.locator('text="Code Sent!"')).to_be_visible(timeout=10000)

        # For SMS, verify phone number is shown (might be masked)
        # The phone number might appear as "***5678" or similar
        expect(page.locator("text=phone")).to_be_visible()

        # Verify OTP input fields are visible (6 separate inputs)
        otp_inputs = page.locator(".otp-input")
        expect(otp_inputs).to_have_count(6)

        # Verify first input is focused
        expect(otp_inputs.first).to_be_focused()

        # Verify Verify Code button is present
        try:
            verify_button = page.locator('[data-test="verify-code"]')
            expect(verify_button).to_be_visible()
        except Exception:
            verify_button = page.get_by_role("button", name="Verify Code")
            expect(verify_button).to_be_visible()

        # Verify Resend link is present
        expect(page.locator('text="Resend"')).to_be_visible()

    def test_signin_input_validation(self, page: Page, base_url: str):
        """
        Test error handling in signin flow.

        Scenarios:
        1. Invalid email format
        2. Non-existent user
        """
        page.goto(f"{base_url}/signin/")

        # Test 1: Invalid email format
        email_input = page.locator('[placeholder="your_email@example.com"]')
        email_input.fill("invalid-email")

        # Both buttons should remain disabled with invalid email
        try:
            email_button = page.locator('[data-test="send-code-email"]')
            sms_button = page.locator('[data-test="send-code-sms"]')
        except Exception:
            email_button = page.get_by_role("button", name="Send Code via Email")
            sms_button = page.get_by_role("button", name="Send Code via SMS")

        expect(email_button).to_be_disabled()
        expect(sms_button).to_be_disabled()

        # Test 2: Non-existent user (valid email format)
        email_input.fill("nonexistent@example.com")

        # Buttons should be enabled with valid email format
        expect(email_button).to_be_enabled(timeout=2000)
        email_button.click()

        # Should show error message for non-existent user
        try:
            error_message = page.locator('[data-test="signin-error"]')
            expect(error_message).to_be_visible(timeout=5000)
        except Exception:
            # Fallback: check for error text
            expect(page.locator("text=not found")).to_be_visible(timeout=5000)
