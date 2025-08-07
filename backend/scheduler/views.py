from datetime import datetime, timedelta, date, time
import pytz
from typing import ClassVar

from accounts.models import SchoolMembership, SchoolRole, TeacherProfile
from accounts.permissions import SchoolPermissionMixin
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    ClassSchedule,
    ClassStatus,
    RecurringClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
)
from .serializers import (
    CancelClassSerializer,
    ClassScheduleSerializer,
    CreateClassScheduleSerializer,
    RecurringClassScheduleSerializer,
    TeacherAvailabilitySerializer,
    TeacherUnavailabilitySerializer,
)


class TeacherAvailabilityViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing teacher availability"""

    serializer_class = TeacherAvailabilitySerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        user_schools = self.get_user_schools()
        queryset = TeacherAvailability.objects.filter(school__in=user_schools).select_related(
            "teacher__user", "school"
        )

        # Filter by teacher if specified
        teacher_id = self.request.query_params.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        return queryset.order_by("day_of_week", "start_time")

    def create(self, request, *args, **kwargs):
        """Override create to handle teacher field properly"""
        data = request.data.copy()
        
        # If teacher is not provided and user has teacher_profile, set it automatically
        if 'teacher' not in data or data['teacher'] is None:
            if hasattr(request.user, 'teacher_profile'):
                data['teacher'] = request.user.teacher_profile.id
                
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Ensure teacher and school are valid"""
        serializer.save()


class TeacherUnavailabilityViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing teacher unavailability"""

    serializer_class = TeacherUnavailabilitySerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        user_schools = self.get_user_schools()
        queryset = TeacherUnavailability.objects.filter(school__in=user_schools).select_related(
            "teacher__user", "school"
        )

        # Filter by teacher if specified
        teacher_id = self.request.query_params.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        return queryset.order_by("date", "start_time")

    def create(self, request, *args, **kwargs):
        """Override create to handle teacher field properly"""
        data = request.data.copy()
        
        # If teacher is not provided and user has teacher_profile, set it automatically
        if 'teacher' not in data or data['teacher'] is None:
            if hasattr(request.user, 'teacher_profile'):
                data['teacher'] = request.user.teacher_profile.id
                
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Ensure teacher and school are valid"""
        serializer.save()


class ClassScheduleViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing class schedules"""

    permission_classes: ClassVar = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateClassScheduleSerializer
        return ClassScheduleSerializer

    def get_queryset(self):
        user_schools = self.get_user_schools()
        user = self.request.user

        # Base queryset
        queryset = (
            ClassSchedule.objects.filter(school__in=user_schools)
            .select_related("teacher__user", "student", "school", "booked_by")
            .prefetch_related("additional_students")
        )

        # Filter based on user role
        if hasattr(user, "teacher_profile"):
            # Teachers can only see their own classes
            queryset = queryset.filter(teacher=user.teacher_profile)
        else:
            # Check if user is admin
            is_admin = SchoolMembership.objects.filter(
                user=user,
                role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
                is_active=True,
            ).exists()

            if not is_admin:
                # Students can only see classes they're participating in
                queryset = queryset.filter(Q(student=user) | Q(additional_students=user))
            # Admins can see all classes in their schools

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)

        end_date = self.request.query_params.get("end_date")
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by teacher
        teacher_id = self.request.query_params.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        # Filter by student
        student_id = self.request.query_params.get("student_id")
        if student_id:
            queryset = queryset.filter(Q(student_id=student_id) | Q(additional_students=student_id))

        return queryset.order_by("scheduled_date", "start_time")

    def perform_create(self, serializer):
        """Create a new class schedule"""
        user = self.request.user

        # Permission checks
        if hasattr(user, "teacher_profile"):
            # Teachers cannot book classes
            raise PermissionDenied("Teachers cannot book classes")

        student = serializer.validated_data.get("student")

        # Students can only book classes for themselves, unless user is a school admin
        is_admin = SchoolMembership.objects.filter(
            user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
        ).exists()

        if not is_admin and student != user:
            raise PermissionDenied("Students can only book classes for themselves")

        # Ensure user has permission to book in this school
        school = serializer.validated_data.get("school")
        if not SchoolMembership.objects.filter(user=user, school=school, is_active=True).exists():
            raise PermissionDenied("You don't have permission to book classes in this school")

        serializer.save()

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a class"""
        class_schedule = self.get_object()

        if not class_schedule.can_be_cancelled:
            return Response(
                {"error": "This class cannot be cancelled"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CancelClassSerializer(data=request.data)
        if serializer.is_valid():
            reason = serializer.validated_data.get("reason", "")
            class_schedule.cancel(reason=reason)

            return Response({"message": "Class cancelled successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm a scheduled class"""
        class_schedule = self.get_object()

        if class_schedule.status != ClassStatus.SCHEDULED:
            return Response(
                {"error": "Only scheduled classes can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        class_schedule.status = ClassStatus.CONFIRMED
        class_schedule.save()

        return Response({"message": "Class confirmed successfully"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark a class as completed"""
        class_schedule = self.get_object()

        # Only teachers can mark their classes as completed
        if (
            not hasattr(request.user, "teacher_profile")
            or class_schedule.teacher != request.user.teacher_profile
        ):
            return Response(
                {"error": "Only the assigned teacher can mark classes as completed"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            class_schedule.complete()
            return Response(
                {"message": "Class marked as completed successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def my_classes(self, request):
        """Get classes for the current user"""
        user = request.user
        user_schools = self.get_user_schools()

        # Get upcoming classes for the user
        today = timezone.now().date()

        if hasattr(user, "teacher_profile"):
            # Teacher's classes
            classes = (
                ClassSchedule.objects.filter(
                    teacher=user.teacher_profile, school__in=user_schools, scheduled_date__gte=today
                )
                .select_related("student", "school")
                .order_by("scheduled_date", "start_time")
            )
        else:
            # Student's classes
            classes = (
                ClassSchedule.objects.filter(
                    Q(student=user) | Q(additional_students=user),
                    school__in=user_schools,
                    scheduled_date__gte=today,
                )
                .select_related("teacher__user", "school")
                .order_by("scheduled_date", "start_time")
            )

        serializer = ClassScheduleSerializer(classes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def available_slots(self, request):
        """
        Get available time slots for a teacher on a specific date.
        
        Implements requirements from GitHub issue #148:
        - Required parameters: teacher_id, date (ISO format)
        - Optional parameters: duration_minutes (default 60), date_end (for ranges)
        - Returns ISO datetime format with proper timezone handling
        - Includes performance optimization with caching
        """
        from .services import AvailableSlotsService, SlotValidationService
        
        # Extract and validate required parameters
        teacher_id = request.query_params.get("teacher_id")
        date_str = request.query_params.get("date")
        
        if not teacher_id or not date_str:
            return Response(
                {"error": "teacher_id and date are required parameters"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract optional parameters
        duration_minutes = request.query_params.get("duration_minutes", 60)
        date_end_str = request.query_params.get("date_end")
        
        try:
            # Validate teacher exists
            teacher = TeacherProfile.objects.select_related('user').get(id=teacher_id)
            
            # Validate and parse dates
            start_date = SlotValidationService.validate_date_format(date_str)
            end_date = None
            if date_end_str:
                end_date = SlotValidationService.validate_date_format(date_end_str)
                SlotValidationService.validate_date_range(start_date, end_date)
            
            # Validate duration
            duration_minutes = int(duration_minutes)
            SlotValidationService.validate_duration(duration_minutes)
            
        except (ValueError, TeacherProfile.DoesNotExist) as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user's accessible schools
        user_schools = self.get_user_schools()
        
        # Initialize service and calculate slots
        service = AvailableSlotsService(teacher=teacher, schools=user_schools)
        
        try:
            available_slots = service.get_available_slots(
                start_date=start_date,
                duration_minutes=duration_minutes,
                end_date=end_date
            )
            
            # Return response in the exact format specified in issue #148
            return Response({
                "available_slots": available_slots
            })
            
        except Exception as e:
            # Log error for debugging (using Django's logging framework)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Error calculating available slots for teacher {teacher_id} "
                f"on {date_str}: {str(e)}"
            )
            
            return Response(
                {"error": "Unable to calculate available slots"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        
        # Extract optional parameters
        try:
            duration_minutes = int(request.query_params.get("duration_minutes", 60))
        except ValueError:
            return Response(
                {"error": "duration_minutes must be a valid integer"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        date_end_str = request.query_params.get("date_end")
        
        # Validate teacher and dates
        try:
            teacher = TeacherProfile.objects.select_related("user").get(id=teacher_id)
            start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            if date_end_str:
                end_date = datetime.strptime(date_end_str, "%Y-%m-%d").date()
                if end_date < start_date:
                    return Response(
                        {"error": "date_end must be after or equal to date"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                end_date = start_date
                
        except (ValueError, TeacherProfile.DoesNotExist) as e:
            if isinstance(e, TeacherProfile.DoesNotExist):
                error_msg = "Teacher not found"
            else:
                error_msg = "Invalid date format. Use YYYY-MM-DD"
            return Response(
                {"error": error_msg}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate duration
        if duration_minutes <= 0 or duration_minutes > 480:  # Max 8 hours
            return Response(
                {"error": "duration_minutes must be between 1 and 480"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user's accessible schools
        user_schools = self.get_user_schools()
        if not user_schools:
            return Response({"available_slots": []})
        
        # Check if teacher belongs to any of the user's accessible schools
        teacher_schools = teacher.availabilities.filter(
            school__in=user_schools
        ).values_list('school_id', flat=True).distinct()
        
        if not teacher_schools:
            return Response(
                {"error": "You don't have permission to view availability for this teacher"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate date range
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Calculate available slots for each date
        all_available_slots = []
        for target_date in date_range:
            slots = self._calculate_available_slots_for_date(
                teacher, user_schools, target_date, duration_minutes
            )
            all_available_slots.extend(slots)
        
        # Sort slots by start time
        all_available_slots.sort(key=lambda x: x["start"])
        
        return Response({"available_slots": all_available_slots})
    
    def _calculate_available_slots_for_date(self, teacher, schools, target_date, duration_minutes):
        """Calculate available slots for a specific date across schools"""
        day_of_week = target_date.strftime("%A").lower()
        
        # Get teacher's availability patterns across all user schools
        availabilities = TeacherAvailability.objects.filter(
            teacher=teacher,
            school__in=schools,
            day_of_week=day_of_week,
            is_active=True
        ).select_related("school", "school__settings")
        
        if not availabilities.exists():
            return []
        
        # Get all conflicting periods for this teacher on this date (for accessible schools)
        conflicting_periods = self._get_conflicting_periods(teacher, target_date, schools)
        
        # Generate available slots for each availability pattern
        all_slots = []
        for availability in availabilities:
            school_timezone = pytz.timezone(availability.school.settings.timezone)
            slots = self._generate_time_slots(
                availability, conflicting_periods, duration_minutes, school_timezone, target_date
            )
            all_slots.extend(slots)
        
        # Remove duplicate slots (same start/end time)
        unique_slots = {}
        for slot in all_slots:
            key = f"{slot['start']}_{slot['end']}"
            if key not in unique_slots:
                unique_slots[key] = slot
        
        return list(unique_slots.values())
    
    def _get_conflicting_periods(self, teacher, target_date, schools=None):
        """Get all conflicting periods (unavailability + bookings) for a teacher on a date"""
        conflicts = []
        
        # Get unavailability periods
        unavailability_filter = {
            'teacher': teacher,
            'date': target_date
        }
        if schools is not None:
            unavailability_filter['school__in'] = schools
            
        unavailabilities = TeacherUnavailability.objects.filter(
            **unavailability_filter
        ).select_related("school", "school__settings")
        
        for unavail in unavailabilities:
            if unavail.is_all_day:
                # All-day unavailability blocks the entire day
                conflicts.append({
                    'start_time': time(0, 0),
                    'end_time': time(23, 59),
                    'timezone': unavail.school.settings.timezone
                })
            else:
                conflicts.append({
                    'start_time': unavail.start_time,
                    'end_time': unavail.end_time,
                    'timezone': unavail.school.settings.timezone
                })
        
        # Get existing bookings
        booking_filter = {
            'teacher': teacher,
            'scheduled_date': target_date,
            'status__in': [ClassStatus.SCHEDULED, ClassStatus.CONFIRMED]
        }
        if schools is not None:
            booking_filter['school__in'] = schools
            
        existing_classes = ClassSchedule.objects.filter(
            **booking_filter
        ).select_related("school", "school__settings")
        
        for booking in existing_classes:
            conflicts.append({
                'start_time': booking.start_time,
                'end_time': booking.end_time,
                'timezone': booking.school.settings.timezone
            })
        
        return conflicts
    
    def _generate_time_slots(self, availability, conflicting_periods, duration_minutes, school_timezone, target_date):
        """Generate available time slots given availability and conflicts"""
        slots = []
        
        # Convert availability times to timezone-aware datetimes
        availability_start = school_timezone.localize(
            datetime.combine(target_date, availability.start_time)
        )
        availability_end = school_timezone.localize(
            datetime.combine(target_date, availability.end_time)
        )
        
        # Convert conflicting periods to the same timezone
        normalized_conflicts = []
        for conflict in conflicting_periods:
            conflict_tz = pytz.timezone(conflict['timezone'])
            conflict_start = conflict_tz.localize(
                datetime.combine(target_date, conflict['start_time'])
            ).astimezone(school_timezone)
            conflict_end = conflict_tz.localize(
                datetime.combine(target_date, conflict['end_time'])
            ).astimezone(school_timezone)
            normalized_conflicts.append((conflict_start, conflict_end))
        
        # Sort conflicts by start time
        normalized_conflicts.sort(key=lambda x: x[0])
        
        # Generate slots
        current_time = availability_start
        slot_duration = timedelta(minutes=duration_minutes)
        
        while current_time + slot_duration <= availability_end:
            slot_end = current_time + slot_duration
            
            # Check if this slot conflicts with any existing booking/unavailability
            slot_available = True
            for conflict_start, conflict_end in normalized_conflicts:
                # Check for overlap: slot overlaps if it starts before conflict ends 
                # and ends after conflict starts (proper overlap detection)
                if current_time < conflict_end and slot_end > conflict_start:
                    slot_available = False
                    break
            
            if slot_available:
                # Convert to UTC for API response
                utc_start = current_time.astimezone(pytz.UTC)
                utc_end = slot_end.astimezone(pytz.UTC)
                
                slots.append({
                    "start": utc_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": utc_end.strftime("%Y-%m-%dT%H:%M:%SZ")
                })
            
            # Move to next potential slot
            current_time += slot_duration
        
        return slots


class RecurringClassScheduleViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing recurring class schedules"""

    serializer_class = RecurringClassScheduleSerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        user_schools = self.get_user_schools()
        user = self.request.user

        queryset = RecurringClassSchedule.objects.filter(school__in=user_schools).select_related(
            "teacher__user", "student", "school", "created_by"
        )

        # Filter based on user role
        if hasattr(user, "teacher_profile"):
            # Teachers can only see their own recurring schedules
            queryset = queryset.filter(teacher=user.teacher_profile)
        elif not user.is_admin:
            # Students can only see recurring schedules they're participating in
            queryset = queryset.filter(student=user)

        return queryset.order_by("day_of_week", "start_time")

    def perform_create(self, serializer):
        """Create recurring schedule with permission checks"""
        user = self.request.user

        # Permission checks
        if hasattr(user, "teacher_profile"):
            # Teachers cannot create recurring schedules
            raise PermissionDenied("Teachers cannot create recurring schedules")

        student = serializer.validated_data.get("student")

        # Students can only create recurring schedules for themselves
        if not user.is_admin and student != user:
            raise PermissionDenied("Students can only create recurring schedules for themselves")

        serializer.save()

    @action(detail=True, methods=["post"])
    def generate_schedules(self, request, pk=None):
        """Generate individual class schedules from recurring schedule"""
        recurring_schedule = self.get_object()

        weeks_ahead = int(request.data.get("weeks_ahead", 4))
        created_schedules = recurring_schedule.generate_class_schedules(weeks_ahead)

        serializer = ClassScheduleSerializer(created_schedules, many=True)
        return Response(
            {
                "message": f"Generated {len(created_schedules)} class schedules",
                "schedules": serializer.data,
            }
        )
