import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import SchoolMembership, SchoolRole, TeacherProfile

from .models import (
    ClassReminder,
    ClassSchedule,
    RecurringClassSchedule,
    ReminderPreference,
    TeacherAvailability,
    TeacherUnavailability,
)


# Utility functions for Django view migration (replacing DRF serializers)
def get_user_schools(user):
    """Get schools where user has membership"""
    return [membership.school for membership in user.school_memberships.filter(is_active=True)]


def ensure_school_access(user, school):
    """Ensure user has access to the school"""
    user_schools = get_user_schools(user)
    if school not in user_schools:
        return False
    return True


def serialize_teacher_availability(availability):
    """Serialize TeacherAvailability instance to dict"""
    return {
        'id': availability.id,
        'teacher': {
            'id': availability.teacher.id,
            'name': availability.teacher.user.name,
            'email': availability.teacher.user.email
        },
        'school': {
            'id': availability.school.id,
            'name': availability.school.name
        },
        'day_of_week': availability.day_of_week,
        'day_of_week_display': availability.get_day_of_week_display(),
        'start_time': availability.start_time.strftime('%H:%M'),
        'end_time': availability.end_time.strftime('%H:%M'),
        'is_active': availability.is_active,
        'created_at': availability.created_at.isoformat(),
        'updated_at': availability.updated_at.isoformat()
    }


def serialize_teacher_unavailability(unavailability):
    """Serialize TeacherUnavailability instance to dict"""
    return {
        'id': unavailability.id,
        'teacher': {
            'id': unavailability.teacher.id,
            'name': unavailability.teacher.user.name,
            'email': unavailability.teacher.user.email
        },
        'school': {
            'id': unavailability.school.id,
            'name': unavailability.school.name
        },
        'date': unavailability.date.isoformat(),
        'start_time': unavailability.start_time.strftime('%H:%M') if unavailability.start_time else None,
        'end_time': unavailability.end_time.strftime('%H:%M') if unavailability.end_time else None,
        'reason': unavailability.reason,
        'is_all_day': unavailability.is_all_day,
        'created_at': unavailability.created_at.isoformat()
    }


def serialize_class_schedule(schedule):
    """Serialize ClassSchedule instance to dict"""
    return {
        'id': schedule.id,
        'teacher': {
            'id': schedule.teacher.id,
            'name': schedule.teacher.user.name,
            'email': schedule.teacher.user.email
        },
        'student': {
            'id': schedule.student.id,
            'name': schedule.student.name,
            'email': schedule.student.email
        },
        'school': {
            'id': schedule.school.id,
            'name': schedule.school.name
        },
        'title': schedule.title,
        'description': schedule.description,
        'class_type': schedule.class_type,
        'class_type_display': schedule.get_class_type_display(),
        'status': schedule.status,
        'status_display': schedule.get_status_display(),
        'scheduled_date': schedule.scheduled_date.isoformat(),
        'start_time': schedule.start_time.strftime('%H:%M'),
        'end_time': schedule.end_time.strftime('%H:%M'),
        'duration_minutes': schedule.duration_minutes,
        'booked_by': {
            'id': schedule.booked_by.id,
            'name': schedule.booked_by.name,
            'email': schedule.booked_by.email
        },
        'booked_at': schedule.booked_at.isoformat(),
        'additional_students': [
            {'id': student.id, 'name': student.name, 'email': student.email}
            for student in schedule.additional_students.all()
        ],
        'max_participants': schedule.max_participants,
        'metadata': schedule.metadata,
        'teacher_notes': schedule.teacher_notes,
        'student_notes': schedule.student_notes,
        'created_at': schedule.created_at.isoformat(),
        'updated_at': schedule.updated_at.isoformat()
    }


def serialize_recurring_schedule(recurring):
    """Serialize RecurringClassSchedule instance to dict"""
    return {
        'id': recurring.id,
        'teacher': {
            'id': recurring.teacher.id,
            'name': recurring.teacher.user.name,
            'email': recurring.teacher.user.email
        },
        'students': [
            {'id': student.id, 'name': student.name, 'email': student.email}
            for student in recurring.students.all()
        ],
        'school': {
            'id': recurring.school.id,
            'name': recurring.school.name
        },
        'title': recurring.title,
        'description': recurring.description,
        'class_type': recurring.class_type,
        'class_type_display': recurring.get_class_type_display(),
        'frequency_type': recurring.frequency_type,
        'frequency_type_display': recurring.get_frequency_type_display(),
        'status': recurring.status,
        'status_display': recurring.get_status_display(),
        'max_participants': recurring.max_participants,
        'day_of_week': recurring.day_of_week,
        'day_of_week_display': recurring.get_day_of_week_display(),
        'start_time': recurring.start_time.strftime('%H:%M'),
        'end_time': recurring.end_time.strftime('%H:%M'),
        'duration_minutes': recurring.duration_minutes,
        'start_date': recurring.start_date.isoformat(),
        'end_date': recurring.end_date.isoformat() if recurring.end_date else None,
        'is_active': recurring.is_active,
        'created_by': {
            'id': recurring.created_by.id,
            'name': recurring.created_by.name,
            'email': recurring.created_by.email
        },
        'created_at': recurring.created_at.isoformat(),
        'updated_at': recurring.updated_at.isoformat()
    }


def serialize_reminder_preference(preference):
    """Serialize ReminderPreference instance to dict"""
    return {
        'id': preference.id,
        'user': {
            'id': preference.user.id,
            'name': preference.user.name,
            'email': preference.user.email
        },
        'school': {
            'id': preference.school.id,
            'name': preference.school.name
        } if preference.school else None,
        'reminder_timing_hours': preference.reminder_timing_hours,
        'communication_channels': preference.communication_channels,
        'timezone_preference': preference.timezone_preference,
        'is_active': preference.is_active,
        'is_school_default': preference.is_school_default,
        'created_at': preference.created_at.isoformat(),
        'updated_at': preference.updated_at.isoformat()
    }


def serialize_class_reminder(reminder):
    """Serialize ClassReminder instance to dict"""
    return {
        'id': reminder.id,
        'class_schedule': {
            'id': reminder.class_schedule.id,
            'title': reminder.class_schedule.title,
            'scheduled_date': reminder.class_schedule.scheduled_date.isoformat(),
            'start_time': reminder.class_schedule.start_time.strftime('%H:%M')
        },
        'reminder_type': reminder.reminder_type,
        'reminder_type_display': reminder.get_reminder_type_display(),
        'recipient': {
            'id': reminder.recipient.id,
            'name': reminder.recipient.name,
            'email': reminder.recipient.email
        },
        'recipient_type': reminder.recipient_type,
        'communication_channel': reminder.communication_channel,
        'communication_channel_display': reminder.get_communication_channel_display(),
        'status': reminder.status,
        'status_display': reminder.get_status_display(),
        'scheduled_for': reminder.scheduled_for.isoformat(),
        'sent_at': reminder.sent_at.isoformat() if reminder.sent_at else None,
        'subject': reminder.subject,
        'message': reminder.message,
        'error_message': reminder.error_message,
        'retry_count': reminder.retry_count,
        'max_retries': reminder.max_retries,
        'metadata': reminder.metadata,
        'created_at': reminder.created_at.isoformat(),
        'updated_at': reminder.updated_at.isoformat()
    }


# Django views for teacher availability (replacing DRF)
@method_decorator(login_required, name='dispatch')
class TeacherAvailabilityView(View):
    """Handle teacher availability CRUD operations"""

    def get(self, request, availability_id=None):
        """List availabilities or get specific availability"""
        user_schools = get_user_schools(request.user)

        if availability_id:
            # Get specific availability
            try:
                availability = TeacherAvailability.objects.select_related("teacher__user", "school").get(
                    id=availability_id, school__in=user_schools
                )
                return JsonResponse(serialize_teacher_availability(availability))
            except TeacherAvailability.DoesNotExist:
                return JsonResponse({'error': 'Availability not found'}, status=404)

        # List availabilities with filtering
        queryset = TeacherAvailability.objects.filter(school__in=user_schools).select_related("teacher__user", "school")

        # Filter by teacher if specified
        teacher_id = request.GET.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        availabilities = queryset.order_by("day_of_week", "start_time")
        data = [serialize_teacher_availability(availability) for availability in availabilities]
        return JsonResponse({'results': data})

    def post(self, request):
        """Create new teacher availability"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # If teacher is not provided and user has teacher_profile, set it automatically
        if ("teacher" not in data or data["teacher"] is None) and hasattr(request.user, "teacher_profile"):
            data["teacher"] = request.user.teacher_profile.id

        try:
            teacher_id = data.get('teacher')
            school_id = data.get('school')

            # Validate teacher and school
            if not teacher_id or not school_id:
                return JsonResponse({'error': 'Teacher and school are required'}, status=400)

            teacher = TeacherProfile.objects.get(id=teacher_id)
            # Ensure teacher belongs to this school through SchoolMembership
            school_membership = SchoolMembership.objects.get(
                user=teacher.user, school_id=school_id, is_active=True
            )
            school = school_membership.school

            # Ensure user has access to this school
            if not ensure_school_access(request.user, school):
                return JsonResponse({'error': 'Permission denied'}, status=403)

            # Create availability
            availability = TeacherAvailability.objects.create(
                teacher=teacher,
                school=school,
                day_of_week=data.get('day_of_week'),
                start_time=data.get('start_time'),
                end_time=data.get('end_time'),
                is_active=data.get('is_active', True)
            )

            return JsonResponse(serialize_teacher_availability(availability), status=201)

        except (TeacherProfile.DoesNotExist, ValidationError) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to create availability'}, status=500)

    def put(self, request, availability_id):
        """Update teacher availability"""
        return self._update_availability(request, availability_id, partial=False)

    def patch(self, request, availability_id):
        """Partially update teacher availability"""
        return self._update_availability(request, availability_id, partial=True)

    def delete(self, request, availability_id):
        """Delete teacher availability"""
        user_schools = get_user_schools(request.user)

        try:
            availability = TeacherAvailability.objects.get(id=availability_id, school__in=user_schools)

            # Check permissions - only the teacher themselves or admins can delete
            if hasattr(request.user, "teacher_profile"):
                if availability.teacher != request.user.teacher_profile:
                    return JsonResponse({'error': 'Teachers can only delete their own availability'}, status=403)
            else:
                is_admin = SchoolMembership.objects.filter(
                    user=request.user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
                ).exists()
                if not is_admin:
                    return JsonResponse({'error': 'Only teachers and administrators can delete availability'}, status=403)

            availability.delete()
            return JsonResponse({'message': 'Availability deleted successfully'})

        except TeacherAvailability.DoesNotExist:
            return JsonResponse({'error': 'Availability not found'}, status=404)

    def _update_availability(self, request, availability_id, partial=False):
        """Helper method to update availability"""
        user_schools = get_user_schools(request.user)

        try:
            data = json.loads(request.body)
            availability = TeacherAvailability.objects.get(id=availability_id, school__in=user_schools)

            # Check permissions - only the teacher themselves or admins can update
            if hasattr(request.user, "teacher_profile"):
                if availability.teacher != request.user.teacher_profile:
                    return JsonResponse({'error': 'Teachers can only update their own availability'}, status=403)
            else:
                is_admin = SchoolMembership.objects.filter(
                    user=request.user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
                ).exists()
                if not is_admin:
                    return JsonResponse({'error': 'Only teachers and administrators can update availability'}, status=403)

            # Update fields
            if 'day_of_week' in data:
                availability.day_of_week = data['day_of_week']
            if 'start_time' in data:
                availability.start_time = data['start_time']
            if 'end_time' in data:
                availability.end_time = data['end_time']
            if 'is_active' in data:
                availability.is_active = data['is_active']

            availability.save()
            return JsonResponse(serialize_teacher_availability(availability))

        except (TeacherAvailability.DoesNotExist, json.JSONDecodeError, ValidationError) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to update availability'}, status=500)


# Django views for teacher unavailability (replacing DRF)
@method_decorator(login_required, name='dispatch')
class TeacherUnavailabilityView(View):
    """Handle teacher unavailability CRUD operations"""

    def get(self, request, unavailability_id=None):
        """List unavailabilities or get specific unavailability"""
        user_schools = get_user_schools(request.user)

        if unavailability_id:
            # Get specific unavailability
            try:
                unavailability = TeacherUnavailability.objects.select_related("teacher__user", "school").get(
                    id=unavailability_id, school__in=user_schools
                )
                return JsonResponse(serialize_teacher_unavailability(unavailability))
            except TeacherUnavailability.DoesNotExist:
                return JsonResponse({'error': 'Unavailability not found'}, status=404)

        # List unavailabilities with filtering
        queryset = TeacherUnavailability.objects.filter(school__in=user_schools).select_related("teacher__user", "school")

        # Filter by teacher if specified
        teacher_id = request.GET.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        unavailabilities = queryset.order_by("date", "start_time")
        data = [serialize_teacher_unavailability(unavailability) for unavailability in unavailabilities]
        return JsonResponse({'results': data})

    def post(self, request):
        """Create new teacher unavailability"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # If teacher is not provided and user has teacher_profile, set it automatically
        if ("teacher" not in data or data["teacher"] is None) and hasattr(request.user, "teacher_profile"):
            data["teacher"] = request.user.teacher_profile.id

        try:
            teacher_id = data.get('teacher')
            school_id = data.get('school')

            # Validate teacher and school
            if not teacher_id or not school_id:
                return JsonResponse({'error': 'Teacher and school are required'}, status=400)

            teacher = TeacherProfile.objects.get(id=teacher_id)
            # Ensure teacher belongs to this school through SchoolMembership
            school_membership = SchoolMembership.objects.get(
                user=teacher.user, school_id=school_id, is_active=True
            )
            school = school_membership.school

            # Ensure user has access to this school
            if not ensure_school_access(request.user, school):
                return JsonResponse({'error': 'Permission denied'}, status=403)

            # Create unavailability
            unavailability = TeacherUnavailability.objects.create(
                teacher=teacher,
                school=school,
                date=data.get('date'),
                start_time=data.get('start_time'),
                end_time=data.get('end_time'),
                reason=data.get('reason', ''),
                is_all_day=data.get('is_all_day', False)
            )

            return JsonResponse(serialize_teacher_unavailability(unavailability), status=201)

        except (TeacherProfile.DoesNotExist, ValidationError) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to create unavailability'}, status=500)

    def put(self, request, unavailability_id):
        """Update teacher unavailability"""
        return self._update_unavailability(request, unavailability_id, partial=False)

    def patch(self, request, unavailability_id):
        """Partially update teacher unavailability"""
        return self._update_unavailability(request, unavailability_id, partial=True)

    def delete(self, request, unavailability_id):
        """Delete teacher unavailability"""
        user_schools = get_user_schools(request.user)

        try:
            unavailability = TeacherUnavailability.objects.get(id=unavailability_id, school__in=user_schools)

            # Check permissions - only the teacher themselves or admins can delete
            if hasattr(request.user, "teacher_profile"):
                if unavailability.teacher != request.user.teacher_profile:
                    return JsonResponse({'error': 'Teachers can only delete their own unavailability'}, status=403)
            else:
                is_admin = SchoolMembership.objects.filter(
                    user=request.user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
                ).exists()
                if not is_admin:
                    return JsonResponse({'error': 'Only teachers and administrators can delete unavailability'}, status=403)

            unavailability.delete()
            return JsonResponse({'message': 'Unavailability deleted successfully'})

        except TeacherUnavailability.DoesNotExist:
            return JsonResponse({'error': 'Unavailability not found'}, status=404)

    def _update_unavailability(self, request, unavailability_id, partial=False):
        """Helper method to update unavailability"""
        user_schools = get_user_schools(request.user)

        try:
            data = json.loads(request.body)
            unavailability = TeacherUnavailability.objects.get(id=unavailability_id, school__in=user_schools)

            # Check permissions - only the teacher themselves or admins can update
            if hasattr(request.user, "teacher_profile"):
                if unavailability.teacher != request.user.teacher_profile:
                    return JsonResponse({'error': 'Teachers can only update their own unavailability'}, status=403)
            else:
                is_admin = SchoolMembership.objects.filter(
                    user=request.user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
                ).exists()
                if not is_admin:
                    return JsonResponse({'error': 'Only teachers and administrators can update unavailability'}, status=403)

            # Update fields
            if 'date' in data:
                unavailability.date = data['date']
            if 'start_time' in data:
                unavailability.start_time = data['start_time']
            if 'end_time' in data:
                unavailability.end_time = data['end_time']
            if 'reason' in data:
                unavailability.reason = data['reason']
            if 'is_all_day' in data:
                unavailability.is_all_day = data['is_all_day']

            unavailability.save()
            return JsonResponse(serialize_teacher_unavailability(unavailability))

        except (TeacherUnavailability.DoesNotExist, json.JSONDecodeError, ValidationError) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to update unavailability'}, status=500)


class ClassScheduleViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing class schedules"""

    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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


# Django views for reminder preferences (replacing DRF)
@method_decorator(login_required, name='dispatch')
class ReminderPreferenceView(View):
    """Handle reminder preference CRUD operations"""

    def get(self, request, preference_id=None):
        """List preferences or get specific preference"""
        if preference_id:
            # Get specific preference (user can only access their own)
            try:
                preference = ReminderPreference.objects.select_related("user", "school").get(
                    id=preference_id, user=request.user
                )
                return JsonResponse(serialize_reminder_preference(preference))
            except ReminderPreference.DoesNotExist:
                return JsonResponse({'error': 'Preference not found'}, status=404)

        # List user's own preferences
        preferences = ReminderPreference.objects.filter(user=request.user).select_related("user", "school").order_by("school", "created_at")
        data = [serialize_reminder_preference(preference) for preference in preferences]
        return JsonResponse({'results': data})

    def post(self, request):
        """Create new reminder preference"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            # Create preference for the current user
            school_id = data.get('school')
            school = None
            if school_id:
                # Ensure user has access to this school
                user_schools = get_user_schools(request.user)
                school = next((s for s in user_schools if s.id == int(school_id)), None)
                if not school:
                    return JsonResponse({'error': 'Permission denied'}, status=403)

            preference = ReminderPreference.objects.create(
                user=request.user,
                school=school,
                reminder_timing_hours=data.get('reminder_timing_hours', [24, 1]),
                communication_channels=data.get('communication_channels', ['email']),
                timezone_preference=data.get('timezone_preference'),
                is_active=data.get('is_active', True),
                is_school_default=data.get('is_school_default', False)
            )

            return JsonResponse(serialize_reminder_preference(preference), status=201)

        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to create preference'}, status=500)

    def put(self, request, preference_id):
        """Update reminder preference"""
        return self._update_preference(request, preference_id, partial=False)

    def patch(self, request, preference_id):
        """Partially update reminder preference"""
        return self._update_preference(request, preference_id, partial=True)

    def delete(self, request, preference_id):
        """Delete reminder preference"""
        try:
            preference = ReminderPreference.objects.get(id=preference_id, user=request.user)
            preference.delete()
            return JsonResponse({'message': 'Preference deleted successfully'})
        except ReminderPreference.DoesNotExist:
            return JsonResponse({'error': 'Preference not found'}, status=404)

    def _update_preference(self, request, preference_id, partial=False):
        """Helper method to update preference"""
        try:
            data = json.loads(request.body)
            preference = ReminderPreference.objects.get(id=preference_id, user=request.user)

            # Update fields
            if 'reminder_timing_hours' in data:
                preference.reminder_timing_hours = data['reminder_timing_hours']
            if 'communication_channels' in data:
                preference.communication_channels = data['communication_channels']
            if 'timezone_preference' in data:
                preference.timezone_preference = data['timezone_preference']
            if 'is_active' in data:
                preference.is_active = data['is_active']
            if 'is_school_default' in data:
                preference.is_school_default = data['is_school_default']

            preference.save()
            return JsonResponse(serialize_reminder_preference(preference))

        except (ReminderPreference.DoesNotExist, json.JSONDecodeError, ValidationError) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to update preference'}, status=500)


# Django views for class reminders (replacing DRF read-only ViewSet)
@method_decorator(login_required, name='dispatch')
class ClassReminderView(View):
    """Handle class reminder read operations"""

    def get(self, request, reminder_id=None):
        """List reminders or get specific reminder"""
        user_schools = get_user_schools(request.user)
        user = request.user

        if reminder_id:
            # Get specific reminder with role-based access
            try:
                # Base queryset for user's schools
                queryset = ClassReminder.objects.filter(class_schedule__school__in=user_schools).select_related(
                    "class_schedule__teacher__user", "class_schedule__student", "class_schedule__school", "recipient"
                )

                # Apply role-based filtering
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

                reminder = queryset.get(id=reminder_id)
                return JsonResponse(serialize_class_reminder(reminder))

            except ClassReminder.DoesNotExist:
                return JsonResponse({'error': 'Reminder not found'}, status=404)

        # List reminders with role-based filtering
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
        status_filter = request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        reminder_type = request.GET.get("reminder_type")
        if reminder_type:
            queryset = queryset.filter(reminder_type=reminder_type)

        date_from = request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(scheduled_for__date__gte=date_from)

        date_to = request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(scheduled_for__date__lte=date_to)

        search = request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(class_schedule__title__icontains=search) | Q(message__icontains=search) | Q(subject__icontains=search)
            )

        reminders = queryset.order_by("-scheduled_for")
        data = [serialize_class_reminder(reminder) for reminder in reminders]
        return JsonResponse({'results': data})


# Django views for user's own reminders (replacing DRF read-only ViewSet)
@method_decorator(login_required, name='dispatch')
class UserRemindersView(View):
    """Handle user's own reminder read operations"""

    def get(self, request, reminder_id=None):
        """List user's reminders or get specific reminder"""
        if reminder_id:
            # Get specific reminder (user can only access their own)
            try:
                reminder = ClassReminder.objects.select_related(
                    "class_schedule__teacher__user", "class_schedule__student", "class_schedule__school"
                ).get(id=reminder_id, recipient=request.user)
                return JsonResponse(serialize_class_reminder(reminder))
            except ClassReminder.DoesNotExist:
                return JsonResponse({'error': 'Reminder not found'}, status=404)

        # List user's own reminders
        reminders = ClassReminder.objects.filter(recipient=request.user).select_related(
            "class_schedule__teacher__user", "class_schedule__student", "class_schedule__school"
        ).order_by("-scheduled_for")
        data = [serialize_class_reminder(reminder) for reminder in reminders]
        return JsonResponse({'results': data})


class ReminderQueueViewSet(viewsets.ViewSet):
    """ViewSet for managing reminder queue (admin only)"""

    permission_classes = [IsAuthenticated]

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




# User = get_user_model()  # Removed with SessionBookingViewSet


# SessionBookingViewSet temporarily removed due to dependency issues with session_booking_service
# Will be re-added once all dependencies are resolved
