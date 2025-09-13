"""
Teacher Dashboard Service

Handles data aggregation and calculations for teacher dashboard API.
Optimized for performance with proper query optimization and caching.
"""

from datetime import timedelta
from decimal import Decimal
import logging
from typing import Any

from django.core.cache import cache
from django.db.models import Q, Sum
from django.utils import timezone

from accounts.models import (
    SchoolActivity,
    SchoolMembership,
    SchoolRole,
    TeacherProfile,
)
from finances.models import ClassSession, SessionStatus, TeacherPaymentEntry

logger = logging.getLogger(__name__)


class TeacherDashboardService:
    """Service class for teacher dashboard data aggregation."""

    def __init__(self, teacher_profile: TeacherProfile):
        self.teacher_profile = teacher_profile
        self.teacher_user = teacher_profile.user
        self.cache_timeout = 300  # 5 minutes cache

    def get_consolidated_dashboard_data(self) -> dict[str, Any]:
        """
        Get all consolidated dashboard data for a teacher.

        Returns:
            Dict containing all dashboard sections with optimized queries.
        """
        try:
            # Check cache first
            cache_key = f"teacher_dashboard_{self.teacher_profile.id}"
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info(f"Returning cached dashboard data for teacher {self.teacher_profile.id}")
                return cached_data  # type: ignore[no-any-return]

            # Gather all data with optimized queries
            dashboard_data = {
                "teacher_info": self._get_teacher_info(),
                "sessions": self._get_sessions_data(),
                "recent_activities": self._get_recent_activities(),
                "earnings": self._get_earnings_data(),
                "quick_stats": self._get_quick_stats(),
            }

            # Cache the result
            cache.set(cache_key, dashboard_data, self.cache_timeout)

            logger.info(f"Generated dashboard data for teacher {self.teacher_profile.id}")
            return dashboard_data

        except Exception as e:
            logger.error(f"Error generating dashboard data for teacher {self.teacher_profile.id}: {e}")
            # Return empty structure on error
            return self._get_empty_dashboard_structure()

    def _get_teacher_info(self) -> dict[str, Any]:
        """Get teacher profile information."""
        # Get schools where teacher is active
        schools = []
        memberships = SchoolMembership.objects.filter(
            user=self.teacher_user, role=SchoolRole.TEACHER, is_active=True
        ).select_related("school")

        for membership in memberships:
            schools.append(
                {"id": membership.school.id, "name": membership.school.name, "joined_at": membership.joined_at}  # type: ignore[attr-defined,attr-defined]
            )

        # Get courses taught
        courses_taught = []
        teacher_courses = self.teacher_profile.teacher_courses.filter(is_active=True).select_related("course")

        for teacher_course in teacher_courses:
            courses_taught.append(
                {
                    "id": teacher_course.course.id,  # type: ignore[attr-defined]
                    "name": teacher_course.course.name,  # type: ignore[attr-defined]
                    "code": teacher_course.course.code,  # type: ignore[attr-defined]
                    "hourly_rate": teacher_course.hourly_rate or self.teacher_profile.hourly_rate,
                }
            )

        return {
            "id": self.teacher_profile.id,
            "name": self.teacher_user.name,
            "email": self.teacher_user.email,
            "specialty": self.teacher_profile.specialty or "",
            "hourly_rate": self.teacher_profile.hourly_rate or Decimal("0.00"),
            "schools": schools,
            "courses_taught": courses_taught,
        }

    def _get_sessions_data(self) -> dict[str, list[dict[str, Any]]]:
        """Get sessions data organized by time periods."""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_start + timedelta(days=6)

        # Base queryset for teacher's sessions
        base_sessions = ClassSession.objects.filter(teacher=self.teacher_profile).prefetch_related("students")

        # Today's sessions
        today_sessions = base_sessions.filter(date=today).order_by("start_time")

        # Upcoming sessions (next 7 days, excluding today)
        upcoming_sessions = base_sessions.filter(
            date__gt=today, date__lte=today + timedelta(days=7), status=SessionStatus.SCHEDULED
        ).order_by("date", "start_time")

        # Recent completed sessions (last 7 days)
        recent_completed = base_sessions.filter(
            date__gte=today - timedelta(days=7), date__lt=today, status=SessionStatus.COMPLETED
        ).order_by("-date", "-start_time")[:10]

        def serialize_session(session):
            return {
                "id": session.id,
                "date": session.date,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "session_type": session.session_type,
                "grade_level": session.grade_level,
                "student_count": session.student_count,
                "student_names": [student.name for student in session.students.all()],
                "status": session.status,
                "notes": session.notes or "",
                "duration_hours": session.duration_hours,
            }

        return {
            "today": [serialize_session(session) for session in today_sessions],
            "upcoming": [serialize_session(session) for session in upcoming_sessions],
            "recent_completed": [serialize_session(session) for session in recent_completed],
        }

    def _get_recent_activities(self) -> list[dict[str, Any]]:
        """Get recent school activities related to this teacher."""
        # Get schools where teacher is active
        school_ids = SchoolMembership.objects.filter(
            user=self.teacher_user, role=SchoolRole.TEACHER, is_active=True
        ).values_list("school_id", flat=True)

        # Get recent activities from these schools
        activities = (
            SchoolActivity.objects.filter(
                Q(school_id__in=school_ids) & (Q(actor=self.teacher_user) | Q(target_user=self.teacher_user))
            )
            .select_related("actor", "target_user", "school")
            .order_by("-timestamp")[:10]
        )

        activities_data = []
        for activity in activities:
            activities_data.append(
                {
                    "id": str(activity.id),
                    "activity_type": activity.activity_type,
                    "description": activity.description,
                    "timestamp": activity.timestamp,
                    "actor_name": activity.actor.name if activity.actor else None,
                    "school_name": activity.school.name,
                }
            )

        return activities_data

    def _get_earnings_data(self) -> dict[str, Any]:
        """Calculate earnings data."""
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)

        # Current month earnings
        current_month_total = TeacherPaymentEntry.objects.filter(
            teacher=self.teacher_profile, session__date__gte=current_month_start, session__date__lte=today
        ).aggregate(total=Sum("amount_earned"))["total"] or Decimal("0.00")

        # Last month earnings
        last_month_total = TeacherPaymentEntry.objects.filter(
            teacher=self.teacher_profile, session__date__gte=last_month_start, session__date__lte=last_month_end
        ).aggregate(total=Sum("amount_earned"))["total"] or Decimal("0.00")

        # Pending amount (completed sessions without payment entries)
        completed_sessions_without_payment = ClassSession.objects.filter(
            teacher=self.teacher_profile, status=SessionStatus.COMPLETED, payment_entry__isnull=True
        )

        pending_amount = Decimal("0.00")
        for session in completed_sessions_without_payment:
            # Estimate pending amount based on duration and hourly rate
            rate = self.teacher_profile.hourly_rate or Decimal("0.00")
            pending_amount += session.duration_hours * rate

        # Total hours taught (all time)
        total_hours = TeacherPaymentEntry.objects.filter(teacher=self.teacher_profile).aggregate(
            total_hours=Sum("hours_taught")
        )["total_hours"] or Decimal("0.00")

        # Recent payments (last 5)
        recent_payments = []
        recent_payment_entries = (
            TeacherPaymentEntry.objects.filter(teacher=self.teacher_profile)
            .select_related("session")
            .order_by("-created_at")[:5]
        )

        for payment in recent_payment_entries:
            recent_payments.append(
                {
                    "id": payment.id,
                    "amount": payment.amount_earned,
                    "date": payment.session.date,
                    "session_info": f"{payment.session.session_type.title()} - {payment.session.grade_level}",
                    "hours": payment.hours_taught,
                }
            )

        return {
            "current_month_total": current_month_total,
            "last_month_total": last_month_total,
            "pending_amount": pending_amount,
            "total_hours_taught": total_hours,
            "recent_payments": recent_payments,
        }

    def _get_quick_stats(self) -> dict[str, Any]:
        """Get quick stats for dashboard widgets."""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Total students (count unique students from sessions)
        unique_students = (
            ClassSession.objects.filter(teacher=self.teacher_profile, status=SessionStatus.COMPLETED)
            .values("students")
            .distinct()
            .count()
        )

        # Sessions today
        sessions_today = ClassSession.objects.filter(teacher=self.teacher_profile, date=today).count()

        # Sessions this week
        sessions_this_week = ClassSession.objects.filter(
            teacher=self.teacher_profile, date__gte=week_start, date__lte=week_end
        ).count()

        return {
            "total_students": unique_students,
            "sessions_today": sessions_today,
            "sessions_this_week": sessions_this_week,
        }

    def _get_empty_dashboard_structure(self) -> dict[str, Any]:
        """Return empty dashboard structure for error cases."""
        return {
            "teacher_info": {
                "id": self.teacher_profile.id,
                "name": self.teacher_user.name,
                "email": self.teacher_user.email,
                "specialty": "",
                "hourly_rate": Decimal("0.00"),
                "schools": [],
                "courses_taught": [],
            },
            "sessions": {"today": [], "upcoming": [], "recent_completed": []},
            "recent_activities": [],
            "earnings": {
                "current_month_total": Decimal("0.00"),
                "last_month_total": Decimal("0.00"),
                "pending_amount": Decimal("0.00"),
                "total_hours_taught": Decimal("0.00"),
                "recent_payments": [],
            },
            "quick_stats": {
                "total_students": 0,
                "sessions_today": 0,
                "sessions_this_week": 0,
            },
        }

    @classmethod
    def invalidate_cache(cls, teacher_profile_id: int) -> None:
        """Invalidate cached dashboard data for a teacher."""
        cache_key = f"teacher_dashboard_{teacher_profile_id}"
        cache.delete(cache_key)
        logger.info(f"Invalidated dashboard cache for teacher {teacher_profile_id}")

    @classmethod
    def warm_cache(cls, teacher_profile: TeacherProfile) -> None:
        """Warm up the cache for a teacher's dashboard."""
        service = cls(teacher_profile)
        service.get_consolidated_dashboard_data()
        logger.info(f"Warmed dashboard cache for teacher {teacher_profile.id}")
