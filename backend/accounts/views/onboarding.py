"""
Onboarding and discovery views for the accounts app.

This module contains all views related to tutor onboarding, discovery,
global search, and bulk operations.
"""

import logging

from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..db_queries import (
    list_school_ids_owned_or_managed,
)
from ..models import (
    Course,
    SchoolMembership,
    SchoolRole,
    TeacherProfile,
)
# Serializers will be imported when needed
from ..throttles import IPBasedThrottle
from ..views.auth import KnoxAuthenticatedAPIView

logger = logging.getLogger(__name__)


class GlobalSearchView(KnoxAuthenticatedAPIView):
    """
    Global search API for searching across teachers, students, classes, and school settings.
    """

    def get(self, request):
        """
        Perform global search across multiple entities.
        
        Query Parameters:
        - q: Search query string
        - entity_types: Comma-separated list of entity types to search (teachers, students, courses, etc.)
        - school_id: Optional school ID to limit search scope
        - limit: Maximum number of results per entity type (default: 10)
        """
        try:
            query = request.query_params.get('q', '').strip()
            if not query:
                return Response(
                    {'error': 'Search query is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse entity types
            entity_types = request.query_params.get('entity_types', 'teachers,students,courses')
            entity_types = [t.strip() for t in entity_types.split(',')]
            
            # Parse school filter
            school_id = request.query_params.get('school_id')
            if school_id:
                try:
                    school_id = int(school_id)
                except ValueError:
                    return Response(
                        {'error': 'Invalid school_id format'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Parse limit
            try:
                limit = int(request.query_params.get('limit', 10))
                limit = max(1, min(limit, 50))  # Between 1 and 50
            except ValueError:
                limit = 10
            
            # Perform search
            results = {}
            
            # Check if user has permission to search in the specified school
            user_school_ids = list_school_ids_owned_or_managed(request.user)
            if school_id and school_id not in user_school_ids:
                return Response(
                    {'error': 'You do not have permission to search in this school'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Search teachers
            if 'teachers' in entity_types:
                results['teachers'] = self._search_teachers(query, school_id, limit, user_school_ids)
            
            # Search students  
            if 'students' in entity_types:
                results['students'] = self._search_students(query, school_id, limit, user_school_ids)
                
            # Search courses
            if 'courses' in entity_types:
                results['courses'] = self._search_courses(query, school_id, limit)
            
            return Response(results)
            
        except Exception as e:
            logger.error(f"Error in global search: {str(e)}")
            return Response(
                {'error': 'Search failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _search_teachers(self, query, school_id, limit, user_school_ids):
        """Search for teachers."""
        from django.db import models
        
        # Base queryset for teachers
        teachers_qs = TeacherProfile.objects.select_related('user').filter(
            user__school_memberships__school_id__in=user_school_ids,
            user__school_memberships__role=SchoolRole.TEACHER,
            user__school_memberships__is_active=True
        )
        
        # Apply school filter if specified
        if school_id:
            teachers_qs = teachers_qs.filter(
                user__school_memberships__school_id=school_id
            )
        
        # Apply search filter
        teachers_qs = teachers_qs.filter(
            models.Q(user__name__icontains=query) |
            models.Q(user__email__icontains=query) |
            models.Q(bio__icontains=query) |
            models.Q(specialty__icontains=query)
        ).distinct()[:limit]
        
        # Serialize results
        results = []
        for teacher in teachers_qs:
            results.append({
                'id': teacher.id,
                'name': teacher.user.name,
                'email': teacher.user.email,
                'bio': teacher.bio[:100] + '...' if len(teacher.bio) > 100 else teacher.bio,
                'specialty': teacher.specialty,
                'type': 'teacher'
            })
        
        return results
    
    def _search_students(self, query, school_id, limit, user_school_ids):
        """Search for students."""
        from django.db import models
        from ..models import StudentProfile
        
        # Base queryset for students
        students_qs = StudentProfile.objects.select_related('user').filter(
            user__school_memberships__school_id__in=user_school_ids,
            user__school_memberships__role=SchoolRole.STUDENT,
            user__school_memberships__is_active=True
        )
        
        # Apply school filter if specified
        if school_id:
            students_qs = students_qs.filter(
                user__school_memberships__school_id=school_id
            )
        
        # Apply search filter
        students_qs = students_qs.filter(
            models.Q(user__name__icontains=query) |
            models.Q(user__email__icontains=query)
        ).distinct()[:limit]
        
        # Serialize results
        results = []
        for student in students_qs:
            results.append({
                'id': student.id,
                'name': student.user.name,
                'email': student.user.email,
                'school_year': student.school_year,
                'type': 'student'
            })
        
        return results
    
    def _search_courses(self, query, school_id, limit):
        """Search for courses."""
        from django.db import models
        
        # Base queryset for courses
        courses_qs = Course.objects.select_related('educational_system')
        
        # Apply search filter
        courses_qs = courses_qs.filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(code__icontains=query)
        )[:limit]
        
        # Serialize results
        results = []
        for course in courses_qs:
            results.append({
                'id': course.id,
                'name': course.name,
                'code': course.code,
                'description': course.description[:100] + '...' if len(course.description) > 100 else course.description,
                'educational_system': course.educational_system.name,
                'type': 'course'
            })
        
        return results


class BulkTeacherActionsView(KnoxAuthenticatedAPIView):
    """
    API endpoint for bulk teacher operations.
    """

    def post(self, request):
        """
        Perform bulk actions on teachers.
        
        Expected payload:
        {
            "action": "invite|activate|deactivate|delete",
            "teacher_ids": [1, 2, 3],
            "school_id": 123,
            "data": {...}  # Additional data for the action
        }
        """
        try:
            action = request.data.get('action')
            teacher_ids = request.data.get('teacher_ids', [])
            school_id = request.data.get('school_id')
            
            if not action:
                return Response(
                    {'error': 'Action is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not teacher_ids:
                return Response(
                    {'error': 'Teacher IDs are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not school_id:
                return Response(
                    {'error': 'School ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user can manage this school
            user_school_ids = list_school_ids_owned_or_managed(request.user)
            if school_id not in user_school_ids:
                return Response(
                    {'error': 'You do not have permission to manage teachers in this school'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Process the action
            if action == 'activate':
                return self._bulk_activate_teachers(teacher_ids, school_id)
            elif action == 'deactivate':
                return self._bulk_deactivate_teachers(teacher_ids, school_id)
            elif action == 'invite':
                return self._bulk_invite_teachers(request.data.get('data', {}), school_id)
            elif action == 'delete':
                return self._bulk_delete_teachers(teacher_ids, school_id)
            else:
                return Response(
                    {'error': f'Unsupported action: {action}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error in bulk teacher actions: {str(e)}")
            return Response(
                {'error': 'Bulk action failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _bulk_activate_teachers(self, teacher_ids, school_id):
        """Bulk activate teacher memberships."""
        updated_count = SchoolMembership.objects.filter(
            user__teacher_profile__id__in=teacher_ids,
            school_id=school_id,
            role=SchoolRole.TEACHER
        ).update(is_active=True)
        
        return Response({
            'message': f'Successfully activated {updated_count} teacher memberships',
            'updated_count': updated_count
        })
    
    def _bulk_deactivate_teachers(self, teacher_ids, school_id):
        """Bulk deactivate teacher memberships."""
        updated_count = SchoolMembership.objects.filter(
            user__teacher_profile__id__in=teacher_ids,
            school_id=school_id,
            role=SchoolRole.TEACHER
        ).update(is_active=False)
        
        return Response({
            'message': f'Successfully deactivated {updated_count} teacher memberships',
            'updated_count': updated_count
        })
    
    def _bulk_invite_teachers(self, invitation_data, school_id):
        """Bulk send teacher invitations."""
        # This would typically create multiple TeacherInvitation objects
        # Implementation would depend on the invitation system design
        emails = invitation_data.get('emails', [])
        
        if not emails:
            return Response(
                {'error': 'Email addresses are required for invitations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implement bulk invitation logic
        return Response({
            'message': f'Bulk invitation feature not yet implemented for {len(emails)} emails',
            'email_count': len(emails)
        })
    
    def _bulk_delete_teachers(self, teacher_ids, school_id):
        """Bulk delete teacher memberships (soft delete)."""
        # Note: This typically should be soft delete (deactivate) rather than hard delete
        updated_count = SchoolMembership.objects.filter(
            user__teacher_profile__id__in=teacher_ids,
            school_id=school_id,
            role=SchoolRole.TEACHER
        ).update(is_active=False)
        
        return Response({
            'message': f'Successfully removed {updated_count} teacher memberships',
            'removed_count': updated_count
        })


class TutorDiscoveryAPIView(APIView):
    """
    Public API endpoint for tutor discovery.
    
    Allows students and parents to search for tutors without authentication.
    Only exposes public profile information with proper privacy controls.
    """
    
    permission_classes = [AllowAny]  # Public endpoint
    throttle_classes = [IPBasedThrottle]  # Rate limiting for public endpoint
    
    def get(self, request):
        """
        Discover tutors based on search criteria.
        
        Query Parameters:
        - subjects: Comma-separated course IDs or names
        - rate_min: Minimum hourly rate (float)
        - rate_max: Maximum hourly rate (float) 
        - education_level: Education level filter
        - educational_system: Educational system ID
        - location: Location filter (future implementation)
        - availability: Availability filter (future implementation)
        - search: Free text search in bio, name, subjects
        - limit: Number of results to return (max 50, default 20)
        - offset: Pagination offset
        - ordering: Sort order (rate, completion_score, activity)
        
        Returns:
        List of public tutor profiles with:
        - Basic profile info (name, bio, specialty)
        - Subjects/courses taught
        - Rate information
        - Profile completion score
        - School information (if tutor is individual)
        """
        try:
            # Parse and validate parameters
            filters = self._parse_filters(request.query_params)
            pagination = self._parse_pagination(request.query_params)
            ordering = self._parse_ordering(request.query_params)
            
            # Generate cache key for performance
            cache_key = self._generate_cache_key(filters, pagination, ordering)
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)
            
            # Build queryset with privacy controls
            tutors_queryset = self._build_tutors_queryset(filters, ordering)
            
            # Apply pagination
            total_count = tutors_queryset.count()
            tutors_queryset = tutors_queryset[pagination['offset']:pagination['offset'] + pagination['limit']]
            
            # Serialize public data
            tutors_data = self._serialize_public_tutors(tutors_queryset, request)
            
            result = {
                'results': tutors_data,
                'count': len(tutors_data),
                'total': total_count,
                'next': self._get_next_url(request, pagination, total_count),
                'previous': self._get_previous_url(request, pagination)
            }
            
            # Cache result (shorter timeout for public endpoint)  
            cache.set(cache_key, result, timeout=300)  # 5 minutes
            
            return Response(result)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in tutor discovery: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve tutor data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _parse_filters(self, params):
        """Parse and validate filter parameters."""
        filters = {}
        
        # Subject filtering
        subjects = params.get('subjects')
        if subjects:
            subject_list = [s.strip() for s in subjects.split(',') if s.strip()]
            filters['subjects'] = subject_list
        
        # Rate filtering
        try:
            rate_min = params.get('rate_min')
            if rate_min:
                filters['rate_min'] = float(rate_min)
                if filters['rate_min'] < 0:
                    raise ValidationError("rate_min must be non-negative")
        except ValueError:
            raise ValidationError("Invalid rate_min format")
        
        try:
            rate_max = params.get('rate_max')
            if rate_max:
                filters['rate_max'] = float(rate_max)
                if filters['rate_max'] < 0:
                    raise ValidationError("rate_max must be non-negative")
        except ValueError:
            raise ValidationError("Invalid rate_max format")
        
        # Validate rate range
        if 'rate_min' in filters and 'rate_max' in filters:
            if filters['rate_min'] > filters['rate_max']:
                raise ValidationError("rate_min cannot be greater than rate_max")
        
        # Education level filtering
        education_level = params.get('education_level')
        if education_level:
            filters['education_level'] = education_level
        
        # Educational system filtering
        educational_system = params.get('educational_system')
        if educational_system:
            try:
                filters['educational_system'] = int(educational_system)
            except ValueError:
                raise ValidationError("Invalid educational_system format")
        
        # Search query
        search = params.get('search')
        if search:
            filters['search'] = search.strip()
        
        return filters
    
    def _parse_pagination(self, params):
        """Parse and validate pagination parameters."""
        try:
            limit = int(params.get('limit', 20))
            limit = min(max(1, limit), 50)  # Between 1 and 50
        except ValueError:
            limit = 20
        
        try:
            offset = int(params.get('offset', 0))
            offset = max(0, offset)  # Non-negative
        except ValueError:
            offset = 0
        
        return {'limit': limit, 'offset': offset}
    
    def _parse_ordering(self, params):
        """Parse and validate ordering parameters."""
        ordering = params.get('ordering', 'completion_score')
        valid_orderings = ['rate', '-rate', 'completion_score', '-completion_score', 'name', '-name']
        
        if ordering not in valid_orderings:
            ordering = 'completion_score'
        
        return ordering
    
    def _generate_cache_key(self, filters, pagination, ordering):
        """Generate cache key for the request."""
        key_parts = ['tutor_discovery']
        
        # Add filters to key
        for key, value in sorted(filters.items()):
            if isinstance(value, list):
                key_parts.append(f"{key}_{'_'.join(map(str, value))}")
            else:
                key_parts.append(f"{key}_{value}")
        
        # Add pagination and ordering
        key_parts.append(f"limit_{pagination['limit']}")
        key_parts.append(f"offset_{pagination['offset']}")
        key_parts.append(f"order_{ordering}")
        
        return '_'.join(key_parts)
    
    def _build_tutors_queryset(self, filters, ordering):
        """Build the tutors queryset with filters and ordering."""
        from django.db import models
        
        # Base queryset - only active teacher profiles with complete profiles
        queryset = TeacherProfile.objects.select_related('user').filter(
            user__school_memberships__role=SchoolRole.TEACHER,
            user__school_memberships__is_active=True,
            is_profile_complete=True  # Only show complete profiles publicly
        ).distinct()
        
        # Apply filters
        if 'subjects' in filters:
            # Filter by teaching subjects
            queryset = queryset.filter(
                teacher_courses__course__name__in=filters['subjects']
            ).distinct()
        
        if 'rate_min' in filters:
            queryset = queryset.filter(hourly_rate__gte=filters['rate_min'])
        
        if 'rate_max' in filters:
            queryset = queryset.filter(hourly_rate__lte=filters['rate_max'])
        
        if 'educational_system' in filters:
            queryset = queryset.filter(
                teacher_courses__course__educational_system_id=filters['educational_system']
            ).distinct()
        
        if 'search' in filters:
            search_query = filters['search']
            queryset = queryset.filter(
                models.Q(user__name__icontains=search_query) |
                models.Q(bio__icontains=search_query) |
                models.Q(specialty__icontains=search_query) |
                models.Q(teaching_subjects__icontains=search_query)
            ).distinct()
        
        # Apply ordering
        ordering_map = {
            'rate': 'hourly_rate',
            '-rate': '-hourly_rate',
            'completion_score': '-profile_completion_score',
            '-completion_score': 'profile_completion_score',
            'name': 'user__name',
            '-name': '-user__name'
        }
        
        queryset = queryset.order_by(ordering_map.get(ordering, '-profile_completion_score'))
        
        return queryset
    
    def _serialize_public_tutors(self, tutors_queryset, request):
        """Serialize tutor data for public consumption."""
        tutors_data = []
        
        for tutor in tutors_queryset:
            # Only expose public information
            tutor_data = {
                'id': tutor.id,
                'name': tutor.user.name,
                'bio': tutor.bio,
                'specialty': tutor.specialty,
                'hourly_rate': float(tutor.hourly_rate) if tutor.hourly_rate else None,
                'profile_completion_score': float(tutor.profile_completion_score),
                'teaching_subjects': tutor.teaching_subjects,
                'education_background': tutor.education_background,
                'teaching_experience': tutor.teaching_experience,
                # Include school info for individual tutors
                'schools': []
            }
            
            # Add school information (public info only)
            for membership in tutor.user.school_memberships.filter(
                role=SchoolRole.TEACHER, 
                is_active=True
            ).select_related('school'):
                school_info = {
                    'id': membership.school.id,
                    'name': membership.school.name,
                    'description': membership.school.description
                }
                tutor_data['schools'].append(school_info)
            
            tutors_data.append(tutor_data)
        
        return tutors_data
    
    def _get_next_url(self, request, pagination, total_count):
        """Generate next page URL."""
        next_offset = pagination['offset'] + pagination['limit']
        if next_offset >= total_count:
            return None
        
        # Build URL with updated offset
        query_params = request.query_params.copy()
        query_params['offset'] = next_offset
        return f"{request.build_absolute_uri('?')}{'&'.join([f'{k}={v}' for k, v in query_params.items()])}"
    
    def _get_previous_url(self, request, pagination):
        """Generate previous page URL."""
        if pagination['offset'] <= 0:
            return None
        
        prev_offset = max(0, pagination['offset'] - pagination['limit'])
        
        # Build URL with updated offset
        query_params = request.query_params.copy()
        query_params['offset'] = prev_offset
        return f"{request.build_absolute_uri('?')}{'&'.join([f'{k}={v}' for k, v in query_params.items()])}"


class TutorOnboardingAPIView(KnoxAuthenticatedAPIView):
    """
    API endpoints for individual tutor onboarding process.
    """

    def get(self, request):
        """
        Get current onboarding status and progress.
        """
        try:
            # Check if user has teacher profile
            if not hasattr(request.user, 'teacher_profile'):
                return Response({
                    'onboarding_complete': False,
                    'current_step': 'create_profile',
                    'progress_percentage': 0,
                    'next_action': 'Create teacher profile'
                })
            
            teacher_profile = request.user.teacher_profile
            
            # Calculate onboarding progress
            progress_data = self._calculate_onboarding_progress(teacher_profile)
            
            return Response(progress_data)
            
        except Exception as e:
            logger.error(f"Error getting onboarding status: {str(e)}")
            return Response(
                {'error': 'Failed to get onboarding status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Complete onboarding step or update progress.
        """
        try:
            step = request.data.get('step')
            step_data = request.data.get('data', {})
            
            if not step:
                return Response(
                    {'error': 'Onboarding step is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process the onboarding step
            result = self._process_onboarding_step(request.user, step, step_data)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error processing onboarding step: {str(e)}")
            return Response(
                {'error': 'Failed to process onboarding step'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_onboarding_progress(self, teacher_profile):
        """Calculate current onboarding progress."""
        steps = {
            'profile_created': bool(teacher_profile),
            'bio_completed': bool(teacher_profile.bio),
            'specialty_set': bool(teacher_profile.specialty),
            'rate_set': bool(teacher_profile.hourly_rate),
            'subjects_added': bool(teacher_profile.teaching_subjects),
            'education_added': bool(teacher_profile.education_background),
        }
        
        completed_steps = sum(steps.values())
        total_steps = len(steps)
        progress_percentage = (completed_steps / total_steps) * 100
        
        # Determine current step
        current_step = 'complete'
        if not steps['profile_created']:
            current_step = 'create_profile'
        elif not steps['bio_completed']:
            current_step = 'add_bio'
        elif not steps['specialty_set']:
            current_step = 'set_specialty'
        elif not steps['rate_set']:
            current_step = 'set_rate'
        elif not steps['subjects_added']:
            current_step = 'add_subjects'
        elif not steps['education_added']:
            current_step = 'add_education'
        
        return {
            'onboarding_complete': progress_percentage >= 100,
            'current_step': current_step,
            'progress_percentage': progress_percentage,
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'steps': steps
        }
    
    def _process_onboarding_step(self, user, step, step_data):
        """Process a specific onboarding step."""
        # This would contain step-specific logic
        # For now, return a placeholder response
        return {
            'success': True,
            'step': step,
            'message': f'Step {step} processed successfully',
            'next_step': self._get_next_step(step)
        }
    
    def _get_next_step(self, current_step):
        """Get the next step in the onboarding process."""
        step_sequence = [
            'create_profile',
            'add_bio',
            'set_specialty', 
            'set_rate',
            'add_subjects',
            'add_education',
            'complete'
        ]
        
        try:
            current_index = step_sequence.index(current_step)
            if current_index < len(step_sequence) - 1:
                return step_sequence[current_index + 1]
        except ValueError:
            pass
        
        return 'complete'


class TutorOnboardingGuidanceView(TutorOnboardingAPIView):
    """Dedicated view for tutor onboarding guidance endpoint."""
    
    def get(self, request):
        """Get onboarding guidance and tips."""
        return Response({
            'guidance': {
                'welcome_message': 'Welcome to Aprende Comigo! Let\'s set up your tutor profile.',
                'steps': [
                    {
                        'step': 'create_profile',
                        'title': 'Create Your Profile',
                        'description': 'Tell us about yourself and your teaching background',
                        'tips': ['Be authentic and professional', 'Highlight your expertise']
                    },
                    {
                        'step': 'add_bio',
                        'title': 'Write Your Bio',
                        'description': 'Share your teaching philosophy and approach',
                        'tips': ['Keep it concise but informative', 'Mention your teaching style']
                    },
                    {
                        'step': 'set_specialty',
                        'title': 'Set Your Specialty',
                        'description': 'Choose your main subject areas',
                        'tips': ['Focus on subjects you\'re most confident in']
                    },
                    {
                        'step': 'set_rate',
                        'title': 'Set Your Hourly Rate',
                        'description': 'Define your teaching rate',
                        'tips': ['Research market rates in your area', 'Consider your experience level']
                    }
                ]
            }
        })


class TutorOnboardingStartView(TutorOnboardingAPIView):
    """Dedicated view for tutor onboarding start endpoint."""
    
    def post(self, request):
        """Start the onboarding process."""
        return super().post(request)


class TutorOnboardingValidateStepView(TutorOnboardingAPIView):
    """Dedicated view for tutor onboarding step validation endpoint."""
    
    def post(self, request):
        """Validate a specific onboarding step without saving."""
        try:
            step = request.data.get('step')
            step_data = request.data.get('data', {})
            
            if not step:
                return Response(
                    {'error': 'Step is required for validation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate the step data
            validation_result = self._validate_step_data(step, step_data)
            
            return Response(validation_result)
            
        except Exception as e:
            logger.error(f"Error validating onboarding step: {str(e)}")
            return Response(
                {'error': 'Step validation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_step_data(self, step, step_data):
        """Validate step data without saving."""
        errors = {}
        
        if step == 'add_bio':
            bio = step_data.get('bio', '').strip()
            if not bio:
                errors['bio'] = 'Bio is required'
            elif len(bio) > 1000:
                errors['bio'] = 'Bio must be less than 1000 characters'
        
        elif step == 'set_rate':
            rate = step_data.get('hourly_rate')
            if not rate:
                errors['hourly_rate'] = 'Hourly rate is required'
            else:
                try:
                    rate = float(rate)
                    if rate < 5.0 or rate > 200.0:
                        errors['hourly_rate'] = 'Rate must be between $5.00 and $200.00'
                except ValueError:
                    errors['hourly_rate'] = 'Invalid rate format'
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'step': step
        }


class TutorOnboardingSaveProgressView(TutorOnboardingAPIView):
    """Dedicated view for tutor onboarding save progress endpoint."""
    
    def post(self, request):
        """Save onboarding progress."""
        return super().post(request)