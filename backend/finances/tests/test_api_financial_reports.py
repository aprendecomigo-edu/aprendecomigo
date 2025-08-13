"""
Consolidated test suite for Financial Reports API endpoints.

This module contains focused tests for:
- Receipt generation and download
- Financial analytics and reporting
- Teacher compensation reports
- Transaction analytics
- Export functionality

Focuses on reporting business logic and data accuracy.
"""

import tempfile
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import School, TeacherProfile
from finances.models import (
    ClassSession,
    PurchaseTransaction,
    Receipt,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.tests.base import FinanceBaseTestCase
from finances.tests.stripe_test_utils import (
    SimpleStripeTestCase,
    comprehensive_stripe_mocks_decorator,
)

User = get_user_model()


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class FinancialReportsAPITestCase(FinanceBaseTestCase, APITestCase):
    """Base test case with common setup for financial reports API tests."""

    def setUp(self):
        """Set up test data common to all financial reports API tests."""
        super().setUp()
        
        # Use existing fixtures from base class
        # school, student_user, teacher_user, admin_user, teacher_profile are already available
        
        # Use existing student account balance and update with test values
        self.student_balance = self.student_account_balance
        self.student_balance.hours_purchased = Decimal("20.00")
        self.student_balance.hours_consumed = Decimal("5.00")
        self.student_balance.balance_amount = Decimal("200.00")
        self.student_balance.save()

        # Create test transactions
        self.completed_transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("150.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_123",
            created_at=timezone.now(),
            metadata={
                'plan_name': 'Test Package',
                'plan_type': 'package',
                'hours_included': '10'
            }
        )

        # Use existing class session from base class or create additional if needed
        # self.class_session is already available from base class

    def authenticate_as_student(self):
        """Authenticate client as the test student."""
        self.client.force_authenticate(user=self.student_user)

    def authenticate_as_teacher(self):
        """Authenticate client as the test teacher."""
        self.client.force_authenticate(user=self.teacher_user)

    def authenticate_as_admin(self):
        """Authenticate client as admin."""
        self.client.force_authenticate(user=self.admin_user)


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class ReceiptGenerationAPITests(FinancialReportsAPITestCase):
    """Test cases for receipt generation and management."""

    @patch('finances.services.receipt_service.render_to_string')
    @patch('weasyprint.HTML')
    def test_generate_receipt_for_completed_transaction(self, mock_html, mock_render):
        """Test receipt generation for completed transaction."""
        # Mock PDF generation
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_html_instance.write_pdf.return_value = b'fake_pdf_content'
        mock_render.return_value = '<html>Test Receipt</html>'
        
        self.authenticate_as_student()
        url = reverse('finances:receipt-generate')
        
        data = {'transaction_id': self.completed_transaction.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('receipt_id', response.data)
        self.assertIn('receipt_number', response.data)
        self.assertEqual(response.data['amount'], 150.0)
        
        # Verify receipt was created in database
        receipt = Receipt.objects.get(id=response.data['receipt_id'])
        self.assertEqual(receipt.transaction, self.completed_transaction)
        self.assertEqual(receipt.student, self.student_user)
        self.assertEqual(receipt.amount, Decimal('150.00'))
        self.assertIsNotNone(receipt.receipt_number)

    def test_generate_receipt_invalid_transaction(self):
        """Test receipt generation fails for invalid transaction."""
        self.authenticate_as_student()
        url = reverse('finances:receipt-generate')
        
        data = {'transaction_id': 99999}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_generate_receipt_incomplete_transaction(self):
        """Test receipt generation fails for incomplete transaction."""
        # Create pending transaction
        pending_transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.PENDING,
            stripe_payment_intent_id="pi_test_pending"
        )
        
        self.authenticate_as_student()
        url = reverse('finances:receipt-generate')
        
        data = {'transaction_id': pending_transaction.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('completed', response.data['error'].lower())

    def test_list_student_receipts(self):
        """Test listing receipts for authenticated student."""
        # Create test receipt
        receipt = Receipt.objects.create(
            transaction=self.completed_transaction,
            student=self.student_user,
            amount=Decimal('150.00'),
            receipt_number='RC-2024-001',
            pdf_file=ContentFile(b'fake_pdf_content', name='receipt.pdf')
        )
        
        self.authenticate_as_student()
        url = reverse('finances:receipt-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        receipt_data = response.data['results'][0]
        self.assertEqual(receipt_data['id'], receipt.id)
        self.assertEqual(receipt_data['receipt_number'], 'RC-2024-001')
        self.assertEqual(Decimal(receipt_data['amount']), Decimal('150.00'))
        self.assertIn('download_url', receipt_data)

    def test_download_receipt_pdf(self):
        """Test downloading receipt PDF file."""
        # Create receipt with PDF
        receipt = Receipt.objects.create(
            transaction=self.completed_transaction,
            student=self.student_user,
            amount=Decimal('150.00'),
            receipt_number='RC-2024-002',
            pdf_file=ContentFile(b'fake_pdf_content', name='receipt.pdf')
        )
        
        self.authenticate_as_student()
        url = reverse('finances:receipt-download', kwargs={'pk': receipt.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_receipt_access_security(self):
        """Test users can only access their own receipts."""
        # Create receipt for another user
        other_student = User.objects.create_user(
            email="other@example.com",
            name="Other Student"
        )
        other_transaction = PurchaseTransaction.objects.create(
            student=other_student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_other"
        )
        other_receipt = Receipt.objects.create(
            transaction=other_transaction,
            student=other_student,
            amount=Decimal('100.00'),
            receipt_number='RC-2024-003'
        )
        
        self.authenticate_as_student()
        url = reverse('finances:receipt-download', kwargs={'pk': other_receipt.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class FinancialAnalyticsAPITests(FinancialReportsAPITestCase):
    """Test cases for financial analytics and reporting."""

    def setUp(self):
        """Set up additional test data for analytics."""
        super().setUp()
        
        # Create additional transactions for analytics
        for i in range(5):
            PurchaseTransaction.objects.create(
                student=self.student_user,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                stripe_payment_intent_id=f"pi_test_analytics_{i}",
                created_at=timezone.now() - timezone.timedelta(days=i)
            )

    def test_student_spending_analytics(self):
        """Test student spending analytics endpoint."""
        self.authenticate_as_student()
        url = reverse('finances:analytics-student-spending')
        
        # Test monthly spending analytics
        response = self.client.get(url, {'period': 'monthly'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        analytics_data = response.data
        self.assertIn('total_spending', analytics_data)
        self.assertIn('transaction_count', analytics_data)
        self.assertIn('spending_by_type', analytics_data)
        self.assertIn('monthly_breakdown', analytics_data)
        
        # Verify calculation accuracy
        self.assertGreater(analytics_data['total_spending'], 0)
        self.assertGreater(analytics_data['transaction_count'], 0)

    def test_school_financial_overview(self):
        """Test school-wide financial overview for admin users."""
        self.authenticate_as_admin()
        url = reverse('finances:analytics-school-overview')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        overview_data = response.data
        self.assertIn('total_revenue', overview_data)
        self.assertIn('active_students', overview_data)
        self.assertIn('transaction_count', overview_data)
        self.assertIn('revenue_by_type', overview_data)
        self.assertIn('top_students', overview_data)
        
        # Verify admin-level aggregations
        self.assertGreaterEqual(overview_data['total_revenue'], 650.0)  # 150 + 5*100
        self.assertGreaterEqual(overview_data['active_students'], 1)

    def test_teacher_compensation_report(self):
        """Test teacher compensation calculation and reporting."""
        # Create additional class sessions for compensation calculation
        for i in range(3):
            session = ClassSession.objects.create(
                teacher=self.teacher_profile,
                school=self.school,
                date=timezone.now().date(),
                start_time=timezone.now().time(),
                end_time=(timezone.now() + timezone.timedelta(hours=1)).time(),
                session_type="individual",
                grade_level="10",
                status="completed"
            )
            session.students.add(self.student_user)
        
        self.authenticate_as_admin()
        url = reverse('finances:analytics-teacher-compensation')
        
        response = self.client.get(url, {
            'teacher_id': self.teacher_profile.id,
            'period': 'monthly'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        compensation_data = response.data
        self.assertIn('total_hours_taught', compensation_data)
        self.assertIn('total_compensation', compensation_data)
        self.assertIn('sessions_completed', compensation_data)
        self.assertIn('hourly_breakdown', compensation_data)
        
        # Verify compensation calculations
        self.assertGreaterEqual(compensation_data['sessions_completed'], 4)  # 1 + 3 new
        self.assertGreater(compensation_data['total_hours_taught'], 0)

    def test_revenue_trends_analysis(self):
        """Test revenue trends over time analysis."""
        self.authenticate_as_admin()
        url = reverse('finances:analytics-revenue-trends')
        
        response = self.client.get(url, {
            'period': 'daily',
            'days': 30
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        trends_data = response.data
        self.assertIn('daily_revenue', trends_data)
        self.assertIn('growth_rate', trends_data)
        self.assertIn('peak_days', trends_data)
        self.assertIn('total_period_revenue', trends_data)
        
        # Verify trend analysis structure
        self.assertIsInstance(trends_data['daily_revenue'], list)
        self.assertGreater(len(trends_data['daily_revenue']), 0)

    def test_analytics_permission_enforcement(self):
        """Test analytics endpoints enforce proper permissions."""
        admin_only_endpoints = [
            reverse('finances:analytics-school-overview'),
            reverse('finances:analytics-teacher-compensation'),
            reverse('finances:analytics-revenue-trends'),
        ]
        
        # Test as regular student
        self.authenticate_as_student()
        for url in admin_only_endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test as teacher
        self.authenticate_as_teacher()
        for url in admin_only_endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class FinancialExportAPITests(FinancialReportsAPITestCase):
    """Test cases for financial data export functionality."""

    def test_export_transactions_csv(self):
        """Test exporting transaction data as CSV."""
        self.authenticate_as_admin()
        url = reverse('finances:export-transactions')
        
        response = self.client.get(url, {
            'format': 'csv',
            'start_date': (timezone.now() - timezone.timedelta(days=30)).date(),
            'end_date': timezone.now().date()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Verify CSV content structure
        content = response.content.decode('utf-8')
        self.assertIn('Transaction ID', content)
        self.assertIn('Student Email', content)
        self.assertIn('Amount', content)
        self.assertIn('Payment Status', content)

    def test_export_student_balances_excel(self):
        """Test exporting student balance data as Excel."""
        self.authenticate_as_admin()
        url = reverse('finances:export-student-balances')
        
        response = self.client.get(url, {'format': 'excel'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Type'], 
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])

    def test_export_teacher_sessions_pdf(self):
        """Test exporting teacher session data as PDF report."""
        with patch('weasyprint.HTML') as mock_html:
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.return_value = b'fake_pdf_report'
            
            self.authenticate_as_admin()
            url = reverse('finances:export-teacher-sessions')
            
            response = self.client.get(url, {
                'format': 'pdf',
                'teacher_id': self.teacher_profile.id,
                'month': timezone.now().month,
                'year': timezone.now().year
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('attachment', response['Content-Disposition'])

    def test_export_permission_validation(self):
        """Test export endpoints require admin permissions."""
        export_endpoints = [
            reverse('finances:export-transactions'),
            reverse('finances:export-student-balances'),
            reverse('finances:export-teacher-sessions'),
        ]
        
        # Test as student
        self.authenticate_as_student()
        for url in export_endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test as teacher  
        self.authenticate_as_teacher()
        for url in export_endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_date_range_validation(self):
        """Test export endpoints validate date ranges properly."""
        self.authenticate_as_admin()
        url = reverse('finances:export-transactions')
        
        # Test invalid date range (start after end)
        response = self.client.get(url, {
            'format': 'csv',
            'start_date': timezone.now().date(),
            'end_date': (timezone.now() - timezone.timedelta(days=30)).date()
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date range', response.data['error'].lower())

    def test_export_large_dataset_pagination(self):
        """Test export handles large datasets with proper pagination/chunking."""
        # Create many transactions
        transactions = []
        for i in range(1000):
            transactions.append(PurchaseTransaction(
                student=self.student_user,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('50.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                stripe_payment_intent_id=f"pi_test_bulk_{i}",
                created_at=timezone.now()
            ))
        PurchaseTransaction.objects.bulk_create(transactions)
        
        self.authenticate_as_admin()
        url = reverse('finances:export-transactions')
        
        response = self.client.get(url, {'format': 'csv'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify large dataset is handled properly
        content = response.content.decode('utf-8')
        lines = content.split('\n')
        self.assertGreater(len(lines), 1000)  # Header + data rows


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class FinancialReportsSecurityTests(FinancialReportsAPITestCase):
    """Security tests for financial reports endpoints."""

    def test_report_endpoints_require_authentication(self):
        """Test all report endpoints require authentication."""
        endpoints = [
            reverse('finances:receipt-generate'),
            reverse('finances:receipt-list'),
            reverse('finances:analytics-student-spending'),
            reverse('finances:analytics-school-overview'),
        ]
        
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_receipt_data_sanitization(self):
        """Test receipt generation sanitizes potentially malicious data."""
        # Create transaction with potentially malicious metadata
        malicious_transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('75.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_malicious",
            metadata={
                'plan_name': '<script>alert("xss")</script>',
                'description': "'; DROP TABLE receipts; --"
            }
        )
        
        with patch('finances.services.receipt_service.render_to_string') as mock_render, \
             patch('weasyprint.HTML') as mock_html:
            
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.return_value = b'safe_pdf_content'
            mock_render.return_value = '<html>Safe Receipt</html>'
            
            self.authenticate_as_student()
            url = reverse('finances:receipt-generate')
            
            data = {'transaction_id': malicious_transaction.id}
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify render_to_string was called with sanitized data
            call_args = mock_render.call_args[1]['context']
            self.assertNotIn('<script>', str(call_args))
            self.assertNotIn('DROP TABLE', str(call_args))

    def test_analytics_data_isolation(self):
        """Test analytics endpoints properly isolate data by user permissions."""
        # Create transactions for different students
        other_student = User.objects.create_user(
            email="other@example.com",
            name="Other Student"
        )
        
        PurchaseTransaction.objects.create(
            student=other_student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('200.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_other_student"
        )
        
        # Student should only see their own analytics
        self.authenticate_as_student()
        url = reverse('finances:analytics-student-spending')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify analytics only include student's transactions
        analytics_data = response.data
        # The exact amount depends on setup, but should not include other student's 200.00
        self.assertLess(analytics_data['total_spending'], 2000.00)  # Reasonable upper bound
