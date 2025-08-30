"""
Dashboard views with clean URLs outside of accounts app
"""

import json
import logging
from datetime import datetime, timedelta
from uuid import uuid4

from django.db import models
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from accounts.models import (
    CustomUser, SchoolMembership, School, TeacherInvitation, InvitationStatus
)
from accounts.models.schools import SchoolRole
from accounts.models.profiles import TeacherProfile, StudentProfile
from finances.models import PurchaseTransaction
from scheduler.models import ClassSchedule
from tasks.models import Task

logger = logging.getLogger('accounts.auth')

class DashboardView(LoginRequiredMixin, View):
    """Main dashboard view that renders appropriate template based on user role"""

    def get(self, request):
        """Render appropriate dashboard template based on user role"""

        # Render appropriate dashboard template based on user role
        if hasattr(request.user, 'teacherprofile'):
            return self._render_teacher_dashboard(request)
        elif hasattr(request.user, 'studentprofile'):
            return self._render_student_dashboard(request)
        elif hasattr(request.user, 'parentprofile'):
            return self._render_parent_dashboard(request)
        elif request.user.is_staff:
            return self._render_admin_dashboard(request)
        else:
            # Fallback for users without specific profiles - render basic dashboard
            return render(request, 'dashboard/basic_dashboard.html', {
                'title': 'Dashboard - Aprende Comigo',
                'user': request.user,
                'active_section': 'dashboard',
                'message': 'Welcome to Aprende Comigo! Please complete your profile setup.'
            })
    
    def _render_teacher_dashboard(self, request):
        """Render teacher-specific dashboard"""
        return render(request, 'dashboard/teacher_dashboard.html')
    
    def _render_student_dashboard(self, request):
        """Render student-specific dashboard"""
        return render(request, 'dashboard/student_dashboard.html')
    
    def _render_parent_dashboard(self, request):
        """Render parent-specific dashboard"""
        return render(request, 'dashboard/parent_dashboard.html')

    def _render_admin_dashboard(self, request):
        """Render admin dashboard directly at /dashboard/ - moved from AdminDashboardView"""
        from scheduler.models import ClassSchedule

        # Get the logged-in user (authentication handled by main get() method)
        user = request.user

        # Get statistics
        total_teachers = TeacherProfile.objects.count()
        total_students = StudentProfile.objects.count()

        # Get active sessions (scheduled in the next 7 days)
        today = timezone.now()
        week_from_now = today + timedelta(days=7)
        active_sessions = ClassSchedule.objects.filter(
            scheduled_date__gte=today.date(),
            scheduled_date__lte=week_from_now.date(),
            status__in=['scheduled', 'confirmed']
        ).count()

        # Get revenue this month from actual financial data

        from finances.models import PurchaseTransaction
        current_month = today.month
        current_year = today.year

        try:
            revenue_this_month = PurchaseTransaction.objects.filter(
                created_at__year=current_year,
                created_at__month=current_month,
                status='completed'
            ).aggregate(total=models.Sum('amount_charged'))['total'] or 0
            revenue_this_month = int(revenue_this_month / 100)  # Convert cents to euros
        except Exception:
            revenue_this_month = 0  # Default to 0 if no payment data

        # Get tasks from task management system
        from tasks.models import Task
        try:
            user_tasks = Task.objects.filter(user=user).order_by('-created_at')[:10]
            tasks = []
            for task in user_tasks:
                tasks.append({
                    'id': task.pk,
                    'title': task.title,
                    'priority': task.priority.lower() if task.priority else 'medium',
                    'status': 'completed' if task.status == 'completed' else 'pending',
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None
                })
        except Exception:
            # Fallback to empty tasks if Task model doesn't exist or has issues
            tasks = []

        # Get upcoming events (classes) - simplified for now
        events = []
        schedules = ClassSchedule.objects.select_related(
            'teacher__user', 'student'
        ).filter(
            scheduled_date__gte=today.date(),
            scheduled_date__lte=week_from_now.date()
        ).order_by('scheduled_date', 'start_time')[:10]

        for schedule in schedules:
            # Get real teacher name
            teacher_name = 'Professor'
            if schedule.teacher and schedule.teacher.user:
                teacher_name = schedule.teacher.user.name
                if not teacher_name:
                    teacher_name = schedule.teacher.user.email.split('@')[0]

            # Get real student name
            student_name = 'Aluno'
            if schedule.student:
                student_name = schedule.student.name
                if not student_name:
                    student_name = schedule.student.email.split('@')[0] if schedule.student.email else 'Aluno'

            # Use the actual title from the schedule, or create a descriptive one
            if schedule.title and schedule.title.strip():
                title = schedule.title
            else:
                # Create a descriptive title based on available data
                class_type_display = schedule.get_class_type_display() if schedule.class_type else 'Aula'
                title = f"{class_type_display} - {teacher_name}"

            events.append({
                'id': schedule.pk,
                'title': title,
                'scheduled_date': schedule.scheduled_date.strftime('%Y-%m-%d'),
                'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else '09:00',
                'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else '10:00',
                'duration_minutes': 60,
                'teacher_name': teacher_name,
                'student_name': student_name,
                'status': schedule.status or 'scheduled'
            })

        context = {
            'title': 'Admin Dashboard - Aprende Comigo',
            'user': user,
            'active_section': 'dashboard',
            'total_teachers': total_teachers,
            'total_students': total_students,
            'active_sessions': active_sessions,
            'revenue_this_month': revenue_this_month,
            'tasks': json.dumps(tasks),  # JSON encode for JavaScript
            'events': events,
            'now': timezone.now(),
        }

        return render(request, 'dashboard/admin_dashboard.html', context)

    def _render_teacher_dashboard(self, request):
        """Render teacher dashboard with teaching tools and data"""
        return render(request, 'dashboard/teacher_dashboard.html', {
            'title': 'Teacher Dashboard - Aprende Comigo',
            'user': request.user,
            'active_section': 'dashboard'
        })

    def _render_student_dashboard(self, request):
        """Render student dashboard with learning tools"""
        return render(request, 'dashboard/student_dashboard.html', {
            'title': 'Student Portal - Aprende Comigo',
            'user': request.user,
            'active_section': 'dashboard'
        })

    def _render_parent_dashboard(self, request):
        """Render parent dashboard with child progress monitoring"""
        return render(request, 'dashboard/parent_dashboard.html', {
            'title': 'Parent Portal - Aprende Comigo',
            'user': request.user,
            'active_section': 'dashboard'
        })




class CalendarView(LoginRequiredMixin, View):
    """Calendar page view with HTMX support for dynamic updates"""

    def get(self, request):
        """Render calendar page with server-side events"""

        
        # Handle HTMX requests
        if request.headers.get('HX-Request'):
            action = request.GET.get('action')
            if action == 'load_events':
                return self._handle_load_events(request)
            elif action == 'switch_view':
                return self._handle_switch_view(request)
            elif action == 'navigate':
                return self._handle_navigate(request)

        # Get current view and date from query params or defaults
        current_view = request.GET.get('view', 'week')
        current_date_str = request.GET.get('date')
        
        if current_date_str:
            try:
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
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

        return render(request, 'dashboard/calendar.html', {
            'title': 'Calendar - Aprende Comigo',
            'user': request.user,
            'active_section': 'calendar',
            'events': events,  # Server-side events
            'current_view': current_view,
            'current_date': current_date,
            'teachers': teachers,
            'students': students,
            **template_data,  # Additional template data (week_days, month_days, hours)
        })

    def post(self, request):
        """Handle calendar form submissions via HTMX"""
        action = request.POST.get('action')
        
        if action == 'create_event':
            return self._handle_create_event(request)
        elif action == 'load_events':
            return self._handle_load_events(request)
        elif action == 'switch_view':
            return self._handle_switch_view(request)
        elif action == 'navigate':
            return self._handle_navigate(request)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

    def _calculate_date_range(self, view, current_date):
        """Calculate start and end dates for the given view and date"""
        
        if view == 'week':
            # Start from Monday of current week
            days_since_monday = current_date.weekday()
            start_date = current_date - timedelta(days=days_since_monday)
            end_date = start_date + timedelta(days=6)
        elif view == 'month':
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
        
        schedules = ClassSchedule.objects.select_related(
            'teacher__user', 'student'
        ).filter(
            scheduled_date__gte=start_date,
            scheduled_date__lte=end_date
        ).order_by('scheduled_date', 'start_time')

        events = []
        for schedule in schedules:
            # Get teacher name
            teacher_name = 'Professor'
            if schedule.teacher and schedule.teacher.user:
                teacher_name = schedule.teacher.user.name
                if not teacher_name:
                    teacher_name = schedule.teacher.user.email.split('@')[0]

            # Get student name
            student_name = 'Aluno'
            if schedule.student:
                student_name = schedule.student.name
                if not student_name:
                    student_name = schedule.student.email.split('@')[0] if schedule.student.email else 'Aluno'

            # Get title
            if schedule.title and schedule.title.strip():
                title = schedule.title
            else:
                class_type_display = schedule.get_class_type_display() if schedule.class_type else 'Aula'
                title = f"{class_type_display} - {teacher_name}"

            events.append({
                'id': schedule.pk,
                'title': title,
                'description': schedule.description or f'{teacher_name} - {schedule.get_class_type_display()}',
                'scheduled_date': schedule.scheduled_date,
                'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else '09:00',
                'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else '10:00',
                'status': schedule.status.lower() or 'scheduled',
                'class_type': schedule.class_type,
                'teacher_name': teacher_name,
                'student_name': student_name,
            })
        
        return events

    def _get_available_teachers(self, user):
        """Get available teachers for form dropdown"""
        
        # Get user's schools
        if user.is_staff or user.is_superuser:
            schools = School.objects.all()
        else:
            school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
            schools = School.objects.filter(id__in=school_ids)
        
        teachers = TeacherProfile.objects.filter(
            user__school_memberships__school__in=schools
        ).select_related('user').distinct()
        
        return [{'id': t.id, 'name': t.user.name or t.user.email} for t in teachers]

    def _get_available_students(self, user):
        """Get available students for form dropdown"""
        
        # Get user's schools
        if user.is_staff or user.is_superuser:
            schools = School.objects.all()
        else:
            school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
            schools = School.objects.filter(id__in=school_ids)
        
        # Get students through school memberships
        student_users = CustomUser.objects.filter(
            school_memberships__school__in=schools,
            school_memberships__role=SchoolRole.STUDENT.value
        ).distinct()
        
        return [{'id': s.id, 'name': s.name or s.email} for s in student_users]

    def _get_template_data(self, current_view, current_date):
        """Generate additional data needed for templates"""
        
        data = {
            'hours': list(range(8, 20))  # 8AM to 7PM
        }
        
        if current_view == 'week':
            # Generate week days (Monday to Sunday)
            days_since_monday = current_date.weekday()
            monday = current_date - timedelta(days=days_since_monday)
            data['week_days'] = [monday + timedelta(days=i) for i in range(7)]
            
        elif current_view == 'month':
            # Generate month grid (42 days - 6 weeks)
            
            # First day of the month
            first_day = current_date.replace(day=1)
            # Last day of the month
            if first_day.month == 12:
                next_month = first_day.replace(year=first_day.year + 1, month=1)
            else:
                next_month = first_day.replace(month=first_day.month + 1)
            last_day = next_month - timedelta(days=1)
            
            # Start from Sunday of the week containing the first day
            days_from_sunday = (first_day.weekday() + 1) % 7
            grid_start = first_day - timedelta(days=days_from_sunday)
            
            # Generate 42 days for complete month view
            month_days = []
            today = timezone.now().date()
            
            for i in range(42):
                day = grid_start + timedelta(days=i)
                month_days.append({
                    'date': day,
                    'is_current_month': day.month == current_date.month and day.year == current_date.year,
                    'is_today': day == today
                })
            
            data['month_days'] = month_days
            
        return data

    def _handle_create_event(self, request):
        """Handle creating a new calendar event"""
        try:
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            scheduled_date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            class_type = request.POST.get('class_type', 'individual')
            teacher_id = request.POST.get('teacher')
            student_id = request.POST.get('student')

            if not all([title, scheduled_date, start_time, end_time, teacher_id, student_id]):
                return render(request, 'dashboard/partials/error_message.html', {
                    'error': 'Por favor, preencha todos os campos obrigatórios.'
                })

            # Get teacher and student objects
            try:
                teacher = TeacherProfile.objects.get(id=teacher_id)
                student = CustomUser.objects.get(id=student_id)
            except (TeacherProfile.DoesNotExist, CustomUser.DoesNotExist):
                return render(request, 'dashboard/partials/error_message.html', {
                    'error': 'Professor ou aluno não encontrado.'
                })

            # Create the schedule
            
            # Get user's first school (TODO: allow school selection)
            school = School.objects.first()
            
            schedule = ClassSchedule.objects.create(
                title=title,
                description=description,
                scheduled_date=scheduled_date,
                start_time=start_time,
                end_time=end_time,
                class_type=class_type,
                teacher=teacher,
                student=student,
                school=school,
                booked_by=request.user
            )

            # Return success message and trigger calendar refresh
            response = render(request, 'dashboard/partials/success_message.html', {
                'message': 'Aula criada com sucesso!'
            })
            response['HX-Trigger'] = 'refreshCalendar'
            return response

        except Exception as e:
            return render(request, 'dashboard/partials/error_message.html', {
                'error': f'Erro ao criar aula: {str(e)}'
            })

    def _handle_load_events(self, request):
        """Handle loading events for a date range via HTMX"""
        
        current_view = request.GET.get('view') or request.POST.get('view', 'week')
        current_date_str = request.GET.get('date') or request.POST.get('date')
        
        if current_date_str:
            try:
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
            except ValueError:
                current_date = timezone.now().date()
        else:
            current_date = timezone.now().date()
        
        start_date, end_date = self._calculate_date_range(current_view, current_date)
        events = self._load_events_for_range(start_date, end_date)
        template_data = self._get_template_data(current_view, current_date)
        
        return render(request, f'dashboard/partials/calendar_{current_view}_grid.html', {
            'events': events,
            'current_date': current_date,
            'current_view': current_view,
            **template_data,
        })

    def _handle_switch_view(self, request):
        """Handle view switching via HTMX"""
        return self._handle_load_events(request)

    def _handle_navigate(self, request):
        """Handle navigation (prev/next) via HTMX"""
        
        current_view = request.POST.get('view', 'week')
        current_date_str = request.POST.get('date')
        direction = request.POST.get('direction')
        
        if current_date_str:
            try:
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
            except ValueError:
                current_date = timezone.now().date()
        else:
            current_date = timezone.now().date()
        
        # Calculate new date based on direction and view
        if direction == 'previous':
            if current_view == 'week':
                new_date = current_date - timedelta(weeks=1)
            elif current_view == 'month':
                if current_date.month == 1:
                    new_date = current_date.replace(year=current_date.year - 1, month=12)
                else:
                    new_date = current_date.replace(month=current_date.month - 1)
            else:  # day
                new_date = current_date - timedelta(days=1)
        elif direction == 'next':
            if current_view == 'week':
                new_date = current_date + timedelta(weeks=1)
            elif current_view == 'month':
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
        
        return render(request, f'dashboard/partials/calendar_{current_view}_grid.html', {
            'events': events,
            'current_date': new_date,
            'current_view': current_view,
            **template_data,
        })


class TeachersView(View):
    """Teachers management page"""

    def get(self, request):
        """Render teachers management page"""
        # TODO: Remove authentication bypass in production
        # if not request.user.is_authenticated:
        #     return redirect('accounts:signin')

        return render(request, 'dashboard/teachers.html', {
            'title': 'Teachers - Aprende Comigo',
            'user': request.user,
            'active_section': 'teachers'
        })


class StudentsView(View):
    """Students management page"""

    def get(self, request):
        """Render students management page"""
        # TODO: Remove authentication bypass in production
        # if not request.user.is_authenticated:
        #     return redirect('accounts:signin')

        return render(request, 'dashboard/students.html', {
            'title': 'Students - Aprende Comigo',
            'user': request.user,
            'active_section': 'students'
        })


class InvitationsView(LoginRequiredMixin, View):
    """Invitations management page"""

    def get(self, request):
        """Render invitations page with server-side data"""

        
        # Get user's schools - using same logic as PeopleView
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)

        # Check if this is a partial request for invitations list
        if request.GET.get('load_invitations'):
            return self._render_invitations_list(request)

        # Fetch invitations server-side
        invitations_queryset = TeacherInvitation.objects.filter(
            school__in=user_schools
        ).select_related('school', 'invited_by').order_by('-created_at')

        invitations = []
        for invitation in invitations_queryset:
            invitations.append({
                'id': invitation.pk,
                'email': invitation.email,
                'role': invitation.get_role_display(),
                'status': invitation.get_status_display(),
                'created_at': invitation.created_at,
                'school_name': invitation.school.name if invitation.school else '',
                'invited_by': invitation.invited_by.get_full_name() if invitation.invited_by else '',
                'custom_message': invitation.custom_message or '',
                'is_active': invitation.status in ['pending', 'sent', 'delivered', 'viewed'] and not invitation.is_accepted and invitation.expires_at > timezone.now()
            })

        return render(request, 'dashboard/invitations.html', {
            'title': 'Invitations - Aprende Comigo',
            'user': request.user,
            'active_section': 'invitations',
            'invitations': invitations,
            'user_schools': user_schools,
        })

    def post(self, request):
        """Handle invitation form submissions"""
        action = request.POST.get('action')
        
        if action == 'send_invitation':
            return self._handle_send_invitation(request)
        elif action == 'resend_invitation':
            return self._handle_resend_invitation(request)
        elif action == 'cancel_invitation':
            return self._handle_cancel_invitation(request)
        elif action == 'load_invitations':
            return self._render_invitations_list(request)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

    def _handle_send_invitation(self, request):
        """Handle sending a new teacher invitation"""

        
        try:
            email = request.POST.get('email')
            role = request.POST.get('role', 'teacher')
            custom_message = request.POST.get('custom_message', '')

            if not email:
                return render(request, 'dashboard/partials/error_message.html', {
                    'error': 'Email is required'
                })

            # Get user's schools
            def get_user_schools(user):
                if user.is_staff or user.is_superuser:
                    return School.objects.all()
                school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
                return School.objects.filter(id__in=school_ids)

            user_schools = get_user_schools(request.user)
            
            if not user_schools.exists():
                return render(request, 'dashboard/partials/error_message.html', {
                    'error': 'No schools found for this user'
                })

            # Use the first school for now (TODO: allow school selection)
            school = user_schools.first()

            # Check for existing active invitation
            existing = TeacherInvitation.objects.filter(
                email=email,
                school=school,
                is_accepted=False,
                expires_at__gt=timezone.now(),
                status__in=[
                    InvitationStatus.PENDING,
                    InvitationStatus.SENT,
                    InvitationStatus.DELIVERED,
                    InvitationStatus.VIEWED,
                ],
            ).first()

            if existing:
                return render(request, 'dashboard/partials/error_message.html', {
                    'error': 'An active invitation already exists for this email and school'
                })

            # Create new invitation
            invitation = TeacherInvitation.objects.create(
                school=school,
                email=email,
                invited_by=request.user,
                role=role,
                custom_message=custom_message,
                batch_id=uuid4(),
                status=InvitationStatus.PENDING
            )

            # TODO: Send email invitation using messaging service
            invitation.mark_email_sent()

            # Return success message and update the invitations list
            response = render(request, 'dashboard/partials/success_message.html', {
                'message': f'Invitation sent successfully to {email}!'
            })
            response['HX-Trigger'] = 'refreshInvitations'
            return response

        except Exception as e:
            return render(request, 'dashboard/partials/error_message.html', {
                'error': f'Failed to send invitation: {str(e)}'
            })

    def _handle_resend_invitation(self, request):
        """Handle resending an existing invitation"""
        try:
            invitation_id = request.POST.get('invitation_id')
            if not invitation_id:
                return render(request, 'dashboard/partials/error_message.html', {
                    'error': 'Invitation ID is required'
                })

            invitation = TeacherInvitation.objects.get(pk=invitation_id)
            
            # TODO: Resend email using messaging service
            invitation.mark_email_sent()

            response = render(request, 'dashboard/partials/success_message.html', {
                'message': f'Invitation resent to {invitation.email}!'
            })
            response['HX-Trigger'] = 'refreshInvitations'
            return response

        except TeacherInvitation.DoesNotExist:
            return render(request, 'dashboard/partials/error_message.html', {
                'error': 'Invitation not found'
            })
        except Exception as e:
            return render(request, 'dashboard/partials/error_message.html', {
                'error': f'Failed to resend invitation: {str(e)}'
            })

    def _handle_cancel_invitation(self, request):
        """Handle canceling an existing invitation"""
        try:
            invitation_id = request.POST.get('invitation_id')
            if not invitation_id:
                return render(request, 'dashboard/partials/error_message.html', {
                    'error': 'Invitation ID is required'
                })

            invitation = TeacherInvitation.objects.get(pk=invitation_id)
            invitation.cancel()

            response = render(request, 'dashboard/partials/success_message.html', {
                'message': f'Invitation to {invitation.email} has been cancelled!'
            })
            response['HX-Trigger'] = 'refreshInvitations'
            return response

        except TeacherInvitation.DoesNotExist:
            return render(request, 'dashboard/partials/error_message.html', {
                'error': 'Invitation not found'
            })
        except Exception as e:
            return render(request, 'dashboard/partials/error_message.html', {
                'error': f'Failed to cancel invitation: {str(e)}'
            })

    def _render_invitations_list(self, request):
        """Render invitations list partial for HTMX updates"""

        # Get user's schools - using same logic as main view
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)

        # Fetch invitations
        invitations_queryset = TeacherInvitation.objects.filter(
            school__in=user_schools
        ).select_related('school', 'invited_by').order_by('-created_at')

        invitations = []
        for invitation in invitations_queryset:
            invitations.append({
                'id': invitation.pk,
                'email': invitation.email,
                'role': invitation.get_role_display(),
                'status': invitation.get_status_display(),
                'created_at': invitation.created_at,
                'school_name': invitation.school.name if invitation.school else '',
                'invited_by': invitation.invited_by.get_full_name() if invitation.invited_by else '',
                'custom_message': invitation.custom_message or '',
                'is_active': invitation.status in ['pending', 'sent', 'delivered', 'viewed'] and not invitation.is_accepted and invitation.expires_at > timezone.now()
            })

        return render(request, 'dashboard/partials/invitations_list.html', {
            'invitations': invitations,
        })


class PeopleView(LoginRequiredMixin, View):
    """Unified people management page with tabs for teachers, students, staff"""

    def get(self, request):
        """Render people management page with initial data server-side"""
        
        # Get user's schools - using same logic as API views
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)

        # Get teachers data with profiles
        teacher_memberships = SchoolMembership.objects.filter(
            school__in=user_schools,
            role=SchoolRole.TEACHER.value
        ).select_related('user', 'school')

        teachers = []
        for membership in teacher_memberships:
            user = membership.user
            try:
                profile = user.teacher_profile
                bio = profile.bio
                specialty = profile.specialty
                hourly_rate = float(profile.hourly_rate) if profile.hourly_rate else None
            except TeacherProfile.DoesNotExist:
                bio = ''
                specialty = ''
                hourly_rate = None

            teachers.append({
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'full_name': user.get_full_name(),
                'bio': bio,
                'specialty': specialty,
                'hourly_rate': hourly_rate,
                'school': {
                    'id': membership.school.id,
                    'name': membership.school.name
                },
                'status': 'active' if user.is_active else 'inactive'
            })

        # Get students data with profiles
        student_memberships = SchoolMembership.objects.filter(
            school__in=user_schools,
            role=SchoolRole.STUDENT.value
        ).select_related('user', 'school')

        students = []
        for membership in student_memberships:
            user = membership.user
            try:
                profile = user.student_profile
                school_year = profile.school_year
            except (StudentProfile.DoesNotExist, AttributeError):
                school_year = ''

            students.append({
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'full_name': user.get_full_name(),
                'school_year': school_year,
                'school': {
                    'id': membership.school.id,
                    'name': membership.school.name
                },
                'status': 'active' if user.is_active else 'inactive'
            })

        # Calculate stats
        teacher_stats = {
            'active': len([t for t in teachers if t['status'] == 'active']),
            'pending': 0,  # We'll implement this based on invitations later
            'inactive': len([t for t in teachers if t['status'] == 'inactive']),
            'total': len(teachers)
        }

        student_stats = {
            'total': len(students)
        }

        return render(request, 'dashboard/people.html', {
            'title': 'People - Aprende Comigo',
            'user': request.user,
            'active_section': 'people',
            'teachers': teachers,
            'students': students,
            'teacher_stats': teacher_stats,
            'student_stats': student_stats,
        })

    def post(self, request):
        """Handle form submissions for adding teachers/students"""
        action = request.POST.get('action')
        
        if action == 'add_teacher':
            return self._handle_add_teacher(request)
        elif action == 'add_student':
            return self._handle_add_student(request)
        elif action == 'invite_teacher':
            return self._handle_invite_teacher(request)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

    def _handle_add_teacher(self, request):
        """Handle adding a new teacher"""

        try:
            email = request.POST.get('email')
            bio = request.POST.get('bio', '')
            specialty = request.POST.get('specialty', '')

            if not email:
                return render(request, 'dashboard/partials/error_message.html', {
                    'error': 'Email is required'
                })

            # Get user's schools
            def get_user_schools(user):
                if user.is_staff or user.is_superuser:
                    return School.objects.all()
                school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
                return School.objects.filter(id__in=school_ids)

            user_schools = get_user_schools(request.user)

            # Check if user exists
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # Create new user if doesn't exist - use email prefix as default name
                default_name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
                user = CustomUser.objects.create_user(
                    email=email,
                    name=default_name  # Use the name field that exists on CustomUser
                )

            # Create or update teacher profile
            teacher_profile, created = TeacherProfile.objects.get_or_create(
                user=user,
                defaults={'bio': bio, 'specialty': specialty}
            )
            if not created:
                teacher_profile.bio = bio
                teacher_profile.specialty = specialty
                teacher_profile.save()

            # Add to user's schools as teacher
            for school in user_schools:
                SchoolMembership.objects.get_or_create(
                    user=user,
                    school=school,
                    defaults={'role': SchoolRole.TEACHER.value}
                )

            # Return updated teachers partial
            return self._render_teachers_partial(request)

        except Exception as e:
            return render(request, 'dashboard/partials/error_message.html', {
                'error': f'Failed to add teacher: {str(e)}'
            })

    def _handle_add_student(self, request):
        """Handle adding a new student"""

        try:
            email = request.POST.get('email')
            name = request.POST.get('name')
            school_year = request.POST.get('school_year', '')
            birth_date = request.POST.get('birth_date')

            if not email or not name or not birth_date:
                return render(request, 'dashboard/partials/error_message.html', {
                    'error': 'Email, name and birth date are required'
                })

            # Get user's schools
            def get_user_schools(user):
                if user.is_staff or user.is_superuser:
                    return School.objects.all()
                school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
                return School.objects.filter(id__in=school_ids)

            user_schools = get_user_schools(request.user)

            # Check if user exists
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # Create new user if doesn't exist
                user = CustomUser.objects.create_user(
                    email=email,
                    name=name  # Use the name field that exists on CustomUser
                )

            # Create or update student profile
            student_profile, created = StudentProfile.objects.get_or_create(
                user=user,
                defaults={'school_year': school_year, 'birth_date': birth_date}
            )
            if not created:
                student_profile.school_year = school_year
                student_profile.birth_date = birth_date
                student_profile.save()

            # Add to user's schools as student
            for school in user_schools:
                SchoolMembership.objects.get_or_create(
                    user=user,
                    school=school,
                    defaults={'role': SchoolRole.STUDENT.value}
                )

            # Return updated students partial
            return self._render_students_partial(request)

        except Exception as e:
            return render(request, 'dashboard/partials/error_message.html', {
                'error': f'Failed to add student: {str(e)}'
            })

    def _handle_invite_teacher(self, request):
        """Handle teacher invitation"""
        # TODO: Implement teacher invitation logic
        return render(request, 'dashboard/partials/success_message.html', {
            'message': 'Teacher invitation functionality coming soon'
        })

    def _render_teachers_partial(self, request):
        """Render teachers list partial for HTMX updates"""
        from accounts.models import SchoolMembership, School
        from accounts.models.schools import SchoolRole
        from accounts.models.profiles import TeacherProfile
        
        # Get user's schools
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)
        
        # Get teachers data with profiles
        teacher_memberships = SchoolMembership.objects.filter(
            school__in=user_schools,
            role=SchoolRole.TEACHER.value
        ).select_related('user', 'school')

        teachers = []
        for membership in teacher_memberships:
            user = membership.user
            try:
                profile = user.teacher_profile
                bio = profile.bio
                specialty = profile.specialty
                hourly_rate = float(profile.hourly_rate) if profile.hourly_rate else None
            except TeacherProfile.DoesNotExist:
                bio = ''
                specialty = ''
                hourly_rate = None

            teachers.append({
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'full_name': user.get_full_name(),
                'bio': bio,
                'specialty': specialty,
                'hourly_rate': hourly_rate,
                'school': {
                    'id': membership.school.id,
                    'name': membership.school.name
                },
                'status': 'active' if user.is_active else 'inactive'
            })

        # Calculate stats
        teacher_stats = {
            'active': len([t for t in teachers if t['status'] == 'active']),
            'pending': 0,  # We'll implement this based on invitations later
            'inactive': len([t for t in teachers if t['status'] == 'inactive']),
            'total': len(teachers)
        }

        return render(request, 'dashboard/partials/teachers_list.html', {
            'teachers': teachers,
            'teacher_stats': teacher_stats,
        })

    def _render_students_partial(self, request):
        """Render students list partial for HTMX updates"""
        from accounts.models import SchoolMembership, School
        from accounts.models.schools import SchoolRole
        from accounts.models.profiles import StudentProfile
        
        # Get user's schools
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)
        
        # Get students data with profiles
        student_memberships = SchoolMembership.objects.filter(
            school__in=user_schools,
            role=SchoolRole.STUDENT.value
        ).select_related('user', 'school')

        students = []
        for membership in student_memberships:
            user = membership.user
            try:
                profile = user.student_profile
                school_year = profile.school_year
            except (StudentProfile.DoesNotExist, AttributeError):
                school_year = ''

            students.append({
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'full_name': user.get_full_name(),
                'school_year': school_year,
                'school': {
                    'id': membership.school.id,
                    'name': membership.school.name
                },
                'status': 'active' if user.is_active else 'inactive'
            })

        student_stats = {
            'total': len(students)
        }

        return render(request, 'dashboard/partials/students_list.html', {
            'students': students,
            'student_stats': student_stats,
        })


class TeachersPartialView(View):
    """Render just the teachers partial for HTMX requests"""

    def get(self, request):
        """Return teachers partial"""
        people_view = PeopleView()
        return people_view._render_teachers_partial(request)


class StudentsPartialView(View):
    """Render just the students partial for HTMX requests"""

    def get(self, request):
        """Return students partial"""
        people_view = PeopleView()
        return people_view._render_students_partial(request)

