"""
Unit tests for PaymentMethodService business logic - ID parameter type handling.

This test suite validates that PaymentMethodService methods properly handle 
integer ID parameters and fail gracefully when receiving invalid ID types.

These tests focus on business logic validation at the service layer, NOT API endpoints.
Tests should initially FAIL (TDD RED state) if there are type handling issues in the service.
"""

from unittest.mock import patch, MagicMock
from common.test_base import BaseModelTestCase
from django.contrib.auth import get_user_model

from finances.models import StoredPaymentMethod
from finances.services.payment_method_service import PaymentMethodService, PaymentMethodValidationError


User = get_user_model()


class PaymentMethodServiceIDParameterTest(BaseModelTestCase):
    """
    Test PaymentMethodService business logic for ID parameter type handling.
    
    Focus: Validate service methods handle integer IDs correctly and fail
    gracefully for invalid ID types at the business logic layer.
    """

    def setUp(self):
        """Set up test data."""
        super().setUp()  # Initialize comprehensive Stripe mocking
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123',
            stripe_customer_id='cus_test_123',
            card_brand='visa',
            card_last4='4242',
            is_default=True,
            is_active=True
        )
        
        self.service = PaymentMethodService()

    @patch('finances.services.payment_method_service.StripeService.detach_payment_method')
    def test_remove_payment_method_with_integer_id(self, mock_detach):
        """
        Test remove_payment_method works correctly with integer ID.
        
        Business Logic: Service method should accept and process integer IDs correctly.
        Expected: Should work without type conversion issues.
        """
        mock_detach.return_value = {'success': True}
        
        # Call service method with integer ID (correct type)
        result = self.service.remove_payment_method(
            student_user=self.student,
            payment_method_id=self.payment_method.id  # integer
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Payment method removed successfully')
        
        # Verify payment method was actually deleted
        with self.assertRaises(StoredPaymentMethod.DoesNotExist):
            StoredPaymentMethod.objects.get(id=self.payment_method.id)

    def test_remove_payment_method_with_string_id_fails(self):
        """
        Test remove_payment_method fails gracefully with string ID.
        
        Business Logic Issue: If string IDs are passed to service methods,
        they should either be handled or fail gracefully.
        
        **Test State:** Should FAIL initially (TDD RED) if service doesn't 
        handle string IDs properly.
        """
        # Call service method with string ID (incorrect type from API layer)
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.remove_payment_method(
                student_user=self.student,
                payment_method_id=str(self.payment_method.id)  # string instead of int
            )

    def test_remove_payment_method_with_non_numeric_string_fails(self):
        """
        Test remove_payment_method handles non-numeric strings gracefully.
        
        Business Logic: Should fail gracefully for completely invalid ID types.
        Expected: Should raise appropriate exception, not cause database errors.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.remove_payment_method(
                student_user=self.student,
                payment_method_id='not-a-number'
            )

    def test_remove_payment_method_with_none_id_fails(self):
        """
        Test remove_payment_method handles None ID gracefully.
        
        Business Logic: Should fail gracefully for None ID values.
        Expected: Should raise appropriate exception with clear error message.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.remove_payment_method(
                student_user=self.student,
                payment_method_id=None
            )

    def test_set_default_payment_method_with_integer_id(self):
        """
        Test set_default_payment_method works correctly with integer ID.
        
        Business Logic: Service method should accept and process integer IDs correctly.
        Expected: Should work without type conversion issues.
        """
        # Create another payment method
        other_payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_456',
            stripe_customer_id='cus_test_123',
            card_brand='mastercard',
            card_last4='5555',
            is_default=False,
            is_active=True
        )
        
        # Call service method with integer ID (correct type)
        result = self.service.set_default_payment_method(
            student_user=self.student,
            payment_method_id=other_payment_method.id  # integer
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Default payment method updated successfully')
        
        # Verify payment method was set as default
        other_payment_method.refresh_from_db()
        self.assertTrue(other_payment_method.is_default)

    def test_set_default_payment_method_with_string_id_fails(self):
        """
        Test set_default_payment_method fails with string ID.
        
        Business Logic Issue: If string IDs are passed from API layer,
        service should either handle conversion or fail gracefully.
        
        **Test State:** Should FAIL initially (TDD RED) if service doesn't 
        handle string IDs properly.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.set_default_payment_method(
                student_user=self.student,
                payment_method_id=str(self.payment_method.id)  # string instead of int
            )

    def test_set_default_payment_method_nonexistent_integer_id(self):
        """
        Test set_default_payment_method with valid integer but nonexistent ID.
        
        Business Logic: Should handle nonexistent IDs gracefully with proper error message.
        Expected: Should return error dict, not raise exception.
        """
        result = self.service.set_default_payment_method(
            student_user=self.student,
            payment_method_id=999999  # integer but doesn't exist
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
        self.assertIn('not found', result['message'].lower())

    def test_remove_payment_method_nonexistent_integer_id(self):
        """
        Test remove_payment_method with valid integer but nonexistent ID.
        
        Business Logic: Should handle nonexistent IDs gracefully with proper error message.
        Expected: Should return error dict, not raise exception.
        """
        result = self.service.remove_payment_method(
            student_user=self.student,
            payment_method_id=999999  # integer but doesn't exist
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
        self.assertIn('not found', result['message'].lower())

    def test_remove_payment_method_boundary_integer_values(self):
        """
        Test remove_payment_method with boundary integer values.
        
        Business Logic: Should handle edge case integer values correctly.
        Expected: Should handle zero and negative integers gracefully.
        """
        # Test with zero
        result = self.service.remove_payment_method(
            student_user=self.student,
            payment_method_id=0
        )
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
        
        # Test with negative integer
        result = self.service.remove_payment_method(
            student_user=self.student,
            payment_method_id=-1
        )
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')

    def test_set_default_payment_method_boundary_integer_values(self):
        """
        Test set_default_payment_method with boundary integer values.
        
        Business Logic: Should handle edge case integer values correctly.
        Expected: Should handle zero and negative integers gracefully.
        """
        # Test with zero
        result = self.service.set_default_payment_method(
            student_user=self.student,
            payment_method_id=0
        )
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
        
        # Test with negative integer  
        result = self.service.set_default_payment_method(
            student_user=self.student,
            payment_method_id=-1
        )
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')


class PaymentMethodServiceTypeValidationTest(BaseModelTestCase):
    """
    Test PaymentMethodService business logic for comprehensive type validation.
    
    Focus: Edge cases and comprehensive type validation at the service layer.
    """

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        self.service = PaymentMethodService()

    def test_remove_payment_method_float_id_conversion(self):
        """
        Test remove_payment_method behavior with float ID values.
        
        Business Logic: Should handle float values that could be converted to integers.
        **Test State:** Should FAIL initially if service doesn't handle float conversion.
        """
        with self.assertRaises((TypeError, ValueError)):
            self.service.remove_payment_method(
                student_user=self.student,
                payment_method_id=1.0  # float that could be converted to int
            )

    def test_set_default_payment_method_boolean_id_fails(self):
        """
        Test set_default_payment_method with boolean ID values.
        
        Business Logic: Should reject non-numeric types like boolean.
        Expected: Should raise appropriate exception for invalid type.
        """
        with self.assertRaises((TypeError, ValueError)):
            self.service.set_default_payment_method(
                student_user=self.student,
                payment_method_id=True  # boolean
            )

    def test_remove_payment_method_list_id_fails(self):
        """
        Test remove_payment_method with list as ID parameter.
        
        Business Logic: Should reject complex types like lists.
        Expected: Should raise appropriate exception for invalid type.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.remove_payment_method(
                student_user=self.student,
                payment_method_id=[1]  # list
            )

    def test_set_default_payment_method_dict_id_fails(self):
        """
        Test set_default_payment_method with dict as ID parameter.
        
        Business Logic: Should reject complex types like dictionaries.
        Expected: Should raise appropriate exception for invalid type.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.set_default_payment_method(
                student_user=self.student,
                payment_method_id={'id': 1}  # dict
            )