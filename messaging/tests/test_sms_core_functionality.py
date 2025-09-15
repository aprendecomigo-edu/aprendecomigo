"""
Essential SMS Backend Tests

Tests only the core functionality needed for the signin flow to work:
- Console backend logs correctly (development)
- SNS backend can be configured (production)
- Backend loading works
- send_sms_otp works end-to-end
- Basic error handling
"""

from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from messaging.services.auth_email_service import send_sms_otp
from messaging.services.sms_backends import ConsoleSMSBackend, SNSSMSBackend, get_sms_backend


class SMSBackendCoreTest(TestCase):
    """Test essential SMS backend functionality."""

    def test_console_backend_logs_message(self):
        """Test console backend logs SMS for development."""
        backend = ConsoleSMSBackend()

        with patch("messaging.services.sms_backends.logger") as mock_logger:
            result = backend.send("+351987654321", "Test OTP: 123456")

        # Should succeed and log
        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "console")
        mock_logger.info.assert_called()

        # Check SMS content was logged
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        sms_logged = any("SMS MESSAGE" in call for call in log_calls)
        self.assertTrue(sms_logged)

    def test_backend_loading_works(self):
        """Test SMS backend loading and switching."""
        # Default should be console
        backend = get_sms_backend()
        self.assertIsInstance(backend, ConsoleSMSBackend)

        # Invalid backend should raise error
        with override_settings(SMS_BACKEND="invalid.backend"):
            with self.assertRaises(ImproperlyConfigured):
                get_sms_backend()

    @patch("messaging.services.sms_backends.boto3")
    def test_sns_backend_can_be_configured(self, mock_boto3):
        """Test SNS backend can be configured for production."""
        mock_sns_client = Mock()
        mock_boto3.client.return_value = mock_sns_client
        mock_sns_client.publish.return_value = {"MessageId": "test-123"}

        with override_settings(SMS_BACKEND="messaging.services.sms_backends.SNSSMSBackend", AWS_SNS_REGION="eu-west-1"):
            backend = get_sms_backend()
            self.assertIsInstance(backend, SNSSMSBackend)

            result = backend.send("+351987654321", "Test")
            self.assertTrue(result["success"])
            self.assertEqual(result["provider"], "sns")

    def test_send_sms_otp_works_end_to_end(self):
        """Test send_sms_otp function works for signin flow."""
        with patch("messaging.services.sms_backends.logger"):
            result = send_sms_otp(phone_number="+351987654321", otp_code="123456", user_name="Test User")

        # Should work end-to-end
        self.assertTrue(result["success"])
        self.assertEqual(result["phone_number"], "+351987654321")
        self.assertEqual(result["service"], "otp_verification")
        self.assertIn("sent_at", result)

    def test_sms_error_handling(self):
        """Test basic error handling when SMS fails."""
        with patch("messaging.services.auth_email_service.send_sms") as mock_send:
            mock_send.return_value = {"success": False, "error": "SMS service unavailable"}

            result = send_sms_otp("+351987654321", "123456", "Error User")

            self.assertFalse(result["success"])
            self.assertIn("error", result)

    @override_settings(DEBUG=True, SMS_BACKEND="messaging.services.sms_backends.ConsoleSMSBackend")
    def test_development_signin_flow_works(self):
        """Test signin flow works in development with console backend."""
        with patch("messaging.services.sms_backends.logger") as mock_logger:
            result = send_sms_otp(
                phone_number="+351987654321",
                otp_code="DEV123",
                user_name="Dev User",
                is_verification=False,  # Signin flow
            )

        # Should work for signin
        self.assertTrue(result["success"])
        self.assertEqual(result["service"], "otp_verification")

        # Should log in development
        mock_logger.info.assert_called()
