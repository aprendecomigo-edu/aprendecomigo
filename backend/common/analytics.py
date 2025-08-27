"""
Advanced analytics and business intelligence logging for Aprende Comigo.
Tracks user behavior, business metrics, and system performance.
"""

import logging
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache

User = get_user_model()

# Business analytics logger
analytics_logger = logging.getLogger('business.analytics')
performance_logger = logging.getLogger('performance.analytics')
user_behavior_logger = logging.getLogger('business.user_behavior')


class AnalyticsTracker:
    """
    Central analytics tracking system for business intelligence.
    """
    
    @staticmethod
    def track_user_action(user, action, resource=None, metadata=None):
        """Track user actions for behavior analysis."""
        data = {
            'user_id': user.id if user and user.is_authenticated else None,
            'user_type': user.role if user and user.is_authenticated else 'anonymous',
            'action': action,
            'resource': resource,
            'timestamp': timezone.now().isoformat(),
            'metadata': metadata or {}
        }
        
        user_behavior_logger.info(
            f"User action: {action}",
            extra={'analytics_data': data}
        )
    
    @staticmethod
    def track_business_event(event_type, event_data):
        """Track significant business events."""
        data = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': event_data
        }
        
        analytics_logger.info(
            f"Business event: {event_type}",
            extra={'business_event': data}
        )
    
    @staticmethod
    def track_financial_event(event_type, amount, currency='EUR', user=None, metadata=None):
        """Track financial events for revenue analytics."""
        data = {
            'event_type': event_type,  # payment_received, refund_issued, etc.
            'amount': str(amount),
            'currency': currency,
            'user_id': user.id if user else None,
            'timestamp': timezone.now().isoformat(),
            'metadata': metadata or {}
        }
        
        analytics_logger.info(
            f"Financial event: {event_type} {amount} {currency}",
            extra={'financial_event': data}
        )
    
    @staticmethod
    def track_education_event(event_type, course_id=None, teacher_id=None, student_id=None, metadata=None):
        """Track educational events for learning analytics."""
        data = {
            'event_type': event_type,  # lesson_completed, assignment_submitted, etc.
            'course_id': course_id,
            'teacher_id': teacher_id,
            'student_id': student_id,
            'timestamp': timezone.now().isoformat(),
            'metadata': metadata or {}
        }
        
        analytics_logger.info(
            f"Education event: {event_type}",
            extra={'education_event': data}
        )
    
    @staticmethod
    def track_performance_metric(metric_name, value, tags=None):
        """Track performance and system metrics."""
        data = {
            'metric': metric_name,
            'value': value,
            'tags': tags or {},
            'timestamp': timezone.now().isoformat()
        }
        
        performance_logger.info(
            f"Performance metric: {metric_name}={value}",
            extra={'performance_metric': data}
        )


class BusinessIntelligence:
    """
    Business intelligence dashboard data aggregation.
    """
    
    @staticmethod
    def get_daily_metrics(date=None):
        """Get daily business metrics for dashboards."""
        if not date:
            date = timezone.now().date()
        
        # This would typically query the database for metrics
        # For now, return cached metrics or compute them
        cache_key = f"daily_metrics_{date}"
        metrics = cache.get(cache_key)
        
        if not metrics:
            metrics = BusinessIntelligence._compute_daily_metrics(date)
            cache.set(cache_key, metrics, 60 * 60)  # Cache for 1 hour
        
        return metrics
    
    @staticmethod
    def _compute_daily_metrics(date):
        """Compute daily metrics from database."""
        from education.models import Course, Enrollment, Payment, Lesson
        
        # Teacher metrics
        active_teachers = User.objects.filter(
            role='teacher',
            is_active=True,
            teacherprofile__courses__created_at__date=date
        ).distinct().count()
        
        # Student metrics
        active_students = User.objects.filter(
            role='student',
            is_active=True,
            studentprofile__enrollments__created_at__date=date
        ).distinct().count()
        
        # Course metrics
        new_courses = Course.objects.filter(created_at__date=date).count()
        active_courses = Course.objects.filter(status='active').count()
        
        # Financial metrics
        daily_revenue = Payment.objects.filter(
            created_at__date=date,
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        # Lesson metrics
        lessons_completed = Lesson.objects.filter(
            completed_at__date=date
        ).count()
        
        metrics = {
            'date': date.isoformat(),
            'teachers': {
                'active': active_teachers,
            },
            'students': {
                'active': active_students,
            },
            'courses': {
                'new': new_courses,
                'active': active_courses,
            },
            'revenue': {
                'daily': str(daily_revenue),
                'currency': 'EUR',
            },
            'lessons': {
                'completed': lessons_completed,
            }
        }
        
        # Track this as a business event
        AnalyticsTracker.track_business_event('daily_metrics_computed', metrics)
        
        return metrics
    
    @staticmethod
    def get_teacher_performance_metrics(teacher_id, days=30):
        """Get teacher performance metrics for the dashboard."""
        cache_key = f"teacher_metrics_{teacher_id}_{days}"
        metrics = cache.get(cache_key)
        
        if not metrics:
            metrics = BusinessIntelligence._compute_teacher_metrics(teacher_id, days)
            cache.set(cache_key, metrics, 60 * 30)  # Cache for 30 minutes
        
        return metrics
    
    @staticmethod
    def _compute_teacher_metrics(teacher_id, days):
        """Compute teacher performance metrics."""
        from education.models import Course, Enrollment, Payment, Lesson
        from django.db.models import Count, Sum, Avg
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        teacher_courses = Course.objects.filter(teacher_id=teacher_id)
        
        # Student metrics
        total_students = Enrollment.objects.filter(
            course__in=teacher_courses,
            is_active=True
        ).count()
        
        # Revenue metrics
        revenue = Payment.objects.filter(
            teacher_id=teacher_id,
            created_at__gte=start_date,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Lesson metrics
        lessons_data = Lesson.objects.filter(
            course__in=teacher_courses,
            created_at__gte=start_date
        ).aggregate(
            total=Count('id'),
            completed=Count('id', filter=models.Q(status='completed'))
        )
        
        metrics = {
            'teacher_id': teacher_id,
            'period_days': days,
            'students': {
                'total': total_students,
            },
            'revenue': {
                'total': str(revenue),
                'currency': 'EUR',
            },
            'lessons': {
                'total': lessons_data['total'],
                'completed': lessons_data['completed'],
                'completion_rate': lessons_data['completed'] / max(lessons_data['total'], 1) * 100
            }
        }
        
        return metrics


class AnalyticsMiddleware:
    """
    Middleware to automatically track user behavior and page views.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Track page view
        if request.user.is_authenticated:
            AnalyticsTracker.track_user_action(
                user=request.user,
                action='page_view',
                resource=request.path,
                metadata={
                    'method': request.method,
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
                    'ip_address': request.META.get('REMOTE_ADDR', ''),
                }
            )
        
        response = self.get_response(request)
        
        return response


# Convenience functions for common analytics events
def track_course_enrollment(student, course):
    """Track when a student enrolls in a course."""
    AnalyticsTracker.track_education_event(
        'course_enrollment',
        course_id=course.id,
        teacher_id=course.teacher.id,
        student_id=student.id,
        metadata={
            'course_title': course.title,
            'course_price': str(course.price_per_hour),
        }
    )

def track_lesson_completion(lesson, student):
    """Track when a student completes a lesson."""
    AnalyticsTracker.track_education_event(
        'lesson_completion',
        course_id=lesson.course.id,
        teacher_id=lesson.course.teacher.id,
        student_id=student.id,
        metadata={
            'lesson_title': lesson.title,
            'lesson_duration': lesson.duration_minutes,
        }
    )

def track_payment_received(payment):
    """Track when a payment is successfully received."""
    AnalyticsTracker.track_financial_event(
        'payment_received',
        amount=payment.amount,
        currency='EUR',
        user=payment.student.user if payment.student else None,
        metadata={
            'payment_method': payment.payment_method,
            'teacher_id': payment.teacher.id,
            'stripe_payment_id': payment.stripe_payment_intent_id,
        }
    )

def track_teacher_signup(teacher):
    """Track when a new teacher signs up."""
    AnalyticsTracker.track_business_event(
        'teacher_signup',
        {
            'teacher_id': teacher.id,
            'user_id': teacher.user.id,
            'subjects': [subject.name for subject in teacher.subjects.all()],
            'experience_years': teacher.experience_years,
        }
    )

def track_student_signup(student):
    """Track when a new student signs up."""
    AnalyticsTracker.track_business_event(
        'student_signup',
        {
            'student_id': student.id,
            'user_id': student.user.id,
            'grade_level': student.grade_level,
        }
    )