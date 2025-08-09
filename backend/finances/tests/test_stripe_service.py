"""
Test suite for Stripe service infrastructure.

This test module follows TDD principles to define and validate the Stripe integration
infrastructure including service initialization, error handling, and security features.
"""

import os
from decimal import Decimal
from unittest.mock import Mock, patch

import stripe
from django.conf import settings
from django.test import TestCase, override_settings

from finances.services.stripe_base import StripeService
from accounts.models import CustomUser


class StripeServiceConfigurationTests(TestCase):
    """Test Stripe service configuration and initialization."""

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_stripe_service_initialization_with_valid_config(self):
        """Test that StripeService initializes correctly with valid configuration."""
        service = StripeService()
        self.assertIsNotNone(service)
        self.assertEqual(stripe.api_key, "sk_test_example_key")

    @override_settings(
        STRIPE_SECRET_KEY="",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_stripe_service_initialization_missing_secret_key(self):
        """Test that StripeService raises error when secret key is missing."""
        with self.assertRaises(ValueError) as context:
            StripeService()
        self.assertIn("STRIPE_SECRET_KEY", str(context.exception))

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_stripe_service_initialization_missing_public_key(self):
        """Test that StripeService raises error when public key is missing."""
        with self.assertRaises(ValueError) as context:
            StripeService()
        self.assertIn("STRIPE_PUBLIC_KEY", str(context.exception))

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET=""
    )
    def test_stripe_service_initialization_missing_webhook_secret(self):
        """Test that StripeService raises error when webhook secret is missing."""
        with self.assertRaises(ValueError) as context:
            StripeService()
        self.assertIn("STRIPE_WEBHOOK_SECRET", str(context.exception))

    @override_settings(
        STRIPE_SECRET_KEY="sk_live_should_not_be_in_development",
        STRIPE_PUBLIC_KEY="pk_live_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_stripe_service_development_environment_validation(self):
        """Test that live keys are rejected in development environment."""
        with patch.dict(os.environ, {'DJANGO_ENV': 'development'}):
            with self.assertRaises(ValueError) as context:
                StripeService(force_environment_validation=True)  # Force validation to run
            self.assertIn("live", str(context.exception).lower())

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_should_not_be_in_production",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_stripe_service_production_environment_validation(self):
        """Test that test keys are rejected in production environment."""
        with patch.dict(os.environ, {'DJANGO_ENV': 'production'}):
            with self.assertRaises(ValueError) as context:
                StripeService(force_environment_validation=True)  # Force validation to run
            self.assertIn("test", str(context.exception).lower())


class StripeServiceErrorHandlingTests(TestCase):
    """Test comprehensive Stripe error handling."""

    def setUp(self):
        """Set up test environment with valid Stripe configuration."""
        self.stripe_settings = {
            'STRIPE_SECRET_KEY': 'sk_test_example_key',
            'STRIPE_PUBLIC_KEY': 'pk_test_example_key',
            'STRIPE_WEBHOOK_SECRET': 'whsec_test_example'
        }

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_handle_stripe_card_error(self):
        """Test handling of Stripe CardError exceptions."""
        service = StripeService()
        
        mock_error = stripe.error.CardError(
            message="Your card was declined.",
            param="number",
            code="card_declined"
        )
        
        result = service.handle_stripe_error(mock_error)
        
        self.assertEqual(result['error_type'], 'card_error')
        self.assertEqual(result['message'], 'Your card was declined.')
        self.assertEqual(result['param'], 'number')
        self.assertEqual(result['code'], 'card_declined')
        self.assertFalse(result['success'])

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_handle_stripe_rate_limit_error(self):
        """Test handling of Stripe RateLimitError exceptions."""
        service = StripeService()
        
        mock_error = stripe.error.RateLimitError(
            message="Too many requests made to the API too quickly"
        )
        
        result = service.handle_stripe_error(mock_error)
        
        self.assertEqual(result['error_type'], 'rate_limit_error')
        self.assertIn('requests', result['message'].lower())
        self.assertFalse(result['success'])

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_handle_stripe_invalid_request_error(self):
        """Test handling of Stripe InvalidRequestError exceptions."""
        service = StripeService()
        
        mock_error = stripe.error.InvalidRequestError(
            message="Invalid request",
            param="amount"
        )
        
        result = service.handle_stripe_error(mock_error)
        
        self.assertEqual(result['error_type'], 'invalid_request_error')
        self.assertEqual(result['message'], 'Invalid request')
        self.assertEqual(result['param'], 'amount')
        self.assertFalse(result['success'])

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_handle_stripe_authentication_error(self):
        """Test handling of Stripe AuthenticationError exceptions."""
        service = StripeService()
        
        mock_error = stripe.error.AuthenticationError(
            message="Invalid API key provided"
        )
        
        result = service.handle_stripe_error(mock_error)
        
        self.assertEqual(result['error_type'], 'authentication_error')
        self.assertIn('authentication', result['message'].lower())
        self.assertFalse(result['success'])

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_handle_stripe_api_connection_error(self):
        """Test handling of Stripe APIConnectionError exceptions."""
        service = StripeService()
        
        mock_error = stripe.error.APIConnectionError(
            message="Network communication with Stripe failed"
        )
        
        result = service.handle_stripe_error(mock_error)
        
        self.assertEqual(result['error_type'], 'api_connection_error')
        self.assertIn('connection', result['message'].lower())
        self.assertFalse(result['success'])

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_handle_stripe_api_error(self):
        """Test handling of generic Stripe APIError exceptions."""
        service = StripeService()
        
        mock_error = stripe.error.APIError(
            message="Something went wrong on Stripe's end"
        )
        
        result = service.handle_stripe_error(mock_error)
        
        self.assertEqual(result['error_type'], 'api_error')
        self.assertIn('server error', result['message'].lower())
        self.assertFalse(result['success'])

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_handle_unknown_exception(self):
        """Test handling of unknown exceptions."""
        service = StripeService()
        
        mock_error = ValueError("Some unexpected error")
        
        result = service.handle_stripe_error(mock_error)
        
        self.assertEqual(result['error_type'], 'unknown_error')
        self.assertIn('unexpected error', result['message'].lower())
        self.assertFalse(result['success'])


class StripeServiceAPIConnectionTests(TestCase):
    """Test Stripe API connection and basic operations."""

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    @patch('stripe.Account.retrieve')
    def test_verify_api_connection_success(self, mock_account_retrieve):
        """Test successful API connection verification."""
        mock_account_retrieve.return_value = Mock(
            id="acct_test123",
            business_profile={'name': 'Test Account'}
        )
        
        service = StripeService()
        result = service.verify_api_connection()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['account_id'], 'acct_test123')
        self.assertIn('connection verified', result['message'].lower())

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    @patch('stripe.Account.retrieve')
    def test_verify_api_connection_failure(self, mock_account_retrieve):
        """Test API connection verification failure."""
        mock_account_retrieve.side_effect = stripe.error.AuthenticationError(
            "Invalid API key provided"
        )
        
        service = StripeService()
        result = service.verify_api_connection()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'authentication_error')
        self.assertIn('authentication', result['message'].lower())

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_get_public_key(self):
        """Test that public key is returned correctly."""
        service = StripeService()
        public_key = service.get_public_key()
        
        self.assertEqual(public_key, "pk_test_example_key")

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_get_webhook_secret(self):
        """Test that webhook secret is returned correctly."""
        service = StripeService()
        webhook_secret = service.get_webhook_secret()
        
        self.assertEqual(webhook_secret, "whsec_test_example")


class StripeServiceWebhookTests(TestCase):
    """Test Stripe webhook handling infrastructure."""

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    @patch('stripe.Webhook.construct_event')
    def test_construct_webhook_event_success(self, mock_construct_event):
        """Test successful webhook event construction."""
        mock_event = {
            'id': 'evt_test123',
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_test123'}}
        }
        mock_construct_event.return_value = mock_event
        
        service = StripeService()
        
        payload = '{"id": "evt_test123", "type": "payment_intent.succeeded"}'
        sig_header = "t=1234567890,v1=signature"
        
        result = service.construct_webhook_event(payload, sig_header)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['event'], mock_event)
        self.assertEqual(result['event']['id'], 'evt_test123')

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    @patch('stripe.Webhook.construct_event')
    def test_construct_webhook_event_invalid_signature(self, mock_construct_event):
        """Test webhook event construction with invalid signature."""
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
            "Unable to extract timestamp and signatures from header",
            sig_header="invalid_signature"
        )
        
        service = StripeService()
        
        payload = '{"id": "evt_test123", "type": "payment_intent.succeeded"}'
        sig_header = "invalid_signature"
        
        result = service.construct_webhook_event(payload, sig_header)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'signature_verification_error')
        self.assertIn('signature', result['message'].lower())

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_is_webhook_event_type_supported(self):
        """Test webhook event type support checking."""
        service = StripeService()
        
        # Test supported event types
        supported_events = [
            'payment_intent.succeeded',
            'payment_intent.payment_failed',
            'customer.created',
            'customer.updated',
            'invoice.payment_succeeded',
            'invoice.payment_failed'
        ]
        
        for event_type in supported_events:
            self.assertTrue(service.is_webhook_event_type_supported(event_type))
        
        # Test unsupported event types
        unsupported_events = [
            'unsupported_event_type',
            'some.random.event',
            ''
        ]
        
        for event_type in unsupported_events:
            self.assertFalse(service.is_webhook_event_type_supported(event_type))


class StripeServiceSecurityTests(TestCase):
    """Test Stripe service security features."""

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_rate_limiting_considerations(self):
        """Test that rate limiting considerations are properly handled."""
        service = StripeService()
        
        # This test verifies that the service is designed with rate limiting in mind
        # In a real implementation, this would test actual rate limiting logic
        self.assertTrue(hasattr(service, 'handle_stripe_error'))
        
        # Simulate rate limit error handling
        rate_limit_error = stripe.error.RateLimitError(
            "Too many requests made to the API too quickly"
        )
        result = service.handle_stripe_error(rate_limit_error)
        
        self.assertEqual(result['error_type'], 'rate_limit_error')
        self.assertFalse(result['success'])

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key", 
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_sensitive_data_not_logged(self):
        """Test that sensitive data is not included in error logs."""
        service = StripeService()
        
        # Test that API keys are not exposed in string representation
        service_str = str(service)
        self.assertNotIn("sk_test_example_key", service_str)
        self.assertNotIn("whsec_test_example", service_str)
        
        # Test that public key can be safely exposed
        public_key = service.get_public_key()
        self.assertEqual(public_key, "pk_test_example_key")

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_environment_key_validation_logic(self):
        """Test the logic for validating keys against environment."""
        service = StripeService()
        
        # Test key validation methods exist and work correctly
        self.assertTrue(service._is_test_key("sk_test_example"))
        self.assertTrue(service._is_test_key("pk_test_example"))
        self.assertFalse(service._is_test_key("sk_live_example"))
        self.assertFalse(service._is_test_key("pk_live_example"))
        
        self.assertTrue(service._is_live_key("sk_live_example"))
        self.assertTrue(service._is_live_key("pk_live_example"))
        self.assertFalse(service._is_live_key("sk_test_example"))
        self.assertFalse(service._is_live_key("pk_test_example"))


class StripeServiceBusinessLogicTests(TestCase):
    """Test Stripe service business logic and edge cases specific to payment processing."""

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_currency_validation_for_eur_only(self):
        """Test that service validates EUR currency for European market."""
        service = StripeService()
        
        # Test EUR is accepted
        self.assertTrue(service.is_currency_supported("eur"))
        
        # Test other currencies are rejected for business requirements
        self.assertFalse(service.is_currency_supported("usd"))
        self.assertFalse(service.is_currency_supported("gbp"))

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_payment_method_restrictions(self):
        """Test that only approved payment methods are allowed."""
        service = StripeService()
        
        # Business requirement: Only cards and SEPA are allowed for Portuguese market
        allowed_methods = service.get_allowed_payment_methods()
        
        self.assertIn("card", allowed_methods)
        self.assertIn("sepa_debit", allowed_methods)
        
        # Should not allow payment methods not suitable for European tutoring
        self.assertNotIn("alipay", allowed_methods)
        self.assertNotIn("wechat_pay", allowed_methods)

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_webhook_signature_timeout_validation(self):
        """Test webhook signature timeout to prevent replay attacks."""
        service = StripeService()
        
        # Create test payload with old timestamp (over 5 minutes ago)
        import time
        old_timestamp = int(time.time()) - 400  # 6+ minutes ago
        payload = '{"test": "data"}'
        
        # This should fail signature validation due to timestamp tolerance
        result = service.construct_webhook_event(payload, f"t={old_timestamp},v1=fakehash")
        
        # Business requirement: Reject old webhook events for security
        self.assertFalse(result['success'])

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_amount_limits_for_educational_platform(self):
        """Test amount validation specific to tutoring platform business rules."""
        service = StripeService()
        
        # Test minimum amount for education services (€0.50)
        self.assertFalse(service.validate_amount_for_education_service(49))  # €0.49
        self.assertTrue(service.validate_amount_for_education_service(50))   # €0.50
        
        # Test maximum amount for individual purchases (€10,000)
        self.assertTrue(service.validate_amount_for_education_service(999999))   # €9,999.99
        self.assertFalse(service.validate_amount_for_education_service(1000001)) # €10,000.01

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_retry_logic_for_temporary_failures(self):
        """Test that temporary API failures are handled with proper retry logic."""
        service = StripeService()
        
        # Simulate temporary connection error
        temp_error = stripe.error.APIConnectionError("Temporary connection problem")
        
        result = service.handle_stripe_error(temp_error)
        
        # Should indicate this is retryable
        self.assertEqual(result['error_type'], 'api_connection_error')
        self.assertTrue(result.get('retryable', False))

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example_key",
        STRIPE_PUBLIC_KEY="pk_test_example_key",
        STRIPE_WEBHOOK_SECRET="whsec_test_example"
    )
    def test_fraud_prevention_metadata_requirements(self):
        """Test that required anti-fraud metadata is validated."""
        service = StripeService()
        
        # Test metadata validation for educational transactions
        valid_metadata = {
            'user_id': '12345',
            'transaction_type': 'package',
            'hours_purchased': '10.0',
            'school_context': 'tutoring'
        }
        
        invalid_metadata = {
            'user_id': '12345'
            # Missing required fields
        }
        
        self.assertTrue(service.validate_educational_metadata(valid_metadata))
        self.assertFalse(service.validate_educational_metadata(invalid_metadata))