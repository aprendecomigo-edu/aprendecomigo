"""
API Tests for Class Completion Status.

Tests the class completion functionality.
Focuses on COMPLETED status transitions and validation.

Test Coverage:
- Marking confirmed classes as completed
- Permission checks for completion actions
- Status transition validation
- Preventing changes to completed classes
"""
from django.urls import reverse
from rest_framework import status

from scheduler.models import ClassSchedule, ClassStatus
from .test_base import SchedulerAPITestCase


class ClassCompletionTests(SchedulerAPITestCase):
    """Test class completion functionality."""

    def setUp(self):
        super().setUp()
        # Create class scheduled for past date so it can be completed
        self.confirmed_class = self.create_class_schedule(
            status=ClassStatus.CONFIRMED,
            teacher=self.teacher_profile,
            student=self.student_user,
            scheduled_date=self.past_date
        )

    def test_teacher_can_mark_own_class_completed(self):
        """Test that teachers can mark their own confirmed classes as completed."""
        self.authenticate_as_teacher()
        
        url = reverse('class-schedules-complete', kwargs={'pk': self.confirmed_class.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.confirmed_class.refresh_from_db()
        self.assertEqual(self.confirmed_class.status, ClassStatus.COMPLETED)

    def test_only_confirmed_classes_can_be_completed(self):
        """Test that only confirmed classes can be marked as completed."""
        scheduled_class = self.create_class_schedule(
            status=ClassStatus.SCHEDULED,
            teacher=self.teacher_profile,
            student=self.student_user,
            scheduled_date=self.past_date
        )
        
        self.authenticate_as_teacher()
        
        url = reverse('class-schedules-complete', kwargs={'pk': scheduled_class.id})
        response = self.client.post(url)
        
        self.assertValidationError(response)

    def test_admin_can_mark_any_class_completed(self):
        """Test that admins can mark any class in their school as completed."""
        self.authenticate_as_admin()
        
        url = reverse('class-schedules-complete', kwargs={'pk': self.confirmed_class.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_mark_class_completed(self):
        """Test that students cannot mark classes as completed."""
        self.authenticate_as_student()
        
        url = reverse('class-schedules-complete', kwargs={'pk': self.confirmed_class.id})
        response = self.client.post(url)
        
        self.assertPermissionDenied(response)

    def test_completion_with_optional_data(self):
        """Test completing class with optional completion data."""
        self.authenticate_as_teacher()
        
        test_cases = [
            {
                'data': {'actual_duration_minutes': 55},
                'expected_duration': 55,
                'description': 'with actual duration'
            },
            {
                'data': {'notes': 'Great progress on algebra'},
                'expected_notes': 'Great progress on algebra',
                'description': 'with completion notes'
            },
        ]
        
        for case in test_cases:
            with self.subTest(description=case['description']):
                # Create fresh confirmed class for each test
                test_class = self.create_class_schedule(
                    status=ClassStatus.CONFIRMED,
                    teacher=self.teacher_profile,
                    student=self.student_user,
                    scheduled_date=self.past_date
                )
                
                test_url = reverse('class-schedules-complete', kwargs={'pk': test_class.id})
                response = self.client.post(test_url, case['data'], format='json')
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                test_class.refresh_from_db()
                self.assertEqual(test_class.status, ClassStatus.COMPLETED)
                
                if 'expected_duration' in case:
                    self.assertEqual(test_class.actual_duration_minutes, case['expected_duration'])
                if 'expected_notes' in case:
                    self.assertEqual(test_class.completion_notes, case['expected_notes'])


class ClassNoShowTests(SchedulerAPITestCase):
    """Test class no-show functionality."""

    def setUp(self):
        super().setUp()
        # Create class scheduled for past date
        self.confirmed_class = self.create_class_schedule(
            status=ClassStatus.CONFIRMED,
            teacher=self.teacher_profile,
            student=self.student_user,
            scheduled_date=self.past_date
        )

    def test_teacher_can_mark_own_class_no_show(self):
        """Test that teachers can mark their own classes as no-show."""
        self.authenticate_as_teacher()
        
        url = reverse('class-schedules-no-show', kwargs={'pk': self.confirmed_class.id})
        data = {'reason': 'Student did not attend'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.confirmed_class.refresh_from_db()
        self.assertEqual(self.confirmed_class.status, ClassStatus.NO_SHOW)

    def test_no_show_with_different_types(self):
        """Test marking no-show with different no_show_type values."""
        self.authenticate_as_teacher()
        
        url = reverse('class-schedules-no-show', kwargs={'pk': self.confirmed_class.id})
        
        for no_show_type in ['student', 'teacher']:
            with self.subTest(no_show_type=no_show_type):
                test_class = self.create_class_schedule(
                    status=ClassStatus.CONFIRMED,
                    teacher=self.teacher_profile,
                    student=self.student_user,
                    scheduled_date=self.past_date
                )
                
                data = {
                    'reason': f'{no_show_type.title()} no-show',
                    'no_show_type': no_show_type
                }
                response = self.client.post(
                    reverse('class-schedules-no-show', kwargs={'pk': test_class.id}), 
                    data, 
                    format='json'
                )
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_mark_no_show(self):
        """Test that students cannot mark classes as no-show."""
        self.authenticate_as_student()
        
        url = reverse('class-schedules-no-show', kwargs={'pk': self.confirmed_class.id})
        data = {'reason': 'Teacher did not attend'}
        response = self.client.post(url, data, format='json')
        
        self.assertPermissionDenied(response)

    def test_admin_can_mark_any_class_no_show(self):
        """Test that admins can mark any class as no-show."""
        self.authenticate_as_admin()
        
        url = reverse('class-schedules-no-show', kwargs={'pk': self.confirmed_class.id})
        data = {'reason': 'Administrative no-show marking'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.confirmed_class.refresh_from_db()
        self.assertEqual(self.confirmed_class.status, ClassStatus.NO_SHOW)

    def test_completed_class_status_is_final(self):
        """Test that completed classes cannot be modified further."""
        completed_class = self.create_class_schedule(
            status=ClassStatus.COMPLETED,
            teacher=self.teacher_profile,
            student=self.student_user,
            scheduled_date=self.past_date
        )
        
        self.authenticate_as_teacher()
        
        # Test various operations that should fail on completed class
        test_operations = [
            ('cancel', 'class-schedules-cancel', {'reason': 'Cannot cancel completed'}),
            ('complete', 'class-schedules-complete', {'notes': 'Cannot complete again'}),
            ('no-show', 'class-schedules-no-show', {'reason': 'Cannot mark no-show'}),
        ]
        
        for operation, url_name, data in test_operations:
            with self.subTest(operation=operation):
                url = reverse(url_name, kwargs={'pk': completed_class.id})
                response = self.client.post(url, data, format='json')
                
                self.assertValidationError(response)