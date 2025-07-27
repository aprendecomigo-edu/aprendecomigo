"""
Comprehensive tests for Stripe webhook handler.

This test suite covers all webhook event types, security validation,
idempotent processing, error handling, and integration scenarios.
"""

import json
import logging
from decimal import Decimal
from unittest.mock import Mock, patch

import stripe
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from finances.models import (
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.services.stripe_base import StripeService


@override_settings(
    STRIPE_SECRET_KEY="sk_test_fake_key_for_testing",
    STRIPE_PUBLIC_KEY="pk_test_fake_key_for_testing", 
    STRIPE_WEBHOOK_SECRET="whsec_test_fake_secret_for_testing"
)
class StripeWebhookHandlerTestCase(TestCase):
    """Test case for Stripe webhook handler functionality."""

    def setUp(self):
        """Set up test data for webhook tests."""
        # Create test student user
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        # Create test transaction
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.PROCESSING,
            stripe_payment_intent_id="pi_test_123456789",
            metadata={
                "hours": "10.00",
                "package_name": "10-hour package"
            }
        )
        
        # Create student account balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("0.00"),
            hours_consumed=Decimal("0.00"),
            balance_amount=Decimal("0.00")
        )
        
        # Test webhook secret
        self.webhook_secret = "whsec_test_secret_key"
        
        # Mock Stripe event data
        self.payment_intent_succeeded_event = {
            "id": "evt_test_webhook_123",
            "object": "event",
            "type": "payment_intent.succeeded",
            "created": 1633024234,
            "data": {
                "object": {
                    "id": "pi_test_123456789",
                    "object": "payment_intent",
                    "amount": 5000,
                    "currency": "eur",
                    "status": "succeeded",
                    "metadata": {
                        "user_id": str(self.student.id),
                        "transaction_type": "package"
                    }
                }
            }
        }
        
        self.payment_intent_failed_event = {
            "id": "evt_test_webhook_456",
            "object": "event", 
            "type": "payment_intent.payment_failed",
            "created": 1633024235,
            "data": {
                "object": {
                    "id": "pi_test_123456789",
                    "object": "payment_intent",
                    "amount": 5000,
                    "currency": "eur",
                    "status": "requires_payment_method",
                    "last_payment_error": {
                        "message": "Your card was declined."
                    }
                }
            }
        }
        
        self.payment_intent_canceled_event = {
            "id": "evt_test_webhook_789",
            "object": "event",
            "type": "payment_intent.canceled", 
            "created": 1633024236,
            "data": {
                "object": {
                    "id": "pi_test_123456789",
                    "object": "payment_intent",
                    "amount": 5000,
                    "currency": "eur",
                    "status": "canceled"
                }
            }
        }
        
        # URL for webhook endpoint
        self.webhook_url = reverse('finances:stripe-webhook')

    def _create_webhook_payload(self, event_data):
        """Create a webhook payload with proper signature."""
        payload = json.dumps(event_data, separators=(',', ':'))
        return payload.encode('utf-8')

    def _generate_test_signature(self, payload, secret):
        """Generate a test signature for webhook validation."""
        import time
        import hmac
        import hashlib
        
        timestamp = str(int(time.time()))
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        signature = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test_secret_key")
    @patch('finances.views.PaymentService')
    @patch('finances.views.StripeService')
    def test_webhook_signature_verification_success(self, mock_stripe_service, mock_payment_service):
        """Test successful webhook signature verification."""
        # Setup mocks
        mock_service = Mock()
        mock_service.construct_webhook_event.return_value = {
            'success': True,
            'event': self.payment_intent_succeeded_event,
            'event_type': 'payment_intent.succeeded',
            'event_id': 'evt_test_webhook_123'
        }
        mock_service.is_webhook_event_type_supported.return_value = True
        mock_stripe_service.return_value = mock_service
        
        mock_payment_service_instance = Mock()
        mock_payment_service_instance.confirm_payment_completion.return_value = {
            'success': True,
            'transaction_id': self.transaction.id
        }
        mock_payment_service.return_value = mock_payment_service_instance
        
        payload = self._create_webhook_payload(self.payment_intent_succeeded_event)
        signature = self._generate_test_signature(payload, self.webhook_secret)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature
        )
        
        self.assertEqual(response.status_code, 200)
        mock_service.construct_webhook_event.assert_called_once()

    @patch('finances.views.StripeService')
    def test_webhook_signature_verification_failure(self, mock_stripe_service):
        """Test webhook signature verification failure."""
        # Setup mock to return signature verification failure
        mock_service = Mock()
        mock_service.construct_webhook_event.return_value = {
            'success': False,
            'error_type': 'signature_verification_error',
            'message': 'Invalid signature'
        }
        mock_stripe_service.return_value = mock_service
        
        payload = self._create_webhook_payload(self.payment_intent_succeeded_event)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE="invalid_signature"
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Invalid signature", status_code=400)

    def test_webhook_missing_signature_header(self):
        """Test webhook request without signature header."""
        payload = self._create_webhook_payload(self.payment_intent_succeeded_event)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json'
            # No HTTP_STRIPE_SIGNATURE header
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Missing signature", status_code=400)

    @patch('finances.views.StripeService')
    def test_webhook_unsupported_event_type(self, mock_stripe_service):
        """Test webhook with unsupported event type."""
        mock_service = Mock()
        mock_service.construct_webhook_event.return_value = {
            'success': True,
            'event': {'type': 'unsupported.event.type', 'id': 'evt_123'},
            'event_type': 'unsupported.event.type',
            'event_id': 'evt_123'
        }
        mock_service.is_webhook_event_type_supported.return_value = False
        mock_stripe_service.return_value = mock_service
        
        payload = self._create_webhook_payload({'type': 'unsupported.event.type'})
        signature = self._generate_test_signature(payload, self.webhook_secret)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Event type not supported", status_code=200)

    @patch('finances.views.PaymentService')
    @patch('finances.views.StripeService')
    def test_payment_intent_succeeded_processing(self, mock_stripe_service, mock_payment_service):
        """Test processing of payment_intent.succeeded event."""
        # Setup mocks
        mock_service = Mock()
        mock_service.construct_webhook_event.return_value = {
            'success': True,
            'event': self.payment_intent_succeeded_event,
            'event_type': 'payment_intent.succeeded',
            'event_id': 'evt_test_webhook_123'
        }
        mock_service.is_webhook_event_type_supported.return_value = True
        mock_stripe_service.return_value = mock_service
        
        mock_payment_service_instance = Mock()
        mock_payment_service_instance.confirm_payment_completion.return_value = {
            'success': True,
            'transaction_id': self.transaction.id
        }
        mock_payment_service.return_value = mock_payment_service_instance
        
        payload = self._create_webhook_payload(self.payment_intent_succeeded_event)
        signature = self._generate_test_signature(payload, self.webhook_secret)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature
        )
        
        self.assertEqual(response.status_code, 200)
        mock_payment_service_instance.confirm_payment_completion.assert_called_once_with(
            "pi_test_123456789"
        )

    @patch('finances.views.PaymentService')
    @patch('finances.views.StripeService')
    def test_payment_intent_failed_processing(self, mock_stripe_service, mock_payment_service):
        """Test processing of payment_intent.payment_failed event."""
        # Setup mocks
        mock_service = Mock()
        mock_service.construct_webhook_event.return_value = {
            'success': True,
            'event': self.payment_intent_failed_event,
            'event_type': 'payment_intent.payment_failed',
            'event_id': 'evt_test_webhook_456'
        }
        mock_service.is_webhook_event_type_supported.return_value = True
        mock_stripe_service.return_value = mock_service
        
        mock_payment_service_instance = Mock()
        mock_payment_service_instance.handle_payment_failure.return_value = {
            'success': True,
            'transaction_id': self.transaction.id
        }
        mock_payment_service.return_value = mock_payment_service_instance
        
        payload = self._create_webhook_payload(self.payment_intent_failed_event)
        signature = self._generate_test_signature(payload, self.webhook_secret)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature
        )
        
        self.assertEqual(response.status_code, 200)
        mock_payment_service_instance.handle_payment_failure.assert_called_once_with(
            "pi_test_123456789",
            "Your card was declined."
        )

    @patch('finances.views.PaymentService')
    @patch('finances.views.StripeService')
    def test_payment_intent_canceled_processing(self, mock_stripe_service, mock_payment_service):
        """Test processing of payment_intent.canceled event."""
        # Setup mocks
        mock_service = Mock()
        mock_service.construct_webhook_event.return_value = {
            'success': True,
            'event': self.payment_intent_canceled_event,
            'event_type': 'payment_intent.canceled',
            'event_id': 'evt_test_webhook_789'
        }
        mock_service.is_webhook_event_type_supported.return_value = True
        mock_stripe_service.return_value = mock_service
        
        mock_payment_service_instance = Mock()
        mock_payment_service_instance.handle_payment_failure.return_value = {
            'success': True,
            'transaction_id': self.transaction.id
        }
        mock_payment_service.return_value = mock_payment_service_instance
        
        payload = self._create_webhook_payload(self.payment_intent_canceled_event)
        signature = self._generate_test_signature(payload, self.webhook_secret)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature
        )
        
        self.assertEqual(response.status_code, 200)
        mock_payment_service_instance.handle_payment_failure.assert_called_once_with(
            "pi_test_123456789",
            "Payment was canceled"
        )

    @patch('finances.views.PaymentService')
    @patch('finances.views.StripeService')
    def test_idempotent_processing_duplicate_events(self, mock_stripe_service, mock_payment_service):
        """Test that duplicate webhook events are handled idempotently."""
        # Create a completed transaction to simulate already processed webhook
        completed_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_duplicate_123",
            metadata={"hours": "10.00"}
        )
        
        event_data = {
            "id": "evt_duplicate_test",
            "object": "event",
            "type": "payment_intent.succeeded",
            "created": 1633024234,
            "data": {
                "object": {
                    "id": "pi_test_duplicate_123",
                    "status": "succeeded"
                }
            }
        }
        
        # Setup mocks
        mock_service = Mock()
        mock_service.construct_webhook_event.return_value = {
            'success': True,
            'event': event_data,
            'event_type': 'payment_intent.succeeded',
            'event_id': 'evt_duplicate_test'
        }
        mock_service.is_webhook_event_type_supported.return_value = True
        mock_stripe_service.return_value = mock_service
        
        mock_payment_service_instance = Mock()
        mock_payment_service_instance.confirm_payment_completion.return_value = {
            'success': False,
            'error_type': 'already_processed',
            'message': 'Transaction already completed'
        }
        mock_payment_service.return_value = mock_payment_service_instance
        
        payload = self._create_webhook_payload(event_data)
        signature = self._generate_test_signature(payload, self.webhook_secret)
        
        # Send the same webhook twice
        for _ in range(2):
            response = self.client.post(
                self.webhook_url,
                data=payload,
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE=signature
            )
            
            # Should return 200 even if already processed (idempotent)
            self.assertEqual(response.status_code, 200)

    def test_webhook_only_accepts_post_requests(self):
        """Test that webhook endpoint only accepts POST requests."""
        payload = self._create_webhook_payload(self.payment_intent_succeeded_event)
        
        # Test GET request
        response = self.client.get(self.webhook_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # Test PUT request
        response = self.client.put(
            self.webhook_url,
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_webhook_csrf_exemption(self):
        """Test that webhook endpoint is properly CSRF exempt."""
        payload = self._create_webhook_payload(self.payment_intent_succeeded_event)
        
        # Make request without CSRF token (should work)
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json'
        )
        
        # Should not fail due to CSRF (will fail for other reasons like missing signature)
        self.assertNotEqual(response.status_code, 403)

    @patch('finances.views.PaymentService')
    @patch('finances.views.StripeService')
    def test_webhook_error_handling_payment_service_failure(self, mock_stripe_service, mock_payment_service):
        """Test webhook error handling when payment service fails."""
        # Setup mocks
        mock_service = Mock()
        mock_service.construct_webhook_event.return_value = {
            'success': True,
            'event': self.payment_intent_succeeded_event,
            'event_type': 'payment_intent.succeeded',
            'event_id': 'evt_test_webhook_123'
        }
        mock_service.is_webhook_event_type_supported.return_value = True
        mock_stripe_service.return_value = mock_service
        
        # Make payment service fail
        mock_payment_service_instance = Mock()
        mock_payment_service_instance.confirm_payment_completion.side_effect = Exception("Database error")
        mock_payment_service.return_value = mock_payment_service_instance
        
        payload = self._create_webhook_payload(self.payment_intent_succeeded_event)
        signature = self._generate_test_signature(payload, self.webhook_secret)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature
        )
        
        # Should return 500 on processing failure
        self.assertEqual(response.status_code, 500)

    @patch('finances.views.logger')
    @patch('finances.views.StripeService')
    def test_webhook_comprehensive_logging(self, mock_stripe_service, mock_logger):
        """Test that webhook events are properly logged."""
        mock_service = Mock()
        mock_service.construct_webhook_event.return_value = {
            'success': True,
            'event': self.payment_intent_succeeded_event,
            'event_type': 'payment_intent.succeeded',
            'event_id': 'evt_test_webhook_123'
        }
        mock_service.is_webhook_event_type_supported.return_value = True
        mock_stripe_service.return_value = mock_service
        
        payload = self._create_webhook_payload(self.payment_intent_succeeded_event)
        signature = self._generate_test_signature(payload, self.webhook_secret)
        
        self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature
        )
        
        # Verify logging calls were made
        mock_logger.info.assert_called()


@override_settings(
    STRIPE_SECRET_KEY="sk_test_fake_key_for_testing",
    STRIPE_PUBLIC_KEY="pk_test_fake_key_for_testing", 
    STRIPE_WEBHOOK_SECRET="whsec_test_fake_secret_for_testing"
)
class WebhookModelIntegrationTestCase(TestCase):
    """Integration tests for webhook handler with actual model operations."""

    def setUp(self):
        """Set up test data for integration tests."""
        self.student = CustomUser.objects.create_user(
            email="integration@test.com",
            name="Integration Test Student"
        )
        
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("75.00"),
            payment_status=TransactionPaymentStatus.PROCESSING,
            stripe_payment_intent_id="pi_integration_test_123",
            metadata={
                "hours": "15.00",
                "package_name": "15-hour package"
            }
        )
        
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("5.00"),
            hours_consumed=Decimal("2.00"),
            balance_amount=Decimal("25.00")
        )

    def test_successful_payment_updates_models_correctly(self):
        """Test that successful payment webhook properly updates all related models."""
        # Verify initial state
        self.assertEqual(self.transaction.payment_status, TransactionPaymentStatus.PROCESSING)
        self.assertEqual(self.student_balance.hours_purchased, Decimal("5.00"))
        self.assertEqual(self.student_balance.balance_amount, Decimal("25.00"))
        
        # Simulate successful payment processing (would be called by webhook)
        from finances.services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # Mock the Stripe API call to return succeeded status
        with patch('stripe.PaymentIntent.retrieve') as mock_retrieve:
            mock_payment_intent = Mock()
            mock_payment_intent.status = 'succeeded'
            mock_payment_intent.id = 'pi_integration_test_123'
            mock_retrieve.return_value = mock_payment_intent
            
            result = payment_service.confirm_payment_completion('pi_integration_test_123')
        
        # Verify the result
        self.assertTrue(result['success'])
        
        # Refresh models from database
        self.transaction.refresh_from_db()
        self.student_balance.refresh_from_db()
        
        # Verify transaction status updated
        self.assertEqual(self.transaction.payment_status, TransactionPaymentStatus.COMPLETED)
        
        # Verify hours were credited (5.00 existing + 15.00 from purchase)
        self.assertEqual(self.student_balance.hours_purchased, Decimal("20.00"))
        
        # Verify balance amount updated (25.00 existing + 75.00 from purchase)
        self.assertEqual(self.student_balance.balance_amount, Decimal("100.00"))

    def test_failed_payment_updates_transaction_status(self):
        """Test that failed payment webhook properly updates transaction status."""
        # Verify initial state
        self.assertEqual(self.transaction.payment_status, TransactionPaymentStatus.PROCESSING)
        
        # Simulate failed payment processing
        from finances.services.payment_service import PaymentService
        
        payment_service = PaymentService()
        result = payment_service.handle_payment_failure(
            'pi_integration_test_123',
            'Insufficient funds'
        )
        
        # Verify the result
        self.assertTrue(result['success'])
        
        # Refresh transaction from database
        self.transaction.refresh_from_db()
        
        # Verify transaction status updated
        self.assertEqual(self.transaction.payment_status, TransactionPaymentStatus.FAILED)
        
        # Verify failure metadata was added
        self.assertIn('error_message', self.transaction.metadata)
        self.assertEqual(self.transaction.metadata['error_message'], 'Insufficient funds')
        
        # Verify student balance unchanged (no hours credited on failure)
        self.student_balance.refresh_from_db()
        self.assertEqual(self.student_balance.hours_purchased, Decimal("5.00"))
        self.assertEqual(self.student_balance.balance_amount, Decimal("25.00"))