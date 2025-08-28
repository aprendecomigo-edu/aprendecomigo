"""
Django views for calendar functionality - moved from dashboard app.
Handles calendar page rendering and scheduling data.
"""

from datetime import timedelta
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from .models import ClassSchedule

User = get_user_model()


@method_decorator(login_required, name='dispatch')
class CalendarView(View):
    """Calendar page view - separate page with clean URL"""

    def get(self, request):
        """Render calendar page"""
        # Load calendar events using scheduler models
        today = timezone.now()
        # Get events for next 30 days to ensure we have enough data
        month_from_now = today + timedelta(days=30)

        schedules = ClassSchedule.objects.select_related(
            'teacher__user', 'student'
        ).filter(
            scheduled_date__gte=today.date(),
            scheduled_date__lte=month_from_now.date()
        ).order_by('scheduled_date', 'start_time')

        events = []
        for schedule in schedules:
            # Get real teacher name
            teacher_name = 'Professor'
            if schedule.teacher and schedule.teacher.user:
                teacher_name = f"{schedule.teacher.user.first_name} {schedule.teacher.user.last_name}".strip()
                if not teacher_name:
                    teacher_name = schedule.teacher.user.email.split('@')[0]

            # Get real student name
            student_name = 'Aluno'
            if schedule.student:
                student_name = f"{schedule.student.first_name} {schedule.student.last_name}".strip()
                if not student_name:
                    student_name = schedule.student.email.split('@')[0] if schedule.student.email else 'Aluno'

            # Use the actual title from the schedule, or create a descriptive one
            if schedule.title and schedule.title.strip():
                title = schedule.title
            else:
                # Create a descriptive title based on available data
                class_type_display = getattr(schedule, 'get_class_type_display', lambda: 'Aula')()
                title = f"{class_type_display} - {teacher_name}"

            events.append({
                'id': schedule.pk,
                'title': title,
                'description': schedule.description or f'{teacher_name} - {class_type_display}',
                'start': f"{schedule.scheduled_date} {schedule.start_time.strftime('%H:%M') if schedule.start_time else '09:00'}",
                'end': f"{schedule.scheduled_date} {schedule.end_time.strftime('%H:%M') if schedule.end_time else '10:00'}",
                'status': schedule.status.lower() or 'scheduled',
                'type': getattr(schedule, 'class_type', 'regular'),
                'teacher_name': teacher_name,
                'student_name': student_name,
                'participants_names': [student_name]
            })

        return render(request, 'scheduler/calendar.html', {
            'title': 'Calendar - Aprende Comigo',
            'user': request.user,
            'active_section': 'calendar',
            'initial_events': json.dumps(events)  # Pass events as JSON
        })
