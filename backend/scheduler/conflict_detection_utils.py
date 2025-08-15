"""
Conflict Detection Utilities - GitHub Issue #152

This module provides consolidated utilities for detecting time conflicts
to eliminate duplicate code throughout the scheduling system.
"""

from datetime import time
from typing import Optional, Any

from django.db.models import Q

from accounts.models import CustomUser, School, TeacherProfile

from .models import ClassSchedule, ClassStatus, TeacherUnavailability


class TimeOverlapDetector:
    """Utility class for detecting time overlaps between slots."""

    @staticmethod
    def has_time_overlap(start1: time, end1: time, start2: time, end2: time) -> bool:
        """
        Check if two time periods overlap.
        Returns True if there is any overlap, False otherwise.
        """
        # Two time periods DON'T overlap if:
        # - First period ends before second starts (end1 <= start2), OR
        # - Second period ends before first starts (end2 <= start1)
        # So they DO overlap if NOT (end1 <= start2 OR end2 <= start1)
        return not (end1 <= start2 or end2 <= start1)


class ClassScheduleConflictDetector:
    """Consolidated class schedule conflict detection."""

    def __init__(self):
        self.overlap_detector = TimeOverlapDetector()

    def get_conflicting_classes_query(
        self,
        teacher: Optional[TeacherProfile] = None,
        student: Optional[CustomUser] = None,
        school: Optional[School] = None,
        date=None,
        start_time: time | None = None,
        end_time: time | None = None,
        exclude_statuses: list[str] | None = None,
    ):
        """
        Build a query for conflicting class schedules.

        Args:
            teacher: Teacher to check conflicts for
            student: Student to check conflicts for
            school: School to filter by
            date: Date to check conflicts on
            start_time: Start time of the period to check
            end_time: End time of the period to check
            exclude_statuses: List of statuses to exclude from conflict check

        Returns:
            QuerySet of conflicting ClassSchedule objects
        """
        query = ClassSchedule.objects.all()

        # Add base filters
        if teacher:
            query = query.filter(teacher=teacher)

        if student:
            # Student can be either the main student or an additional participant
            query = query.filter(Q(student=student) | Q(additional_students=student))

        if school:
            query = query.filter(school=school)

        if date:
            query = query.filter(scheduled_date=date)

        # Only check active statuses by default
        if exclude_statuses is None:
            exclude_statuses = [ClassStatus.CANCELLED, ClassStatus.COMPLETED, ClassStatus.NO_SHOW, ClassStatus.REJECTED]

        # Use only the active statuses for conflict detection
        active_statuses = [ClassStatus.SCHEDULED, ClassStatus.CONFIRMED]
        if exclude_statuses:
            active_statuses = [status for status in active_statuses if status not in exclude_statuses]
        query = query.filter(status__in=active_statuses)

        # Add time overlap exclusion if times are provided
        if start_time and end_time:
            query = query.exclude(Q(end_time__lte=start_time) | Q(start_time__gte=end_time))

        return query

    def has_teacher_conflict(
        self, teacher: TeacherProfile, school: School, date, start_time: time, end_time: time
    ) -> bool:
        """Check if teacher has conflicting classes."""
        return self.get_conflicting_classes_query(
            teacher=teacher, school=school, date=date, start_time=start_time, end_time=end_time
        ).exists()

    def has_student_conflict(self, student: CustomUser, school: School, date, start_time: time, end_time: time) -> bool:
        """Check if student has conflicting classes."""
        return self.get_conflicting_classes_query(
            student=student, school=school, date=date, start_time=start_time, end_time=end_time
        ).exists()

    def get_teacher_conflict_details(
        self, teacher: TeacherProfile, school: School, date, start_time: time, end_time: time
    ) -> dict[str, Any] | None:
        """Get details of conflicting teacher class."""
        conflicting_class = self.get_conflicting_classes_query(
            teacher=teacher, school=school, date=date, start_time=start_time, end_time=end_time
        ).first()

        if conflicting_class:
            return {
                "class_id": conflicting_class.id,
                "title": conflicting_class.title,
                "existing_start_time": conflicting_class.start_time,
                "existing_end_time": conflicting_class.end_time,
                "student_name": conflicting_class.student.name,
            }

        return None


class UnavailabilityConflictDetector:
    """Consolidated unavailability conflict detection."""

    def __init__(self):
        self.overlap_detector = TimeOverlapDetector()

    def has_unavailability_conflict(
        self, teacher: TeacherProfile, school: School, date, start_time: time, end_time: time
    ) -> bool:
        """Check if booking conflicts with teacher unavailability."""
        unavailabilities = TeacherUnavailability.objects.filter(teacher=teacher, school=school, date=date)

        for unavailability in unavailabilities:
            if unavailability.is_all_day:
                return True

            # Check for time overlap using consolidated logic
            if (
                unavailability.start_time
                and unavailability.end_time
                and self.overlap_detector.has_time_overlap(
                    start_time, end_time, unavailability.start_time, unavailability.end_time
                )
            ):
                return True

        return False

    def get_unavailability_periods(self, teacher: TeacherProfile, school: School, date) -> list[dict[str, Any]]:
        """Get all unavailability periods for a date."""
        unavailabilities = TeacherUnavailability.objects.filter(teacher=teacher, school=school, date=date)

        periods = []
        for unavailability in unavailabilities:
            period = {
                "reason": unavailability.reason,
                "is_all_day": unavailability.is_all_day,
            }
            if not unavailability.is_all_day:
                period["start_time"] = unavailability.start_time
                period["end_time"] = unavailability.end_time
            periods.append(period)

        return periods


class ConflictDetectionOrchestrator:
    """Main orchestrator for all conflict detection."""

    def __init__(self):
        self.class_conflict_detector = ClassScheduleConflictDetector()
        self.unavailability_detector = UnavailabilityConflictDetector()
        self.overlap_detector = TimeOverlapDetector()

    def check_all_conflicts(
        self, teacher: TeacherProfile, student: CustomUser, school: School, date, start_time: time, end_time: time
    ) -> dict[str, Any]:
        """
        Comprehensive conflict check for booking validation.

        Returns:
            Dict with conflict information including:
            - has_conflicts: bool
            - teacher_conflicts: List[Dict]
            - student_conflicts: List[Dict]
            - unavailability_conflicts: List[Dict]
        """
        result = {
            "has_conflicts": False,
            "teacher_conflicts": [],
            "student_conflicts": [],
            "unavailability_conflicts": [],
        }

        # Check teacher class conflicts
        if self.class_conflict_detector.has_teacher_conflict(teacher, school, date, start_time, end_time):
            result["teacher_conflicts"] = ["Teacher has conflicting class"]
            result["has_conflicts"] = True

        # Check student conflicts
        if self.class_conflict_detector.has_student_conflict(student, school, date, start_time, end_time):
            result["student_conflicts"] = ["Student has conflicting class"]
            result["has_conflicts"] = True

        # Check unavailability conflicts
        if self.unavailability_detector.has_unavailability_conflict(teacher, school, date, start_time, end_time):
            unavailability_periods = self.unavailability_detector.get_unavailability_periods(teacher, school, date)
            result["unavailability_conflicts"] = unavailability_periods
            result["has_conflicts"] = True

        return result

    def has_any_conflicts(
        self, teacher: TeacherProfile, student: CustomUser, school: School, date, start_time: time, end_time: time
    ) -> bool:
        """Quick check if there are any conflicts (optimized for performance)."""
        # Check teacher conflicts first (usually fastest)
        if self.class_conflict_detector.has_teacher_conflict(teacher, school, date, start_time, end_time):
            return True

        # Check student conflicts
        if self.class_conflict_detector.has_student_conflict(student, school, date, start_time, end_time):
            return True

        # Check unavailability conflicts
        return bool(
            self.unavailability_detector.has_unavailability_conflict(teacher, school, date, start_time, end_time)
        )
