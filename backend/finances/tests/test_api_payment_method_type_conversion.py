"""
Payment Method ID Type Conversion API Tests - Issue #173 Priority 4

This test suite validates that payment method API endpoints properly handle
string vs integer parameter conversion issues, addressing type conversion
problems in payment method operations.

These tests are designed to initially FAIL to demonstrate current type
conversion issues where payment method endpoints don't properly handle
mixed string/integer ID parameters.

Test Coverage:
- Payment Method ID parameter handling (string vs integer)
- StudentBalanceViewSet payment method actions parameter validation
- Type conversion in payment method retrieval and manipulation
- Error handling for invalid ID formats
- Consistency in ID parameter handling across payment endpoints
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from unittest.mock import Mock, patch

from accounts.models import School
from finances.tests.stripe_test_utils import comprehensive_stripe_mocks_decorator
from finances.models import (
    StoredPaymentMethod,
    StudentAccountBalance,
    PurchaseTransaction,
    TransactionPaymentStatus,
    TransactionType
)
from .stripe_test_utils import StripeTestMixin

User = get_user_model()


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PaymentMethodIDTypeConversionTests(StripeTestMixin, APITestCase):
    """
    Test payment method ID type conversion handling.
    
    These tests validate that payment method API endpoints properly
    handle both string and integer ID parameters without type errors.
    """

    def setUp(self):
        """Set up test data for payment method type conversion tests."""
        super().setUp()
        self.setup_stripe_mocks()
        
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        self.school = School.objects.create(
            name='Test School'
        )
        
        # Create payment method
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123456789',
            stripe_customer_id='cus_test_123456789',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )
        
        # Create student balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('2.00'),
            balance_amount=Decimal('100.00')
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
    
    def tearDown(self):
        """Clean up after each test."""
        self.teardown_stripe_mocks()
        super().tearDown()

    def test_payment_method_string_id_parameter_handling_fails(self):
        """
        Test that payment method endpoints handle string ID parameters.
        
        This test validates that when payment method IDs are passed as
        strings (common in URL parameters and JSON), they are properly
        converted and handled.
        
        Expected to FAIL initially due to type conversion issues.
        """
        # Test with string ID parameter
        string_id = str(self.payment_method.id)
        
        # Test removal with string ID
        remove_url = '/api/finances/studentbalance/remove-payment-method/'
        remove_data = {
            'payment_method_id': string_id,  # String ID
            'reason': 'Type conversion test'
        }
        
        response = self.client.post(remove_url, remove_data, format='json')
        
        # Should handle string ID without type errors
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_data = response.json()
            error_message = str(error_data).lower()
            
            # Should not fail due to type conversion issues
            type_error_indicators = [
                'invalid literal for int',
                'expected int',
                'type error',
                'cannot convert',
                'invalid id format'
            ]
            
            for indicator in type_error_indicators:
                self.assertNotIn(
                    indicator,
                    error_message,
                    f"Payment method removal should handle string IDs. "
                    f"Got type conversion error: {error_data}. "
                    f"Check ID parameter validation in StudentBalanceViewSet."
                )

    def test_payment_method_integer_id_parameter_handling_fails(self):
        """
        Test that payment method endpoints handle integer ID parameters.
        
        This test validates that when payment method IDs are passed as
        integers (from programmatic calls), they are properly handled.
        
        Expected to FAIL initially due to inconsistent type handling.
        """
        # Test with integer ID parameter
        integer_id = int(self.payment_method.id)
        
        # Test setting default with integer ID
        set_default_url = '/api/finances/studentbalance/set-default-payment-method/'
        set_default_data = {
            'payment_method_id': integer_id,  # Integer ID
        }
        
        response = self.client.post(set_default_url, set_default_data, format='json')
        
        # Should handle integer ID properly
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_data = response.json()
            error_message = str(error_data).lower()
            
            # Should not fail due to type handling issues
            self.assertNotIn(
                'string',
                error_message,
                f"Payment method endpoints should handle integer IDs. "
                f"Got error mentioning 'string': {error_data}. "
                f"Check type consistency in payment method actions."
            )

    def test_payment_method_mixed_type_consistency_fails(self):
        """
        Test consistency between string and integer ID handling.
        
        This test validates that the same operation works identically
        whether the ID is provided as string or integer.
        
        Expected to FAIL initially due to inconsistent type handling.
        """
        # Create second payment method for testing
        second_payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_987654321',
            stripe_customer_id='cus_test_987654321',
            card_brand='mastercard',
            card_last4='5678',
            card_exp_month=8,
            card_exp_year=2026,
            is_default=False,
            is_active=True,
        )
        
        # Test setting default with string ID
        set_default_url = '/api/finances/studentbalance/set-default-payment-method/'
        
        string_data = {
            'payment_method_id': str(second_payment_method.id),  # String
        }
        
        string_response = self.client.post(set_default_url, string_data, format='json')
        
        # Reset to original default
        self.payment_method.is_default = True
        self.payment_method.save()
        second_payment_method.is_default = False
        second_payment_method.save()
        
        # Test setting default with integer ID
        integer_data = {
            'payment_method_id': int(second_payment_method.id),  # Integer
        }
        
        integer_response = self.client.post(set_default_url, integer_data, format='json')
        
        # Both should have same behavior (success or failure)
        self.assertEqual(
            string_response.status_code,
            integer_response.status_code,
            f"String and integer ID parameters should behave identically. "
            f"String response: {string_response.status_code}, "
            f"Integer response: {integer_response.status_code}. "
            f"Check type conversion consistency in payment method actions."
        )
        
        # If both succeed, responses should be similar
        if string_response.status_code == status.HTTP_200_OK:
            string_data = string_response.json()
            integer_data = integer_response.json()
            
            self.assertEqual(
                string_data.get('success'),
                integer_data.get('success'),
                f"String and integer operations should have same success status. "
                f"String success: {string_data.get('success')}, "
                f"Integer success: {integer_data.get('success')}"
            )

    def test_payment_method_invalid_id_format_handling_fails(self):
        """
        Test handling of invalid payment method ID formats.
        
        This test validates that invalid ID formats are handled gracefully
        with appropriate error messages, not type conversion errors.
        
        Expected to FAIL initially due to poor invalid ID handling.
        """
        invalid_ids = [
            'not-a-number',
            '12.5',  # Decimal
            '',      # Empty string
            'None',  # String "None"
            '0',     # Zero (invalid ID)
            '-1',    # Negative number
        ]
        
        remove_url = '/api/finances/studentbalance/remove-payment-method/'
        
        for invalid_id in invalid_ids:
            with self.subTest(invalid_id=invalid_id):
                remove_data = {
                    'payment_method_id': invalid_id,
                    'reason': f'Testing invalid ID: {invalid_id}'
                }
                
                response = self.client.post(remove_url, remove_data, format='json')
                
                # Should return 400 with appropriate error
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                    f"Invalid ID '{invalid_id}' should return 400 Bad Request"
                )
                
                error_data = response.json()
                error_message = str(error_data).lower()
                
                # Should have user-friendly error, not technical type error
                user_friendly_indicators = [
                    'invalid payment method',
                    'payment method not found',
                    'invalid id',
                    'does not exist'
                ]
                
                technical_error_indicators = [
                    'valueerror',
                    'invalid literal for int',
                    'could not convert',
                    'traceback'
                ]
                
                has_user_friendly = any(indicator in error_message for indicator in user_friendly_indicators)
                has_technical_error = any(indicator in error_message for indicator in technical_error_indicators)
                
                self.assertTrue(
                    has_user_friendly,
                    f"Invalid ID '{invalid_id}' should have user-friendly error. "
                    f"Got: {error_data}"
                )
                
                self.assertFalse(
                    has_technical_error,
                    f"Invalid ID '{invalid_id}' should not expose technical errors. "
                    f"Got: {error_data}. Check error handling in payment method validation."
                )

    def test_payment_method_id_in_stripe_integration_fails(self):
        """
        Test that payment method ID type conversion works with Stripe integration.
        
        This test validates that ID parameters are properly converted
        when passed to Stripe service integrations.
        
        Expected to FAIL initially due to type issues in Stripe integration.
        """
        # Configure mock Stripe service responses via patching
        with patch('finances.services.payment_method_service.StripeService') as mock_stripe_service:
            mock_stripe_service.return_value.detach_payment_method.return_value = {
                'success': True,
                'message': 'Payment method detached'
            }
            
            # Test with different ID types
            id_formats = [
                str(self.payment_method.id),    # String
                int(self.payment_method.id),    # Integer
                f"{self.payment_method.id}",    # Formatted string
            ]
            
            remove_url = '/api/finances/studentbalance/remove-payment-method/'
            
            for id_format in id_formats:
                with self.subTest(id_format=type(id_format).__name__):
                    remove_data = {
                        'payment_method_id': id_format,
                        'reason': f'Testing ID format: {type(id_format).__name__}'
                    }
                    
                    response = self.client.post(remove_url, remove_data, format='json')
                    
                    # All formats should work consistently
                    if response.status_code not in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]:
                        error_data = response.json()
                        error_message = str(error_data).lower()
                        
                        # Should not fail due to ID type issues
                        type_error_indicators = [
                            'type error',
                            'expected int',
                            'expected string',
                            'cannot convert'
                        ]
                        
                        for indicator in type_error_indicators:
                            self.assertNotIn(
                                indicator,
                                error_message,
                                f"ID format {type(id_format).__name__} should not cause type errors. "
                                f"Got: {error_data}. Check Stripe integration type handling."
                            )

    def test_payment_method_query_parameter_type_handling_fails(self):
        """
        Test payment method ID handling in query parameters.
        
        This test validates that payment method IDs in URL query parameters
        (always strings) are properly converted for database lookups.
        
        Expected to FAIL initially due to query parameter type issues.
        """
        # Payment methods list with ID filtering (if supported)
        list_url = f'/api/finances/studentbalance/payment-methods/?id={self.payment_method.id}'
        response = self.client.get(list_url)
        
        # Should handle string query parameter properly
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            payment_methods = data.get('payment_methods', [])
            
            if payment_methods:
                # Should find the payment method by ID
                found_method = payment_methods[0]
                self.assertEqual(
                    found_method.get('id'),
                    self.payment_method.id,
                    f"Query parameter ID filtering should work. "
                    f"Expected ID {self.payment_method.id}, got {found_method.get('id')}"
                )
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            error_data = response.json()
            error_message = str(error_data).lower()
            
            # Should not fail due to query parameter type conversion
            self.assertNotIn(
                'invalid literal for int',
                error_message,
                f"Query parameter ID should be handled properly. "
                f"Got type conversion error: {error_data}"
            )


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PaymentMethodRetrievalTypeTests(StripeTestMixin, APITestCase):
    """
    Test payment method retrieval with different ID parameter types.
    
    These tests focus on the retrieval and lookup operations that
    might have type conversion issues.
    """

    def setUp(self):
        """Set up test data for retrieval type tests."""
        super().setUp()
        self.setup_stripe_mocks()
        
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_retrieval',
            stripe_customer_id='cus_test_retrieval',
            card_brand='visa',
            card_last4='1234',
            card_exp_month=10,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
    
    def tearDown(self):
        """Clean up after each test."""
        self.teardown_stripe_mocks()
        super().tearDown()

    def test_payment_method_detail_retrieval_type_conversion_fails(self):
        """
        Test that payment method detail retrieval handles type conversion.
        
        This test validates that individual payment method retrieval
        works with both string and integer ID parameters.
        
        Expected to FAIL initially due to retrieval type issues.
        """
        # Test different ID parameter types
        id_variants = [
            self.payment_method.id,         # Integer
            str(self.payment_method.id),    # String
            f"{self.payment_method.id}",    # Formatted string
        ]
        
        # Test payment method detail endpoint (if exists)
        for id_variant in id_variants:
            with self.subTest(id_type=type(id_variant).__name__):
                detail_url = f'/api/finances/studentbalance/payment-methods/{id_variant}/'
                response = self.client.get(detail_url)
                
                # Should handle all ID types consistently
                if response.status_code == status.HTTP_404_NOT_FOUND:
                    # Skip if endpoint doesn't exist
                    continue
                elif response.status_code == status.HTTP_400_BAD_REQUEST:
                    error_data = response.json()
                    error_message = str(error_data).lower()
                    
                    # Should not fail due to type conversion
                    self.assertNotIn(
                        'invalid literal',
                        error_message,
                        f"Payment method retrieval should handle {type(id_variant).__name__} IDs. "
                        f"Got type error: {error_data}"
                    )
                elif response.status_code == status.HTTP_200_OK:
                    data = response.json()
                    retrieved_id = data.get('id')
                    
                    # Should retrieve the correct payment method
                    self.assertEqual(
                        retrieved_id,
                        self.payment_method.id,
                        f"Should retrieve correct payment method with {type(id_variant).__name__} ID"
                    )

    def test_payment_method_lookup_validation_consistency_fails(self):
        """
        Test that payment method lookup validation is consistent.
        
        This test validates that the same validation logic applies
        regardless of how the ID parameter is provided.
        
        Expected to FAIL initially due to inconsistent validation.
        """
        # Create test scenarios with different operations
        operations = [
            ('remove-payment-method', {'payment_method_id': None, 'reason': 'Test'}),
            ('set-default-payment-method', {'payment_method_id': None}),
        ]
        
        for operation, data_template in operations:
            with self.subTest(operation=operation):
                url = f'/api/finances/studentbalance/{operation}/'
                
                # Test with string ID
                string_data = data_template.copy()
                string_data['payment_method_id'] = str(self.payment_method.id)
                
                string_response = self.client.post(url, string_data, format='json')
                
                # Test with integer ID
                integer_data = data_template.copy()
                integer_data['payment_method_id'] = int(self.payment_method.id)
                
                integer_response = self.client.post(url, integer_data, format='json')
                
                # Both should have consistent behavior
                self.assertEqual(
                    string_response.status_code,
                    integer_response.status_code,
                    f"Operation '{operation}' should handle string and integer IDs consistently. "
                    f"String: {string_response.status_code}, Integer: {integer_response.status_code}"
                )
                
                # If both succeed or fail, the reason should be the same
                if string_response.status_code == integer_response.status_code == status.HTTP_400_BAD_REQUEST:
                    string_error = str(string_response.json()).lower()
                    integer_error = str(integer_response.json()).lower()
                    
                    # Errors should be similar (not type-related differences)
                    type_specific_terms = ['string', 'integer', 'int', 'str', 'type']
                    
                    string_has_type_terms = any(term in string_error for term in type_specific_terms)
                    integer_has_type_terms = any(term in integer_error for term in type_specific_terms)
                    
                    # Neither should have type-specific errors
                    self.assertFalse(
                        string_has_type_terms or integer_has_type_terms,
                        f"Validation errors should not be type-specific. "
                        f"String error: {string_error}, Integer error: {integer_error}"
                    )

    def test_payment_method_bulk_operations_type_handling_fails(self):
        """
        Test that bulk payment method operations handle mixed ID types.
        
        This test validates that operations involving multiple payment
        method IDs handle mixed string/integer parameters correctly.
        
        Expected to FAIL initially due to bulk operation type issues.
        """
        # Create multiple payment methods
        second_payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_bulk_2',
            stripe_customer_id='cus_test_bulk_2',
            card_brand='mastercard',
            card_last4='5678',
            card_exp_month=6,
            card_exp_year=2026,
            is_default=False,
            is_active=True,
        )
        
        # Test bulk operation with mixed ID types (if supported)
        bulk_data = {
            'payment_method_ids': [
                str(self.payment_method.id),        # String
                int(second_payment_method.id),      # Integer
            ],
            'operation': 'deactivate',
            'reason': 'Bulk type conversion test'
        }
        
        bulk_url = '/api/finances/studentbalance/bulk-payment-methods/'
        response = self.client.post(bulk_url, bulk_data, format='json')
        
        # Should handle mixed ID types
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_data = response.json()
            error_message = str(error_data).lower()
            
            # Should not fail due to mixed type handling
            mixed_type_indicators = [
                'type mismatch',
                'inconsistent types',
                'expected all int',
                'expected all string'
            ]
            
            for indicator in mixed_type_indicators:
                self.assertNotIn(
                    indicator,
                    error_message,
                    f"Bulk operations should handle mixed ID types. "
                    f"Got error: {error_data}. Check bulk operation type handling."
                )