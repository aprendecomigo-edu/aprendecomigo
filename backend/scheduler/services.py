"""
Service classes for scheduler business logic.
Following Django best practices for separation of concerns.
"""
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
import pytz
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q

from accounts.models import TeacherProfile, School
from .models import (
    TeacherAvailability,
    TeacherUnavailability, 
    ClassSchedule,
    ClassStatus
)


class AvailableSlotsService:
    """
    Service class for calculating available time slots for teachers.
    Implements business logic requirements from GitHub issue #148.
    """
    
    DEFAULT_DURATION_MINUTES = 60
    MIN_BUFFER_MINUTES = 0  # Minimum buffer between sessions
    CACHE_TIMEOUT = 300  # 5 minutes cache
    
    def __init__(self, teacher: TeacherProfile, schools: List[School]):
        self.teacher = teacher
        self.schools = schools
    
    def get_available_slots(
        self, 
        start_date: datetime.date,
        duration_minutes: int = DEFAULT_DURATION_MINUTES,
        end_date: Optional[datetime.date] = None
    ) -> List[Dict]:
        """
        Calculate available time slots for a teacher.
        
        Args:
            start_date: Starting date for slot calculation
            duration_minutes: Duration of each slot in minutes (default 60)
            end_date: Optional end date for range queries
            
        Returns:
            List of available slots with ISO datetime format
        """
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive")
            
        if end_date and end_date < start_date:
            raise ValueError("End date must be after start date")
            
        # Use cache key for performance optimization (disabled in tests)
        import sys
        from django.conf import settings
        
        # Disable caching during tests or when running with test command
        use_cache = not (getattr(settings, 'TESTING', False) or 'test' in sys.argv)
        
        cache_key = None
        cached_result = None
        if use_cache:
            cache_key = self._get_cache_key(start_date, duration_minutes, end_date)
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
        available_slots = []
        
        # Process single date or date range
        if end_date:
            current_date = start_date
            while current_date <= end_date:
                slots = self._calculate_slots_for_date(current_date, duration_minutes)
                available_slots.extend(slots)
                current_date += timedelta(days=1)
        else:
            available_slots = self._calculate_slots_for_date(start_date, duration_minutes)
        
        # Cache the result (only if not in tests)
        if use_cache and cache_key:
            cache.set(cache_key, available_slots, self.CACHE_TIMEOUT)
        
        return available_slots
    
    def _calculate_slots_for_date(self, date: datetime.date, duration_minutes: int) -> List[Dict]:
        """Calculate available slots for a specific date."""
        slots = []
        day_of_week = date.strftime("%A").lower()
        
        for school in self.schools:
            # Get teacher availability for this day
            availability = self._get_teacher_availability(school, day_of_week)
            if not availability:
                continue
                
            # Check for all-day unavailability
            if self._is_all_day_unavailable(school, date):
                continue
                
            # Get time blocks that are unavailable
            unavailable_periods = self._get_unavailable_periods(school, date)
            booked_periods = self._get_booked_periods(school, date)
            
            # Generate slots within availability window
            school_slots = self._generate_time_slots(
                date=date,
                availability_start=availability.start_time,
                availability_end=availability.end_time,
                duration_minutes=duration_minutes,
                unavailable_periods=unavailable_periods + booked_periods,
                school=school
            )
            
            slots.extend(school_slots)
            
        return slots
    
    def _get_teacher_availability(self, school: School, day_of_week: str) -> Optional[TeacherAvailability]:
        """Get teacher's regular availability for a specific day."""
        return TeacherAvailability.objects.filter(
            teacher=self.teacher,
            school=school,
            day_of_week=day_of_week,
            is_active=True
        ).first()
    
    def _is_all_day_unavailable(self, school: School, date: datetime.date) -> bool:
        """Check if teacher is unavailable all day."""
        unavailability = TeacherUnavailability.objects.filter(
            teacher=self.teacher,
            school=school,
            date=date,
            is_all_day=True
        ).exists()
        return unavailability
    
    def _get_unavailable_periods(self, school: School, date: datetime.date) -> List[Tuple[time, time]]:
        """Get partial-day unavailability periods."""
        unavailabilities = TeacherUnavailability.objects.filter(
            teacher=self.teacher,
            school=school,
            date=date,
            is_all_day=False
        ).values_list('start_time', 'end_time')
        
        return list(unavailabilities)
    
    def _get_booked_periods(self, school: School, date: datetime.date) -> List[Tuple[time, time]]:
        """Get existing class booking periods."""
        bookings = ClassSchedule.objects.filter(
            teacher=self.teacher,
            school=school,
            scheduled_date=date,
            status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED]
        ).values_list('start_time', 'end_time')
        
        return list(bookings)
    
    def _generate_time_slots(
        self,
        date: datetime.date,
        availability_start: time,
        availability_end: time,
        duration_minutes: int,
        unavailable_periods: List[Tuple[time, time]],
        school: School
    ) -> List[Dict]:
        """Generate discrete time slots within availability window."""
        slots = []
        duration_delta = timedelta(minutes=duration_minutes)
        buffer_delta = timedelta(minutes=self.MIN_BUFFER_MINUTES)
        
        # Get school timezone (default to UTC if no settings)
        try:
            timezone_name = school.settings.timezone if hasattr(school, 'settings') and school.settings else 'UTC'
        except AttributeError:
            timezone_name = 'UTC'
        school_timezone = pytz.timezone(timezone_name)
        
        # Convert availability times to timezone-aware datetimes
        availability_start_dt = school_timezone.localize(
            datetime.combine(date, availability_start)
        )
        availability_end_dt = school_timezone.localize(
            datetime.combine(date, availability_end)
        )
        
        current_datetime = availability_start_dt
        
        while current_datetime + duration_delta <= availability_end_dt:
            slot_end_datetime = current_datetime + duration_delta
            
            # Check if this slot conflicts with any unavailable periods
            if not self._slot_conflicts_with_periods(
                current_datetime.time(), 
                slot_end_datetime.time(), 
                unavailable_periods
            ):
                # Convert to UTC for API response
                start_utc = current_datetime.astimezone(pytz.UTC)
                end_utc = slot_end_datetime.astimezone(pytz.UTC)
                
                slots.append({
                    "start": start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                })
            
            # Move to next potential slot (with buffer if needed)
            current_datetime = slot_end_datetime + buffer_delta
        
        return slots
    
    def _slot_conflicts_with_periods(
        self, 
        slot_start: time, 
        slot_end: time, 
        periods: List[Tuple[time, time]]
    ) -> bool:
        """Check if a time slot conflicts with any unavailable periods."""
        for period_start, period_end in periods:
            if slot_start < period_end and slot_end > period_start:
                return True
        return False
    
    def _get_cache_key(
        self, 
        start_date: datetime.date, 
        duration_minutes: int, 
        end_date: Optional[datetime.date]
    ) -> str:
        """Generate cache key for slot calculation."""
        key_parts = [
            f"slots",
            f"teacher_{self.teacher.id}",
            f"date_{start_date.isoformat()}",
            f"duration_{duration_minutes}"
        ]
        
        if end_date:
            key_parts.append(f"end_{end_date.isoformat()}")
            
        school_ids = sorted([school.id for school in self.schools])
        key_parts.append(f"schools_{'_'.join(map(str, school_ids))}")
        
        return ":".join(key_parts)


class SlotValidationService:
    """Service for validating slot-related input parameters."""
    
    @staticmethod
    def validate_date_format(date_str: str) -> datetime.date:
        """Validate and parse date string in ISO format."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be in ISO format (YYYY-MM-DD)")
    
    @staticmethod
    def validate_duration(duration_minutes: int) -> None:
        """Validate duration parameter."""
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        
        if duration_minutes > 480:  # 8 hours max
            raise ValueError("Duration cannot exceed 480 minutes (8 hours)")
    
    @staticmethod
    def validate_date_range(start_date: datetime.date, end_date: datetime.date) -> None:
        """Validate date range parameters."""
        if end_date < start_date:
            raise ValueError("date_end must be after or equal to date")
        
        # Limit range to prevent abuse
        max_days = 90
        if (end_date - start_date).days > max_days:
            raise ValueError(f"Date range cannot exceed {max_days} days")
