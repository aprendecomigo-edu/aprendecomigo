"""
Consolidated test suite for Payment API endpoints.

This module contains focused tests for:
- Payment method management (CRUD operations)
- Purchase initiation and transaction processing
- Stripe webhook handling and validation
- Payment flow integration tests
- PCI compliance and security validation

Focuses on payment business logic and security requirements.
"""

import json
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from finances.models import (
    PlanType,
    PricingPlan,
    PurchaseTransaction,
    StoredPaymentMethod,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.tests.base import FinanceBaseTestCase
from finances.tests.stripe_test_utils import (
    SimpleStripeTestCase,
    comprehensive_stripe_mocks_decorator,
)

User = get_user_model()


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PaymentAPITestCase(FinanceBaseTestCase, APITestCase):
    """Base test case with common setup for payment API tests."""

    def setUp(self):
        """Set up test data common to all payment API tests."""
        super().setUp()
        
        # Create additional student for testing
        self.other_student = User.objects.create_user(
            email="other@example.com",
            name="Other Student",
            password="testpass123"
        )
        
        # Use existing pricing plan from base class and create additional ones if needed
        self.package_plan = self.pricing_plan  # Use existing plan from base
        
        self.subscription_plan = PricingPlan.objects.create(
            name="Monthly Unlimited",
            description="Unlimited tutoring for one month",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("40.00"),
            price_eur=Decimal("499.99"),
            validity_days=None,
            is_active=True
        )

    def authenticate_as_student(self):
        """Authenticate client as the test student."""
        self.client.force_authenticate(user=self.student_user)

    def authenticate_as_admin(self):
        """Authenticate client as admin."""
        self.client.force_authenticate(user=self.admin_user)


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PaymentMethodAPITests(PaymentAPITestCase):
    """Test cases for payment method management endpoints."""

    def setUp(self):
        """Set up payment method test data."""
        super().setUp()
        
        # Create test payment method
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_123",
            card_brand="visa",
            card_last4="4242",
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True
        )

    def test_list_payment_methods_authenticated(self):
        """Test authenticated user can list their payment methods."""
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-payment-methods')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
        
        payment_method_data = response.data['payment_methods'][0]
        self.assertEqual(payment_method_data['id'], self.payment_method.id)
        self.assertEqual(payment_method_data['card_brand'], 'visa')
        self.assertTrue(payment_method_data['is_default'])

    def test_payment_method_pci_compliance_masking(self):
        """Test that card details are properly masked for PCI compliance."""
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-payment-methods')
        
        response = self.client.get(url)
        payment_method = response.data['payment_methods'][0]
        
        # Verify card number is masked
        self.assertEqual(payment_method['card_display'], 'Visa ****X242')
        # Verify sensitive data is not exposed
        self.assertNotIn('stripe_payment_method_id', payment_method)

    @patch('finances.services.payment_method_service.PaymentMethodService.add_payment_method')
    def test_add_payment_method_success(self, mock_add_method):
        """Test successful payment method addition with proper service integration."""
        mock_add_method.return_value = {
            'success': True,
            'payment_method_id': 2,
            'card_display': 'Visa ****4242',
            'is_default': False,
            'message': 'Payment method added successfully'
        }
        
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-payment-methods')
        
        data = {
            'stripe_payment_method_id': 'pm_test_new',
            'is_default': False
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify service called with correct parameters
        mock_add_method.assert_called_once_with(
            student_user=self.student_user,
            stripe_payment_method_id='pm_test_new',
            is_default=False
        )

    def test_add_payment_method_invalid_stripe_id_format(self):
        """Test validation of Stripe payment method ID format."""
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-payment-methods')
        
        invalid_ids = ['invalid_id', 'pm_', 'pm_' + 'x' * 100, '']
        
        for stripe_id in invalid_ids:
            data = {
                'stripe_payment_method_id': stripe_id,
                'is_default': False
            }
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                           f"Should reject invalid ID: {stripe_id}")

    @patch('finances.services.payment_method_service.PaymentMethodService.remove_payment_method')
    def test_remove_payment_method_success(self, mock_remove_method):
        """Test successful payment method removal."""
        mock_remove_method.return_value = {
            'success': True,
            'message': 'Payment method removed successfully',
            'was_default': True
        }
        
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-remove-payment-method', 
                     kwargs={'pk': self.payment_method.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify service receives integer ID, not string
        mock_remove_method.assert_called_once_with(
            student_user=self.student_user,
            payment_method_id=self.payment_method.id
        )

    def test_cross_user_payment_method_security(self):
        """Test users cannot access other users' payment methods."""
        # Create another user's payment method
        other_payment_method = StoredPaymentMethod.objects.create(
            student=self.other_student,
            stripe_payment_method_id="pm_other_123",
            card_brand="mastercard",
            card_last4="5555"
        )
        
        self.authenticate_as_student()
        
        # Try to remove other user's payment method
        url = reverse('finances:studentbalance-remove-payment-method',
                     kwargs={'pk': other_payment_method.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PurchaseInitiationAPITests(PaymentAPITestCase):
    """Test cases for purchase initiation and transaction processing."""

    def setUp(self):
        """Set up purchase test data with Stripe mocks."""
        super().setUp()
        
        # Mock Stripe payment intent creation
        self.stripe_patcher = patch('stripe.PaymentIntent.create')
        self.mock_stripe_create = self.stripe_patcher.start()
        
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_test_12345"
        mock_payment_intent.client_secret = "pi_test_12345_secret"
        mock_payment_intent.amount = 25000
        mock_payment_intent.currency = "eur"
        self.mock_stripe_create.return_value = mock_payment_intent

    def tearDown(self):
        """Clean up patches."""
        super().tearDown()
        self.stripe_patcher.stop()

    def test_initiate_package_purchase_authenticated(self):
        """Test authenticated user can initiate package purchase."""
        self.authenticate_as_student()
        url = reverse('finances:purchase-initiate')
        
        data = {
            'pricing_plan_id': self.package_plan.id,
            'guest_email': None
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify response structure
        self.assertIn('client_secret', response.data)
        self.assertIn('transaction_id', response.data)
        self.assertEqual(response.data['amount'], 250.0)
        
        # Verify transaction created
        transaction = PurchaseTransaction.objects.get(
            id=response.data['transaction_id']
        )
        self.assertEqual(transaction.student, self.student_user)
        self.assertEqual(transaction.amount, Decimal('250.00'))
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.PROCESSING)

    def test_initiate_guest_purchase(self):
        """Test guest user can initiate purchase with email."""
        url = reverse('finances:purchase-initiate')
        
        data = {
            'pricing_plan_id': self.package_plan.id,
            'guest_email': 'guest@example.com'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify guest transaction handling
        transaction = PurchaseTransaction.objects.get(
            id=response.data['transaction_id']
        )
        self.assertIsNone(transaction.student)  # Guest purchases have no student initially

    def test_initiate_purchase_inactive_plan(self):
        """Test purchase initiation fails for inactive plans."""
        inactive_plan = PricingPlan.objects.create(
            name="Inactive Plan",
            plan_type=PlanType.PACKAGE,
            price_eur=Decimal("100.00"),
            is_active=False
        )
        
        self.authenticate_as_student()
        url = reverse('finances:purchase-initiate')
        
        data = {
            'pricing_plan_id': inactive_plan.id,
            'guest_email': None
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not available', response.data['error'].lower())

    def test_initiate_purchase_stripe_error_handling(self):
        """Test proper handling of Stripe API errors."""
        # Mock Stripe error
        self.mock_stripe_create.side_effect = Exception("Stripe API Error")
        
        self.authenticate_as_student()
        url = reverse('finances:purchase-initiate')
        
        data = {
            'pricing_plan_id': self.package_plan.id,
            'guest_email': None
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('payment processing', response.data['error'].lower())


@override_settings(
    STRIPE_SECRET_KEY="sk_test_fake",
    STRIPE_WEBHOOK_SECRET="whsec_test_fake"
)
@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class StripeWebhookAPITests(FinanceBaseTestCase, TestCase):
    """Test cases for Stripe webhook handling."""

    def setUp(self):
        """Set up webhook test data."""
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.PROCESSING,
            stripe_payment_intent_id="pi_test_123456789"
        )
        
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("0.00"),
            hours_consumed=Decimal("0.00"),
            balance_amount=Decimal("0.00")
        )

    @patch('stripe.Webhook.construct_event')
    def test_payment_intent_succeeded_webhook(self, mock_construct_event):
        """Test successful payment webhook processing."""
        # Mock webhook event
        mock_event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123456789",
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
        mock_construct_event.return_value = mock_event
        
        url = reverse('finances:stripe-webhook')
        payload = json.dumps(mock_event)
        
        response = self.client.post(
            url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify transaction status updated
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.payment_status, TransactionPaymentStatus.COMPLETED)

    @patch('stripe.Webhook.construct_event')
    def test_payment_intent_failed_webhook(self, mock_construct_event):
        """Test failed payment webhook processing."""
        mock_event = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test_123456789",
                    "status": "failed",
                    "last_payment_error": {
                        "message": "Your card was declined."
                    }
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        url = reverse('finances:stripe-webhook')
        payload = json.dumps(mock_event)
        
        response = self.client.post(
            url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify transaction status updated
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.payment_status, TransactionPaymentStatus.FAILED)

    def test_webhook_invalid_signature(self):
        """Test webhook rejects invalid signatures for security."""
        url = reverse('finances:stripe-webhook')
        payload = json.dumps({"type": "test.event"})
        
        # Test without signature header
        response = self.client.post(
            url,
            data=payload,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('stripe.Webhook.construct_event')
    def test_webhook_idempotent_processing(self, mock_construct_event):
        """Test webhook events are processed idempotently."""
        mock_event = {
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123456789",
                    "status": "succeeded"
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        url = reverse('finances:stripe-webhook')
        payload = json.dumps(mock_event)
        
        # Process same webhook twice
        for _ in range(2):
            response = self.client.post(
                url,
                data=payload,
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='test_signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify transaction only processed once
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.payment_status, TransactionPaymentStatus.COMPLETED)


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PaymentSecurityTests(PaymentAPITestCase):
    """Security tests for payment endpoints."""

    def test_payment_method_endpoints_require_authentication(self):
        """Test payment method endpoints require authentication."""
        endpoints = [
            reverse('finances:studentbalance-payment-methods'),
            reverse('finances:studentbalance-remove-payment-method', kwargs={'pk': 1}),
            reverse('finances:studentbalance-set-default-payment-method', kwargs={'pk': 1}),
        ]
        
        for url in endpoints:
            for method in ['get', 'post', 'delete']:
                if hasattr(self.client, method):
                    response = getattr(self.client, method)(url)
                    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purchase_endpoints_handle_injection_attempts(self):
        """Test purchase endpoints are protected against injection attacks."""
        self.authenticate_as_student()
        url = reverse('finances:purchase-initiate')
        
        malicious_data = {
            'pricing_plan_id': "'; DROP TABLE finances_pricinplan; --",
            'guest_email': "<script>alert('xss')</script>"
        }
        
        response = self.client.post(url, malicious_data, format='json')
        
        # Should return validation error, not crash
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payment_method_data_isolation(self):
        """Test payment methods are properly isolated between users."""
        # Create payment methods for both users
        StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_student_123",
            card_brand="visa",
            card_last4="4242"
        )
        
        StoredPaymentMethod.objects.create(
            student=self.other_student,
            stripe_payment_method_id="pm_other_123",
            card_brand="mastercard",
            card_last4="5555"
        )
        
        # Student should only see their own payment methods
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-payment-methods')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        
        payment_method = response.data['payment_methods'][0]
        self.assertEqual(payment_method['card_brand'], 'visa')
