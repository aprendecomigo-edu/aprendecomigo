"""
Minimal API Tests for Issue #183 - Card Display Format (Expected failures)

These tests focus specifically on the card display format issue without complex setup.
They validate that StoredPaymentMethod serialization returns the NEW expected format
'Visa ****4242' instead of the legacy format 'Visa ****X242'.

These tests will FAIL initially (TDD red state) and should pass after implementing
the card display format improvements.
"""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from finances.models import StoredPaymentMethod
from finances.serializers import StoredPaymentMethodSerializer

User = get_user_model()


class MinimalCardDisplayFormatTests(APITestCase):
    """
    Minimal tests for card display format issue #183.
    
    These tests demonstrate the specific format conversion issue without
    complex test setup that might mask the core problem.
    """

    def setUp(self):
        """Set up minimal test data."""
        # Create user
        self.user = User.objects.create_user(
            email="test@example.com",
            name="Test User"
        )

    def test_legacy_card_format_conversion_x242(self):
        """
        Test conversion of legacy format 'X242' to new format '****4242'.
        
        This test will FAIL initially - it expects the NEW format but
        the current implementation returns the legacy format.
        """
        # Create payment method with legacy masked format
        payment_method = StoredPaymentMethod.objects.create(
            student=self.user,
            stripe_payment_method_id="pm_test_legacy",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="X242",  # Legacy format
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True
        )

        # Test serializer output
        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        # CRITICAL: This will FAIL initially
        expected_display = "Visa ****4242"  # NEW expected format
        actual_display = data['card_display']

        self.assertEqual(
            actual_display,
            expected_display,
            f"Legacy format 'X242' should convert to '{expected_display}' but got '{actual_display}'"
        )

    def test_legacy_card_format_conversion_x444(self):
        """
        Test conversion of legacy format 'X444' to new format '****4444'.
        
        This test will FAIL initially for Mastercard test pattern.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.user,
            stripe_payment_method_id="pm_test_legacy_mc",
            stripe_customer_id="cus_test_customer", 
            card_brand="mastercard",
            card_last4="X444",  # Legacy format
            card_exp_month=6,
            card_exp_year=2026,
            is_default=False,
            is_active=True
        )

        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        expected_display = "Mastercard ****4444"  # NEW expected format
        actual_display = data['card_display']

        self.assertEqual(
            actual_display,
            expected_display,
            f"Legacy Mastercard format 'X444' should convert to '{expected_display}' but got '{actual_display}'"
        )

    def test_raw_digits_format_unchanged(self):
        """
        Test that raw 4-digit format remains unchanged.
        
        Raw digits like '4242' should display as 'Visa ****4242' directly.
        This test should PASS as raw digits are already in correct format.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.user,
            stripe_payment_method_id="pm_test_raw",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="4242",  # Raw format (correct)
            card_exp_month=3,
            card_exp_year=2027,
            is_default=False,
            is_active=True
        )

        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        expected_display = "Visa ****4242"
        actual_display = data['card_display']

        self.assertEqual(
            actual_display,
            expected_display,
            f"Raw format '4242' should display as '{expected_display}' but got '{actual_display}'"
        )

    def test_unknown_legacy_format_fallback(self):
        """
        Test fallback handling for unknown legacy patterns.
        
        Legacy formats that don't match known patterns should still be
        handled gracefully without breaking.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.user,
            stripe_payment_method_id="pm_test_unknown",
            stripe_customer_id="cus_test_customer",
            card_brand="amex",
            card_last4="X999",  # Unknown legacy pattern
            card_exp_month=9,
            card_exp_year=2025,
            is_default=False,
            is_active=True
        )

        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        # Should not crash and should include brand name
        actual_display = data['card_display']
        self.assertIn("Amex", actual_display)
        self.assertIsInstance(actual_display, str)
        self.assertGreater(len(actual_display), 0)

    def test_model_str_method_uses_new_format(self):
        """
        Test that model's __str__ method also uses new format.
        
        The model's string representation should be consistent with API serializer.
        This test will FAIL initially if model __str__ still uses legacy format.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.user,
            stripe_payment_method_id="pm_test_str",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="X242",  # Legacy format
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True
        )

        # Test model string representation
        model_str = str(payment_method)
        
        # Should contain the NEW format
        expected_format = "****4242"
        self.assertIn(
            expected_format,
            model_str,
            f"Model __str__ should use new format containing '{expected_format}' but got '{model_str}'"
        )

    def test_card_display_property_directly(self):
        """
        Test the model's card_display property directly.
        
        This bypasses serializer and tests the model property that should
        handle the format conversion.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.user,
            stripe_payment_method_id="pm_test_property",
            stripe_customer_id="cus_test_customer", 
            card_brand="visa",
            card_last4="X242",  # Legacy format
            card_exp_month=12,
            card_exp_year=2025,
            is_default=False,
            is_active=True
        )

        # Test card_display property directly
        card_display = payment_method.card_display

        expected_display = "Visa ****4242"
        self.assertEqual(
            card_display,
            expected_display,
            f"Model card_display property should return '{expected_display}' but got '{card_display}'"
        )