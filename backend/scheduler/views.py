from typing import ClassVar

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import SchoolMembership, SchoolRole, TeacherProfile
from accounts.permissions import SchoolPermissionMixin

from .models import (
    ClassReminder,
    ClassSchedule,
    RecurringClassSchedule,
    ReminderPreference,
    TeacherAvailability,
    TeacherUnavailability,
)
from .serializers import (
    CancelClassSerializer,
    ClassReminderSerializer,
    ClassScheduleSerializer,
    CreateClassScheduleSerializer,
    ProcessReminderQueueSerializer,
    RecurringClassScheduleSerializer,
    ReminderPreferenceSerializer,
    TeacherAvailabilitySerializer,
    TeacherUnavailabilitySerializer,
    TriggerReminderSerializer,
)


class TeacherAvailabilityViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing teacher availability"""

    serializer_class = TeacherAvailabilitySerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        user_schools = self.get_user_schools()
        queryset = TeacherAvailability.objects.filter(school__in=user_schools).select_related("teacher__user", "school")

        # Filter by teacher if specified
        teacher_id = self.request.query_params.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        return queryset.order_by("day_of_week", "start_time")

    def create(self, request, *args, **kwargs):
        """Override create to handle teacher field properly"""
        data = request.data.copy()

        # If teacher is not provided and user has teacher_profile, set it automatically
        if ("teacher" not in data or data["teacher"] is None) and hasattr(request.user, "teacher_profile"):
            data["teacher"] = request.user.teacher_profile.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Ensure teacher and school are valid"""
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Update teacher availability with permission checks"""
        instance = self.get_object()
        user = request.user

        # Check permissions - only the teacher themselves or admins can update availability
        if hasattr(user, "teacher_profile"):
            # Teachers can only update their own availability
            if instance.teacher != user.teacher_profile:
                raise PermissionDenied("Teachers can only update their own availability")
        else:
            # Check if user is admin
            is_admin = SchoolMembership.objects.filter(
                user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
            ).exists()
            if not is_admin:
                raise PermissionDenied("Only teachers and administrators can update availability")

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partial update teacher availability with permission checks"""
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete teacher availability with permission checks"""
        instance = self.get_object()
        user = request.user

        # Check permissions - only the teacher themselves or admins can delete availability
        if hasattr(user, "teacher_profile"):
            # Teachers can only delete their own availability
            if instance.teacher != user.teacher_profile:
                raise PermissionDenied("Teachers can only delete their own availability")
        else:
            # Check if user is admin
            is_admin = SchoolMembership.objects.filter(
                user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
            ).exists()
            if not is_admin:
                raise PermissionDenied("Only teachers and administrators can delete availability")

        return super().destroy(request, *args, **kwargs)


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
        if ("teacher" not in data or data["teacher"] is None) and hasattr(request.user, "teacher_profile"):
            data["teacher"] = request.user.teacher_profile.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Ensure teacher and school are valid"""
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Update teacher unavailability with permission checks"""
        instance = self.get_object()
        user = request.user

        # Check permissions - only the teacher themselves or admins can update unavailability
        if hasattr(user, "teacher_profile"):
            # Teachers can only update their own unavailability
            if instance.teacher != user.teacher_profile:
                raise PermissionDenied("Teachers can only update their own unavailability")
        else:
            # Check if user is admin
            is_admin = SchoolMembership.objects.filter(
                user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
            ).exists()
            if not is_admin:
                raise PermissionDenied("Only teachers and administrators can update unavailability")

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partial update teacher unavailability with permission checks"""
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete teacher unavailability with permission checks"""
        instance = self.get_object()
        user = request.user

        # Check permissions - only the teacher themselves or admins can delete unavailability
        if hasattr(user, "teacher_profile"):
            # Teachers can only delete their own unavailability
            if instance.teacher != user.teacher_profile:
                raise PermissionDenied("Teachers can only delete their own unavailability")
        else:
            # Check if user is admin
            is_admin = SchoolMembership.objects.filter(
                user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
            ).exists()
            if not is_admin:
                raise PermissionDenied("Only teachers and administrators can delete unavailability")

        return super().destroy(request, *args, **kwargs)


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

    def get_object_for_permissions(self):
        """Get object without applying user-specific filtering for permission checking."""
        pk = self.kwargs.get("pk")
        try:
            return (
                ClassSchedule.objects.select_related("teacher__user", "student", "school", "booked_by")
                .prefetch_related("additional_students")
                .get(pk=pk)
            )
        except ClassSchedule.DoesNotExist:
            from django.http import Http404

            raise Http404

    def create(self, request, *args, **kwargs):
        """Create a new class schedule with enhanced booking logic"""
        user = request.user

        # Early permission checks before serializer validation
        if hasattr(user, "teacher_profile"):
            # Teachers cannot book classes
            raise PermissionDenied("Teachers cannot book classes")

        # Check school membership permission early
        school_id = request.data.get("school")
        if school_id:
            # Import School model here to avoid circular import
            from accounts.models import School

            try:
                school = School.objects.get(id=school_id)
                if not SchoolMembership.objects.filter(user=user, school=school, is_active=True).exists():
                    raise PermissionDenied("You don't have permission to book classes in this school")
            except School.DoesNotExist:
                # Let serializer validation handle invalid school ID
                pass

        # Now validate the data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = serializer.validated_data.get("student")

        # Students can only book classes for themselves, unless user is a school admin
        is_admin = SchoolMembership.objects.filter(
            user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
        ).exists()

        if not is_admin and student != user:
            raise PermissionDenied("Students can only book classes for themselves")

        # Final school permission check with validated data
        school = serializer.validated_data.get("school")
        if not SchoolMembership.objects.filter(user=user, school=school, is_active=True).exists():
            raise PermissionDenied("You don't have permission to book classes in this school")

        # Set the student to current user if not provided (for backward compatibility)
        if not student and not is_admin:
            serializer.validated_data["student"] = user

        # The actual booking creation is now handled by the serializer's create method
        # which uses BookingOrchestratorService
        instance = serializer.save()

        # Return the instance serialized with the full ClassScheduleSerializer
        headers = self.get_success_headers(serializer.data)
        return Response(
            ClassScheduleSerializer(instance, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        """Update a class schedule with permission checks"""
        user = request.user

        # Use custom get_object to avoid queryset filtering for permission checking
        instance = self.get_object_for_permissions()

        # Check permissions - only admins and teachers can update classes
        if hasattr(user, "teacher_profile"):
            # Teachers can only update their own classes
            if instance.teacher != user.teacher_profile:
                raise PermissionDenied("Teachers can only update their own classes")
        else:
            # Check if user is admin
            is_admin = SchoolMembership.objects.filter(
                user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
            ).exists()
            if not is_admin:
                raise PermissionDenied("Students cannot update class schedules")

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partial update a class schedule with permission checks"""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a class schedule with permission checks"""
        user = request.user

        # Use custom get_object to avoid queryset filtering for permission checking
        self.get_object_for_permissions()

        # Check permissions - only admins can delete classes
        is_admin = SchoolMembership.objects.filter(
            user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
        ).exists()

        if not is_admin:
            raise PermissionDenied("Only administrators can delete class schedules")

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a class"""
        from .services import ClassPermissionService, ClassStatusTransitionService

        # Use custom get_object to avoid queryset filtering for permission checking
        class_schedule = self.get_object_for_permissions()
        user = request.user

        # Check permissions
        permission_service = ClassPermissionService()
        if not permission_service.can_cancel_class(class_schedule, user):
            return Response(
                {"error": "You don't have permission to cancel this class"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate request data
        serializer = CancelClassSerializer(data=request.data)
        if serializer.is_valid():
            reason = serializer.validated_data.get("reason", "")

            # Check and execute status transition
            transition_service = ClassStatusTransitionService()
            try:
                transition_service.cancel_class(class_schedule, user, reason)
                return Response({"message": "Class cancelled successfully"}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm a scheduled class"""
        from .services import ClassPermissionService, ClassStatusTransitionService

        # Use custom get_object to avoid queryset filtering for permission checking
        class_schedule = self.get_object_for_permissions()
        user = request.user

        # Check permissions
        permission_service = ClassPermissionService()
        if not permission_service.can_confirm_class(class_schedule, user):
            return Response(
                {"error": "You don't have permission to confirm this class"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check and execute status transition
        transition_service = ClassStatusTransitionService()
        try:
            transition_service.confirm_class(class_schedule, user)
            return Response({"message": "Class confirmed successfully"}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark a class as completed"""
        from .services import ClassCompletionOrchestratorService

        # Use custom get_object to avoid queryset filtering for permission checking
        class_schedule = self.get_object_for_permissions()
        user = request.user

        # Extract optional parameters
        actual_duration_minutes = request.data.get("actual_duration_minutes")
        notes = request.data.get("notes", "")

        # Validate actual_duration_minutes if provided
        if actual_duration_minutes is not None:
            try:
                actual_duration_minutes = int(actual_duration_minutes)
            except (ValueError, TypeError):
                return Response(
                    {"error": "actual_duration_minutes must be a valid integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Use orchestrator service for completion
        orchestrator = ClassCompletionOrchestratorService()
        try:
            orchestrator.complete_class(class_schedule, user, actual_duration_minutes, notes)
            return Response({"message": "Class marked as completed successfully"}, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def no_show(self, request, pk=None):
        """Mark a class as no-show"""
        from .services import ClassCompletionOrchestratorService

        # Use custom get_object to avoid queryset filtering for permission checking
        class_schedule = self.get_object_for_permissions()
        user = request.user

        # Extract required and optional parameters
        reason = request.data.get("reason", "").strip()
        notes = request.data.get("notes", "")
        no_show_type = request.data.get("no_show_type", "student")

        # Use orchestrator service for no-show marking (handles all validation)
        orchestrator = ClassCompletionOrchestratorService()
        try:
            orchestrator.mark_no_show(class_schedule, user, reason, no_show_type, notes)
            return Response({"message": "Class marked as no-show successfully"}, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject a scheduled class"""
        from .services import ClassPermissionService, ClassStatusTransitionService

        # Use custom get_object to avoid queryset filtering for permission checking
        class_schedule = self.get_object_for_permissions()
        user = request.user

        # Check permissions
        permission_service = ClassPermissionService()
        if not permission_service.can_reject_class(class_schedule, user):
            return Response(
                {"error": "You don't have permission to reject this class"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check and execute status transition
        transition_service = ClassStatusTransitionService()
        try:
            transition_service.reject_class(class_schedule, user)
            return Response({"message": "Class rejected successfully"}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
                {"error": "teacher_id and date are required parameters"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Extract optional parameters
        duration_minutes = request.query_params.get("duration_minutes", 60)
        date_end_str = request.query_params.get("date_end")

        try:
            # Validate teacher exists
            teacher = TeacherProfile.objects.select_related("user").get(id=teacher_id)

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
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Get user's accessible schools
        user_schools = self.get_user_schools()

        # Validate that the teacher belongs to at least one of the user's accessible schools
        from accounts.models import SchoolMembership

        teacher_schools = SchoolMembership.objects.filter(user=teacher.user, is_active=True).values_list(
            "school_id", flat=True
        )

        # Check if there's any overlap between user's schools and teacher's schools
        common_schools = set(user_schools.values_list("id", flat=True)) & set(teacher_schools)
        if not common_schools:
            return Response(
                {"error": "You don't have permission to view this teacher's availability"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Only use the schools that are accessible to both user and teacher
        accessible_schools = user_schools.filter(id__in=common_schools)

        # Initialize service and calculate slots
        service = AvailableSlotsService(teacher=teacher, schools=accessible_schools)

        try:
            available_slots = service.get_available_slots(
                start_date=start_date, duration_minutes=duration_minutes, end_date=end_date
            )

            # Return response in the exact format specified in issue #148
            return Response({"available_slots": available_slots})

        except Exception as e:
            # Log error for debugging (using Django's logging framework)
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating available slots for teacher {teacher_id} on {date_str}: {e!s}")

            return Response(
                {"error": "Unable to calculate available slots"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"])
    def reminders(self, request, pk=None):
        """Get reminders for a specific class"""
        class_schedule = self.get_object()

        reminders = (
            ClassReminder.objects.filter(class_schedule=class_schedule)
            .select_related("recipient")
            .order_by("-created_at")
        )

        serializer = ClassReminderSerializer(reminders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def trigger_reminder(self, request, pk=None):
        """Manually trigger a reminder for a class"""
        try:
            from .reminder_services import (
                RecipientDeterminationService,
                ReminderService,
            )
        except ImportError:
            # Fallback if services not yet implemented
            return Response({"error": "Reminder services not available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        from django.utils import timezone

        class_schedule = self.get_object()
        user = request.user

        # Check permissions - only admins and teachers can trigger reminders
        if hasattr(user, "teacher_profile"):
            # Teachers can only trigger for their own classes
            if class_schedule.teacher != user.teacher_profile:
                raise PermissionDenied("You can only trigger reminders for your own classes")
        else:
            # Check if user is admin
            is_admin = SchoolMembership.objects.filter(
                user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
            ).exists()
            if not is_admin:
                raise PermissionDenied("Only teachers and admins can trigger reminders")

        # Validate request data
        serializer = TriggerReminderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reminder_type = serializer.validated_data["reminder_type"]
        custom_message = serializer.validated_data.get("message", "")
        custom_channels = serializer.validated_data.get("channels", [])
        custom_subject = serializer.validated_data.get("subject", "")

        # Prevent duplicate reminders for non-custom types
        if reminder_type != "custom":
            existing = ClassReminder.objects.filter(
                class_schedule=class_schedule, reminder_type=reminder_type, status__in=["sent", "pending"]
            ).exists()

            if existing:
                return Response({"error": "duplicate"}, status=status.HTTP_409_CONFLICT)

        # Check if class is in the past
        if class_schedule.is_past:
            return Response({"error": "past class"}, status=status.HTTP_400_BAD_REQUEST)

        # Determine recipients and send reminders
        recipients = RecipientDeterminationService.determine_recipients(class_schedule, reminder_type)

        reminders_sent = 0
        failed_count = 0

        for recipient_data in recipients:
            recipient_user = recipient_data["user"]
            channels = custom_channels if custom_channels else recipient_data["channels"]

            for channel in channels:
                try:
                    reminder = ClassReminder.objects.create(
                        class_schedule=class_schedule,
                        reminder_type=reminder_type,
                        recipient=recipient_user,
                        recipient_type=recipient_data["role"],
                        communication_channel=channel,
                        scheduled_for=timezone.now(),
                        subject=custom_subject
                        or f"Class {reminder_type.replace('_', ' ').title()}: {class_schedule.title}",
                        message=custom_message or f"Reminder for your class: {class_schedule.title}",
                        metadata={"triggered_by": user.id, "triggered_manually": True},
                    )

                    success = ReminderService.send_reminder(reminder)
                    if success:
                        reminders_sent += 1
                    else:
                        failed_count += 1
                except Exception:
                    failed_count += 1

        # Prepare response with communication status
        response_data = {
            "message": "Reminder process completed",
            "reminders_sent": reminders_sent,
            "failed_notifications": failed_count,
            "notifications_sent": reminders_sent,
            "communication_status": "success"
            if failed_count == 0
            else ("failed" if reminders_sent == 0 else "partial_failure"),
        }

        if failed_count > 0:
            response_data["communication_error"] = f"Failed to send {failed_count} notifications"
            response_data["retry_attempts"] = 1

        return Response(response_data, status=status.HTTP_200_OK)


class RecurringClassScheduleViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing recurring class schedules"""

    serializer_class = RecurringClassScheduleSerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        user_schools = self.get_user_schools()
        user = self.request.user

        queryset = (
            RecurringClassSchedule.objects.filter(school__in=user_schools)
            .select_related("teacher__user", "school", "created_by", "cancelled_by", "paused_by")
            .prefetch_related("students")
        )

        # Filter based on user role
        if hasattr(user, "teacher_profile"):
            # Teachers can only see their own recurring schedules
            queryset = queryset.filter(teacher=user.teacher_profile)
        elif not user.is_admin:
            # Students can only see recurring schedules they're participating in
            queryset = queryset.filter(students=user)

        # Apply filters from query parameters
        teacher_id = self.request.query_params.get("teacher")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        student_id = self.request.query_params.get("student")
        if student_id:
            queryset = queryset.filter(students=student_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        frequency_type = self.request.query_params.get("frequency_type")
        if frequency_type:
            queryset = queryset.filter(frequency_type=frequency_type.upper())

        return queryset.order_by("day_of_week", "start_time")

    def perform_create(self, serializer):
        """Create recurring schedule with permission checks"""
        user = self.request.user

        # Permission checks
        if hasattr(user, "teacher_profile"):
            # Teachers cannot create recurring schedules
            raise PermissionDenied("Teachers cannot create recurring schedules")

        # Only admins can create recurring schedules
        if not user.is_admin:
            raise PermissionDenied("Only admins can create recurring schedules")

        serializer.save()

    def perform_update(self, serializer):
        """Update recurring schedule with permission checks"""
        user = self.request.user

        # Only admins can update recurring schedules
        if not user.is_admin:
            raise PermissionDenied("Only admins can update recurring schedules")

        serializer.save()

    def perform_destroy(self, instance):
        """Override destroy to soft delete (cancel) the recurring series"""
        user = self.request.user

        # Only admins can delete recurring schedules
        if not user.is_admin:
            raise PermissionDenied("Only admins can delete recurring schedules")

        # Use cancel_series for soft delete instead of hard delete
        instance.cancel_series(reason="Series deleted via API", cancelled_by=user)

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return cancelled series data instead of 204"""
        instance = self.get_object()
        self.perform_destroy(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def generate_schedules(self, request, pk=None):
        """Generate individual class schedules from recurring schedule"""
        from .serializers import GenerateRecurringSchedulesSerializer

        recurring_schedule = self.get_object()

        # Validate request data
        serializer = GenerateRecurringSchedulesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        weeks_ahead = serializer.validated_data.get("weeks_ahead", 4)
        serializer.validated_data.get("skip_existing", True)

        created_schedules = recurring_schedule.generate_instances(weeks_ahead)

        return Response(
            {
                "message": f"Generated {len(created_schedules)} class schedules",
                "created_schedules": [schedule.id for schedule in created_schedules],
                "weeks_ahead": weeks_ahead,
            }
        )

    @action(detail=True, methods=["post"])
    def cancel_instance(self, request, pk=None):
        """Cancel a specific occurrence of the recurring class"""
        from .serializers import CancelRecurringInstanceSerializer

        recurring_schedule = self.get_object()

        # Only admins can cancel instances
        if not request.user.is_admin:
            raise PermissionDenied("Only admins can cancel recurring class instances")

        # Validate request data
        serializer = CancelRecurringInstanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        date = serializer.validated_data["date"]
        reason = serializer.validated_data.get("reason", "")

        try:
            result = recurring_schedule.cancel_occurrence(date=date, reason=reason, cancelled_by=request.user)
            return Response(result)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_student(self, request, pk=None):
        """Add a student to the recurring class"""
        from accounts.models import CustomUser

        from .serializers import AddStudentToRecurringSerializer

        recurring_schedule = self.get_object()

        # Only admins can manage students
        if not request.user.is_admin:
            raise PermissionDenied("Only admins can manage students in recurring classes")

        # Validate request data
        serializer = AddStudentToRecurringSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data["student_id"]

        try:
            student = CustomUser.objects.get(id=student_id)
            recurring_schedule.add_student(student)

            # Return updated recurring schedule data
            response_serializer = RecurringClassScheduleSerializer(recurring_schedule)
            return Response(response_serializer.data)

        except CustomUser.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def remove_student(self, request, pk=None):
        """Remove a student from the recurring class"""
        from accounts.models import CustomUser

        from .serializers import RemoveStudentFromRecurringSerializer

        recurring_schedule = self.get_object()

        # Only admins can manage students
        if not request.user.is_admin:
            raise PermissionDenied("Only admins can manage students in recurring classes")

        # Validate request data
        serializer = RemoveStudentFromRecurringSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data["student_id"]

        try:
            student = CustomUser.objects.get(id=student_id)
            recurring_schedule.remove_student(student)

            # Return updated recurring schedule data
            response_serializer = RecurringClassScheduleSerializer(recurring_schedule)
            return Response(response_serializer.data)

        except CustomUser.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReminderPreferenceViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing user reminder preferences"""

    serializer_class = ReminderPreferenceSerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        """Return user's own reminder preferences"""
        return (
            ReminderPreference.objects.filter(user=self.request.user)
            .select_related("user", "school")
            .order_by("school", "created_at")
        )

    def perform_create(self, serializer):
        """Create preferences for the current user"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Ensure users can only update their own preferences"""
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only update your own preferences")
        serializer.save()


class ClassReminderViewSet(SchoolPermissionMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing class reminders"""

    serializer_class = ClassReminderSerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        """Return reminders based on user role"""
        user = self.request.user
        user_schools = self.get_user_schools()

        # Base queryset for user's schools
        queryset = ClassReminder.objects.filter(class_schedule__school__in=user_schools).select_related(
            "class_schedule__teacher__user", "class_schedule__student", "class_schedule__school", "recipient"
        )

        # Filter based on user role
        if hasattr(user, "teacher_profile"):
            # Teachers see reminders for their classes
            queryset = queryset.filter(class_schedule__teacher=user.teacher_profile)
        else:
            # Check if user is admin
            is_admin = SchoolMembership.objects.filter(
                user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
            ).exists()

            if not is_admin:
                # Students see only their own reminders
                queryset = queryset.filter(recipient=user)
            # Admins can see all reminders in their schools

        # Apply filters
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        reminder_type = self.request.query_params.get("reminder_type")
        if reminder_type:
            queryset = queryset.filter(reminder_type=reminder_type)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(scheduled_for__date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(scheduled_for__date__lte=date_to)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(class_schedule__title__icontains=search) | Q(message__icontains=search) | Q(subject__icontains=search)
            )

        return queryset.order_by("-scheduled_for")


class UserRemindersViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user's own reminders"""

    serializer_class = ClassReminderSerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        """Return only current user's reminders"""
        return (
            ClassReminder.objects.filter(recipient=self.request.user)
            .select_related("class_schedule__teacher__user", "class_schedule__student", "class_schedule__school")
            .order_by("-scheduled_for")
        )


class ReminderQueueViewSet(viewsets.ViewSet):
    """ViewSet for managing reminder queue (admin only)"""

    permission_classes: ClassVar = [IsAuthenticated]

    def list(self, request):
        """Get reminder queue status"""
        # Check admin permissions
        is_admin = SchoolMembership.objects.filter(
            user=request.user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
        ).exists()

        if not is_admin:
            raise PermissionDenied("Only admins can access reminder queue status")

        from .reminder_services import ReminderBackgroundTaskService

        status_data = ReminderBackgroundTaskService.get_queue_health_status()

        # Format for API response
        response_data = {
            "pending_reminders": status_data["pending_reminders_count"],
            "processing_reminders": 0,  # Mock value
            "failed_reminders": status_data["failed_reminders_count"],
            "last_processed_at": status_data["last_processed_at"],
            "queue_health": status_data["queue_status"],
            "worker_status": status_data["worker_status"],
        }

        return Response(response_data)

    @action(detail=False, methods=["post"])
    def process(self, request):
        """Process reminder queue"""
        # Check admin permissions
        is_admin = SchoolMembership.objects.filter(
            user=request.user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
        ).exists()

        if not is_admin:
            raise PermissionDenied("Only admins can process reminder queue")

        from .reminder_services import ReminderBackgroundTaskService

        # Validate request data
        serializer = ProcessReminderQueueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        batch_size = serializer.validated_data.get("batch_size", 50)
        max_batches = serializer.validated_data.get("max_batches", 10)

        # Process queue
        import time

        start_time = time.time()

        result = ReminderBackgroundTaskService.process_reminder_queue(batch_size=batch_size, max_batches=max_batches)

        processing_time = time.time() - start_time

        response_data = {
            "message": "Queue processing completed",
            "processed_count": result["total_processed"],
            "failed_count": result["total_failed"],
            "skipped_count": 0,  # Mock value
            "processing_time_seconds": round(processing_time, 2),
            "errors": result["errors"],
        }

        return Response(response_data)
