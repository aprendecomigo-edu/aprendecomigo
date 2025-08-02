"""
Tests for PaymentAnalyticsService.

This test suite covers payment analytics functionality including success rates,
revenue trends, failure analysis, and performance metrics for administrative
dashboard monitoring.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import School
from finances.models import (
    PurchaseTransaction, TransactionPaymentStatus, TransactionType,
    WebhookEventLog, WebhookEventStatus, StudentAccountBalance
)
from finances.services.payment_analytics_service import PaymentAnalyticsService

User = get_user_model()


class PaymentAnalyticsServiceTest(TestCase):
    """Test cases for PaymentAnalyticsService."""
    
    def setUp(self):
        """Set up test data."""
        # Create test school
        self.school = School.objects.create(
            name="Test School"
        )
        
        # Create test users
        self.student1 = User.objects.create_user(
            email="student1@test.com",
            name="Student One"
        )
        
        self.student2 = User.objects.create_user(
            email="student2@test.com", 
            name="Student Two"
        )
        
        # Create analytics service instance
        self.service = PaymentAnalyticsService()
        
        # Create test time periods
        self.now = timezone.now()
        self.today = self.now.date()
        self.yesterday = self.today - timedelta(days=1)
        self.last_week = self.today - timedelta(days=7)
        self.last_month = self.today - timedelta(days=30)
    
    def _create_transaction(self, student, amount, status, created_at=None, transaction_type=TransactionType.PACKAGE):
        """Helper method to create a transaction."""
        if created_at is None:
            created_at = self.now
        
        transaction = PurchaseTransaction.objects.create(
            student=student,
            transaction_type=transaction_type,
            amount=amount,
            payment_status=status,
            stripe_payment_intent_id=f"pi_test_{timezone.now().timestamp()}"
        )
        # Update created_at separately to override auto_now_add behavior
        transaction.created_at = created_at
        transaction.save()
        return transaction
    
    def _create_webhook_log(self, event_type, status, created_at=None):
        """Helper method to create a webhook event log."""
        if created_at is None:
            created_at = self.now
            
        log = WebhookEventLog.objects.create(
            stripe_event_id=f"evt_test_{timezone.now().timestamp()}",
            event_type=event_type,
            status=status,
            payload={'test': 'data'}
        )
        # Update created_at separately to override auto_now_add behavior
        log.created_at = created_at
        log.save()
        return log


class PaymentSuccessRateTest(PaymentAnalyticsServiceTest):
    """Test payment success rate calculations."""
    
    def test_overall_success_rate(self):
        """Test calculating overall payment success rate."""
        # Create successful transactions
        self._create_transaction(self.student1, Decimal('50.00'), TransactionPaymentStatus.COMPLETED)
        self._create_transaction(self.student2, Decimal('75.00'), TransactionPaymentStatus.COMPLETED)
        
        # Create failed transactions
        self._create_transaction(self.student1, Decimal('30.00'), TransactionPaymentStatus.FAILED)
        
        metrics = self.service.get_success_rate_metrics()
        
        self.assertEqual(metrics['total_transactions'], 3)
        self.assertEqual(metrics['successful_transactions'], 2)
        self.assertEqual(metrics['failed_transactions'], 1)
        self.assertAlmostEqual(metrics['success_rate'], 66.67, places=2)
    
    def test_success_rate_empty_dataset(self):
        """Test success rate calculation with no transactions."""
        metrics = self.service.get_success_rate_metrics()
        
        self.assertEqual(metrics['total_transactions'], 0)
        self.assertEqual(metrics['success_rate'], 0.0)
    
    def test_success_rate_by_time_period(self):
        """Test success rate calculation for specific time periods."""
        # Create transactions at different times
        old_time = self.now - timedelta(days=2)  # Clearly outside 24 hours
        recent_time = self.now - timedelta(minutes=30)  # Clearly within 24 hours
        
        # Old successful transaction
        self._create_transaction(self.student1, Decimal('50.00'), TransactionPaymentStatus.COMPLETED, old_time)
        
        # Recent successful transaction
        self._create_transaction(self.student2, Decimal('75.00'), TransactionPaymentStatus.COMPLETED, recent_time)
        
        # Recent failed transaction
        self._create_transaction(self.student1, Decimal('30.00'), TransactionPaymentStatus.FAILED, recent_time)
        
        # Test last 24 hours
        metrics_24h = self.service.get_success_rate_metrics(hours=24)
        self.assertEqual(metrics_24h['total_transactions'], 2)
        self.assertEqual(metrics_24h['successful_transactions'], 1)
        self.assertAlmostEqual(metrics_24h['success_rate'], 50.0, places=2)
        
        # Test all time
        metrics_all = self.service.get_success_rate_metrics()
        self.assertEqual(metrics_all['total_transactions'], 3)
        self.assertEqual(metrics_all['successful_transactions'], 2)


class RevenueAnalyticsTest(PaymentAnalyticsServiceTest):
    """Test revenue analytics functionality."""
    
    def test_revenue_trends(self):
        """Test revenue trend calculations."""
        # Create transactions over different days
        day1_time = self.now - timedelta(days=2)
        day2_time = self.now - timedelta(days=1)
        day3_time = self.now
        
        # Day 1: €100
        self._create_transaction(self.student1, Decimal('100.00'), TransactionPaymentStatus.COMPLETED, day1_time)
        
        # Day 2: €150 
        self._create_transaction(self.student2, Decimal('75.00'), TransactionPaymentStatus.COMPLETED, day2_time)
        self._create_transaction(self.student1, Decimal('75.00'), TransactionPaymentStatus.COMPLETED, day2_time)
        
        # Day 3: €50 (plus a failed transaction that shouldn't count)
        self._create_transaction(self.student2, Decimal('50.00'), TransactionPaymentStatus.COMPLETED, day3_time)
        self._create_transaction(self.student1, Decimal('25.00'), TransactionPaymentStatus.FAILED, day3_time)
        
        trends = self.service.get_revenue_trends(days=3)
        
        self.assertEqual(len(trends['daily_revenue']), 3)
        self.assertEqual(trends['total_revenue'], Decimal('300.00'))
        
        # Verify daily breakdowns (should be ordered from oldest to newest)
        daily_data = {item['date']: item['revenue'] for item in trends['daily_revenue']}
        self.assertEqual(daily_data[day1_time.date()], Decimal('100.00'))
        self.assertEqual(daily_data[day2_time.date()], Decimal('150.00'))
        self.assertEqual(daily_data[day3_time.date()], Decimal('50.00'))
    
    def test_revenue_by_transaction_type(self):
        """Test revenue breakdown by transaction type."""
        # Create package transactions
        self._create_transaction(self.student1, Decimal('100.00'), TransactionPaymentStatus.COMPLETED, 
                               transaction_type=TransactionType.PACKAGE)
        self._create_transaction(self.student2, Decimal('150.00'), TransactionPaymentStatus.COMPLETED,
                               transaction_type=TransactionType.PACKAGE) 
        
        # Create subscription transactions
        self._create_transaction(self.student1, Decimal('50.00'), TransactionPaymentStatus.COMPLETED,
                               transaction_type=TransactionType.SUBSCRIPTION)
        
        revenue_breakdown = self.service.get_revenue_by_type()
        
        self.assertEqual(revenue_breakdown['package'], Decimal('250.00'))
        self.assertEqual(revenue_breakdown['subscription'], Decimal('50.00'))
        self.assertEqual(revenue_breakdown['total'], Decimal('300.00'))
    
    def test_average_transaction_value(self):
        """Test average transaction value calculation."""
        # Create transactions with different values
        self._create_transaction(self.student1, Decimal('100.00'), TransactionPaymentStatus.COMPLETED)
        self._create_transaction(self.student2, Decimal('200.00'), TransactionPaymentStatus.COMPLETED)
        self._create_transaction(self.student1, Decimal('50.00'), TransactionPaymentStatus.COMPLETED)
        
        # Failed transaction shouldn't affect average
        self._create_transaction(self.student2, Decimal('1000.00'), TransactionPaymentStatus.FAILED)
        
        metrics = self.service.get_transaction_value_metrics()
        
        self.assertEqual(metrics['total_successful_transactions'], 3)
        self.assertEqual(metrics['total_revenue'], Decimal('350.00'))
        self.assertAlmostEqual(float(metrics['average_transaction_value']), 116.67, places=2)
        self.assertEqual(metrics['highest_transaction'], Decimal('200.00'))
        self.assertEqual(metrics['lowest_transaction'], Decimal('50.00'))


class FailureAnalysisTest(PaymentAnalyticsServiceTest):
    """Test payment failure analysis functionality."""
    
    def test_failure_rate_trends(self):
        """Test failure rate trend analysis."""
        # Create transactions over multiple days
        for days_ago in range(7):
            created_time = self.now - timedelta(days=days_ago)
            
            # Create some successful and failed transactions each day
            self._create_transaction(self.student1, Decimal('50.00'), TransactionPaymentStatus.COMPLETED, created_time)
            self._create_transaction(self.student2, Decimal('50.00'), TransactionPaymentStatus.COMPLETED, created_time)
            
            if days_ago < 3:  # More failures in recent days
                self._create_transaction(self.student1, Decimal('25.00'), TransactionPaymentStatus.FAILED, created_time)
        
        failure_trends = self.service.get_failure_analysis(days=7)
        
        self.assertEqual(len(failure_trends['daily_failures']), 7)
        self.assertEqual(failure_trends['total_failures'], 3)
        self.assertAlmostEqual(failure_trends['overall_failure_rate'], 17.65, places=2)  # 3/17 transactions failed
    
    def test_common_failure_reasons(self):
        """Test analysis of common failure reasons."""
        # This would require webhook event analysis
        # Create some webhook events with different failure types
        self._create_webhook_log('payment_intent.payment_failed', WebhookEventStatus.PROCESSED)
        self._create_webhook_log('customer.card_declined', WebhookEventStatus.PROCESSED) 
        self._create_webhook_log('payment_intent.payment_failed', WebhookEventStatus.PROCESSED)
        
        failure_reasons = self.service.get_common_failure_reasons()
        
        self.assertIn('payment_intent.payment_failed', failure_reasons)
        self.assertEqual(failure_reasons['payment_intent.payment_failed'], 2)
        self.assertEqual(failure_reasons['customer.card_declined'], 1)


class WebhookAnalyticsTest(PaymentAnalyticsServiceTest):
    """Test webhook analytics functionality."""
    
    def test_webhook_processing_metrics(self):
        """Test webhook processing performance metrics."""
        # Create webhook logs with different statuses
        self._create_webhook_log('payment_intent.succeeded', WebhookEventStatus.PROCESSED)
        self._create_webhook_log('payment_intent.succeeded', WebhookEventStatus.PROCESSED)
        self._create_webhook_log('payment_intent.payment_failed', WebhookEventStatus.FAILED)
        self._create_webhook_log('customer.created', WebhookEventStatus.RETRYING)
        
        webhook_metrics = self.service.get_webhook_metrics()
        
        self.assertEqual(webhook_metrics['total_events'], 4)
        self.assertEqual(webhook_metrics['processed_events'], 2)
        self.assertEqual(webhook_metrics['failed_events'], 1)
        self.assertEqual(webhook_metrics['retrying_events'], 1)
        self.assertAlmostEqual(webhook_metrics['success_rate'], 50.0, places=2)
    
    def test_webhook_processing_times(self):
        """Test webhook processing time analytics."""
        # Create processed webhook logs
        log1 = self._create_webhook_log('payment_intent.succeeded', WebhookEventStatus.RECEIVED)
        log1.mark_as_processed()
        
        log2 = self._create_webhook_log('customer.created', WebhookEventStatus.RECEIVED)
        log2.mark_as_processed()
        
        processing_metrics = self.service.get_webhook_processing_metrics()
        
        self.assertEqual(processing_metrics['total_processed'], 2)
        self.assertIsNotNone(processing_metrics['average_processing_time'])
        self.assertIsNotNone(processing_metrics['max_processing_time'])
        self.assertIsNotNone(processing_metrics['min_processing_time'])


class DashboardMetricsTest(PaymentAnalyticsServiceTest):
    """Test comprehensive dashboard metrics."""
    
    def test_comprehensive_dashboard_metrics(self):
        """Test getting comprehensive metrics for admin dashboard."""
        # Create a mix of transactions and webhook events
        self._create_transaction(self.student1, Decimal('100.00'), TransactionPaymentStatus.COMPLETED)
        self._create_transaction(self.student2, Decimal('50.00'), TransactionPaymentStatus.FAILED)
        
        self._create_webhook_log('payment_intent.succeeded', WebhookEventStatus.PROCESSED)
        self._create_webhook_log('payment_intent.payment_failed', WebhookEventStatus.FAILED)
        
        # Create student account balance
        StudentAccountBalance.objects.create(
            student=self.student1,
            hours_purchased=Decimal('10.0'),
            hours_consumed=Decimal('5.0'),
            balance_amount=Decimal('50.00')
        )
        
        dashboard_metrics = self.service.get_dashboard_metrics()
        
        # Verify all expected sections are present
        expected_sections = [
            'payment_success_rate',
            'revenue_summary', 
            'transaction_metrics',
            'webhook_metrics',
            'failure_analysis',
            'recent_activity'
        ]
        
        for section in expected_sections:
            self.assertIn(section, dashboard_metrics)
        
        # Verify some specific metrics
        self.assertEqual(dashboard_metrics['payment_success_rate']['total_transactions'], 2)
        self.assertEqual(dashboard_metrics['revenue_summary']['total_revenue'], Decimal('100.00'))
        self.assertEqual(dashboard_metrics['webhook_metrics']['total_events'], 2)
    
    def test_dashboard_metrics_time_filtering(self):
        """Test dashboard metrics with time period filtering."""
        # Create old and recent transactions
        old_time = self.now - timedelta(days=10)
        recent_time = self.now - timedelta(hours=1)
        
        self._create_transaction(self.student1, Decimal('100.00'), TransactionPaymentStatus.COMPLETED, old_time)
        self._create_transaction(self.student2, Decimal('50.00'), TransactionPaymentStatus.COMPLETED, recent_time)
        
        # Test 24-hour metrics
        metrics_24h = self.service.get_dashboard_metrics(hours=24)
        self.assertEqual(metrics_24h['payment_success_rate']['total_transactions'], 1)
        self.assertEqual(metrics_24h['revenue_summary']['total_revenue'], Decimal('50.00'))
        
        # Test all-time metrics
        metrics_all = self.service.get_dashboard_metrics()
        self.assertEqual(metrics_all['payment_success_rate']['total_transactions'], 2)
        self.assertEqual(metrics_all['revenue_summary']['total_revenue'], Decimal('150.00'))


class PerformanceOptimizationTest(PaymentAnalyticsServiceTest):
    """Test performance optimization and caching."""
    
    def test_large_dataset_performance(self):
        """Test analytics performance with larger datasets."""
        # Create a larger number of transactions
        for i in range(100):
            status = TransactionPaymentStatus.COMPLETED if i % 3 != 0 else TransactionPaymentStatus.FAILED
            amount = Decimal('50.00') if i % 2 == 0 else Decimal('75.00')
            
            self._create_transaction(
                self.student1 if i % 2 == 0 else self.student2,
                amount,
                status,
                self.now - timedelta(days=i % 30)  # Spread over 30 days
            )
        
        # Test that analytics still perform reasonably
        import time
        start_time = time.time()
        
        dashboard_metrics = self.service.get_dashboard_metrics()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(processing_time, 2.0)  # 2 seconds max
        
        # Verify metrics are still accurate
        self.assertEqual(dashboard_metrics['payment_success_rate']['total_transactions'], 100)
        expected_successful = 67  # Roughly 2/3 should be successful based on our logic
        self.assertEqual(dashboard_metrics['payment_success_rate']['successful_transactions'], expected_successful)