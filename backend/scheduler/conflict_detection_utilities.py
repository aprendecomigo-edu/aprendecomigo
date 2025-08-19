"""
Conflict Detection Utilities - GitHub Issue #152

This module contains specific conflict detection utility functions that support
the enhanced scheduling rules and conflict management.

These utilities focus on PURE UTILITY FUNCTIONS with minimal external dependencies
and handle edge cases, boundary conditions, and complex scenarios.

Utilities:
- detect_student_conflicts() - Student double-booking detection
- detect_teacher_conflicts() - Teacher conflict detection with buffer times
- detect_time_overlap() - Time overlap calculation utilities
- handle_day_boundary_cases() - Classes spanning day boundaries
- calculate_buffer_impact() - Buffer time calculations
- find_available_gaps() - Find gaps in schedules
- validate_time_boundaries() - Time boundary validation
"""

from datetime import date, datetime, time, timedelta
from typing import Any

from django.db.models import Q


def detect_student_conflicts(
    student_id: int,
    school_id: int,
    booking_date: date,
    start_time: time,
    end_time: time,
    exclude_class_id: int | None = None,
) -> dict[str, Any] | None:
    """
    Pure utility function to detect student scheduling conflicts.
    Returns conflict details or None if no conflicts found.
    """

    from .models import ClassSchedule, ClassStatus

    # Find conflicting classes for this student
    conflicting_classes = ClassSchedule.objects.filter(
        Q(student_id=student_id) | Q(additional_students=student_id),
        scheduled_date=booking_date,
        status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
    ).exclude(Q(end_time__lte=start_time) | Q(start_time__gte=end_time))

    if exclude_class_id:
        conflicting_classes = conflicting_classes.exclude(id=exclude_class_id)

    # Check conflicts across ALL schools
    all_school_conflicts = (
        ClassSchedule.objects.filter(
            Q(student_id=student_id) | Q(additional_students=student_id),
            scheduled_date=booking_date,
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
        )
        .exclude(Q(end_time__lte=start_time) | Q(start_time__gte=end_time))
        .exclude(school_id=school_id)
    )

    if exclude_class_id:
        all_school_conflicts = all_school_conflicts.exclude(id=exclude_class_id)

    # Return cross-school conflict first (higher priority)
    cross_school_conflict = all_school_conflicts.select_related("teacher__user", "school", "student").first()
    if cross_school_conflict:
        return {
            "has_conflict": True,
            "conflict_type": "cross_school",
            "conflicting_class": {
                "id": cross_school_conflict.id,
                "title": cross_school_conflict.title,
                "start_time": cross_school_conflict.start_time,
                "end_time": cross_school_conflict.end_time,
                "teacher_name": cross_school_conflict.teacher.user.name,
                "school_name": cross_school_conflict.school.name,
                "date": cross_school_conflict.scheduled_date,
            },
        }

    # Check same-school conflicts
    same_school_conflict = conflicting_classes.select_related("teacher__user", "student").first()
    if same_school_conflict:
        conflict_type = "group_participation" if same_school_conflict.class_type == "group" else "double_booking"

        return {
            "has_conflict": True,
            "conflict_type": conflict_type,
            "conflicting_class": {
                "id": same_school_conflict.id,
                "title": same_school_conflict.title,
                "start_time": same_school_conflict.start_time,
                "end_time": same_school_conflict.end_time,
                "teacher_name": same_school_conflict.teacher.user.name,
                "class_type": same_school_conflict.class_type,
                "date": same_school_conflict.scheduled_date,
            },
        }

    return None


def detect_teacher_conflicts(
    teacher_id: int,
    school_id: int,
    booking_date: date,
    start_time: time,
    end_time: time,
    buffer_minutes: int = 15,
    exclude_class_id: int | None = None,
) -> dict[str, Any] | None:
    """
    Pure utility function to detect teacher scheduling conflicts including buffer time.
    Returns conflict details or None if no conflicts found.
    """
    from .models import ClassSchedule, ClassStatus

    if buffer_minutes == 0:
        # Simple time overlap check
        conflicting_classes = ClassSchedule.objects.filter(
            teacher_id=teacher_id,
            school_id=school_id,
            scheduled_date=booking_date,
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
        ).exclude(Q(end_time__lte=start_time) | Q(start_time__gte=end_time))

        if exclude_class_id:
            conflicting_classes = conflicting_classes.exclude(id=exclude_class_id)

        conflict = conflicting_classes.select_related("student", "teacher__user").first()
        if conflict:
            return {
                "has_conflict": True,
                "conflict_type": "time_overlap",
                "buffer_minutes": 0,
                "conflicting_class": {
                    "id": conflict.id,
                    "title": conflict.title,
                    "start_time": conflict.start_time,
                    "end_time": conflict.end_time,
                    "student_name": conflict.student.name,
                    "date": conflict.scheduled_date,
                },
            }
        return None

    # Buffer time conflict detection
    return _detect_buffer_conflicts(
        teacher_id, school_id, booking_date, start_time, end_time, buffer_minutes, exclude_class_id
    )


def _detect_buffer_conflicts(
    teacher_id: int,
    school_id: int,
    booking_date: date,
    start_time: time,
    end_time: time,
    buffer_minutes: int,
    exclude_class_id: int | None = None,
) -> dict[str, Any] | None:
    """Detect conflicts considering buffer time requirements."""
    from .models import ClassSchedule, ClassStatus

    # Calculate buffer-adjusted times
    start_datetime = datetime.combine(booking_date, start_time)
    end_datetime = datetime.combine(booking_date, end_time)

    buffer_start_datetime = start_datetime - timedelta(minutes=buffer_minutes)
    buffer_end_datetime = end_datetime + timedelta(minutes=buffer_minutes)

    # Handle day boundary cases
    search_dates = [booking_date]
    if buffer_start_datetime.date() < booking_date:
        search_dates.append(booking_date - timedelta(days=1))
    if buffer_end_datetime.date() > booking_date:
        search_dates.append(booking_date + timedelta(days=1))

    conflicts = []
    for search_date in search_dates:
        date_classes = ClassSchedule.objects.filter(
            teacher_id=teacher_id,
            school_id=school_id,
            scheduled_date=search_date,
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
        ).select_related("student")

        if exclude_class_id:
            date_classes = date_classes.exclude(id=exclude_class_id)

        for existing_class in date_classes:
            if _has_buffer_time_conflict(
                booking_date,
                start_time,
                end_time,
                existing_class.scheduled_date,
                existing_class.start_time,
                existing_class.end_time,
                buffer_minutes,
            ):
                conflicts.append(existing_class)

    if conflicts:
        conflict = conflicts[0]
        earliest_time = _calculate_earliest_available_after_class(
            conflict.scheduled_date, conflict.end_time, buffer_minutes
        )

        return {
            "has_conflict": True,
            "conflict_type": "buffer_time",
            "buffer_minutes": buffer_minutes,
            "earliest_available_time": earliest_time,
            "conflicting_class": {
                "id": conflict.id,
                "title": conflict.title,
                "start_time": conflict.start_time,
                "end_time": conflict.end_time,
                "student_name": conflict.student.name,
                "date": conflict.scheduled_date,
            },
        }

    return None


def _has_buffer_time_conflict(
    date1: date, start1: time, end1: time, date2: date, start2: time, end2: time, buffer_minutes: int
) -> bool:
    """Check if two classes conflict considering buffer time."""
    # Convert to datetimes for precise calculation
    datetime1_start = datetime.combine(date1, start1)
    datetime1_end = datetime.combine(date1, end1)
    datetime2_start = datetime.combine(date2, start2)
    datetime2_end = datetime.combine(date2, end2)

    # Add buffer to the first class
    buffered1_start = datetime1_start - timedelta(minutes=buffer_minutes)
    buffered1_end = datetime1_end + timedelta(minutes=buffer_minutes)

    # Check if the buffered class overlaps with the existing class
    return not (buffered1_end <= datetime2_start or buffered1_start >= datetime2_end)


def _calculate_earliest_available_after_class(conflict_date: date, conflict_end_time: time, buffer_minutes: int) -> str:
    """Calculate earliest available time after a conflicting class."""
    conflict_end_datetime = datetime.combine(conflict_date, conflict_end_time)
    earliest_datetime = conflict_end_datetime + timedelta(minutes=buffer_minutes)
    return earliest_datetime.strftime("%H:%M")


def detect_time_overlap(
    start1: time, end1: time, start2: time, end2: time, return_details: bool = False
) -> bool | dict[str, Any]:
    """
    Detect if two time ranges overlap within the same day.

    Args:
        start1, end1: First time range
        start2, end2: Second time range
        return_details: If True, return detailed overlap information

    Returns:
        bool or dict with overlap details
    """
    # Basic overlap check: two ranges overlap if neither ends before the other starts
    has_overlap = not (end1 <= start2 or start1 >= end2)

    if not return_details:
        return has_overlap

    # Calculate overlap details
    result: dict[str, Any] = {"has_overlap": has_overlap}

    if has_overlap:
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        # Calculate overlap duration in minutes
        overlap_duration = (
            datetime.combine(date.today(), overlap_end) - datetime.combine(date.today(), overlap_start)
        ).total_seconds() / 60

        result.update(
            {"overlap_start": overlap_start, "overlap_end": overlap_end, "overlap_minutes": int(overlap_duration)}
        )
    else:
        result.update({"overlap_start": None, "overlap_end": None, "overlap_minutes": 0})

    return result


def handle_day_boundary_cases(booking_date: date, start_time: time, end_time: time) -> dict[str, Any]:
    """
    Handle classes that span day boundaries (e.g., 23:30 - 01:00).

    Args:
        booking_date: The date the class starts
        start_time: Class start time
        end_time: Class end time

    Returns:
        Dictionary with boundary information
    """
    crosses_midnight = start_time > end_time

    if crosses_midnight:
        # Class spans midnight
        end_date = booking_date + timedelta(days=1)
        start_datetime = datetime.combine(booking_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)
    else:
        # Normal same-day class
        end_date = booking_date
        start_datetime = datetime.combine(booking_date, start_time)
        end_datetime = datetime.combine(booking_date, end_time)

    # Calculate total duration
    total_seconds = (end_datetime - start_datetime).total_seconds()
    total_minutes = int(total_seconds / 60)

    return {
        "crosses_midnight": crosses_midnight,
        "start_date": booking_date,
        "end_date": end_date,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "total_minutes": total_minutes,
        "duration_hours": total_minutes / 60,
    }


def calculate_buffer_impact(existing_classes: list[dict], buffer_minutes: int) -> dict[str, Any]:
    """
    Calculate the impact of buffer time on a list of existing classes.

    Args:
        existing_classes: List of dicts with 'start_time', 'end_time', 'date'
        buffer_minutes: Buffer time to apply

    Returns:
        Dictionary with buffer impact analysis
    """
    if not existing_classes or buffer_minutes <= 0:
        return {"blocked_periods": [], "total_blocked_minutes": 0, "affects_classes": False}

    blocked_periods = []

    for cls in existing_classes:
        cls_date = cls.get("date", date.today())
        cls_start = cls["start_time"]
        cls_end = cls["end_time"]

        # Calculate buffered period
        start_datetime = datetime.combine(cls_date, cls_start)
        end_datetime = datetime.combine(cls_date, cls_end)

        buffer_start = start_datetime - timedelta(minutes=buffer_minutes)
        buffer_end = end_datetime + timedelta(minutes=buffer_minutes)

        blocked_periods.append(
            {
                "original_start": cls_start,
                "original_end": cls_end,
                "buffered_start": buffer_start.time(),
                "buffered_end": buffer_end.time(),
                "buffered_start_date": buffer_start.date(),
                "buffered_end_date": buffer_end.date(),
                "crosses_day_boundary": buffer_start.date() != buffer_end.date(),
                "total_blocked_minutes": int((buffer_end - buffer_start).total_seconds() / 60),
            }
        )

    total_blocked = sum(period["total_blocked_minutes"] for period in blocked_periods)

    return {
        "blocked_periods": blocked_periods,
        "total_blocked_minutes": total_blocked,
        "affects_classes": len(blocked_periods) > 0,
        "buffer_minutes_applied": buffer_minutes,
    }


def find_available_gaps(
    schedule: list[dict],
    target_duration_minutes: int,
    working_start: time = time(8, 0),
    working_end: time = time(18, 0),
    buffer_minutes: int = 0,
) -> list[dict[str, Any]]:
    """
    Find available gaps in a schedule that can fit a class of target duration.

    Args:
        schedule: List of scheduled classes with 'start_time' and 'end_time'
        target_duration_minutes: Required duration for new class
        working_start: Start of working hours
        working_end: End of working hours
        buffer_minutes: Required buffer time around existing classes

    Returns:
        List of available time slots
    """
    if not schedule:
        # No existing classes, entire working day available
        return [
            {
                "start_time": working_start,
                "end_time": working_end,
                "duration_minutes": int(
                    (
                        datetime.combine(date.today(), working_end) - datetime.combine(date.today(), working_start)
                    ).total_seconds()
                    / 60
                ),
            }
        ]

    # Sort schedule by start time
    sorted_schedule = sorted(schedule, key=lambda x: x["start_time"])

    gaps = []
    current_time = working_start

    for cls in sorted_schedule:
        cls_start = cls["start_time"]
        cls_end = cls["end_time"]

        # Apply buffer time
        if buffer_minutes > 0:
            buffered_start = (datetime.combine(date.today(), cls_start) - timedelta(minutes=buffer_minutes)).time()

            buffered_end = (datetime.combine(date.today(), cls_end) + timedelta(minutes=buffer_minutes)).time()
        else:
            buffered_start = cls_start
            buffered_end = cls_end

        # Check if there's a gap before this class
        if current_time < buffered_start:
            gap_duration = (
                datetime.combine(date.today(), buffered_start) - datetime.combine(date.today(), current_time)
            ).total_seconds() / 60

            if gap_duration >= target_duration_minutes:
                gaps.append(
                    {
                        "start_time": current_time,
                        "end_time": buffered_start,
                        "duration_minutes": int(gap_duration),
                        "can_fit_target": True,
                    }
                )

        # Update current time to end of this class (including buffer)
        current_time = max(current_time, buffered_end)

    # Check for gap after last class until end of working hours
    if current_time < working_end:
        final_gap_duration = (
            datetime.combine(date.today(), working_end) - datetime.combine(date.today(), current_time)
        ).total_seconds() / 60

        if final_gap_duration >= target_duration_minutes:
            gaps.append(
                {
                    "start_time": current_time,
                    "end_time": working_end,
                    "duration_minutes": int(final_gap_duration),
                    "can_fit_target": True,
                }
            )

    return gaps


def validate_time_boundaries(start_time: time, end_time: time, max_duration_minutes: int = 480) -> dict[str, Any]:
    """
    Validate time boundaries for class scheduling.

    Args:
        start_time: Proposed start time
        end_time: Proposed end time
        max_duration_minutes: Maximum allowed duration (default 8 hours)

    Returns:
        Dictionary with validation results
    """
    errors = []
    warnings = []

    # Check basic time order
    crosses_midnight = start_time > end_time

    if crosses_midnight:
        warnings.append("Class spans midnight - ensure this is intentional")

        # Calculate duration across midnight
        start_datetime = datetime.combine(date.today(), start_time)
        end_datetime = datetime.combine(date.today() + timedelta(days=1), end_time)
        duration_minutes = (end_datetime - start_datetime).total_seconds() / 60
    else:
        # Normal same-day duration
        duration_minutes = (
            datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)
        ).total_seconds() / 60

    # Validate duration
    if duration_minutes <= 0:
        errors.append("Class duration must be positive")
    elif duration_minutes > max_duration_minutes:
        errors.append(f"Class duration ({int(duration_minutes)} min) exceeds maximum ({max_duration_minutes} min)")
    elif duration_minutes < 15:
        warnings.append("Very short class duration (less than 15 minutes)")

    # Check for unusual times
    if start_time < time(6, 0) or start_time > time(23, 0):
        warnings.append("Unusual start time - outside typical hours (06:00-23:00)")

    if end_time < time(6, 0) or end_time > time(23, 59):
        warnings.append("Unusual end time - outside typical hours (06:00-23:59)")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "crosses_midnight": crosses_midnight,
        "duration_minutes": int(duration_minutes),
        "duration_hours": duration_minutes / 60,
    }
