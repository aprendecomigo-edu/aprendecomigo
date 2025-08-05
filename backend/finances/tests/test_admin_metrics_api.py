"""
Tests for admin payment metrics API endpoints.

This test suite covers the administrative payment monitoring API endpoints
including metrics dashboard, transaction history, and webhook monitoring.
"""

import json
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import School
from finances.models import (
    PurchaseTransaction, TransactionPaymentStatus, TransactionType,
    WebhookEventLog, WebhookEventStatus
)

User = get_user_model()


class AdminMetricsAPITest(TestCase):
    """Test cases for admin metrics API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Clean up any existing webhooks from previous tests
        from finances.models import WebhookEventLog, PurchaseTransaction
        WebhookEventLog.objects.all().delete()
        PurchaseTransaction.objects.all().delete()
        
        # Create test school
        self.school = School.objects.create(name="Test School")
        
        # Create admin user (superuser)
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            name="Admin User",
            is_staff=True,
            is_superuser=True
        )
        
        # Create non-admin user
        self.regular_user = User.objects.create_user(
            email="user@test.com",
            name="Regular User"
        )
        
        # Create student users
        self.student1 = User.objects.create_user(
            email="student1@test.com",
            name="Student One"
        )
        
        self.student2 = User.objects.create_user(
            email="student2@test.com",
            name="Student Two"
        )
        
        # Set up API client
        self.client = APIClient()
        
        # Create test data
        self._create_test_transactions()
        self._create_test_webhook_logs()
    
    def _create_test_transactions(self):
        """Create test transactions for metrics."""
        now = timezone.now()
        
        # Successful transactions
        self.successful_transaction1 = PurchaseTransaction.objects.create(
            student=self.student1,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_success_1"
        )
        
        self.successful_transaction2 = PurchaseTransaction.objects.create(
            student=self.student2,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_success_2"
        )
        
        # Failed transaction
        self.failed_transaction = PurchaseTransaction.objects.create(
            student=self.student1,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('75.00'),
            payment_status=TransactionPaymentStatus.FAILED,
            stripe_payment_intent_id="pi_test_failed_1"
        )
        
        # Pending transaction
        self.pending_transaction = PurchaseTransaction.objects.create(
            student=self.student2,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.PENDING,
            stripe_payment_intent_id="pi_test_pending_1"
        )
    
    def _create_test_webhook_logs(self):
        """Create test webhook logs."""
        # Successful webhook events
        self.webhook_success1 = WebhookEventLog.objects.create(
            stripe_event_id="evt_test_success_1",
            event_type="payment_intent.succeeded",
            status=WebhookEventStatus.PROCESSED,
            payload={"test": "data"}
        )
        
        self.webhook_success2 = WebhookEventLog.objects.create(
            stripe_event_id="evt_test_success_2",
            event_type="customer.created",
            status=WebhookEventStatus.PROCESSED,
            payload={"test": "data"}
        )
        
        # Failed webhook event
        self.webhook_failed = WebhookEventLog.objects.create(
            stripe_event_id="evt_test_failed_1",
            event_type="payment_intent.payment_failed",
            status=WebhookEventStatus.FAILED,
            payload={"test": "data"}
        )
        
        # Pending webhook event
        self.webhook_pending = WebhookEventLog.objects.create(
            stripe_event_id="evt_test_pending_1",
            event_type="payment_intent.created",
            status=WebhookEventStatus.RECEIVED,
            payload={"test": "data"}
        )


class PaymentMetricsEndpointTest(AdminMetricsAPITest):
    """Test the /api/admin/payments/metrics/ endpoint."""
    
    def test_admin_can_access_metrics(self):
        """Test that admin users can access payment metrics."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-payment-metrics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        data = response.json()
        self.assertIn('generated_at', data)
        self.assertIn('payment_success_rate', data)
        self.assertIn('revenue_summary', data)
        self.assertIn('transaction_metrics', data)
        self.assertIn('webhook_metrics', data)
        self.assertIn('failure_analysis', data)
        self.assertIn('recent_activity', data)
        
        # Verify metrics values
        success_rate = data['payment_success_rate']
        self.assertEqual(success_rate['total_transactions'], 4)
        self.assertEqual(success_rate['successful_transactions'], 2)
        self.assertEqual(success_rate['failed_transactions'], 1)
        self.assertEqual(success_rate['pending_transactions'], 1)
        self.assertEqual(success_rate['success_rate'], 50.0)
        
        # Verify revenue summary
        revenue = data['revenue_summary']
        self.assertEqual(float(revenue['total']), 150.00)  # Only successful transactions
        self.assertEqual(float(revenue['package']), 100.00)
        self.assertEqual(float(revenue['subscription']), 50.00)
        
        # Verify webhook metrics
        webhook_metrics = data['webhook_metrics']
        self.assertEqual(webhook_metrics['total_events'], 4)
        self.assertEqual(webhook_metrics['processed_events'], 2)
        self.assertEqual(webhook_metrics['failed_events'], 1)
        self.assertEqual(webhook_metrics['pending_events'], 1)
        self.assertEqual(webhook_metrics['success_rate'], 50.0)
    
    def test_non_admin_cannot_access_metrics(self):
        """Test that non-admin users cannot access payment metrics."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('finances:admin-payment-metrics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_cannot_access_metrics(self):
        """Test that unauthenticated users cannot access payment metrics."""
        url = reverse('finances:admin-payment-metrics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_metrics_with_time_filter(self):
        """Test metrics endpoint with time period filtering."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-payment-metrics')
        
        # Test with hours filter
        response = self.client.get(url, {'hours': 24})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['time_period']['hours'], 24)
        
        # Test with days filter
        response = self.client.get(url, {'days': 7})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['time_period']['days'], 7)
    
    def test_metrics_invalid_time_filter(self):
        """Test metrics endpoint with invalid time parameters."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-payment-metrics')
        
        # Test with invalid hours value
        response = self.client.get(url, {'hours': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with negative days
        response = self.client.get(url, {'days': -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with zero hours
        response = self.client.get(url, {'hours': 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TransactionHistoryEndpointTest(AdminMetricsAPITest):
    """Test the /api/admin/payments/transactions/ endpoint."""
    
    def test_admin_can_access_transaction_history(self):
        """Test that admin users can access transaction history."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-transaction-history')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('count', data)
        self.assertIn('results', data)
        
        # Should return all 4 transactions
        self.assertEqual(data['count'], 4)
        self.assertEqual(len(data['results']), 4)
        
        # Verify transaction structure
        transaction = data['results'][0]
        expected_fields = [
            'id', 'student', 'amount', 'payment_status', 'transaction_type',
            'stripe_payment_intent_id', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, transaction)
    
    def test_transaction_history_filtering(self):
        """Test transaction history with filtering parameters."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-transaction-history')
        
        # Filter by payment status
        response = self.client.get(url, {'payment_status': TransactionPaymentStatus.COMPLETED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 2)  # Only successful transactions
        
        # Filter by transaction type
        response = self.client.get(url, {'transaction_type': TransactionType.PACKAGE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 3)  # Package transactions
        
        # Filter by student
        response = self.client.get(url, {'student': self.student1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 2)  # Student1's transactions
    
    def test_transaction_history_search(self):
        """Test transaction history search functionality."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-transaction-history')
        
        # Search by payment intent ID
        response = self.client.get(url, {'search': 'pi_test_success_1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['stripe_payment_intent_id'], 'pi_test_success_1')
        
        # Search by student name
        response = self.client.get(url, {'search': 'Student One'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 2)  # Student One's transactions
    
    def test_transaction_history_ordering(self):
        """Test transaction history ordering."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-transaction-history')
        
        # Order by created_at descending (default)
        response = self.client.get(url, {'ordering': '-created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should be ordered by creation time, newest first
        created_times = [transaction['created_at'] for transaction in data['results']]
        self.assertEqual(created_times, sorted(created_times, reverse=True))
        
        # Order by amount ascending
        response = self.client.get(url, {'ordering': 'amount'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        amounts = [float(transaction['amount']) for transaction in data['results']]
        self.assertEqual(amounts, sorted(amounts))
    
    def test_non_admin_cannot_access_transactions(self):
        """Test that non-admin users cannot access transaction history."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('finances:admin-transaction-history')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class WebhookStatusEndpointTest(AdminMetricsAPITest):
    """Test the /api/admin/webhooks/status/ endpoint."""
    
    def test_admin_can_access_webhook_status(self):
        """Test that admin users can access webhook status."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-webhook-status')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('count', data)
        self.assertIn('results', data)
        self.assertIn('summary', data)
        
        # Should return all 4 webhook events
        self.assertEqual(data['count'], 4)
        self.assertEqual(len(data['results']), 4)
        
        # Verify webhook structure
        webhook = data['results'][0]
        expected_fields = [
            'id', 'stripe_event_id', 'event_type', 'status',
            'retry_count', 'error_message', 'created_at', 'processed_at'
        ]
        for field in expected_fields:
            self.assertIn(field, webhook)
        
        # Verify summary
        summary = data['summary']
        self.assertEqual(summary['total_events'], 4)
        self.assertEqual(summary['processed_events'], 2)
        self.assertEqual(summary['failed_events'], 1)
        self.assertEqual(summary['pending_events'], 1)
    
    def test_webhook_status_filtering(self):
        """Test webhook status with filtering parameters."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-webhook-status')
        
        # Filter by status
        response = self.client.get(url, {'status': WebhookEventStatus.PROCESSED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 2)  # Only processed events
        
        # Filter by event type
        response = self.client.get(url, {'event_type': 'payment_intent.succeeded'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 1)  # Only payment_intent.succeeded events
    
    def test_webhook_status_search(self):
        """Test webhook status search functionality."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-webhook-status')
        
        # Search by event ID
        response = self.client.get(url, {'search': 'evt_test_success_1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['stripe_event_id'], 'evt_test_success_1')
        
        # Search by event type
        response = self.client.get(url, {'search': 'payment_intent'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 3)  # Events with 'payment_intent' in type
    
    def test_non_admin_cannot_access_webhook_status(self):
        """Test that non-admin users cannot access webhook status."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('finances:admin-webhook-status')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminAPIPerformanceTest(AdminMetricsAPITest):
    """Test performance and reliability of admin APIs."""
    
    def test_large_dataset_performance(self):
        """Test API performance with larger datasets."""
        # Create additional test data
        from django.utils import timezone
        
        # Create 50 additional transactions
        for i in range(50):
            PurchaseTransaction.objects.create(
                student=self.student1 if i % 2 == 0 else self.student2,
                transaction_type=TransactionType.PACKAGE if i % 3 == 0 else TransactionType.SUBSCRIPTION,
                amount=Decimal('50.00'),
                payment_status=TransactionPaymentStatus.COMPLETED if i % 4 != 0 else TransactionPaymentStatus.FAILED,
                stripe_payment_intent_id=f"pi_test_bulk_{i}"
            )
        
        # Create 30 additional webhook logs
        for i in range(30):
            WebhookEventLog.objects.create(
                stripe_event_id=f"evt_test_bulk_{i}",
                event_type="payment_intent.succeeded" if i % 2 == 0 else "customer.created",
                status=WebhookEventStatus.PROCESSED if i % 3 != 0 else WebhookEventStatus.FAILED,
                payload={"test": f"data_{i}"}
            )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Test metrics endpoint performance
        import time
        start_time = time.time()
        
        response = self.client.get(reverse('finances:admin-payment-metrics'))
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(processing_time, 2.0)  # Should complete within 2 seconds
        
        # Verify data integrity with larger dataset
        data = response.json()
        self.assertEqual(data['payment_success_rate']['total_transactions'], 54)  # 4 original + 50 new
        self.assertEqual(data['webhook_metrics']['total_events'], 34)  # 4 original + 30 new
    
    def test_api_error_handling(self):
        """Test API error handling for edge cases."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test with malformed query parameters
        response = self.client.get(
            reverse('finances:admin-payment-metrics'),
            {'hours': 'abc', 'days': 'xyz'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test transaction history with invalid student ID
        response = self.client.get(
            reverse('finances:admin-transaction-history'),
            {'student': 99999}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 0)  # No transactions for non-existent student
    
    def test_api_pagination(self):
        """Test API pagination with large result sets."""
        # Create additional transactions for pagination testing
        for i in range(25):
            PurchaseTransaction.objects.create(
                student=self.student1,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('10.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                stripe_payment_intent_id=f"pi_test_page_{i}"
            )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-transaction-history')
        
        # Test first page
        response = self.client.get(url, {'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data['results']), 10)
        self.assertIsNotNone(data.get('next'))  # Should have next page
        
        # Test second page
        response = self.client.get(url, {'page': 2, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data['results']), 10)
        self.assertIsNotNone(data.get('previous'))  # Should have previous page