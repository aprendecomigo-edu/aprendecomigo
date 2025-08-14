"""
Scheduling Rules & Conflict Management Services - GitHub Issue #152

This module contains all the business logic services required for advanced scheduling rules
and conflict management including:

1. SchedulingRulesService - Main orchestrator for all scheduling rules
2. SchedulingConfigurationService - Configuration management and rule resolution
3. ConflictDetectionService - Enhanced conflict detection utilities
4. AvailabilityCalculationService - Available slots with buffer/notice rules

These services work together to ensure robust class booking with:
- Minimum notice period validation (configurable, default 2 hours)
- Buffer time between classes (configurable, default 15 minutes)
- Enhanced conflict detection (student double-booking, teacher conflicts)
- Booking limits per day/week (configurable by school/teacher/student)
- Configuration hierarchy (school defaults -> teacher overrides -> class-type specific)
"""

from datetime import date, datetime, time, timedelta
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
import pytz

from accounts.models import CustomUser, School, TeacherProfile

from .constants import (
    DEFAULT_BUFFER_TIME_MINUTES,
    DEFAULT_MINIMUM_NOTICE_HOURS,
    DEFAULT_MINIMUM_NOTICE_MINUTES,
    DEFAULT_STUDENT_MAX_DAILY_BOOKINGS,
    DEFAULT_TEACHER_MAX_DAILY_BOOKINGS,
)
from .models import ClassSchedule, ClassStatus, ClassType, TeacherAvailability, TeacherUnavailability


class SchedulingConfigurationService:
    """Service for managing scheduling rule configuration and inheritance."""

    def get_minimum_notice_hours(
        self, school: School, teacher: TeacherProfile = None, class_type: str | None = None
    ) -> int:
        """Get minimum notice period in hours with configuration hierarchy."""
        # Teacher-specific override
        if teacher and teacher.minimum_notice_minutes is not None:
            return teacher.minimum_notice_minutes // 60

        # School default
        try:
            school_settings = school.settings
            return school_settings.default_minimum_notice_minutes // 60
        except (AttributeError, ValueError, TypeError):
            # Fallback to system default
            return DEFAULT_MINIMUM_NOTICE_HOURS

    def get_minimum_notice_minutes(
        self, school: School, teacher: TeacherProfile = None, class_type: str | None = None
    ) -> int:
        """Get minimum notice period in minutes with configuration hierarchy."""
        # Teacher-specific override
        if teacher and teacher.minimum_notice_minutes is not None:
            return teacher.minimum_notice_minutes

        # School default
        try:
            school_settings = school.settings
            return school_settings.default_minimum_notice_minutes
        except (AttributeError, ValueError, TypeError):
            # Fallback to system default (2 hours)
            return DEFAULT_MINIMUM_NOTICE_MINUTES

    def get_buffer_time_minutes(
        self, school: School, teacher: TeacherProfile = None, class_type: str | None = None
    ) -> int:
        """Get buffer time in minutes with class-type and teacher hierarchy."""
        # Teacher-specific override
        if teacher and teacher.buffer_time_minutes is not None:
            return teacher.buffer_time_minutes

        # Class-type specific rules (from school)
        try:
            school_settings = school.settings
            if class_type == ClassType.GROUP and hasattr(school_settings, "buffer_time_group"):
                return school_settings.buffer_time_group
            elif class_type == ClassType.TRIAL and hasattr(school_settings, "buffer_time_trial"):
                return school_settings.buffer_time_trial

            # School default
            return school_settings.default_buffer_time_minutes
        except (AttributeError, ValueError, TypeError):
            # Fallback to system default
            return DEFAULT_BUFFER_TIME_MINUTES

    def get_daily_booking_limit(self, school: School, teacher: TeacherProfile = None, is_student: bool = False) -> int:
        """Get daily booking limit with role and teacher hierarchy."""
        if is_student:
            try:
                return school.settings.student_max_daily_bookings
            except (AttributeError, ValueError, TypeError):
                return DEFAULT_STUDENT_MAX_DAILY_BOOKINGS  # Student fallback

        # Teacher limits
        if teacher and teacher.max_daily_bookings is not None:
            return teacher.max_daily_bookings

        try:
            return school.settings.default_max_daily_bookings
        except (AttributeError, ValueError, TypeError):
            return DEFAULT_TEACHER_MAX_DAILY_BOOKINGS  # Teacher fallback

    def get_weekly_booking_limit(self, school: School, teacher: TeacherProfile = None, is_student: bool = False) -> int:
        """Get weekly booking limit with role and teacher hierarchy."""
        if is_student:
            try:
                return school.settings.student_max_weekly_bookings
            except (AttributeError, ValueError, TypeError):
                return 10  # Student fallback

        # Teacher limits
        if teacher and teacher.max_weekly_bookings is not None:
            return teacher.max_weekly_bookings

        try:
            return school.settings.default_max_weekly_bookings
        except (AttributeError, ValueError, TypeError):
            return 30  # Teacher fallback

    def get_rule_configuration(
        self, school: School, teacher: TeacherProfile = None, class_type: str | None = None, is_student: bool = False
    ) -> dict[str, Any]:
        """Get complete rule configuration for display/debugging."""
        return {
            "minimum_notice_minutes": self.get_minimum_notice_minutes(school, teacher, class_type),
            "minimum_notice_hours": self.get_minimum_notice_hours(school, teacher, class_type),
            "buffer_time_minutes": self.get_buffer_time_minutes(school, teacher, class_type),
            "daily_booking_limit": self.get_daily_booking_limit(school, teacher, is_student),
            "weekly_booking_limit": self.get_weekly_booking_limit(school, teacher, is_student),
            "class_type": class_type,
            "is_student": is_student,
            "teacher_overrides": {
                "minimum_notice_minutes": teacher.minimum_notice_minutes if teacher else None,
                "buffer_time_minutes": teacher.buffer_time_minutes if teacher else None,
                "max_daily_bookings": teacher.max_daily_bookings if teacher else None,
                "max_weekly_bookings": teacher.max_weekly_bookings if teacher else None,
            }
            if teacher
            else None,
        }


class SchedulingRulesService:
    """Main orchestrator service for scheduling rules validation."""

    def __init__(self):
        self.config_service = SchedulingConfigurationService()

    def validate_minimum_notice(
        self, booking_datetime: datetime, school: School, teacher: TeacherProfile = None, class_type: str | None = None
    ) -> bool:
        """Validate that booking meets minimum notice period requirement."""
        minimum_hours = self.config_service.get_minimum_notice_hours(school, teacher, class_type)
        minimum_minutes = self.config_service.get_minimum_notice_minutes(school, teacher, class_type)

        now_utc = timezone.now()

        # Handle timezone-aware vs naive datetime
        if booking_datetime.tzinfo is None:
            # Treat as UTC for testing consistency
            booking_datetime_utc = timezone.make_aware(booking_datetime, pytz.UTC)
        else:
            booking_datetime_utc = booking_datetime.astimezone(pytz.UTC)

        minimum_allowed_time = now_utc + timedelta(minutes=minimum_minutes)

        if booking_datetime_utc < minimum_allowed_time:
            teacher_name = teacher.user.name if teacher else "the teacher"
            error_msg = (
                f"Classes must be booked at least {minimum_hours} hours ({minimum_minutes} minutes) "
                f"in advance. {teacher_name} requires {minimum_hours} hour minimum notice."
            )
            raise ValidationError(error_msg)

        return True

    def calculate_buffer_time(
        self, class_type: str | None = None, teacher: TeacherProfile = None, school: School = None
    ) -> int:
        """Calculate required buffer time in minutes."""
        if not school:
            return 15  # Default fallback

        return self.config_service.get_buffer_time_minutes(school, teacher, class_type)

    def validate_booking_limits(
        self,
        student: CustomUser,
        teacher: TeacherProfile,
        school: School,
        booking_date: date,
        class_type: str | None = None,
    ) -> bool:
        """Validate that booking doesn't exceed daily/weekly limits."""
        # Get limits
        teacher_daily_limit = self.config_service.get_daily_booking_limit(school, teacher, is_student=False)
        teacher_weekly_limit = self.config_service.get_weekly_booking_limit(school, teacher, is_student=False)
        student_daily_limit = self.config_service.get_daily_booking_limit(school, is_student=True)
        student_weekly_limit = self.config_service.get_weekly_booking_limit(school, is_student=True)

        # Check teacher daily limit
        teacher_daily_count = ClassSchedule.objects.filter(
            teacher=teacher,
            school=school,
            scheduled_date=booking_date,
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
        ).count()

        if teacher_daily_count >= teacher_daily_limit:
            raise ValidationError(
                f"{teacher.user.name} has reached their daily limit of {teacher_daily_limit} classes "
                f"for {booking_date}. Please try booking for another day."
            )

        # Check teacher weekly limit
        week_start = booking_date - timedelta(days=booking_date.weekday())
        week_end = week_start + timedelta(days=6)
        teacher_weekly_count = ClassSchedule.objects.filter(
            teacher=teacher,
            school=school,
            scheduled_date__range=[week_start, week_end],
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
        ).count()

        if teacher_weekly_count >= teacher_weekly_limit:
            raise ValidationError(
                f"{teacher.user.name} has reached their weekly limit of {teacher_weekly_limit} classes "
                f"for the week of {week_start}. Please try booking for another week."
            )

        # Check student daily limit
        student_daily_count = ClassSchedule.objects.filter(
            Q(student=student) | Q(additional_students=student),
            school=school,
            scheduled_date=booking_date,
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
        ).count()

        if student_daily_count >= student_daily_limit:
            raise ValidationError(
                f"Student has reached their daily limit of {student_daily_limit} classes "
                f"for {booking_date}. Please try booking for another day."
            )

        # Check student weekly limit
        student_weekly_count = ClassSchedule.objects.filter(
            Q(student=student) | Q(additional_students=student),
            school=school,
            scheduled_date__range=[week_start, week_end],
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
        ).count()

        if student_weekly_count >= student_weekly_limit:
            raise ValidationError(
                f"Student has reached their weekly limit of {student_weekly_limit} classes "
                f"for the week of {week_start}. Please try booking for another week."
            )

        return True

    def get_rule_configuration(
        self, school: School, teacher: TeacherProfile = None, class_type: str | None = None, is_student: bool = False
    ) -> dict[str, Any]:
        """Get complete rule configuration - delegate to configuration service."""
        return self.config_service.get_rule_configuration(school, teacher, class_type, is_student)


class ConflictDetectionService:
    """Enhanced conflict detection service for students and teachers."""

    def __init__(self):
        self.scheduling_service = SchedulingRulesService()

    def detect_student_conflicts(
        self,
        student: CustomUser,
        school: School,
        booking_date: date,
        start_time: time,
        end_time: time,
        exclude_class_id: int | None = None,
    ) -> dict[str, Any] | None:
        """Detect if student has conflicting classes."""
        conflicting_classes = ClassSchedule.objects.filter(
            Q(student=student) | Q(additional_students=student),
            scheduled_date=booking_date,
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
        ).exclude(Q(end_time__lte=start_time) | Q(start_time__gte=end_time))

        if exclude_class_id:
            conflicting_classes = conflicting_classes.exclude(id=exclude_class_id)

        # Check conflicts across ALL schools, not just current school
        all_school_conflicts = (
            ClassSchedule.objects.filter(
                Q(student=student) | Q(additional_students=student),
                scheduled_date=booking_date,
                status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
            )
            .exclude(Q(end_time__lte=start_time) | Q(start_time__gte=end_time))
            .exclude(school=school)
        )

        if exclude_class_id:
            all_school_conflicts = all_school_conflicts.exclude(id=exclude_class_id)

        conflict = conflicting_classes.first()
        cross_school_conflict = all_school_conflicts.first()

        if cross_school_conflict:
            return {
                "has_conflict": True,
                "type": "cross_school_student_conflict",
                "conflicting_class": {
                    "id": cross_school_conflict.id,
                    "title": cross_school_conflict.title,
                    "start_time": cross_school_conflict.start_time,
                    "end_time": cross_school_conflict.end_time,
                    "teacher_name": cross_school_conflict.teacher.user.name,
                    "school_name": cross_school_conflict.school.name,
                },
                "error_message": (
                    f"Student has a conflicting class '{cross_school_conflict.title}' "
                    f"at {cross_school_conflict.start_time}-{cross_school_conflict.end_time} "
                    f"with {cross_school_conflict.teacher.user.name} in another school "
                    f"({cross_school_conflict.school.name}). Please cancel that class first."
                ),
            }

        if conflict:
            # Check if it's a group class conflict
            if conflict.class_type == ClassType.GROUP:
                return {
                    "has_conflict": True,
                    "type": "group_class_student_conflict",
                    "conflicting_class": {
                        "id": conflict.id,
                        "title": conflict.title,
                        "start_time": conflict.start_time,
                        "end_time": conflict.end_time,
                        "teacher_name": conflict.teacher.user.name,
                        "class_type": conflict.class_type,
                    },
                    "error_message": (
                        f"Student is already participating in group class '{conflict.title}' "
                        f"at {conflict.start_time}-{conflict.end_time} "
                        f"with {conflict.teacher.user.name}. Students cannot double-book themselves."
                    ),
                }

            return {
                "has_conflict": True,
                "type": "student_double_booking",
                "conflicting_class": {
                    "id": conflict.id,
                    "title": conflict.title,
                    "start_time": conflict.start_time,
                    "end_time": conflict.end_time,
                    "teacher_name": conflict.teacher.user.name,
                },
                "error_message": (
                    f"Student has a conflicting class '{conflict.title}' "
                    f"at {conflict.start_time}-{conflict.end_time} "
                    f"with {conflict.teacher.user.name}. Students cannot double-book themselves."
                ),
            }

        return None

    def detect_teacher_conflicts(
        self,
        teacher: TeacherProfile,
        school: School,
        booking_date: date,
        start_time: time,
        end_time: time,
        class_type: str | None = None,
        exclude_class_id: int | None = None,
    ) -> dict[str, Any] | None:
        """Detect if teacher has conflicting classes including buffer time."""
        buffer_minutes = self.scheduling_service.calculate_buffer_time(class_type, teacher, school)

        # Calculate buffer-adjusted times
        start_datetime = datetime.combine(booking_date, start_time)
        end_datetime = datetime.combine(booking_date, end_time)

        buffer_start_datetime = start_datetime - timedelta(minutes=buffer_minutes)
        buffer_end_datetime = end_datetime + timedelta(minutes=buffer_minutes)

        buffer_start_datetime.time()
        buffer_end_datetime.time()

        # Handle day boundary crossing
        search_dates = [booking_date]
        if buffer_start_datetime.date() < booking_date:
            search_dates.append(booking_date - timedelta(days=1))
        if buffer_end_datetime.date() > booking_date:
            search_dates.append(booking_date + timedelta(days=1))

        conflicts = []
        for search_date in search_dates:
            date_conflicts = ClassSchedule.objects.filter(
                teacher=teacher,
                school=school,
                scheduled_date=search_date,
                status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
            )

            if exclude_class_id:
                date_conflicts = date_conflicts.exclude(id=exclude_class_id)

            for existing_class in date_conflicts:
                if self._has_buffer_conflict(
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
            conflict = conflicts[0]  # Return first conflict

            if buffer_minutes == 0:
                error_msg = (
                    f"Teacher has a conflicting class '{conflict.title}' "
                    f"at {conflict.start_time}-{conflict.end_time} on {conflict.scheduled_date} "
                    f"with {conflict.student.name}."
                )
            else:
                earliest_available = self._calculate_earliest_available_time(
                    conflict.scheduled_date, conflict.end_time, buffer_minutes
                )
                error_msg = (
                    f"Teacher requires {buffer_minutes} minute buffer time between classes. "
                    f"Existing class '{conflict.title}' at {conflict.start_time}-{conflict.end_time} "
                    f"with {conflict.student.name} conflicts with requested time. "
                    f"Earliest available time: {earliest_available}."
                )

            return {
                "has_conflict": True,
                "type": "teacher_buffer_conflict" if buffer_minutes > 0 else "teacher_time_conflict",
                "conflicting_class": {
                    "id": conflict.id,
                    "title": conflict.title,
                    "start_time": conflict.start_time,
                    "end_time": conflict.end_time,
                    "student_name": conflict.student.name,
                },
                "buffer_minutes": buffer_minutes,
                "error_message": error_msg,
            }

        return None

    def _has_buffer_conflict(
        self, date1: date, start1: time, end1: time, date2: date, start2: time, end2: time, buffer_minutes: int
    ) -> bool:
        """Check if two time slots conflict considering buffer time."""
        if buffer_minutes == 0:
            # Simple overlap check
            if date1 != date2:
                return False
            return not (end1 <= start2 or start1 >= end2)

        # Convert to datetime for buffer calculation
        datetime1_start = datetime.combine(date1, start1)
        datetime1_end = datetime.combine(date1, end1)
        datetime2_start = datetime.combine(date2, start2)
        datetime2_end = datetime.combine(date2, end2)

        # Add buffer
        buffered1_start = datetime1_start - timedelta(minutes=buffer_minutes)
        buffered1_end = datetime1_end + timedelta(minutes=buffer_minutes)

        # Check overlap
        return not (buffered1_end <= datetime2_start or buffered1_start >= datetime2_end)

    def _calculate_earliest_available_time(
        self, conflict_date: date, conflict_end_time: time, buffer_minutes: int
    ) -> str:
        """Calculate earliest available time after a conflicting class."""
        conflict_end_datetime = datetime.combine(conflict_date, conflict_end_time)
        earliest_datetime = conflict_end_datetime + timedelta(minutes=buffer_minutes)
        return earliest_datetime.strftime("%H:%M")

    def detect_time_overlap(
        self, start1: time, end1: time, start2: time, end2: time, return_details: bool = False
    ) -> bool | dict[str, Any]:
        """Detect if two time ranges overlap."""
        has_overlap = not (end1 <= start2 or start1 >= end2)

        if not return_details:
            return has_overlap

        if has_overlap:
            overlap_start = max(start1, start2)
            overlap_end = min(end1, end2)
            overlap_minutes = (
                datetime.combine(date.today(), overlap_end) - datetime.combine(date.today(), overlap_start)
            ).total_seconds() // 60
        else:
            overlap_start = None
            overlap_end = None
            overlap_minutes = 0

        return {
            "has_overlap": has_overlap,
            "overlap_start": overlap_start,
            "overlap_end": overlap_end,
            "overlap_minutes": int(overlap_minutes),
        }

    def handle_day_boundary_cases(self, booking_date: date, start_time: time, end_time: time) -> dict[str, Any]:
        """Handle classes that span day boundaries."""
        crosses_midnight = start_time > end_time

        if crosses_midnight:
            end_date = booking_date + timedelta(days=1)
            # Calculate total duration spanning midnight
            start_datetime = datetime.combine(booking_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)
            total_minutes = int((end_datetime - start_datetime).total_seconds() // 60)
        else:
            end_date = booking_date
            start_datetime = datetime.combine(booking_date, start_time)
            end_datetime = datetime.combine(booking_date, end_time)
            total_minutes = int((end_datetime - start_datetime).total_seconds() // 60)

        return {
            "crosses_midnight": crosses_midnight,
            "start_date": booking_date,
            "end_date": end_date,
            "total_minutes": total_minutes,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
        }


class AvailabilityCalculationService:
    """Service for calculating available slots with scheduling rules applied."""

    def __init__(self):
        self.scheduling_service = SchedulingRulesService()
        self.conflict_service = ConflictDetectionService()

    def get_available_slots_with_rules(
        self,
        teacher: TeacherProfile,
        school: School,
        start_date: date,
        duration_minutes: int,
        end_date: date | None = None,
        class_type: str | None = None,
        requesting_student: CustomUser = None,
    ) -> dict[str, Any]:
        """Calculate available slots respecting all scheduling rules."""
        if end_date is None:
            end_date = start_date

        # Get configuration
        config = self.scheduling_service.get_rule_configuration(
            school, teacher, class_type, is_student=bool(requesting_student)
        )

        available_slots = []
        current_date = start_date

        while current_date <= end_date:
            day_slots = self._get_slots_for_date_with_rules(
                teacher, school, current_date, duration_minutes, class_type, requesting_student, config
            )
            available_slots.extend(day_slots)
            current_date += timedelta(days=1)

        return {
            "available_slots": available_slots,
            "restrictions_applied": {
                "buffer_time_minutes": config["buffer_time_minutes"],
                "minimum_notice_hours": config["minimum_notice_hours"],
                "daily_booking_limit": config["daily_booking_limit"],
                "class_type": class_type,
                "teacher_name": teacher.user.name,
            },
            "total_slots": len(available_slots),
        }

    def _get_slots_for_date_with_rules(
        self,
        teacher: TeacherProfile,
        school: School,
        booking_date: date,
        duration_minutes: int,
        class_type: str | None = None,
        requesting_student: CustomUser = None,
        config: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Get available slots for a specific date applying all rules."""
        if config is None:
            config = self.scheduling_service.get_rule_configuration(
                school, teacher, class_type, is_student=bool(requesting_student)
            )

        day_of_week = booking_date.strftime("%A").lower()

        # Get teacher availability for this day
        availability = TeacherAvailability.objects.filter(
            teacher=teacher, school=school, day_of_week=day_of_week, is_active=True
        ).first()

        if not availability:
            return []

        # Check if we've reached daily booking limits
        if not self._check_daily_booking_capacity(teacher, school, booking_date, config):
            return []

        slots = []
        current_time = availability.start_time
        end_limit = availability.end_time
        buffer_minutes = config["buffer_time_minutes"]
        minimum_notice_minutes = config["minimum_notice_minutes"]

        while current_time < end_limit:
            slot_end_datetime = datetime.combine(booking_date, current_time) + timedelta(minutes=duration_minutes)
            slot_end_time = slot_end_datetime.time()

            # Check if slot fits within availability
            if slot_end_time > end_limit:
                break

            # Check minimum notice period
            if not self._meets_minimum_notice(booking_date, current_time, minimum_notice_minutes):
                current_time = self._advance_time_slot(current_time)
                continue

            # Check for conflicts (unavailability, existing classes, buffer times)
            if self._has_slot_conflicts(
                teacher, school, booking_date, current_time, slot_end_time, class_type, buffer_minutes
            ):
                current_time = self._advance_time_slot(current_time)
                continue

            # Create slot
            slot = self._create_slot(teacher, school, booking_date, current_time, slot_end_time, duration_minutes)
            slots.append(slot)

            current_time = self._advance_time_slot(current_time)

        return slots

    def _check_daily_booking_capacity(
        self, teacher: TeacherProfile, school: School, booking_date: date, config: dict[str, Any]
    ) -> bool:
        """Check if daily booking limit allows more slots."""
        daily_limit = config["daily_booking_limit"]
        current_count = ClassSchedule.objects.filter(
            teacher=teacher,
            school=school,
            scheduled_date=booking_date,
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
        ).count()

        # Reserve some slots for the limit (not all slots should be available)
        return current_count < daily_limit

    def _meets_minimum_notice(self, booking_date: date, booking_time: time, minimum_notice_minutes: int) -> bool:
        """Check if slot meets minimum notice requirement."""
        now_utc = timezone.now()
        booking_datetime = timezone.make_aware(datetime.combine(booking_date, booking_time), pytz.UTC)
        minimum_allowed = now_utc + timedelta(minutes=minimum_notice_minutes)
        return booking_datetime >= minimum_allowed

    def _has_slot_conflicts(
        self,
        teacher: TeacherProfile,
        school: School,
        booking_date: date,
        start_time: time,
        end_time: time,
        class_type: str | None = None,
        buffer_minutes: int = 15,
    ) -> bool:
        """Check if slot has any conflicts."""
        # Check unavailability
        unavailabilities = TeacherUnavailability.objects.filter(teacher=teacher, school=school, date=booking_date)

        for unavailability in unavailabilities:
            if unavailability.is_all_day:
                return True
            if (
                unavailability.start_time
                and unavailability.end_time
                and not (end_time <= unavailability.start_time or start_time >= unavailability.end_time)
            ):
                return True

        # Check existing classes with buffer time
        teacher_conflict = self.conflict_service.detect_teacher_conflicts(
            teacher, school, booking_date, start_time, end_time, class_type
        )

        return teacher_conflict is not None

    def _create_slot(
        self,
        teacher: TeacherProfile,
        school: School,
        booking_date: date,
        start_time: time,
        end_time: time,
        duration_minutes: int,
    ) -> dict[str, Any]:
        """Create slot data structure."""
        try:
            school_timezone_str = school.settings.timezone
        except (AttributeError, ValueError, TypeError):
            school_timezone_str = "UTC"

        school_tz = pytz.timezone(school_timezone_str)
        naive_datetime = datetime.combine(booking_date, start_time)
        local_datetime = school_tz.localize(naive_datetime)
        utc_datetime = local_datetime.astimezone(pytz.UTC)

        return {
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "start_datetime_iso": utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_datetime_iso": (utc_datetime + timedelta(minutes=duration_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "start_datetime_local": local_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "school_id": school.id,
            "school_name": school.name,
            "duration_minutes": duration_minutes,
            "teacher_id": teacher.id,
            "teacher_name": teacher.user.name,
        }

    def _advance_time_slot(self, current_time: time) -> time:
        """Advance to next 30-minute slot."""
        current_datetime = datetime.combine(date.today(), current_time)
        next_datetime = current_datetime + timedelta(minutes=30)
        return next_datetime.time()
