"""
Tests for API parameter type conversion issues (GitHub Issue #169).

This test suite specifically validates that URL path parameters (payment method IDs, 
receipt IDs) and form data parameters are properly converted from strings to integers 
before being passed to service methods.

The tests in this file focus ONLY on the type conversion behavior and should FAIL 
initially (TDD RED state) before the implementation fixes are applied.
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from finances.models import (
    StoredPaymentMethod,
    PurchaseTransaction,
    Receipt,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)


User = get_user_model()


class PaymentMethodIDTypeConversionTest(APITestCase):
    """
    Test payment method ID type conversion from URL path parameters.
    
    Issue: URL path parameters are received as strings (e.g., '1') but service 
    methods expect integers (e.g., 1). Tests ensure proper conversion.
    """
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
        
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123',
            card_brand='visa',
            card_last4='4242',
            is_default=True
        )
    
    @patch('finances.services.payment_method_service.PaymentMethodService.remove_payment_method')
    def test_remove_payment_method_id_type_conversion(self, mock_remove_method):
        """
        Test that payment_method_id from URL path is converted to integer.
        
        **Issue:** URL path parameter 'pk' is a string but service expects integer
        **Expected:** payment_method_id should be passed as integer, not string
        **Test State:** Should FAIL before implementation fix (TDD RED)
        """
        mock_remove_method.return_value = {
            'success': True,
            'message': 'Payment method removed successfully',
            'was_default': True
        }
        
        self.client.force_authenticate(user=self.student)
        
        # Make API call with payment method ID in URL path 
        url = reverse('finances:studentbalance-remove-payment-method', 
                     kwargs={'pk': str(self.payment_method.id)})  # URL pk will be string
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # CRITICAL: Verify service method receives INTEGER, not string
        mock_remove_method.assert_called_once_with(
            student_user=self.student,
            payment_method_id=self.payment_method.id  # Should be integer, not '1'
        )
    
    @patch('finances.services.payment_method_service.PaymentMethodService.set_default_payment_method')
    def test_set_default_payment_method_id_type_conversion(self, mock_set_default):
        """
        Test that payment_method_id from URL path is converted to integer.
        
        **Issue:** URL path parameter 'pk' is a string but service expects integer
        **Expected:** payment_method_id should be passed as integer, not string
        **Test State:** Should FAIL before implementation fix (TDD RED)
        """
        mock_set_default.return_value = {
            'success': True,
            'message': 'Default payment method updated successfully'
        }
        
        self.client.force_authenticate(user=self.student)
        
        # Make API call with payment method ID in URL path
        url = reverse('finances:studentbalance-set-default-payment-method', 
                     kwargs={'pk': str(self.payment_method.id)})  # URL pk will be string
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # CRITICAL: Verify service method receives INTEGER, not string
        mock_set_default.assert_called_once_with(
            student_user=self.student,
            payment_method_id=self.payment_method.id  # Should be integer, not '1'
        )
    
    def test_remove_payment_method_invalid_id_conversion(self):
        """
        Test error handling when payment method ID cannot be converted to integer.
        
        **Expected:** Should handle non-numeric IDs gracefully
        **Test State:** Should FAIL before implementation fix (TDD RED)
        """
        self.client.force_authenticate(user=self.student)
        
        # Try with non-numeric ID that can't be converted to integer
        url = reverse('finances:studentbalance-remove-payment-method', 
                     kwargs={'pk': 'invalid-id'})
        response = self.client.delete(url)
        
        # Should return 404 or 400, not 500 (server error)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])


class ReceiptIDTypeConversionTest(APITestCase):
    """
    Test receipt ID type conversion from URL path parameters.
    
    Issue: URL path parameters are received as strings but service methods expect integers.
    """
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
        
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_test_123'
        )
        
        self.receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('50.00')
        )
    
    @patch('finances.services.receipt_service.ReceiptGenerationService.get_receipt_download_url')
    def test_download_receipt_id_type_conversion(self, mock_download_url):
        """
        Test that receipt_id from URL path is converted to integer.
        
        **Issue:** URL path parameter 'pk' is a string but service expects integer
        **Expected:** receipt_id should be passed as integer, not string
        **Test State:** Should FAIL before implementation fix (TDD RED)
        """
        mock_download_url.return_value = {
            'success': True,
            'download_url': '/media/receipts/test.pdf',
            'receipt_number': 'RCP-2025-12345678',
            'filename': 'receipt_RCP-2025-12345678.pdf'
        }
        
        self.client.force_authenticate(user=self.student)
        
        # Make API call with receipt ID in URL path
        url = reverse('finances:studentbalance-download-receipt', 
                     kwargs={'pk': str(self.receipt.id)})  # URL pk will be string
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # CRITICAL: Verify service method receives INTEGER, not string
        mock_download_url.assert_called_once_with(
            receipt_id=self.receipt.id,  # Should be integer, not '1'
            student_user=self.student
        )
    
    def test_download_receipt_invalid_id_conversion(self):
        """
        Test error handling when receipt ID cannot be converted to integer.
        
        **Expected:** Should handle non-numeric IDs gracefully
        **Test State:** Should FAIL before implementation fix (TDD RED)
        """
        self.client.force_authenticate(user=self.student)
        
        # Try with non-numeric ID that can't be converted to integer
        url = reverse('finances:studentbalance-download-receipt', 
                     kwargs={'pk': 'invalid-receipt-id'})
        response = self.client.get(url)
        
        # Should return 404 or 400, not 500 (server error)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])


class FormDataTypeConversionTest(APITestCase):
    """
    Test validation of form data type conversion in renewal payments.
    
    Note: DRF serializers with IntegerField already handle string->integer conversion
    correctly for form data, so these tests verify the validation behavior.
    """
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
        
        # Create student balance
        StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('100.00')
        )
    
    def test_renew_subscription_with_invalid_payment_method_id_format(self):
        """
        Test error handling for non-numeric payment_method_id in form data.
        
        **Expected:** Should return 400 Bad Request for invalid ID format
        **Note:** Serializers already handle this correctly with IntegerField
        """
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-renew-subscription')
        data = {
            'original_transaction_id': 1,
            'payment_method_id': 'invalid-payment-method-id'  # Invalid format
        }
        response = self.client.post(url, data)
        
        # Should return 400 Bad Request for invalid ID format
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('payment_method_id', response.data)
    
    def test_quick_topup_with_invalid_payment_method_id_format(self):
        """
        Test error handling for non-numeric payment_method_id in form data.
        
        **Expected:** Should return 400 Bad Request for invalid ID format  
        **Note:** Serializers already handle this correctly with IntegerField
        """
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-quick-topup')
        data = {
            'hours': '5.00',
            'payment_method_id': 'invalid-payment-method-id'  # Invalid format
        }
        response = self.client.post(url, data)
        
        # Should return 400 Bad Request for invalid ID format
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('payment_method_id', response.data)


class EdgeCaseTypeConversionTest(APITestCase):
    """
    Test edge cases for type conversion in API parameters.
    
    Covers boundary conditions and error scenarios for ID parameter handling.
    """
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
    
    def test_payment_method_id_zero_handling(self):
        """
        Test handling of payment method ID = 0 (edge case).
        
        **Expected:** Should handle zero ID appropriately (likely 404 not found)
        **Test State:** Should FAIL before implementation fix (TDD RED)
        """
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-remove-payment-method', kwargs={'pk': '0'})
        response = self.client.delete(url)
        
        # Should return 404 for non-existent payment method
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_receipt_id_negative_handling(self):
        """
        Test handling of negative receipt ID (edge case).
        
        **Expected:** Should handle negative IDs appropriately
        **Test State:** Should FAIL before implementation fix (TDD RED)
        """
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-download-receipt', kwargs={'pk': '-1'})
        response = self.client.delete(url)
        
        # Should return 404 or 400, not 500
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])
    
    def test_large_integer_id_handling(self):
        """
        Test handling of very large integer IDs.
        
        **Expected:** Should handle large integers without overflow errors
        **Test State:** Should FAIL before implementation fix (TDD RED)
        """
        self.client.force_authenticate(user=self.student)
        
        large_id = str(2**31 - 1)  # Max 32-bit signed integer
        url = reverse('finances:studentbalance-remove-payment-method', kwargs={'pk': large_id})
        response = self.client.delete(url)
        
        # Should return 404 for non-existent payment method, not 500
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)