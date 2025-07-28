"""
Service for calculating school dashboard metrics.
Implements efficient queries with proper caching.
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Any
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.core.cache import cache
from accounts.models import School, SchoolMembership, SchoolRole, SchoolInvitation
from finances.models import ClassSession


class SchoolMetricsService:
    """Service for calculating school dashboard metrics"""
    
    CACHE_TTL = 300  # 5 minutes
    
    def __init__(self, school: School):
        self.school = school
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get complete metrics for the school with caching"""
        cache_key = f'school_metrics_{self.school.id}'
        metrics = cache.get(cache_key)
        
        if metrics is None:
            metrics = self._calculate_metrics()
            cache.set(cache_key, metrics, self.CACHE_TTL)
            
        return metrics
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate all metrics for the school"""
        return {
            'student_count': self._get_student_metrics(),
            'teacher_count': self._get_teacher_metrics(),
            'class_metrics': self._get_class_metrics(),
            'engagement_metrics': self._get_engagement_metrics()
        }
    
    def _get_student_metrics(self) -> Dict[str, Any]:
        """Calculate student-related metrics"""
        memberships = SchoolMembership.objects.filter(
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        total = memberships.count()
        active = memberships.filter(is_active=True).count()
        inactive = total - active
        
        # Calculate trends
        trends = self._calculate_membership_trends(SchoolRole.STUDENT)
        
        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'trend': trends
        }
    
    def _get_teacher_metrics(self) -> Dict[str, Any]:
        """Calculate teacher-related metrics"""
        memberships = SchoolMembership.objects.filter(
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        total = memberships.count()
        active = memberships.filter(is_active=True).count()
        inactive = total - active
        
        # Calculate trends
        trends = self._calculate_membership_trends(SchoolRole.TEACHER)
        
        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'trend': trends
        }
    
    def _get_class_metrics(self) -> Dict[str, Any]:
        """Calculate class session metrics"""
        today = timezone.now().date()
        
        # Get all sessions for this school
        sessions = ClassSession.objects.filter(school=self.school)
        
        # Today's metrics
        today_sessions = sessions.filter(date=today)
        completed_today = today_sessions.filter(status='completed').count()
        scheduled_today = today_sessions.filter(status='scheduled').count()
        active_classes = sessions.filter(status='scheduled').count()
        
        # Calculate completion rate
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(status='completed').count()
        completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0.0
        
        # Calculate trends
        trends = self._calculate_class_trends()
        
        return {
            'active_classes': active_classes,
            'completed_today': completed_today,
            'scheduled_today': scheduled_today,
            'completion_rate': round(completion_rate, 2),
            'trend': trends
        }
    
    def _get_engagement_metrics(self) -> Dict[str, Any]:
        """Calculate engagement metrics based on invitations"""
        invitations = SchoolInvitation.objects.filter(school=self.school)
        
        invitations_sent = invitations.count()
        invitations_accepted = invitations.filter(is_accepted=True).count()
        acceptance_rate = (invitations_accepted / invitations_sent * 100) if invitations_sent > 0 else 0.0
        
        # Calculate average time to accept
        accepted_invitations = invitations.filter(is_accepted=True)
        if accepted_invitations.exists():
            avg_time = self._calculate_avg_time_to_accept(accepted_invitations)
        else:
            avg_time = "00:00:00"
        
        return {
            'invitations_sent': invitations_sent,
            'invitations_accepted': invitations_accepted,
            'acceptance_rate': round(acceptance_rate, 2),
            'avg_time_to_accept': avg_time
        }
    
    def _calculate_membership_trends(self, role: SchoolRole) -> Dict[str, List[int]]:
        """Calculate membership trends for a specific role"""
        now = timezone.now()
        
        # Daily trend (last 7 days)
        daily = []
        for i in range(7):
            date = (now - timedelta(days=i)).date()
            count = SchoolMembership.objects.filter(
                school=self.school,
                role=role,
                joined_at__date=date
            ).count()
            daily.append(count)
        daily.reverse()
        
        # Weekly trend (last 4 weeks)
        weekly = []
        for i in range(4):
            start_date = (now - timedelta(weeks=i+1)).date()
            end_date = (now - timedelta(weeks=i)).date()
            count = SchoolMembership.objects.filter(
                school=self.school,
                role=role,
                joined_at__date__range=[start_date, end_date]
            ).count()
            weekly.append(count)
        weekly.reverse()
        
        # Monthly trend (last 6 months) - using proper calendar arithmetic
        monthly = []
        for i in range(6):
            # Calculate start and end of month using proper calendar arithmetic
            current_month = now.replace(day=1) - relativedelta(months=i)
            start_date = current_month.replace(day=1)
            # Get last day of the month
            next_month = start_date + relativedelta(months=1)
            end_date = next_month - timedelta(days=1)
            
            count = SchoolMembership.objects.filter(
                school=self.school,
                role=role,
                joined_at__date__range=[start_date.date(), end_date.date()]
            ).count()
            monthly.append(count)
        monthly.reverse()
        
        return {
            'daily': daily,
            'weekly': weekly,
            'monthly': monthly
        }
    
    def _calculate_class_trends(self) -> Dict[str, List[int]]:
        """Calculate class session trends"""
        now = timezone.now()
        
        # Daily trend (last 7 days)
        daily = []
        for i in range(7):
            date = (now - timedelta(days=i)).date()
            count = ClassSession.objects.filter(
                school=self.school,
                date=date,
                status='completed'
            ).count()
            daily.append(count)
        daily.reverse()
        
        # Weekly trend (last 4 weeks)
        weekly = []
        for i in range(4):
            start_date = (now - timedelta(weeks=i+1)).date()
            end_date = (now - timedelta(weeks=i)).date()
            count = ClassSession.objects.filter(
                school=self.school,
                date__range=[start_date, end_date],
                status='completed'
            ).count()
            weekly.append(count)
        weekly.reverse()
        
        return {
            'daily': daily,
            'weekly': weekly
        }
    
    def _calculate_avg_time_to_accept(self, accepted_invitations) -> str:
        """Calculate average time to accept invitations"""
        # This would need to track when invitations were accepted
        # For now, return a placeholder
        # In a real implementation, you'd need to add an 'accepted_at' field
        return "24:00:00"  # Placeholder
    
    @classmethod
    def invalidate_cache(cls, school_id: int):
        """Invalidate cached metrics for a school"""
        cache_key = f'school_metrics_{school_id}'
        cache.delete(cache_key)


class SchoolActivityService:
    """Service for managing school activities"""
    
    @classmethod
    def create_activity(cls, school, activity_type, actor, description, **kwargs):
        """Create a new school activity"""
        from accounts.models import SchoolActivity
        
        return SchoolActivity.objects.create(
            school=school,
            activity_type=activity_type,
            actor=actor,
            description=description,
            **kwargs
        )
    
    @classmethod
    def get_activity_feed(cls, school, page_size=20, filters=None):
        """Get paginated activity feed for a school"""
        from accounts.models import SchoolActivity
        
        activities = SchoolActivity.objects.filter(school=school).select_related(
            'actor', 'target_user', 'target_class__teacher'
        ).prefetch_related(
            'target_invitation__invited_by'
        )
        
        # Apply filters if provided
        if filters:
            if 'activity_types' in filters:
                activity_types = filters['activity_types'].split(',')
                activities = activities.filter(activity_type__in=activity_types)
            
            if 'date_from' in filters:
                activities = activities.filter(timestamp__gte=filters['date_from'])
            
            if 'date_to' in filters:
                activities = activities.filter(timestamp__lte=filters['date_to'])
        
        return activities[:page_size]