from datetime import datetime, timedelta
from typing import ClassVar

from accounts.models import SchoolMembership, TeacherProfile
from accounts.permissions import SchoolPermissionMixin
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
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

    def perform_create(self, serializer):
        """Ensure teacher and school are valid"""
        # Only teachers can create their own availability
        user = self.request.user
        if hasattr(user, "teacher_profile"):
            serializer.save(teacher=user.teacher_profile)
        else:
            # Admin can create availability for any teacher
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

    def perform_create(self, serializer):
        """Ensure teacher and school are valid"""
        # Only teachers can create their own unavailability
        user = self.request.user
        if hasattr(user, "teacher_profile"):
            serializer.save(teacher=user.teacher_profile)
        else:
            # Admin can create unavailability for any teacher
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
        elif not user.is_admin:
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
        """Create class schedule with permission checks"""
        user = self.request.user

        # Permission checks
        if hasattr(user, "teacher_profile"):
            # Teachers cannot book classes
            raise PermissionError("Teachers cannot book classes")

        student = serializer.validated_data.get("student")

        # Students can only book classes for themselves
        if not user.is_admin and student != user:
            raise PermissionError("Students can only book classes for themselves")

        # Ensure user has permission to book in this school
        school = serializer.validated_data.get("school")
        if not SchoolMembership.objects.filter(user=user, school=school, is_active=True).exists():
            raise PermissionError("You don't have permission to book classes in this school")

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
        """Get available time slots for a teacher on a specific date"""
        teacher_id = request.query_params.get("teacher_id")
        date_str = request.query_params.get("date")

        if not teacher_id or not date_str:
            return Response(
                {"error": "teacher_id and date are required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            teacher = TeacherProfile.objects.get(id=teacher_id)
        except (ValueError, TeacherProfile.DoesNotExist):
            return Response(
                {"error": "Invalid teacher_id or date format"}, status=status.HTTP_400_BAD_REQUEST
            )

        user_schools = self.get_user_schools()
        available_slots = []

        for school in user_schools:
            # Get teacher's availability for this day
            day_of_week = date.strftime("%A").lower()
            availability = TeacherAvailability.objects.filter(
                teacher=teacher, school=school, day_of_week=day_of_week, is_active=True
            ).first()

            if not availability:
                continue

            # Check for unavailability
            unavailability = TeacherUnavailability.objects.filter(
                teacher=teacher, school=school, date=date
            ).first()

            if unavailability and unavailability.is_all_day:
                continue

            # Get existing classes for this day
            existing_classes = ClassSchedule.objects.filter(
                teacher=teacher,
                school=school,
                scheduled_date=date,
                status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
            ).values_list("start_time", "end_time")

            # Generate available slots (assuming 1-hour slots)
            current_time = availability.start_time
            end_time = availability.end_time

            while current_time < end_time:
                slot_end = (datetime.combine(date, current_time) + timedelta(hours=1)).time()
                if slot_end > end_time:
                    break

                # Check if this slot conflicts with existing classes
                slot_available = True
                for start, end in existing_classes:
                    if current_time < end and slot_end > start:
                        slot_available = False
                        break

                # Check if this slot conflicts with unavailability
                if unavailability and not unavailability.is_all_day:
                    if (
                        current_time < unavailability.end_time
                        and slot_end > unavailability.start_time
                    ):
                        slot_available = False

                if slot_available:
                    available_slots.append(
                        {
                            "start_time": current_time.strftime("%H:%M"),
                            "end_time": slot_end.strftime("%H:%M"),
                            "school_id": school.id,
                            "school_name": school.name,
                        }
                    )

                current_time = slot_end

        return Response(
            {"teacher_id": teacher_id, "date": date_str, "available_slots": available_slots}
        )


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
            raise PermissionError("Teachers cannot create recurring schedules")

        student = serializer.validated_data.get("student")

        # Students can only create recurring schedules for themselves
        if not user.is_admin and student != user:
            raise PermissionError("Students can only create recurring schedules for themselves")

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
