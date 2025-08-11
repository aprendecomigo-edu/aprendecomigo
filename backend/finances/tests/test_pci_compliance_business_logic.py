"""
PCI Compliance Business Logic Tests for Payment System

This test suite validates PCI compliance at the business logic layer, focusing on:
- StoredPaymentMethod model data validation and storage
- Payment method creation services and data sanitization  
- Card display methods and masking logic
- Internal business logic for secure card data handling

These tests are designed to FAIL initially to demonstrate current PCI violations
in the business logic before implementing security fixes.

Critical PCI DSS Requirements Tested:
- Requirement 3: Protect stored cardholder data
- Requirement 4: Encrypt transmission of cardholder data across open, public networks
- No raw PANs (Primary Account Numbers) stored
- No CVV/CVV2/CVC2/CID values stored
- Proper data masking for display purposes

Test Coverage:
1. Model-level PCI compliance validation
2. Payment method creation business logic security
3. Card display and masking methods
4. Payment method service layer security
5. Data validation and sanitization logic
"""

import re
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from finances.models import (
    StoredPaymentMethod,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.services.payment_method_service import PaymentMethodService
from finances.services.renewal_payment_service import RenewalPaymentService

User = get_user_model()


class StoredPaymentMethodModelPCIComplianceTests(TestCase):
    """
    Test PCI compliance for StoredPaymentMethod model business logic.
    
    Validates that the model properly handles card data storage,
    validation, and display methods in compliance with PCI DSS.
    """

    def setUp(self):
        """Set up test data for model tests."""
        self.student = User.objects.create_user(
            email='test@example.com',
            name='Test Student',
        )

    def test_card_last4_should_not_store_raw_digits(self):
        """
        Test that card_last4 field does not store raw card digits.
        
        CRITICAL: This test will FAIL initially to demonstrate the current
        PCI violation where raw card digits are stored directly.
        
        PCI DSS Requirement 3.3: Mask PAN when displayed
        """
        # Create payment method with current vulnerable pattern
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_pci_violation',
            stripe_customer_id='cus_test_pci',
            card_brand='visa',
            card_last4='4242',  # This is the PCI violation - raw digits
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )
        
        # CRITICAL PCI COMPLIANCE CHECK - This will FAIL initially
        self.assertNotRegex(
            payment_method.card_last4,
            r'^\d{4}$',
            f"StoredPaymentMethod.card_last4 stores raw digits: '{payment_method.card_last4}'. "
            f"This violates PCI DSS Requirement 3.3 - PAN must be masked when displayed."
        )

    def test_card_last4_validation_should_reject_cvv_patterns(self):
        """
        Test that card_last4 field validation rejects CVV-like patterns.
        
        CRITICAL: This test will FAIL initially because there's no validation
        to prevent CVV-like patterns in the card_last4 field.
        
        PCI DSS Requirement 3.2: Do not store sensitive authentication data
        """
        # Test CVV-like patterns that should be rejected
        cvv_patterns = ['123', '456', '789', '000']
        
        for cvv_pattern in cvv_patterns:
            with self.subTest(cvv_pattern=cvv_pattern):
                with self.assertRaises(ValidationError, 
                    msg=f"Model should reject CVV-like pattern: '{cvv_pattern}'"
                ):
                    payment_method = StoredPaymentMethod(
                        student=self.student,
                        stripe_payment_method_id=f'pm_test_{cvv_pattern}',
                        stripe_customer_id='cus_test_cvv',
                        card_brand='visa',
                        card_last4=cvv_pattern,  # CVV-like pattern should be rejected
                        card_exp_month=12,
                        card_exp_year=2025,
                        is_default=False,
                        is_active=True,
                    )
                    payment_method.full_clean()  # This should raise ValidationError

    def test_card_display_property_should_mask_digits(self):
        """
        Test that card_display property properly masks card digits.
        
        CRITICAL: This test will FAIL initially because the current
        implementation exposes raw digits in the display format.
        
        PCI DSS Requirement 3.3: Mask PAN when displayed (show only first 6 and last 4)
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_display',
            stripe_customer_id='cus_test_display',
            card_brand='mastercard',
            card_last4='5678',  # Raw digits that should be masked
            card_exp_month=8,
            card_exp_year=2024,
            is_default=False,
            is_active=True,
        )
        
        card_display = payment_method.card_display
        
        # CRITICAL: Display should not end with raw digits
        # This test will FAIL initially due to format like "Mastercard ****5678"
        self.assertNotRegex(
            card_display,
            r'\d{4}$',
            f"card_display property exposes raw digits at end: '{card_display}'. "
            f"Should use masked format like '**** **** **** 5678' or 'ending in 5678'"
        )
        
        # Additional check: should not contain consecutive unmasked digits
        digit_sequences = re.findall(r'\d{3,}', card_display)
        self.assertEqual(
            len(digit_sequences), 0,
            f"card_display contains unmasked digit sequences: {digit_sequences} in '{card_display}'"
        )

    def test_str_method_should_mask_card_data(self):
        """
        Test that __str__ method properly masks card data.
        
        CRITICAL: This test will FAIL initially because the __str__ method
        exposes raw card digits in the string representation.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_str',
            stripe_customer_id='cus_test_str',
            card_brand='visa',
            card_last4='9999',
            card_exp_month=6,
            card_exp_year=2026,
            is_default=True,
            is_active=True,
        )
        
        str_representation = str(payment_method)
        
        # Should not expose raw digits in string representation
        self.assertNotRegex(
            str_representation,
            r'\*{4}\d{4}',
            f"__str__ method exposes raw digits: '{str_representation}'"
        )

    def test_model_clean_should_validate_pci_compliance(self):
        """
        Test that model clean() method validates PCI compliance.
        
        CRITICAL: This test will FAIL initially because there's no
        PCI validation in the model's clean() method.
        """
        # Test that clean() method rejects raw card data patterns
        payment_method = StoredPaymentMethod(
            student=self.student,
            stripe_payment_method_id='pm_test_clean',
            stripe_customer_id='cus_test_clean',
            card_brand='visa',
            card_last4='1111',  # Raw digits should be rejected
            card_exp_month=12,
            card_exp_year=2025,
            is_default=False,
            is_active=True,
        )
        
        # This should raise ValidationError due to PCI compliance check
        with self.assertRaises(ValidationError, 
            msg="Model clean() should reject raw card digits for PCI compliance"
        ):
            payment_method.clean()

    def test_save_method_should_enforce_pci_masking(self):
        """
        Test that save() method enforces PCI-compliant data masking.
        
        CRITICAL: This test will FAIL initially because save() doesn't
        automatically mask card data before storage.
        """
        # Attempt to save raw card data
        payment_method = StoredPaymentMethod(
            student=self.student,
            stripe_payment_method_id='pm_test_save',
            stripe_customer_id='cus_test_save', 
            card_brand='amex',
            card_last4='3456',  # Raw digits
            card_exp_month=9,
            card_exp_year=2027,
            is_default=False,
            is_active=True,
        )
        
        payment_method.save()
        
        # After save, card_last4 should be masked, not raw digits
        saved_payment_method = StoredPaymentMethod.objects.get(pk=payment_method.pk)
        self.assertNotRegex(
            saved_payment_method.card_last4,
            r'^\d{4}$',
            f"save() method allows raw digits to be stored: '{saved_payment_method.card_last4}'"
        )


class PaymentMethodServicePCIComplianceTests(TestCase):
    """
    Test PCI compliance for PaymentMethodService business logic.
    
    Validates that payment method service operations maintain
    PCI compliance when creating and managing payment methods.
    """

    def setUp(self):
        """Set up test data for service tests."""
        self.student = User.objects.create_user(
            email='service@example.com',
            name='Service Test Student',
        )
        self.service = PaymentMethodService()

    @patch('finances.services.payment_method_service.StripeService')
    def test_add_payment_method_should_mask_card_data(self, mock_stripe_service_class):
        """
        Test that add_payment_method service masks card data from Stripe.
        
        CRITICAL: This test will FAIL initially because the service
        directly stores raw card data received from Stripe.
        
        PCI DSS Requirement 3.3: Mask PAN when displayed
        """
        # Mock Stripe service responses
        mock_stripe_service = mock_stripe_service_class.return_value
        
        # Mock payment method with raw card data (as received from Stripe)
        mock_payment_method = Mock()
        mock_payment_method.id = 'pm_test_service'
        mock_payment_method.type = 'card'
        mock_payment_method.card = {
            'brand': 'visa',
            'last4': '4242',  # Raw data from Stripe that should be masked
            'exp_month': 12,
            'exp_year': 2025
        }
        
        mock_stripe_service.retrieve_payment_method.return_value = {
            'success': True,
            'payment_method': mock_payment_method.card  # Stripe card data
        }
        
        mock_stripe_service.create_customer.return_value = {
            'success': True,
            'customer_id': 'cus_service_test',
            'customer': Mock(id='cus_service_test')
        }
        
        mock_stripe_service.attach_payment_method_to_customer.return_value = {
            'success': True,
            'payment_method': mock_payment_method
        }
        
        # Add payment method through service
        result = self.service.add_payment_method(
            student_user=self.student,
            stripe_payment_method_id='pm_test_service',
            is_default=False
        )
        
        self.assertTrue(result['success'])
        
        # Verify payment method was created
        payment_method = StoredPaymentMethod.objects.get(
            stripe_payment_method_id='pm_test_service'
        )
        
        # CRITICAL: Service should mask card data before storage
        # This test will FAIL initially because raw data is stored
        self.assertNotRegex(
            payment_method.card_last4,
            r'^\d{4}$',
            f"PaymentMethodService stores raw card_last4: '{payment_method.card_last4}'. "
            f"Service should mask data from Stripe before storage."
        )

    @patch('finances.services.payment_method_service.StripeService')
    def test_add_payment_method_should_reject_suspicious_patterns(self, mock_stripe_service_class):
        """
        Test that add_payment_method rejects suspicious data patterns.
        
        CRITICAL: This test will FAIL initially because there's no
        validation for suspicious patterns that might be CVV data.
        """
        mock_stripe_service = mock_stripe_service_class.return_value
        
        # Mock Stripe response with suspicious pattern (looks like CVV)
        mock_stripe_service.retrieve_payment_method.return_value = {
            'success': True,
            'payment_method': {
                'brand': 'visa',
                'last4': '123',  # Suspicious 3-digit pattern
                'exp_month': 12,
                'exp_year': 2025
            }
        }
        
        mock_stripe_service.create_customer.return_value = {
            'success': True,
            'customer_id': 'cus_suspicious_test',
            'customer': Mock(id='cus_suspicious_test')
        }
        
        # This should fail due to suspicious pattern validation
        result = self.service.add_payment_method(
            student_user=self.student,
            stripe_payment_method_id='pm_suspicious_pattern',
            is_default=False
        )
        
        # Should reject suspicious patterns
        self.assertFalse(result['success'], 
            "Service should reject suspicious 3-digit patterns that could be CVV data")
        self.assertIn('suspicious_pattern', result.get('error_type', ''))

    def test_get_payment_methods_should_return_masked_data(self):
        """
        Test that get_payment_methods returns properly masked card data.
        
        CRITICAL: This test will FAIL initially because the service
        returns raw card data instead of properly masked data.
        """
        # Create payment method with raw data (current vulnerable state)
        StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_get_methods',
            stripe_customer_id='cus_test_get_methods',
            card_brand='mastercard',
            card_last4='7890',  # Raw digits
            card_exp_month=6,
            card_exp_year=2024,
            is_default=True,
            is_active=True,
        )
        
        # Get payment methods through service
        payment_methods = self.service.get_student_payment_methods(self.student)
        
        self.assertEqual(len(payment_methods), 1)
        payment_method = payment_methods[0]
        
        # CRITICAL: Service should return masked data
        # This test will FAIL initially
        card_display = payment_method.get('card_display', '')
        self.assertNotRegex(
            card_display,
            r'\d{4}$',
            f"get_payment_methods returns raw digits: '{card_display}'"
        )


class CardDataMaskingBusinessLogicTests(TestCase):
    """
    Test business logic for card data masking and display methods.
    
    Validates various scenarios where card data needs to be properly
    masked according to PCI DSS requirements.
    """

    def setUp(self):
        """Set up test data for masking logic tests."""
        self.student = User.objects.create_user(
            email='masking@example.com',
            name='Masking Test Student',
        )

    def test_card_masking_utility_functions(self):
        """
        Test utility functions for card data masking.
        
        CRITICAL: This test will FAIL initially because masking utility
        functions don't exist in the current implementation.
        """
        from finances.utils import mask_card_number, is_safe_card_display
        
        # Test card number masking
        test_cases = [
            ('4242424242424242', '**** **** **** 4242'),
            ('5555555555554444', '**** **** **** 4444'),
            ('378282246310005', '**** ****** *0005'),  # AMEX format
        ]
        
        for card_number, expected_masked in test_cases:
            with self.subTest(card_number=card_number):
                masked = mask_card_number(card_number)
                self.assertEqual(masked, expected_masked)
                self.assertTrue(is_safe_card_display(masked))
                
                # Should not expose more than 4 consecutive digits
                consecutive_digits = re.findall(r'\d{5,}', masked)
                self.assertEqual(len(consecutive_digits), 0)

    def test_secure_card_display_patterns(self):
        """
        Test that card display follows secure patterns.
        
        Validates that card display methods produce PCI-compliant output
        that doesn't expose sensitive information.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_secure_display',
            stripe_customer_id='cus_test_secure_display',
            card_brand='discover',
            card_last4='1234',
            card_exp_month=3,
            card_exp_year=2028,
            is_default=False,
            is_active=True,
        )
        
        # Test various display methods
        display_methods = [
            payment_method.card_display,
            str(payment_method),
            payment_method.get_secure_display(),  # This method should exist
        ]
        
        for display_text in display_methods:
            with self.subTest(display_method=display_text):
                # Should not contain raw digits at the end
                self.assertNotRegex(
                    display_text,
                    r'\*{4}\d{4}$',
                    f"Display method exposes raw digits: '{display_text}'"
                )
                
                # Should follow safe patterns
                self.assertRegex(
                    display_text,
                    r'.*(\*{4}|\*{6}|ending in|termina em).*',
                    f"Display should use masked format: '{display_text}'"
                )

    def test_payment_method_serialization_security(self):
        """
        Test that payment method data serialization maintains PCI compliance.
        
        CRITICAL: This test will FAIL initially because serialization
        may expose raw card data in various formats.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_serialization',
            stripe_customer_id='cus_test_serialization',
            card_brand='visa',
            card_last4='8888',
            card_exp_month=11,
            card_exp_year=2029,
            is_default=True,
            is_active=True,
        )
        
        # Test model_to_dict serialization security
        from django.forms.models import model_to_dict
        serialized_data = model_to_dict(payment_method)
        
        # Serialized data should not expose raw card digits
        card_last4 = str(serialized_data.get('card_last4', ''))
        self.assertNotRegex(
            card_last4,
            r'^\d{4}$',
            f"model_to_dict exposes raw card_last4: '{card_last4}'"
        )
        
        # Test JSON serialization safety
        import json
        from django.core import serializers
        
        json_data = serializers.serialize('json', [payment_method])
        json_dict = json.loads(json_data)[0]
        
        fields = json_dict.get('fields', {})
        serialized_card_last4 = fields.get('card_last4', '')
        
        self.assertNotRegex(
            str(serialized_card_last4),
            r'^\d{4}$',
            f"JSON serialization exposes raw card_last4: '{serialized_card_last4}'"
        )


class RenewalPaymentServicePCIComplianceTests(TestCase):
    """
    Test PCI compliance for RenewalPaymentService business logic.
    
    Validates that renewal payment operations maintain PCI compliance
    when processing payments with stored payment methods.
    """

    def setUp(self):
        """Set up test data for renewal service tests."""
        self.student = User.objects.create_user(
            email='renewal@example.com',
            name='Renewal Test Student',
        )
        
        # Create student balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('3.00'),
            balance_amount=Decimal('75.00')
        )
        
        # Create payment method with raw data (current vulnerable state)
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_renewal_test',
            stripe_customer_id='cus_renewal_test',
            card_brand='visa',
            card_last4='2222',  # Raw digits - PCI violation
            card_exp_month=7,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )
        
        # Create original transaction for renewal
        self.original_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_original_renewal',
            stripe_customer_id='cus_renewal_test',
            metadata={
                'subscription_name': 'Premium Plan',
                'billing_cycle': 'monthly'
            }
        )
        
        self.renewal_service = RenewalPaymentService()

    def test_renewal_service_should_not_expose_payment_method_data(self):
        """
        Test that renewal service internal operations don't expose payment method data.
        
        CRITICAL: This test may FAIL if internal service methods
        log or expose sensitive payment method information.
        """
        # Mock renewal operation
        with patch('finances.services.renewal_payment_service.stripe') as mock_stripe:
            mock_payment_intent = Mock()
            mock_payment_intent.id = 'pi_renewal_test'
            mock_payment_intent.status = 'succeeded'
            
            mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
            mock_stripe.PaymentIntent.confirm.return_value = mock_payment_intent
            
            # Perform renewal operation
            result = self.renewal_service.process_subscription_renewal(
                self.original_transaction.id,
                self.student
            )
            
            # Service result should not expose payment method details
            result_str = str(result)
            
            # Should not contain sensitive data in service response
            sensitive_patterns = [
                r'\b\d{4}\b',  # 4-digit sequences
                r'card_last4',
                r'4242|2222|1234',  # Common test card patterns
            ]
            
            for pattern in sensitive_patterns:
                self.assertNotRegex(
                    result_str,
                    pattern,
                    f"Renewal service exposes sensitive data matching pattern '{pattern}' in: {result_str}"
                )

    def test_renewal_transaction_metadata_should_not_include_card_data(self):
        """
        Test that renewal transaction metadata doesn't include card data.
        
        CRITICAL: This test will FAIL initially if transaction metadata
        accidentally includes payment method information.
        """
        # Mock successful renewal
        with patch('finances.services.renewal_payment_service.stripe') as mock_stripe:
            mock_payment_intent = Mock()
            mock_payment_intent.id = 'pi_renewal_metadata_test'
            mock_payment_intent.status = 'succeeded'
            
            mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
            mock_stripe.PaymentIntent.confirm.return_value = mock_payment_intent
            
            # Process renewal
            result = self.renewal_service.process_subscription_renewal(
                self.original_transaction.id,
                self.student
            )
            
            if result['success']:
                # Check created transaction metadata
                new_transaction = PurchaseTransaction.objects.filter(
                    stripe_payment_intent_id='pi_renewal_metadata_test'
                ).first()
                
                if new_transaction:
                    metadata = new_transaction.metadata or {}
                    metadata_str = str(metadata)
                    
                    # Metadata should not contain card information
                    card_data_patterns = [
                        r'\b\d{4}\b',  # 4-digit sequences
                        r'card_last4|card_brand|card_exp',
                        r'payment_method_id',
                        r'2222|4242|1234|5555',  # Test card patterns
                    ]
                    
                    for pattern in card_data_patterns:
                        self.assertNotRegex(
                            metadata_str,
                            pattern,
                            f"Transaction metadata contains card data pattern '{pattern}': {metadata_str}"
                        )

    def test_payment_processing_logs_should_not_expose_card_data(self):
        """
        Test that payment processing doesn't log sensitive card data.
        
        This test checks that business logic logging maintains PCI compliance
        by not exposing sensitive payment method information in logs.
        """
        import logging
        from io import StringIO
        
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger('finances.services.renewal_payment_service')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        try:
            with patch('finances.services.renewal_payment_service.stripe') as mock_stripe:
                mock_payment_intent = Mock()
                mock_payment_intent.id = 'pi_log_test'
                mock_payment_intent.status = 'succeeded'
                
                mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
                mock_stripe.PaymentIntent.confirm.return_value = mock_payment_intent
                
                # Process renewal (this may generate logs)
                self.renewal_service.process_subscription_renewal(
                    self.original_transaction.id,
                    self.student
                )
                
                # Check log output for sensitive data
                log_contents = log_capture.getvalue()
                
                # Logs should not contain card data
                sensitive_log_patterns = [
                    r'\b\d{16}\b',  # Full card numbers
                    r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b',  # Formatted card numbers
                    r'card_last4.*\d{4}',  # card_last4 with digits
                    r'2222|4242',  # Test card digits
                ]
                
                for pattern in sensitive_log_patterns:
                    self.assertNotRegex(
                        log_contents,
                        pattern,
                        f"Payment processing logs expose sensitive data pattern '{pattern}'"
                    )
        
        finally:
            logger.removeHandler(handler)


class PCIComplianceUtilityTests(TestCase):
    """
    Test utility functions and helpers for PCI compliance.
    
    Validates that utility functions properly handle sensitive data
    and provide secure alternatives for common operations.
    """

    def test_pci_validation_utility_functions(self):
        """
        Test utility functions for PCI compliance validation.
        
        CRITICAL: This test will FAIL initially because PCI validation
        utility functions don't exist in the current implementation.
        """
        from finances.utils import (
            is_pci_compliant_display,
            sanitize_card_data,
            validate_no_cvv_pattern,
        )
        
        # Test PCI compliance validation
        test_cases = [
            ('4242', False),  # Raw digits - not compliant
            ('****4242', False),  # Still exposes raw ending
            ('**** **** **** 4242', True),  # Proper masking
            ('Visa ending in 4242', True),  # Descriptive format
            ('•••• •••• •••• 4242', True),  # Alternative masking
        ]
        
        for display_text, expected_compliant in test_cases:
            with self.subTest(display=display_text):
                is_compliant = is_pci_compliant_display(display_text)
                self.assertEqual(
                    is_compliant, expected_compliant,
                    f"PCI compliance check incorrect for: '{display_text}'"
                )

    def test_card_data_sanitization(self):
        """
        Test that card data sanitization removes sensitive information.
        
        CRITICAL: This test will FAIL initially because sanitization
        functions don't exist in the current implementation.
        """
        from finances.utils import sanitize_for_storage, sanitize_for_display
        
        # Test data sanitization
        raw_card_data = {
            'number': '4242424242424242',
            'cvc': '123',
            'exp_month': 12,
            'exp_year': 2025,
            'last4': '4242',
        }
        
        # Sanitize for storage
        storage_safe = sanitize_for_storage(raw_card_data)
        
        # Should not contain sensitive data
        self.assertNotIn('number', storage_safe)
        self.assertNotIn('cvc', storage_safe)
        
        # Should mask last4 for storage
        self.assertNotRegex(
            storage_safe.get('card_last4', ''),
            r'^\d{4}$',
            "sanitize_for_storage should mask card_last4"
        )
        
        # Sanitize for display
        display_safe = sanitize_for_display(raw_card_data)
        
        # Should provide safe display format
        self.assertRegex(
            display_safe.get('card_display', ''),
            r'.*\*.*',
            "sanitize_for_display should include masking characters"
        )

    def test_cvv_pattern_detection(self):
        """
        Test detection of patterns that might be CVV data.
        
        This helps prevent accidental storage of CVV-like patterns
        in fields that should only contain card identification data.
        """
        from finances.utils import contains_potential_cvv_pattern
        
        # Test cases for CVV pattern detection
        cvv_test_cases = [
            ('123', True),  # 3-digit CVV
            ('1234', True),  # 4-digit CVV (AMEX)
            ('42424', False),  # 5 digits - not CVV
            ('ab123', False),  # Mixed characters
            ('000', True),  # All zeros still CVV pattern
            ('999', True),  # All nines still CVV pattern
        ]
        
        for test_value, should_detect_cvv in cvv_test_cases:
            with self.subTest(value=test_value):
                has_cvv_pattern = contains_potential_cvv_pattern(test_value)
                self.assertEqual(
                    has_cvv_pattern, should_detect_cvv,
                    f"CVV detection incorrect for: '{test_value}'"
                )


class PCIComplianceIntegrationTests(TestCase):
    """
    Integration tests for PCI compliance across the payment system.
    
    Tests end-to-end scenarios to ensure PCI compliance is maintained
    throughout the entire payment processing workflow.
    """

    def setUp(self):
        """Set up test data for integration tests."""
        self.student = User.objects.create_user(
            email='integration@example.com',
            name='Integration Test Student',
        )

    def test_complete_payment_method_lifecycle_pci_compliance(self):
        """
        Test complete payment method lifecycle maintains PCI compliance.
        
        This integration test covers the full lifecycle:
        1. Payment method creation
        2. Storage and retrieval
        3. Display and serialization
        4. Updates and modifications
        5. Usage in payments
        
        CRITICAL: This test will FAIL initially due to multiple PCI violations
        throughout the payment method lifecycle.
        """
        service = PaymentMethodService()
        
        with patch('finances.services.payment_method_service.StripeService') as mock_stripe_service_class:
            mock_stripe_service = mock_stripe_service_class.return_value
            
            # Mock Stripe responses with raw card data
            mock_stripe_service.retrieve_payment_method.return_value = {
                'success': True,
                'payment_method': {
                    'brand': 'visa',
                    'last4': '4242',  # Raw data from Stripe
                    'exp_month': 12,
                    'exp_year': 2025
                }
            }
            
            mock_stripe_service.create_customer.return_value = {
                'success': True,
                'customer_id': 'cus_integration_test',
                'customer': Mock(id='cus_integration_test')
            }
            
            mock_stripe_service.attach_payment_method_to_customer.return_value = {
                'success': True,
                'payment_method': Mock()
            }
            
            # Step 1: Create payment method
            result = service.add_payment_method(
                student_user=self.student,
                stripe_payment_method_id='pm_integration_test',
                is_default=True
            )
            
            self.assertTrue(result['success'])
            
            # Step 2: Retrieve and validate storage compliance
            payment_method = StoredPaymentMethod.objects.get(
                stripe_payment_method_id='pm_integration_test'
            )
            
            # CRITICAL: Throughout lifecycle, should never expose raw card data
            lifecycle_checks = [
                ('model.card_last4', payment_method.card_last4),
                ('model.card_display', payment_method.card_display),
                ('model.__str__', str(payment_method)),
            ]
            
            for check_name, check_value in lifecycle_checks:
                # Should not contain raw digits
                self.assertNotRegex(
                    str(check_value),
                    r'^\d{4}$|.*\*{4}\d{4}$',
                    f"PCI violation in {check_name}: '{check_value}'"
                )
            
            # Step 3: Test serialization compliance
            from django.core import serializers
            json_data = serializers.serialize('json', [payment_method])
            
            # Serialized data should not expose raw card digits
            self.assertNotRegex(
                json_data,
                r'"card_last4":\s*"?\d{4}"?',
                f"JSON serialization exposes raw card data: {json_data}"
            )
            
            # Step 4: Test usage in payment processing (mock)
            with patch('finances.services.renewal_payment_service.stripe') as mock_renewal_stripe:
                mock_payment_intent = Mock()
                mock_payment_intent.id = 'pi_integration_test'
                mock_payment_intent.status = 'succeeded'
                
                mock_renewal_stripe.PaymentIntent.create.return_value = mock_payment_intent
                
                # Create a transaction that would use this payment method
                transaction = PurchaseTransaction.objects.create(
                    student=self.student,
                    transaction_type=TransactionType.PACKAGE,
                    amount=Decimal('50.00'),
                    payment_status=TransactionPaymentStatus.COMPLETED,
                    stripe_payment_intent_id='pi_integration_test',
                    stripe_customer_id='cus_integration_test',
                )
                
                # Transaction should not contain payment method details
                transaction_str = str(transaction)
                metadata_str = str(transaction.metadata or {})
                
                for data_str in [transaction_str, metadata_str]:
                    self.assertNotRegex(
                        data_str,
                        r'\b\d{4}\b',
                        f"Transaction data contains card digits: {data_str}"
                    )

    def test_error_handling_maintains_pci_compliance(self):
        """
        Test that error handling throughout the system maintains PCI compliance.
        
        CRITICAL: This test may FAIL if error messages, exception details,
        or logging accidentally expose sensitive payment method information.
        """
        # Create payment method for error testing
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_error_test',
            stripe_customer_id='cus_error_test',
            card_brand='visa',
            card_last4='5555',
            card_exp_month=1,
            card_exp_year=2020,  # Expired card
            is_default=True,
            is_active=True,
        )
        
        service = PaymentMethodService()
        
        # Test various error scenarios
        error_scenarios = [
            # Invalid Stripe payment method
            ('pm_invalid_12345', 'Invalid Stripe payment method'),
            # Expired payment method operations
            ('pm_expired_12345', 'Expired payment method error'),
        ]
        
        for invalid_pm_id, scenario_desc in error_scenarios:
            with self.subTest(scenario=scenario_desc):
                try:
                    with patch('finances.services.payment_method_service.StripeService') as mock_stripe_service_class:
                        mock_stripe_service = mock_stripe_service_class.return_value
                        mock_stripe_service.retrieve_payment_method.return_value = {
                            'success': False,
                            'error': 'Payment method not found',
                            'error_type': 'invalid_request'
                        }
                        
                        # Attempt operation that should fail
                        result = service.add_payment_method(
                            student_user=self.student,
                            stripe_payment_method_id=invalid_pm_id,
                            is_default=False
                        )
                        
                        # Error response should not contain sensitive data
                        error_str = str(result)
                        self.assertNotRegex(
                            error_str,
                            r'\b\d{4}\b',
                            f"Error response contains card digits: {error_str}"
                        )
                        
                        # Should not expose payment method details in errors
                        sensitive_fields = [
                            'card_last4', 'stripe_payment_method_id',
                            'stripe_customer_id', '5555'
                        ]
                        
                        for sensitive_field in sensitive_fields:
                            self.assertNotIn(
                                sensitive_field, error_str,
                                f"Error exposes sensitive field '{sensitive_field}': {error_str}"
                            )
                
                except Exception as e:
                    # Even exceptions should not expose card data
                    exception_str = str(e)
                    self.assertNotRegex(
                        exception_str,
                        r'\b\d{4}\b',
                        f"Exception exposes card digits: {exception_str}"
                    )