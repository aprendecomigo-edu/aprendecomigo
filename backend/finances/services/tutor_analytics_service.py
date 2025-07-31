"""
Tutor Analytics Service

Provides business metrics and analytics for individual tutors managing their own schools.
Focuses on revenue trends, session analytics, and student metrics.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.db.models import (
    Sum, Count, Avg, Q, F, Value, DecimalField,
    Case, When, IntegerField
)
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, Coalesce
from django.utils import timezone
from django.core.cache import cache

from accounts.models import School, TeacherProfile, SchoolMembership, SchoolRole
from finances.models import (
    ClassSession, SessionStatus, SessionType,
    TeacherPaymentEntry, PaymentStatus,
    StudentAccountBalance, PurchaseTransaction, TransactionPaymentStatus
)


class TutorAnalyticsService:
    """
    Service class for generating tutor analytics and business metrics.
    
    All methods ensure school-scoped data access for security.
    """
    
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @classmethod
    def get_tutor_analytics(
        cls, 
        teacher: TeacherProfile, 
        school: School,
        time_range: str = "30d",
        include_projections: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a tutor.
        
        Args:
            teacher: TeacherProfile instance
            school: School instance (must be owned by teacher)
            time_range: One of "7d", "30d", "90d", "1y"
            include_projections: Whether to include revenue projections
            
        Returns:
            Dictionary with analytics data
        """
        # Validate teacher owns the school
        if not cls._validate_teacher_school_ownership(teacher, school):
            raise PermissionError("Teacher does not own or manage this school")
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = cls._calculate_start_date(end_date, time_range)
        
        # Generate cache key
        cache_key = f"tutor_analytics_{teacher.id}_{school.id}_{time_range}_{start_date}_{end_date}"
        
        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Build analytics data
        analytics = {
            "overview": cls._get_overview_metrics(teacher, school, start_date, end_date),
            "revenue": cls._get_revenue_analytics(teacher, school, start_date, end_date),
            "sessions": cls._get_session_analytics(teacher, school, start_date, end_date),
            "students": cls._get_student_analytics(teacher, school, start_date, end_date),
            "trends": cls._get_trend_analytics(teacher, school, start_date, end_date),
            "meta": {
                "time_range": time_range,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "generated_at": timezone.now().isoformat()
            }
        }
        
        if include_projections:
            analytics["projections"] = cls._get_revenue_projections(teacher, school)
        
        # Cache the results
        cache.set(cache_key, analytics, cls.CACHE_TIMEOUT)
        
        return analytics
    
    @classmethod
    def _validate_teacher_school_ownership(cls, teacher: TeacherProfile, school: School) -> bool:
        """Validate that teacher owns or manages the school."""
        return SchoolMembership.objects.filter(
            user=teacher.user,
            school=school,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists()
    
    @classmethod
    def _calculate_start_date(cls, end_date: datetime.date, time_range: str) -> datetime.date:
        """Calculate start date based on time range."""
        if time_range == "7d":
            return end_date - timedelta(days=7)
        elif time_range == "30d":
            return end_date - timedelta(days=30)
        elif time_range == "90d":
            return end_date - timedelta(days=90)
        elif time_range == "1y":
            return end_date - timedelta(days=365)
        else:
            # Default to 30 days
            return end_date - timedelta(days=30)
    
    @classmethod
    def _get_overview_metrics(
        cls, 
        teacher: TeacherProfile, 
        school: School, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> Dict[str, Any]:
        """Get high-level overview metrics."""
        
        # Total revenue in period
        total_revenue = TeacherPaymentEntry.objects.filter(
            teacher=teacher,
            school=school,
            session__date__range=(start_date, end_date),
            payment_status__in=[PaymentStatus.CALCULATED, PaymentStatus.PAID]
        ).aggregate(
            total=Coalesce(Sum('amount_earned'), Decimal('0.00'))
        )['total']
        
        # Total sessions in period
        session_stats = ClassSession.objects.filter(
            teacher=teacher,
            school=school,
            date__range=(start_date, end_date)
        ).aggregate(
            total_sessions=Count('id'),
            completed_sessions=Count('id', filter=Q(status=SessionStatus.COMPLETED)),
            cancelled_sessions=Count('id', filter=Q(status=SessionStatus.CANCELLED)),
            total_hours=Coalesce(Sum('actual_duration_hours'), Decimal('0.00'))
        )
        
        # Active students (students with sessions in period)
        active_students = ClassSession.objects.filter(
            teacher=teacher,
            school=school,
            date__range=(start_date, end_date),
            status=SessionStatus.COMPLETED
        ).values('students').distinct().count()
        
        # Completion rate
        completion_rate = 0
        if session_stats['total_sessions'] > 0:
            completion_rate = (session_stats['completed_sessions'] / session_stats['total_sessions']) * 100
        
        return {
            "total_revenue": float(total_revenue),
            "total_sessions": session_stats['total_sessions'],
            "completed_sessions": session_stats['completed_sessions'],
            "cancelled_sessions": session_stats['cancelled_sessions'],
            "total_hours_taught": float(session_stats['total_hours'] or 0),
            "active_students": active_students,
            "completion_rate": round(completion_rate, 2)
        }
    
    @classmethod
    def _get_revenue_analytics(
        cls, 
        teacher: TeacherProfile, 
        school: School, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> Dict[str, Any]:
        """Get detailed revenue analytics."""
        
        # Revenue by session type
        revenue_by_type = TeacherPaymentEntry.objects.filter(
            teacher=teacher,
            school=school,
            session__date__range=(start_date, end_date),
            payment_status__in=[PaymentStatus.CALCULATED, PaymentStatus.PAID]
        ).values('session__session_type').annotate(
            revenue=Coalesce(Sum('amount_earned'), Decimal('0.00')),
            sessions=Count('session'),
            avg_per_session=Avg('amount_earned')
        )
        
        # Revenue trends (daily over period)
        revenue_trends = TeacherPaymentEntry.objects.filter(
            teacher=teacher,
            school=school,
            session__date__range=(start_date, end_date),
            payment_status__in=[PaymentStatus.CALCULATED, PaymentStatus.PAID]
        ).extra(
            select={'day': 'date(session_date)'}
        ).values('session__date').annotate(
            revenue=Coalesce(Sum('amount_earned'), Decimal('0.00')),
            sessions=Count('session')
        ).order_by('session__date')
        
        # Average hourly rate
        avg_hourly_rate = TeacherPaymentEntry.objects.filter(
            teacher=teacher,
            school=school,
            session__date__range=(start_date, end_date),
            payment_status__in=[PaymentStatus.CALCULATED, PaymentStatus.PAID]
        ).aggregate(
            avg_rate=Avg('rate_applied')
        )['avg_rate'] or Decimal('0.00')
        
        return {
            "by_session_type": [
                {
                    "session_type": item['session__session_type'],
                    "revenue": float(item['revenue']),
                    "sessions": item['sessions'],
                    "avg_per_session": float(item['avg_per_session'] or 0)
                }
                for item in revenue_by_type
            ],
            "daily_trends": [
                {
                    "date": item['session__date'].isoformat(),
                    "revenue": float(item['revenue']),
                    "sessions": item['sessions']
                }
                for item in revenue_trends
            ],
            "average_hourly_rate": float(avg_hourly_rate)
        }
    
    @classmethod
    def _get_session_analytics(
        cls, 
        teacher: TeacherProfile, 
        school: School, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> Dict[str, Any]:
        """Get session-related analytics."""
        
        # Sessions by status
        sessions_by_status = ClassSession.objects.filter(
            teacher=teacher,
            school=school,
            date__range=(start_date, end_date)
        ).values('status').annotate(
            count=Count('id')
        )
        
        # Sessions by type
        sessions_by_type = ClassSession.objects.filter(
            teacher=teacher,
            school=school,
            date__range=(start_date, end_date)
        ).values('session_type').annotate(
            count=Count('id'),
            avg_duration=Avg('actual_duration_hours')
        )
        
        # Peak teaching hours (hours of day when most sessions occur)
        peak_hours = ClassSession.objects.filter(
            teacher=teacher,
            school=school,
            date__range=(start_date, end_date),
            status=SessionStatus.COMPLETED
        ).extra(
            select={'hour': 'EXTRACT(hour FROM start_time)'}
        ).values('hour').annotate(
            sessions=Count('id')
        ).order_by('-sessions')[:5]  # Top 5 hours
        
        return {
            "by_status": [
                {
                    "status": item['status'],
                    "count": item['count']
                }
                for item in sessions_by_status
            ],
            "by_type": [
                {
                    "session_type": item['session_type'],
                    "count": item['count'],
                    "avg_duration_hours": float(item['avg_duration'] or 0)
                }
                for item in sessions_by_type
            ],
            "peak_teaching_hours": [
                {
                    "hour": int(item['hour']),
                    "sessions": item['sessions']
                }
                for item in peak_hours
            ]
        }
    
    @classmethod
    def _get_student_analytics(
        cls, 
        teacher: TeacherProfile, 
        school: School, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> Dict[str, Any]:
        """Get student-related analytics."""
        
        # Get all students who had sessions with this teacher in this school
        student_sessions = ClassSession.objects.filter(
            teacher=teacher,
            school=school,
            date__range=(start_date, end_date),
            status=SessionStatus.COMPLETED
        ).prefetch_related('students')
        
        # Students with session counts
        student_data = {}
        for session in student_sessions:
            for student in session.students.all():
                if student.id not in student_data:
                    student_data[student.id] = {
                        'name': student.name,
                        'sessions': 0,
                        'hours': Decimal('0.00')
                    }
                student_data[student.id]['sessions'] += 1
                student_data[student.id]['hours'] += session.actual_duration_hours or session.duration_hours
        
        # Sort by session count
        top_students = sorted(
            student_data.values(),
            key=lambda x: x['sessions'],
            reverse=True
        )[:10]  # Top 10 students
        
        # New vs returning students
        all_time_students = set()
        for session in ClassSession.objects.filter(
            teacher=teacher,
            school=school,
            date__lt=start_date,
            status=SessionStatus.COMPLETED
        ).prefetch_related('students'):
            for student in session.students.all():
                all_time_students.add(student.id)
        
        period_students = set(student_data.keys())
        new_students = period_students - all_time_students
        returning_students = period_students - new_students
        
        return {
            "total_active_students": len(student_data),
            "new_students": len(new_students),
            "returning_students": len(returning_students),
            "top_students": [
                {
                    "name": student['name'],
                    "sessions": student['sessions'],
                    "hours": float(student['hours'])
                }
                for student in top_students
            ]
        }
    
    @classmethod
    def _get_trend_analytics(
        cls, 
        teacher: TeacherProfile, 
        school: School, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> Dict[str, Any]:
        """Get trend analytics comparing with previous period."""
        
        # Calculate previous period
        period_length = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_length)
        previous_end = start_date
        
        # Current period metrics
        current_metrics = cls._get_period_metrics(teacher, school, start_date, end_date)
        previous_metrics = cls._get_period_metrics(teacher, school, previous_start, previous_end)
        
        # Calculate changes
        def calculate_change(current, previous):
            if previous == 0 and current == 0:
                return 0
            elif previous == 0:
                return 100  # 100% increase from 0
            else:
                return ((current - previous) / previous) * 100
        
        return {
            "revenue_change": round(calculate_change(
                current_metrics['revenue'], 
                previous_metrics['revenue']
            ), 2),
            "sessions_change": round(calculate_change(
                current_metrics['sessions'], 
                previous_metrics['sessions']
            ), 2),
            "students_change": round(calculate_change(
                current_metrics['students'], 
                previous_metrics['students']
            ), 2),
            "hours_change": round(calculate_change(
                current_metrics['hours'], 
                previous_metrics['hours']
            ), 2)
        }
    
    @classmethod
    def _get_period_metrics(
        cls, 
        teacher: TeacherProfile, 
        school: School, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> Dict[str, float]:
        """Get basic metrics for a period."""
        
        revenue = TeacherPaymentEntry.objects.filter(
            teacher=teacher,
            school=school,
            session__date__range=(start_date, end_date),
            payment_status__in=[PaymentStatus.CALCULATED, PaymentStatus.PAID]
        ).aggregate(
            total=Coalesce(Sum('amount_earned'), Decimal('0.00'))
        )['total']
        
        session_data = ClassSession.objects.filter(
            teacher=teacher,
            school=school,
            date__range=(start_date, end_date)
        ).aggregate(
            sessions=Count('id'),
            hours=Coalesce(Sum('actual_duration_hours'), Decimal('0.00'))
        )
        
        # Count unique students
        students = ClassSession.objects.filter(
            teacher=teacher,
            school=school,
            date__range=(start_date, end_date),
            status=SessionStatus.COMPLETED
        ).values('students').distinct().count()
        
        return {
            'revenue': float(revenue),
            'sessions': session_data['sessions'],
            'hours': float(session_data['hours'] or 0),
            'students': students
        }
    
    @classmethod
    def _get_revenue_projections(
        cls, 
        teacher: TeacherProfile, 
        school: School
    ) -> Dict[str, Any]:
        """Get revenue projections based on historical data."""
        
        # Get last 3 months of data for projection
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)
        
        # Monthly revenue trend
        monthly_revenue = TeacherPaymentEntry.objects.filter(
            teacher=teacher,
            school=school,
            session__date__range=(start_date, end_date),
            payment_status__in=[PaymentStatus.CALCULATED, PaymentStatus.PAID]
        ).extra(
            select={'month': 'EXTRACT(month FROM session_date)', 'year': 'EXTRACT(year FROM session_date)'}
        ).values('session__date__month', 'session__date__year').annotate(
            revenue=Coalesce(Sum('amount_earned'), Decimal('0.00'))
        ).order_by('session__date__year', 'session__date__month')
        
        if len(monthly_revenue) < 2:
            return {
                "next_month_projection": 0.0,
                "confidence": "low",
                "note": "Insufficient historical data for reliable projections"
            }
        
        # Simple linear trend calculation
        revenues = [float(item['revenue']) for item in monthly_revenue]
        if len(revenues) >= 3:
            # Use last 3 months average growth
            recent_avg = sum(revenues[-3:]) / 3
            earlier_avg = sum(revenues[-6:-3]) / 3 if len(revenues) >= 6 else revenues[0]
            
            if earlier_avg > 0:
                growth_rate = (recent_avg - earlier_avg) / earlier_avg
            else:
                growth_rate = 0
            
            next_month_projection = recent_avg * (1 + growth_rate)
            confidence = "medium" if len(revenues) >= 6 else "low"
        else:
            # Use simple average
            next_month_projection = sum(revenues) / len(revenues)
            confidence = "low"
        
        return {
            "next_month_projection": round(next_month_projection, 2),
            "confidence": confidence,
            "historical_months": len(revenues)
        }