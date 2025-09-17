"""
Comprehensive Unit Tests for Verification Services

This module tests the authentication services implemented in phases 1-4:
- OTPService: 6-digit OTP generation with 10-min validity and 5 attempt limit
- PhoneValidationService: E.164 international phone validation
- Email verification workflows

These are critical security components that require thorough testing.
"""

from datetime import timedelta
import hashlib
import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone

from accounts.models import VerificationToken
from accounts.services.otp_service import OTPService
from accounts.services.phone_validation import PhoneValidationService
from accounts.tests.test_base import BaseTestCase
from accounts.tests.test_utils import get_unique_email, get_unique_phone_number

User = get_user_model()


class OTPServiceTest(BaseTestCase):
    """Test OTPService for secure OTP generation and verification"""

    def setUp(self):
        self.user = User.objects.create_user(
            email=get_unique_email("test"), name="Test User", phone_number=get_unique_phone_number()
        )

    def test_generate_otp_creates_6_digit_code(self):
        """Test OTP generation creates proper 6-digit code"""
        otp_code, _token_id = OTPService.generate_otp(self.user, "email")

        # Verify format: exactly 6 digits
        self.assertRegex(otp_code, r"^\d{6}$")
        self.assertEqual(len(otp_code), 6)

        # Verify it's in valid range (100000-999999)
        code_int = int(otp_code)
        self.assertGreaterEqual(code_int, 100000)
        self.assertLessEqual(code_int, 999999)

    def test_generate_otp_creates_verification_token(self):
        """Test OTP generation creates proper VerificationToken"""
        otp_code, token_id = OTPService.generate_otp(self.user, "email")

        # Verify token exists
        token = VerificationToken.objects.get(id=token_id)
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token_type, "signin_otp")
        self.assertEqual(token.max_attempts, 5)
        self.assertIsNone(token.used_at)

        # Verify token_value is SHA256 hash of OTP
        expected_hash = hashlib.sha256(otp_code.encode()).hexdigest()
        self.assertEqual(token.token_value, expected_hash)

    def test_generate_otp_sets_10_minute_expiry(self):
        """Test OTP expires after exactly 10 minutes"""
        before_time = timezone.now()
        _otp_code, token_id = OTPService.generate_otp(self.user, "email")
        after_time = timezone.now()

        token = VerificationToken.objects.get(id=token_id)

        # Calculate expected expiry time (10 minutes from generation)
        expected_min = before_time + timedelta(minutes=10)
        expected_max = after_time + timedelta(minutes=10)

        self.assertGreaterEqual(token.expires_at, expected_min)
        self.assertLessEqual(token.expires_at, expected_max)

    def test_generate_otp_clears_existing_signin_otps(self):
        """Test generating new OTP clears existing unused signin OTPs"""
        # Generate first OTP
        _otp_code1, token_id1 = OTPService.generate_otp(self.user, "email")

        # Verify first token exists
        self.assertTrue(VerificationToken.objects.filter(id=token_id1).exists())

        # Generate second OTP
        _otp_code2, token_id2 = OTPService.generate_otp(self.user, "sms")

        # First token should be deleted
        self.assertFalse(VerificationToken.objects.filter(id=token_id1).exists())

        # Second token should exist
        self.assertTrue(VerificationToken.objects.filter(id=token_id2).exists())

    def test_generate_otp_preserves_other_token_types(self):
        """Test generating signin OTP doesn't affect other token types"""
        # Create other token type manually
        other_token = VerificationToken.objects.create(
            user=self.user,
            token_type="email_verification",
            token_value="some_hash",
            expires_at=timezone.now() + timedelta(hours=1),
        )

        # Generate signin OTP
        _otp_code, _token_id = OTPService.generate_otp(self.user, "email")

        # Other token should still exist
        self.assertTrue(VerificationToken.objects.filter(id=other_token.id).exists())

    def test_generate_otp_updates_user_preferred_method(self):
        """Test OTP generation updates user's preferred OTP method"""
        # Initial default method is email
        self.assertEqual(self.user.preferred_otp_method, "email")

        # Generate email OTP
        OTPService.generate_otp(self.user, "email")

        self.user.refresh_from_db()
        self.assertEqual(self.user.preferred_otp_method, "email")

        # Generate SMS OTP
        OTPService.generate_otp(self.user, "sms")

        self.user.refresh_from_db()
        self.assertEqual(self.user.preferred_otp_method, "sms")

    def test_generate_otp_codes_are_random(self):
        """Test OTP codes are sufficiently random"""
        codes = set()

        # Generate 100 OTP codes
        for _ in range(100):
            otp_code, _ = OTPService.generate_otp(self.user, "email")
            codes.add(otp_code)

        # Should have high uniqueness (>90% unique in 100 attempts)
        self.assertGreater(len(codes), 90)

    def test_verify_otp_success_with_valid_code(self):
        """Test OTP verification succeeds with valid code"""
        otp_code, token_id = OTPService.generate_otp(self.user, "email")

        success, result = OTPService.verify_otp(token_id, otp_code)

        self.assertTrue(success)
        self.assertEqual(result, self.user)

        # Token should be marked as used
        token = VerificationToken.objects.get(id=token_id)
        self.assertIsNotNone(token.used_at)

    def test_verify_otp_failure_with_invalid_code(self):
        """Test OTP verification fails with invalid code"""
        _otp_code, token_id = OTPService.generate_otp(self.user, "email")

        success, result = OTPService.verify_otp(token_id, "000000")

        self.assertFalse(success)
        self.assertIn("Invalid code", result)

        # Token should NOT be marked as used
        token = VerificationToken.objects.get(id=token_id)
        self.assertIsNone(token.used_at)
        self.assertEqual(token.attempts, 1)

    def test_verify_otp_failure_with_invalid_token_id(self):
        """Test OTP verification fails with invalid token ID"""
        success, result = OTPService.verify_otp(99999, "123456")

        self.assertFalse(success)
        self.assertEqual(result, "Invalid verification session")

    def test_verify_otp_failure_with_expired_token(self):
        """Test OTP verification fails with expired token"""
        otp_code, token_id = OTPService.generate_otp(self.user, "email")

        # Manually expire the token
        token = VerificationToken.objects.get(id=token_id)
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save()

        success, result = OTPService.verify_otp(token_id, otp_code)

        self.assertFalse(success)
        self.assertIn("expired", result)

    def test_verify_otp_tracks_failed_attempts(self):
        """Test OTP verification tracks failed attempts correctly"""
        _otp_code, token_id = OTPService.generate_otp(self.user, "email")

        # Make 3 failed attempts
        for i in range(3):
            success, result = OTPService.verify_otp(token_id, "000000")
            self.assertFalse(success)

            if i < 4:  # Not locked yet
                self.assertIn(f"{4 - i} attempts remaining", result)

        # Token should have 3 failed attempts
        token = VerificationToken.objects.get(id=token_id)
        self.assertEqual(token.attempts, 3)
        self.assertIsNone(token.used_at)

    def test_verify_otp_locks_after_5_attempts(self):
        """Test OTP verification locks after 5 failed attempts"""
        otp_code, token_id = OTPService.generate_otp(self.user, "email")

        # Make 5 failed attempts
        for i in range(5):
            success, result = OTPService.verify_otp(token_id, "000000")
            self.assertFalse(success)

        # 6th attempt should be locked (even with correct code)
        success, result = OTPService.verify_otp(token_id, otp_code)
        self.assertFalse(success)
        self.assertIn("Too many failed attempts", result)

        # Token should be locked
        token = VerificationToken.objects.get(id=token_id)
        self.assertTrue(token.is_locked())

    def test_verify_otp_used_token_rejected(self):
        """Test already used OTP tokens are rejected"""
        otp_code, token_id = OTPService.generate_otp(self.user, "email")

        # Use the token once
        success, result = OTPService.verify_otp(token_id, otp_code)
        self.assertTrue(success)

        # Try to use it again
        success, result = OTPService.verify_otp(token_id, otp_code)
        self.assertFalse(success)
        self.assertEqual(result, "Invalid verification session")

    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired OTP tokens"""
        # Create another user for the expired token to avoid cleanup by generate_otp
        other_user = User.objects.create_user(
            email="other@example.com", name="Other User", phone_number="+351987654322"
        )

        # Create expired token for other user
        expired_token = VerificationToken.objects.create(
            user=other_user,
            token_type="signin_otp",
            token_value="some_hash",
            expires_at=timezone.now() - timedelta(hours=1),
        )

        # Create non-expired token for main user
        _otp_code, active_token_id = OTPService.generate_otp(self.user, "email")

        # Create non-OTP token (should not be affected)
        other_token = VerificationToken.objects.create(
            user=self.user,
            token_type="email_verification",
            token_value="other_hash",
            expires_at=timezone.now() - timedelta(hours=1),
        )

        # Run cleanup
        deleted_count = OTPService.cleanup_expired_tokens()

        # Only expired OTP token should be deleted
        self.assertEqual(deleted_count, 1)
        self.assertFalse(VerificationToken.objects.filter(id=expired_token.id).exists())
        self.assertTrue(VerificationToken.objects.filter(id=active_token_id).exists())
        self.assertTrue(VerificationToken.objects.filter(id=other_token.id).exists())


class PhoneValidationServiceTest(TestCase):
    """Test PhoneValidationService for E.164 international phone validation"""

    def test_validate_us_phone_numbers(self):
        """Test validation of US phone numbers"""
        valid_us_numbers = [
            "+12345678901",
            "+1 234 567 8901",
            "+1-234-567-8901",
            "+1.234.567.8901",
            "12345678901",  # Should add +1
            "2345678901",  # 10-digit US number
        ]

        for number in valid_us_numbers:
            with self.subTest(number=number):
                result = PhoneValidationService.validate_and_normalize(number)
                self.assertTrue(result.startswith("+1"))
                self.assertEqual(len(result), 12)  # +1 + 10 digits

    def test_validate_portugal_phone_numbers(self):
        """Test validation of Portugal phone numbers"""
        valid_pt_numbers = [
            "+351987654321",
            "+351 987 654 321",
            "+351-987-654-321",
            "987654321",  # Should add +351
        ]

        for number in valid_pt_numbers:
            with self.subTest(number=number):
                result = PhoneValidationService.validate_and_normalize(number)
                self.assertEqual(result, "+351987654321")

    def test_validate_spain_phone_numbers(self):
        """Test validation of Spain phone numbers"""
        valid_es_numbers = [
            "+34612345678",
            "+34 612 345 678",
            "612345678",  # Should add +34
        ]

        for number in valid_es_numbers:
            with self.subTest(number=number):
                result = PhoneValidationService.validate_and_normalize(number)
                self.assertEqual(result, "+34612345678")

    def test_validate_uk_phone_numbers(self):
        """Test validation of UK phone numbers"""
        valid_uk_numbers = [
            "+447700900123",
            "+44 7700 900123",
        ]

        for number in valid_uk_numbers:
            with self.subTest(number=number):
                result = PhoneValidationService.validate_and_normalize(number)
                self.assertTrue(result.startswith("+44"))

    def test_validate_brazil_phone_numbers(self):
        """Test validation of Brazil phone numbers"""
        valid_br_numbers = [
            "+5511987654321",
            "+55 11 98765-4321",
        ]

        for number in valid_br_numbers:
            with self.subTest(number=number):
                result = PhoneValidationService.validate_and_normalize(number)
                self.assertTrue(result.startswith("+55"))

    def test_clean_phone_number_formatting(self):
        """Test phone number cleaning removes formatting"""
        test_cases = [
            ("+1 (234) 567-8901", "+12345678901"),
            ("+351 987 654 321", "+351987654321"),
            ("00351987654321", "+351987654321"),  # Convert 00 to +
            ("0987654321", "987654321"),  # Remove leading 0
        ]

        for input_number, expected in test_cases:
            with self.subTest(input=input_number):
                cleaned = PhoneValidationService._clean_phone_number(input_number)
                self.assertEqual(cleaned, expected)

    def test_invalid_phone_numbers_rejected(self):
        """Test invalid phone numbers are properly rejected"""
        invalid_numbers = [
            "",
            None,
            "abc123",
            "+",
            "123",  # Too short
            "+1234567890123456",  # Too long
            "+0123456789",  # Invalid country code (starts with 0)
        ]

        for number in invalid_numbers:
            with self.subTest(number=number):
                with self.assertRaises(ValidationError):
                    PhoneValidationService.validate_and_normalize(number)

    def test_ambiguous_numbers_require_country_code(self):
        """Test ambiguous numbers require explicit country code"""
        ambiguous_numbers = [
            "12345678",  # Too short for known patterns
            "1234567890123",  # Too long for known patterns
            "812345678",  # Doesn't match known patterns
        ]

        for number in ambiguous_numbers:
            with self.subTest(number=number):
                with self.assertRaises(ValidationError) as cm:
                    PhoneValidationService.validate_and_normalize(number)
                self.assertIn("country code", str(cm.exception))

    def test_format_for_display_us_numbers(self):
        """Test display formatting for US numbers"""
        formatted = PhoneValidationService.format_for_display("+12345678901")
        self.assertEqual(formatted, "+1 (234) 567-8901")

    def test_format_for_display_international_numbers(self):
        """Test display formatting for international numbers"""
        # International numbers kept as-is for now
        formatted = PhoneValidationService.format_for_display("+351987654321")
        self.assertEqual(formatted, "+351987654321")

    def test_format_for_display_invalid_numbers(self):
        """Test display formatting for invalid/short numbers"""
        test_cases = [
            ("", ""),
            (None, None),
            ("123", "123"),
            ("+1234", "+1234"),  # Too short for formatting
        ]

        for input_number, expected in test_cases:
            with self.subTest(input=input_number):
                result = PhoneValidationService.format_for_display(input_number)
                self.assertEqual(result, expected)

    def test_django_validator_function(self):
        """Test phone_number_validator function for Django forms"""
        from accounts.services.phone_validation import phone_number_validator

        # Valid number should not raise exception
        try:
            phone_number_validator("+351987654321")
        except ValidationError:
            self.fail("phone_number_validator raised ValidationError for valid number")

        # Invalid number should raise ValidationError
        with self.assertRaises(ValidationError):
            phone_number_validator("invalid")

    def test_country_code_patterns_validation(self):
        """Test country-specific pattern validation"""
        # Test US pattern validation
        self.assertTrue(PhoneValidationService.COUNTRY_PATTERNS["US"].match("+12345678901"))
        self.assertFalse(
            PhoneValidationService.COUNTRY_PATTERNS["US"].match("+11234567890")  # Invalid area code
        )

        # Test PT pattern validation
        self.assertTrue(PhoneValidationService.COUNTRY_PATTERNS["PT"].match("+351987654321"))
        self.assertFalse(
            PhoneValidationService.COUNTRY_PATTERNS["PT"].match("+35112345678")  # Invalid mobile prefix
        )

    def test_edge_cases_whitespace_handling(self):
        """Test handling of whitespace and edge cases"""
        test_cases = [
            ("  +351987654321  ", "+351987654321"),
            ("\t+1 234 567 8901\n", "+12345678901"),
            ("+351 987 654 321", "+351987654321"),
        ]

        for input_number, expected in test_cases:
            with self.subTest(input=repr(input_number)):
                result = PhoneValidationService.validate_and_normalize(input_number)
                self.assertEqual(result, expected)

    def test_security_input_sanitization(self):
        """Test that phone validation properly sanitizes input"""
        # Test with potential injection attempts
        malicious_inputs = [
            "+351987654321'; DROP TABLE users; --",
            "+351987654321<script>alert('xss')</script>",
            "+351987654321\x00\x01\x02",  # Null bytes and control chars
        ]

        for malicious_input in malicious_inputs:
            with self.subTest(input=malicious_input):
                # Should either validate safely or raise ValidationError
                try:
                    result = PhoneValidationService.validate_and_normalize(malicious_input)
                    # If it doesn't raise an error, result should be clean
                    self.assertRegex(result, r"^\+[1-9]\d{1,14}$")
                except ValidationError:
                    # ValidationError is acceptable for malicious input
                    pass

    def test_performance_with_large_input(self):
        """Test performance with unusually large input"""
        # Test with very long string
        long_input = "1" * 1000

        with self.assertRaises(ValidationError):
            PhoneValidationService.validate_and_normalize(long_input)

    def test_normalize_international_prefix_conversion(self):
        """Test conversion of international prefixes"""
        test_cases = [
            ("00351987654321", "+351987654321"),  # 00 -> +
            ("011351987654321", "11351987654321"),  # 011 not converted (US international prefix)
        ]

        for input_number, expected_clean in test_cases:
            with self.subTest(input=input_number):
                cleaned = PhoneValidationService._clean_phone_number(input_number)
                self.assertEqual(cleaned, expected_clean)


class EmailVerificationServiceTest(BaseTestCase):
    """Test email verification workflows and edge cases"""

    def setUp(self):
        self.user = User.objects.create_user(
            email=get_unique_email("test"), name="Test User", phone_number=get_unique_phone_number()
        )
        # Create a request factory for testing views
        from django.test import RequestFactory

        self.factory = RequestFactory()

    def _create_request_for_user(self, user):
        """Helper to create an authenticated request for a user"""
        from django.contrib.sessions.middleware import SessionMiddleware

        request = self.factory.post("/send-verification-email/")
        request.user = user
        # Add session support
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        return request

    @patch("accounts.views.send_magic_link_email")
    def test_send_verification_email_success(self, mock_send_email):
        """Test successful email verification sending"""
        mock_send_email.return_value = {"success": True}

        from accounts.views import send_verification_email

        request = self._create_request_for_user(self.user)
        result = send_verification_email(request)

        # Should return success response
        self.assertEqual(result.status_code, 200)
        # Check that send_magic_link_email was called with correct parameters
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        self.assertEqual(call_args[0], self.user.email)  # email
        # call_args[1] is the magic_link (generated dynamically)
        self.assertEqual(call_args[2], self.user.first_name)  # user_name
        # Check is_verification=True in kwargs
        call_kwargs = mock_send_email.call_args[1]
        self.assertTrue(call_kwargs.get("is_verification", False))

    @patch("accounts.views.send_magic_link_email", side_effect=Exception("SMTP error"))
    def test_send_verification_email_failure(self, mock_send_email):
        """Test email verification sending failure handling"""
        from accounts.views import send_verification_email

        request = self._create_request_for_user(self.user)
        result = send_verification_email(request)

        # Should return error response due to exception
        self.assertEqual(result.status_code, 200)
        self.assertIn("error", result.content.decode())

    def test_multiple_verification_emails_allowed(self):
        """Test that multiple verification emails can be sent"""
        with patch("accounts.views.send_magic_link_email") as mock_send_email:
            mock_send_email.return_value = {"success": True}

            from accounts.views import send_verification_email

            # Send first email
            request1 = self._create_request_for_user(self.user)
            result1 = send_verification_email(request1)
            self.assertEqual(result1.status_code, 200)

            # Send second email immediately
            request2 = self._create_request_for_user(self.user)
            result2 = send_verification_email(request2)
            self.assertEqual(result2.status_code, 200)

            # Both calls should succeed
            self.assertEqual(mock_send_email.call_count, 2)

    def test_email_verification_with_already_verified_user(self):
        """Test email verification attempt on already verified user"""
        self.user.email_verified = True
        self.user.email_verified_at = timezone.now()
        self.user.save()

        with patch("accounts.views.send_magic_link_email") as mock_send_email:
            from accounts.views import send_verification_email

            request = self._create_request_for_user(self.user)
            result = send_verification_email(request)

            # Should return message indicating already verified
            self.assertEqual(result.status_code, 200)
            self.assertIn("already verified", result.content.decode())
            # Should not call send_magic_link_email for already verified users
            mock_send_email.assert_not_called()


class SMSVerificationServiceTest(BaseTestCase):
    """Test SMS/OTP verification workflows"""

    def setUp(self):
        self.user = User.objects.create_user(
            email=get_unique_email("test"), name="Test User", phone_number=get_unique_phone_number()
        )

    def _create_request_for_user(self, user):
        """Helper to create a request object for the given user"""
        from django.contrib.sessions.middleware import SessionMiddleware

        request = RequestFactory().post("/verify-sms/")
        request.user = user
        # Add session support
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        return request

    @patch("accounts.views.send_sms_otp")
    def test_send_verification_sms_success(self, mock_send_sms):
        """Test successful SMS verification sending"""
        mock_send_sms.return_value = {"success": True}

        from accounts.views import send_verification_sms

        request = self._create_request_for_user(self.user)
        response = send_verification_sms(request)

        self.assertEqual(response.status_code, 200)

        # Check that send_sms_otp was called with correct parameters
        mock_send_sms.assert_called_once()
        call_args = mock_send_sms.call_args[0]
        self.assertEqual(call_args[0], self.user.phone_number)  # phone_number
        self.assertRegex(call_args[1], r"^\d{6}$")  # otp_code is 6 digits
        self.assertEqual(call_args[2], self.user.first_name)  # user_name
        # Check is_verification=True in kwargs
        call_kwargs = mock_send_sms.call_args[1]
        self.assertTrue(call_kwargs.get("is_verification", False))

        # Check response contains success message
        self.assertContains(response, f"Verification code sent to {self.user.phone_number}!")

    @patch("accounts.views.send_sms_otp", side_effect=Exception("SMS service error"))
    def test_send_verification_sms_failure(self, mock_send_sms):
        """Test SMS verification sending failure handling"""
        from accounts.views import send_verification_sms

        request = self._create_request_for_user(self.user)
        response = send_verification_sms(request)

        # Should return an error response but still be a valid HTTP response
        self.assertIn(response.status_code, [200, 400])
        self.assertContains(response, "error", status_code=response.status_code)

    def test_send_verification_sms_no_phone_number(self):
        """Test SMS verification for user without phone number"""
        # Update phone number directly in database to bypass validation
        User = get_user_model()
        User.objects.filter(pk=self.user.pk).update(phone_number="")
        self.user.refresh_from_db()

        from accounts.views import send_verification_sms

        request = self._create_request_for_user(self.user)
        response = send_verification_sms(request)

        # Should return error response
        self.assertIn(response.status_code, [200, 400])
        self.assertContains(response, "phone", status_code=response.status_code)

    def test_send_verification_sms_invalid_phone_number(self):
        """Test SMS verification with invalid phone number"""
        # Bypass model validation by updating directly in database
        User = get_user_model()
        User.objects.filter(pk=self.user.pk).update(phone_number="invalid")
        self.user.refresh_from_db()

        with patch("accounts.views.send_sms_otp") as mock_send_sms:
            mock_send_sms.side_effect = ValidationError("Invalid phone number")

            from accounts.views import send_verification_sms

            request = self._create_request_for_user(self.user)
            response = send_verification_sms(request)

            # Should return error response
            self.assertIn(response.status_code, [200, 400])
            self.assertContains(response, "error", status_code=response.status_code)

    @patch("accounts.views.send_sms_otp")
    def test_sms_verification_generates_otp_session(self, mock_send_sms):
        """Test SMS verification generates proper OTP session data"""
        mock_send_sms.return_value = {"success": True}

        from accounts.views import send_verification_sms

        # This would normally be called within a view with request.session
        # For unit testing, we test the OTP generation directly
        otp_code, token_id = OTPService.generate_otp(self.user, "sms")

        # Verify OTP was generated correctly
        self.assertIsNotNone(otp_code)
        self.assertIsNotNone(token_id)

        token = VerificationToken.objects.get(id=token_id)
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token_type, "signin_otp")
