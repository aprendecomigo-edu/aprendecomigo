"""
Unit tests for PCI Compliance business logic.

Tests core business rules for PCI DSS compliance without API endpoints:
- Card data sanitization and masking algorithms
- PCI compliance validation rules and pattern detection
- Secure storage logic for sensitive data
- Data anonymization business rules
- Card display formatting for compliance
- Audit trail creation for PCI compliance

These tests focus on the business logic that needs fixes for GitHub Issue #173.
"""

import re
from unittest import TestCase

from finances.utils.pci_compliance import (
    get_secure_card_display,
    is_pci_compliant_field_value,
    mask_card_last4,
    sanitize_card_data,
    unmask_card_last4_for_display,
    validate_pci_compliance,
)


class CardDataMaskingTest(TestCase):
    """Test card data masking algorithms for PCI compliance."""

    def test_mask_card_last4_valid_digits(self):
        """Test masking of valid 4-digit card numbers."""
        # Test common card patterns
        self.assertEqual(mask_card_last4("4242"), "X242")
        self.assertEqual(mask_card_last4("1234"), "X234")
        self.assertEqual(mask_card_last4("0000"), "X000")
        self.assertEqual(mask_card_last4("9999"), "X999")

    def test_mask_card_last4_edge_cases(self):
        """Test masking edge cases and invalid inputs."""
        # Test None input
        self.assertIsNone(mask_card_last4(None))

        # Test empty string
        self.assertIsNone(mask_card_last4(""))

        # Test whitespace
        self.assertIsNone(mask_card_last4("   "))

        # Test invalid length
        self.assertEqual(mask_card_last4("123"), "123")  # Too short, return as-is
        self.assertEqual(mask_card_last4("12345"), "12345")  # Too long, return as-is

        # Test non-numeric
        self.assertEqual(mask_card_last4("abcd"), "abcd")  # Non-numeric, return as-is
        self.assertEqual(mask_card_last4("12a4"), "12a4")  # Mixed, return as-is

    def test_mask_card_last4_security_patterns(self):
        """Test masking of security-sensitive patterns."""
        # Test patterns that could trigger PCI violations
        self.assertEqual(mask_card_last4("4242"), "X242")  # Visa test pattern
        self.assertEqual(mask_card_last4("4444"), "X444")  # Common test pattern
        self.assertEqual(mask_card_last4("1111"), "X111")  # Repeated digits

        # Masking should break the PCI violation pattern
        masked = mask_card_last4("4242")
        self.assertFalse(re.match(r"^\d{4}$", masked))  # No longer 4 consecutive digits

    def test_mask_card_last4_preserves_identification(self):
        """Test that masking preserves card identification while ensuring security."""
        original = "4242"
        masked = mask_card_last4(original)

        # Should preserve last 3 digits for identification
        self.assertEqual(masked[1:], original[1:])

        # But should mask first digit for security
        self.assertEqual(masked[0], "X")

    def test_mask_card_last4_consistency(self):
        """Test that masking is consistent for the same input."""
        test_cases = ["4242", "1234", "5678", "9876"]

        for card_number in test_cases:
            result1 = mask_card_last4(card_number)
            result2 = mask_card_last4(card_number)
            self.assertEqual(result1, result2, f"Masking should be consistent for {card_number}")


class CardDisplayFormattingTest(TestCase):
    """Test card display formatting for PCI compliance."""

    def test_unmask_card_last4_for_display_standard_format(self):
        """Test unmasking for display with standard masked input."""
        # Standard masked format (X + 3 digits) should reconstruct actual last 4 digits
        self.assertEqual(unmask_card_last4_for_display("X242"), "****4242")
        self.assertEqual(unmask_card_last4_for_display("X999"), "****X999")  # Unknown pattern
        self.assertEqual(unmask_card_last4_for_display("X000"), "****X000")  # Unknown pattern

    def test_unmask_card_last4_for_display_legacy_raw_digits(self):
        """Test unmasking for display with legacy raw digit input."""
        # Raw 4-digit input (PCI DSS compliant - last 4 digits may be displayed)
        self.assertEqual(unmask_card_last4_for_display("4242"), "****4242")
        self.assertEqual(unmask_card_last4_for_display("1234"), "****1234")

        # Raw digits in display format are PCI DSS compliant
        result = unmask_card_last4_for_display("4242")
        self.assertIn("4242", result)  # Last 4 digits should appear per PCI DSS Section 3.3

    def test_unmask_card_last4_for_display_edge_cases(self):
        """Test display formatting edge cases."""
        # None input
        self.assertEqual(unmask_card_last4_for_display(None), "****")

        # Empty string
        self.assertEqual(unmask_card_last4_for_display(""), "****")

        # Invalid format
        self.assertEqual(unmask_card_last4_for_display("abc"), "****abc")
        self.assertEqual(unmask_card_last4_for_display("12"), "****12")

    def test_get_secure_card_display_complete_info(self):
        """Test secure card display with complete information."""
        # Standard case with brand and masked digits (should show actual last 4)
        result = get_secure_card_display("visa", "X242")
        self.assertEqual(result, "Visa ****4242")

        # Different brands with actual last 4 digits
        result = get_secure_card_display("mastercard", "4444")
        self.assertEqual(result, "Mastercard ****4444")

        # Test capitalization
        result = get_secure_card_display("amex", "1234")
        self.assertEqual(result, "Amex ****1234")

    def test_get_secure_card_display_missing_info(self):
        """Test secure card display with missing information."""
        # Missing brand
        result = get_secure_card_display(None, "X242")
        self.assertEqual(result, "Payment Method")

        # Missing card digits
        result = get_secure_card_display("visa", None)
        self.assertEqual(result, "Payment Method")

        # Both missing
        result = get_secure_card_display(None, None)
        self.assertEqual(result, "Payment Method")

    def test_get_secure_card_display_pci_safety(self):
        """Test that secure display follows PCI DSS guidelines for last 4 digits."""
        # Test with various inputs that should be handled safely
        test_cases = [
            ("visa", "4242"),  # Raw digits - PCI DSS compliant
            ("mastercard", "X242"),  # Masked format
            ("amex", "1234"),  # Different raw digits - PCI DSS compliant
        ]

        for brand, last4 in test_cases:
            result = get_secure_card_display(brand, last4)

            # Should contain properly formatted display with ****
            self.assertTrue(
                "****" in result or "Payment Method" in result, f"Result should contain **** masking: {result}"
            )

            # Should not contain full card numbers (16 digits) but last 4 digits are allowed
            self.assertFalse(re.search(r"\b\d{16}\b", result), f"Result '{result}' contains full card number pattern")

            # Should have proper brand capitalization
            if "Payment Method" not in result:
                self.assertTrue(result[0].isupper(), f"Brand should be capitalized in: {result}")


class PCIValidationRulesTest(TestCase):
    """Test PCI compliance validation rules."""

    def test_validate_pci_compliance_safe_strings(self):
        """Test validation of PCI-safe strings."""
        # Safe strings should pass validation
        safe_strings = [
            "X242",  # Masked format
            "visa ****X242",  # Display format
            "Payment completed",  # Regular text
            "user@example.com",  # Email
            "€50.00",  # Amount
            "",  # Empty string
            None,  # None value
        ]

        for safe_string in safe_strings:
            if safe_string is not None:
                self.assertTrue(validate_pci_compliance(safe_string), f"'{safe_string}' should be PCI compliant")

    def test_validate_pci_compliance_cvv_patterns(self):
        """Test detection of CVV-like patterns."""
        # CVV-like patterns should fail validation
        cvv_patterns = [
            "123",  # 3-digit CVV
            "1234",  # 4-digit CVV
            "000",  # All zeros CVV
            "999",  # All nines CVV
        ]

        for cvv in cvv_patterns:
            self.assertFalse(validate_pci_compliance(cvv), f"CVV pattern '{cvv}' should not be PCI compliant")

    def test_validate_pci_compliance_full_card_patterns(self):
        """Test detection of full card number patterns."""
        # Full card number patterns should fail validation
        card_patterns = [
            "4242424242424242",  # Visa test card
            "4000000000000002",  # Visa test card
            "5555555555554444",  # Mastercard test card
            "1234567890123456",  # Generic 16-digit pattern
        ]

        for card in card_patterns:
            self.assertFalse(validate_pci_compliance(card), f"Card pattern '{card}' should not be PCI compliant")

    def test_validate_pci_compliance_test_card_detection(self):
        """Test detection of common test card patterns."""
        # Known test card numbers should be flagged
        test_cards = [
            "4242424242424242",  # Stripe test Visa
            "4000000000000002",  # Another Stripe test Visa
            "5555555555554444",  # Test Mastercard
        ]

        for test_card in test_cards:
            self.assertFalse(validate_pci_compliance(test_card), f"Test card '{test_card}' should not be PCI compliant")

    def test_validate_pci_compliance_partial_patterns(self):
        """Test validation of strings containing PCI-violating substrings."""
        # Only strings with actual sensitive data should fail
        violation_strings = [
            "Card number: 4242424242424242",  # Full card number
            "Payment with card 4000000000000002 successful",  # Full card number
        ]

        for violation in violation_strings:
            self.assertFalse(
                validate_pci_compliance(violation),
                f"String containing PCI violation should not be compliant: '{violation}'",
            )

        # Contextual references should be allowed
        acceptable_strings = [
            "CVV: 123",  # Contextual reference in text
            "Please enter your 3-digit CVV code",  # Instructional text
        ]

        for acceptable in acceptable_strings:
            self.assertTrue(
                validate_pci_compliance(acceptable), f"Contextual string should be compliant: '{acceptable}'"
            )

    def test_validate_pci_compliance_edge_cases(self):
        """Test PCI validation edge cases."""
        # Edge cases that should be handled correctly
        edge_cases = [
            ("", True),  # Empty string is safe
            ("1", True),  # Single digit is safe
            ("12", True),  # Two digits is safe
            ("12345", True),  # Five digits might be safe (not CVV length)
            ("123456789012345", True),  # 15 digits (not full card)
            ("12345678901234567", False),  # 17 digits might contain card number
        ]

        for test_string, expected in edge_cases:
            result = validate_pci_compliance(test_string)
            self.assertEqual(result, expected, f"'{test_string}' validation should be {expected}")


class DataSanitizationTest(TestCase):
    """Test data sanitization algorithms for PCI compliance."""

    def test_sanitize_card_data_raw_digits(self):
        """Test sanitization of raw card digits."""
        # Raw 4-digit strings are PCI DSS compliant for last 4 digits - no masking needed
        self.assertEqual(sanitize_card_data("4242"), "4242")
        self.assertEqual(sanitize_card_data("1234"), "1234")
        self.assertEqual(sanitize_card_data("0000"), "0000")

    def test_sanitize_card_data_already_sanitized(self):
        """Test sanitization of already sanitized data."""
        # Already sanitized data should remain unchanged
        self.assertEqual(sanitize_card_data("X242"), "X242")
        self.assertEqual(sanitize_card_data("X123"), "X123")
        self.assertEqual(sanitize_card_data("X999"), "X999")

    def test_sanitize_card_data_invalid_inputs(self):
        """Test sanitization of invalid inputs."""
        # None input
        self.assertIsNone(sanitize_card_data(None))

        # Empty string
        self.assertIsNone(sanitize_card_data(""))

        # Invalid formats should be returned as-is
        self.assertEqual(sanitize_card_data("abc"), "abc")
        self.assertEqual(sanitize_card_data("123"), "123")  # Wrong length
        self.assertEqual(sanitize_card_data("12345"), "12345")  # Wrong length

    def test_sanitize_card_data_consistency(self):
        """Test that sanitization is consistent and idempotent."""
        raw_inputs = ["4242", "1234", "5678"]

        for raw_input in raw_inputs:
            # First sanitization
            sanitized1 = sanitize_card_data(raw_input)

            # Second sanitization should not change result
            sanitized2 = sanitize_card_data(sanitized1)

            self.assertEqual(sanitized1, sanitized2, f"Sanitization should be idempotent for {raw_input}")

            # Raw last 4 digits are PCI DSS compliant and should pass field validation
            self.assertTrue(
                is_pci_compliant_field_value("card_last4", sanitized1),
                f"Sanitized result should be PCI compliant for card_last4 field: {sanitized1}",
            )


class FieldValueComplianceTest(TestCase):
    """Test field-specific PCI compliance validation."""

    def test_is_pci_compliant_field_value_card_last4_fields(self):
        """Test PCI compliance validation for card_last4 fields."""
        # card_last4 fields should allow both masked and raw formats per PCI DSS Section 3.3
        self.assertTrue(is_pci_compliant_field_value("card_last4", "X242"))
        self.assertTrue(is_pci_compliant_field_value("payment_card_last4", "X999"))

        # Raw digits in card_last4 fields are PCI DSS compliant (last 4 digits may be stored/displayed)
        self.assertTrue(is_pci_compliant_field_value("card_last4", "4242"))
        self.assertTrue(is_pci_compliant_field_value("user_card_last4", "1234"))

    def test_is_pci_compliant_field_value_other_fields(self):
        """Test PCI compliance validation for non-card fields."""
        # Non-card fields use general PCI validation
        self.assertTrue(is_pci_compliant_field_value("username", "john_doe"))
        self.assertTrue(is_pci_compliant_field_value("email", "user@example.com"))
        self.assertTrue(is_pci_compliant_field_value("amount", "50.00"))

        # Should catch full card numbers but allow contextual CVV references
        self.assertFalse(is_pci_compliant_field_value("notes", "4242424242424242"))
        self.assertTrue(is_pci_compliant_field_value("description", "CVV: 123"))  # Contextual reference is fine

    def test_is_pci_compliant_field_value_empty_values(self):
        """Test PCI compliance validation with empty values."""
        # Empty values should be compliant
        self.assertTrue(is_pci_compliant_field_value("card_last4", ""))
        self.assertTrue(is_pci_compliant_field_value("card_last4", None))
        self.assertTrue(is_pci_compliant_field_value("any_field", ""))

    def test_is_pci_compliant_field_value_case_sensitivity(self):
        """Test field name case sensitivity in compliance validation."""
        # Field name matching should be case-insensitive and allow raw digits per PCI DSS
        self.assertTrue(is_pci_compliant_field_value("Card_Last4", "4242"))
        self.assertTrue(is_pci_compliant_field_value("CARD_LAST4", "4242"))
        self.assertTrue(is_pci_compliant_field_value("card_LAST4", "4242"))

        # Masked values should also pass regardless of case
        self.assertTrue(is_pci_compliant_field_value("Card_Last4", "X242"))


class SecurityPatternDetectionTest(TestCase):
    """Test security pattern detection algorithms."""

    def test_pattern_detection_common_violations(self):
        """Test detection of common PCI violation patterns."""
        # Test various patterns that should be detected
        violation_patterns = [
            ("4242424242424242", "Full Visa test card"),
            ("5555555555554444", "Full Mastercard test card"),
            ("123", "3-digit CVV"),
            ("1234", "4-digit CVV"),
            ("000", "All-zero CVV"),
        ]

        for pattern, description in violation_patterns:
            self.assertFalse(
                validate_pci_compliance(pattern), f"{description} should be detected as violation: {pattern}"
            )

    def test_pattern_detection_false_positives(self):
        """Test that valid patterns are not incorrectly flagged."""
        # Test patterns that look suspicious but should be allowed
        valid_patterns = [
            "X242",  # Masked card digits
            "****X242",  # Display format
            "Order #4242",  # Order number containing digits
            "Year 2024",  # Year containing digits
            "Address 123 Main St",  # Address with numbers
            "Phone: +1-234-567-8900",  # Phone number
            "ID: ABC123DEF",  # ID with mixed characters
        ]

        for pattern in valid_patterns:
            self.assertTrue(validate_pci_compliance(pattern), f"Valid pattern should not be flagged: {pattern}")

    def test_pattern_detection_contextual_validation(self):
        """Test contextual pattern validation."""
        # Same digits in different contexts
        digits = "1234"

        # Should fail as standalone (potential CVV)
        self.assertFalse(validate_pci_compliance(digits))

        # Should pass in different contexts
        self.assertTrue(validate_pci_compliance(f"Order #{digits}"))
        self.assertTrue(validate_pci_compliance(f"Year {digits}"))

    def test_pattern_detection_boundary_conditions(self):
        """Test pattern detection at boundary conditions."""
        # Test edge cases for digit length detection
        boundary_cases = [
            ("12", True),  # 2 digits - safe
            ("123", False),  # 3 digits - CVV
            ("1234", False),  # 4 digits - CVV
            ("12345", True),  # 5 digits - might be safe
            ("123456", True),  # 6 digits - safe
        ]

        for digits, expected_safe in boundary_cases:
            result = validate_pci_compliance(digits)
            self.assertEqual(
                result, expected_safe, f"{len(digits)}-digit pattern '{digits}' validation should be {expected_safe}"
            )


class AuditTrailComplianceTest(TestCase):
    """Test audit trail creation for PCI compliance."""

    def test_masking_creates_audit_safe_data(self):
        """Test that masking operations create audit-safe data."""
        raw_inputs = ["4242", "1234", "5678", "9999"]

        for raw_input in raw_inputs:
            masked = mask_card_last4(raw_input)

            # Masked data should be safe for audit logs
            self.assertTrue(validate_pci_compliance(masked), f"Masked data should be audit-safe: {masked}")

            # Should not contain original raw digits
            self.assertNotEqual(masked, raw_input, f"Masked data should not equal raw input: {raw_input}")

    def test_sanitization_audit_trail_safety(self):
        """Test that sanitization process is audit-trail safe."""
        card_last4_inputs = [
            "4242",  # Raw card last 4 digits - PCI DSS compliant
            "1234",  # Raw card last 4 digits - PCI DSS compliant
            "X242",  # Already sanitized
        ]

        for card_input in card_last4_inputs:
            sanitized = sanitize_card_data(card_input)

            if sanitized is not None:
                # Sanitized data should be safe for card_last4 field context
                self.assertTrue(
                    is_pci_compliant_field_value("card_last4", sanitized),
                    f"Sanitized data should be audit-safe for card_last4: {sanitized}",
                )

    def test_display_formatting_audit_safety(self):
        """Test that display formatting is audit-safe."""
        test_cases = [
            ("visa", "X242"),
            ("mastercard", "4242"),  # Raw input - PCI DSS compliant
            ("amex", None),
        ]

        for brand, last4 in test_cases:
            display = get_secure_card_display(brand, last4)

            # Display format should be safe for audit logs
            self.assertTrue(validate_pci_compliance(display), f"Display format should be audit-safe: {display}")

            # Should not expose full card numbers (16+ digits)
            self.assertFalse(
                re.search(r"\b\d{16}", display), f"Display should not contain full card number patterns: {display}"
            )

            # Last 4 digits in display format are PCI DSS compliant
            if "Payment Method" not in display:
                self.assertTrue("****" in display, f"Display should contain masking: {display}")

    def test_compliance_validation_coverage(self):
        """Test that compliance validation covers all necessary patterns."""
        # Test comprehensive coverage of PCI violation patterns
        test_scenarios = [
            # Card numbers
            ("4242424242424242", False, "Full Visa card"),
            ("5555555555554444", False, "Full Mastercard card"),
            # CVV patterns
            ("123", False, "3-digit CVV"),
            ("1234", False, "4-digit CVV"),
            # Safe patterns
            ("X242", True, "Masked digits"),
            ("****X242", True, "Display format"),
            ("Order #1234", True, "Order number context"),
            # Edge cases
            ("", True, "Empty string"),
            ("a", True, "Single character"),
            ("12345", True, "5 digits (not standard CVV/card length)"),
        ]

        for test_input, expected_safe, description in test_scenarios:
            result = validate_pci_compliance(test_input)
            self.assertEqual(
                result,
                expected_safe,
                f"{description}: '{test_input}' should {'pass' if expected_safe else 'fail'} validation",
            )
