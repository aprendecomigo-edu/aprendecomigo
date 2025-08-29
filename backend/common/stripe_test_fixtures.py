"""
Comprehensive Stripe API Test Fixtures and Mocks

This module provides realistic Stripe API response fixtures and mocking utilities
for testing the Aprende Comigo payment system. All fixtures are based on the
official Stripe API documentation and match actual response formats.

Key Features:
- Complete Stripe object mocks (PaymentIntent, Customer, PaymentMethod, etc.)
- Realistic response data that matches Stripe API v2023-10-16
- Error response fixtures for testing failure scenarios
- Centralized mock management for consistent testing
- PCI-compliant test data (no real card numbers)

Usage:
    from common.stripe_test_fixtures import StripeFixtures, mock_stripe_service
    
    # Use fixtures directly
    fixtures = StripeFixtures()
    payment_intent_data = fixtures.payment_intent_succeeded()
    
    # Use as decorator
    @mock_stripe_service
    def test_payment_flow(self):
        # All Stripe API calls are automatically mocked
        pass
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

import stripe
from django.conf import settings


class StripeFixtures:
    """
    Comprehensive Stripe API response fixtures based on official documentation.
    
    All fixtures represent realistic Stripe objects with proper field types,
    relationships, and data structures as defined in Stripe API v2023-10-16.
    """
    
    def __init__(self):
        """Initialize fixtures with base configuration."""
        self.base_timestamp = int(datetime.now().timestamp())
        self.base_url = "https://api.stripe.com/v1"
    
    def payment_intent_created(self, 
                              payment_intent_id: str = "pi_test_created",
                              amount: int = 2000,
                              currency: str = "eur",
                              customer_id: Optional[str] = None,
                              metadata: Optional[Dict[str, str]] = None) -> Mock:
        """
        Mock PaymentIntent in 'requires_payment_method' status.
        
        Represents a newly created PaymentIntent that needs a payment method
        to be attached before it can be confirmed.
        
        Args:
            payment_intent_id: Unique identifier for the PaymentIntent
            amount: Amount in cents (e.g., 2000 = €20.00)
            currency: Three-letter ISO currency code
            customer_id: Optional Stripe customer ID
            metadata: Optional key-value metadata
            
        Returns:
            Mock object representing a Stripe PaymentIntent
        """
        pi = Mock(spec=stripe.PaymentIntent)
        pi.id = payment_intent_id
        pi.object = "payment_intent"
        pi.amount = amount
        pi.currency = currency
        pi.status = "requires_payment_method"
        pi.client_secret = f"{payment_intent_id}_secret_test"
        pi.created = self.base_timestamp
        pi.customer = customer_id
        pi.metadata = metadata or {}
        pi.automatic_payment_methods = {"enabled": True}
        pi.payment_method = None
        pi.payment_method_types = ["card", "sepa_debit"]
        pi.confirmation_method = "automatic"
        pi.capture_method = "automatic"
        pi.livemode = False
        
        return pi
    
    def payment_intent_succeeded(self,
                                payment_intent_id: str = "pi_test_succeeded", 
                                amount: int = 2000,
                                currency: str = "eur",
                                payment_method_id: str = "pm_test_card",
                                customer_id: Optional[str] = None,
                                metadata: Optional[Dict[str, str]] = None) -> Mock:
        """
        Mock PaymentIntent in 'succeeded' status.
        
        Represents a successfully processed payment with complete payment details.
        
        Args:
            payment_intent_id: Unique identifier for the PaymentIntent
            amount: Amount in cents that was charged
            currency: Three-letter ISO currency code
            payment_method_id: ID of the payment method used
            customer_id: Optional Stripe customer ID
            metadata: Optional key-value metadata
            
        Returns:
            Mock object representing a successful Stripe PaymentIntent
        """
        pi = self.payment_intent_created(payment_intent_id, amount, currency, customer_id, metadata)
        pi.status = "succeeded"
        pi.payment_method = payment_method_id
        pi.amount_received = amount
        pi.charges = Mock()
        pi.charges.object = "list"
        pi.charges.data = [self.charge_succeeded(payment_intent_id, amount, payment_method_id)]
        
        return pi
    
    def charge_succeeded(self, 
                        payment_intent_id: str,
                        amount: int,
                        payment_method_id: str) -> Mock:
        """
        Mock Charge object for successful payment.
        
        Represents the actual charge that was processed as part of a PaymentIntent.
        """
        charge = Mock()
        charge.id = f"ch_test_{uuid4().hex[:16]}"
        charge.object = "charge"
        charge.amount = amount
        charge.captured = True
        charge.created = self.base_timestamp
        charge.currency = "eur"
        charge.paid = True
        charge.payment_intent = payment_intent_id
        charge.payment_method = payment_method_id
        charge.status = "succeeded"
        
        return charge
    
    def customer_created(self,
                        customer_id: str = "cus_test_customer",
                        email: str = "test@aprendecomigo.com", 
                        name: str = "Test Student",
                        metadata: Optional[Dict[str, str]] = None) -> Mock:
        """
        Mock Stripe Customer object.
        
        Represents a customer in Stripe with their basic information.
        
        Args:
            customer_id: Unique customer identifier
            email: Customer's email address
            name: Customer's full name
            metadata: Optional key-value metadata
            
        Returns:
            Mock object representing a Stripe Customer
        """
        customer = Mock(spec=stripe.Customer)
        customer.id = customer_id
        customer.object = "customer"
        customer.email = email
        customer.name = name
        customer.created = self.base_timestamp
        customer.metadata = metadata or {}
        customer.default_source = None
        customer.invoice_prefix = f"TEST{uuid4().hex[:4].upper()}"
        customer.livemode = False
        
        return customer
    
    def payment_method_card(self,
                           payment_method_id: str = "pm_test_card",
                           customer_id: Optional[str] = None,
                           card_brand: str = "visa",
                           card_last4: str = "4242",
                           exp_month: int = 12,
                           exp_year: int = 2025) -> Mock:
        """
        Mock PaymentMethod with card details.
        
        Represents a card payment method with PCI-compliant display data.
        
        Args:
            payment_method_id: Unique payment method identifier
            customer_id: ID of customer this payment method belongs to
            card_brand: Card brand (visa, mastercard, etc.)
            card_last4: Last 4 digits of card number
            exp_month: Expiration month (1-12)
            exp_year: Expiration year (4 digits)
            
        Returns:
            Mock object representing a Stripe PaymentMethod
        """
        pm = Mock(spec=stripe.PaymentMethod)
        pm.id = payment_method_id
        pm.object = "payment_method"
        pm.type = "card"
        pm.customer = customer_id
        pm.created = self.base_timestamp
        pm.livemode = False
        
        # Card details (PCI-compliant - only safe display data)
        pm.card = Mock()
        pm.card.brand = card_brand
        pm.card.last4 = card_last4
        pm.card.exp_month = exp_month
        pm.card.exp_year = exp_year
        pm.card.funding = "credit"
        pm.card.country = "PT"  # Portugal
        
        # Mock detach method for testing payment method removal
        def mock_detach():
            pm.customer = None
            return pm
        pm.detach = mock_detach
        
        # Mock attach method for testing payment method attachment
        def mock_attach(customer):
            pm.customer = customer
            return pm
        pm.attach = mock_attach
        
        return pm
    
    def payment_method_list(self, 
                           customer_id: str,
                           payment_methods: List[Mock]) -> Mock:
        """
        Mock PaymentMethod list response.
        
        Args:
            customer_id: Customer ID to list payment methods for
            payment_methods: List of payment method mocks
            
        Returns:
            Mock object representing Stripe list response
        """
        list_response = Mock()
        list_response.object = "list"
        list_response.data = payment_methods
        list_response.has_more = False
        list_response.url = f"/v1/payment_methods"
        
        return list_response
    
    def refund_created(self,
                      refund_id: str = "re_test_refund",
                      payment_intent_id: str = "pi_test_succeeded",
                      amount: int = 2000,
                      reason: str = "requested_by_customer") -> Mock:
        """
        Mock Refund object.
        
        Args:
            refund_id: Unique refund identifier  
            payment_intent_id: PaymentIntent being refunded
            amount: Amount to refund in cents
            reason: Reason for refund
            
        Returns:
            Mock object representing a Stripe Refund
        """
        refund = Mock(spec=stripe.Refund)
        refund.id = refund_id
        refund.object = "refund"
        refund.amount = amount
        refund.created = self.base_timestamp
        refund.currency = "eur"
        refund.payment_intent = payment_intent_id
        refund.reason = reason
        refund.status = "succeeded"
        
        return refund
    
    def account_test(self) -> Mock:
        """
        Mock Account object for API connection testing.
        
        Returns:
            Mock object representing a Stripe Account
        """
        account = Mock(spec=stripe.Account)
        account.id = "acct_test_aprende_comigo"
        account.object = "account"
        account.business_profile = Mock()
        account.business_profile.name = "Aprende Comigo Test"
        account.country = "PT"
        account.default_currency = "eur"
        account.type = "standard"
        
        return account
    
    def webhook_event(self,
                     event_type: str = "payment_intent.succeeded",
                     event_id: str = "evt_test_webhook",
                     data_object: Optional[Mock] = None) -> Mock:
        """
        Mock Webhook Event object.
        
        Args:
            event_type: Type of webhook event
            event_id: Unique event identifier
            data_object: The object that triggered the event
            
        Returns:
            Mock object representing a Stripe Event
        """
        event = Mock(spec=stripe.Event)
        event.id = event_id
        event.object = "event"
        event.type = event_type
        event.created = self.base_timestamp
        event.data = Mock()
        event.data.object = data_object or self.payment_intent_succeeded()
        event.livemode = False
        event.request = Mock()
        event.request.id = f"req_test_{uuid4().hex[:16]}"
        
        return event
    
    # Error response fixtures
    
    def stripe_card_error(self, 
                         code: str = "card_declined",
                         message: str = "Your card was declined.",
                         param: str = "number") -> stripe.error.CardError:
        """
        Mock Stripe CardError exception.
        
        Args:
            code: Stripe error code
            message: Human-readable error message
            param: Parameter that caused the error
            
        Returns:
            StripeError exception for testing error handling
        """
        return stripe.error.CardError(
            message=message,
            param=param,
            code=code,
            http_status=402
        )
    
    def stripe_authentication_error(self,
                                   message: str = "Invalid API Key provided") -> stripe.error.AuthenticationError:
        """
        Mock Stripe AuthenticationError exception.
        
        Returns:
            AuthenticationError for testing API key validation
        """
        return stripe.error.AuthenticationError(
            message=message,
            http_status=401
        )
    
    def stripe_api_error(self, 
                        message: str = "An error occurred with our API.") -> stripe.error.APIError:
        """
        Mock generic Stripe API error.
        
        Returns:
            APIError for testing general API failures
        """
        return stripe.error.APIError(
            message=message,
            http_status=500
        )


class StripeServiceMocker:
    """
    Centralized Stripe API mocking system.
    
    Provides automatic mocking of all Stripe API calls with realistic responses
    that match the business logic expectations of our payment services.
    """
    
    def __init__(self):
        """Initialize mocker with default fixtures."""
        self.fixtures = StripeFixtures()
        self.active_patches = []
    
    def start_mocking(self):
        """
        Start comprehensive Stripe API mocking.
        
        Patches all Stripe API methods used by the application with
        realistic mock responses.
        """
        # Patch stripe.api_key to prevent real API key assignment
        api_key_patch = patch.object(stripe, 'api_key', 'sk_test_mocked_key')
        
        # PaymentIntent mocks
        pi_create_patch = patch('stripe.PaymentIntent.create')
        pi_retrieve_patch = patch('stripe.PaymentIntent.retrieve')  
        pi_confirm_patch = patch('stripe.PaymentIntent.confirm')
        
        # Customer mocks
        customer_create_patch = patch('stripe.Customer.create')
        customer_retrieve_patch = patch('stripe.Customer.retrieve')
        customer_modify_patch = patch('stripe.Customer.modify')
        
        # PaymentMethod mocks  
        pm_retrieve_patch = patch('stripe.PaymentMethod.retrieve')
        pm_list_patch = patch('stripe.PaymentMethod.list')
        pm_detach_patch = patch('stripe.PaymentMethod.detach')
        pm_attach_patch = patch('stripe.PaymentMethod.attach')
        
        # Refund mocks
        refund_create_patch = patch('stripe.Refund.create')
        refund_retrieve_patch = patch('stripe.Refund.retrieve')
        refund_list_patch = patch('stripe.Refund.list')
        
        # Account mock
        account_retrieve_patch = patch('stripe.Account.retrieve')
        
        # Webhook mock
        webhook_construct_patch = patch('stripe.Webhook.construct_event')
        
        # Start all patches
        api_key_patch.start()  # Start the API key patch
        mock_pi_create = pi_create_patch.start()
        mock_pi_retrieve = pi_retrieve_patch.start()
        mock_pi_confirm = pi_confirm_patch.start()
        
        mock_customer_create = customer_create_patch.start()
        mock_customer_retrieve = customer_retrieve_patch.start()
        mock_customer_modify = customer_modify_patch.start()
        
        mock_pm_retrieve = pm_retrieve_patch.start()
        mock_pm_list = pm_list_patch.start()
        mock_pm_detach = pm_detach_patch.start()
        mock_pm_attach = pm_attach_patch.start()
        
        mock_refund_create = refund_create_patch.start()
        mock_refund_retrieve = refund_retrieve_patch.start()
        mock_refund_list = refund_list_patch.start()
        
        mock_account_retrieve = account_retrieve_patch.start()
        mock_webhook_construct = webhook_construct_patch.start()
        
        # Configure realistic return values
        mock_pi_create.return_value = self.fixtures.payment_intent_created()
        mock_pi_retrieve.return_value = self.fixtures.payment_intent_succeeded()
        mock_pi_confirm.return_value = self.fixtures.payment_intent_succeeded()
        
        mock_customer_create.return_value = self.fixtures.customer_created()
        mock_customer_retrieve.return_value = self.fixtures.customer_created()
        mock_customer_modify.return_value = self.fixtures.customer_created()
        
        mock_pm_retrieve.return_value = self.fixtures.payment_method_card()
        mock_pm_list.return_value = self.fixtures.payment_method_list(
            "cus_test_customer", 
            [self.fixtures.payment_method_card()]
        )
        mock_pm_detach.return_value = self.fixtures.payment_method_card()
        mock_pm_attach.return_value = self.fixtures.payment_method_card()
        
        mock_refund_create.return_value = self.fixtures.refund_created()
        mock_refund_retrieve.return_value = self.fixtures.refund_created()  
        mock_refund_list.return_value = Mock(data=[self.fixtures.refund_created()])
        
        mock_account_retrieve.return_value = self.fixtures.account_test()
        mock_webhook_construct.return_value = self.fixtures.webhook_event()
        
        # Store patches for cleanup
        self.active_patches = [
            api_key_patch,
            pi_create_patch, pi_retrieve_patch, pi_confirm_patch,
            customer_create_patch, customer_retrieve_patch, customer_modify_patch,
            pm_retrieve_patch, pm_list_patch, pm_detach_patch, pm_attach_patch,
            refund_create_patch, refund_retrieve_patch, refund_list_patch,
            account_retrieve_patch, webhook_construct_patch
        ]
        
        return {
            'payment_intent_create': mock_pi_create,
            'payment_intent_retrieve': mock_pi_retrieve,
            'payment_intent_confirm': mock_pi_confirm,
            'customer_create': mock_customer_create,
            'customer_retrieve': mock_customer_retrieve,
            'customer_modify': mock_customer_modify,
            'payment_method_retrieve': mock_pm_retrieve,
            'payment_method_list': mock_pm_list,
            'payment_method_detach': mock_pm_detach,
            'payment_method_attach': mock_pm_attach,
            'refund_create': mock_refund_create,
            'refund_retrieve': mock_refund_retrieve,
            'refund_list': mock_refund_list,
            'account_retrieve': mock_account_retrieve,
            'webhook_construct': mock_webhook_construct,
        }
    
    def stop_mocking(self):
        """Stop all active Stripe API mocking."""
        for patch_obj in self.active_patches:
            patch_obj.stop()
        self.active_patches = []
    
    def configure_specific_responses(self, **mock_configs):
        """
        Configure specific mock responses for custom test scenarios.
        
        Args:
            **mock_configs: Dictionary of mock configurations
                Example: payment_intent_create={'side_effect': StripeError}
        """
        # This would be implemented to allow per-test customization
        pass


def mock_stripe_service(test_func):
    """
    Decorator to automatically mock all Stripe API calls for a test.
    
    Usage:
        @mock_stripe_service
        def test_payment_flow(self):
            # All Stripe API calls are mocked with realistic responses
            result = payment_service.create_payment_intent(...)
            self.assertTrue(result['success'])
    """
    def wrapper(*args, **kwargs):
        mocker = StripeServiceMocker()
        try:
            mocker.start_mocking()
            return test_func(*args, **kwargs)
        finally:
            mocker.stop_mocking()
    
    return wrapper


# Global instance for easy access
stripe_fixtures = StripeFixtures()