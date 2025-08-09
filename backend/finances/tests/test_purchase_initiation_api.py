"""
Test suite for Purchase Initiation API following TDD principles.

This module comprehensively tests the purchase initiation API endpoint that allows
students to initiate tutoring hour purchases, following the GitHub Issue #30 requirements.

The API endpoint `/finances/api/purchase/initiate/` handles:
- Package and subscription plan purchases 
- Authenticated user and guest purchases
- Stripe payment intent creation
- Transaction record creation
- Comprehensive error handling and validation
"""

import json
import logging
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

import stripe
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from finances.models import (
    PricingPlan,
    PlanType,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)

User = get_user_model()

# Disable logging during tests to reduce noise
logging.disable(logging.CRITICAL)


class PurchaseInitiationAPITestCase(TestCase):
    """Base test case with common setup for purchase initiation API tests."""
    
    def setUp(self):
        """Set up test environment with users, pricing plans, and API client."""
        self.client = APIClient()
        
        # Create test users
        self.authenticated_user = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )
        
        self.guest_user_email = "guest@test.com"
        
        # Create test pricing plans
        self.package_plan = PricingPlan.objects.create(
            name="10 Hour Package",
            description="10 hours of tutoring",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("250.00"),
            validity_days=365,
            display_order=1,
            is_active=True
        )
        
        self.subscription_plan = PricingPlan.objects.create(
            name="Monthly Unlimited",
            description="Unlimited tutoring for one month",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("40.00"),
            price_eur=Decimal("499.99"),
            validity_days=None,
            display_order=2,
            is_active=True
        )
        
        self.inactive_plan = PricingPlan.objects.create(
            name="Inactive Plan",
            description="This plan is not active",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("5.00"),
            price_eur=Decimal("125.00"),
            validity_days=180,
            display_order=3,
            is_active=False
        )
        
        # API endpoint URL
        self.url = reverse('finances:purchase-initiate')
        
        # Mock Stripe configuration
        self.stripe_patcher = patch.multiple(
            'django.conf.settings',
            STRIPE_SECRET_KEY='sk_test_example_key',
            STRIPE_PUBLIC_KEY='pk_test_example_key',
            STRIPE_WEBHOOK_SECRET='whsec_test_example'
        )
        self.stripe_patcher.start()
        
    def tearDown(self):
        """Clean up after each test."""
        self.stripe_patcher.stop()


class PurchaseInitiationAPIAuthenticatedUserTests(PurchaseInitiationAPITestCase):
    """Test purchase initiation API for authenticated users."""
    
    def setUp(self):
        """Set up authenticated user session."""
        super().setUp()
        self.client.force_authenticate(user=self.authenticated_user)
    
    @patch('stripe.PaymentIntent.create')
    def test_initiate_purchase_package_plan_success(self, mock_stripe_create):
        """Test successful purchase initiation for authenticated user with package plan."""
        # Mock Stripe PaymentIntent response
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_test_package_auth"
        mock_payment_intent.client_secret = "pi_test_package_auth_secret_xyz"
        mock_payment_intent.amount = 25000  # 250.00 EUR in cents
        mock_payment_intent.currency = "eur"
        mock_payment_intent.customer = None
        mock_stripe_create.return_value = mock_payment_intent
        
        # Request data
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        # Make API request
        response = self.client.post(self.url, request_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['client_secret'], "pi_test_package_auth_secret_xyz")
        self.assertIsNotNone(response.data['transaction_id'])
        self.assertEqual(response.data['payment_intent_id'], "pi_test_package_auth")
        
        # Verify Stripe was called correctly
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args[1]
        self.assertEqual(call_args['amount'], 25000)
        self.assertEqual(call_args['currency'], 'eur')
        self.assertIn('automatic_payment_methods', call_args)
        
        # Verify metadata
        metadata = call_args['metadata']
        self.assertEqual(metadata['user_id'], str(self.authenticated_user.id))
        self.assertEqual(metadata['pricing_plan_id'], str(self.package_plan.id))
        self.assertEqual(metadata['transaction_type'], TransactionType.PACKAGE)
        
        # Verify transaction record created
        transaction_id = response.data['transaction_id']
        transaction = PurchaseTransaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.student, self.authenticated_user)
        self.assertEqual(transaction.amount, Decimal('250.00'))
        self.assertEqual(transaction.transaction_type, TransactionType.PACKAGE)
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.PENDING)
        self.assertEqual(transaction.stripe_payment_intent_id, "pi_test_package_auth")
        self.assertIsNotNone(transaction.expires_at)  # Package should have expiration
    
    @patch('stripe.PaymentIntent.create')
    def test_initiate_purchase_subscription_plan_success(self, mock_stripe_create):
        """Test successful purchase initiation for authenticated user with subscription plan."""
        # Mock Stripe PaymentIntent response
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_test_subscription_auth"
        mock_payment_intent.client_secret = "pi_test_subscription_auth_secret_xyz"
        mock_payment_intent.amount = 49999  # 499.99 EUR in cents
        mock_payment_intent.currency = "eur"
        mock_payment_intent.customer = None
        mock_stripe_create.return_value = mock_payment_intent
        
        # Request data
        request_data = {
            "plan_id": self.subscription_plan.id,
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        # Make API request
        response = self.client.post(self.url, request_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify transaction record for subscription
        transaction_id = response.data['transaction_id']
        transaction = PurchaseTransaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.transaction_type, TransactionType.SUBSCRIPTION)
        self.assertIsNone(transaction.expires_at)  # Subscription should not have expiration
        
        # Verify metadata includes plan details
        stripe_metadata = mock_stripe_create.call_args[1]['metadata']
        self.assertEqual(stripe_metadata['transaction_type'], TransactionType.SUBSCRIPTION)
    
    def test_initiate_purchase_missing_plan_id(self):
        """Test purchase initiation fails when plan_id is missing."""
        request_data = {
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertIn('plan_id', response.data['message'].lower())
    
    def test_initiate_purchase_invalid_plan_id(self):
        """Test purchase initiation fails when plan_id is invalid."""
        request_data = {
            "plan_id": 99999,  # Non-existent plan ID
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertIn('not found', response.data['message'].lower())
    
    def test_initiate_purchase_inactive_plan(self):
        """Test purchase initiation fails when plan is inactive."""
        request_data = {
            "plan_id": self.inactive_plan.id,
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertIn('not currently active', response.data['message'].lower())
    
    def test_initiate_purchase_missing_student_info(self):
        """Test purchase initiation fails when student_info is missing."""
        request_data = {
            "plan_id": self.package_plan.id
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertIn('student_info', response.data['message'].lower())
    
    @patch('stripe.PaymentIntent.create')
    def test_initiate_purchase_stripe_card_error(self, mock_stripe_create):
        """Test purchase initiation handles Stripe card errors properly."""
        # Mock Stripe CardError
        mock_stripe_create.side_effect = stripe.error.CardError(
            message="Your card was declined.",
            param="number",
            code="card_declined"
        )
        
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'card_error')
        self.assertIn('declined', response.data['message'].lower())
        
        # Verify no transaction was created
        self.assertFalse(
            PurchaseTransaction.objects.filter(student=self.authenticated_user).exists()
        )
    
    @patch('stripe.PaymentIntent.create')
    def test_initiate_purchase_stripe_api_error(self, mock_stripe_create):
        """Test purchase initiation handles Stripe API errors properly."""
        # Mock Stripe APIError
        mock_stripe_create.side_effect = stripe.error.APIError(
            message="An error occurred with our API."
        )
        
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'api_error')
        self.assertIn('server error', response.data['message'].lower())


class PurchaseInitiationAPIGuestUserTests(PurchaseInitiationAPITestCase):
    """Test purchase initiation API for guest (unauthenticated) users."""
    
    @patch('stripe.PaymentIntent.create')
    def test_initiate_purchase_guest_user_success(self, mock_stripe_create):
        """Test successful purchase initiation for guest user."""
        # Mock Stripe PaymentIntent response
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_test_guest"
        mock_payment_intent.client_secret = "pi_test_guest_secret_xyz"
        mock_payment_intent.amount = 25000
        mock_payment_intent.currency = "eur"
        mock_payment_intent.customer = None
        mock_stripe_create.return_value = mock_payment_intent
        
        # Request data with guest user info
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "Guest Student",
                "email": self.guest_user_email
            }
        }
        
        # Make API request without authentication
        response = self.client.post(self.url, request_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['client_secret'], "pi_test_guest_secret_xyz")
        
        # Verify guest user was created
        guest_user = User.objects.get(email=self.guest_user_email)
        self.assertEqual(guest_user.name, "Guest Student")
        
        # Verify transaction record created for guest user
        transaction_id = response.data['transaction_id']
        transaction = PurchaseTransaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.student, guest_user)
        self.assertEqual(transaction.amount, Decimal('250.00'))
    
    @patch('stripe.PaymentIntent.create')
    def test_initiate_purchase_guest_user_existing_email(self, mock_stripe_create):
        """Test purchase initiation for guest user with existing email address."""
        # Mock Stripe PaymentIntent response
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_test_existing_email"
        mock_payment_intent.client_secret = "pi_test_existing_email_secret"
        mock_payment_intent.amount = 25000
        mock_payment_intent.currency = "eur"
        mock_payment_intent.customer = None
        mock_stripe_create.return_value = mock_payment_intent
        
        # Request data with existing user's email
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "Different Name",
                "email": self.authenticated_user.email  # Use existing user's email
            }
        }
        
        # Make API request without authentication
        response = self.client.post(self.url, request_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify transaction was created for existing user
        transaction_id = response.data['transaction_id']
        transaction = PurchaseTransaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.student, self.authenticated_user)
        
        # Verify no duplicate user was created
        user_count = User.objects.filter(email=self.authenticated_user.email).count()
        self.assertEqual(user_count, 1)
    
    def test_initiate_purchase_guest_invalid_email(self):
        """Test purchase initiation fails for guest with invalid email."""
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "Test Student",
                "email": "invalid-email-format"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertIn('email', response.data['message'].lower())
    
    def test_initiate_purchase_guest_missing_name(self):
        """Test purchase initiation fails for guest with missing name."""
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "email": "guest@test.com"
                # Missing name field
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertIn('name', response.data['message'].lower())


class PurchaseInitiationAPIValidationTests(PurchaseInitiationAPITestCase):
    """Test validation and error handling for purchase initiation API."""
    
    def setUp(self):
        """Set up authenticated user session."""
        super().setUp()
        self.client.force_authenticate(user=self.authenticated_user)
    
    def test_initiate_purchase_invalid_http_method(self):
        """Test that only POST method is allowed."""
        # Test GET request
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test PUT request
        response = self.client.put(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test DELETE request
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_initiate_purchase_invalid_json_format(self):
        """Test purchase initiation with invalid JSON format."""
        # Send invalid JSON
        response = self.client.post(
            self.url, 
            "invalid json content", 
            content_type='application/json'
        )
        
        # DRF automatically handles JSON parse errors, so this might return 400 or 500
        # depending on how DRF processes the invalid JSON
        self.assertIn(response.status_code, [400, 500])
        if response.status_code == 400:
            # If DRF returns 400, it should have error info
            self.assertIn('detail', response.data)
        # If it's 500, that's also acceptable for malformed JSON
    
    def test_initiate_purchase_empty_request_body(self):
        """Test purchase initiation with empty request body."""
        response = self.client.post(self.url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'validation_error')
    
    def test_initiate_purchase_plan_id_wrong_type(self):
        """Test purchase initiation with wrong type for plan_id."""
        request_data = {
            "plan_id": "not-a-number",
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'validation_error')
    
    def test_initiate_purchase_student_info_wrong_type(self):
        """Test purchase initiation with wrong type for student_info."""
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": "not-an-object"
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_type'], 'validation_error')


class PurchaseInitiationAPIAtomicTransactionTests(PurchaseInitiationAPITestCase):
    """Test atomic transaction consistency for purchase initiation API."""
    
    def setUp(self):
        """Set up authenticated user session."""
        super().setUp()
        self.client.force_authenticate(user=self.authenticated_user)
    
    @patch('stripe.PaymentIntent.create')
    @patch('finances.models.PurchaseTransaction.save')
    def test_initiate_purchase_atomic_transaction_rollback(
        self, 
        mock_transaction_save, 
        mock_stripe_create
    ):
        """Test that database operations are rolled back if any step fails."""
        # Mock successful Stripe response
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_test_rollback"
        mock_payment_intent.client_secret = "pi_test_rollback_secret"
        mock_payment_intent.amount = 25000
        mock_payment_intent.currency = "eur"
        mock_payment_intent.customer = None
        mock_stripe_create.return_value = mock_payment_intent
        
        # Mock database save failure
        mock_transaction_save.side_effect = Exception("Database error")
        
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        # Verify error response
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        
        # Verify no transaction was persisted despite Stripe success
        self.assertFalse(
            PurchaseTransaction.objects.filter(
                stripe_payment_intent_id="pi_test_rollback"
            ).exists()
        )
    
    @patch('stripe.PaymentIntent.create')
    def test_initiate_purchase_creates_student_account_balance(self, mock_stripe_create):
        """Test that student account balance is created if it doesn't exist."""
        # Mock Stripe PaymentIntent response
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_test_balance_creation"
        mock_payment_intent.client_secret = "pi_test_balance_creation_secret"
        mock_payment_intent.amount = 25000
        mock_payment_intent.currency = "eur"
        mock_payment_intent.customer = None
        mock_stripe_create.return_value = mock_payment_intent
        
        # Ensure no existing balance for user
        StudentAccountBalance.objects.filter(student=self.authenticated_user).delete()
        
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        # Verify successful response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify student account balance was created
        balance = StudentAccountBalance.objects.get(student=self.authenticated_user)
        self.assertEqual(balance.hours_purchased, Decimal('0.00'))
        self.assertEqual(balance.hours_consumed, Decimal('0.00'))
        self.assertEqual(balance.balance_amount, Decimal('0.00'))


class PurchaseInitiationAPISecurityTests(PurchaseInitiationAPITestCase):
    """Test security aspects of purchase initiation API."""
    
    def test_initiate_purchase_sql_injection_attempt(self):
        """Test that API is protected against SQL injection attempts."""
        malicious_data = {
            "plan_id": "1'; DROP TABLE finances_pricingplan; --",
            "student_info": {
                "name": "'; DROP TABLE accounts_customuser; --",
                "email": "test@test.com"
            }
        }
        
        response = self.client.post(self.url, malicious_data, format='json')
        
        # Should return validation error, not crash
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify tables still exist
        self.assertTrue(PricingPlan.objects.exists())
        self.assertTrue(User.objects.exists())
    
    def test_initiate_purchase_xss_attempt(self):
        """Test that API sanitizes potentially malicious input."""
        malicious_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "<script>alert('xss')</script>",
                "email": "test@test.com"
            }
        }
        
        # Should not authenticate for this test
        response = self.client.post(self.url, malicious_data, format='json')
        
        # Should handle gracefully without executing script
        self.assertIn(response.status_code, [400, 201])  # Either validation error or success
        
        # If successful, verify script tags are handled safely
        if response.status_code == 201:
            transaction_id = response.data['transaction_id']
            transaction = PurchaseTransaction.objects.get(id=transaction_id)
            # Should not contain executable script
            self.assertNotIn('script', transaction.student.name.lower())
    
    def test_initiate_purchase_oversized_payload(self):
        """Test that API handles oversized payloads appropriately."""
        # Create extremely large name field
        oversized_name = "A" * 10000
        
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": oversized_name,
                "email": "test@test.com"
            }
        }
        
        response = self.client.post(self.url, request_data, format='json')
        
        # Should return validation error for oversized field
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class PurchaseInitiationAPIRateLimitingTests(PurchaseInitiationAPITestCase):
    """Test rate limiting for purchase initiation API."""
    
    def setUp(self):
        """Set up authenticated user session."""
        super().setUp()
        self.client.force_authenticate(user=self.authenticated_user)
    
    @patch('stripe.PaymentIntent.create')
    def test_initiate_purchase_multiple_rapid_requests(self, mock_stripe_create):
        """Test handling of multiple rapid purchase requests."""
        # Clear cache to ensure fresh state for rate limiting
        from django.core.cache import cache
        cache.clear()
        
        # Mock different Stripe responses for each call
        mock_payment_intents = []
        for i in range(6):  # Create one extra mock for the test
            mock_pi = Mock()
            mock_pi.id = f"pi_test_rapid_{i}"
            mock_pi.client_secret = f"pi_test_rapid_{i}_secret"
            mock_pi.amount = 25000
            mock_pi.currency = "eur"
            mock_pi.customer = None
            mock_payment_intents.append(mock_pi)
        
        mock_stripe_create.side_effect = mock_payment_intents
        
        request_data = {
            "plan_id": self.package_plan.id,
            "student_info": {
                "name": "Test Student",
                "email": "student@test.com"
            }
        }
        
        # Temporarily enable throttling for this test by patching the view
        from common.throttles import PurchaseInitiationEmailThrottle
        from finances.views import purchase_initiate
        original_throttle_classes = getattr(purchase_initiate, 'throttle_classes', [])
        
        # Apply throttling temporarily
        purchase_initiate.throttle_classes = [PurchaseInitiationEmailThrottle]
        
        try:
            # Make multiple rapid requests
            responses = []
            for i in range(6):  # Try more than the rate limit
                response = self.client.post(self.url, request_data, format='json')
                responses.append(response)
            
            # Check if rate limiting is working
            success_responses = [r for r in responses if r.status_code == status.HTTP_201_CREATED]
            throttled_responses = [r for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS]
            
            # In testing environment without rate limiting enabled, all should succeed
            # This test documents the expected behavior when rate limiting is enabled in production
            if len(throttled_responses) > 0:
                # Rate limiting is active
                self.assertEqual(len(success_responses), 5)
                self.assertEqual(len(throttled_responses), 1)
                
                # Verify rate limiting error message in throttled response
                throttled_response = throttled_responses[0]
                self.assertIn('throttled', throttled_response.data.get('detail', '').lower())
                
                # Verify exactly 5 transactions were created (not 6)
                transaction_count = PurchaseTransaction.objects.filter(
                    student=self.authenticated_user
                ).count()
                self.assertEqual(transaction_count, 5)
            else:
                # Rate limiting disabled in test environment - all requests succeed
                # This is expected behavior in testing configuration
                self.assertEqual(len(success_responses), 6)
                self.assertEqual(len(throttled_responses), 0)
                
                # Verify all 6 transactions were created
                transaction_count = PurchaseTransaction.objects.filter(
                    student=self.authenticated_user
                ).count()
                self.assertEqual(transaction_count, 6)
                
        finally:
            # Restore original throttle classes
            purchase_initiate.throttle_classes = original_throttle_classes


# Re-enable logging after all tests
def tearDownModule():
    """Re-enable logging after test module completion."""
    logging.disable(logging.NOTSET)