"""
Base test classes for the Aprende Comigo platform.

This module provides common test utilities and base classes that ensure
proper test isolation and external service mocking.
"""

from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

# Test settings that disable throttling and external services
THROTTLE_FREE_TEST_SETTINGS = {
    "REST_FRAMEWORK": {"DEFAULT_THROTTLE_CLASSES": [], "DEFAULT_THROTTLE_RATES": {}},
    # Override all throttle rates to be very high for tests
    "REST_FRAMEWORK_THROTTLE_RATES": {
        "auth_code_request": "10000/min",
        "auth_signup_ip": "10000/min",
        "auth_code_verify_email": "10000/min",
        "auth_code_verify_ip": "10000/min",
        "purchase_initiation": "10000/min",
        "purchase_initiation_email": "10000/min",
    },
    # Use dummy cache to prevent throttling state persistence
    "CACHES": {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    },
    # Mock email backend to prevent real email sending
    "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
}


@override_settings(**THROTTLE_FREE_TEST_SETTINGS)
class BaseAPITestCase(APITestCase):
    """
    Base test case for API tests that need throttling disabled
    and external services mocked.

    Use this class for any API tests to ensure:
    - No throttling interferes with tests
    - No real emails are sent
    - Cache doesn't persist between tests
    - External services are properly mocked
    """

    def setUp(self):
        """Set up test environment with common mocking."""
        super().setUp()

        # Mock Stripe configuration to prevent real API calls
        self.stripe_patcher = patch.multiple(
            "django.conf.settings",
            STRIPE_SECRET_KEY="sk_test_mock_key",
            STRIPE_PUBLIC_KEY="pk_test_mock_key",
            STRIPE_WEBHOOK_SECRET="whsec_test_mock",
        )
        self.stripe_patcher.start()

        # Clear cache to ensure test isolation
        from django.core.cache import cache

        cache.clear()

    def tearDown(self):
        """Clean up after test."""
        self.stripe_patcher.stop()
        super().tearDown()


@override_settings(**THROTTLE_FREE_TEST_SETTINGS)
class BaseModelTestCase(TestCase):
    """
    Base test case for model tests that need external services mocked.

    Use this class for model tests that might trigger signals or
    other operations that could call external services.
    """

    def setUp(self):
        """Set up test environment with common mocking."""
        super().setUp()

        # Clear cache to ensure test isolation
        from django.core.cache import cache

        cache.clear()


def mock_external_services(test_func):
    """
    Decorator to mock common external services for unit tests.

    This decorator automatically mocks:
    - Email sending (send_mail)
    - Stripe API calls
    - SMS services (via httpx)

    Usage:
        @mock_external_services
        def test_my_feature(self):
            # Test code here - external services are mocked
            pass
    """

    def wrapper(*args, **kwargs):
        with (
            patch("django.core.mail.send_mail") as mock_send_mail,
            patch("stripe.PaymentIntent.create") as mock_stripe_pi,
            patch("stripe.Customer.create") as mock_stripe_customer,
            patch("httpx.Client.post") as mock_httpx_post,
            patch("httpx.AsyncClient.post") as mock_httpx_async_post,
        ):
            # Set up default mock return values
            mock_send_mail.return_value = True
            mock_stripe_pi.return_value.id = "pi_mock_test"
            mock_stripe_pi.return_value.client_secret = "pi_mock_test_secret"
            mock_stripe_customer.return_value.id = "cus_mock_test"

            # Set up httpx mock return values
            mock_httpx_response = type(
                "MockResponse", (), {"status_code": 200, "json": lambda: {"success": True, "mock": True}}
            )()
            mock_httpx_post.return_value = mock_httpx_response
            mock_httpx_async_post.return_value = mock_httpx_response

            return test_func(*args, **kwargs)

    return wrapper
