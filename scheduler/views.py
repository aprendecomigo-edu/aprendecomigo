from datetime import datetime, timedelta
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from waffle.decorators import waffle_switch
from waffle.mixins import WaffleSwitchMixin

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole, TeacherProfile

from .models import (
    ClassSchedule,
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


class CalendarView(WaffleSwitchMixin, LoginRequiredMixin, View):
    """Calendar page view with HTMX support for dynamic updates"""

    waffle_switch = "schedule_feature"

    def get(self, request):
        """Render calendar page with server-side events"""

        # Handle HTMX requests
        if request.headers.get("HX-Request"):
            action = request.GET.get("action")
            if action == "load_events":
                return self._handle_load_events(request)
            elif action == "switch_view":
                return self._handle_switch_view(request)
            elif action == "navigate":
                return self._handle_navigate(request)

        # Get current view and date from query params or defaults
        current_view = request.GET.get("view", "week")
        current_date_str = request.GET.get("date")

        if current_date_str:
            try:
                current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
            except ValueError:
                current_date = timezone.now().date()
        else:
            current_date = timezone.now().date()

        # Calculate date range based on view
        start_date, end_date = self._calculate_date_range(current_view, current_date)

        # Load events for the current view
        events = self._load_events_for_range(start_date, end_date)

        # Load teachers and students for form dropdowns
        teachers = self._get_available_teachers(request.user)
        students = self._get_available_students(request.user)

        # Generate additional data for templates
        template_data = self._get_template_data(current_view, current_date)

        return render(
            request,
            "scheduler/calendar.html",
            {
                "title": "Calendar - Aprende Comigo",
                "user": request.user,
                "active_section": "calendar",
                "events": events,  # Server-side events
                "current_view": current_view,
                "current_date": current_date,
                "teachers": teachers,
                "students": students,
                **template_data,  # Additional template data (week_days, month_days, hours)
            },
        )

    def post(self, request):
        """Handle calendar form submissions via HTMX"""
        action = request.POST.get("action")

        if action == "create_event":
            return self._handle_create_event(request)
        elif action == "load_events":
            return self._handle_load_events(request)
        elif action == "switch_view":
            return self._handle_switch_view(request)
        elif action == "navigate":
            return self._handle_navigate(request)
        else:
            return JsonResponse({"error": "Invalid action"}, status=400)

    def _calculate_date_range(self, view, current_date):
        """Calculate start and end dates for the given view and date"""

        if view == "week":
            # Start from Monday of current week
            days_since_monday = current_date.weekday()
            start_date = current_date - timedelta(days=days_since_monday)
            end_date = start_date + timedelta(days=6)
        elif view == "month":
            # Start from first day of month, end at last day
            start_date = current_date.replace(day=1)
            if start_date.month == 12:
                next_month = start_date.replace(year=start_date.year + 1, month=1)
            else:
                next_month = start_date.replace(month=start_date.month + 1)
            end_date = next_month - timedelta(days=1)
        else:  # day view
            start_date = current_date
            end_date = current_date

        return start_date, end_date

    def _load_events_for_range(self, start_date, end_date):
        """Load events for the specified date range"""

        schedules = (
            ClassSchedule.objects.select_related("teacher__user", "student")
            .filter(scheduled_date__gte=start_date, scheduled_date__lte=end_date)
            .order_by("scheduled_date", "start_time")
        )

        events = []
        for schedule in schedules:
            # Get teacher name
            teacher_name = "Professor"
            if schedule.teacher and schedule.teacher.user:
                teacher_name = schedule.teacher.user.name
                if not teacher_name:
                    teacher_name = schedule.teacher.user.email.split("@")[0]

            # Get student name
            student_name = "Aluno"
            if schedule.student:
                student_name = schedule.student.name
                if not student_name:
                    student_name = schedule.student.email.split("@")[0] if schedule.student.email else "Aluno"

            # Get title
            if schedule.title and schedule.title.strip():
                title = schedule.title
            else:
                class_type_display = schedule.get_class_type_display() if schedule.class_type else "Aula"
                title = f"{class_type_display} - {teacher_name}"

            events.append(
                {
                    "id": schedule.pk,
                    "title": title,
                    "description": schedule.description or f"{teacher_name} - {schedule.get_class_type_display()}",
                    "scheduled_date": schedule.scheduled_date,
                    "start_time": schedule.start_time.strftime("%H:%M") if schedule.start_time else "09:00",
                    "end_time": schedule.end_time.strftime("%H:%M") if schedule.end_time else "10:00",
                    "status": schedule.status.lower() or "scheduled",
                    "class_type": schedule.class_type,
                    "teacher_name": teacher_name,
                    "student_name": student_name,
                }
            )

        return events

    def _get_available_teachers(self, user):
        """Get available teachers for form dropdown"""

        # Get user's schools
        if user.is_staff or user.is_superuser:
            schools = School.objects.all()
        else:
            school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
            schools = School.objects.filter(id__in=school_ids)

        teachers = (
            TeacherProfile.objects.filter(user__school_memberships__school__in=schools)
            .select_related("user")
            .distinct()
        )

        return [{"id": t.id, "name": t.user.name or t.user.email} for t in teachers]

    def _get_available_students(self, user):
        """Get available students for form dropdown"""

        # Get user's schools
        if user.is_staff or user.is_superuser:
            schools = School.objects.all()
        else:
            school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
            schools = School.objects.filter(id__in=school_ids)

        # Get students through school memberships
        student_users = CustomUser.objects.filter(
            school_memberships__school__in=schools, school_memberships__role=SchoolRole.STUDENT.value
        ).distinct()

        return [{"id": s.id, "name": s.name or s.email} for s in student_users]

    def _get_template_data(self, current_view, current_date):
        """Generate additional data needed for templates"""

        data = {
            "hours": list(range(8, 20))  # 8AM to 7PM
        }

        if current_view == "week":
            # Generate week days (Monday to Sunday)
            days_since_monday = current_date.weekday()
            monday = current_date - timedelta(days=days_since_monday)
            data["week_days"] = [monday + timedelta(days=i) for i in range(7)]

        elif current_view == "month":
            # Generate month grid (42 days - 6 weeks)

            # First day of the month
            first_day = current_date.replace(day=1)
            # Last day of the month
            # Month boundary calculation (first_day is sufficient for grid generation)

            # Start from Sunday of the week containing the first day
            days_from_sunday = (first_day.weekday() + 1) % 7
            grid_start = first_day - timedelta(days=days_from_sunday)

            # Generate 42 days for complete month view
            month_days = []
            today = timezone.now().date()

            for i in range(42):
                day = grid_start + timedelta(days=i)
                month_days.append(
                    {
                        "date": day,
                        "is_current_month": day.month == current_date.month and day.year == current_date.year,
                        "is_today": day == today,
                    }
                )

            data["month_days"] = month_days

        return data

    def _handle_create_event(self, request):
        """Handle creating a new calendar event"""
        try:
            title = request.POST.get("title")
            description = request.POST.get("description", "")
            scheduled_date = request.POST.get("date")
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            class_type = request.POST.get("class_type", "individual")
            teacher_id = request.POST.get("teacher")
            student_id = request.POST.get("student")

            if not all([title, scheduled_date, start_time, end_time, teacher_id, student_id]):
                return render(
                    request,
                    "shared/partials/error_message.html",
                    {"error": "Por favor, preencha todos os campos obrigatórios."},
                )

            # Get teacher and student objects
            try:
                teacher = TeacherProfile.objects.get(id=teacher_id)
                student = CustomUser.objects.get(id=student_id)
            except (TeacherProfile.DoesNotExist, CustomUser.DoesNotExist):
                return render(
                    request, "shared/partials/error_message.html", {"error": "Professor ou aluno não encontrado."}
                )

            # Calculate duration in minutes
            from datetime import datetime

            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

            # Create the schedule

            # Get user's first school (TODO: allow school selection)
            school = School.objects.first()

            ClassSchedule.objects.create(
                title=title,
                description=description,
                scheduled_date=scheduled_date,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                class_type=class_type,
                teacher=teacher,
                student=student,
                school=school,
                booked_by=request.user,
            )

            # Return success message and trigger calendar refresh
            response = render(request, "shared/partials/success_message.html", {"message": "Aula criada com sucesso!"})
            response["HX-Trigger"] = "refreshCalendar"
            return response

        except Exception as e:
            return render(request, "shared/partials/error_message.html", {"error": f"Erro ao criar aula: {e!s}"})

    def _handle_load_events(self, request):
        """Handle loading events for a date range via HTMX"""

        current_view = request.GET.get("view") or request.POST.get("view", "week")
        current_date_str = request.GET.get("date") or request.POST.get("date")

        if current_date_str:
            try:
                current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
            except ValueError:
                current_date = timezone.now().date()
        else:
            current_date = timezone.now().date()

        start_date, end_date = self._calculate_date_range(current_view, current_date)
        events = self._load_events_for_range(start_date, end_date)
        template_data = self._get_template_data(current_view, current_date)

        return render(
            request,
            f"scheduler/partials/calendar_{current_view}_grid.html",
            {
                "events": events,
                "current_date": current_date,
                "current_view": current_view,
                **template_data,
            },
        )

    def _handle_switch_view(self, request):
        """Handle view switching via HTMX"""
        return self._handle_load_events(request)

    def _handle_navigate(self, request):
        """Handle navigation (prev/next) via HTMX"""

        current_view = request.POST.get("view", "week")
        current_date_str = request.POST.get("date")
        direction = request.POST.get("direction")

        if current_date_str:
            try:
                current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
            except ValueError:
                current_date = timezone.now().date()
        else:
            current_date = timezone.now().date()

        # Calculate new date based on direction and view
        if direction == "previous":
            if current_view == "week":
                new_date = current_date - timedelta(weeks=1)
            elif current_view == "month":
                if current_date.month == 1:
                    new_date = current_date.replace(year=current_date.year - 1, month=12)
                else:
                    new_date = current_date.replace(month=current_date.month - 1)
            else:  # day
                new_date = current_date - timedelta(days=1)
        elif direction == "next":
            if current_view == "week":
                new_date = current_date + timedelta(weeks=1)
            elif current_view == "month":
                if current_date.month == 12:
                    new_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    new_date = current_date.replace(month=current_date.month + 1)
            else:  # day
                new_date = current_date + timedelta(days=1)
        else:  # today
            new_date = timezone.now().date()

        start_date, end_date = self._calculate_date_range(current_view, new_date)
        events = self._load_events_for_range(start_date, end_date)
        template_data = self._get_template_data(current_view, new_date)

        return render(
            request,
            f"scheduler/partials/calendar_{current_view}_grid.html",
            {
                "events": events,
                "current_date": new_date,
                "current_view": current_view,
                **template_data,
            },
        )


# HTMX Template-based views for PWA
@method_decorator(login_required, name="dispatch")
class ClassScheduleTemplateView(WaffleSwitchMixin, TemplateView):
    """Main class schedule view with HTMX support"""

    template_name = "scheduler/scheduling/class_schedule.html"
    waffle_switch = "schedule_feature"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_schools = get_user_schools(user)

        # Get schedule summary
        schedule_queryset = ClassSchedule.objects.filter(school__in=user_schools)
        if hasattr(user, "teacher_profile"):
            schedule_queryset = schedule_queryset.filter(teacher=user.teacher_profile)
        elif not self._is_admin(user):
            schedule_queryset = schedule_queryset.filter(Q(student=user) | Q(additional_students=user))

        context.update(
            {
                "schedule_summary": {
                    "scheduled": schedule_queryset.filter(status="scheduled").count(),
                    "completed": schedule_queryset.filter(status="completed").count(),
                    "cancelled": schedule_queryset.filter(status="cancelled").count(),
                    "no_show": schedule_queryset.filter(status="no_show").count(),
                },
                "user_schools": user_schools,
                "user_is_admin": self._is_admin(user),
                "today": datetime.now().date(),
                "current_filter": self.request.GET.get("status", "all"),
                "start_date": self.request.GET.get("start_date", datetime.now().date()),
                "end_date": self.request.GET.get("end_date", datetime.now().date() + timedelta(days=30)),
                "active_section": "scheduler",  # For dashboard navigation
            }
        )

        if context["user_is_admin"] or not hasattr(user, "teacher_profile"):
            context["available_teachers"] = TeacherProfile.objects.filter(
                user__school_memberships__school__in=user_schools, user__school_memberships__is_active=True
            ).distinct()
            context["available_students"] = CustomUser.objects.filter(
                school_memberships__school__in=user_schools,
                school_memberships__is_active=True,
                school_memberships__role=SchoolRole.STUDENT,
            ).distinct()

        # If this is an HTMX request, return partial content
        if self.request.headers.get("HX-Request"):
            # Only list view is supported - calendar functionality moved to dedicated CalendarView
            self.template_name = "scheduler/scheduling/partials/schedule_list_content.html"
            context["schedules"] = self._get_filtered_schedules()

        return context

    def post(self, request, *args, **kwargs):
        """Handle creating new class schedules"""
        action = request.POST.get("action")

        if action == "create_schedule":
            return self._create_schedule(request)

        return JsonResponse({"error": "Unknown action"}, status=400)

    def _create_schedule(self, request):
        """Create a new class schedule"""
        user = request.user

        # Teachers cannot book classes
        if hasattr(user, "teacher_profile"):
            return JsonResponse({"error": "Teachers cannot book classes"}, status=403)

        try:
            # Validate school access
            school_id = request.POST.get("school")
            if not school_id:
                return JsonResponse({"error": "School is required"}, status=400)

            school = get_object_or_404(School, id=school_id)
            if not SchoolMembership.objects.filter(user=user, school=school, is_active=True).exists():
                return JsonResponse({"error": "No permission to book classes in this school"}, status=403)

            # Check if admin
            is_admin = self._is_admin(user)

            # Validate student
            student_id = request.POST.get("student")
            if student_id:
                student = get_object_or_404(CustomUser, id=student_id)
                # Non-admins can only book for themselves
                if not is_admin and student != user:
                    return JsonResponse({"error": "Students can only book for themselves"}, status=403)
            else:
                # Default to current user if not admin
                student = user if not is_admin else None

            # Get teacher
            teacher_id = request.POST.get("teacher")
            if not teacher_id:
                return JsonResponse({"error": "Teacher is required"}, status=400)
            teacher = get_object_or_404(TeacherProfile, id=teacher_id)

            # Create the schedule
            schedule = ClassSchedule.objects.create(
                title=request.POST.get("title"),
                description=request.POST.get("description", ""),
                teacher=teacher,
                student=student,
                school=school,
                scheduled_date=request.POST.get("scheduled_date"),
                start_time=request.POST.get("start_time"),
                end_time=request.POST.get("end_time"),
                status="scheduled",
                booked_by=user,
            )

            # Add additional students
            additional_students = request.POST.getlist("additional_students")
            if additional_students:
                schedule.additional_students.set(additional_students)

            # Return updated schedule list
            context = self.get_context_data()
            context["schedules"] = self._get_filtered_schedules()
            return render(request, "scheduler/scheduling/partials/schedule_list_content.html", context)

        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Failed to create schedule: {e!s}"}, status=500)

    def _get_filtered_schedules(self):
        """Get filtered schedules based on request parameters"""
        user = self.request.user
        user_schools = get_user_schools(user)

        queryset = (
            ClassSchedule.objects.filter(school__in=user_schools)
            .select_related("teacher__user", "student", "school", "booked_by")
            .prefetch_related("additional_students")
        )

        # Filter based on user role
        if hasattr(user, "teacher_profile"):
            queryset = queryset.filter(teacher=user.teacher_profile)
        elif not self._is_admin(user):
            # Students see only their classes
            queryset = queryset.filter(Q(student=user) | Q(additional_students=user))

        # Apply filters
        status_filter = self.request.GET.get("status", "all")
        if status_filter != "all":
            queryset = queryset.filter(status=status_filter)

        start_date = self.request.GET.get("start_date")
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)

        end_date = self.request.GET.get("end_date")
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)

        teacher_id = self.request.GET.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        student_id = self.request.GET.get("student_id")
        if student_id:
            queryset = queryset.filter(Q(student_id=student_id) | Q(additional_students=student_id))

        return queryset.order_by("scheduled_date", "start_time")

    def _is_admin(self, user):
        """Check if user is admin"""
        return SchoolMembership.objects.filter(
            user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
        ).exists()


@method_decorator(login_required, name="dispatch")
class TeacherAvailabilityTemplateView(WaffleSwitchMixin, TemplateView):
    """Teacher availability view with HTMX support"""

    template_name = "scheduler/availability/teacher_availability.html"
    waffle_switch = "schedule_feature"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_schools = get_user_schools(user)

        # Get availability summary
        availability_queryset = TeacherAvailability.objects.filter(school__in=user_schools)
        if hasattr(user, "teacher_profile") and not self._is_admin(user):
            availability_queryset = availability_queryset.filter(teacher=user.teacher_profile)

        # Calculate summary stats
        active_slots = availability_queryset.filter(is_active=True).count()
        total_hours = 0
        days_count = availability_queryset.values("day_of_week").distinct().count()

        for availability in availability_queryset.filter(is_active=True):
            start_time = datetime.combine(datetime.today(), availability.start_time)
            end_time = datetime.combine(datetime.today(), availability.end_time)
            duration = end_time - start_time
            total_hours += duration.total_seconds() / 3600

        context.update(
            {
                "availability_summary": {
                    "active_slots": active_slots,
                    "total_hours": f"{total_hours:.1f}",
                    "days_count": days_count,
                },
                "user_schools": user_schools,
                "user_is_admin": self._is_admin(user),
                "selected_teacher_id": self.request.GET.get("teacher_id"),
                "active_section": "scheduler",  # For dashboard navigation
            }
        )

        if context["user_is_admin"]:
            context["available_teachers"] = TeacherProfile.objects.filter(
                user__school_memberships__school__in=user_schools, user__school_memberships__is_active=True
            ).distinct()

        # Prepare availability data for templates
        if self.request.headers.get("HX-Request"):
            self.template_name = "scheduler/availability/partials/availability_list_content.html"
            context["availabilities"] = self._get_filtered_availabilities()
        else:
            # Prepare data for the grid view
            context["availability_by_day"] = self._get_availability_by_day()
            context["availabilities"] = self._get_filtered_availabilities()
            context["unavailabilities"] = self._get_filtered_unavailabilities()

        return context

    def _get_filtered_availabilities(self):
        """Get filtered availabilities based on request parameters"""
        user = self.request.user
        user_schools = get_user_schools(user)

        queryset = TeacherAvailability.objects.filter(school__in=user_schools).select_related("teacher__user", "school")

        # Filter by teacher if specified
        teacher_id = self.request.GET.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        elif hasattr(user, "teacher_profile") and not self._is_admin(user):
            queryset = queryset.filter(teacher=user.teacher_profile)

        return queryset.order_by("day_of_week", "start_time")

    def _get_filtered_unavailabilities(self):
        """Get filtered unavailabilities based on request parameters"""
        user = self.request.user
        user_schools = get_user_schools(user)

        queryset = TeacherUnavailability.objects.filter(
            school__in=user_schools,
            date__gte=datetime.now().date(),  # Only future unavailabilities by default
        ).select_related("teacher__user", "school")

        # Filter by teacher if specified
        teacher_id = self.request.GET.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        elif hasattr(user, "teacher_profile") and not self._is_admin(user):
            queryset = queryset.filter(teacher=user.teacher_profile)

        # Show all if requested
        if not self.request.GET.get("show_all"):
            queryset = queryset[:20]  # Limit to recent entries

        return queryset.order_by("date", "start_time")

    def _get_availability_by_day(self):
        """Organize availability by day of week for grid view"""
        availabilities = self._get_filtered_availabilities()

        # Initialize days (Monday=0 to Sunday=6)
        availability_by_day = []
        for day in range(7):
            day_availabilities = availabilities.filter(day_of_week=day)
            availability_by_day.append({"day": day, "availabilities": list(day_availabilities)})

        return availability_by_day

    def post(self, request, *args, **kwargs):
        """Handle creating availability"""
        action = request.POST.get("action")

        if action == "create_availability":
            return self._create_availability(request)

        return JsonResponse({"error": "Unknown action"}, status=400)

    def _create_availability(self, request):
        """Create new teacher availability"""
        user = request.user

        try:
            # If teacher is not provided and user has teacher_profile, set it automatically
            teacher_id = request.POST.get("teacher")
            if not teacher_id and hasattr(user, "teacher_profile"):
                teacher_id = user.teacher_profile.id

            school_id = request.POST.get("school")
            if not teacher_id or not school_id:
                return JsonResponse({"error": "Teacher and school are required"}, status=400)

            teacher = get_object_or_404(TeacherProfile, id=teacher_id)
            # Ensure teacher belongs to this school through SchoolMembership
            school_membership = get_object_or_404(
                SchoolMembership, user=teacher.user, school_id=school_id, is_active=True
            )
            school = school_membership.school

            # Ensure user has access to this school
            if not ensure_school_access(user, school):
                return JsonResponse({"error": "Permission denied"}, status=403)

            # Create availability
            TeacherAvailability.objects.create(
                teacher=teacher,
                school=school,
                day_of_week=request.POST.get("day_of_week"),
                start_time=request.POST.get("start_time"),
                end_time=request.POST.get("end_time"),
                is_active=request.POST.get("is_active") == "on",
            )

            # Return updated availability list
            context = self.get_context_data()
            return render(request, "scheduler/availability/partials/availability_list_content.html", context)

        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Failed to create availability: {e!s}"}, status=500)

    def _is_admin(self, user):
        """Check if user is admin"""
        return SchoolMembership.objects.filter(
            user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
        ).exists()


# Action views for ClassSchedule
@waffle_switch("schedule_feature")
@login_required
def class_schedule_cancel(request, schedule_id):
    """Cancel a class"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    from scheduler.services import ClassPermissionService, ClassStatusTransitionService

    user = request.user
    user_schools = get_user_schools(user)

    try:
        schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)

        # Check permissions
        permission_service = ClassPermissionService()
        if not permission_service.can_cancel_class(schedule, user):
            return JsonResponse({"error": "Permission denied"}, status=403)

        # Get cancellation reason
        data = json.loads(request.body)
        reason = data.get("reason", "")

        # Cancel the class
        transition_service = ClassStatusTransitionService()
        transition_service.cancel_class(schedule, user, reason)

        return JsonResponse({"message": "Class cancelled successfully"})

    except ClassSchedule.DoesNotExist:
        return JsonResponse({"error": "Schedule not found"}, status=404)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Failed to cancel: {e!s}"}, status=500)


@waffle_switch("schedule_feature")
@login_required
def class_schedule_confirm(request, schedule_id):
    """Confirm a class"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    from scheduler.services import ClassPermissionService, ClassStatusTransitionService

    user = request.user
    user_schools = get_user_schools(user)

    try:
        schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)

        # Check permissions
        permission_service = ClassPermissionService()
        if not permission_service.can_confirm_class(schedule, user):
            return JsonResponse({"error": "Permission denied"}, status=403)

        # Confirm the class
        transition_service = ClassStatusTransitionService()
        transition_service.confirm_class(schedule, user)

        return JsonResponse({"message": "Class confirmed successfully"})

    except ClassSchedule.DoesNotExist:
        return JsonResponse({"error": "Schedule not found"}, status=404)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Failed to confirm: {e!s}"}, status=500)


@waffle_switch("schedule_feature")
@login_required
def class_schedule_complete(request, schedule_id):
    """Complete a class"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    from scheduler.services import ClassCompletionOrchestratorService

    user = request.user
    user_schools = get_user_schools(user)

    try:
        schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)

        # Get completion data
        data = json.loads(request.body)
        actual_duration = data.get("actual_duration_minutes")
        notes = data.get("notes", "")

        # Complete the class
        orchestrator = ClassCompletionOrchestratorService()
        orchestrator.complete_class(schedule, user, actual_duration, notes)

        return JsonResponse({"message": "Class completed successfully"})

    except ClassSchedule.DoesNotExist:
        return JsonResponse({"error": "Schedule not found"}, status=404)
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Failed to complete: {e!s}"}, status=500)


@waffle_switch("schedule_feature")
@login_required
def class_schedule_no_show(request, schedule_id):
    """Mark class as no-show"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    from scheduler.services import ClassCompletionOrchestratorService

    user = request.user
    user_schools = get_user_schools(user)

    try:
        schedule = ClassSchedule.objects.get(id=schedule_id, school__in=user_schools)

        # Get no-show data
        data = json.loads(request.body)
        reason = data.get("reason", "").strip()
        notes = data.get("notes", "")
        no_show_type = data.get("no_show_type", "student")

        # Mark as no-show
        orchestrator = ClassCompletionOrchestratorService()
        orchestrator.mark_no_show(schedule, user, reason, no_show_type, notes)

        return JsonResponse({"message": "Marked as no-show successfully"})

    except ClassSchedule.DoesNotExist:
        return JsonResponse({"error": "Schedule not found"}, status=404)
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Failed to mark no-show: {e!s}"}, status=500)
