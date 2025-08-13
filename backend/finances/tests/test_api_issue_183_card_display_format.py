"""
API Tests for Issue #183 - Card Display Format API Responses (5-8 failures expected)

These tests validate that API endpoints return payment method card display information
in the NEW expected format: 'Visa ****4242' (PCI-compliant) instead of the legacy
format: 'Visa ****X242'. 

These tests will FAIL initially (TDD red state) and should pass after implementing
the card display format improvements.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock

from accounts.models import School
from finances.models import StoredPaymentMethod, StudentAccountBalance, PricingPlan
from common.test_base import BaseAPITestCase

User = get_user_model()


class CardDisplayFormatAPITests(BaseAPITestCase):
    """
    Test card display format in API responses for Issue #183.
    
    These tests validate that payment method APIs return the NEW expected format
    'Visa ****4242' instead of the legacy format 'Visa ****X242'.
    """
    
    def setUp(self):
        """Set up test data for card display format tests."""
        super().setUp()
        self.client = APIClient()
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            address="123 Test St"
        )
        
        # Create student user
        self.student_user = User.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        # Create student account balance
        StudentAccountBalance.objects.create(
            student=self.student_user,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('0.00')
        )
        
        # Create pricing plan
        self.pricing_plan = PricingPlan.objects.create(
            school=self.school,
            name="Basic Plan",
            hours=10,
            price=Decimal('100.00'),
            is_active=True
        )
        
        # Create stored payment method with legacy masked format
        self.payment_method_legacy = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_legacy_card",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="X242",  # Legacy masked format
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True
        )
        
        # Create another payment method with raw digits (should be handled correctly)
        self.payment_method_raw = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_raw_card",
            stripe_customer_id="cus_test_customer",
            card_brand="mastercard", 
            card_last4="4444",  # Raw 4 digits
            card_exp_month=6,
            card_exp_year=2026,
            is_default=False,
            is_active=True
        )
        
        # Authenticate as student
        self.client.force_authenticate(user=self.student_user)

    def test_payment_methods_list_api_card_display_format(self):
        """
        Test GET /api/student-balance/payment-methods/ returns NEW card display format.
        
        Expected: 'Visa ****4242' instead of legacy 'Visa ****X242'
        This test will FAIL initially.
        """
        url = "/api/student-balance/payment-methods/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertIn('payment_methods', data)
        payment_methods = data['payment_methods']
        
        # Find the legacy masked payment method
        legacy_method = next(
            (pm for pm in payment_methods if pm['id'] == self.payment_method_legacy.id), 
            None
        )
        self.assertIsNotNone(legacy_method, "Legacy payment method not found in API response")
        
        # CRITICAL: This will FAIL initially - expects NEW format
        expected_card_display = "Visa ****4242"  # NEW PCI-compliant format
        actual_card_display = legacy_method['card_display']
        
        self.assertEqual(
            actual_card_display,
            expected_card_display,
            f"Card display format should be '{expected_card_display}' but got '{actual_card_display}'. "
            f"Legacy format 'Visa ****X242' should be converted to PCI-compliant format."
        )

    def test_payment_methods_list_api_raw_digits_format(self):
        """
        Test GET /api/student-balance/payment-methods/ handles raw digits correctly.
        
        Expected: 'Mastercard ****4444' for raw card_last4="4444"
        This test should validate proper handling of non-legacy formats.
        """
        url = "/api/student-balance/payment-methods/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Find the raw digits payment method  
        raw_method = next(
            (pm for pm in data['payment_methods'] if pm['id'] == self.payment_method_raw.id),
            None
        )
        self.assertIsNotNone(raw_method, "Raw digits payment method not found in API response")
        
        # Should display raw digits correctly without conversion issues
        expected_card_display = "Mastercard ****4444"
        actual_card_display = raw_method['card_display']
        
        self.assertEqual(
            actual_card_display,
            expected_card_display,
            f"Raw digits should display as '{expected_card_display}' but got '{actual_card_display}'"
        )

    @patch('finances.services.payment_method_service.StripeService')
    def test_add_payment_method_api_response_format(self, mock_stripe_service):
        """
        Test POST /api/student-balance/payment-methods/ returns NEW format in response.
        
        When adding a payment method, the API response should include the payment method
        with the NEW card display format.
        This test will FAIL initially.
        """
        # Mock Stripe service responses
        mock_instance = MagicMock()
        mock_stripe_service.return_value = mock_instance
        
        # Mock payment method retrieval
        mock_instance.get_payment_method.return_value = {
            'success': True,
            'payment_method': {
                'id': 'pm_test_new_card',
                'card': {
                    'brand': 'visa',
                    'last4': '0002',
                    'exp_month': 12,
                    'exp_year': 2027
                }
            }
        }
        
        # Mock customer creation/retrieval
        mock_instance.create_or_get_customer.return_value = {
            'success': True,
            'customer_id': 'cus_test_new_customer'
        }
        
        # Mock payment method attachment
        mock_instance.attach_payment_method_to_customer.return_value = {
            'success': True
        }
        
        url = "/api/student-balance/payment-methods/"
        data = {
            "stripe_payment_method_id": "pm_test_new_card",
            "is_default": False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        response_data = response.json()
        self.assertIn('payment_method', response_data)
        payment_method = response_data['payment_method']
        
        # CRITICAL: This will FAIL initially - expects NEW format
        expected_card_display = "Visa ****0002"  # NEW format for Visa ending in 0002
        actual_card_display = payment_method['card_display']
        
        self.assertEqual(
            actual_card_display,
            expected_card_display,
            f"New payment method should display as '{expected_card_display}' but got '{actual_card_display}'"
        )

    def test_serializer_direct_card_display_format(self):
        """
        Test StoredPaymentMethodSerializer directly for card display format.
        
        This test validates the serializer level to ensure the format conversion
        is working at the serialization layer.
        This test will FAIL initially.
        """
        from finances.serializers import StoredPaymentMethodSerializer
        
        # Test legacy masked format conversion
        serializer = StoredPaymentMethodSerializer(self.payment_method_legacy)
        data = serializer.data
        
        expected_card_display = "Visa ****4242"  # NEW format
        actual_card_display = data['card_display']
        
        self.assertEqual(
            actual_card_display,
            expected_card_display,
            f"Serializer should convert legacy 'X242' to '{expected_card_display}' but got '{actual_card_display}'"
        )

    def test_multiple_card_brands_display_format(self):
        """
        Test different card brands use NEW display format consistently.
        
        Create payment methods for various brands and verify they all use
        the NEW format instead of legacy format.
        This test will FAIL initially for legacy masked cards.
        """
        # Create different card brands with legacy format
        card_brands_legacy = [
            ('amex', 'X002', 'Amex ****0002'),
            ('discover', 'X444', 'Discover ****4444'), 
            ('mastercard', 'X242', 'Mastercard ****4242'),
        ]
        
        payment_methods = []
        for brand, last4, expected_display in card_brands_legacy:
            pm = StoredPaymentMethod.objects.create(
                student=self.student_user,
                stripe_payment_method_id=f"pm_test_{brand}",
                stripe_customer_id="cus_test_customer",
                card_brand=brand,
                card_last4=last4,  # Legacy masked format
                card_exp_month=12,
                card_exp_year=2025,
                is_default=False,
                is_active=True
            )
            payment_methods.append((pm, expected_display))
        
        # Test API response for all brands
        url = "/api/student-balance/payment-methods/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        api_payment_methods = data['payment_methods']
        
        for pm, expected_display in payment_methods:
            api_pm = next(
                (api_pm for api_pm in api_payment_methods if api_pm['id'] == pm.id),
                None
            )
            self.assertIsNotNone(api_pm, f"Payment method {pm.id} not found in API response")
            
            # CRITICAL: This will FAIL initially for legacy formats
            actual_display = api_pm['card_display']
            self.assertEqual(
                actual_display,
                expected_display,
                f"{pm.card_brand} card should display as '{expected_display}' but got '{actual_display}'"
            )

    def test_renewal_api_includes_new_card_format(self):
        """
        Test renewal API response includes payment method with NEW display format.
        
        When renewing a subscription, if payment method info is returned,
        it should use the NEW format.
        This test will FAIL initially.
        """
        # This test would be implemented once we understand the renewal API
        # endpoint's response structure and if it includes payment method info
        self.skipTest(
            "Renewal API card display format test - requires analysis of renewal endpoint response structure"
        )

    def test_error_response_with_payment_method_includes_new_format(self):
        """
        Test error responses that include payment method info use NEW format.
        
        When API errors include payment method details, they should use the NEW format.
        This is an edge case that might be part of the 5-8 failures mentioned.
        """
        # Create expired payment method with legacy format
        expired_pm = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_expired",
            stripe_customer_id="cus_test_customer", 
            card_brand="visa",
            card_last4="X242",  # Legacy format
            card_exp_month=1,
            card_exp_year=2020,  # Expired
            is_default=False,
            is_active=True
        )
        
        # If error responses include payment method details, they should use NEW format
        # This is an edge case test - the exact endpoint would need to be determined
        # based on which APIs include payment method info in error responses
        
        self.skipTest(
            "Error response card format test - requires identification of which APIs "
            "include payment method details in error responses"
        )