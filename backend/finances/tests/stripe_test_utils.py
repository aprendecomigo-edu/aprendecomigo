"""
Stripe Testing Utilities

This module provides comprehensive mocking utilities for Stripe API calls
in tests, preventing external API requests and rate limiting issues.

Usage:
    from finances.tests.stripe_test_utils import StripeTestMixin

    class MyTestCase(StripeTestMixin, TestCase):
        def setUp(self):
            super().setUp()
            self.setup_stripe_mocks()

        def test_my_function(self):
            # Stripe calls will be automatically mocked
            pass
"""

from contextlib import contextmanager, suppress
from decimal import Decimal
from functools import wraps
import json
from typing import Any
from unittest.mock import Mock, patch

from django.test import TestCase
import stripe


class MockStripeObject(Mock):
    """Enhanced Mock object that behaves more like Stripe objects."""

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        """Convert to dictionary like real Stripe objects."""
        return {key: getattr(self, key) for key in dir(self) if not key.startswith("_")}


class MockPaymentIntent(MockStripeObject):
    """Mock Stripe PaymentIntent object."""

    def __init__(
        self,
        id: str = "pi_test_mock",
        amount: int = 25000,
        currency: str = "eur",
        status: str = "requires_payment_method",
        client_secret: str | None = None,
        customer: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.id = id
        self.object = "payment_intent"
        self.amount = amount
        self.currency = currency
        self.status = status
        self.client_secret = client_secret or f"{id}_secret"
        self.customer = customer
        self.metadata = metadata or {}
        self.automatic_payment_methods = {"enabled": True}
        self.created = 1234567890
        self.livemode = False


class MockPaymentMethod(MockStripeObject):
    """Mock Stripe PaymentMethod object."""

    def __init__(
        self,
        id: str = "pm_test_mock",
        type: str = "card",
        card: dict[str, Any] | None = None,
        customer: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.id = id
        self.object = "payment_method"
        self.type = type
        self.customer = customer
        self.card = card or {"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2025, "funding": "credit"}
        self.created = 1234567890
        self.livemode = False


class MockCustomer(MockStripeObject):
    """Mock Stripe Customer object."""

    def __init__(
        self, id: str = "cus_test_mock", email: str = "test@example.com", name: str = "Test Customer", **kwargs
    ):
        super().__init__(**kwargs)
        self.id = id
        self.object = "customer"
        self.email = email
        self.name = name
        self.created = 1234567890
        self.livemode = False
        self.default_source = None
        self.invoice_prefix = "TEST"


class MockChargeOutcome(MockStripeObject):
    """Mock Stripe Charge outcome object."""

    def __init__(
        self,
        network_status="approved_by_network",
        reason=None,
        risk_level="normal",
        seller_message="Payment complete.",
        type="authorized",
    ):
        super().__init__()
        self.network_status = network_status
        self.reason = reason
        self.risk_level = risk_level
        self.seller_message = seller_message
        self.type = type


class MockCharge(MockStripeObject):
    """Mock Stripe Charge object."""

    def __init__(
        self,
        id: str = "ch_test_mock",
        amount: int = 25000,
        currency: str = "eur",
        status: str = "succeeded",
        payment_intent: str = "pi_test_mock",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.id = id
        self.object = "charge"
        self.amount = amount
        self.currency = currency
        self.status = status
        self.payment_intent = payment_intent
        self.paid = status == "succeeded"
        self.refunded = False
        self.outcome = MockChargeOutcome()
        self.created = 1234567890
        self.livemode = False


class MockInvoice(MockStripeObject):
    """Mock Stripe Invoice object."""

    def __init__(
        self,
        id: str = "in_test_mock",
        amount_due: int = 25000,
        currency: str = "eur",
        status: str = "draft",
        customer: str = "cus_test_mock",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.id = id
        self.object = "invoice"
        self.amount_due = amount_due
        self.currency = currency
        self.status = status
        self.customer = customer
        self.created = 1234567890
        self.livemode = False


class MockRefund(MockStripeObject):
    """Mock Stripe Refund object."""

    def __init__(
        self,
        id: str = "re_test_mock",
        amount: int = 25000,
        currency: str = "eur",
        status: str = "succeeded",
        charge: str = "ch_test_mock",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.id = id
        self.object = "refund"
        self.amount = amount
        self.currency = currency
        self.status = status
        self.charge = charge
        self.created = 1234567890


class StripeTestMixin:
    """
    Mixin class that provides comprehensive Stripe API mocking.

    This mixin patches all common Stripe API calls to return mock objects
    instead of making actual HTTP requests to Stripe's API.
    """

    def setup_stripe_mocks(self):
        """Set up comprehensive Stripe API mocks."""
        self._stripe_patchers = []
        self._mock_stripe_objects = {}

        # Mock Stripe API key settings
        self._patch_stripe_settings()

        # Mock PaymentIntent operations
        self._setup_payment_intent_mocks()

        # Mock PaymentMethod operations
        self._setup_payment_method_mocks()

        # Mock Customer operations
        self._setup_customer_mocks()

        # Mock Charge operations
        self._setup_charge_mocks()

        # Mock Invoice operations
        self._setup_invoice_mocks()

        # Mock Refund operations
        self._setup_refund_mocks()

        # Mock WebHook operations
        self._setup_webhook_mocks()

        # Start all patchers
        self._start_patchers()

    def teardown_stripe_mocks(self):
        """Clean up all Stripe mocks."""
        for patcher in self._stripe_patchers:
            try:
                patcher.stop()
            except RuntimeError:
                # Patcher was not started or already stopped
                pass
        self._stripe_patchers.clear()
        self._mock_stripe_objects.clear()

    def _patch_stripe_settings(self):
        """Patch Django settings for Stripe configuration."""
        settings_patcher = patch.multiple(
            "django.conf.settings",
            STRIPE_SECRET_KEY="sk_test_mock_key",
            STRIPE_PUBLIC_KEY="pk_test_mock_key",
            STRIPE_WEBHOOK_SECRET="whsec_test_mock_secret",
        )
        self._stripe_patchers.append(settings_patcher)

        # Patch StripeService to prevent configuration validation during tests
        stripe_service_init_patcher = patch("finances.services.stripe_base.StripeService.__init__")
        self._stripe_patchers.append(stripe_service_init_patcher)

        # Patch PaymentMethodService to prevent StripeService instantiation
        payment_method_service_init_patcher = patch(
            "finances.services.payment_method_service.PaymentMethodService.__init__"
        )
        self._stripe_patchers.append(payment_method_service_init_patcher)

    def _setup_payment_intent_mocks(self):
        """Set up PaymentIntent API mocks."""
        # PaymentIntent.create
        create_patcher = patch("stripe.PaymentIntent.create")
        self._stripe_patchers.append(create_patcher)
        self.mock_payment_intent_create = create_patcher

        # PaymentIntent.retrieve
        retrieve_patcher = patch("stripe.PaymentIntent.retrieve")
        self._stripe_patchers.append(retrieve_patcher)
        self.mock_payment_intent_retrieve = retrieve_patcher

        # PaymentIntent.modify
        modify_patcher = patch("stripe.PaymentIntent.modify")
        self._stripe_patchers.append(modify_patcher)
        self.mock_payment_intent_modify = modify_patcher

        # PaymentIntent.confirm
        confirm_patcher = patch("stripe.PaymentIntent.confirm")
        self._stripe_patchers.append(confirm_patcher)
        self.mock_payment_intent_confirm = confirm_patcher

        # PaymentIntent.cancel
        cancel_patcher = patch("stripe.PaymentIntent.cancel")
        self._stripe_patchers.append(cancel_patcher)
        self.mock_payment_intent_cancel = cancel_patcher

    def _setup_payment_method_mocks(self):
        """Set up PaymentMethod API mocks."""
        # PaymentMethod.create
        create_patcher = patch("stripe.PaymentMethod.create")
        self._stripe_patchers.append(create_patcher)
        self.mock_payment_method_create = create_patcher

        # PaymentMethod.retrieve
        retrieve_patcher = patch("stripe.PaymentMethod.retrieve")
        self._stripe_patchers.append(retrieve_patcher)
        self.mock_payment_method_retrieve = retrieve_patcher

        # PaymentMethod.attach
        attach_patcher = patch("stripe.PaymentMethod.attach")
        self._stripe_patchers.append(attach_patcher)
        self.mock_payment_method_attach = attach_patcher

        # PaymentMethod.detach
        detach_patcher = patch("stripe.PaymentMethod.detach")
        self._stripe_patchers.append(detach_patcher)
        self.mock_payment_method_detach = detach_patcher

    def _setup_customer_mocks(self):
        """Set up Customer API mocks."""
        # Customer.create
        create_patcher = patch("stripe.Customer.create")
        self._stripe_patchers.append(create_patcher)
        self.mock_customer_create = create_patcher

        # Customer.retrieve
        retrieve_patcher = patch("stripe.Customer.retrieve")
        self._stripe_patchers.append(retrieve_patcher)
        self.mock_customer_retrieve = retrieve_patcher

        # Customer.modify
        modify_patcher = patch("stripe.Customer.modify")
        self._stripe_patchers.append(modify_patcher)
        self.mock_customer_modify = modify_patcher

        # Customer.delete
        delete_patcher = patch("stripe.Customer.delete")
        self._stripe_patchers.append(delete_patcher)
        self.mock_customer_delete = delete_patcher

    def _setup_charge_mocks(self):
        """Set up Charge API mocks."""
        # Charge.create
        create_patcher = patch("stripe.Charge.create")
        self._stripe_patchers.append(create_patcher)
        self.mock_charge_create = create_patcher

        # Charge.retrieve
        retrieve_patcher = patch("stripe.Charge.retrieve")
        self._stripe_patchers.append(retrieve_patcher)
        self.mock_charge_retrieve = retrieve_patcher

    def _setup_invoice_mocks(self):
        """Set up Invoice API mocks."""
        # Invoice.create
        create_patcher = patch("stripe.Invoice.create")
        self._stripe_patchers.append(create_patcher)
        self.mock_invoice_create = create_patcher

        # Invoice.retrieve
        retrieve_patcher = patch("stripe.Invoice.retrieve")
        self._stripe_patchers.append(retrieve_patcher)
        self.mock_invoice_retrieve = retrieve_patcher

        # Invoice.finalize_invoice
        finalize_patcher = patch("stripe.Invoice.finalize_invoice")
        self._stripe_patchers.append(finalize_patcher)
        self.mock_invoice_finalize = finalize_patcher

    def _setup_refund_mocks(self):
        """Set up Refund API mocks."""
        # Refund.create
        create_patcher = patch("stripe.Refund.create")
        self._stripe_patchers.append(create_patcher)
        self.mock_refund_create = create_patcher

        # Refund.retrieve
        retrieve_patcher = patch("stripe.Refund.retrieve")
        self._stripe_patchers.append(retrieve_patcher)
        self.mock_refund_retrieve = retrieve_patcher

    def _setup_webhook_mocks(self):
        """Set up Webhook API mocks."""
        # Webhook.construct_event
        construct_patcher = patch("stripe.Webhook.construct_event")
        self._stripe_patchers.append(construct_patcher)
        self.mock_webhook_construct = construct_patcher

    def _start_patchers(self):
        """Start all patchers and configure default return values."""
        # Start StripeService mock (index 1 after settings patch)
        self.mock_stripe_service_init_obj = self._stripe_patchers[1].start()

        # Start PaymentMethodService mock (index 2)
        self.mock_payment_method_service_init_obj = self._stripe_patchers[2].start()

        # Start PaymentIntent mocks
        self.mock_payment_intent_create_obj = self.mock_payment_intent_create.start()
        self.mock_payment_intent_retrieve_obj = self.mock_payment_intent_retrieve.start()
        self.mock_payment_intent_modify_obj = self.mock_payment_intent_modify.start()
        self.mock_payment_intent_confirm_obj = self.mock_payment_intent_confirm.start()
        self.mock_payment_intent_cancel_obj = self.mock_payment_intent_cancel.start()

        # Start PaymentMethod mocks
        self.mock_payment_method_create_obj = self.mock_payment_method_create.start()
        self.mock_payment_method_retrieve_obj = self.mock_payment_method_retrieve.start()
        self.mock_payment_method_attach_obj = self.mock_payment_method_attach.start()
        self.mock_payment_method_detach_obj = self.mock_payment_method_detach.start()

        # Start Customer mocks
        self.mock_customer_create_obj = self.mock_customer_create.start()
        self.mock_customer_retrieve_obj = self.mock_customer_retrieve.start()
        self.mock_customer_modify_obj = self.mock_customer_modify.start()
        self.mock_customer_delete_obj = self.mock_customer_delete.start()

        # Start Charge mocks
        self.mock_charge_create_obj = self.mock_charge_create.start()
        self.mock_charge_retrieve_obj = self.mock_charge_retrieve.start()

        # Start Invoice mocks
        self.mock_invoice_create_obj = self.mock_invoice_create.start()
        self.mock_invoice_retrieve_obj = self.mock_invoice_retrieve.start()
        self.mock_invoice_finalize_obj = self.mock_invoice_finalize.start()

        # Start Refund mocks
        self.mock_refund_create_obj = self.mock_refund_create.start()
        self.mock_refund_retrieve_obj = self.mock_refund_retrieve.start()

        # Start Webhook mocks
        self.mock_webhook_construct_obj = self.mock_webhook_construct.start()

        # Configure default return values
        self._configure_default_responses()

    def _configure_default_responses(self):
        """Configure default responses for all mock objects."""
        # Configure StripeService mock - make __init__ do nothing
        self.mock_stripe_service_init_obj.return_value = None

        # Configure PaymentMethodService mock - make __init__ do nothing
        self.mock_payment_method_service_init_obj.return_value = None

        # PaymentIntent defaults
        self.mock_payment_intent_create_obj.return_value = MockPaymentIntent()
        self.mock_payment_intent_retrieve_obj.return_value = MockPaymentIntent()
        self.mock_payment_intent_modify_obj.return_value = MockPaymentIntent()
        self.mock_payment_intent_confirm_obj.return_value = MockPaymentIntent(status="succeeded")
        self.mock_payment_intent_cancel_obj.return_value = MockPaymentIntent(status="canceled")

        # PaymentMethod defaults
        self.mock_payment_method_create_obj.return_value = MockPaymentMethod()
        self.mock_payment_method_retrieve_obj.return_value = MockPaymentMethod()
        self.mock_payment_method_attach_obj.return_value = MockPaymentMethod(customer="cus_test_mock")
        self.mock_payment_method_detach_obj.return_value = MockPaymentMethod(customer=None)

        # Customer defaults
        self.mock_customer_create_obj.return_value = MockCustomer()
        self.mock_customer_retrieve_obj.return_value = MockCustomer()
        self.mock_customer_modify_obj.return_value = MockCustomer()
        self.mock_customer_delete_obj.return_value = {"id": "cus_test_mock", "deleted": True}

        # Charge defaults
        self.mock_charge_create_obj.return_value = MockCharge()
        self.mock_charge_retrieve_obj.return_value = MockCharge()

        # Invoice defaults
        self.mock_invoice_create_obj.return_value = MockInvoice()
        self.mock_invoice_retrieve_obj.return_value = MockInvoice()
        self.mock_invoice_finalize_obj.return_value = MockInvoice(status="open")

        # Refund defaults
        self.mock_refund_create_obj.return_value = MockRefund()
        self.mock_refund_retrieve_obj.return_value = MockRefund()

        # Webhook defaults
        self.mock_webhook_construct_obj.return_value = {
            "id": "evt_test_mock",
            "type": "payment_intent.succeeded",
            "data": {"object": MockPaymentIntent(status="succeeded").to_dict()},
        }

    def create_mock_payment_intent(self, **kwargs) -> MockPaymentIntent:
        """Create a mock PaymentIntent with custom attributes."""
        return MockPaymentIntent(**kwargs)

    def create_mock_payment_method(self, **kwargs) -> MockPaymentMethod:
        """Create a mock PaymentMethod with custom attributes."""
        return MockPaymentMethod(**kwargs)

    def create_mock_customer(self, **kwargs) -> MockCustomer:
        """Create a mock Customer with custom attributes."""
        return MockCustomer(**kwargs)

    def create_mock_payment_method(self, **kwargs) -> MockPaymentMethod:  # type: ignore[no-redef]
        """Create a mock PaymentMethod with custom attributes."""
        return MockPaymentMethod(**kwargs)

    def create_mock_payment_intent(self, **kwargs) -> MockPaymentIntent:  # type: ignore[no-redef]
        """Create a mock PaymentIntent with custom attributes."""
        return MockPaymentIntent(**kwargs)

    def simulate_stripe_error(self, error_type: str = "CardError", message: str = "Your card was declined."):
        """Configure mocks to simulate Stripe errors."""
        if error_type == "CardError":
            error = stripe.error.CardError(message=message, param="number", code="card_declined")  # type: ignore[attr-defined]
        elif error_type == "APIError":
            error = stripe.error.APIError(message=message)  # type: ignore[attr-defined]
        elif error_type == "RateLimitError":
            error = stripe.error.RateLimitError(message="Too many requests")  # type: ignore[attr-defined]
        else:
            error = stripe.error.StripeError(message=message)  # type: ignore[attr-defined]

        # Configure all create operations to raise the error
        self.mock_payment_intent_create_obj.side_effect = error
        self.mock_payment_method_create_obj.side_effect = error
        self.mock_customer_create_obj.side_effect = error

        return error


class MockStripeServiceInstance:
    """
    Mock instance of StripeService that provides all methods with realistic return values.

    This class replaces StripeService instances during tests to prevent actual
    Stripe API calls and configuration validation.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mock service without any validation."""
        pass

    def retrieve_payment_method(self, payment_method_id: str) -> dict[str, Any]:
        """Mock payment method retrieval."""
        return {
            "success": True,
            "payment_method": {
                "id": payment_method_id,
                "type": "card",
                "card": {"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2025},
            },
            "message": "Payment method retrieved successfully",
        }

    def create_customer(self, email: str, name: str, metadata: dict[str, str] | None = None) -> dict[str, Any]:
        """Mock customer creation."""
        return {
            "success": True,
            "customer": MockCustomer(email=email, name=name),
            "customer_id": "cus_mock_test_123",
            "message": "Customer created successfully",
        }

    def retrieve_customer(self, customer_id: str) -> dict[str, Any]:
        """Mock customer retrieval."""
        return {"success": True, "customer": MockCustomer(id=customer_id), "message": "Customer retrieved successfully"}

    def attach_payment_method_to_customer(self, payment_method_id: str, customer_id: str) -> dict[str, Any]:
        """Mock payment method attachment."""
        return {
            "success": True,
            "payment_method": MockPaymentMethod(id=payment_method_id, customer=customer_id),
            "message": "Payment method attached successfully",
        }

    def detach_payment_method(self, payment_method_id: str) -> dict[str, Any]:
        """Mock payment method detachment."""
        return {"success": True, "message": "Payment method detached successfully"}

    def handle_stripe_error(self, error: Exception) -> dict[str, Any]:
        """Mock error handling."""
        return {"success": False, "error_type": "mock_error", "message": "Mock error for testing"}

    def get_public_key(self) -> str:
        """Mock public key retrieval."""
        return "pk_test_mock_key"

    def get_webhook_secret(self) -> str:
        """Mock webhook secret retrieval."""
        return "whsec_test_mock_secret"

    def construct_webhook_event(self, payload: str, sig_header: str) -> dict[str, Any]:
        """
        Mock webhook event construction for testing.

        This method simulates the behavior of the real StripeService.construct_webhook_event()
        method, returning a mock event structure that webhook tests can use.

        Args:
            payload: The raw webhook payload (JSON string)
            sig_header: The Stripe signature header

        Returns:
            Dict containing success status and mock event data
        """

        try:
            # Parse the payload to get event data
            event_data = json.loads(payload)

            # Return successful mock response with the parsed event
            return {
                "success": True,
                "event": event_data,
                "event_type": event_data.get("type"),
                "event_id": event_data.get("id", "evt_test_mock"),
            }

        except json.JSONDecodeError:
            # Return error for invalid JSON payload
            return {"success": False, "error_type": "invalid_payload", "message": "Invalid JSON payload"}
        except Exception as e:
            # Return general error for other issues
            return {
                "success": False,
                "error_type": "construction_error",
                "message": f"Mock webhook construction error: {e!s}",
            }

    def is_webhook_event_type_supported(self, event_type: str) -> bool:
        """
        Mock webhook event type support check.

        Returns True for the same event types that the real StripeService supports.

        Args:
            event_type: The webhook event type to check

        Returns:
            bool: True if the event type is supported
        """
        # Match the SUPPORTED_WEBHOOK_EVENTS from the real StripeService
        supported_events = {
            "payment_intent.succeeded",
            "payment_intent.payment_failed",
            "payment_intent.created",
            "payment_intent.canceled",
            "customer.created",
            "customer.updated",
            "payment_method.attached",
        }
        return event_type in supported_events


class MockPaymentMethodServiceInstance:
    """
    Mock instance of PaymentMethodService with realistic return values.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mock service without StripeService dependency."""
        self.stripe_service = MockStripeServiceInstance()

    def add_payment_method(
        self, student_user, stripe_payment_method_id: str, is_default: bool = False, auto_create_customer: bool = True
    ) -> dict[str, Any]:
        """Mock payment method addition."""
        return {
            "success": True,
            "payment_method_id": 1,
            "card_display": "Visa ending in 4242",
            "is_default": is_default,
            "stripe_customer_id": "cus_mock_test_123",
            "message": "Payment method added successfully",
        }

    def remove_payment_method(self, student_user, payment_method_id: int) -> dict[str, Any]:
        """Mock payment method removal."""
        # Support dynamic test data configuration for error scenarios
        if hasattr(self.__class__, "_remove_error_data"):
            result = self.__class__._remove_error_data.copy()
            # Clear test data after use for isolation
            delattr(self.__class__, "_remove_error_data")
            return result  # type: ignore[no-any-return]

        return {"success": True, "message": "Payment method removed successfully", "was_default": False}

    def list_payment_methods(self, student_user, include_expired: bool = False) -> dict[str, Any]:
        """Mock payment method listing."""
        # Support dynamic test data configuration
        if hasattr(self.__class__, "_test_data"):
            result = {
                "success": True,
                "payment_methods": self.__class__._test_data.get("payment_methods", []),
                "count": self.__class__._test_data.get("count", 0),
            }
            # Clear test data after use for isolation
            delattr(self.__class__, "_test_data")
            return result

        return {"success": True, "payment_methods": [], "count": 0}

    def set_default_payment_method(self, student_user, payment_method_id: int) -> dict[str, Any]:
        """Mock setting default payment method."""
        return {"success": True, "message": "Default payment method updated successfully"}

    def get_default_payment_method(self, student_user):
        """Mock getting default payment method."""
        return None

    def cleanup_expired_payment_methods(self, student_user=None) -> dict[str, Any]:
        """Mock cleanup of expired payment methods."""
        return {"success": True, "expired_count": 0, "message": "Cleaned up 0 expired payment methods"}


class MockPaymentServiceInstance:
    """
    Mock instance of PaymentService with realistic return values.
    """

    _instance = None
    _global_simulate_error = False
    _global_error_response = {
        "success": False,
        "error_type": "stripe_error",
        "message": "Mock Stripe error for testing",
    }

    def __init__(self, *args, **kwargs):
        """Initialize mock service without dependencies."""
        self.stripe_service = MockStripeServiceInstance()
        # Store reference to this instance for test access
        MockPaymentServiceInstance._instance = self

    @classmethod
    def get_current_instance(cls):
        """Get the current mock instance for configuration."""
        return cls._instance

    @classmethod
    def simulate_stripe_error(cls, error_type="stripe_error", message="Mock Stripe error for testing"):
        """Configure error simulation for all future instances."""
        cls._global_simulate_error = True
        cls._global_error_response = {"success": False, "error_type": error_type, "message": message}

    @classmethod
    def reset_error_simulation(cls):
        """Reset error simulation back to normal operation."""
        cls._global_simulate_error = False

    def process_payment(self, student_user, plan_id: int, payment_method_id: int | None = None) -> dict[str, Any]:
        """Mock payment processing."""
        return {
            "success": True,
            "payment_intent_id": "pi_mock_payment_123",
            "client_secret": "pi_mock_payment_123_secret",
            "transaction_id": 12345,
            "amount_paid": 250.0,
            "message": "Payment processed successfully",
        }

    def create_payment_intent(
        self, user, pricing_plan_id: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Mock payment intent creation with correct signature."""
        # Check if we should simulate an error
        if self._global_simulate_error:
            return self._global_error_response

        # Create a real transaction in the database for the test
        from finances.models import PricingPlan, PurchaseTransaction, TransactionPaymentStatus, TransactionType

        try:
            pricing_plan = PricingPlan.objects.get(id=int(pricing_plan_id))
        except PricingPlan.DoesNotExist:
            return {
                "success": False,
                "error_type": "validation_error",
                "message": f"Pricing plan with ID {pricing_plan_id} not found",
            }

        # Import the model constants
        from finances.models import PlanType

        # Create a mock transaction
        transaction = PurchaseTransaction.objects.create(
            student=user,
            transaction_type=TransactionType.PACKAGE
            if pricing_plan.plan_type == PlanType.PACKAGE
            else TransactionType.SUBSCRIPTION,
            amount=pricing_plan.price_eur,
            payment_status=TransactionPaymentStatus.PROCESSING,
            stripe_payment_intent_id="pi_mock_payment_123",
            stripe_customer_id=getattr(user, "stripe_customer_id", None) or "cus_mock_test_123",
        )

        return {
            "success": True,
            "client_secret": "pi_mock_payment_intent_secret",
            "transaction_id": transaction.id,
            "payment_intent_id": "pi_mock_payment_123",
        }

    def confirm_payment_completion(self, payment_intent_id: str) -> dict[str, Any]:
        """Mock payment completion confirmation with actual database updates."""
        try:
            from decimal import Decimal

            from finances.models import PurchaseTransaction, StudentAccountBalance, TransactionPaymentStatus

            # Find transaction by payment intent ID
            try:
                transaction = PurchaseTransaction.objects.get(stripe_payment_intent_id=payment_intent_id)
            except PurchaseTransaction.DoesNotExist:
                return {
                    "success": False,
                    "error_type": "transaction_not_found",
                    "message": "Transaction not found for payment intent ID",
                }

            # Check if already completed (idempotency)
            if transaction.payment_status == TransactionPaymentStatus.COMPLETED:
                return {
                    "success": True,
                    "payment_intent_id": payment_intent_id,
                    "transaction_id": transaction.id,
                    "message": "Payment already completed (idempotent)",
                    "error_type": "invalid_transaction_state",
                }

            # Update transaction status to completed
            transaction.payment_status = TransactionPaymentStatus.COMPLETED
            transaction.save()

            # Credit hours to student account (simplified mock logic)
            student_balance, created = StudentAccountBalance.objects.get_or_create(
                student=transaction.student,
                defaults={
                    "hours_purchased": Decimal("0.00"),
                    "hours_consumed": Decimal("0.00"),
                    "balance_amount": Decimal("0.00"),
                },
            )

            # For mock purposes, just add some hours (this would normally be calculated)
            hours_to_add = Decimal("10.00")  # Mock hours based on transaction
            student_balance.hours_purchased += hours_to_add
            student_balance.balance_amount = student_balance.hours_purchased - student_balance.hours_consumed
            student_balance.save()

            return {
                "success": True,
                "payment_intent_id": payment_intent_id,
                "transaction_id": transaction.id,
                "hours_credited": float(hours_to_add),
                "message": "Payment completed successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error_type": "processing_error",
                "message": f"Error confirming payment completion: {e!s}",
            }

    def handle_payment_failure(self, payment_intent_id: str, error_message: str | None = None) -> dict[str, Any]:
        """Mock payment failure handling with actual database updates."""
        try:
            from finances.models import PurchaseTransaction, TransactionPaymentStatus

            # Find transaction by payment intent ID
            try:
                transaction = PurchaseTransaction.objects.get(stripe_payment_intent_id=payment_intent_id)
            except PurchaseTransaction.DoesNotExist:
                return {
                    "success": False,
                    "error_type": "transaction_not_found",
                    "message": "Transaction not found for payment intent ID",
                }

            # Check if already failed (idempotency)
            if transaction.payment_status == TransactionPaymentStatus.FAILED:
                return {
                    "success": True,
                    "payment_intent_id": payment_intent_id,
                    "transaction_id": transaction.id,
                    "message": "Payment already marked as failed (idempotent)",
                    "error_type": "invalid_transaction_state",
                }

            # Update transaction status to failed
            transaction.payment_status = TransactionPaymentStatus.FAILED
            if error_message:
                # In a real implementation, this would store the error message
                # For mock purposes, we'll just update the status
                pass
            transaction.save()

            return {
                "success": True,
                "payment_intent_id": payment_intent_id,
                "transaction_id": transaction.id,
                "error_message": error_message or "Payment failed",
                "message": "Payment failure handled successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error_type": "processing_error",
                "message": f"Error handling payment failure: {e!s}",
            }

    def get_payment_status(self, payment_intent_id: str) -> dict[str, Any]:
        """Mock payment status retrieval."""
        return {
            "success": True,
            "payment_intent_id": payment_intent_id,
            "status": "succeeded",
            "amount": 25000,
            "currency": "eur",
            "created": 1234567890,
        }


class MockPaymentAnalyticsServiceInstance:
    """
    Mock instance of PaymentAnalyticsService with realistic return values.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mock service without dependencies."""
        pass

    def get_revenue_summary(self, school=None, start_date=None, end_date=None) -> dict[str, Any]:
        """Mock revenue summary."""
        return {
            "total_revenue": 15000.0,
            "transaction_count": 150,
            "average_transaction": 100.0,
            "period_start": start_date,
            "period_end": end_date,
        }

    def get_payment_method_analytics(self, school=None, start_date=None, end_date=None) -> dict[str, Any]:
        """Mock payment method analytics."""
        return {"card_payments": 120, "bank_transfers": 30, "success_rate": 0.95}


class MockRefundServiceInstance:
    """
    Mock instance of RefundService with realistic return values.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mock service without dependencies."""
        self.stripe_service = MockStripeServiceInstance()

    def process_refund(
        self, transaction_id: int, amount: Decimal | None = None, reason: str | None = None
    ) -> dict[str, Any]:
        """Mock refund processing."""
        return {
            "success": True,
            "refund_id": "ref_mock_123",
            "amount_refunded": float(amount) if amount else 100.0,
            "message": "Refund processed successfully",
        }


class MockDisputeServiceInstance:
    """
    Mock instance of DisputeService with realistic return values.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mock service without dependencies."""
        self.stripe_service = MockStripeServiceInstance()

    def handle_dispute(self, dispute_id: str, action: str) -> dict[str, Any]:
        """Mock dispute handling."""
        return {
            "success": True,
            "dispute_id": dispute_id,
            "action_taken": action,
            "message": "Dispute handled successfully",
        }


class MockFraudDetectionServiceInstance:
    """
    Mock instance of FraudDetectionService with realistic return values.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mock service without dependencies."""
        pass

    def analyze_transaction(self, transaction_data: dict) -> dict[str, Any]:
        """Mock fraud analysis."""
        return {
            "fraud_score": 0.1,  # Low risk score
            "is_suspicious": False,
            "recommendation": "approve",
            "message": "Transaction appears legitimate",
        }


class MockReceiptGenerationServiceInstance:
    """
    Mock instance of ReceiptGenerationService with realistic return values.
    """

    @classmethod
    def _generate_html_content(cls, receipt) -> str:
        """Mock HTML generation."""
        return "<html><body>Fake HTML receipt for testing</body></html>"

    @classmethod
    def _create_receipt_record(cls, transaction):
        """Mock receipt record creation."""
        from decimal import Decimal

        from finances.models import Receipt

        receipt = Receipt.objects.create(
            transaction=transaction,
            student=transaction.student,
            amount=transaction.amount_eur or Decimal("100.00"),
            receipt_number=f"RCP-2025-MOCK{transaction.id}",
        )
        return receipt

    @classmethod
    def _save_html_file(cls, receipt, html_content):
        """Mock HTML file saving."""
        from django.core.files.base import ContentFile

        receipt.pdf_file.save(
            f"receipt_{receipt.receipt_number}.html", ContentFile(html_content.encode("utf-8")), save=True
        )

    @classmethod
    def _cleanup_receipt_file(cls, receipt):
        """Mock cleanup of receipt file."""
        if receipt.pdf_file:
            receipt.pdf_file.delete(save=False)

    @classmethod
    def _prepare_template_context(cls, receipt):
        """Mock template context preparation."""
        return {
            "receipt": receipt,
            "transaction": receipt.transaction,
            "student": receipt.student,
            "amount": receipt.amount,
            "date": receipt.created_at,
        }

    @classmethod
    def _get_receipt_css(cls):
        """Mock CSS for receipt."""
        return """
            body { font-family: Arial, sans-serif; }
            .receipt { margin: 20px; }
        """

    @classmethod
    def generate_receipt(cls, transaction_id: int, force_regenerate: bool = False) -> dict[str, Any]:
        """Mock receipt generation with complete database interaction."""
        from django.db import transaction as db_transaction

        from finances.models import PurchaseTransaction, Receipt, TransactionPaymentStatus

        # Type validation to match real service
        if transaction_id is None:
            raise ValueError("transaction_id cannot be None")
        if isinstance(transaction_id, bool) or not isinstance(transaction_id, int):
            raise TypeError(f"transaction_id must be an integer, got {type(transaction_id).__name__}")

        try:
            # Get transaction
            try:
                transaction = PurchaseTransaction.objects.select_related("student").get(id=transaction_id)
            except PurchaseTransaction.DoesNotExist:
                return {"success": False, "error_type": "not_found", "message": "Transaction not found"}

            # Validate transaction status
            if transaction.payment_status != TransactionPaymentStatus.COMPLETED:
                return {
                    "success": False,
                    "error_type": "invalid_status",
                    "message": "Can only generate receipts for completed transactions",
                }

            # Check existing receipt
            existing_receipt = Receipt.objects.filter(transaction=transaction).first()
            if existing_receipt and not force_regenerate:
                return {
                    "success": True,
                    "receipt_id": existing_receipt.id,
                    "receipt_number": existing_receipt.receipt_number,
                    "amount": float(existing_receipt.amount),
                    "already_existed": True,
                    "message": "Receipt already exists",
                }

            # Generate receipt with atomic transaction
            with db_transaction.atomic():
                if existing_receipt and force_regenerate:
                    cls._cleanup_receipt_file(existing_receipt)
                    existing_receipt.delete()

                receipt = cls._create_receipt_record(transaction)
                html_content = cls._generate_html_content(receipt)
                cls._save_html_file(receipt, html_content)

            return {
                "success": True,
                "receipt_id": receipt.id,
                "receipt_number": receipt.receipt_number,
                "amount": float(receipt.amount),
                "html_file_url": receipt.pdf_file.url if receipt.pdf_file else None,
                "message": "Receipt generated successfully",
            }

        except Exception as e:
            return {"success": False, "error_type": "generation_error", "message": f"Failed to generate receipt: {e!s}"}

    def __init__(self, *args, **kwargs):
        """Initialize mock service without dependencies."""
        pass


class MockPackageExpirationServiceInstance:
    """
    Mock instance of PackageExpirationService with realistic return values.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mock service without dependencies."""
        pass

    def check_package_expiration(self, student_user) -> dict[str, Any]:
        """Mock package expiration check."""
        return {
            "has_expired_packages": False,
            "expired_count": 0,
            "total_hours_lost": 0.0,
            "message": "No expired packages found",
        }


class MockHourDeductionServiceInstance:
    """
    Mock instance of HourDeductionService with realistic return values.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mock service without dependencies."""
        pass

    def deduct_hours(self, student_user, hours: Decimal, session_id=None) -> dict[str, Any]:
        """Mock hour deduction."""
        return {
            "success": True,
            "hours_deducted": float(hours),
            "remaining_balance": 25.5,
            "message": f"Successfully deducted {hours} hours",
        }


class MockRenewalPaymentServiceInstance:
    """
    Mock instance of RenewalPaymentService with realistic return values.
    """

    def __init__(self, *args, **kwargs):
        """Initialize mock service without dependencies."""
        from decimal import Decimal

        # Match the real service's QUICK_TOPUP_PACKAGES structure
        self.QUICK_TOPUP_PACKAGES = {
            Decimal("5.00"): Decimal("50.00"),  # 5 hours for €50
            Decimal("10.00"): Decimal("95.00"),  # 10 hours for €95 (5% discount)
            Decimal("20.00"): Decimal("180.00"),  # 20 hours for €180 (10% discount)
        }
        self.stripe_service = MockStripeServiceInstance()
        self.payment_method_service = MockPaymentMethodServiceInstance()

    def process_quick_topup(self, student_user, amount: Decimal, payment_method_id: int) -> dict[str, Any]:
        """Mock quick top-up processing."""
        return {
            "success": True,
            "payment_intent_id": "pi_mock_test_123",
            "client_secret": "pi_mock_test_123_secret_abc",
            "hours_added": float(amount),
            "new_balance": float(amount * 2),  # Mock balance calculation
            "message": f"Successfully topped up with {amount} hours",
        }

    def process_subscription_renewal(
        self, student_user, subscription_id: int, payment_method_id: int
    ) -> dict[str, Any]:
        """Mock subscription renewal processing."""
        return {
            "success": True,
            "payment_intent_id": "pi_mock_renewal_123",
            "client_secret": "pi_mock_renewal_123_secret_abc",
            "subscription_id": subscription_id,
            "hours_added": 40.0,  # Mock subscription hours
            "new_balance": 80.0,  # Mock new balance
            "message": "Subscription renewed successfully",
        }

    def get_available_topup_packages(self) -> list[dict[str, Any]]:
        """Mock getting available top-up packages."""
        packages = []
        for hours, price in self.QUICK_TOPUP_PACKAGES.items():
            packages.append(
                {
                    "hours": float(hours),
                    "price": float(price),
                    "price_per_hour": float(price / hours),
                    "savings_percent": self._calculate_savings_percent(hours, price),
                }
            )
        return packages

    def _calculate_savings_percent(self, hours, price):
        """Mock savings calculation to match real service."""
        base_price_per_hour = 10.0  # Mock base price
        standard_total = float(hours) * base_price_per_hour
        actual_total = float(price)
        if standard_total <= actual_total:
            return 0.0
        return ((standard_total - actual_total) / standard_total) * 100

    def _get_payment_method_for_renewal(self, student_user, payment_method_id=None):
        """Mock payment method retrieval for renewal."""
        # This is called internally by the real service
        return type(
            "MockPaymentMethod", (), {"id": payment_method_id or 1, "stripe_payment_method_id": "pm_mock_123"}
        )()


@contextmanager
def mock_stripe_services():
    """
    Context manager to mock all Stripe-related services.

    This patches service classes at the import level to prevent Stripe
    configuration validation and API calls during tests.

    Usage:
        with mock_stripe_services():
            # All Stripe services are now mocked
            service = PaymentMethodService()
            result = service.add_payment_method(...)
    """
    patches = []

    try:
        # Mock StripeService to prevent configuration validation
        stripe_service_patch = patch("finances.services.stripe_base.StripeService", MockStripeServiceInstance)
        patches.append(stripe_service_patch)

        # Mock PaymentMethodService
        payment_method_service_patch = patch(
            "finances.services.payment_method_service.PaymentMethodService", MockPaymentMethodServiceInstance
        )
        patches.append(payment_method_service_patch)

        # Mock RenewalPaymentService
        renewal_payment_service_patch = patch(
            "finances.services.renewal_payment_service.RenewalPaymentService", MockRenewalPaymentServiceInstance
        )
        patches.append(renewal_payment_service_patch)

        # Mock PaymentService
        payment_service_patch = patch("finances.services.payment_service.PaymentService", MockPaymentServiceInstance)
        patches.append(payment_service_patch)

        # Mock PaymentAnalyticsService
        analytics_service_patch = patch(
            "finances.services.payment_analytics_service.PaymentAnalyticsService", MockPaymentAnalyticsServiceInstance
        )
        patches.append(analytics_service_patch)

        # Mock RefundService
        refund_service_patch = patch("finances.services.refund_service.RefundService", MockRefundServiceInstance)
        patches.append(refund_service_patch)

        # Mock DisputeService
        dispute_service_patch = patch("finances.services.dispute_service.DisputeService", MockDisputeServiceInstance)
        patches.append(dispute_service_patch)

        # Mock FraudDetectionService
        fraud_service_patch = patch(
            "finances.services.fraud_detection_service.FraudDetectionService", MockFraudDetectionServiceInstance
        )
        patches.append(fraud_service_patch)

        # Mock ReceiptGenerationService
        receipt_service_patch = patch(
            "finances.services.receipt_service.ReceiptGenerationService", MockReceiptGenerationServiceInstance
        )
        patches.append(receipt_service_patch)

        # Mock PackageExpirationService
        expiration_service_patch = patch(
            "finances.services.package_expiration_service.PackageExpirationService",
            MockPackageExpirationServiceInstance,
        )
        patches.append(expiration_service_patch)

        # Mock HourDeductionService
        hour_deduction_service_patch = patch(
            "finances.services.hour_deduction_service.HourDeductionService", MockHourDeductionServiceInstance
        )
        patches.append(hour_deduction_service_patch)

        # Mock Django settings for Stripe configuration
        settings_patch = patch.multiple(
            "django.conf.settings",
            STRIPE_SECRET_KEY="sk_test_mock_key_for_testing",
            STRIPE_PUBLIC_KEY="pk_test_mock_key_for_testing",
            STRIPE_WEBHOOK_SECRET="whsec_test_mock_secret_for_testing",
        )
        patches.append(settings_patch)

        # Mock Stripe API key setting
        stripe_api_key_patch = patch("stripe.api_key", "sk_test_mock_key_for_testing")
        patches.append(stripe_api_key_patch)

        # Start all patches
        for p in patches:
            p.start()

        yield

    finally:
        # Stop all patches
        for p in patches:
            try:
                p.stop()
            except RuntimeError:
                # Patch was not started or already stopped
                pass


def mock_stripe_services_decorator(test_func=None, *, apply_to_class=False):
    """
    Decorator to mock all Stripe-related services for a test function or class.

    Usage as function decorator:
        @mock_stripe_services_decorator
        def test_payment_method(self):
            # Stripe services are mocked
            pass

    Usage as class decorator:
        @mock_stripe_services_decorator(apply_to_class=True)
        class TestPaymentMethods(TestCase):
            def test_something(self):
                # All test methods have Stripe services mocked
                pass
    """

    def decorator(func_or_class):
        if apply_to_class:
            # Apply to all test methods in the class
            original_setup = getattr(func_or_class, "setUp", None)
            original_teardown = getattr(func_or_class, "tearDown", None)

            def new_setup(self):
                self._stripe_patches = []

                # Mock StripeService
                stripe_service_patch = patch("finances.services.stripe_base.StripeService", MockStripeServiceInstance)
                self._stripe_patches.append(stripe_service_patch)

                # Mock PaymentMethodService
                payment_method_service_patch = patch(
                    "finances.services.payment_method_service.PaymentMethodService", MockPaymentMethodServiceInstance
                )
                self._stripe_patches.append(payment_method_service_patch)

                # Mock RenewalPaymentService
                renewal_payment_service_patch = patch(
                    "finances.services.renewal_payment_service.RenewalPaymentService", MockRenewalPaymentServiceInstance
                )
                self._stripe_patches.append(renewal_payment_service_patch)

                # Mock additional services that may be instantiated
                additional_service_patches = [
                    patch("finances.services.payment_service.PaymentService", MockPaymentServiceInstance),
                    patch(
                        "finances.services.payment_analytics_service.PaymentAnalyticsService",
                        MockPaymentAnalyticsServiceInstance,
                    ),
                    patch("finances.services.refund_service.RefundService", MockRefundServiceInstance),
                    patch("finances.services.dispute_service.DisputeService", MockDisputeServiceInstance),
                    patch(
                        "finances.services.fraud_detection_service.FraudDetectionService",
                        MockFraudDetectionServiceInstance,
                    ),
                    patch(
                        "finances.services.receipt_service.ReceiptGenerationService",
                        MockReceiptGenerationServiceInstance,
                    ),
                    patch(
                        "finances.services.package_expiration_service.PackageExpirationService",
                        MockPackageExpirationServiceInstance,
                    ),
                    patch(
                        "finances.services.hour_deduction_service.HourDeductionService",
                        MockHourDeductionServiceInstance,
                    ),
                    # Also patch the views that import services locally
                    patch("finances.views.PaymentService", MockPaymentServiceInstance),
                    patch("finances.views.StripeService", MockStripeServiceInstance),
                    # Patch receipt service at all possible import locations
                    patch(
                        "finances.views_financial_reports.ReceiptGenerationService",
                        MockReceiptGenerationServiceInstance,
                    ),
                ]

                # Patch import locations in function-based views after they're imported
                import_patches = []
                try:
                    # These patches target local imports that happen at runtime
                    import_patches.extend(
                        [
                            patch(
                                "finances.views_financial_reports.generate_receipt.ReceiptGenerationService",
                                MockReceiptGenerationServiceInstance,
                            ),
                        ]
                    )
                except AttributeError:
                    # Function may not have been imported yet
                    pass

                additional_service_patches.extend(import_patches)
                self._stripe_patches.extend(additional_service_patches)

                # Mock Django settings
                settings_patch = patch.multiple(
                    "django.conf.settings",
                    STRIPE_SECRET_KEY="sk_test_mock_key_for_testing",
                    STRIPE_PUBLIC_KEY="pk_test_mock_key_for_testing",
                    STRIPE_WEBHOOK_SECRET="whsec_test_mock_secret_for_testing",
                )
                self._stripe_patches.append(settings_patch)

                # Start all patches
                for p in self._stripe_patches:
                    p.start()

                if original_setup:
                    original_setup(self)

            def new_teardown(self):
                if original_teardown:
                    original_teardown(self)

                # Stop all patches
                for p in getattr(self, "_stripe_patches", []):
                    with suppress(RuntimeError):
                        p.stop()

            func_or_class.setUp = new_setup
            func_or_class.tearDown = new_teardown
            return func_or_class
        else:
            # Apply to individual function
            @wraps(func_or_class)
            def wrapper(*args, **kwargs):
                with mock_stripe_services():
                    return func_or_class(*args, **kwargs)

            return wrapper

    if test_func is None:
        # Called with arguments: @mock_stripe_services_decorator(apply_to_class=True)
        return decorator
    else:
        # Called without arguments: @mock_stripe_services_decorator
        return decorator(test_func)

    def reset_stripe_mocks(self):
        """Reset all Stripe mocks to their default configurations."""
        for mock_obj in [
            self.mock_payment_intent_create_obj,
            self.mock_payment_intent_retrieve_obj,
            self.mock_payment_intent_modify_obj,
            self.mock_payment_intent_confirm_obj,
            self.mock_payment_intent_cancel_obj,
            self.mock_payment_method_create_obj,
            self.mock_payment_method_retrieve_obj,
            self.mock_payment_method_attach_obj,
            self.mock_payment_method_detach_obj,
            self.mock_customer_create_obj,
            self.mock_customer_retrieve_obj,
            self.mock_customer_modify_obj,
            self.mock_customer_delete_obj,
            self.mock_charge_create_obj,
            self.mock_charge_retrieve_obj,
            self.mock_invoice_create_obj,
            self.mock_invoice_retrieve_obj,
            self.mock_invoice_finalize_obj,
            self.mock_refund_create_obj,
            self.mock_refund_retrieve_obj,
            self.mock_webhook_construct_obj,
        ]:
            mock_obj.reset_mock()
            mock_obj.side_effect = None

        # Reconfigure default responses
        self._configure_default_responses()


class StripeTestCase(StripeTestMixin, TestCase):
    """
    Base test case class with Stripe mocking automatically set up.

    Usage:
        class MyStripeTest(StripeTestCase):
            def test_payment_creation(self):
                # All Stripe API calls are automatically mocked
                pass
    """

    def setUp(self):
        """Set up the test case with Stripe mocks."""
        super().setUp()
        self.setup_stripe_mocks()

    def tearDown(self):
        """Clean up the test case."""
        self.teardown_stripe_mocks()
        super().tearDown()


class SimpleStripeTestCase(TestCase):
    """
    Simplified test case with comprehensive Stripe service mocking.

    This is the recommended base class for new tests that need Stripe mocking.
    It provides service-level mocking without the complexity of individual API mocks.

    Usage:
        class MyStripeTest(SimpleStripeTestCase):
            def test_payment_method_addition(self):
                # PaymentMethodService, StripeService, etc. are automatically mocked
                service = PaymentMethodService()
                result = service.add_payment_method(...)
    """

    def setUp(self):
        """Set up comprehensive Stripe service mocks."""
        super().setUp()

        # Mock StripeService constructor to prevent validation
        self.stripe_init_patcher = patch("finances.services.stripe_base.StripeService.__init__")
        self.mock_stripe_init = self.stripe_init_patcher.start()
        self.mock_stripe_init.return_value = None

        # Create a mock stripe service instance with proper methods
        self.mock_stripe_service = MockStripeServiceInstance()

    def tearDown(self):
        """Clean up Stripe service mocks."""
        self.stripe_init_patcher.stop()
        super().tearDown()

    def get_mock_stripe_service(self):
        """Get a properly configured mock StripeService instance."""
        return self.mock_stripe_service


def mock_stripe_service_responses():
    """
    Decorator to mock common Stripe service responses.

    This decorator is useful for testing service layer components
    that use Stripe services.
    """

    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            with patch("finances.services.payment_service.StripeService") as mock_service:
                # Configure mock service responses
                mock_instance = mock_service.return_value
                mock_instance.create_payment_intent.return_value = {
                    "success": True,
                    "payment_intent": MockPaymentIntent(),
                    "client_secret": "pi_test_mock_secret",
                }
                mock_instance.create_customer.return_value = {
                    "success": True,
                    "customer": MockCustomer(),
                    "customer_id": "cus_test_mock",
                }
                mock_instance.attach_payment_method_to_customer.return_value = {
                    "success": True,
                    "payment_method": MockPaymentMethod(customer="cus_test_mock"),
                }
                mock_instance.detach_payment_method.return_value = {
                    "success": True,
                    "message": "Payment method detached successfully",
                }
                mock_instance.retrieve_payment_method.return_value = {
                    "success": True,
                    "payment_method": MockPaymentMethod(),
                }

                # Execute the test with mocked services
                return test_func(self, *args, **kwargs)

        return wrapper

    return decorator


@contextmanager
def comprehensive_stripe_service_mocks():
    """
    Context manager that provides comprehensive mocking for all service instantiations.

    This specifically targets the direct instantiations in views.py and serializers.py
    that cause Stripe configuration errors during testing.

    Mocks:
    - StripeService() instantiations in views.py (lines 828, 1156, 1186)
    - PaymentMethodService() instantiations in views.py (lines 2151, 2228, 2275)
    - RenewalPaymentService() instantiations in views.py (lines 2310, 2361, 2439) and serializers.py (line 966)

    Usage:
        with comprehensive_stripe_service_mocks():
            # Make API calls to views/endpoints that instantiate services
            response = self.client.post('/api/endpoint/')
    """
    patches = []

    try:
        # Mock all Stripe-related services at their source modules and import locations
        service_patches = [
            patch("finances.services.stripe_base.StripeService", MockStripeServiceInstance),
            patch("finances.services.payment_method_service.PaymentMethodService", MockPaymentMethodServiceInstance),
            patch("finances.services.renewal_payment_service.RenewalPaymentService", MockRenewalPaymentServiceInstance),
            patch("finances.services.payment_service.PaymentService", MockPaymentServiceInstance),
            # Also patch the imported references in views.py
            patch("finances.views.PaymentService", MockPaymentServiceInstance),
            patch("finances.views.StripeService", MockStripeServiceInstance),
        ]
        patches.extend(service_patches)

        # Services are imported from their full module paths, so we patch the service modules themselves
        # which should be sufficient to catch all instantiations

        # Mock Django settings to prevent configuration validation
        settings_patch = patch.multiple(
            "django.conf.settings",
            STRIPE_SECRET_KEY="sk_test_mock_comprehensive_mocking",
            STRIPE_PUBLIC_KEY="pk_test_mock_comprehensive_mocking",
            STRIPE_WEBHOOK_SECRET="whsec_test_mock_comprehensive_mocking",
        )
        patches.append(settings_patch)

        # Mock stripe.api_key to prevent API key validation
        stripe_api_key_patch = patch("stripe.api_key", "sk_test_mock_comprehensive_mocking")
        patches.append(stripe_api_key_patch)

        # Start all patches
        for p in patches:
            p.start()

        yield

    finally:
        # Stop all patches
        for p in patches:
            try:
                p.stop()
            except RuntimeError:
                # Patch was not started or already stopped
                pass


def comprehensive_stripe_mocks_decorator(test_func=None, *, apply_to_class=False):
    """
    Decorator that provides comprehensive Stripe service mocking.

    This decorator ensures that all service instantiations in views.py and serializers.py
    are properly mocked to prevent Stripe configuration errors during testing.

    Usage as function decorator:
        @comprehensive_stripe_mocks_decorator
        def test_api_endpoint(self):
            response = self.client.post('/api/payment-methods/')
            # No Stripe configuration errors

    Usage as class decorator:
        @comprehensive_stripe_mocks_decorator(apply_to_class=True)
        class TestPaymentAPI(TestCase):
            def test_something(self):
                # All methods have comprehensive mocking
                pass
    """

    def decorator(func_or_class):
        if apply_to_class:
            # Apply to all test methods in the class
            original_setup = getattr(func_or_class, "setUp", None)
            original_teardown = getattr(func_or_class, "tearDown", None)

            def new_setup(self):
                self._comprehensive_patches = []

                # Mock all service classes to prevent instantiation issues
                service_patches = [
                    patch("finances.services.stripe_base.StripeService", MockStripeServiceInstance),
                    patch(
                        "finances.services.payment_method_service.PaymentMethodService",
                        MockPaymentMethodServiceInstance,
                    ),
                    patch(
                        "finances.services.renewal_payment_service.RenewalPaymentService",
                        MockRenewalPaymentServiceInstance,
                    ),
                    patch("finances.services.payment_service.PaymentService", MockPaymentServiceInstance),
                    patch(
                        "finances.services.payment_analytics_service.PaymentAnalyticsService",
                        MockPaymentAnalyticsServiceInstance,
                    ),
                    patch("finances.services.refund_service.RefundService", MockRefundServiceInstance),
                    patch("finances.services.dispute_service.DisputeService", MockDisputeServiceInstance),
                    patch(
                        "finances.services.fraud_detection_service.FraudDetectionService",
                        MockFraudDetectionServiceInstance,
                    ),
                    patch(
                        "finances.services.receipt_service.ReceiptGenerationService",
                        MockReceiptGenerationServiceInstance,
                    ),
                    patch(
                        "finances.services.package_expiration_service.PackageExpirationService",
                        MockPackageExpirationServiceInstance,
                    ),
                    patch(
                        "finances.services.hour_deduction_service.HourDeductionService",
                        MockHourDeductionServiceInstance,
                    ),
                    # Also patch the imported references in views.py
                    patch("finances.views.PaymentService", MockPaymentServiceInstance),
                    patch("finances.views.StripeService", MockStripeServiceInstance),
                ]
                self._comprehensive_patches.extend(service_patches)

                # Services are imported from their full module paths, so patching the service modules
                # themselves should catch all instantiations

                # Mock Django settings
                settings_patch = patch.multiple(
                    "django.conf.settings",
                    STRIPE_SECRET_KEY="sk_test_comprehensive_class_mocking",
                    STRIPE_PUBLIC_KEY="pk_test_comprehensive_class_mocking",
                    STRIPE_WEBHOOK_SECRET="whsec_test_comprehensive_class_mocking",
                )
                self._comprehensive_patches.append(settings_patch)

                # Start all patches
                for p in self._comprehensive_patches:
                    p.start()

                if original_setup:
                    original_setup(self)

            def new_teardown(self):
                if original_teardown:
                    original_teardown(self)

                # Stop all patches
                for p in getattr(self, "_comprehensive_patches", []):
                    with suppress(RuntimeError):
                        p.stop()

            func_or_class.setUp = new_setup
            func_or_class.tearDown = new_teardown
            return func_or_class
        else:
            # Apply to individual function
            @wraps(func_or_class)
            def wrapper(*args, **kwargs):
                with comprehensive_stripe_service_mocks():
                    return func_or_class(*args, **kwargs)

            return wrapper

    if test_func is None:
        # Called with arguments: @comprehensive_stripe_mocks_decorator(apply_to_class=True)
        return decorator
    else:
        # Called without arguments: @comprehensive_stripe_mocks_decorator
        return decorator(test_func)
