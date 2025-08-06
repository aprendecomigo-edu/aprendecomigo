"""
Tests for enhanced subscription API functionality in the finances app.

Tests the enhanced StudentBalanceViewSet with subscription information
including billing dates, subscription status, and related features.
"""

from decimal import Decimal
from datetime import date, timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from finances.models import (
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)


User = get_user_model()


class EnhancedSubscriptionAPITest(APITestCase):
    """Test cases for enhanced subscription API functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
        
        # Create student account balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('150.00')
        )
    
    def test_summary_with_no_subscription(self):
        """Test summary endpoint with no subscription."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription_info = response.data['subscription_info']
        self.assertFalse(subscription_info['is_active'])
        self.assertIsNone(subscription_info['next_billing_date'])
        self.assertIsNone(subscription_info['billing_cycle'])
        self.assertEqual(subscription_info['subscription_status'], 'inactive')
        self.assertFalse(subscription_info['cancel_at_period_end'])
    
    def test_summary_with_active_subscription(self):
        """Test summary endpoint with active subscription."""
        # Create subscription transaction
        subscription_date = timezone.now() - timedelta(days=15)  # 15 days ago
        
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=subscription_date,
            metadata={
                'plan_name': 'Monthly Subscription',
                'plan_type': 'subscription',
                'hours_included': '10'
            }
        )
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription_info = response.data['subscription_info']
        self.assertTrue(subscription_info['is_active'])
        self.assertEqual(subscription_info['billing_cycle'], 'monthly')
        self.assertEqual(subscription_info['subscription_status'], 'active')
        self.assertFalse(subscription_info['cancel_at_period_end'])
        self.assertIsNotNone(subscription_info['next_billing_date'])
        self.assertIsNotNone(subscription_info['current_period_start'])
        self.assertIsNotNone(subscription_info['current_period_end'])
    
    def test_summary_with_multiple_subscriptions(self):
        """Test summary endpoint with multiple subscriptions (uses latest)."""
        # Create older subscription
        old_subscription_date = timezone.now() - timedelta(days=60)
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=old_subscription_date,
            metadata={'plan_name': 'Old Subscription'}
        )
        
        # Create newer subscription
        new_subscription_date = timezone.now() - timedelta(days=10)
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('35.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=new_subscription_date,
            metadata={'plan_name': 'New Subscription'}
        )
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription_info = response.data['subscription_info']
        self.assertTrue(subscription_info['is_active'])
        # Should use the newer subscription for billing calculations
        self.assertEqual(subscription_info['billing_cycle'], 'monthly')
    
    def test_summary_with_package_transactions(self):
        """Test summary endpoint ignores package transactions for subscription info."""
        # Create package transaction (should be ignored for subscription info)
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            metadata={'plan_name': 'Package Deal'}
        )
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription_info = response.data['subscription_info']
        self.assertFalse(subscription_info['is_active'])  # No subscription
        self.assertEqual(subscription_info['subscription_status'], 'inactive')
    
    def test_summary_with_pending_subscription(self):
        """Test summary endpoint with pending subscription transaction."""
        # Create pending subscription (should be ignored)
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.PENDING,
            metadata={'plan_name': 'Pending Subscription'}
        )
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription_info = response.data['subscription_info']
        self.assertFalse(subscription_info['is_active'])  # Pending not counted
        self.assertEqual(subscription_info['subscription_status'], 'inactive')
    
    @patch('django.utils.timezone.now')
    def test_billing_cycle_calculation(self, mock_now):
        """Test billing cycle calculation logic."""
        # Mock current date
        mock_now.return_value = timezone.datetime(2025, 2, 15, tzinfo=dt_timezone.utc)
        
        # Create subscription from January 15
        subscription_date = timezone.datetime(2025, 1, 15, tzinfo=dt_timezone.utc)
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=subscription_date,
            metadata={'plan_name': 'Monthly Subscription'}
        )
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription_info = response.data['subscription_info']
        self.assertTrue(subscription_info['is_active'])
        self.assertEqual(subscription_info['billing_cycle'], 'monthly')
        
        # Check billing dates
        # Current period should be Feb 15 - Mar 14
        # Next billing should be Mar 15
        current_period_start = subscription_info['current_period_start']
        current_period_end = subscription_info['current_period_end']
        next_billing_date = subscription_info['next_billing_date']
        
        self.assertEqual(current_period_start, '2025-02-15')
        self.assertEqual(current_period_end, '2025-03-14')
        self.assertEqual(next_billing_date, '2025-03-15')
    
    @patch('django.utils.timezone.now')
    def test_billing_cycle_past_period(self, mock_now):
        """Test billing cycle calculation when current date is past period end."""
        # Mock current date to be past the expected period end
        mock_now.return_value = timezone.datetime(2025, 3, 20, tzinfo=dt_timezone.utc)
        
        # Create subscription from January 15
        subscription_date = timezone.datetime(2025, 1, 15, tzinfo=dt_timezone.utc)
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=subscription_date,
            metadata={'plan_name': 'Monthly Subscription'}
        )
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription_info = response.data['subscription_info']
        self.assertTrue(subscription_info['is_active'])
        
        # Should adjust to current period (March 15 - April 14)
        current_period_start = subscription_info['current_period_start']
        current_period_end = subscription_info['current_period_end']
        next_billing_date = subscription_info['next_billing_date']
        
        self.assertEqual(current_period_start, '2025-03-15')
        self.assertEqual(current_period_end, '2025-04-14')
        self.assertEqual(next_billing_date, '2025-04-15')
    
    def test_summary_response_structure(self):
        """Test complete summary response structure."""
        # Create subscription transaction
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            metadata={'plan_name': 'Monthly Subscription'}
        )
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check all expected fields are present
        expected_fields = [
            'student_info',
            'balance_summary',
            'package_status',
            'upcoming_expirations',
            'subscription_info'
        ]
        
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # Check subscription_info structure
        subscription_fields = [
            'is_active',
            'next_billing_date',
            'billing_cycle',
            'subscription_status',
            'cancel_at_period_end',
            'current_period_start',
            'current_period_end'
        ]
        
        for field in subscription_fields:
            self.assertIn(field, response.data['subscription_info'])
        
        # Check student_info structure
        student_info_fields = ['id', 'name', 'email']
        for field in student_info_fields:
            self.assertIn(field, response.data['student_info'])
        
        # Check balance_summary structure
        balance_fields = ['hours_purchased', 'hours_consumed', 'remaining_hours', 'balance_amount']
        for field in balance_fields:
            self.assertIn(field, response.data['balance_summary'])
    
    def test_admin_access_other_student_subscription(self):
        """Test admin can access subscription info for other students."""
        # Create admin user
        admin_user = User.objects.create_user(
            email='admin@example.com',
            name='Admin User',
            password='adminpass123',
            is_staff=True
        )
        
        # Create subscription for the student
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            metadata={'plan_name': 'Monthly Subscription'}
        )
        
        self.client.force_authenticate(user=admin_user)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url, {'email': self.student.email})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription_info = response.data['subscription_info']
        self.assertTrue(subscription_info['is_active'])
        
        # Verify it's the correct student's data
        student_info = response.data['student_info']
        self.assertEqual(student_info['email'], self.student.email)
    
    def test_non_admin_cannot_access_other_student(self):
        """Test non-admin cannot access other student's subscription info."""
        # Create another student
        other_student = User.objects.create_user(
            email='other@example.com',
            name='Other Student',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-summary')
        response = self.client.get(url, {'email': other_student.email})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Permission denied', response.data['error'])


class SubscriptionInfoServiceTest(TestCase):
    """Test cases for subscription info service methods."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
    
    def test_get_subscription_info_no_subscription(self):
        """Test _get_subscription_info with no subscriptions."""
        from finances.views import StudentBalanceViewSet
        
        viewset = StudentBalanceViewSet()
        result = viewset._get_subscription_info(self.student)
        
        expected_result = {
            'is_active': False,
            'next_billing_date': None,
            'billing_cycle': None,
            'subscription_status': 'inactive',
            'cancel_at_period_end': False,
            'current_period_start': None,
            'current_period_end': None,
        }
        
        self.assertEqual(result, expected_result)
    
    def test_get_subscription_info_with_active_subscription(self):
        """Test _get_subscription_info with active subscription."""
        from finances.views import StudentBalanceViewSet
        
        # Create subscription transaction
        subscription_date = timezone.now() - timedelta(days=10)
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=subscription_date,
            metadata={'plan_name': 'Monthly Subscription'}
        )
        
        viewset = StudentBalanceViewSet()
        result = viewset._get_subscription_info(self.student)
        
        self.assertTrue(result['is_active'])
        self.assertEqual(result['billing_cycle'], 'monthly')
        self.assertEqual(result['subscription_status'], 'active')
        self.assertFalse(result['cancel_at_period_end'])
        self.assertIsNotNone(result['next_billing_date'])
        self.assertIsNotNone(result['current_period_start'])
        self.assertIsNotNone(result['current_period_end'])
    
    @patch('django.utils.timezone.now')
    def test_billing_date_calculation_edge_cases(self, mock_now):
        """Test billing date calculation for edge cases."""
        from finances.views import StudentBalanceViewSet
        
        # Test subscription created on last day of month
        mock_now.return_value = timezone.datetime(2025, 3, 31, tzinfo=dt_timezone.utc)
        
        subscription_date = timezone.datetime(2025, 1, 31, tzinfo=dt_timezone.utc)
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=subscription_date,
            metadata={'plan_name': 'Monthly Subscription'}
        )
        
        viewset = StudentBalanceViewSet()
        result = viewset._get_subscription_info(self.student)
        
        self.assertTrue(result['is_active'])
        # Should handle month transitions correctly
        self.assertIsNotNone(result['current_period_start'])
        self.assertIsNotNone(result['current_period_end'])
        self.assertIsNotNone(result['next_billing_date'])