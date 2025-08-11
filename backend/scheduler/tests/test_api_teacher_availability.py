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
        # Should include the availability created in test setup
        self.assertGreaterEqual(len(response.data['results']), 5)  # Mon-Fri setup

    def test_teacher_can_update_own_availability(self):
        """Test that teachers can update their own availability."""
        availability = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile,
            day_of_week=WeekDay.MONDAY
        ).first()
        
        self.authenticate_as_teacher()
        
        url = reverse('teacher-availability-detail', kwargs={'pk': availability.id})
        data = {'end_time': '18:00:00'}  # Extend hours
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['end_time'], '18:00:00')

    def test_teacher_can_modify_other_teacher_availability_same_school(self):
        """Test that teachers can modify other teachers' availability in the same school (current behavior)."""
        other_availability = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile2
        ).first()
        
        self.authenticate_as_teacher()
        
        url = reverse('teacher-availability-detail', kwargs={'pk': other_availability.id})
        data = {'end_time': '18:00:00'}
        
        response = self.client.patch(url, data, format='json')
        
        # Current implementation allows teachers to modify other teachers' availability
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['end_time'], '18:00:00')

    def test_admin_can_manage_any_teacher_availability(self):
        """Test that admins can manage any teacher's availability in their school."""
        availability = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile,
            day_of_week=WeekDay.MONDAY
        ).first()
        
        self.authenticate_as_admin()
        
        url = reverse('teacher-availability-detail', kwargs={'pk': availability.id})
        data = {'end_time': '16:00:00'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_time_range_rejected(self):
        """Test that invalid time ranges (end before start) are rejected."""
        self.authenticate_as_teacher()
        
        data = {
            'school': self.school.id,
            'day_of_week': WeekDay.SUNDAY,
            'start_time': '12:00:00',
            'end_time': '09:00:00'  # Invalid: before start time
        }
        
        response = self.client.post(self.availability_url, data, format='json')
        
        self.assertValidationError(response)

    def test_overlapping_availability_allowed(self):
        """Test that overlapping availability periods are allowed (current behavior)."""
        self.authenticate_as_teacher()
        
        # Create availability that overlaps with existing Monday 9-5
        data = {
            'school': self.school.id,
            'day_of_week': WeekDay.MONDAY,
            'start_time': '10:00:00',  # Overlaps existing 9-5
            'end_time': '14:00:00'
        }
        
        response = self.client.post(self.availability_url, data, format='json')
        
        # The current implementation allows overlapping availability periods
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['day_of_week'], WeekDay.MONDAY)
        self.assertEqual(response.data['start_time'], '10:00:00')


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

    def test_teacher_can_create_all_day_unavailability(self):
        """Test that teachers can create all-day unavailability."""
        self.authenticate_as_teacher()
        
        data = {
            'school': self.school.id,
            'date': self.tomorrow.isoformat(),
            'is_all_day': True,
            'reason': 'Sick day'
        }
        
        response = self.client.post(self.unavailability_url, data, format='json')
        
        self.assertCreatedWithData(response, {
            'is_all_day': True,
            'reason': 'Sick day'
        })

    def test_teacher_can_list_own_unavailability(self):
        """Test that teachers can list their own unavailability periods."""
        # Create an unavailability period
        self.create_teacher_unavailability(
            teacher=self.teacher_profile,
            date=self.tomorrow,
            reason='Test unavailability'
        )
        
        self.authenticate_as_teacher()
        
        response = self.client.get(self.unavailability_url)
        
        self.assertListResponse(response, expected_count=1)

    def test_teacher_can_delete_own_unavailability(self):
        """Test that teachers can delete their own unavailability periods."""
        unavailability = self.create_teacher_unavailability(
            teacher=self.teacher_profile,
            date=self.tomorrow
        )
        
        self.authenticate_as_teacher()
        
        url = reverse('teacher-unavailability-detail', kwargs={'pk': unavailability.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            TeacherUnavailability.objects.filter(id=unavailability.id).exists()
        )

    def test_teacher_can_modify_other_teacher_unavailability_same_school(self):
        """Test that teachers can modify other teachers' unavailability in the same school (current behavior)."""
        other_unavailability = self.create_teacher_unavailability(
            teacher=self.teacher_profile2,
            date=self.tomorrow
        )
        
        self.authenticate_as_teacher()
        
        url = reverse('teacher-unavailability-detail', kwargs={'pk': other_unavailability.id})
        response = self.client.delete(url)
        
        # Current implementation allows teachers to modify other teachers' unavailability
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            TeacherUnavailability.objects.filter(id=other_unavailability.id).exists()
        )

    def test_unavailability_in_past_allowed(self):
        """Test that creating unavailability in the past is allowed (current behavior)."""
        self.authenticate_as_teacher()
        
        data = {
            'school': self.school.id,
            'date': self.past_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'reason': 'Past unavailability'
        }
        
        response = self.client.post(self.unavailability_url, data, format='json')
        
        # The current implementation allows creating past unavailability
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['date'], self.past_date.isoformat())
        self.assertEqual(response.data['reason'], 'Past unavailability')