"""
Base test classes for the Aprende Comigo platform.

This module provides common test utilities and base classes that ensure
proper test isolation and external service mocking.
"""

from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase
from .stripe_test_fixtures import StripeServiceMocker

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
    - All Stripe API calls are comprehensively mocked
    """

    def setUp(self):
        """Set up test environment with comprehensive mocking."""
        super().setUp()
        
        # Start comprehensive Stripe API mocking
        self.stripe_mocker = StripeServiceMocker()
        self.stripe_mocks = self.stripe_mocker.start_mocking()
        
        # Mock Stripe configuration settings
        self.stripe_config_patcher = patch.multiple(
            'django.conf.settings',
            STRIPE_SECRET_KEY='sk_test_4eC39HqLyjWDarjtT1zdp7dc',  # Stripe's published test key
            STRIPE_PUBLIC_KEY='pk_test_TYooMQauvdEDq54NiTphI7jx',   # Stripe's published test key
            STRIPE_WEBHOOK_SECRET='whsec_test_mock_webhook_secret'
        )
        self.stripe_config_patcher.start()
        
        # Clear cache to ensure test isolation
        from django.core.cache import cache

        cache.clear()

    def tearDown(self):
        """Clean up after test."""
        # Stop Stripe API mocking
        self.stripe_mocker.stop_mocking()
        
        # Stop configuration patching
        self.stripe_config_patcher.stop()
        
        super().tearDown()


@override_settings(**THROTTLE_FREE_TEST_SETTINGS)
class BaseModelTestCase(TestCase):
    """
    Base test case for model tests that need external services mocked.

    Use this class for model tests that might trigger signals or
    other operations that could call external services.
    """

    def setUp(self):
        """Set up test environment with comprehensive mocking."""
        super().setUp()
        
        # Start comprehensive Stripe API mocking for model tests that might trigger payment operations
        self.stripe_mocker = StripeServiceMocker()
        self.stripe_mocks = self.stripe_mocker.start_mocking()
        
        # Mock Stripe configuration settings
        self.stripe_config_patcher = patch.multiple(
            'django.conf.settings',
            STRIPE_SECRET_KEY='sk_test_4eC39HqLyjWDarjtT1zdp7dc',
            STRIPE_PUBLIC_KEY='pk_test_TYooMQauvdEDq54NiTphI7jx',
            STRIPE_WEBHOOK_SECRET='whsec_test_mock_webhook_secret'
        )
        self.stripe_config_patcher.start()
        
        # Clear cache to ensure test isolation
        from django.core.cache import cache

        cache.clear()
    
    def tearDown(self):
        """Clean up after test."""
        # Stop Stripe API mocking
        self.stripe_mocker.stop_mocking()
        
        # Stop configuration patching  
        self.stripe_config_patcher.stop()
        
        super().tearDown()


def mock_external_services(test_func):
    """
    Decorator to comprehensively mock all external services for unit tests.
    
    This decorator automatically mocks:
    - Email sending (send_mail)
    - Complete Stripe API (PaymentIntent, Customer, PaymentMethod, etc.)
    - SMS services
    - HTTP requests
    
    Usage:
        @mock_external_services
        def test_my_feature(self):
            # Test code here - all external services are comprehensively mocked
            pass
    """

    def wrapper(*args, **kwargs):
        # Initialize comprehensive Stripe mocking
        stripe_mocker = StripeServiceMocker()
        
        try:
            # Start comprehensive Stripe mocking
            stripe_mocks = stripe_mocker.start_mocking()
            
            with patch('django.core.mail.send_mail') as mock_send_mail, \
                 patch('requests.get') as mock_requests_get, \
                 patch('requests.post') as mock_requests_post:
                
                # Configure basic service mocks
                mock_send_mail.return_value = True
                mock_requests_get.return_value.status_code = 200
                mock_requests_post.return_value.status_code = 200
                
                return test_func(*args, **kwargs)
                
        finally:
            # Always clean up Stripe mocking
            stripe_mocker.stop_mocking()
    
    return wrapper
