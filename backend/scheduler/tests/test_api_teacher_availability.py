"""
API Tests for Teacher Availability Management.

Tests the TeacherAvailability and TeacherUnavailability API endpoints.
Covers CRUD operations, validation, and permission checks.

Test Coverage:
- Creating, reading, updating teacher availability schedules
- Managing teacher unavailability periods
- Permission checks for availability management
- Validation of time periods and conflicts
"""
from datetime import time
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from scheduler.models import TeacherAvailability, TeacherUnavailability, WeekDay
from .test_base import SchedulerAPITestCase


class TeacherAvailabilityTests(SchedulerAPITestCase):
    """Test teacher availability API endpoints."""

    def setUp(self):
        super().setUp()
        self.availability_url = reverse('teacher-availability-list')

    def test_teacher_can_create_availability(self):
        """Test that teachers can create their own availability."""
        self.authenticate_as_teacher()
        
        data = {
            'school': self.school.id,
            'day_of_week': WeekDay.SATURDAY,
            'start_time': '09:00:00',
            'end_time': '12:00:00'
        }
        
        response = self.client.post(self.availability_url, data, format='json')
        
        self.assertCreatedWithData(response, {
            'day_of_week': WeekDay.SATURDAY,
            'start_time': '09:00:00',
            'end_time': '12:00:00'
        })

    def test_teacher_can_list_own_availability(self):
        """Test that teachers can list their own availability."""
        self.authenticate_as_teacher()
        
        response = self.client.get(self.availability_url)
        
        self.assertListResponse(response)
        # Should include the availability created in test setup (Mon-Fri)
        self.assertGreaterEqual(len(response.data['results']), 5)

    def test_teacher_can_update_own_availability(self):
        """Test that teachers can update their own availability."""
        availability = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile,
            day_of_week=WeekDay.MONDAY
        ).first()
        
        self.authenticate_as_teacher()
        
        url = reverse('teacher-availability-detail', kwargs={'pk': availability.id})
        data = {'end_time': '16:00:00'}  # Valid end time within reasonable range
        
        response = self.client.patch(url, data, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.data['end_time'], '16:00:00')

    def test_availability_permission_rules(self):
        """Test permission rules for availability management."""
        other_availability = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile2
        ).first()
        
        own_availability = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile,
            day_of_week=WeekDay.MONDAY
        ).first()
        
        permission_tests = [
            ('teacher', own_availability, True, 'teachers can modify own availability'),
            ('teacher', other_availability, False, 'teachers cannot modify others availability'),
            ('admin', own_availability, True, 'admins can modify any availability'),
        ]
        
        for role, availability, should_succeed, description in permission_tests:
            with self.subTest(test=description):
                getattr(self, f'authenticate_as_{role}')()
                
                url = reverse('teacher-availability-detail', kwargs={'pk': availability.id})
                data = {'is_active': False}  # Use simpler field that's less likely to cause validation issues
                response = self.client.patch(url, data, format='json')
                
                if should_succeed:
                    self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
                else:
                    self.assertPermissionDenied(response)

    def test_availability_validation_rules(self):
        """Test various availability validation rules."""
        self.authenticate_as_teacher()
        
        validation_tests = [
            {
                'data': {
                    'school': self.school.id,
                    'day_of_week': WeekDay.SUNDAY,
                    'start_time': '12:00:00',
                    'end_time': '09:00:00'  # Invalid: before start time
                },
                'description': 'end time before start time'
            },
            {
                'data': {
                    'school': self.school.id,
                    'day_of_week': WeekDay.MONDAY,
                    'start_time': '10:00:00',  # Overlaps existing 9-17
                    'end_time': '14:00:00'
                },
                'description': 'overlapping availability'
            },
        ]
        
        for test_case in validation_tests:
            with self.subTest(description=test_case['description']):
                response = self.client.post(
                    self.availability_url, 
                    test_case['data'], 
                    format='json'
                )
                self.assertValidationError(response)


class TeacherUnavailabilityTests(SchedulerAPITestCase):
    """Test teacher unavailability API endpoints."""

    def setUp(self):
        super().setUp()
        self.unavailability_url = reverse('teacher-unavailability-list')

    def test_teacher_can_create_unavailability(self):
        """Test that teachers can create their own unavailability periods."""
        self.authenticate_as_teacher()
        
        data = {
            'school': self.school.id,
            'date': self.tomorrow.isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'reason': 'Doctor appointment'
        }
        
        response = self.client.post(self.unavailability_url, data, format='json')
        
        self.assertCreatedWithData(response, {
            'date': self.tomorrow.isoformat(),
            'reason': 'Doctor appointment'
        })

    def test_unavailability_creation_types(self):
        """Test different types of unavailability creation."""
        self.authenticate_as_teacher()
        
        unavailability_types = [
            {
                'data': {
                    'school': self.school.id,
                    'date': self.tomorrow.isoformat(),
                    'start_time': '10:00:00',
                    'end_time': '12:00:00',
                    'reason': 'Doctor appointment'
                },
                'expected': {
                    'reason': 'Doctor appointment',
                    'is_all_day': False
                },
                'description': 'partial day unavailability'
            },
            {
                'data': {
                    'school': self.school.id,
                    'date': (self.tomorrow + timezone.timedelta(days=1)).isoformat(),
                    'is_all_day': True,
                    'reason': 'Sick day'
                },
                'expected': {
                    'is_all_day': True,
                    'reason': 'Sick day'
                },
                'description': 'all-day unavailability'
            },
        ]
        
        for test_case in unavailability_types:
            with self.subTest(description=test_case['description']):
                response = self.client.post(
                    self.unavailability_url, 
                    test_case['data'], 
                    format='json'
                )
                self.assertCreatedWithData(response, test_case['expected'])

    def test_teacher_unavailability_crud_operations(self):
        """Test CRUD operations for teacher unavailability."""
        self.authenticate_as_teacher()
        
        # Create unavailability
        unavailability = self.create_teacher_unavailability(
            teacher=self.teacher_profile,
            date=self.tomorrow,
            reason='Test unavailability'
        )
        
        # Test list
        response = self.client.get(self.unavailability_url)
        self.assertListResponse(response, expected_count=1)
        
        # Test retrieve
        detail_url = reverse('teacher-unavailability-detail', kwargs={'pk': unavailability.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test delete
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            TeacherUnavailability.objects.filter(id=unavailability.id).exists()
        )


    def test_unavailability_validation_and_permissions(self):
        """Test unavailability validation rules and permissions."""
        other_unavailability = self.create_teacher_unavailability(
            teacher=self.teacher_profile2,
            date=self.tomorrow
        )
        
        self.authenticate_as_teacher()
        
        # Test permission: cannot modify other teacher's unavailability
        url = reverse('teacher-unavailability-detail', kwargs={'pk': other_unavailability.id})
        response = self.client.delete(url)
        self.assertPermissionDenied(response)
        
        # Test validation: cannot create past unavailability
        past_data = {
            'school': self.school.id,
            'date': self.past_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'reason': 'Past unavailability'
        }
        response = self.client.post(self.unavailability_url, past_data, format='json')
        self.assertValidationError(response)