import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import CustomUser, SchoolMembership, SchoolRole, TeacherProfile

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
    return school in user_schools


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

        except (TeacherProfile.DoesNotExist, ValidationError):
            return JsonResponse({'error': 'Invalid data'}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to create availability'}, status=500)

    def put(self, request, availability_id):
        """Update teacher availability"""
        return self._update_availability(request, availability_id)

    def patch(self, request, availability_id):
        """Partially update teacher availability"""
        return self._update_availability(request, availability_id)

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

    def _update_availability(self, request, availability_id):
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

        except (TeacherAvailability.DoesNotExist, json.JSONDecodeError, ValidationError):
            return JsonResponse({'error': 'Invalid request'}, status=400)
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

        except (TeacherProfile.DoesNotExist, ValidationError):
            return JsonResponse({'error': 'Invalid data'}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to create unavailability'}, status=500)

    def put(self, request, unavailability_id):
        """Update teacher unavailability"""
        return self._update_unavailability(request, unavailability_id)

    def patch(self, request, unavailability_id):
        """Partially update teacher unavailability"""
        return self._update_unavailability(request, unavailability_id)

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

    def _update_unavailability(self, request, unavailability_id):
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

        except (TeacherUnavailability.DoesNotExist, json.JSONDecodeError, ValidationError):
            return JsonResponse({'error': 'Invalid request'}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to update unavailability'}, status=500)


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

        except ValidationError:
            return JsonResponse({'error': 'Invalid data'}, status=400)
        except Exception:
            return JsonResponse({'error': 'Failed to create preference'}, status=500)

    def put(self, request, preference_id):
        """Update reminder preference"""
        return self._update_preference(request, preference_id)

    def patch(self, request, preference_id):
        """Partially update reminder preference"""
        return self._update_preference(request, preference_id)

    def delete(self, request, preference_id):
        """Delete reminder preference"""
        try:
            preference = ReminderPreference.objects.get(id=preference_id, user=request.user)
            preference.delete()
            return JsonResponse({'message': 'Preference deleted successfully'})
        except ReminderPreference.DoesNotExist:
            return JsonResponse({'error': 'Preference not found'}, status=404)

    def _update_preference(self, request, preference_id):
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

        except (ReminderPreference.DoesNotExist, json.JSONDecodeError, ValidationError):
            return JsonResponse({'error': 'Invalid request'}, status=400)
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


# =============================================================================
# Phase 1: ReminderQueueView (Admin Functionality)
# =============================================================================

@method_decorator(login_required, name='dispatch')
class ReminderQueueView(View):
    """Handle reminder queue management (admin only)"""

    def get(self, request):
        """Get reminder queue status"""
        # Check admin permissions
        is_admin = SchoolMembership.objects.filter(
            user=request.user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists()

        if not is_admin:
            return JsonResponse(
                {'error': 'Only administrators can access reminder queue status'},
                status=403
            )

        try:
            # Import here to avoid circular imports
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

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse(
                {'error': f'Failed to get reminder queue status: {e!s}'},
                status=500
            )

    def post(self, request):
        """Process reminder queue"""
        # Check admin permissions
        is_admin = SchoolMembership.objects.filter(
            user=request.user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists()

        if not is_admin:
            return JsonResponse(
                {'error': 'Only administrators can process reminder queue'},
                status=403
            )

        try:
            # Import here to avoid circular imports
            from .reminder_services import ReminderBackgroundTaskService

            # Parse request data
            data = json.loads(request.body) if request.body else {}
            force_process = data.get('force_process', False)
            max_reminders = data.get('max_reminders', 100)

            # Validate data
            if not isinstance(max_reminders, int) or max_reminders < 1:
                return JsonResponse({'error': 'max_reminders must be a positive integer'}, status=400)

            # Process the queue
            result = ReminderBackgroundTaskService.process_reminder_queue(
                force_process=force_process,
                max_reminders=max_reminders
            )

            response_data = {
                "message": "Reminder queue processing initiated",
                "processed_count": result.get("processed_count", 0),
                "failed_count": result.get("failed_count", 0),
                "queue_status": result.get("queue_status", "unknown"),
                "processing_time": result.get("processing_time", 0),
            }

            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse(
                {'error': f'Failed to process reminder queue: {e!s}'},
                status=500
            )


# =============================================================================
# Phase 2: RecurringClassScheduleView (Recurring Classes) - COMPLETE
# =============================================================================


@method_decorator(login_required, name='dispatch')
class RecurringClassScheduleView(View):
    """Handle recurring class schedule CRUD operations"""

    def get(self, request, schedule_id=None):
        """List recurring schedules or get specific schedule"""
        user_schools = get_user_schools(request.user)
        user = request.user

        if schedule_id:
            # Get specific recurring schedule
            try:
                recurring_schedule = RecurringClassSchedule.objects.filter(
                    id=schedule_id, school__in=user_schools
                ).select_related(
                    "teacher__user", "school", "created_by", "cancelled_by", "paused_by"
                ).prefetch_related("students").get()

                # Check permissions
                if hasattr(user, "teacher_profile"):
                    # Teachers can only see their own recurring schedules
                    if recurring_schedule.teacher != user.teacher_profile:
                        return JsonResponse({'error': 'Permission denied'}, status=403)
                elif not self._is_admin(user) and user not in recurring_schedule.students.all():
                    # Students can only see recurring schedules they're participating in
                    return JsonResponse({'error': 'Permission denied'}, status=403)

                return JsonResponse(serialize_recurring_schedule(recurring_schedule))

            except RecurringClassSchedule.DoesNotExist:
                return JsonResponse({'error': 'Recurring schedule not found'}, status=404)

        # List recurring schedules
        queryset = (
            RecurringClassSchedule.objects.filter(school__in=user_schools)
            .select_related("teacher__user", "school", "created_by", "cancelled_by", "paused_by")
            .prefetch_related("students")
        )

        # Filter based on user role
        if hasattr(user, "teacher_profile"):
            # Teachers can only see their own recurring schedules
            queryset = queryset.filter(teacher=user.teacher_profile)
        elif not self._is_admin(user):
            # Students can only see recurring schedules they're participating in
            queryset = queryset.filter(students=user)
        # Admins can see all schedules in their schools

        # Apply query parameter filters
        teacher_id = request.GET.get("teacher")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        student_id = request.GET.get("student")
        if student_id:
            queryset = queryset.filter(students=student_id)

        status_filter = request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        frequency_type = request.GET.get("frequency_type")
        if frequency_type:
            queryset = queryset.filter(frequency_type=frequency_type.upper())

        # Order by day_of_week and start_time
        queryset = queryset.order_by("day_of_week", "start_time")

        # Serialize results
        data = [serialize_recurring_schedule(schedule) for schedule in queryset]
        return JsonResponse({'results': data})

    def post(self, request, schedule_id=None):
        """Create new recurring schedule or handle actions"""
        user = request.user

        if schedule_id:
            # Handle actions on existing schedule
            action = request.GET.get('action')
            if action == 'generate_schedules':
                return self._generate_schedules(request, schedule_id)
            elif action == 'cancel_instance':
                return self._cancel_instance(request, schedule_id)
            elif action == 'add_student':
                return self._add_student(request, schedule_id)
            elif action == 'remove_student':
                return self._remove_student(request, schedule_id)
            else:
                return JsonResponse({'error': 'Unknown action'}, status=400)

        # Create new recurring schedule
        # Permission checks
        if hasattr(user, "teacher_profile"):
            # Teachers cannot create recurring schedules
            return JsonResponse({'error': 'Teachers cannot create recurring schedules'}, status=403)

        # Only admins can create recurring schedules
        if not self._is_admin(user):
            return JsonResponse({'error': 'Only admins can create recurring schedules'}, status=403)

        try:
            data = json.loads(request.body)

            # Validate required fields
            required_fields = ['title', 'teacher_id', 'school_id', 'day_of_week', 'start_time', 'end_time']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'Missing required field: {field}'}, status=400)

            # Create the recurring schedule
            # Note: This would normally use a serializer, but we're creating a basic implementation
            recurring_schedule = RecurringClassSchedule.objects.create(
                title=data['title'],
                description=data.get('description', ''),
                teacher_id=data['teacher_id'],
                school_id=data['school_id'],
                day_of_week=data['day_of_week'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                frequency_type=data.get('frequency_type', 'WEEKLY'),
                max_students=data.get('max_students', 10),
                created_by=user
            )

            return JsonResponse(serialize_recurring_schedule(recurring_schedule), status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to create recurring schedule: {e!s}'}, status=500)

    def put(self, request, schedule_id):
        """Update recurring schedule"""
        return self._update_schedule(request, schedule_id)

    def patch(self, request, schedule_id):
        """Partially update recurring schedule"""
        return self._update_schedule(request, schedule_id)

    def delete(self, request, schedule_id):
        """Delete (cancel) recurring schedule"""
        user = request.user
        user_schools = get_user_schools(user)

        # Only admins can delete recurring schedules
        if not self._is_admin(user):
            return JsonResponse({'error': 'Only admins can delete recurring schedules'}, status=403)

        try:
            recurring_schedule = RecurringClassSchedule.objects.filter(
                id=schedule_id, school__in=user_schools
            ).get()

            # Use cancel_series for soft delete instead of hard delete
            recurring_schedule.cancel_series(reason="Series deleted via API", cancelled_by=user)

            return JsonResponse(serialize_recurring_schedule(recurring_schedule))

        except RecurringClassSchedule.DoesNotExist:
            return JsonResponse({'error': 'Recurring schedule not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Failed to delete recurring schedule: {e!s}'}, status=500)

    def _update_schedule(self, request, schedule_id):
        """Helper method to update recurring schedule"""
        user = request.user
        user_schools = get_user_schools(user)

        # Only admins can update recurring schedules
        if not self._is_admin(user):
            return JsonResponse({'error': 'Only admins can update recurring schedules'}, status=403)

        try:
            data = json.loads(request.body)
            recurring_schedule = RecurringClassSchedule.objects.filter(
                id=schedule_id, school__in=user_schools
            ).get()

            # Update fields if provided
            for field in ['title', 'description', 'start_time', 'end_time', 'max_students']:
                if field in data:
                    setattr(recurring_schedule, field, data[field])

            recurring_schedule.save()

            return JsonResponse(serialize_recurring_schedule(recurring_schedule))

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except RecurringClassSchedule.DoesNotExist:
            return JsonResponse({'error': 'Recurring schedule not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Failed to update recurring schedule: {e!s}'}, status=500)

    def _generate_schedules(self, request, schedule_id):
        """Generate individual class schedules from recurring schedule"""
        user_schools = get_user_schools(request.user)

        try:
            data = json.loads(request.body) if request.body else {}
            recurring_schedule = RecurringClassSchedule.objects.filter(
                id=schedule_id, school__in=user_schools
            ).get()

            weeks_ahead = data.get("weeks_ahead", 4)

            created_schedules = recurring_schedule.generate_instances(weeks_ahead)

            return JsonResponse({
                "message": f"Generated {len(created_schedules)} class schedules",
                "created_schedules": [schedule.id for schedule in created_schedules],
                "weeks_ahead": weeks_ahead,
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except RecurringClassSchedule.DoesNotExist:
            return JsonResponse({'error': 'Recurring schedule not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Failed to generate schedules: {e!s}'}, status=500)

    def _cancel_instance(self, request, schedule_id):
        """Cancel a specific occurrence of the recurring class"""
        user = request.user
        user_schools = get_user_schools(user)

        # Only admins can cancel instances
        if not self._is_admin(user):
            return JsonResponse({'error': 'Only admins can cancel recurring class instances'}, status=403)

        try:
            data = json.loads(request.body)
            recurring_schedule = RecurringClassSchedule.objects.filter(
                id=schedule_id, school__in=user_schools
            ).get()

            date = data.get("date")
            reason = data.get("reason", "")

            if not date:
                return JsonResponse({'error': 'Date is required'}, status=400)

            result = recurring_schedule.cancel_occurrence(date=date, reason=reason, cancelled_by=user)
            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except RecurringClassSchedule.DoesNotExist:
            return JsonResponse({'error': 'Recurring schedule not found'}, status=404)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to cancel instance: {e!s}'}, status=500)

    def _add_student(self, request, schedule_id):
        """Add a student to the recurring class"""
        user = request.user
        user_schools = get_user_schools(user)

        # Only admins can manage students
        if not self._is_admin(user):
            return JsonResponse({'error': 'Only admins can manage students in recurring classes'}, status=403)

        try:
            data = json.loads(request.body)
            recurring_schedule = RecurringClassSchedule.objects.filter(
                id=schedule_id, school__in=user_schools
            ).get()

            student_id = data.get("student_id")
            if not student_id:
                return JsonResponse({'error': 'student_id is required'}, status=400)

            from accounts.models import CustomUser
            student = CustomUser.objects.get(id=student_id)
            recurring_schedule.add_student(student)

            return JsonResponse(serialize_recurring_schedule(recurring_schedule))

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except RecurringClassSchedule.DoesNotExist:
            return JsonResponse({'error': 'Recurring schedule not found'}, status=404)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to add student: {e!s}'}, status=500)

    def _remove_student(self, request, schedule_id):
        """Remove a student from the recurring class"""
        user = request.user
        user_schools = get_user_schools(user)

        # Only admins can manage students
        if not self._is_admin(user):
            return JsonResponse({'error': 'Only admins can manage students in recurring classes'}, status=403)

        try:
            data = json.loads(request.body)
            recurring_schedule = RecurringClassSchedule.objects.filter(
                id=schedule_id, school__in=user_schools
            ).get()

            student_id = data.get("student_id")
            if not student_id:
                return JsonResponse({'error': 'student_id is required'}, status=400)

            from accounts.models import CustomUser
            student = CustomUser.objects.get(id=student_id)
            recurring_schedule.remove_student(student)

            return JsonResponse(serialize_recurring_schedule(recurring_schedule))

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except RecurringClassSchedule.DoesNotExist:
            return JsonResponse({'error': 'Recurring schedule not found'}, status=404)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to remove student: {e!s}'}, status=500)

    def _is_admin(self, user):
        """Check if user is admin"""
        return SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists()


# =============================================================================
# Phase 3: ClassScheduleView (Class Schedules) - CRITICAL
# =============================================================================

def serialize_class_schedule(class_schedule):
    """Serialize ClassSchedule instance to dict"""
    return {
        'id': class_schedule.id,
        'title': class_schedule.title,
        'description': class_schedule.description,
        'teacher': {
            'id': class_schedule.teacher.id,
            'name': class_schedule.teacher.user.name,
            'email': class_schedule.teacher.user.email
        } if class_schedule.teacher else None,
        'student': {
            'id': class_schedule.student.id,
            'name': class_schedule.student.name,
            'email': class_schedule.student.email
        } if class_schedule.student else None,
        'additional_students': [{
            'id': student.id,
            'name': student.name,
            'email': student.email
        } for student in class_schedule.additional_students.all()],
        'school': {
            'id': class_schedule.school.id,
            'name': class_schedule.school.name
        },
        'scheduled_date': class_schedule.scheduled_date.isoformat(),
        'start_time': class_schedule.start_time.strftime('%H:%M'),
        'end_time': class_schedule.end_time.strftime('%H:%M'),
        'status': class_schedule.status,
        'status_display': class_schedule.get_status_display(),
        'booked_by': {
            'id': class_schedule.booked_by.id,
            'name': class_schedule.booked_by.name,
            'email': class_schedule.booked_by.email
        } if class_schedule.booked_by else None,
        'recurring_schedule': {
            'id': class_schedule.recurring_schedule.id,
            'title': class_schedule.recurring_schedule.title
        } if class_schedule.recurring_schedule else None,
        'actual_duration_minutes': class_schedule.actual_duration_minutes,
        'notes': class_schedule.notes,
        'created_at': class_schedule.created_at.isoformat(),
        'updated_at': class_schedule.updated_at.isoformat()
    }


@method_decorator(login_required, name='dispatch')
class ClassScheduleView(View):
    """Handle class schedule CRUD and actions (CRITICAL - used by calendar)"""

    def get(self, request, schedule_id=None):
        """List or retrieve class schedules"""
        user = request.user
        user_schools = get_user_schools(user)

        if schedule_id:
            # Get specific schedule
            try:
                schedule = ClassSchedule.objects.select_related(
                    'teacher__user', 'student', 'school', 'booked_by'
                ).prefetch_related('additional_students').get(
                    id=schedule_id,
                    school__in=user_schools
                )

                # Check view permissions
                if hasattr(user, 'teacher_profile'):
                    if schedule.teacher != user.teacher_profile:
                        return JsonResponse({'error': 'Permission denied'}, status=403)
                elif not self._is_admin(user):
                    # Students can only see classes they're in
                    all_students = list(schedule.additional_students.all())
                    if schedule.student:
                        all_students.append(schedule.student)
                    if user not in all_students:
                        return JsonResponse({'error': 'Permission denied'}, status=403)

                return JsonResponse(serialize_class_schedule(schedule))

            except ClassSchedule.DoesNotExist:
                return JsonResponse({'error': 'Schedule not found'}, status=404)

        # List schedules
        queryset = ClassSchedule.objects.filter(
            school__in=user_schools
        ).select_related(
            'teacher__user', 'student', 'school', 'booked_by'
        ).prefetch_related('additional_students')

        # Filter based on user role
        if hasattr(user, 'teacher_profile'):
            queryset = queryset.filter(teacher=user.teacher_profile)
        elif not self._is_admin(user):
            # Students see only their classes
            from django.db.models import Q
            queryset = queryset.filter(
                Q(student=user) | Q(additional_students=user)
            )

        # Apply filters
        start_date = request.GET.get('start_date')
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)

        end_date = request.GET.get('end_date')
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)

        status_filter = request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        teacher_id = request.GET.get('teacher_id')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        student_id = request.GET.get('student_id')
        if student_id:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(student_id=student_id) | Q(additional_students=student_id)
            )

        schedules = queryset.order_by('scheduled_date', 'start_time')
        return JsonResponse({
            'results': [serialize_class_schedule(s) for s in schedules]
        })

    def post(self, request):
        """Create new class schedule"""
        user = request.user

        # Teachers cannot book classes
        if hasattr(user, 'teacher_profile'):
            return JsonResponse({'error': 'Teachers cannot book classes'}, status=403)

        try:
            data = json.loads(request.body)

            # Validate school access
            school_id = data.get('school')
            if not school_id:
                return JsonResponse({'error': 'School is required'}, status=400)

            from accounts.models import School
            try:
                school = School.objects.get(id=school_id)
                if not SchoolMembership.objects.filter(
                    user=user, school=school, is_active=True
                ).exists():
                    return JsonResponse({'error': 'No permission to book classes in this school'}, status=403)
            except School.DoesNotExist:
                return JsonResponse({'error': 'School not found'}, status=404)

            # Check if admin
            is_admin = self._is_admin(user)

            # Validate student
            student_id = data.get('student')
            if student_id:
                student = CustomUser.objects.get(id=student_id)
                # Non-admins can only book for themselves
                if not is_admin and student != user:
                    return JsonResponse({'error': 'Students can only book for themselves'}, status=403)
            else:
                # Default to current user if not admin
                student = user if not is_admin else None

            # Get teacher
            teacher_id = data.get('teacher')
            if not teacher_id:
                return JsonResponse({'error': 'Teacher is required'}, status=400)
            teacher = TeacherProfile.objects.get(id=teacher_id)

            # Create the schedule
            schedule = ClassSchedule.objects.create(
                title=data.get('title'),
                description=data.get('description', ''),
                teacher=teacher,
                student=student,
                school=school,
                scheduled_date=data.get('scheduled_date'),
                start_time=data.get('start_time'),
                end_time=data.get('end_time'),
                status='scheduled',
                booked_by=user,
                recurring_schedule_id=data.get('recurring_schedule')
            )

            # Add additional students
            additional_students = data.get('additional_students', [])
            if additional_students:
                schedule.additional_students.set(additional_students)

            return JsonResponse(serialize_class_schedule(schedule), status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except (CustomUser.DoesNotExist, TeacherProfile.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to create schedule: {e!s}'}, status=500)

    def put(self, request, schedule_id):
        """Update class schedule"""
        return self._update_schedule(request, schedule_id, partial=False)

    def patch(self, request, schedule_id):
        """Partially update class schedule"""
        return self._update_schedule(request, schedule_id, partial=True)

    def delete(self, request, schedule_id):
        """Delete class schedule (admin only)"""
        user = request.user

        # Only admins can delete
        if not self._is_admin(user):
            return JsonResponse({'error': 'Only administrators can delete schedules'}, status=403)

        try:
            user_schools = get_user_schools(user)
            schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)
            schedule.delete()
            return JsonResponse({'message': 'Schedule deleted successfully'})
        except ClassSchedule.DoesNotExist:
            return JsonResponse({'error': 'Schedule not found'}, status=404)

    def _update_schedule(self, request, schedule_id, partial=False):
        """Helper to update schedule"""
        user = request.user
        user_schools = get_user_schools(user)

        try:
            data = json.loads(request.body)
            schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)

            # Check permissions
            if hasattr(user, 'teacher_profile'):
                if schedule.teacher != user.teacher_profile:
                    return JsonResponse({'error': 'Teachers can only update their own classes'}, status=403)
            elif not self._is_admin(user):
                return JsonResponse({'error': 'Students cannot update schedules'}, status=403)

            # Update fields
            if not partial or 'title' in data:
                schedule.title = data.get('title', schedule.title)
            if not partial or 'description' in data:
                schedule.description = data.get('description', schedule.description)
            if not partial or 'scheduled_date' in data:
                schedule.scheduled_date = data.get('scheduled_date', schedule.scheduled_date)
            if not partial or 'start_time' in data:
                schedule.start_time = data.get('start_time', schedule.start_time)
            if not partial or 'end_time' in data:
                schedule.end_time = data.get('end_time', schedule.end_time)
            if not partial or 'status' in data:
                schedule.status = data.get('status', schedule.status)

            schedule.save()
            return JsonResponse(serialize_class_schedule(schedule))

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except ClassSchedule.DoesNotExist:
            return JsonResponse({'error': 'Schedule not found'}, status=404)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to update schedule: {e!s}'}, status=500)

    def _is_admin(self, user):
        """Check if user is admin"""
        return SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists()


# Action views for ClassSchedule
@login_required
def class_schedule_cancel(request, schedule_id):
    """Cancel a class"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from scheduler.services import ClassPermissionService, ClassStatusTransitionService

    user = request.user
    user_schools = get_user_schools(user)

    try:
        schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)

        # Check permissions
        permission_service = ClassPermissionService()
        if not permission_service.can_cancel_class(schedule, user):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        # Get cancellation reason
        data = json.loads(request.body)
        reason = data.get('reason', '')

        # Cancel the class
        transition_service = ClassStatusTransitionService()
        transition_service.cancel_class(schedule, user, reason)

        return JsonResponse({'message': 'Class cancelled successfully'})

    except ClassSchedule.DoesNotExist:
        return JsonResponse({'error': 'Schedule not found'}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Failed to cancel: {e!s}'}, status=500)


@login_required
def class_schedule_confirm(request, schedule_id):
    """Confirm a class"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from scheduler.services import ClassPermissionService, ClassStatusTransitionService

    user = request.user
    user_schools = get_user_schools(user)

    try:
        schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)

        # Check permissions
        permission_service = ClassPermissionService()
        if not permission_service.can_confirm_class(schedule, user):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        # Confirm the class
        transition_service = ClassStatusTransitionService()
        transition_service.confirm_class(schedule, user)

        return JsonResponse({'message': 'Class confirmed successfully'})

    except ClassSchedule.DoesNotExist:
        return JsonResponse({'error': 'Schedule not found'}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Failed to confirm: {e!s}'}, status=500)


@login_required
def class_schedule_complete(request, schedule_id):
    """Complete a class"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from scheduler.services import ClassCompletionOrchestratorService

    user = request.user
    user_schools = get_user_schools(user)

    try:
        schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)

        # Get completion data
        data = json.loads(request.body)
        actual_duration = data.get('actual_duration_minutes')
        notes = data.get('notes', '')

        # Complete the class
        orchestrator = ClassCompletionOrchestratorService()
        orchestrator.complete_class(schedule, user, actual_duration, notes)

        return JsonResponse({'message': 'Class completed successfully'})

    except ClassSchedule.DoesNotExist:
        return JsonResponse({'error': 'Schedule not found'}, status=404)
    except PermissionDenied as e:
        return JsonResponse({'error': str(e)}, status=403)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Failed to complete: {e!s}'}, status=500)


@login_required
def class_schedule_no_show(request, schedule_id):
    """Mark class as no-show"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from scheduler.services import ClassCompletionOrchestratorService

    user = request.user
    user_schools = get_user_schools(user)

    try:
        schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)

        # Get no-show data
        data = json.loads(request.body)
        reason = data.get('reason', '').strip()
        notes = data.get('notes', '')
        no_show_type = data.get('no_show_type', 'student')

        # Mark as no-show
        orchestrator = ClassCompletionOrchestratorService()
        orchestrator.mark_no_show(schedule, user, reason, no_show_type, notes)

        return JsonResponse({'message': 'Marked as no-show successfully'})

    except ClassSchedule.DoesNotExist:
        return JsonResponse({'error': 'Schedule not found'}, status=404)
    except PermissionDenied as e:
        return JsonResponse({'error': str(e)}, status=403)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Failed to mark no-show: {e!s}'}, status=500)
