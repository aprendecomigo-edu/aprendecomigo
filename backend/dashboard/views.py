"""
Dashboard views with clean URLs outside of accounts app
"""

import logging

from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.views import View

User = get_user_model()
logger = logging.getLogger('accounts.auth')

class DashboardView(View):
    """Main dashboard view that renders appropriate template based on user role"""
    
    def get(self, request):
        """Render appropriate dashboard template based on user role"""
        # Debug session information
        logger.info(f"Dashboard access: session_key={request.session.session_key}, authenticated={request.user.is_authenticated}, user={request.user}")
        
        # Auto-login for testing (TODO: Remove in production)
        if not request.user.is_authenticated:
            try:
                admin_user = User.objects.get(email='admin@test.com')
                login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
                logger.info(f"Auto-login successful for testing user: {admin_user}")
            except User.DoesNotExist:
                # Create a test admin user if it doesn't exist
                from django.contrib.auth.models import User as AuthUser
                admin_user = AuthUser.objects.create_user(
                    username='admin@test.com',
                    email='admin@test.com',
                    first_name='Admin',
                    last_name='User',
                    is_staff=True,
                    is_superuser=True
                )
                admin_user.set_unusable_password()
                admin_user.save()
                login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
                logger.info(f"Created and logged in test admin user: {admin_user}")
        
        # If still not authenticated after auto-login attempt, redirect to signin
        if not request.user.is_authenticated:
            logger.warning(f"Unauthenticated dashboard access from session {request.session.session_key}")
            return redirect('accounts:signin')
        
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
            return self._render_general_dashboard(request)
    
    def _render_admin_dashboard(self, request):
        """Render admin dashboard directly at /dashboard/ - moved from AdminDashboardView"""
        from datetime import timedelta
        import json
        
        from django.utils import timezone
        
        from accounts.models import StudentProfile, TeacherProfile
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
        from datetime import datetime
        from django.db import models
        from education.models import Payment
        current_month = today.month
        current_year = today.year
        
        try:
            revenue_this_month = Payment.objects.filter(
                created_at__year=current_year,
                created_at__month=current_month,
                status='completed'
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            revenue_this_month = int(revenue_this_month / 100)  # Convert cents to euros
        except Exception:
            revenue_this_month = 0  # Default to 0 if no payment data
        
        # Get tasks from task management system
        from tasks.models import Task
        try:
            user_tasks = Task.objects.filter(assigned_to=user).order_by('-created_at')[:10]
            tasks = []
            for task in user_tasks:
                tasks.append({
                    'id': task.pk,
                    'title': task.title,
                    'priority': task.priority.lower() if task.priority else 'medium',
                    'status': 'completed' if task.completed else 'pending',
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
    
    def _render_general_dashboard(self, request):
        """Render general dashboard for users without specific roles"""
        return render(request, 'dashboard/general_dashboard.html', {
            'title': 'Dashboard - Aprende Comigo',
            'user': request.user,
            'active_section': 'dashboard'
        })




class CalendarView(View):
    """Calendar page view - separate page with clean URL"""
    
    def get(self, request):
        """Render calendar page"""
        from django.contrib.auth import get_user_model, login
        from datetime import timedelta
        import json
        
        User = get_user_model()  # Move outside if block to fix scope issue
        
        if not request.user.is_authenticated:
            # TODO: Temporary authentication for testing - use same pattern as accounts views
            try:
                admin_user = User.objects.get(email='admin@test.com')
                login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
            except User.DoesNotExist:
                return redirect('accounts:signin')
        
        # TODO: Get test user for testing
        try:
            test_user = User.objects.get(email='admin@test.com')
        except User.DoesNotExist:
            test_user = request.user if request.user.is_authenticated else None
        
        # Load calendar events using same logic as dashboard for consistency
        from datetime import timedelta
        from django.utils import timezone
        from scheduler.models import ClassSchedule
        
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
                class_type_display = schedule.get_class_type_display() if schedule.class_type else 'Aula'
                title = f"{class_type_display} - {teacher_name}"
                
            events.append({
                'id': schedule.pk,
                'title': title,
                'description': schedule.description or f'{teacher_name} - {schedule.get_class_type_display()}',
                'start': f"{schedule.scheduled_date} {schedule.start_time.strftime('%H:%M') if schedule.start_time else '09:00'}",
                'end': f"{schedule.scheduled_date} {schedule.end_time.strftime('%H:%M') if schedule.end_time else '10:00'}",
                'status': schedule.status.lower() or 'scheduled',
                'type': schedule.class_type,
                'teacher_name': teacher_name,
                'student_name': student_name,
                'participants_names': [student_name]
            })
        
        return render(request, 'dashboard/calendar.html', {
            'title': 'Calendar - Aprende Comigo',
            'user': test_user,
            'active_section': 'calendar',
            'initial_events': json.dumps(events)  # Pass events as JSON
        })


class ChatView(View):
    """Chat page view with real-time messaging"""
    
    def get(self, request):
        """Render chat page"""
        from django.contrib.auth import get_user_model
        User = get_user_model()  # Add missing User definition
        
        # TODO: Remove authentication bypass in production
        # if not request.user.is_authenticated:
        #     return redirect('accounts:signin')
        
        # TODO: Get test user for testing
        try:
            test_user = User.objects.get(email='admin@test.com')
        except User.DoesNotExist:
            test_user = request.user if request.user.is_authenticated else None
        
        return render(request, 'dashboard/chat.html', {
            'title': 'Chat - Aprende Comigo',
            'user': test_user,
            'active_section': 'chat'
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


class AnalyticsView(View):
    """Analytics and reports page"""
    
    def get(self, request):
        """Render analytics page"""
        # TODO: Remove authentication bypass in production
        # if not request.user.is_authenticated:
        #     return redirect('accounts:signin')
        
        return render(request, 'dashboard/analytics.html', {
            'title': 'Analytics - Aprende Comigo',
            'user': request.user,
            'active_section': 'analytics'
        })


class InvitationsView(View):
    """Invitations management page"""
    
    def get(self, request):
        """Render invitations page"""
        # TODO: Remove authentication bypass in production
        # if not request.user.is_authenticated:
        #     return redirect('accounts:signin')
        
        return render(request, 'dashboard/invitations.html', {
            'title': 'Invitations - Aprende Comigo',
            'user': request.user,
            'active_section': 'invitations'
        })


class PeopleView(View):
    """Unified people management page with tabs for teachers, students, staff"""
    
    def get(self, request):
        """Render people management page"""
        from django.contrib.auth import get_user_model, login
        User = get_user_model()
        
        if not request.user.is_authenticated:
            # TODO: Temporary authentication for testing - use same pattern as accounts views
            try:
                admin_user = User.objects.get(email='admin@test.com')
                login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
            except User.DoesNotExist:
                return redirect('accounts:signin')
        
        # TODO: Get test user for testing
        try:
            test_user = User.objects.get(email='admin@test.com')
        except User.DoesNotExist:
            test_user = request.user if request.user.is_authenticated else None
        
        return render(request, 'dashboard/people.html', {
            'title': 'People - Aprende Comigo',
            'user': test_user,
            'active_section': 'people'
        })

