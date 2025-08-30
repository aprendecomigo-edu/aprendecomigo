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

        # Get user's active school membership to determine role
        active_membership = SchoolMembership.objects.filter(
            user=request.user, 
            is_active=True
        ).first()

        if active_membership:
            role = active_membership.role
            # Check school role first (higher priority than individual profiles)
            if role in [SchoolRole.SCHOOL_OWNER.value, SchoolRole.SCHOOL_ADMIN.value]:
                return self._render_admin_dashboard(request)
            elif role == SchoolRole.TEACHER.value:
                return self._render_teacher_dashboard(request)
            elif role == SchoolRole.STUDENT.value:
                return self._render_student_dashboard(request)
            elif role == SchoolRole.PARENT.value:
                return self._render_parent_dashboard(request)

        # TODO: No Fallbacks something is wrong if there's no active membership
        logger.error(f"User {request.user.id} has no active school membership.")
        return JsonResponse({'error': 'No active school membership found.'}, status=403)

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
                return render(request, 'shared/partials/error_message.html', {
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
                return render(request, 'shared/partials/error_message.html', {
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
                return render(request, 'shared/partials/error_message.html', {
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
            response = render(request, 'shared/partials/success_message.html', {
                'message': f'Invitation sent successfully to {email}!'
            })
            response['HX-Trigger'] = 'refreshInvitations'
            return response

        except Exception as e:
            return render(request, 'shared/partials/error_message.html', {
                'error': f'Failed to send invitation: {str(e)}'
            })

    def _handle_resend_invitation(self, request):
        """Handle resending an existing invitation"""
        try:
            invitation_id = request.POST.get('invitation_id')
            if not invitation_id:
                return render(request, 'shared/partials/error_message.html', {
                    'error': 'Invitation ID is required'
                })

            invitation = TeacherInvitation.objects.get(pk=invitation_id)
            
            # TODO: Resend email using messaging service
            invitation.mark_email_sent()

            response = render(request, 'shared/partials/success_message.html', {
                'message': f'Invitation resent to {invitation.email}!'
            })
            response['HX-Trigger'] = 'refreshInvitations'
            return response

        except TeacherInvitation.DoesNotExist:
            return render(request, 'shared/partials/error_message.html', {
                'error': 'Invitation not found'
            })
        except Exception as e:
            return render(request, 'shared/partials/error_message.html', {
                'error': f'Failed to resend invitation: {str(e)}'
            })

    def _handle_cancel_invitation(self, request):
        """Handle canceling an existing invitation"""
        try:
            invitation_id = request.POST.get('invitation_id')
            if not invitation_id:
                return render(request, 'shared/partials/error_message.html', {
                    'error': 'Invitation ID is required'
                })

            invitation = TeacherInvitation.objects.get(pk=invitation_id)
            invitation.cancel()

            response = render(request, 'shared/partials/success_message.html', {
                'message': f'Invitation to {invitation.email} has been cancelled!'
            })
            response['HX-Trigger'] = 'refreshInvitations'
            return response

        except TeacherInvitation.DoesNotExist:
            return render(request, 'shared/partials/error_message.html', {
                'error': 'Invitation not found'
            })
        except Exception as e:
            return render(request, 'shared/partials/error_message.html', {
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
                return render(request, 'shared/partials/error_message.html', {
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
            return render(request, 'shared/partials/error_message.html', {
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
                return render(request, 'shared/partials/error_message.html', {
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
            return render(request, 'shared/partials/error_message.html', {
                'error': f'Failed to add student: {str(e)}'
            })

    def _handle_invite_teacher(self, request):
        """Handle teacher invitation"""
        # TODO: Implement teacher invitation logic
        return render(request, 'shared/partials/success_message.html', {
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

