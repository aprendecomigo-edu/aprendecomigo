"""
Unit tests for ReceiptGenerationService business logic - ID parameter type handling.

This test suite validates that ReceiptGenerationService methods properly handle 
integer ID parameters and fail gracefully when receiving invalid ID types.

These tests focus on business logic validation at the service layer, NOT API endpoints.
Tests should initially FAIL (TDD RED state) if there are type handling issues in the service.
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from .stripe_test_utils import SimpleStripeTestCase
from django.contrib.auth import get_user_model

from finances.models import (
    PurchaseTransaction, 
    Receipt, 
    TransactionPaymentStatus, 
    TransactionType
)
from finances.services.receipt_service import ReceiptGenerationService, ReceiptValidationError


User = get_user_model()


class ReceiptServiceIDParameterTest(SimpleStripeTestCase):
    """
    Test ReceiptGenerationService business logic for ID parameter type handling.
    
    Focus: Validate service methods handle integer IDs correctly and fail
    gracefully for invalid ID types at the business logic layer.
    """

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        self.completed_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_test_123',
            stripe_customer_id='cus_test_123'
        )
        
        self.receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.completed_transaction,
            amount=Decimal('50.00'),
            metadata={'test': 'data'}
        )
        
        self.service = ReceiptGenerationService()

    @patch('finances.services.receipt_service.ReceiptGenerationService._generate_pdf_content')
    @patch('finances.services.receipt_service.ReceiptGenerationService._save_pdf_file')
    def test_generate_receipt_with_integer_transaction_id(self, mock_save_pdf, mock_generate_pdf):
        """
        Test generate_receipt works correctly with integer transaction ID.
        
        Business Logic: Service method should accept and process integer IDs correctly.
        Expected: Should work without type conversion issues.
        """
        mock_generate_pdf.return_value = b'fake pdf content'
        mock_save_pdf.return_value = None
        
        # Call service method with integer ID (correct type)
        result = self.service.generate_receipt(
            transaction_id=self.completed_transaction.id,  # integer
            force_regenerate=True
        )
        
        self.assertTrue(result['success'])
        self.assertIn('receipt_id', result)
        self.assertIn('receipt_number', result)
        self.assertEqual(result['message'], 'Receipt generated successfully')

    def test_generate_receipt_with_string_transaction_id_fails(self):
        """
        Test generate_receipt fails gracefully with string transaction ID.
        
        Business Logic Issue: If string IDs are passed to service methods,
        they should either be handled or fail gracefully.
        
        **Test State:** Should FAIL initially (TDD RED) if service doesn't 
        handle string IDs properly.
        """
        # Call service method with string ID (incorrect type from API layer)
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.generate_receipt(
                transaction_id=str(self.completed_transaction.id)  # string instead of int
            )

    def test_generate_receipt_with_non_numeric_string_fails(self):
        """
        Test generate_receipt handles non-numeric strings gracefully.
        
        Business Logic: Should fail gracefully for completely invalid ID types.
        Expected: Should raise appropriate exception, not cause database errors.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.generate_receipt(
                transaction_id='not-a-number'
            )

    def test_generate_receipt_with_none_transaction_id_fails(self):
        """
        Test generate_receipt handles None transaction ID gracefully.
        
        Business Logic: Should fail gracefully for None ID values.
        Expected: Should raise appropriate exception with clear error message.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.generate_receipt(
                transaction_id=None
            )

    def test_get_receipt_download_url_with_integer_receipt_id(self):
        """
        Test get_receipt_download_url works correctly with integer receipt ID.
        
        Business Logic: Service method should accept and process integer IDs correctly.
        Expected: Should work without type conversion issues.
        """
        # Add a fake PDF file to the receipt
        self.receipt.pdf_file.name = 'fake_receipt.pdf'
        self.receipt.save()
        
        # Call service method with integer ID (correct type)
        result = self.service.get_receipt_download_url(
            receipt_id=self.receipt.id,  # integer
            student_user=self.student
        )
        
        self.assertTrue(result['success'])
        self.assertIn('download_url', result)
        self.assertIn('receipt_number', result)

    def test_get_receipt_download_url_with_string_receipt_id_fails(self):
        """
        Test get_receipt_download_url fails with string receipt ID.
        
        Business Logic Issue: If string IDs are passed from API layer,
        service should either handle conversion or fail gracefully.
        
        **Test State:** Should FAIL initially (TDD RED) if service doesn't 
        handle string IDs properly.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.get_receipt_download_url(
                receipt_id=str(self.receipt.id),  # string instead of int
                student_user=self.student
            )

    def test_generate_receipt_nonexistent_integer_transaction_id(self):
        """
        Test generate_receipt with valid integer but nonexistent transaction ID.
        
        Business Logic: Should handle nonexistent IDs gracefully with proper error message.
        Expected: Should return error dict, not raise exception.
        """
        result = self.service.generate_receipt(
            transaction_id=999999  # integer but doesn't exist
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
        self.assertIn('not found', result['message'].lower())

    def test_get_receipt_download_url_nonexistent_integer_receipt_id(self):
        """
        Test get_receipt_download_url with valid integer but nonexistent receipt ID.
        
        Business Logic: Should handle nonexistent IDs gracefully with proper error message.
        Expected: Should return error dict, not raise exception.
        """
        result = self.service.get_receipt_download_url(
            receipt_id=999999,  # integer but doesn't exist
            student_user=self.student
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
        self.assertIn('not found', result['message'].lower())

    def test_generate_receipt_boundary_integer_values(self):
        """
        Test generate_receipt with boundary integer values.
        
        Business Logic: Should handle edge case integer values correctly.
        Expected: Should handle zero and negative integers gracefully.
        """
        # Test with zero
        result = self.service.generate_receipt(transaction_id=0)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
        
        # Test with negative integer
        result = self.service.generate_receipt(transaction_id=-1)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')

    def test_get_receipt_download_url_boundary_integer_values(self):
        """
        Test get_receipt_download_url with boundary integer values.
        
        Business Logic: Should handle edge case integer values correctly.
        Expected: Should handle zero and negative integers gracefully.
        """
        # Test with zero
        result = self.service.get_receipt_download_url(
            receipt_id=0,
            student_user=self.student
        )
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
        
        # Test with negative integer
        result = self.service.get_receipt_download_url(
            receipt_id=-1,
            student_user=self.student
        )
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')


class ReceiptServiceTransactionValidationTest(SimpleStripeTestCase):
    """
    Test ReceiptGenerationService transaction validation for ID-related business logic.
    
    Focus: Validate business rules around transaction IDs and receipt generation.
    """

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        # Create a processing transaction (should not allow receipt generation)
        self.processing_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.PROCESSING,
            stripe_payment_intent_id='pi_test_456'
        )
        
        self.service = ReceiptGenerationService()

    def test_generate_receipt_invalid_transaction_status_with_integer_id(self):
        """
        Test generate_receipt with valid integer ID but invalid transaction status.
        
        Business Logic: Should validate transaction status even with correct ID type.
        Expected: Should return business logic error, not type error.
        """
        result = self.service.generate_receipt(
            transaction_id=self.processing_transaction.id  # integer, but processing status
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'invalid_status')
        self.assertIn('completed', result['message'].lower())

    def test_generate_receipt_invalid_transaction_status_with_string_id_fails(self):
        """
        Test generate_receipt with string ID and invalid transaction status.
        
        Business Logic Issue: Should fail due to type error before reaching status validation.
        
        **Test State:** Should FAIL initially (TDD RED) due to type handling issue.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.generate_receipt(
                transaction_id=str(self.processing_transaction.id)  # string, processing status
            )


class ReceiptServiceTypeValidationTest(SimpleStripeTestCase):
    """
    Test ReceiptGenerationService business logic for comprehensive type validation.
    
    Focus: Edge cases and comprehensive type validation at the service layer.
    """

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        self.service = ReceiptGenerationService()

    def test_generate_receipt_float_transaction_id_fails(self):
        """
        Test generate_receipt behavior with float transaction ID values.
        
        Business Logic: Should handle float values that could be converted to integers.
        **Test State:** Should FAIL initially if service doesn't handle float conversion.
        """
        with self.assertRaises((TypeError, ValueError)):
            self.service.generate_receipt(transaction_id=1.0)  # float

    def test_get_receipt_download_url_boolean_receipt_id_fails(self):
        """
        Test get_receipt_download_url with boolean receipt ID values.
        
        Business Logic: Should reject non-numeric types like boolean.
        Expected: Should raise appropriate exception for invalid type.
        """
        with self.assertRaises((TypeError, ValueError)):
            self.service.get_receipt_download_url(
                receipt_id=True,  # boolean
                student_user=self.student
            )

    def test_generate_receipt_list_transaction_id_fails(self):
        """
        Test generate_receipt with list as transaction ID parameter.
        
        Business Logic: Should reject complex types like lists.
        Expected: Should raise appropriate exception for invalid type.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.generate_receipt(transaction_id=[1])  # list

    def test_get_receipt_download_url_dict_receipt_id_fails(self):
        """
        Test get_receipt_download_url with dict as receipt ID parameter.
        
        Business Logic: Should reject complex types like dictionaries.
        Expected: Should raise appropriate exception for invalid type.
        """
        with self.assertRaises((TypeError, ValueError, AttributeError)):
            self.service.get_receipt_download_url(
                receipt_id={'id': 1},  # dict
                student_user=self.student
            )

    def test_list_student_receipts_user_parameter_validation(self):
        """
        Test list_student_receipts parameter validation doesn't have ID type issues.
        
        Business Logic: This method doesn't take ID parameters, but validate it works correctly.
        Expected: Should work normally without ID-related type issues.
        """
        result = self.service.list_student_receipts(
            student_user=self.student,
            filters={'is_valid': True}
        )
        
        self.assertTrue(result['success'])
        self.assertIn('receipts', result)
        self.assertIn('count', result)
        self.assertIsInstance(result['count'], int)