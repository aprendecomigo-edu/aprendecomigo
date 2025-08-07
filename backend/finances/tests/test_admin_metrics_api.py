"""
DRF API Tests for Admin Payment Metrics Endpoints.

This test suite provides comprehensive coverage of the administrative payment 
monitoring API endpoints, serving as both test validation and API documentation.

**API Endpoints Tested:**
- GET /api/finances/admin/payments/metrics/ - Payment dashboard metrics
- GET /api/finances/admin/payments/transactions/ - Transaction history with filters
- GET /api/finances/admin/webhooks/status/ - Webhook processing status

**Authentication & Permissions:**
- All endpoints require superuser authentication (AdminOnlyPermission)
- Regular authenticated users receive 403 Forbidden
- Unauthenticated requests receive 401 Unauthorized

**Response Formats:**
- All responses include consistent error handling
- Paginated endpoints follow DRF pagination standards
- Timestamps in ISO 8601 format
- Decimal amounts as strings for precision

**Test Categories:**
- Authentication & authorization testing
- Response structure validation  
- Query parameter filtering & validation
- Pagination & ordering behavior
- Performance & error handling
- Edge cases & boundary conditions
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
    
    def assert_valid_payment_metrics_response(self, response_data):
        """
        Validate the structure and content of payment metrics API response.
        
        This method serves as living documentation for the payment metrics
        API response format and ensures consistent validation across tests.
        
        Args:
            response_data (dict): The JSON response data from the API
            
        Expected Response Structure:
        {
            "generated_at": "2025-01-01T12:00:00Z",
            "time_period": {"hours": 24, "days": null},
            "payment_success_rate": {
                "total_transactions": 4,
                "successful_transactions": 2,
                "failed_transactions": 1,
                "pending_transactions": 1,
                "success_rate": 50.0
            },
            "revenue_summary": {
                "total": "150.00",
                "package": "100.00", 
                "subscription": "50.00"
            },
            "transaction_metrics": {...},
            "webhook_metrics": {
                "total_events": 4,
                "processed_events": 2,
                "failed_events": 1,
                "pending_events": 1,
                "success_rate": 50.0
            },
            "failure_analysis": {...},
            "recent_activity": [...]
        }
        """
        # Validate top-level structure
        required_top_level_fields = [
            'generated_at', 'payment_success_rate', 'revenue_summary',
            'transaction_metrics', 'webhook_metrics', 'failure_analysis', 
            'recent_activity'
        ]
        for field in required_top_level_fields:
            self.assertIn(field, response_data, f"Missing required field: {field}")
        
        # Validate payment success rate structure
        success_rate = response_data['payment_success_rate']
        success_rate_fields = [
            'total_transactions', 'successful_transactions', 
            'failed_transactions', 'pending_transactions', 'success_rate'
        ]
        for field in success_rate_fields:
            self.assertIn(field, success_rate, f"Missing success rate field: {field}")
        
        # Validate webhook metrics structure  
        webhook_metrics = response_data['webhook_metrics']
        webhook_fields = [
            'total_events', 'processed_events', 'failed_events', 
            'pending_events', 'success_rate'
        ]
        for field in webhook_fields:
            self.assertIn(field, webhook_metrics, f"Missing webhook field: {field}")
        
        # Validate revenue summary structure and format
        revenue = response_data['revenue_summary']
        self.assertIn('total', revenue)
        # Revenue amounts should be decimal strings for precision
        self.assertIsInstance(revenue['total'], (str, int, float))
        
        # Validate timestamp format
        self.assertIsInstance(response_data['generated_at'], str)
    
    def assert_valid_transaction_list_response(self, response_data):
        """
        Validate the structure of paginated transaction list response.
        
        Expected Response Structure:
        {
            "count": 4,
            "next": "http://example.com/api/path/?page=2",
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "student": 1,
                    "amount": "150.00",
                    "payment_status": "completed",
                    "transaction_type": "package",
                    "stripe_payment_intent_id": "pi_...",
                    "created_at": "2025-01-01T12:00:00Z",
                    "updated_at": "2025-01-01T12:00:00Z"
                },
                ...
            ]
        }
        """
        # Validate pagination structure
        pagination_fields = ['count', 'results']
        for field in pagination_fields:
            self.assertIn(field, response_data, f"Missing pagination field: {field}")
        
        self.assertIsInstance(response_data['count'], int)
        self.assertIsInstance(response_data['results'], list)
        
        # Validate transaction structure if results exist
        if response_data['results']:
            transaction = response_data['results'][0]
            required_transaction_fields = [
                'id', 'student', 'amount', 'payment_status', 
                'transaction_type', 'stripe_payment_intent_id',
                'created_at', 'updated_at'
            ]
            for field in required_transaction_fields:
                self.assertIn(field, transaction, f"Missing transaction field: {field}")
    
    def assert_valid_webhook_status_response(self, response_data):
        """
        Validate the structure of webhook status response with summary.
        
        Expected Response Structure:
        {
            "count": 4,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "stripe_event_id": "evt_...",
                    "event_type": "payment_intent.succeeded",
                    "status": "processed",
                    "retry_count": 0,
                    "error_message": null,
                    "created_at": "2025-01-01T12:00:00Z",
                    "processed_at": "2025-01-01T12:01:00Z"
                },
                ...
            ],
            "summary": {
                "total_events": 4,
                "processed_events": 2,
                "failed_events": 1,
                "pending_events": 1,
                "average_processing_time": 1.5
            }
        }
        """
        # Validate pagination structure
        self.assert_valid_transaction_list_response(response_data)
        
        # Validate webhook-specific summary
        self.assertIn('summary', response_data)
        summary = response_data['summary']
        
        summary_fields = [
            'total_events', 'processed_events', 'failed_events',
            'pending_events', 'average_processing_time'
        ]
        for field in summary_fields:
            self.assertIn(field, summary, f"Missing summary field: {field}")
        
        # Validate webhook event structure if results exist
        if response_data['results']:
            webhook = response_data['results'][0]
            required_webhook_fields = [
                'id', 'stripe_event_id', 'event_type', 'status',
                'retry_count', 'error_message', 'created_at', 'processed_at'
            ]
            for field in required_webhook_fields:
                self.assertIn(field, webhook, f"Missing webhook field: {field}")
    
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
        """
        Test admin users can access payment metrics with proper response structure.
        
        **API Endpoint:** GET /api/finances/admin/payments/metrics/
        **Expected Response:** 200 OK with comprehensive payment analytics
        **Authentication:** Requires superuser permissions
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-payment-metrics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Use comprehensive response validation helper
        data = response.json()
        self.assert_valid_payment_metrics_response(data)
        
        # Verify calculated metrics match test data expectations
        success_rate = data['payment_success_rate']
        self.assertEqual(success_rate['total_transactions'], 4)
        self.assertEqual(success_rate['successful_transactions'], 2)
        self.assertEqual(success_rate['failed_transactions'], 1)
        self.assertEqual(success_rate['pending_transactions'], 1)
        self.assertEqual(success_rate['success_rate'], 50.0)
        
        # Verify revenue calculations (only completed transactions count)
        revenue = data['revenue_summary']
        self.assertEqual(float(revenue['total']), 150.00)  # Only successful transactions
        self.assertEqual(float(revenue['package']), 100.00)
        self.assertEqual(float(revenue['subscription']), 50.00)
        
        # Verify webhook metrics calculations
        webhook_metrics = data['webhook_metrics']
        self.assertEqual(webhook_metrics['total_events'], 4)
        self.assertEqual(webhook_metrics['processed_events'], 2)
        self.assertEqual(webhook_metrics['failed_events'], 1)
        self.assertEqual(webhook_metrics['pending_events'], 1)
        self.assertEqual(webhook_metrics['success_rate'], 50.0)
    
    def test_non_admin_cannot_access_metrics(self):
        """
        Test non-admin users receive 403 Forbidden when accessing metrics.
        
        **Security Test:** Verifies AdminOnlyPermission enforcement
        **Expected Behavior:** Regular authenticated users are denied access
        """
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('finances:admin-payment-metrics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify response structure for error cases
        error_data = response.json()
        self.assertIn('detail', error_data)
        self.assertIn('permission', error_data['detail'].lower())
    
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
        """
        Test admin users can access paginated transaction history.
        
        **API Endpoint:** GET /api/finances/admin/payments/transactions/
        **Expected Response:** 200 OK with paginated transaction list
        **Features Tested:** Pagination, response structure, data accuracy
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('finances:admin-transaction-history')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Use comprehensive response validation helper
        data = response.json()
        self.assert_valid_transaction_list_response(data)
        
        # Verify data accuracy matches test setup
        self.assertEqual(data['count'], 4)  # All test transactions
        self.assertEqual(len(data['results']), 4)
        
        # Verify transactions are ordered by creation date (newest first)
        results = data['results']
        created_times = [result['created_at'] for result in results]
        self.assertEqual(created_times, sorted(created_times, reverse=True))
    
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