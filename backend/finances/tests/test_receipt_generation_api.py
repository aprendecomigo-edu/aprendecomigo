"""
Tests for receipt generation APIs in the finances app.

Tests the ReceiptGenerationService and related API endpoints for
generating, listing, and downloading PDF receipts.
"""

import tempfile
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from finances.models import (
    PurchaseTransaction,
    Receipt,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.services.receipt_service import ReceiptGenerationService


User = get_user_model()


class ReceiptGenerationServiceTest(TestCase):
    """Test cases for the ReceiptGenerationService."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
        
        # Create a completed transaction
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_test_123',
            metadata={
                'plan_name': 'Test Package',
                'plan_type': 'package',
                'hours_included': '10',
                'price_eur': '50.00'
            }
        )
    
    @patch('finances.services.receipt_service.render_to_string')
    @patch('weasyprint.HTML')
    def test_generate_receipt_success(self, mock_html, mock_render):
        """Test successful receipt generation."""
        # Mock PDF generation
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_html_instance.write_pdf.return_value = b'fake_pdf_content'
        mock_render.return_value = '<html>Test Receipt</html>'
        
        result = ReceiptGenerationService.generate_receipt(self.transaction.id)
        
        self.assertTrue(result['success'])
        self.assertIn('receipt_id', result)
        self.assertIn('receipt_number', result)
        self.assertEqual(result['amount'], 50.0)
        
        # Check receipt was created in database
        receipt = Receipt.objects.get(id=result['receipt_id'])
        self.assertEqual(receipt.transaction, self.transaction)
        self.assertEqual(receipt.student, self.student)
        self.assertEqual(receipt.amount, Decimal('50.00'))
    
    def test_generate_receipt_invalid_transaction(self):
        """Test receipt generation with invalid transaction ID."""
        result = ReceiptGenerationService.generate_receipt(99999)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
        self.assertIn('Transaction not found', result['message'])
    
    def test_generate_receipt_incomplete_transaction(self):
        """Test receipt generation with incomplete transaction."""
        # Create pending transaction
        pending_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.PENDING
        )
        
        result = ReceiptGenerationService.generate_receipt(pending_transaction.id)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'invalid_status')
        self.assertIn('completed transactions', result['message'])
    
    @patch('finances.services.receipt_service.render_to_string')
    @patch('weasyprint.HTML')
    def test_generate_receipt_already_exists(self, mock_html, mock_render):
        """Test receipt generation when receipt already exists."""
        # Create existing receipt
        existing_receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=self.transaction.amount
        )
        
        result = ReceiptGenerationService.generate_receipt(self.transaction.id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['receipt_id'], existing_receipt.id)
        self.assertTrue(result.get('already_existed', False))
    
    def test_list_student_receipts(self):
        """Test listing student receipts."""
        # Create multiple receipts
        receipt1 = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('50.00')
        )
        
        # Create another transaction and receipt
        transaction2 = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        receipt2 = Receipt.objects.create(
            student=self.student,
            transaction=transaction2,
            amount=Decimal('30.00')
        )
        
        result = ReceiptGenerationService.list_student_receipts(self.student)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 2)
        self.assertEqual(len(result['receipts']), 2)
        
        # Check receipt data
        receipt_data = result['receipts'][0]  # Most recent first
        self.assertEqual(receipt_data['id'], receipt2.id)
        self.assertEqual(receipt_data['amount'], 30.0)
    
    def test_list_student_receipts_with_filters(self):
        """Test listing student receipts with filters."""
        # Create receipt
        receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('50.00'),
            is_valid=True
        )
        
        # Test valid filter
        result = ReceiptGenerationService.list_student_receipts(
            self.student, 
            filters={'is_valid': True}
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        
        # Test invalid filter
        result = ReceiptGenerationService.list_student_receipts(
            self.student, 
            filters={'is_valid': False}
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 0)
    
    def test_get_receipt_download_url(self):
        """Test getting receipt download URL."""
        # Create receipt with mock PDF file
        receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('50.00')
        )
        
        # Mock PDF file
        receipt.pdf_file.save(
            'test_receipt.pdf',
            ContentFile(b'fake_pdf_content'),
            save=True
        )
        
        result = ReceiptGenerationService.get_receipt_download_url(
            receipt.id,
            self.student
        )
        
        self.assertTrue(result['success'])
        self.assertIn('download_url', result)
        self.assertEqual(result['receipt_number'], receipt.receipt_number)
    
    def test_get_receipt_download_url_wrong_student(self):
        """Test getting receipt download URL with wrong student."""
        # Create another student
        other_student = User.objects.create_user(
            email='other@example.com',
            name='Other Student',
            password='testpass123'
        )
        
        # Create receipt
        receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('50.00')
        )
        
        result = ReceiptGenerationService.get_receipt_download_url(
            receipt.id,
            other_student
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'permission_denied')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ReceiptAPITest(APITestCase):
    """Test cases for receipt API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
        
        # Create a completed transaction
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_test_123',
            metadata={
                'plan_name': 'Test Package',
            }
        )
        
        # Create receipt
        self.receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('50.00')
        )
    
    def test_list_receipts_authenticated(self):
        """Test listing receipts as authenticated student."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-receipts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
    
    def test_list_receipts_unauthenticated(self):
        """Test listing receipts without authentication."""
        url = reverse('finances:studentbalance-receipts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('finances.services.receipt_service.ReceiptGenerationService.generate_receipt')
    def test_generate_receipt_success(self, mock_generate):
        """Test successful receipt generation."""
        mock_generate.return_value = {
            'success': True,
            'receipt_id': 1,
            'receipt_number': 'RCP-2025-12345678',
            'amount': 50.0,
            'message': 'Receipt generated successfully'
        }
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-generate-receipt')
        data = {'transaction_id': self.transaction.id}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['receipt_id'], 1)
        
        # Verify service was called with correct parameters
        mock_generate.assert_called_once_with(
            transaction_id=self.transaction.id,
            force_regenerate=False
        )
    
    def test_generate_receipt_invalid_transaction(self):
        """Test receipt generation with invalid transaction ID."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-generate-receipt')
        data = {'transaction_id': 99999}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_generate_receipt_missing_data(self):
        """Test receipt generation with missing transaction_id."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-generate-receipt')
        data = {}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('finances.services.receipt_service.ReceiptGenerationService.get_receipt_download_url')
    def test_download_receipt_success(self, mock_download):
        """Test successful receipt download."""
        mock_download.return_value = {
            'success': True,
            'download_url': '/media/receipts/test.pdf',
            'receipt_number': 'RCP-2025-12345678',
            'filename': 'receipt_RCP-2025-12345678.pdf'
        }
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-download-receipt', kwargs={'pk': self.receipt.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('download_url', response.data)
        
        # Verify service was called with correct parameters
        mock_download.assert_called_once_with(
            receipt_id=self.receipt.id,
            student_user=self.student
        )
    
    def test_download_receipt_not_found(self):
        """Test downloading non-existent receipt."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-download-receipt', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_receipts_with_filters(self):
        """Test listing receipts with query parameters."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-receipts')
        response = self.client.get(url, {
            'is_valid': 'true',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_receipts_invalid_date_format(self):
        """Test listing receipts with invalid date format."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-receipts')
        response = self.client.get(url, {'start_date': 'invalid-date'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid start_date format', response.data['error'])


class ReceiptModelTest(TestCase):
    """Test cases for the Receipt model."""
    
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
            payment_status=TransactionPaymentStatus.COMPLETED
        )
    
    def test_receipt_creation(self):
        """Test creating a receipt."""
        receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('50.00')
        )
        
        self.assertIsNotNone(receipt.receipt_number)
        self.assertTrue(receipt.receipt_number.startswith('RCP-2025-'))
        self.assertEqual(receipt.amount, Decimal('50.00'))
        self.assertEqual(receipt.student, self.student)
        self.assertEqual(receipt.transaction, self.transaction)
        self.assertTrue(receipt.is_valid)
    
    def test_receipt_number_generation(self):
        """Test automatic receipt number generation."""
        receipt = Receipt(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('50.00')
        )
        
        # Receipt number should be None before saving
        self.assertIsNone(receipt.receipt_number)
        
        receipt.save()
        
        # Receipt number should be generated after saving
        self.assertIsNotNone(receipt.receipt_number)
        self.assertTrue(receipt.receipt_number.startswith('RCP-2025-'))
        self.assertEqual(len(receipt.receipt_number), 13)  # RCP-YYYY-XXXXXXXX
    
    def test_receipt_str_representation(self):
        """Test string representation of receipt."""
        receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('50.00')
        )
        
        expected_str = f"Receipt {receipt.receipt_number} - €50.00 for {self.student.name}"
        self.assertEqual(str(receipt), expected_str)
    
    def test_receipt_validation_amount_mismatch(self):
        """Test receipt validation with amount mismatch."""
        receipt = Receipt(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal('100.00')  # Different from transaction amount
        )
        
        with self.assertRaisesMessage(Exception, 'Receipt amount must match transaction amount'):
            receipt.full_clean()
    
    def test_receipt_validation_student_mismatch(self):
        """Test receipt validation with student mismatch."""
        other_student = User.objects.create_user(
            email='other@example.com',
            name='Other Student',
            password='testpass123'
        )
        
        receipt = Receipt(
            student=other_student,  # Different from transaction student
            transaction=self.transaction,
            amount=self.transaction.amount
        )
        
        with self.assertRaisesMessage(Exception, 'Receipt student must match transaction student'):
            receipt.full_clean()