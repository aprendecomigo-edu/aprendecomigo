"""
Payment Analytics Service for administrative dashboard monitoring.

This service provides comprehensive analytics for payment system monitoring,
including success rates, revenue trends, failure analysis, and webhook metrics
for administrative oversight of the Aprende Comigo platform.
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.db.models import Count, Sum, Avg, Q, Max, Min
from django.utils import timezone

from finances.models import (
    PurchaseTransaction, TransactionPaymentStatus, TransactionType,
    WebhookEventLog, WebhookEventStatus, StudentAccountBalance
)

logger = logging.getLogger(__name__)


class PaymentAnalyticsService:
    """
    Service for payment system analytics and monitoring.
    
    Provides comprehensive metrics for administrative dashboard including:
    - Payment success rates and trends
    - Revenue analysis and forecasting
    - Failure pattern detection
    - Webhook processing monitoring
    - Performance metrics
    """
    
    def __init__(self):
        """Initialize the analytics service."""
        self.cache_timeout = 300  # 5 minutes cache for expensive queries
    
    def get_success_rate_metrics(self, hours: Optional[int] = None, days: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate payment success rate metrics.
        
        Args:
            hours: Limit analysis to last N hours
            days: Limit analysis to last N days
            
        Returns:
            Dict containing success rate metrics
        """
        queryset = PurchaseTransaction.objects.all()
        
        # Apply time filtering
        if hours:
            cutoff_time = timezone.now() - timedelta(hours=hours)
            queryset = queryset.filter(created_at__gte=cutoff_time)
        elif days:
            cutoff_time = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created_at__gte=cutoff_time)
        
        # Calculate metrics
        total_transactions = queryset.count()
        
        if total_transactions == 0:
            return {
                'total_transactions': 0,
                'successful_transactions': 0,
                'failed_transactions': 0,
                'pending_transactions': 0,
                'success_rate': 0.0,
                'failure_rate': 0.0
            }
        
        successful_transactions = queryset.filter(
            payment_status=TransactionPaymentStatus.COMPLETED
        ).count()
        
        failed_transactions = queryset.filter(
            payment_status=TransactionPaymentStatus.FAILED
        ).count()
        
        pending_transactions = queryset.filter(
            payment_status__in=[
                TransactionPaymentStatus.PENDING,
                TransactionPaymentStatus.PROCESSING
            ]
        ).count()
        
        success_rate = (successful_transactions / total_transactions) * 100
        failure_rate = (failed_transactions / total_transactions) * 100
        
        return {
            'total_transactions': total_transactions,
            'successful_transactions': successful_transactions,
            'failed_transactions': failed_transactions,
            'pending_transactions': pending_transactions,
            'success_rate': round(success_rate, 2),
            'failure_rate': round(failure_rate, 2)
        }
    
    def get_revenue_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get revenue trend analysis over specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing revenue trends and daily breakdowns
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Get successful transactions only
        transactions = PurchaseTransaction.objects.filter(
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at__gte=cutoff_date
        ).order_by('created_at')
        
        # Calculate total revenue
        total_revenue = transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Group by date for daily trends
        daily_revenue = {}
        for transaction in transactions:
            date = transaction.created_at.date()
            daily_revenue[date] = daily_revenue.get(date, Decimal('0.00')) + transaction.amount
        
        # Convert to list format for API response
        daily_data = []
        current_date = cutoff_date.date()
        end_date = timezone.now().date()
        
        while current_date <= end_date:
            daily_data.append({
                'date': current_date,
                'revenue': daily_revenue.get(current_date, Decimal('0.00'))
            })
            current_date += timedelta(days=1)
        
        return {
            'total_revenue': total_revenue,
            'daily_revenue': daily_data,
            'period_days': days,
            'average_daily_revenue': total_revenue / days if days > 0 else Decimal('0.00')
        }
    
    def get_revenue_by_type(self, hours: Optional[int] = None) -> Dict[str, Decimal]:
        """
        Get revenue breakdown by transaction type.
        
        Args:
            hours: Limit to last N hours (optional)
            
        Returns:
            Dict with revenue by transaction type
        """
        queryset = PurchaseTransaction.objects.filter(
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        if hours:
            cutoff_time = timezone.now() - timedelta(hours=hours)
            queryset = queryset.filter(created_at__gte=cutoff_time)
        
        # Group by transaction type
        type_breakdown = queryset.values('transaction_type').annotate(
            revenue=Sum('amount')
        )
        
        result = {
            'package': Decimal('0.00'),
            'subscription': Decimal('0.00'),
            'total': Decimal('0.00')
        }
        
        for item in type_breakdown:
            transaction_type = item['transaction_type']
            revenue = item['revenue'] or Decimal('0.00')
            
            if transaction_type == TransactionType.PACKAGE:
                result['package'] = revenue
            elif transaction_type == TransactionType.SUBSCRIPTION:
                result['subscription'] = revenue
            
            result['total'] += revenue
        
        return result
    
    def get_transaction_value_metrics(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Get transaction value analysis metrics.
        
        Args:
            hours: Limit to last N hours (optional)
            
        Returns:
            Dict containing transaction value metrics
        """
        queryset = PurchaseTransaction.objects.filter(
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        if hours:
            cutoff_time = timezone.now() - timedelta(hours=hours)
            queryset = queryset.filter(created_at__gte=cutoff_time)
        
        if not queryset.exists():
            return {
                'total_successful_transactions': 0,
                'total_revenue': Decimal('0.00'),
                'average_transaction_value': Decimal('0.00'),
                'highest_transaction': Decimal('0.00'),
                'lowest_transaction': Decimal('0.00')
            }
        
        aggregates = queryset.aggregate(
            total_transactions=Count('id'),
            total_revenue=Sum('amount'),
            average_value=Avg('amount'),
            highest_value=Max('amount'),
            lowest_value=Min('amount')
        )
        
        return {
            'total_successful_transactions': aggregates['total_transactions'],
            'total_revenue': aggregates['total_revenue'] or Decimal('0.00'),
            'average_transaction_value': aggregates['average_value'] or Decimal('0.00'),
            'highest_transaction': aggregates['highest_value'] or Decimal('0.00'),
            'lowest_transaction': aggregates['lowest_value'] or Decimal('0.00')
        }
    
    def get_failure_analysis(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze payment failures over specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing failure analysis metrics
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        all_transactions = PurchaseTransaction.objects.filter(
            created_at__gte=cutoff_date
        )
        
        failed_transactions = all_transactions.filter(
            payment_status=TransactionPaymentStatus.FAILED
        )
        
        total_transactions = all_transactions.count()
        total_failures = failed_transactions.count()
        
        overall_failure_rate = (total_failures / total_transactions * 100) if total_transactions > 0 else 0
        
        # Daily failure breakdown
        daily_failures = {}
        for transaction in failed_transactions:
            date = transaction.created_at.date()
            daily_failures[date] = daily_failures.get(date, 0) + 1
        
        # Convert to list format
        daily_data = []
        current_date = cutoff_date.date()
        end_date = timezone.now().date()
        
        while current_date <= end_date:
            daily_data.append({
                'date': current_date,
                'failures': daily_failures.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        return {
            'total_failures': total_failures,
            'total_transactions': total_transactions,
            'overall_failure_rate': round(overall_failure_rate, 2),
            'daily_failures': daily_data,
            'period_days': days
        }
    
    def get_common_failure_reasons(self, days: int = 7) -> Dict[str, int]:
        """
        Analyze common failure reasons from webhook events.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict mapping failure reasons to occurrence counts
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Get failed webhook events that might indicate payment failures
        failed_events = WebhookEventLog.objects.filter(
            created_at__gte=cutoff_date,
            event_type__icontains='failed'
        )
        
        # Count event types
        event_counts = failed_events.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {item['event_type']: item['count'] for item in event_counts}
    
    def get_webhook_metrics(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Get webhook processing metrics.
        
        Args:
            hours: Limit to last N hours (optional)
            
        Returns:
            Dict containing webhook processing metrics
        """
        queryset = WebhookEventLog.objects.all()
        
        if hours:
            cutoff_time = timezone.now() - timedelta(hours=hours)
            queryset = queryset.filter(created_at__gte=cutoff_time)
        
        total_events = queryset.count()
        
        if total_events == 0:
            return {
                'total_events': 0,
                'processed_events': 0,
                'failed_events': 0,
                'retrying_events': 0,
                'pending_events': 0,
                'success_rate': 0.0
            }
        
        # Build status map by manually counting each status
        # This is more reliable than the values().annotate() approach which seems to have issues
        processed_events = queryset.filter(status=WebhookEventStatus.PROCESSED).count()
        failed_events = queryset.filter(status=WebhookEventStatus.FAILED).count()
        retrying_events = queryset.filter(status=WebhookEventStatus.RETRYING).count()
        received_events = queryset.filter(status=WebhookEventStatus.RECEIVED).count()
        processing_events = queryset.filter(status=WebhookEventStatus.PROCESSING).count()
        pending_events = received_events + processing_events
        
        success_rate = (processed_events / total_events) * 100 if total_events > 0 else 0
        
        return {
            'total_events': total_events,
            'processed_events': processed_events,
            'failed_events': failed_events,
            'retrying_events': retrying_events,
            'pending_events': pending_events,
            'success_rate': round(success_rate, 2)
        }
    
    def get_webhook_processing_metrics(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Get webhook processing time metrics.
        
        Args:
            hours: Limit to last N hours (optional)
            
        Returns:
            Dict containing processing time metrics
        """
        queryset = WebhookEventLog.objects.filter(
            status=WebhookEventStatus.PROCESSED,
            processed_at__isnull=False
        )
        
        if hours:
            cutoff_time = timezone.now() - timedelta(hours=hours)
            queryset = queryset.filter(created_at__gte=cutoff_time)
        
        processing_times = []
        for log in queryset:
            duration = log.get_processing_duration()
            if duration:
                processing_times.append(duration.total_seconds())
        
        if not processing_times:
            return {
                'total_processed': 0,
                'average_processing_time': 0.0,
                'max_processing_time': 0.0,
                'min_processing_time': 0.0
            }
        
        return {
            'total_processed': len(processing_times),
            'average_processing_time': sum(processing_times) / len(processing_times),
            'max_processing_time': max(processing_times),
            'min_processing_time': min(processing_times)
        }
    
    def get_dashboard_metrics(self, hours: Optional[int] = None, days: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics for admin interface.
        
        Args:
            hours: Limit analysis to last N hours
            days: Limit analysis to last N days (overridden by hours if both provided)
            
        Returns:
            Dict containing all dashboard metrics
        """
        try:
            # Use hours if provided, otherwise use days
            time_filter_hours = hours
            time_filter_days = days if not hours else None
            
            logger.info(f"Generating dashboard metrics for hours={time_filter_hours}, days={time_filter_days}")
            
            metrics = {
                'generated_at': timezone.now(),
                'time_period': {
                    'hours': time_filter_hours,
                    'days': time_filter_days
                },
                'payment_success_rate': self.get_success_rate_metrics(
                    hours=time_filter_hours, days=time_filter_days
                ),
                'revenue_summary': self.get_revenue_by_type(hours=time_filter_hours),
                'transaction_metrics': self.get_transaction_value_metrics(hours=time_filter_hours),
                'webhook_metrics': self.get_webhook_metrics(hours=time_filter_hours),
                'failure_analysis': self.get_failure_analysis(days=time_filter_days or 7),
                'recent_activity': self._get_recent_activity_summary()
            }
            
            # Add revenue trends if analyzing multiple days
            if time_filter_days and time_filter_days > 1:
                metrics['revenue_trends'] = self.get_revenue_trends(days=time_filter_days)
            
            logger.info("Dashboard metrics generated successfully")
            return metrics
            
        except Exception as e:
            logger.error(f"Error generating dashboard metrics: {str(e)}", exc_info=True)
            raise
    
    def _get_recent_activity_summary(self) -> Dict[str, Any]:
        """
        Get summary of recent payment activity.
        
        Returns:
            Dict containing recent activity metrics
        """
        last_24h = timezone.now() - timedelta(hours=24)
        
        recent_transactions = PurchaseTransaction.objects.filter(
            created_at__gte=last_24h
        )
        
        recent_webhooks = WebhookEventLog.objects.filter(
            created_at__gte=last_24h
        )
        
        return {
            'recent_transactions': recent_transactions.count(),
            'recent_successful_payments': recent_transactions.filter(
                payment_status=TransactionPaymentStatus.COMPLETED
            ).count(),
            'recent_failed_payments': recent_transactions.filter(
                payment_status=TransactionPaymentStatus.FAILED
            ).count(),
            'recent_webhook_events': recent_webhooks.count(),
            'recent_webhook_failures': recent_webhooks.filter(
                status=WebhookEventStatus.FAILED
            ).count()
        }
    
    def get_student_analytics(self, student_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics for a specific student.
        
        Args:
            student_id: ID of the student to analyze
            days: Number of days to analyze
            
        Returns:
            Dict containing student-specific analytics
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        transactions = PurchaseTransaction.objects.filter(
            student_id=student_id,
            created_at__gte=cutoff_date
        )
        
        total_spent = transactions.filter(
            payment_status=TransactionPaymentStatus.COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get account balance if exists
        try:
            account_balance = StudentAccountBalance.objects.get(student_id=student_id)
            balance_info = {
                'current_balance': account_balance.balance_amount,
                'hours_purchased': account_balance.hours_purchased,
                'hours_consumed': account_balance.hours_consumed,
                'hours_remaining': account_balance.remaining_hours
            }
        except StudentAccountBalance.DoesNotExist:
            balance_info = {
                'current_balance': Decimal('0.00'),
                'hours_purchased': Decimal('0.00'),
                'hours_consumed': Decimal('0.00'),
                'hours_remaining': Decimal('0.00')
            }
        
        return {
            'student_id': student_id,
            'period_days': days,
            'total_transactions': transactions.count(),
            'successful_transactions': transactions.filter(
                payment_status=TransactionPaymentStatus.COMPLETED
            ).count(),
            'total_spent': total_spent,
            'account_balance': balance_info,
            'transaction_history': list(transactions.order_by('-created_at')[:10].values(
                'id', 'amount', 'payment_status', 'transaction_type', 'created_at'
            ))
        }