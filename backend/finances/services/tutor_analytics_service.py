"""
Tutor Analytics Service for financial analytics and reporting.

This service provides analytics functionality for tutors including
revenue tracking, session statistics, and financial performance metrics.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone

from finances.models import (
    PurchaseTransaction,
    TransactionPaymentStatus,
    TransactionType,
    TeacherPaymentEntry,
    ClassSession,
)

logger = logging.getLogger(__name__)


class TutorAnalyticsService:
    """
    Service for providing tutor-focused financial analytics and insights.
    
    This service helps tutors track their earnings, session performance,
    and financial trends across different time periods.
    """
    
    def __init__(self):
        """Initialize the tutor analytics service."""
        logger.info("TutorAnalyticsService initialized")
    
    def get_tutor_revenue_summary(
        self,
        tutor_user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get revenue summary for a tutor within a date range.
        
        Args:
            tutor_user_id: ID of the tutor user
            start_date: Start date for the analysis (defaults to 30 days ago)
            end_date: End date for the analysis (defaults to now)
            
        Returns:
            Dict containing revenue summary metrics
        """
        if end_date is None:
            end_date = timezone.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
            
        logger.info(f"Generating revenue summary for tutor {tutor_user_id} from {start_date} to {end_date}")
        
        try:
            # Get payment entries for the tutor in the date range
            payment_entries = TeacherPaymentEntry.objects.filter(
                teacher_id=tutor_user_id,
                session__created_at__range=(start_date, end_date),
                payment_status='completed'
            )
            
            # Calculate metrics
            total_earnings = payment_entries.aggregate(
                total=Sum('payment_amount')
            )['total'] or Decimal('0.00')
            
            session_count = payment_entries.count()
            
            average_per_session = (
                total_earnings / session_count if session_count > 0 else Decimal('0.00')
            )
            
            # Get sessions breakdown
            sessions_by_type = payment_entries.values('session__session_type').annotate(
                count=Count('id'),
                earnings=Sum('payment_amount')
            )
            
            return {
                'success': True,
                'tutor_id': tutor_user_id,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_earnings': str(total_earnings),
                    'session_count': session_count,
                    'average_per_session': str(average_per_session)
                },
                'sessions_breakdown': list(sessions_by_type),
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating tutor revenue summary: {e}")
            return {
                'success': False,
                'error_type': 'analytics_error',
                'message': 'Unable to generate revenue summary'
            }
    
    def get_tutor_session_analytics(
        self,
        tutor_user_id: int,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get session analytics for a tutor over a specified period.
        
        Args:
            tutor_user_id: ID of the tutor user
            period_days: Number of days to analyze (default: 30)
            
        Returns:
            Dict containing session analytics
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=period_days)
        
        logger.info(f"Generating session analytics for tutor {tutor_user_id} over {period_days} days")
        
        try:
            # Get sessions for the tutor in the period
            sessions = ClassSession.objects.filter(
                teacher_id=tutor_user_id,
                created_at__range=(start_date, end_date)
            )
            
            # Calculate session metrics
            total_sessions = sessions.count()
            completed_sessions = sessions.filter(status='completed').count()
            cancelled_sessions = sessions.filter(status='cancelled').count()
            
            completion_rate = (
                (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
            )
            
            # Average session duration
            avg_duration = sessions.filter(
                status='completed',
                actual_duration_minutes__isnull=False
            ).aggregate(
                avg=Avg('actual_duration_minutes')
            )['avg'] or 0
            
            # Sessions by day of week
            sessions_by_day = {}
            for session in sessions:
                day_name = session.created_at.strftime('%A')
                sessions_by_day[day_name] = sessions_by_day.get(day_name, 0) + 1
            
            return {
                'success': True,
                'tutor_id': tutor_user_id,
                'period_days': period_days,
                'session_metrics': {
                    'total_sessions': total_sessions,
                    'completed_sessions': completed_sessions,
                    'cancelled_sessions': cancelled_sessions,
                    'completion_rate': round(completion_rate, 2),
                    'average_duration_minutes': round(avg_duration, 2) if avg_duration else 0
                },
                'sessions_by_day': sessions_by_day,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating session analytics: {e}")
            return {
                'success': False,
                'error_type': 'analytics_error',
                'message': 'Unable to generate session analytics'
            }
    
    def get_tutor_earnings_trend(
        self,
        tutor_user_id: int,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Get earnings trend for a tutor over specified number of months.
        
        Args:
            tutor_user_id: ID of the tutor user
            months: Number of months to analyze (default: 6)
            
        Returns:
            Dict containing earnings trend data
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months * 30)  # Approximate months
        
        logger.info(f"Generating earnings trend for tutor {tutor_user_id} over {months} months")
        
        try:
            # Get payment entries grouped by month
            payment_entries = TeacherPaymentEntry.objects.filter(
                teacher_id=tutor_user_id,
                session__created_at__range=(start_date, end_date),
                payment_status='completed'
            ).extra(
                select={'month': "strftime('%%Y-%%m', session__created_at)"}
            ).values('month').annotate(
                earnings=Sum('payment_amount'),
                session_count=Count('id')
            ).order_by('month')
            
            # Format the data for frontend consumption
            trend_data = []
            for entry in payment_entries:
                trend_data.append({
                    'month': entry['month'],
                    'earnings': str(entry['earnings']),
                    'session_count': entry['session_count']
                })
            
            # Calculate total for the period
            total_earnings = sum(
                Decimal(entry['earnings']) for entry in trend_data
            )
            
            return {
                'success': True,
                'tutor_id': tutor_user_id,
                'months_analyzed': months,
                'trend_data': trend_data,
                'total_earnings': str(total_earnings),
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating earnings trend: {e}")
            return {
                'success': False,
                'error_type': 'analytics_error',
                'message': 'Unable to generate earnings trend'
            }