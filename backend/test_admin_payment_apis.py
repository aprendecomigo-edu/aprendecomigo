"""
Comprehensive test suite for Administrative Payment Action APIs.

This test suite covers all the functionality implemented in GitHub Issue #116:
- RefundService with Stripe integration
- DisputeService for dispute management  
- FraudDetectionService for pattern detection
- All admin API endpoints
- Rate limiting functionality
- Audit logging

Tests use mocked Stripe responses to ensure reliable testing without actual API calls.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from finances.models import (
    PurchaseTransaction,
    TransactionPaymentStatus,
    TransactionType,
    StudentAccountBalance,
    PaymentDispute,
    AdminAction,
    FraudAlert,
    DisputeStatus,
    DisputeReason,
    AdminActionType,
    FraudAlertSeverity,
    FraudAlertStatus,
)
from finances.services.refund_service import RefundService
from finances.services.dispute_service import DisputeService
from finances.services.fraud_detection_service import FraudDetectionService
from finances.services.rate_limiter import StripeRateLimiter, stripe_rate_limit


User = get_user_model()


class BaseAdminPaymentTestCase(TestCase):
    """Base test case with common setup for admin payment tests."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            name='Admin User',
            is_staff=True,
            is_superuser=True
        )
        
        self.student_user = User.objects.create_user(
            email='student@test.com',
            name='Student User'
        )
        
        # Create test transaction
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_test_12345',
            metadata={'hours': '10'}
        )
        
        # Create student balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student_user,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('2.00'),
            balance_amount=Decimal('50.00')
        )


class RefundServiceTestCase(BaseAdminPaymentTestCase):
    """Test cases for RefundService functionality."""
    
    def setUp(self):
        super().setUp()
        self.refund_service = RefundService()
    
    @patch('stripe.Refund.create')
    def test_process_refund_success(self, mock_refund_create):
        """Test successful refund processing."""
        # Mock Stripe refund response
        mock_refund = Mock()
        mock_refund.id = 're_test_12345'
        mock_refund.status = 'succeeded'
        mock_refund_create.return_value = mock_refund
        
        result = self.refund_service.process_refund(
            transaction_id=self.transaction.id,
            refund_amount=Decimal('25.00'),
            reason='Customer request',
            admin_user=self.admin_user
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_id'], 're_test_12345')
        self.assertEqual(result['refund_amount'], Decimal('25.00'))
        
        # Verify transaction metadata updated
        self.transaction.refresh_from_db()
        self.assertIn('refunds', self.transaction.metadata)
        
        # Verify admin action logged
        admin_action = AdminAction.objects.filter(
            action_type=AdminActionType.REFUND_CREATED,
            admin_user=self.admin_user
        ).first()
        self.assertIsNotNone(admin_action)
        self.assertTrue(admin_action.success)
    
    def test_process_refund_invalid_transaction(self):
        """Test refund processing with invalid transaction ID."""
        result = self.refund_service.process_refund(
            transaction_id=99999,
            admin_user=self.admin_user
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'transaction_not_found')
    
    def test_process_refund_invalid_amount(self):
        """Test refund processing with invalid amount."""
        result = self.refund_service.process_refund(
            transaction_id=self.transaction.id,
            refund_amount=Decimal('100.00'),  # More than transaction amount
            admin_user=self.admin_user
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'invalid_refund_amount')
    
    @patch('stripe.Refund.retrieve')
    def test_get_refund_status(self, mock_refund_retrieve):
        """Test getting refund status from Stripe."""
        # Mock Stripe refund response
        mock_refund = Mock()
        mock_refund.id = 're_test_12345'
        mock_refund.status = 'succeeded'
        mock_refund.amount = 2500  # In cents
        mock_refund.currency = 'eur'
        mock_refund.created = 1640995200
        mock_refund.reason = 'requested_by_customer'
        mock_refund_retrieve.return_value = mock_refund
        
        result = self.refund_service.get_refund_status('re_test_12345')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_id'], 're_test_12345')
        self.assertEqual(result['status'], 'succeeded')
        self.assertEqual(result['amount'], 25.0)  # Converted from cents


class DisputeServiceTestCase(BaseAdminPaymentTestCase):
    """Test cases for DisputeService functionality."""
    
    def setUp(self):
        super().setUp()
        self.dispute_service = DisputeService()
    
    @patch('stripe.Dispute.retrieve')
    def test_sync_dispute_from_stripe(self, mock_dispute_retrieve):
        """Test syncing dispute from Stripe."""
        # Mock Stripe dispute response
        mock_dispute = Mock()
        mock_dispute.id = 'dp_test_12345'
        mock_dispute.payment_intent = self.transaction.stripe_payment_intent_id
        mock_dispute.amount = 5000  # In cents
        mock_dispute.currency = 'eur'
        mock_dispute.reason = 'fraudulent'
        mock_dispute.status = 'needs_response'
        mock_dispute.evidence_details = Mock()
        mock_dispute.evidence_details.due_by = 1640995200
        mock_dispute.to_dict_recursive.return_value = {'test': 'data'}
        mock_dispute_retrieve.return_value = mock_dispute
        
        result = self.dispute_service.sync_dispute_from_stripe(
            stripe_dispute_id='dp_test_12345',
            admin_user=self.admin_user
        )
        
        self.assertTrue(result['success'])
        self.assertTrue(result['created'])
        
        # Verify dispute created locally
        dispute = PaymentDispute.objects.filter(
            stripe_dispute_id='dp_test_12345'
        ).first()
        self.assertIsNotNone(dispute)
        self.assertEqual(dispute.amount, Decimal('50.00'))
        self.assertEqual(dispute.reason, DisputeReason.FRAUDULENT)
    
    def test_sync_dispute_transaction_not_found(self):
        """Test syncing dispute when local transaction not found."""
        with patch('stripe.Dispute.retrieve') as mock_retrieve:
            mock_dispute = Mock()
            mock_dispute.payment_intent = 'pi_nonexistent'
            mock_retrieve.return_value = mock_dispute
            
            result = self.dispute_service.sync_dispute_from_stripe(
                stripe_dispute_id='dp_test_12345',
                admin_user=self.admin_user
            )
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error_type'], 'transaction_not_found')
    
    def test_update_dispute_notes(self):
        """Test updating dispute internal notes."""
        # Create a test dispute
        dispute = PaymentDispute.objects.create(
            stripe_dispute_id='dp_test_12345',
            purchase_transaction=self.transaction,
            amount=Decimal('50.00'),
            reason=DisputeReason.FRAUDULENT,
            status=DisputeStatus.NEEDS_RESPONSE
        )
        
        result = self.dispute_service.update_dispute_notes(
            dispute_id=dispute.id,
            internal_notes='Customer contacted, investigating',
            admin_user=self.admin_user
        )
        
        self.assertTrue(result['success'])
        
        # Verify notes updated
        dispute.refresh_from_db()
        self.assertEqual(dispute.internal_notes, 'Customer contacted, investigating')


class FraudDetectionServiceTestCase(BaseAdminPaymentTestCase):
    """Test cases for FraudDetectionService functionality."""
    
    def setUp(self):
        super().setUp()
        self.fraud_service = FraudDetectionService()
    
    def test_analyze_transaction_new_user_high_value(self):
        """Test fraud analysis for new user with high value transaction."""
        # Create a new user with recent signup
        new_user = User.objects.create_user(
            email='newuser@test.com',
            name='New User'
        )
        
        # Create high-value transaction
        high_value_transaction = PurchaseTransaction.objects.create(
            student=new_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('300.00'),  # High value
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_high_value'
        )
        
        result = self.fraud_service.analyze_transaction(
            transaction=high_value_transaction,
            admin_user=self.admin_user
        )
        
        self.assertTrue(result['success'])
        self.assertGreater(result['risk_score'], Decimal('40.00'))
        
        # Check if alert was generated
        fraud_alert = FraudAlert.objects.filter(
            target_user=new_user,
            alert_type='new_user_high_value'
        ).first()
        self.assertIsNotNone(fraud_alert)
    
    def test_analyze_user_activity(self):
        """Test user activity analysis for fraud patterns."""
        # Create multiple transactions for pattern analysis
        for i in range(5):
            PurchaseTransaction.objects.create(
                student=self.student_user,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('50.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                stripe_payment_intent_id=f'pi_test_{i}',
                created_at=timezone.now() - timedelta(days=i)
            )
        
        result = self.fraud_service.analyze_user_activity(
            user=self.student_user,
            days_back=7,
            admin_user=self.admin_user
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['transactions_analyzed'], 6)  # 5 new + 1 from setUp
        self.assertIn('user_patterns', result)
    
    def test_get_active_alerts(self):
        """Test retrieving active fraud alerts."""
        # Create test fraud alert
        alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.HIGH,
            alert_type='test_pattern',
            description='Test fraud alert',
            target_user=self.student_user,
            risk_score=Decimal('75.00')
        )
        
        result = self.fraud_service.get_active_alerts(
            severity=FraudAlertSeverity.HIGH,
            limit=10
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['alerts'][0]['alert_id'], alert.alert_id)


class RateLimiterTestCase(TestCase):
    """Test cases for rate limiting functionality."""
    
    def setUp(self):
        self.rate_limiter = StripeRateLimiter(cache_prefix='test_rate_limit')
    
    def test_rate_limit_allowed(self):
        """Test that requests are allowed under normal circumstances."""
        result = self.rate_limiter.is_allowed('read_operations', 'test_user')
        
        self.assertTrue(result['allowed'])
        self.assertIn('tokens_remaining', result)
    
    def test_rate_limit_exceeded(self):
        """Test rate limit enforcement when threshold exceeded."""
        # Exhaust rate limit
        for i in range(100):  # Exceed the limit
            self.rate_limiter.is_allowed('write_operations', 'test_user')
        
        # Next request should be rate limited
        result = self.rate_limiter.is_allowed('write_operations', 'test_user')
        
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'rate_limit_exceeded')
        self.assertIn('retry_after', result)
    
    def test_rate_limit_decorator(self):
        """Test rate limiting decorator functionality."""
        call_count = 0
        
        @stripe_rate_limit('read_operations', 'test_function')
        def test_function():
            nonlocal call_count
            call_count += 1
            return 'success'
        
        # Should execute successfully
        result = test_function()
        self.assertEqual(result, 'success')
        self.assertEqual(call_count, 1)
    
    def test_get_rate_limit_status(self):
        """Test getting rate limit status."""
        status = self.rate_limiter.get_rate_limit_status('read_operations', 'test_user')
        
        self.assertIn('operation_type', status)
        self.assertIn('requests_per_second_limit', status)
        self.assertIn('current_tokens', status)


class AdminPaymentAPITestCase(APITestCase):
    """Test cases for admin payment API endpoints."""
    
    def setUp(self):
        """Set up test data for API tests."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            name='Admin User',
            is_staff=True,
            is_superuser=True
        )
        
        # Create student user
        self.student_user = User.objects.create_user(
            email='student@test.com',
            name='Student User'
        )
        
        # Create test transaction
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_test_12345',
            metadata={'hours': '10'}
        )
        
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)
    
    @patch('finances.services.refund_service.RefundService.process_refund')
    def test_process_refund_api(self, mock_process_refund):
        """Test process refund API endpoint."""
        mock_process_refund.return_value = {
            'success': True,
            'refund_id': 're_test_12345',
            'refund_amount': Decimal('25.00'),
            'transaction_id': self.transaction.id
        }
        
        url = reverse('finances:admin-process-refund')
        data = {
            'transaction_id': self.transaction.id,
            'refund_amount': '25.00',
            'reason': 'Customer request'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['refund_id'], 're_test_12345')
    
    def test_process_refund_api_missing_transaction_id(self):
        """Test process refund API with missing transaction ID."""
        url = reverse('finances:admin-process-refund')
        data = {
            'refund_amount': '25.00',
            'reason': 'Customer request'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('transaction_id is required', response.data['error'])
    
    def test_process_refund_api_unauthorized(self):
        """Test process refund API without admin permissions."""
        # Create non-admin user
        regular_user = User.objects.create_user(
            email='regular@test.com',
            name='Regular User'
        )
        self.client.force_authenticate(user=regular_user)
        
        url = reverse('finances:admin-process-refund')
        data = {
            'transaction_id': self.transaction.id,
            'refund_amount': '25.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('finances.services.dispute_service.DisputeService.sync_dispute_from_stripe')
    def test_sync_dispute_api(self, mock_sync_dispute):
        """Test sync dispute API endpoint."""
        mock_sync_dispute.return_value = {
            'success': True,
            'dispute_id': 1,
            'stripe_dispute_id': 'dp_test_12345',
            'created': True
        }
        
        url = reverse('finances:admin-sync-dispute')
        data = {'stripe_dispute_id': 'dp_test_12345'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    @patch('finances.services.fraud_detection_service.FraudDetectionService.analyze_transaction')
    def test_analyze_transaction_fraud_api(self, mock_analyze):
        """Test transaction fraud analysis API endpoint."""
        mock_analyze.return_value = {
            'success': True,
            'transaction_id': self.transaction.id,
            'risk_score': Decimal('25.00'),
            'risk_factors': [],
            'alerts_generated': [],
            'alert_count': 0
        }
        
        url = reverse('finances:admin-analyze-transaction-fraud', kwargs={'transaction_id': self.transaction.id})
        
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['transaction_id'], self.transaction.id)
    
    def test_get_admin_action_log_api(self):
        """Test admin action log API endpoint."""
        # Create test admin action
        AdminAction.objects.create(
            action_type=AdminActionType.REFUND_CREATED,
            action_description='Test refund',
            admin_user=self.admin_user,
            target_user=self.student_user,
            success=True,
            result_message='Test action'
        )
        
        url = reverse('finances:admin-action-log')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['count'], 0)
        self.assertIn('actions', response.data)


class AdminActionAuditTestCase(BaseAdminPaymentTestCase):
    """Test cases for admin action audit logging."""
    
    def test_admin_action_creation(self):
        """Test admin action record creation."""
        action = AdminAction.objects.create(
            action_type=AdminActionType.REFUND_CREATED,
            action_description='Test refund processing',
            admin_user=self.admin_user,
            target_user=self.student_user,
            target_transaction=self.transaction,
            success=True,
            result_message='Refund processed successfully',
            amount_impacted=Decimal('25.00'),
            stripe_reference_id='re_test_12345'
        )
        
        self.assertEqual(action.action_type, AdminActionType.REFUND_CREATED)
        self.assertEqual(action.admin_user, self.admin_user)
        self.assertEqual(action.target_user, self.student_user)
        self.assertTrue(action.success)
        self.assertEqual(action.amount_impacted, Decimal('25.00'))
    
    def test_admin_action_string_representation(self):
        """Test admin action string representation."""
        action = AdminAction.objects.create(
            action_type=AdminActionType.REFUND_CREATED,
            action_description='Test action',
            admin_user=self.admin_user,
            success=True,
            result_message='Success'
        )
        
        str_repr = str(action)
        self.assertIn('✓', str_repr)  # Success indicator
        self.assertIn('Refund Created', str_repr)
        self.assertIn(self.admin_user.name, str_repr)


if __name__ == '__main__':
    # Run specific test classes or all tests
    pytest.main([__file__, '-v'])