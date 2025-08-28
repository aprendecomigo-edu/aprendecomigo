"""
API views for accounts app - Teacher and Student management
"""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from .models import (
    CustomUser,
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile,
)


def get_user_schools(user):
    """Get all schools where the user is a member."""
    if user.is_staff or user.is_superuser:
        # Staff/superuser can see all schools
        return School.objects.all()

    # Get schools through SchoolMembership
    school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
    return School.objects.filter(id__in=school_ids)


@method_decorator(login_required, name='dispatch')
class TeacherAPIView(View):
    """API endpoints for teacher management"""

    def get(self, request):
        """List all teachers in user's schools"""
        user_schools = get_user_schools(request.user)

        # Get all teacher memberships from user's schools
        teacher_memberships = SchoolMembership.objects.filter(
            school__in=user_schools,
            role=SchoolRole.TEACHER.value
        ).select_related('user', 'school')

        teachers = []
        for membership in teacher_memberships:
            user = membership.user
            # Try to get teacher profile if it exists
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
                'first_name': user.first_name,
                'last_name': user.last_name,
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

        return JsonResponse({'teachers': teachers})

    def post(self, request):
        """Create a new teacher profile for an existing user"""
        try:
            data = json.loads(request.body)
            email = data.get('email')
            bio = data.get('bio', '')
            specialty = data.get('specialty', '')

            if not email:
                return JsonResponse({'error': 'Email is required'}, status=400)

            # Check if user exists
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # Create new user if doesn't exist
                user = CustomUser.objects.create_user(
                    email=email,
                    username=email,
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', '')
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
            user_schools = get_user_schools(request.user)
            for school in user_schools:
                SchoolMembership.objects.get_or_create(
                    user=user,
                    school=school,
                    defaults={'role': SchoolRole.TEACHER.value}
                )

            return JsonResponse({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'bio': bio,
                'specialty': specialty,
                'created': created
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(login_required, name='dispatch')
class StudentAPIView(View):
    """API endpoints for student management"""

    def get(self, request):
        """List all students in user's schools"""
        user_schools = get_user_schools(request.user)

        # Get all student memberships from user's schools
        student_memberships = SchoolMembership.objects.filter(
            school__in=user_schools,
            role=SchoolRole.STUDENT.value
        ).select_related('user', 'school')

        students = []
        for membership in student_memberships:
            user = membership.user
            # Try to get student profile if it exists
            try:
                profile = user.student_profile
                grade = profile.grade
            except StudentProfile.DoesNotExist:
                grade = ''

            students.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
                'grade': grade,
                'school': {
                    'id': membership.school.id,
                    'name': membership.school.name
                },
                'status': 'active' if user.is_active else 'inactive'
            })

        return JsonResponse({'students': students})

    def post(self, request):
        """Create a new student profile for an existing user"""
        try:
            data = json.loads(request.body)
            email = data.get('email')
            grade = data.get('grade', '')

            if not email:
                return JsonResponse({'error': 'Email is required'}, status=400)

            # Check if user exists
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # Create new user if doesn't exist
                user = CustomUser.objects.create_user(
                    email=email,
                    username=email,
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', '')
                )

            # Create or update student profile
            student_profile, created = StudentProfile.objects.get_or_create(
                user=user,
                defaults={'grade': grade}
            )
            if not created:
                student_profile.grade = grade
                student_profile.save()

            # Add to user's schools as student
            user_schools = get_user_schools(request.user)
            for school in user_schools:
                SchoolMembership.objects.get_or_create(
                    user=user,
                    school=school,
                    defaults={'role': SchoolRole.STUDENT.value}
                )

            return JsonResponse({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'grade': grade,
                'created': created
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
