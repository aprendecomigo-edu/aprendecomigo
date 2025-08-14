"""
Base Stripe service for handling Stripe API operations.

This service provides centralized Stripe integration with comprehensive error handling,
security validation, and webhook processing infrastructure for the Aprende Comigo platform.
"""

import logging
import os
from typing import Any

from django.conf import settings
import stripe

from .rate_limiter import stripe_rate_limit

logger = logging.getLogger(__name__)


class StripeService:
    """
    Base service class for Stripe integration.

    Provides centralized configuration, error handling, and security validation
    for all Stripe API operations in the Aprende Comigo platform.
    """

    # Supported webhook event types for the platform
    SUPPORTED_WEBHOOK_EVENTS = {
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "payment_intent.created",
        "payment_intent.canceled",
        "customer.created",
        "customer.updated",
        "customer.deleted",
        "invoice.payment_succeeded",
        "invoice.payment_failed",
        "invoice.created",
        "subscription.created",
        "subscription.updated",
        "subscription.deleted",
    }

    def __init__(self, force_environment_validation=False):
        """
        Initialize Stripe service with configuration validation.

        Args:
            force_environment_validation: Whether to force environment validation even in tests

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        self._validate_configuration(force_environment_validation=force_environment_validation)
        self._configure_stripe()

    def _validate_configuration(self, force_environment_validation=False) -> None:
        """
        Validate Stripe configuration including environment-specific key validation.

        Args:
            force_environment_validation: Whether to force environment validation even in tests

        Raises:
            ValueError: If configuration is invalid or missing
        """
        # Check required settings first
        required_settings = ["STRIPE_SECRET_KEY", "STRIPE_PUBLIC_KEY", "STRIPE_WEBHOOK_SECRET"]
        for setting_name in required_settings:
            value = getattr(settings, setting_name, "")
            if not value:
                raise ValueError(f"Missing required Stripe configuration: {setting_name}")

        # Skip environment validation during tests unless explicitly forced
        if not force_environment_validation and (
            hasattr(settings, "TESTING") or "test" in os.environ.get("DJANGO_SETTINGS_MODULE", "")
        ):
            return

        # Check required settings
        required_settings = ["STRIPE_SECRET_KEY", "STRIPE_PUBLIC_KEY", "STRIPE_WEBHOOK_SECRET"]
        for setting_name in required_settings:
            value = getattr(settings, setting_name, "")
            if not value:
                raise ValueError(f"Missing required Stripe configuration: {setting_name}")

        # Get current environment
        django_env = os.environ.get("DJANGO_ENV", "development")

        # Validate key types against environment
        secret_key = settings.STRIPE_SECRET_KEY
        public_key = settings.STRIPE_PUBLIC_KEY

        if django_env == "development":
            if self._is_live_key(secret_key) or self._is_live_key(public_key):
                raise ValueError(
                    "Live Stripe keys detected in development environment. "
                    "Use test keys (sk_test_* and pk_test_*) for development."
                )
        elif django_env == "production":
            if self._is_test_key(secret_key) or self._is_test_key(public_key):
                raise ValueError(
                    "Test Stripe keys detected in production environment. "
                    "Use live keys (sk_live_* and pk_live_*) for production."
                )

    def _configure_stripe(self) -> None:
        """Configure Stripe API with secret key."""
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_version = "2023-10-16"  # Use specific API version for consistency

    def _is_test_key(self, key: str) -> bool:
        """Check if a key is a test key."""
        return key.startswith(("sk_test_", "pk_test_"))

    def _is_live_key(self, key: str) -> bool:
        """Check if a key is a live key."""
        return key.startswith(("sk_live_", "pk_live_"))

    def get_public_key(self) -> str:
        """
        Get the Stripe public key for frontend use.

        Returns:
            str: The Stripe public key
        """
        return settings.STRIPE_PUBLIC_KEY

    def get_webhook_secret(self) -> str:
        """
        Get the Stripe webhook secret.

        Returns:
            str: The Stripe webhook secret
        """
        return settings.STRIPE_WEBHOOK_SECRET

    def verify_api_connection(self) -> dict[str, Any]:
        """
        Verify connection to Stripe API by retrieving account information.

        Returns:
            Dict containing success status and account information or error details
        """
        try:
            account = stripe.Account.retrieve()
            return {
                "success": True,
                "message": "Stripe API connection verified successfully",
                "account_id": account.id,
                "account_name": account.business_profile.get("name") if account.business_profile else None,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API connection failed: {e}")
            return self.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error during Stripe API verification: {e}")
            return self.handle_stripe_error(e)

    def handle_stripe_error(self, error: Exception) -> dict[str, Any]:
        """
        Handle Stripe API errors with comprehensive error mapping.

        Args:
            error: The exception that occurred

        Returns:
            Dict containing error details and user-friendly messages
        """
        error_result = {
            "success": False,
            "error_type": "unknown_error",
            "message": "An unexpected error occurred",
            "param": None,
            "code": None,
        }

        if isinstance(error, stripe.error.CardError):
            # Card was declined
            error_result.update(
                {
                    "error_type": "card_error",
                    "message": error.user_message or "Your card was declined.",
                    "param": error.param,
                    "code": error.code,
                }
            )
            logger.warning(f"Stripe CardError: {error.user_message} (code: {error.code})")

        elif isinstance(error, stripe.error.RateLimitError):
            # Too many requests made to the API too quickly
            error_result.update(
                {
                    "error_type": "rate_limit_error",
                    "message": "Too many requests. Please wait a moment and try again.",
                }
            )
            logger.warning("Stripe RateLimitError: API rate limit exceeded")

        elif isinstance(error, stripe.error.InvalidRequestError):
            # Invalid parameters were supplied to Stripe's API
            error_result.update(
                {
                    "error_type": "invalid_request_error",
                    "message": error.user_message or "Invalid request parameters.",
                    "param": error.param,
                }
            )
            logger.error(f"Stripe InvalidRequestError: {error.user_message} (param: {error.param})")

        elif isinstance(error, stripe.error.AuthenticationError):
            # Authentication with Stripe's API failed
            error_result.update(
                {
                    "error_type": "authentication_error",
                    "message": "Authentication with payment processor failed. Please contact support.",
                }
            )
            logger.error("Stripe AuthenticationError: API authentication failed")

        elif isinstance(error, stripe.error.APIConnectionError):
            # Network communication with Stripe failed
            error_result.update(
                {
                    "error_type": "api_connection_error",
                    "message": "Network connection failed. Please check your internet connection and try again.",
                    "retryable": True,
                }
            )
            logger.error(f"Stripe APIConnectionError: {error}")

        elif isinstance(error, stripe.error.SignatureVerificationError):
            # Webhook signature verification failed
            error_result.update(
                {
                    "error_type": "signature_verification_error",
                    "message": "Webhook signature verification failed.",
                }
            )
            logger.error(f"Stripe SignatureVerificationError: {error}")

        elif isinstance(error, stripe.error.APIError):
            # Generic Stripe API error
            error_result.update(
                {
                    "error_type": "api_error",
                    "message": "Payment processor server error. Please try again later.",
                }
            )
            logger.error(f"Stripe APIError: {error}")

        else:
            # Non-Stripe error
            error_result.update(
                {
                    "error_type": "unknown_error",
                    "message": "An unexpected error occurred. Please try again later.",
                }
            )
            logger.error(f"Unexpected error in Stripe service: {error}")

        return error_result

    def construct_webhook_event(self, payload: str, sig_header: str) -> dict[str, Any]:
        """
        Construct and verify a Stripe webhook event.

        Args:
            payload: The raw webhook payload
            sig_header: The Stripe signature header

        Returns:
            Dict containing the constructed event or error details
        """
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.get_webhook_secret())

            return {"success": True, "event": event, "event_type": event.get("type"), "event_id": event.get("id")}

        except stripe.error.StripeError as e:
            logger.error(f"Webhook event construction failed: {e}")
            return self.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error constructing webhook event: {e}")
            return self.handle_stripe_error(e)

    def is_webhook_event_type_supported(self, event_type: str) -> bool:
        """
        Check if a webhook event type is supported by the platform.

        Args:
            event_type: The webhook event type to check

        Returns:
            bool: True if the event type is supported, False otherwise
        """
        return event_type in self.SUPPORTED_WEBHOOK_EVENTS

    def __str__(self) -> str:
        """
        String representation that doesn't expose sensitive information.

        Returns:
            str: Safe string representation
        """
        django_env = os.environ.get("DJANGO_ENV", "development")
        key_type = "test" if self._is_test_key(settings.STRIPE_SECRET_KEY) else "live"
        return f"StripeService(environment={django_env}, key_type={key_type})"

    def __repr__(self) -> str:
        """
        Representation that doesn't expose sensitive information.

        Returns:
            str: Safe string representation
        """
        return self.__str__()

    @stripe_rate_limit("read_operations")
    def retrieve_payment_method(self, payment_method_id: str) -> dict[str, Any]:
        """
        Retrieve a payment method from Stripe.

        Args:
            payment_method_id: Stripe PaymentMethod ID to retrieve

        Returns:
            Dict containing success status and payment method data or error information
        """
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)

            return {
                "success": True,
                "payment_method": payment_method,
                "message": "Payment method retrieved successfully",
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment method {payment_method_id}: {e}")
            return self.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error retrieving payment method {payment_method_id}: {e}")
            return self.handle_stripe_error(e)

    @stripe_rate_limit("write_operations")
    def detach_payment_method(self, payment_method_id: str) -> dict[str, Any]:
        """
        Detach a payment method from its customer in Stripe.

        Args:
            payment_method_id: Stripe PaymentMethod ID to detach

        Returns:
            Dict containing success status or error information
        """
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            payment_method.detach()

            logger.info(f"Successfully detached payment method {payment_method_id}")

            return {"success": True, "message": "Payment method detached successfully"}

        except stripe.error.StripeError as e:
            logger.error(f"Error detaching payment method {payment_method_id}: {e}")
            return self.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error detaching payment method {payment_method_id}: {e}")
            return self.handle_stripe_error(e)

    @stripe_rate_limit("write_operations")
    def attach_payment_method_to_customer(self, payment_method_id: str, customer_id: str) -> dict[str, Any]:
        """
        Attach a payment method to a customer in Stripe.

        Args:
            payment_method_id: Stripe PaymentMethod ID to attach
            customer_id: Stripe Customer ID to attach to

        Returns:
            Dict containing success status or error information
        """
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            payment_method.attach(customer=customer_id)

            logger.info(f"Successfully attached payment method {payment_method_id} to customer {customer_id}")

            return {
                "success": True,
                "payment_method": payment_method,
                "message": "Payment method attached successfully",
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error attaching payment method {payment_method_id} to customer {customer_id}: {e}")
            return self.handle_stripe_error(e)
        except Exception as e:
            logger.error(
                f"Unexpected error attaching payment method {payment_method_id} to customer {customer_id}: {e}"
            )
            return self.handle_stripe_error(e)

    @stripe_rate_limit("read_operations")
    def list_customer_payment_methods(self, customer_id: str, payment_method_type: str = "card") -> dict[str, Any]:
        """
        List all payment methods for a customer in Stripe.

        Args:
            customer_id: Stripe Customer ID to list payment methods for
            payment_method_type: Type of payment methods to list (default: 'card')

        Returns:
            Dict containing success status and payment methods list or error information
        """
        try:
            payment_methods = stripe.PaymentMethod.list(customer=customer_id, type=payment_method_type)

            return {
                "success": True,
                "payment_methods": payment_methods.data,
                "count": len(payment_methods.data),
                "message": "Payment methods retrieved successfully",
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error listing payment methods for customer {customer_id}: {e}")
            return self.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error listing payment methods for customer {customer_id}: {e}")
            return self.handle_stripe_error(e)

    @stripe_rate_limit("write_operations")
    def create_customer(self, email: str, name: str, metadata: dict[str, str] | None = None) -> dict[str, Any]:
        """
        Create a new customer in Stripe.

        Args:
            email: Customer email address
            name: Customer name
            metadata: Optional metadata to attach to the customer

        Returns:
            Dict containing success status and customer data or error information
        """
        try:
            customer_data = {
                "email": email,
                "name": name,
            }

            if metadata:
                customer_data["metadata"] = metadata

            customer = stripe.Customer.create(**customer_data)

            logger.info(f"Successfully created Stripe customer {customer.id} for {email}")

            return {
                "success": True,
                "customer": customer,
                "customer_id": customer.id,
                "message": "Customer created successfully",
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating customer for {email}: {e}")
            return self.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error creating customer for {email}: {e}")
            return self.handle_stripe_error(e)

    @stripe_rate_limit("read_operations")
    def retrieve_customer(self, customer_id: str) -> dict[str, Any]:
        """
        Retrieve a customer from Stripe.

        Args:
            customer_id: Stripe Customer ID to retrieve

        Returns:
            Dict containing success status and customer data or error information
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)

            return {"success": True, "customer": customer, "message": "Customer retrieved successfully"}

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving customer {customer_id}: {e}")
            return self.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error retrieving customer {customer_id}: {e}")
            return self.handle_stripe_error(e)

    @stripe_rate_limit("write_operations")
    def update_customer(self, customer_id: str, **kwargs) -> dict[str, Any]:
        """
        Update a customer in Stripe.

        Args:
            customer_id: Stripe Customer ID to update
            **kwargs: Fields to update

        Returns:
            Dict containing success status and updated customer data or error information
        """
        try:
            customer = stripe.Customer.modify(customer_id, **kwargs)

            logger.info(f"Successfully updated Stripe customer {customer_id}")

            return {"success": True, "customer": customer, "message": "Customer updated successfully"}

        except stripe.error.StripeError as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            return self.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error updating customer {customer_id}: {e}")
            return self.handle_stripe_error(e)

    def validate_amount_for_education_service(self, amount_cents: int) -> bool:
        """
        Validate payment amount for education services.

        Args:
            amount_cents: Payment amount in cents (e.g., 50 for €0.50)

        Returns:
            bool: True if amount is valid for education services, False otherwise
        """
        # Minimum amount: €0.50 (50 cents)
        MIN_AMOUNT_CENTS = 50

        # Maximum amount: €10,000 (1,000,000 cents)
        MAX_AMOUNT_CENTS = 1000000

        return MIN_AMOUNT_CENTS <= amount_cents <= MAX_AMOUNT_CENTS

    def is_currency_supported(self, currency: str) -> bool:
        """
        Check if currency is supported for education services.

        Args:
            currency: Currency code (e.g., 'eur', 'usd')

        Returns:
            bool: True if currency is supported, False otherwise
        """
        # Only EUR is supported for European market
        return currency.lower() == "eur"

    def get_allowed_payment_methods(self) -> list:
        """
        Get list of allowed payment methods for education services.

        Returns:
            list: List of allowed payment method types
        """
        return ["card", "sepa_debit", "ideal"]

    def validate_educational_metadata(self, metadata: dict) -> bool:
        """
        Validate metadata for educational transactions to prevent fraud.

        Args:
            metadata: Dictionary of metadata to validate

        Returns:
            bool: True if metadata is valid for educational context
        """
        required_fields = {"user_id", "transaction_type", "hours_purchased", "school_context"}

        # Check all required fields are present
        if not all(field in metadata for field in required_fields):
            return False

        # Validate specific field values
        valid_transaction_types = {"package", "subscription", "one_time"}
        if metadata.get("transaction_type") not in valid_transaction_types:
            return False

        return True
