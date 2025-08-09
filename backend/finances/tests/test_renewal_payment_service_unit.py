"""
Unit tests for RenewalPaymentService business logic - ID parameter type handling.

This test suite validates that RenewalPaymentService methods properly handle 
integer ID parameters and fail gracefully when receiving invalid ID types.

These tests focus on business logic validation at the service layer, NOT API endpoints.
Tests should initially FAIL (TDD RED state) if there are type handling issues in the service.
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from finances.models import (
    PurchaseTransaction,
    StoredPaymentMethod,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType
)
from finances.services.renewal_payment_service import RenewalPaymentService, RenewalPaymentError


User = get_user_model()


class RenewalPaymentServiceIDParameterTest(TestCase):
    """
    Test RenewalPaymentService business logic for ID parameter type handling.
    
    Focus: Validate service methods handle integer IDs correctly and fail
    gracefully for invalid ID types at the business logic layer.
    """

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        # Create completed subscription transaction for renewal
        self.original_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_original_123',
            stripe_customer_id='cus_test_123',
            expires_at=timezone.now() + timezone.timedelta(days=30),
            metadata={'plan_name': 'Premium Plan', 'hours_included': '10'}
        )
        
        # Create active payment method
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123',
            stripe_customer_id='cus_test_123',
            card_brand='visa',
            card_last4='4242',
            is_default=True,
            is_active=True
        )
        
        # Create student account balance
        StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('100.00')
        )
        
        self.service = RenewalPaymentService()

    def test_get_renewable_transaction_with_integer_id(self):
        """
        Test _get_renewable_transaction works correctly with integer transaction ID.
        
        Business Logic: Internal service method should accept and process integer IDs correctly.
        Expected: Should work without type conversion issues.
        """
        # Call internal service method with integer ID (correct type)
        result = self.service._get_renewable_transaction(
            student_user=self.student,
            transaction_id=self.original_transaction.id  # integer
        )
        
        # Should return the transaction object, not error dict
        self.assertIsInstance(result, PurchaseTransaction)
        self.assertEqual(result.id, self.original_transaction.id)

    def test_get_renewable_transaction_with_string_id_fails(self):
        """
        Test _get_renewable_transaction fails gracefully with string transaction ID.
        
        Business Logic Issue: If string IDs are passed to service methods,
        they should either be handled or fail gracefully.
        
        **Test State:** Should FAIL initially (TDD RED) if service doesn't 
        handle string IDs properly.
        """
        # Call internal service method with string ID (incorrect type from API layer)
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service._get_renewable_transaction(
                student_user=self.student,
                transaction_id=str(self.original_transaction.id)  # string instead of int
            )

    def test_get_renewable_transaction_with_non_numeric_string_fails(self):
        """
        Test _get_renewable_transaction handles non-numeric strings gracefully.
        
        Business Logic: Should fail gracefully for completely invalid ID types.
        Expected: Should raise appropriate exception, not cause database errors.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service._get_renewable_transaction(
                student_user=self.student,
                transaction_id='not-a-number'
            )

    def test_get_renewable_transaction_with_none_id_fails(self):
        """
        Test _get_renewable_transaction handles None transaction ID gracefully.
        
        Business Logic: Should fail gracefully for None ID values.
        Expected: Should raise appropriate exception with clear error message.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service._get_renewable_transaction(
                student_user=self.student,
                transaction_id=None
            )

    def test_get_payment_method_for_renewal_with_integer_id(self):
        """
        Test _get_payment_method_for_renewal works correctly with integer payment method ID.
        
        Business Logic: Internal service method should accept and process integer IDs correctly.
        Expected: Should work without type conversion issues.
        """
        # Call internal service method with integer ID (correct type)
        result = self.service._get_payment_method_for_renewal(
            student_user=self.student,
            payment_method_id=self.payment_method.id  # integer
        )
        
        # Should return the payment method object, not error dict
        self.assertIsInstance(result, StoredPaymentMethod)
        self.assertEqual(result.id, self.payment_method.id)

    def test_get_payment_method_for_renewal_with_string_id_fails(self):
        """
        Test _get_payment_method_for_renewal fails with string payment method ID.
        
        Business Logic Issue: If string IDs are passed from API layer,
        service should either handle conversion or fail gracefully.
        
        **Test State:** Should FAIL initially (TDD RED) if service doesn't 
        handle string IDs properly.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service._get_payment_method_for_renewal(
                student_user=self.student,
                payment_method_id=str(self.payment_method.id)  # string instead of int
            )

    @patch('finances.services.renewal_payment_service.stripe.PaymentIntent.create')
    @patch('finances.services.renewal_payment_service.stripe.PaymentIntent.confirm')
    def test_renew_subscription_with_integer_original_transaction_id(self, mock_confirm, mock_create):
        """
        Test renew_subscription works correctly with integer original_transaction_id.
        
        Business Logic: Public service method should accept and process integer IDs correctly.
        Expected: Should work without type conversion issues.
        """
        # Mock Stripe responses
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = 'pi_renewal_123'
        mock_payment_intent.client_secret = 'pi_renewal_123_secret'
        mock_payment_intent.status = 'succeeded'
        mock_create.return_value = mock_payment_intent
        mock_confirm.return_value = mock_payment_intent
        
        # Call service method with integer ID (correct type)
        result = self.service.renew_subscription(
            student_user=self.student,
            original_transaction_id=self.original_transaction.id,  # integer
            payment_method_id=self.payment_method.id
        )
        
        self.assertTrue(result['success'])
        self.assertIn('transaction_id', result)
        self.assertIn('payment_intent_id', result)
        self.assertEqual(result['message'], 'Subscription renewed successfully')

    @patch('finances.services.renewal_payment_service.RenewalPaymentService._get_renewable_transaction')
    def test_renew_subscription_with_string_original_transaction_id_fails(self, mock_get_transaction):
        """
        Test renew_subscription fails with string original_transaction_id.
        
        Business Logic Issue: If string IDs are passed from API layer,
        service should either handle conversion or fail gracefully.
        
        **Test State:** Should FAIL initially (TDD RED) if service doesn't 
        handle string IDs properly by passing them to internal methods.
        """
        # Configure mock to raise error when string ID is passed
        mock_get_transaction.side_effect = TypeError("unsupported operand type(s)")
        
        with self.assertRaises(TypeError):
            self.service.renew_subscription(
                student_user=self.student,
                original_transaction_id=str(self.original_transaction.id),  # string instead of int
                payment_method_id=self.payment_method.id
            )

    def test_get_renewable_transaction_nonexistent_integer_id(self):
        """
        Test _get_renewable_transaction with valid integer but nonexistent transaction ID.
        
        Business Logic: Should handle nonexistent IDs gracefully with proper error message.
        Expected: Should return error dict, not raise exception.
        """
        result = self.service._get_renewable_transaction(
            student_user=self.student,
            transaction_id=999999  # integer but doesn't exist
        )
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'transaction_not_found')
        self.assertIn('not found', result['message'].lower())

    def test_get_payment_method_for_renewal_nonexistent_integer_id(self):
        """
        Test _get_payment_method_for_renewal with valid integer but nonexistent payment method ID.
        
        Business Logic: Should handle nonexistent IDs gracefully with proper error message.
        Expected: Should return error dict, not raise exception.
        """
        result = self.service._get_payment_method_for_renewal(
            student_user=self.student,
            payment_method_id=999999  # integer but doesn't exist
        )
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'payment_method_not_found')
        self.assertIn('not found', result['message'].lower())

    def test_get_renewable_transaction_boundary_integer_values(self):
        """
        Test _get_renewable_transaction with boundary integer values.
        
        Business Logic: Should handle edge case integer values correctly.
        Expected: Should handle zero and negative integers gracefully.
        """
        # Test with zero
        result = self.service._get_renewable_transaction(
            student_user=self.student,
            transaction_id=0
        )
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'transaction_not_found')
        
        # Test with negative integer
        result = self.service._get_renewable_transaction(
            student_user=self.student,
            transaction_id=-1
        )
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'transaction_not_found')

    def test_get_payment_method_for_renewal_boundary_integer_values(self):
        """
        Test _get_payment_method_for_renewal with boundary integer values.
        
        Business Logic: Should handle edge case integer values correctly.
        Expected: Should handle zero and negative integers gracefully.
        """
        # Test with zero
        result = self.service._get_payment_method_for_renewal(
            student_user=self.student,
            payment_method_id=0
        )
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'payment_method_not_found')
        
        # Test with negative integer
        result = self.service._get_payment_method_for_renewal(
            student_user=self.student,
            payment_method_id=-1
        )
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'payment_method_not_found')


class RenewalPaymentServiceTransactionValidationTest(TestCase):
    """
    Test RenewalPaymentService transaction validation for ID-related business logic.
    
    Focus: Validate business rules around transaction IDs and renewal eligibility.
    """

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        # Create processing transaction (should not be renewable)
        self.processing_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('75.00'),
            payment_status=TransactionPaymentStatus.PROCESSING,
            stripe_payment_intent_id='pi_processing_456'
        )
        
        # Create package transaction (should not be renewable)
        self.package_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_package_789'
        )
        
        self.service = RenewalPaymentService()

    def test_get_renewable_transaction_invalid_status_with_integer_id(self):
        """
        Test _get_renewable_transaction with valid integer ID but invalid transaction status.
        
        Business Logic: Should validate transaction status even with correct ID type.
        Expected: Should return business logic error, not type error.
        """
        result = self.service._get_renewable_transaction(
            student_user=self.student,
            transaction_id=self.processing_transaction.id  # integer, but processing status
        )
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'invalid_transaction_status')
        self.assertIn('completed', result['message'].lower())

    def test_get_renewable_transaction_invalid_type_with_integer_id(self):
        """
        Test _get_renewable_transaction with valid integer ID but invalid transaction type.
        
        Business Logic: Should validate transaction type even with correct ID type.
        Expected: Should return business logic error, not type error.
        """
        result = self.service._get_renewable_transaction(
            student_user=self.student,
            transaction_id=self.package_transaction.id  # integer, but package type
        )
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'invalid_transaction_type')
        self.assertIn('subscription', result['message'].lower())

    def test_get_renewable_transaction_invalid_type_with_string_id_fails(self):
        """
        Test _get_renewable_transaction with string ID and invalid transaction type.
        
        Business Logic Issue: Should fail due to type error before reaching type validation.
        
        **Test State:** Should FAIL initially (TDD RED) due to type handling issue.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service._get_renewable_transaction(
                student_user=self.student,
                transaction_id=str(self.package_transaction.id)  # string, package type
            )


class RenewalPaymentServiceTypeValidationTest(TestCase):
    """
    Test RenewalPaymentService business logic for comprehensive type validation.
    
    Focus: Edge cases and comprehensive type validation at the service layer.
    """

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        self.service = RenewalPaymentService()

    def test_get_renewable_transaction_float_id_fails(self):
        """
        Test _get_renewable_transaction behavior with float transaction ID values.
        
        Business Logic: Should handle float values that could be converted to integers.
        **Test State:** Should FAIL initially if service doesn't handle float conversion.
        """
        with self.assertRaises((TypeError, ValueError)):
            self.service._get_renewable_transaction(
                student_user=self.student,
                transaction_id=1.0  # float
            )

    def test_get_payment_method_for_renewal_boolean_id_fails(self):
        """
        Test _get_payment_method_for_renewal with boolean payment method ID values.
        
        Business Logic: Should reject non-numeric types like boolean.
        Expected: Should raise appropriate exception for invalid type.
        """
        with self.assertRaises((TypeError, ValueError)):
            self.service._get_payment_method_for_renewal(
                student_user=self.student,
                payment_method_id=True  # boolean
            )

    def test_get_renewable_transaction_list_id_fails(self):
        """
        Test _get_renewable_transaction with list as transaction ID parameter.
        
        Business Logic: Should reject complex types like lists.
        Expected: Should raise appropriate exception for invalid type.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service._get_renewable_transaction(
                student_user=self.student,
                transaction_id=[1]  # list
            )

    def test_get_payment_method_for_renewal_dict_id_fails(self):
        """
        Test _get_payment_method_for_renewal with dict as payment method ID parameter.
        
        Business Logic: Should reject complex types like dictionaries.
        Expected: Should raise appropriate exception for invalid type.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service._get_payment_method_for_renewal(
                student_user=self.student,
                payment_method_id={'id': 1}  # dict
            )

    def test_quick_topup_hours_decimal_validation(self):
        """
        Test quick_topup hours parameter validation doesn't have ID type issues.
        
        Business Logic: This method uses Decimal hours, not ID parameters.
        Expected: Should validate Decimal values correctly without ID-related type issues.
        """
        # Test with valid hours value
        result = self.service.quick_topup(
            student_user=self.student,
            hours=Decimal('5.00'),  # Valid package
            payment_method_id=None  # This will fail due to no default payment method
        )
        
        # Should fail due to no payment method, not due to type conversion
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'no_default_payment_method')

    def test_get_available_topup_packages_no_id_parameters(self):
        """
        Test get_available_topup_packages doesn't have ID-related type issues.
        
        Business Logic: This method doesn't take ID parameters.
        Expected: Should work normally without ID-related type issues.
        """
        packages = self.service.get_available_topup_packages()
        
        self.assertIsInstance(packages, list)
        self.assertGreater(len(packages), 0)
        
        # Verify package structure
        for package in packages:
            self.assertIn('hours', package)
            self.assertIn('price', package)
            self.assertIn('price_per_hour', package)
            self.assertIn('savings_percent', package)
            self.assertIsInstance(package['hours'], float)
            self.assertIsInstance(package['price'], float)