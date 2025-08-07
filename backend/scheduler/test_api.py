"""
Streamlined API Tests for Enhanced Scheduler Models and Serializers.
Focus on essential functionality from the scheduling refactor.
"""
import json
from datetime import date, datetime, time, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    TeacherProfile,
    SchoolRole,
    SchoolSettings,
    EducationalSystem,
)
from .models import (
    ClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
    ClassType,
    ClassStatus,
    WeekDay,
)


class SchedulerAPITestCase(TestCase):
    """Base test case with common setup for scheduler API tests."""

    def setUp(self):
        """Set up test data."""
        # Create educational system and school
        self.edu_system = EducationalSystem.objects.create(
            name="Test System", code="custom", description="Test educational system"
        )
        self.school = School.objects.create(name="Test School", description="Test Description")
        self.school_settings = SchoolSettings.objects.create(
            school=self.school, timezone="America/New_York", educational_system=self.edu_system
        )

        # Create test users
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com", name="Test Teacher", password="testpass123"
        )
        self.teacher_profile = TeacherProfile.objects.create(user=self.teacher_user, bio="Test bio")

        self.student1 = CustomUser.objects.create_user(
            email="student1@test.com", name="Student One", password="testpass123"
        )
        self.student2 = CustomUser.objects.create_user(
            email="student2@test.com", name="Student Two", password="testpass123"
        )
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com", name="Admin User", password="testpass123"
        )

        # Create school memberships
        SchoolMembership.objects.create(
            user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER
        )
        SchoolMembership.objects.create(
            user=self.student1, school=self.school, role=SchoolRole.STUDENT
        )
        SchoolMembership.objects.create(
            user=self.student2, school=self.school, role=SchoolRole.STUDENT
        )
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_OWNER
        )

        # Set up test dates and API client
        self.future_date = timezone.now().date() + timedelta(days=7)
        self.past_date = timezone.now().date() - timedelta(days=7)
        self.client = APIClient()

        # Create teacher availability for testing
        self.availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=self.future_date.strftime("%A").lower(),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )


class ClassScheduleCRUDAPITests(SchedulerAPITestCase):
    """Test essential CRUD operations for ClassSchedule API."""

    def test_create_individual_class_success(self):
        """Test creating individual class via API."""
        self.client.force_authenticate(user=self.student1)
        
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'student': self.student1.id,
            'school': self.school.id,
            'title': 'Math Tutoring',
            'class_type': ClassType.INDIVIDUAL,
            'scheduled_date': self.future_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Math Tutoring')
        self.assertEqual(response.data['class_type'], ClassType.INDIVIDUAL)
        self.assertTrue(ClassSchedule.objects.filter(title='Math Tutoring').exists())

    def test_create_group_class_success(self):
        """Test creating group class with participants via API."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'title': 'Group Math Class',
            'class_type': ClassType.GROUP,
            'scheduled_date': self.future_date.isoformat(),
            'start_time': '14:00:00',
            'end_time': '15:00:00',
            'duration_minutes': 60,
            'max_participants': 3,
            'participants': [self.student1.id, self.student2.id],
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['class_type'], ClassType.GROUP)
        self.assertEqual(response.data['participant_count'], 2)
        self.assertIn('Student One', response.data['participants_names'])

    def test_retrieve_class_schedule(self):
        """Test retrieving a specific class schedule."""
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student1,
            school=self.school,
            title='Test Class',
            scheduled_date=self.future_date,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.student1
        )
        
        self.client.force_authenticate(user=self.student1)
        url = reverse('class-schedules-detail', kwargs={'pk': class_schedule.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Class')

    def test_update_class_schedule(self):
        """Test updating a class schedule."""
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student1,
            school=self.school,
            title='Original Title',
            scheduled_date=self.future_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student1
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('class-schedules-detail', kwargs={'pk': class_schedule.id})
        update_data = {'title': 'Updated Title', 'description': 'Updated description'}
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')


class GroupClassAPITests(SchedulerAPITestCase):
    """Test group class specific functionality."""

    def test_group_class_capacity_validation(self):
        """Test group class capacity limits via API."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'title': 'Overcapacity Group Class',
            'class_type': ClassType.GROUP,
            'scheduled_date': self.future_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
            'max_participants': 2,
            'participants': [self.student1.id, self.student2.id],  # At capacity
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_full'])

    def test_group_class_exceeds_capacity_fails(self):
        """Test that exceeding group capacity fails."""
        student3 = CustomUser.objects.create_user(
            email="student3@test.com", name="Student Three", password="testpass123"
        )
        SchoolMembership.objects.create(
            user=student3, school=self.school, role=SchoolRole.STUDENT
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'title': 'Overcapacity Group Class',
            'class_type': ClassType.GROUP,
            'scheduled_date': self.future_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
            'max_participants': 2,
            'participants': [self.student1.id, self.student2.id, student3.id],  # Over capacity
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ClassStatusManagementAPITests(SchedulerAPITestCase):
    """Test status management endpoints."""

    def setUp(self):
        super().setUp()
        self.class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student1,
            school=self.school,
            title='Status Test Class',
            scheduled_date=self.future_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student1
        )

    def test_cancel_class_success(self):
        """Test cancelling a class via API."""
        self.client.force_authenticate(user=self.student1)
        
        url = reverse('class-schedules-cancel', kwargs={'pk': self.class_schedule.id})
        data = {'reason': 'Family emergency'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.class_schedule.refresh_from_db()
        self.assertEqual(self.class_schedule.status, ClassStatus.CANCELLED)

    def test_confirm_class_success(self):
        """Test confirming a class via API."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('class-schedules-confirm', kwargs={'pk': self.class_schedule.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.class_schedule.refresh_from_db()
        self.assertEqual(self.class_schedule.status, ClassStatus.CONFIRMED)

    def test_complete_class_success(self):
        """Test completing a class via API."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('class-schedules-complete', kwargs={'pk': self.class_schedule.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.class_schedule.refresh_from_db()
        self.assertEqual(self.class_schedule.status, ClassStatus.COMPLETED)


class SerializerValidationTests(SchedulerAPITestCase):
    """Test key serializer validation rules."""

    def test_individual_class_requires_student(self):
        """Test that individual classes require a student."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'title': 'Individual Class',
            'class_type': ClassType.INDIVIDUAL,
            'scheduled_date': self.future_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
            # No student provided
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_past_date_validation(self):
        """Test that past dates are rejected."""
        self.client.force_authenticate(user=self.student1)
        
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'student': self.student1.id,
            'school': self.school.id,
            'title': 'Past Class',
            'scheduled_date': self.past_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_group_class_min_participants_validation(self):
        """Test that group classes must allow at least 2 participants."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'title': 'Group Class',
            'class_type': ClassType.GROUP,
            'scheduled_date': self.future_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
            'max_participants': 1,  # Too low for group class
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationPermissionTests(SchedulerAPITestCase):
    """Test authentication and permission requirements."""

    def test_unauthenticated_create_fails(self):
        """Test that unauthenticated users cannot create classes."""
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'student': self.student1.id,
            'school': self.school.id,
            'title': 'Unauthorized Class',
            'scheduled_date': self.future_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_teacher_create_permission_denied(self):
        """Test that teachers cannot create classes."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'student': self.student1.id,
            'school': self.school.id,
            'title': 'Teacher Created Class',
            'scheduled_date': self.future_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_only_book_for_themselves(self):
        """Test that students can only book classes for themselves."""
        self.client.force_authenticate(user=self.student1)
        
        url = reverse('class-schedules-list')
        data = {
            'teacher': self.teacher_profile.id,
            'student': self.student2.id,  # Different student
            'school': self.school.id,
            'title': 'Cross Student Booking',
            'scheduled_date': self.future_date.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EnhancedSerializerFieldsTests(SchedulerAPITestCase):
    """Test new serializer fields from scheduling refactor."""

    def test_enhanced_read_only_fields(self):
        """Test that enhanced serializer fields work correctly."""
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student1,
            school=self.school,
            title='Enhanced Fields Test',
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            scheduled_date=self.future_date,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.teacher_user
        )

        self.client.force_authenticate(user=self.student1)
        url = reverse('class-schedules-detail', kwargs={'pk': class_schedule.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check enhanced read-only fields
        self.assertEqual(response.data['teacher_name'], 'Test Teacher')
        self.assertEqual(response.data['student_name'], 'Student One')
        self.assertEqual(response.data['school_name'], 'Test School')
        self.assertEqual(response.data['class_type_display'], 'Individual')
        self.assertEqual(response.data['status_display'], 'Scheduled')
        self.assertEqual(response.data['participant_count'], 1)
        self.assertFalse(response.data['is_full'])
        self.assertTrue(response.data['can_be_cancelled'])
        self.assertFalse(response.data['is_past'])

    def test_timezone_datetime_fields(self):
        """Test timezone-aware datetime fields."""
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student1,
            school=self.school,
            title='Timezone Test',
            scheduled_date=self.future_date,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.teacher_user
        )

        self.client.force_authenticate(user=self.student1)
        url = reverse('class-schedules-detail', kwargs={'pk': class_schedule.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['scheduled_datetime_utc'])
        self.assertIsNotNone(response.data['scheduled_datetime_local'])


class TeacherAvailabilityAPITests(SchedulerAPITestCase):
    """Comprehensive tests for Teacher Availability API endpoints."""

    def test_create_teacher_availability_success(self):
        """Test creating teacher availability via API as teacher."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-availability-list')
        data = {
            'school': self.school.id,
            'day_of_week': WeekDay.TUESDAY,
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'is_recurring': True,
            'effective_from': self.future_date.isoformat(),
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['day_of_week'], WeekDay.TUESDAY)
        self.assertEqual(response.data['teacher'], self.teacher_profile.id)
        self.assertTrue(response.data['is_recurring'])
        self.assertEqual(response.data['school'], self.school.id)

    def test_create_availability_admin_for_teacher(self):
        """Test admin creating availability for a teacher."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('teacher-availability-list')
        data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'day_of_week': WeekDay.TUESDAY,  # Changed from WEDNESDAY to avoid conflict with test setup
            'start_time': '10:00:00',
            'end_time': '16:00:00',
            'is_recurring': True,
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['teacher'], self.teacher_profile.id)
        self.assertEqual(response.data['day_of_week'], WeekDay.TUESDAY)  # Updated assertion

    def test_list_teacher_availability_filtered_by_teacher(self):
        """Test listing availability with teacher filtering."""
        # Create multiple teacher profiles for filtering test
        other_teacher_user = CustomUser.objects.create_user(
            email="other_teacher@test.com", name="Other Teacher", password="testpass123"
        )
        other_teacher_profile = TeacherProfile.objects.create(user=other_teacher_user, bio="Other bio")
        SchoolMembership.objects.create(
            user=other_teacher_user, school=self.school, role=SchoolRole.TEACHER
        )
        
        # Create availability for both teachers
        TeacherAvailability.objects.create(
            teacher=other_teacher_profile, school=self.school,
            day_of_week=WeekDay.THURSDAY, start_time=time(10, 0), end_time=time(16, 0)
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('teacher-availability-list')
        response = self.client.get(url, {'teacher_id': self.teacher_profile.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return availabilities for the filtered teacher
        for item in response.data['results']:
            self.assertEqual(item['teacher'], self.teacher_profile.id)

    def test_retrieve_teacher_availability(self):
        """Test retrieving a specific teacher availability."""
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            day_of_week=WeekDay.FRIDAY, start_time=time(9, 0), end_time=time(17, 0)
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-availability-detail', kwargs={'pk': availability.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], availability.id)
        self.assertEqual(response.data['day_of_week'], WeekDay.FRIDAY)
        self.assertEqual(response.data['teacher_name'], 'Test Teacher')
        self.assertEqual(response.data['school_name'], 'Test School')

    def test_update_teacher_availability(self):
        """Test updating teacher availability via PATCH."""
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            day_of_week=WeekDay.FRIDAY, start_time=time(9, 0), end_time=time(17, 0)
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-availability-detail', kwargs={'pk': availability.id})
        update_data = {
            'start_time': '08:00:00',
            'end_time': '18:00:00',
            'is_active': False
        }
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['start_time'], '08:00:00')
        self.assertEqual(response.data['end_time'], '18:00:00')
        self.assertFalse(response.data['is_active'])

    def test_full_update_teacher_availability(self):
        """Test updating teacher availability via PUT."""
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            day_of_week=WeekDay.FRIDAY, start_time=time(9, 0), end_time=time(17, 0)
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-availability-detail', kwargs={'pk': availability.id})
        update_data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'day_of_week': WeekDay.SATURDAY,
            'start_time': '10:00:00',
            'end_time': '16:00:00',
            'is_recurring': False,
            'is_active': True
        }
        
        response = self.client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['day_of_week'], WeekDay.SATURDAY)
        self.assertFalse(response.data['is_recurring'])

    def test_delete_teacher_availability(self):
        """Test deleting teacher availability."""
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            day_of_week=WeekDay.FRIDAY, start_time=time(9, 0), end_time=time(17, 0)
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-availability-detail', kwargs={'pk': availability.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TeacherAvailability.objects.filter(id=availability.id).exists())


class TeacherUnavailabilityAPITests(SchedulerAPITestCase):
    """Comprehensive tests for Teacher Unavailability API endpoints."""

    def test_create_all_day_unavailability_success(self):
        """Test creating all-day unavailability via API."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-unavailability-list')
        data = {
            'school': self.school.id,
            'date': self.future_date.isoformat(),
            'is_all_day': True,
            'reason': 'Public holiday',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_all_day'])
        self.assertEqual(response.data['reason'], 'Public holiday')
        self.assertEqual(response.data['teacher'], self.teacher_profile.id)
        self.assertIsNone(response.data['start_time'])
        self.assertIsNone(response.data['end_time'])

    def test_create_partial_day_unavailability_success(self):
        """Test creating partial day unavailability via API."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-unavailability-list')
        data = {
            'school': self.school.id,
            'date': self.future_date.isoformat(),
            'start_time': '14:00:00',
            'end_time': '16:00:00',
            'is_all_day': False,
            'reason': 'Doctor appointment',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_all_day'])
        self.assertEqual(response.data['start_time'], '14:00:00')
        self.assertEqual(response.data['end_time'], '16:00:00')
        self.assertEqual(response.data['reason'], 'Doctor appointment')

    def test_create_unavailability_admin_for_teacher(self):
        """Test admin creating unavailability for a teacher."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('teacher-unavailability-list')
        data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'date': self.future_date.isoformat(),
            'start_time': '12:00:00',
            'end_time': '13:00:00',
            'is_all_day': False,
            'reason': 'Lunch break',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['teacher'], self.teacher_profile.id)
        self.assertEqual(response.data['reason'], 'Lunch break')

    def test_list_teacher_unavailability_filtered(self):
        """Test listing unavailability with teacher filtering."""
        # Create unavailability record
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            date=self.future_date, is_all_day=True, reason='Sick day'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('teacher-unavailability-list')
        response = self.client.get(url, {'teacher_id': self.teacher_profile.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)
        for item in response.data['results']:
            self.assertEqual(item['teacher'], self.teacher_profile.id)

    def test_retrieve_teacher_unavailability(self):
        """Test retrieving a specific teacher unavailability."""
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            date=self.future_date, start_time=time(10, 0), end_time=time(12, 0),
            is_all_day=False, reason='Meeting'
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-unavailability-detail', kwargs={'pk': unavailability.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], unavailability.id)
        self.assertEqual(response.data['reason'], 'Meeting')
        self.assertEqual(response.data['teacher_name'], 'Test Teacher')
        self.assertEqual(response.data['school_name'], 'Test School')

    def test_update_teacher_unavailability(self):
        """Test updating teacher unavailability via PATCH."""
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            date=self.future_date, start_time=time(10, 0), end_time=time(12, 0),
            is_all_day=False, reason='Meeting'
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-unavailability-detail', kwargs={'pk': unavailability.id})
        update_data = {
            'reason': 'Updated meeting',
            'start_time': '09:00:00',
            'end_time': '11:00:00'
        }
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reason'], 'Updated meeting')
        self.assertEqual(response.data['start_time'], '09:00:00')
        self.assertEqual(response.data['end_time'], '11:00:00')

    def test_full_update_teacher_unavailability(self):
        """Test updating teacher unavailability via PUT."""
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            date=self.future_date, is_all_day=False,
            start_time=time(10, 0), end_time=time(12, 0), reason='Meeting'
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-unavailability-detail', kwargs={'pk': unavailability.id})
        update_data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'date': self.future_date.isoformat(),
            'is_all_day': True,
            'reason': 'Full day off'
        }
        
        response = self.client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_all_day'])
        self.assertEqual(response.data['reason'], 'Full day off')
        self.assertIsNone(response.data['start_time'])
        self.assertIsNone(response.data['end_time'])

    def test_delete_teacher_unavailability(self):
        """Test deleting teacher unavailability."""
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            date=self.future_date, is_all_day=True, reason='Holiday'
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-unavailability-detail', kwargs={'pk': unavailability.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TeacherUnavailability.objects.filter(id=unavailability.id).exists())


class AvailabilityValidationTests(SchedulerAPITestCase):
    """Test validation rules for Teacher Availability and Unavailability APIs."""

    def test_availability_start_time_before_end_time(self):
        """Test that start_time must be before end_time for availability."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-availability-list')
        data = {
            'school': self.school.id,
            'day_of_week': WeekDay.MONDAY,
            'start_time': '17:00:00',  # After end_time
            'end_time': '09:00:00',
            'is_recurring': True,
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_time', str(response.data).lower() or str(response.content).lower())

    def test_availability_overlapping_slots_validation(self):
        """Test that overlapping availability slots are rejected."""
        # Create existing availability
        TeacherAvailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            day_of_week=WeekDay.MONDAY, start_time=time(9, 0), end_time=time(17, 0)
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-availability-list')
        data = {
            'school': self.school.id,
            'day_of_week': WeekDay.MONDAY,  # Same day
            'start_time': '15:00:00',  # Overlaps with existing 9-17
            'end_time': '19:00:00',
            'is_recurring': True,
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('overlap', str(response.data).lower() or str(response.content).lower())

    def test_availability_effective_date_validation(self):
        """Test that effective_until must be after effective_from."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-availability-list')
        data = {
            'school': self.school.id,
            'day_of_week': WeekDay.TUESDAY,
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'effective_from': self.future_date.isoformat(),
            'effective_until': (self.future_date - timedelta(days=1)).isoformat(),  # Before effective_from
            'is_recurring': True,
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('effective_until', str(response.data).lower() or str(response.content).lower())

    def test_unavailability_start_time_before_end_time(self):
        """Test that start_time must be before end_time for partial unavailability."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-unavailability-list')
        data = {
            'school': self.school.id,
            'date': self.future_date.isoformat(),
            'start_time': '16:00:00',  # After end_time
            'end_time': '14:00:00',
            'is_all_day': False,
            'reason': 'Invalid time range',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_time', str(response.data).lower() or str(response.content).lower())

    def test_unavailability_partial_day_requires_times(self):
        """Test that partial day unavailability requires start_time and end_time."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-unavailability-list')
        data = {
            'school': self.school.id,
            'date': self.future_date.isoformat(),
            'is_all_day': False,
            'reason': 'Missing times',
            # Missing start_time and end_time
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_time', str(response.data).lower() or str(response.content).lower())

    def test_unavailability_overlapping_slots_validation(self):
        """Test that overlapping unavailability slots are rejected."""
        # Create existing unavailability
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            date=self.future_date, start_time=time(14, 0), end_time=time(16, 0),
            is_all_day=False, reason='Existing appointment'
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-unavailability-list')
        data = {
            'school': self.school.id,
            'date': self.future_date.isoformat(),
            'start_time': '15:00:00',  # Overlaps with existing 14-16
            'end_time': '17:00:00',
            'is_all_day': False,
            'reason': 'Overlapping appointment',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('overlap', str(response.data).lower() or str(response.content).lower())

    def test_unavailability_all_day_conflicts_with_partial(self):
        """Test that all-day unavailability conflicts with existing partial unavailability."""
        # Create existing partial unavailability
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            date=self.future_date, start_time=time(14, 0), end_time=time(16, 0),
            is_all_day=False, reason='Partial appointment'
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('teacher-unavailability-list')
        data = {
            'school': self.school.id,
            'date': self.future_date.isoformat(),
            'is_all_day': True,
            'reason': 'All day off',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unavailability already exists', str(response.data).lower() or str(response.content).lower())


class AvailableSlotsAPITests(SchedulerAPITestCase):
    """
    Comprehensive tests for the enhanced available_slots endpoint.
    Tests implementation of GitHub issue #148 requirements.
    
    These tests are designed to FAIL initially until the new implementation is complete.
    """
    
    def setUp(self):
        super().setUp()
        self.available_slots_url = '/api/scheduler/schedules/available_slots/'
        
        # Create multiple time slots for testing
        self.test_date = timezone.now().date() + timedelta(days=1)
        self.test_date_str = self.test_date.isoformat()
        
        # Create comprehensive availability schedule
        TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=self.test_date.strftime("%A").lower(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Create a scheduled class to test availability filtering
        ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student1,
            school=self.school,
            title='Existing Class',
            scheduled_date=self.test_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )

    def test_available_slots_requires_teacher_id_parameter(self):
        """Test that teacher_id parameter is required."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'date': self.test_date_str,
            # Missing teacher_id
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('teacher_id', str(response.data).lower())

    def test_available_slots_requires_date_parameter(self):
        """Test that date parameter is required."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            # Missing date
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', str(response.data).lower())

    def test_available_slots_validates_date_format(self):
        """Test that date parameter must be in ISO format YYYY-MM-DD."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test invalid date formats
        invalid_dates = ['2025-13-01', '2025/08/06', '08-06-2025', 'invalid-date']
        
        for invalid_date in invalid_dates:
            data = {
                'teacher_id': self.teacher_profile.id,
                'date': invalid_date,
            }
            
            response = self.client.get(self.available_slots_url, data)
            
            self.assertEqual(
                response.status_code, 
                status.HTTP_400_BAD_REQUEST,
                f"Expected 400 for invalid date format: {invalid_date}"
            )

    def test_available_slots_new_response_format(self):
        """Test that response uses new JSON format with ISO datetime strings."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        # This test will FAIL until new implementation is complete
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # New format should have only 'available_slots' at root level
        self.assertIn('available_slots', response.data)
        self.assertIsInstance(response.data['available_slots'], list)
        
        # Old format fields should NOT be present
        self.assertNotIn('teacher_id', response.data)
        self.assertNotIn('date', response.data)
        
        # Each slot should have ISO datetime format
        if response.data['available_slots']:
            slot = response.data['available_slots'][0]
            self.assertIn('start', slot)
            self.assertIn('end', slot)
            
            # Should NOT have old format fields
            self.assertNotIn('start_time', slot)
            self.assertNotIn('end_time', slot)
            self.assertNotIn('school_id', slot)
            self.assertNotIn('school_name', slot)
            
            # Verify ISO datetime format (should end with 'Z' for UTC)
            self.assertTrue(slot['start'].endswith('Z'))
            self.assertTrue(slot['end'].endswith('Z'))

    def test_available_slots_default_duration_60_minutes(self):
        """Test that default duration is 60 minutes when not specified."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
            # No duration_minutes specified - should default to 60
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        # This test will FAIL until new implementation is complete
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return slots with 60-minute duration (excluding the existing 10-11 class)
        available_slots = response.data['available_slots']
        
        if available_slots:
            # Calculate duration from first slot
            slot = available_slots[0]
            start_time = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
            duration = (end_time - start_time).total_seconds() / 60
            
            self.assertEqual(duration, 60.0)

    def test_available_slots_custom_duration_parameter(self):
        """Test that duration_minutes parameter works with custom values."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test different duration values
        test_durations = [30, 45, 90, 120]
        
        for duration in test_durations:
            data = {
                'teacher_id': self.teacher_profile.id,
                'date': self.test_date_str,
                'duration_minutes': duration,
            }
            
            response = self.client.get(self.available_slots_url, data)
            
            # This test will FAIL until new implementation is complete
            self.assertEqual(
                response.status_code, 
                status.HTTP_200_OK,
                f"Failed for duration {duration} minutes"
            )
            
            # Verify slots have correct duration
            available_slots = response.data['available_slots']
            
            if available_slots:
                slot = available_slots[0]
                start_time = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
                actual_duration = (end_time - start_time).total_seconds() / 60
                
                self.assertEqual(
                    actual_duration, 
                    float(duration),
                    f"Expected {duration} minutes, got {actual_duration}"
                )

    def test_available_slots_date_range_query(self):
        """Test date range queries using date_end parameter."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create availability for multiple days
        tomorrow = self.test_date + timedelta(days=1)
        day_after = self.test_date + timedelta(days=2)
        
        for test_date in [tomorrow, day_after]:
            TeacherAvailability.objects.create(
                teacher=self.teacher_profile,
                school=self.school,
                day_of_week=test_date.strftime("%A").lower(),
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True
            )
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
            'date_end': day_after.isoformat(),
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        # This test will FAIL until new implementation is complete
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return slots across the date range
        available_slots = response.data['available_slots']
        self.assertGreater(len(available_slots), 0)
        
        # Verify dates are within the specified range
        for slot in available_slots:
            slot_date = datetime.fromisoformat(slot['start'].replace('Z', '+00:00')).date()
            self.assertTrue(self.test_date <= slot_date <= day_after)

    def test_available_slots_performance_requirement(self):
        """Test that response time is under 300ms."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create extensive availability data to test performance
        for i in range(5):  # Multiple days
            test_date = self.test_date + timedelta(days=i)
            TeacherAvailability.objects.create(
                teacher=self.teacher_profile,
                school=self.school,
                day_of_week=test_date.strftime("%A").lower(),
                start_time=time(8, 0),
                end_time=time(18, 0),
                is_active=True
            )
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
            'date_end': (self.test_date + timedelta(days=4)).isoformat(),
        }
        
        # Measure response time
        start_time = timezone.now()
        response = self.client.get(self.available_slots_url, data)
        end_time = timezone.now()
        
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # This test will FAIL until performance optimization is complete
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(
            response_time_ms, 
            300, 
            f"Response time {response_time_ms}ms exceeds 300ms requirement"
        )

    def test_available_slots_filters_existing_classes(self):
        """Test that existing scheduled classes are properly filtered out."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        # This test will FAIL until new implementation is complete
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        available_slots = response.data['available_slots']
        
        # Verify that the existing class slot (10:00-11:00) is not available
        for slot in available_slots:
            start_time = datetime.fromisoformat(slot['start'].replace('Z', '+00:00')).time()
            end_time = datetime.fromisoformat(slot['end'].replace('Z', '+00:00')).time()
            
            # Should not overlap with existing class (10:00-11:00)
            self.assertFalse(
                (start_time < time(11, 0) and end_time > time(10, 0)),
                f"Slot {start_time}-{end_time} overlaps with existing class"
            )

    def test_available_slots_respects_teacher_unavailability(self):
        """Test that teacher unavailability periods are respected."""
        # Create unavailability for part of the day
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.test_date,
            start_time=time(14, 0),
            end_time=time(16, 0),
            is_all_day=False,
            reason='Doctor appointment'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        # This test will FAIL until new implementation is complete  
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        available_slots = response.data['available_slots']
        
        # Verify that unavailable period (14:00-16:00) is not included
        import pytz
        school_timezone = pytz.timezone(self.school_settings.timezone)
        
        for slot in available_slots:
            # Convert UTC slot times back to school timezone for comparison
            start_utc = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
            end_utc = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
            start_local = start_utc.astimezone(school_timezone).time()
            end_local = end_utc.astimezone(school_timezone).time()
            
            # Should not overlap with unavailable period (14:00-16:00 local time)
            self.assertFalse(
                (start_local < time(16, 0) and end_local > time(14, 0)),
                f"Slot {start_local}-{end_local} overlaps with unavailable period"
            )

    def test_available_slots_handles_all_day_unavailability(self):
        """Test that all-day unavailability returns empty slots."""
        # Create all-day unavailability
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.test_date,
            is_all_day=True,
            reason='Public holiday'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        # This test will FAIL until new implementation is complete
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['available_slots']), 0)

    def test_available_slots_invalid_teacher_id(self):
        """Test error handling for invalid teacher_id."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': 99999,  # Non-existent teacher ID
            'date': self.test_date_str,
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('teacher', str(response.data).lower())

    def test_available_slots_negative_duration(self):
        """Test that negative duration values are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
            'duration_minutes': -30,
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', str(response.data).lower())

    def test_available_slots_zero_duration(self):
        """Test that zero duration values are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
            'duration_minutes': 0,
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', str(response.data).lower())

    def test_available_slots_date_end_before_date_start(self):
        """Test that date_end before date is rejected."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
            'date_end': (self.test_date - timedelta(days=1)).isoformat(),  # Before start date
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_end', str(response.data).lower())

    def test_available_slots_authentication_required(self):
        """Test that authentication is required."""
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.test_date_str,
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_available_slots_school_permission_filtering(self):
        """Test that only slots from user's schools are returned."""
        # Create another school and teacher that current user shouldn't see
        other_school = School.objects.create(name="Other School", description="Other School")
        other_teacher_user = CustomUser.objects.create_user(
            email="other@test.com", name="Other Teacher", password="testpass123"
        )
        other_teacher_profile = TeacherProfile.objects.create(user=other_teacher_user, bio="Other bio")
        
        # Admin user is not a member of other_school, so shouldn't see its data
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': other_teacher_profile.id,
            'date': self.test_date_str,
        }
        
        response = self.client.get(self.available_slots_url, data)
        
        # Should fail due to school permission restrictions
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST])


class RobustClassBookingAPITests(SchedulerAPITestCase):
    """
    Tests for NEW class booking endpoint improvements (GitHub Issue #149).
    
    These tests are designed to FAIL initially since the functionality doesn't exist yet.
    This follows TDD red-green-refactor approach.
    
    NEW functionality being tested:
    1. Booking with minimal parameters (teacher_id, date, start_time, duration_minutes)  
    2. Automatic booked_by setting to requesting user
    3. Student conflict validation (can't book overlapping classes)
    4. Minimum notice period validation (24 hours default)
    5. Group class creation with max_participants
    6. Joining existing group classes when capacity available
    7. Group class at capacity prevention
    8. New endpoint alias /api/scheduling/classes/
    """
    
    def setUp(self):
        super().setUp()
        
        # URLs for testing - new alias endpoint that should be added
        self.classes_url = '/api/scheduling/classes/'  # NEW endpoint alias
        self.schedules_url = reverse('class-schedules-list')  # Existing endpoint
        
        # Future dates for testing minimum notice period
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        self.next_week = timezone.now().date() + timedelta(days=7)
        
    def test_booking_with_minimal_parameters_success(self):
        """Test NEW requirement: booking with minimal required parameters."""
        self.client.force_authenticate(user=self.student1)
        
        # Only required parameters: teacher_id, date, start_time, duration_minutes
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.next_week.isoformat(),
            'start_time': '10:00:00',
            'duration_minutes': 60,
        }
        
        # This test will FAIL until new implementation is complete
        response = self.client.post(self.classes_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify required fields are set automatically
        self.assertEqual(response.data['teacher'], self.teacher_profile.id)
        self.assertEqual(response.data['student'], self.student1.id)  # Auto-set for student bookings
        self.assertEqual(response.data['duration_minutes'], 60)
        self.assertEqual(response.data['status'], ClassStatus.SCHEDULED)
        
        # Verify class was created in database
        self.assertTrue(ClassSchedule.objects.filter(
            teacher=self.teacher_profile,
            student=self.student1,
            scheduled_date=self.next_week,
            start_time=time(10, 0)
        ).exists())

    def test_booked_by_automatically_set_to_requesting_user(self):
        """Test NEW requirement: booked_by is automatically set to requesting user."""
        self.client.force_authenticate(user=self.student1)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.next_week.isoformat(),
            'start_time': '14:00:00',
            'duration_minutes': 60,
        }
        
        # This test will FAIL until new implementation is complete
        response = self.client.post(self.classes_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['booked_by'], self.student1.id)
        self.assertIsNotNone(response.data['booked_at'])
        
        # Verify in database
        booking = ClassSchedule.objects.get(id=response.data['id'])
        self.assertEqual(booking.booked_by, self.student1)

    def test_student_conflict_validation_prevents_double_booking(self):
        """Test NEW requirement: student cannot book two classes at same time."""
        # Create existing booking for student1
        existing_booking = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student1,
            school=self.school,
            title='Existing Class',
            scheduled_date=self.next_week,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student1
        )
        
        self.client.force_authenticate(user=self.student1)
        
        # Try to book overlapping class
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.next_week.isoformat(),
            'start_time': '10:30:00',  # Overlaps with existing 10:00-11:00
            'duration_minutes': 60,
        }
        
        # This test will FAIL until student conflict validation is implemented
        response = self.client.post(self.classes_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('conflict', str(response.data).lower())
        self.assertIn('student', str(response.data).lower())

    def test_minimum_notice_period_validation_24_hours_default(self):
        """Test NEW requirement: minimum notice period validation (24 hours default)."""
        self.client.force_authenticate(user=self.student1)
        
        # Try to book class with less than 24 hours notice
        tomorrow_same_time = timezone.now() + timedelta(hours=12)  # Only 12 hours notice
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': tomorrow_same_time.date().isoformat(),
            'start_time': tomorrow_same_time.strftime('%H:%M:%S'),
            'duration_minutes': 60,
        }
        
        # This test will FAIL until minimum notice period validation is implemented
        response = self.client.post(self.classes_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('notice', str(response.data).lower())
        self.assertIn('24', str(response.data))

    def test_group_class_creation_with_max_participants(self):
        """Test NEW requirement: group class creation with max_participants."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.next_week.isoformat(),
            'start_time': '15:00:00',
            'duration_minutes': 90,
            'max_participants': 4,
            'class_type': ClassType.GROUP,
            'description': 'Group Math Class'
        }
        
        # This test will FAIL until max_participants functionality is implemented
        response = self.client.post(self.classes_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['class_type'], ClassType.GROUP)
        self.assertEqual(response.data['max_participants'], 4)
        
        # Verify in database
        booking = ClassSchedule.objects.get(id=response.data['id'])
        self.assertEqual(booking.max_participants, 4)

    def test_joining_existing_group_class_when_capacity_available(self):
        """Test NEW requirement: join existing group class when capacity available."""
        # Create existing group class with capacity
        existing_group = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student1,
            school=self.school,
            title='Math Study Group',
            class_type=ClassType.GROUP,
            scheduled_date=self.next_week,
            start_time=time(16, 0),
            end_time=time(17, 30),
            duration_minutes=90,
            max_participants=3,
            booked_by=self.student1
        )
        
        self.client.force_authenticate(user=self.student2)
        
        # Student2 tries to book same time slot - should join existing group
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.next_week.isoformat(),
            'start_time': '16:00:00',
            'duration_minutes': 90,
        }
        
        # This test will FAIL until group joining logic is implemented
        response = self.client.post(self.classes_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should return the existing group class with updated participants
        self.assertEqual(response.data['id'], existing_group.id)
        self.assertEqual(response.data['class_type'], ClassType.GROUP)
        self.assertIn(self.student2.id, response.data['participants'])
        self.assertEqual(response.data['participant_count'], 2)

    def test_group_class_at_capacity_prevents_joining(self):
        """Test NEW requirement: cannot join group class when at capacity."""
        # Create student3 for this test
        student3 = CustomUser.objects.create_user(
            email="student3@test.com", name="Student Three", password="testpass123"
        )
        SchoolMembership.objects.create(
            user=student3, school=self.school, role=SchoolRole.STUDENT
        )
        
        # Create group class at capacity
        existing_group = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student1,
            school=self.school,
            title='Full Study Group',
            class_type=ClassType.GROUP,
            scheduled_date=self.next_week,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            max_participants=2,  # At capacity with student1 and student2
            booked_by=self.student1
        )
        existing_group.additional_students.add(self.student2)  # Now at capacity (2/2)
        
        self.client.force_authenticate(user=student3)
        
        # Student3 tries to join full group
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.next_week.isoformat(),
            'start_time': '14:00:00',
            'duration_minutes': 60,
        }
        
        # This test will FAIL until capacity checking is implemented
        response = self.client.post(self.classes_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('capacity', str(response.data).lower())
        self.assertIn('full', str(response.data).lower())

    def test_new_endpoint_alias_classes_works(self):
        """Test NEW requirement: /api/scheduling/classes/ endpoint alias works."""
        self.client.force_authenticate(user=self.student1)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.next_week.isoformat(),
            'start_time': '11:00:00',
            'duration_minutes': 45,
        }
        
        # This test will FAIL until new endpoint alias is implemented
        response = self.client.post(self.classes_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should work identically to existing schedules endpoint
        self.assertIn('id', response.data)
        self.assertEqual(response.data['teacher'], self.teacher_profile.id)
        self.assertEqual(response.data['duration_minutes'], 45)

    def test_booking_preserves_existing_validation_rules(self):
        """Test that new booking endpoint preserves existing validation (past dates, teacher availability)."""
        self.client.force_authenticate(user=self.student1)
        
        # Test 1: Past date validation should still work
        past_date = timezone.now().date() - timedelta(days=1)
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': past_date.isoformat(),
            'start_time': '10:00:00',
            'duration_minutes': 60,
        }
        
        response = self.client.post(self.classes_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 2: Teacher unavailability should still work
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.next_week,
            start_time=time(15, 0),
            end_time=time(17, 0),
            is_all_day=False,
            reason='Unavailable period'
        )
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.next_week.isoformat(),
            'start_time': '16:00:00',  # During unavailable period
            'duration_minutes': 60,
        }
        
        response = self.client.post(self.classes_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_optional_parameters_work_with_minimal_booking(self):
        """Test that optional parameters (description, class_type) work with minimal booking."""
        self.client.force_authenticate(user=self.student1)
        
        data = {
            'teacher_id': self.teacher_profile.id,
            'date': self.next_week.isoformat(),
            'start_time': '13:00:00',
            'duration_minutes': 30,
            'description': 'Quick review session',
            'class_type': ClassType.TRIAL,
        }
        
        # This test will FAIL until new implementation supports optional params
        response = self.client.post(self.classes_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Quick review session')
        self.assertEqual(response.data['class_type'], ClassType.TRIAL)
        self.assertEqual(response.data['duration_minutes'], 30)


class AvailabilityPermissionTests(SchedulerAPITestCase):
    """Test permission controls and school context filtering for Availability APIs."""

    def setUp(self):
        super().setUp()
        # Create another school and teacher for permission testing
        self.other_school = School.objects.create(name="Other School", description="Other Description")
        self.other_teacher_user = CustomUser.objects.create_user(
            email="other_teacher@test.com", name="Other Teacher", password="testpass123"
        )
        self.other_teacher_profile = TeacherProfile.objects.create(
            user=self.other_teacher_user, bio="Other teacher bio"
        )
        
        # Create memberships for other school
        SchoolMembership.objects.create(
            user=self.other_teacher_user, school=self.other_school, role=SchoolRole.TEACHER
        )

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access availability APIs."""
        # Test availability list
        url = reverse('teacher-availability-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test unavailability list
        url = reverse('teacher-unavailability-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_teacher_can_only_modify_own_availability(self):
        """Test that teachers can only modify their own availability."""
        # Create availability for other teacher
        other_availability = TeacherAvailability.objects.create(
            teacher=self.other_teacher_profile, school=self.other_school,
            day_of_week=WeekDay.MONDAY, start_time=time(9, 0), end_time=time(17, 0)
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        
        # Try to update other teacher's availability
        url = reverse('teacher-availability-detail', kwargs={'pk': other_availability.id})
        response = self.client.get(url)
        
        # Should not be able to see availability from other school
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_teacher_can_only_modify_own_unavailability(self):
        """Test that teachers can only modify their own unavailability."""
        # Create unavailability for other teacher
        other_unavailability = TeacherUnavailability.objects.create(
            teacher=self.other_teacher_profile, school=self.other_school,
            date=self.future_date, is_all_day=True, reason='Other teacher holiday'
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        
        # Try to access other teacher's unavailability
        url = reverse('teacher-unavailability-detail', kwargs={'pk': other_unavailability.id})
        response = self.client.get(url)
        
        # Should not be able to see unavailability from other school
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_manage_any_teacher_in_school(self):
        """Test that school admins can manage availability for any teacher in their school."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create availability for teacher via admin
        url = reverse('teacher-availability-list')
        data = {
            'teacher': self.teacher_profile.id,
            'school': self.school.id,
            'day_of_week': WeekDay.WEDNESDAY,
            'start_time': '10:00:00',
            'end_time': '16:00:00',
            'is_recurring': True,
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['teacher'], self.teacher_profile.id)

    def test_admin_cannot_manage_teachers_from_other_schools(self):
        """Test that admins cannot manage teachers from other schools."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Try to create availability for teacher in other school
        url = reverse('teacher-availability-list')
        data = {
            'teacher': self.other_teacher_profile.id,
            'school': self.other_school.id,  # Admin is not member of this school
            'day_of_week': WeekDay.WEDNESDAY,
            'start_time': '10:00:00',
            'end_time': '16:00:00',
            'is_recurring': True,
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should fail due to school permission restrictions
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_context_filtering_availability(self):
        """Test that users only see availability for schools they belong to."""
        # Create availability in both schools
        TeacherAvailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            day_of_week=WeekDay.MONDAY, start_time=time(9, 0), end_time=time(17, 0)
        )
        TeacherAvailability.objects.create(
            teacher=self.other_teacher_profile, school=self.other_school,
            day_of_week=WeekDay.TUESDAY, start_time=time(9, 0), end_time=time(17, 0)
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('teacher-availability-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see availability from admin's school
        school_ids = {item['school'] for item in response.data}
        self.assertEqual(school_ids, {self.school.id})
        self.assertNotIn(self.other_school.id, school_ids)

    def test_school_context_filtering_unavailability(self):
        """Test that users only see unavailability for schools they belong to."""
        # Create unavailability in both schools
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile, school=self.school,
            date=self.future_date, is_all_day=True, reason='School holiday'
        )
        TeacherUnavailability.objects.create(
            teacher=self.other_teacher_profile, school=self.other_school,
            date=self.future_date, is_all_day=True, reason='Other school holiday'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('teacher-unavailability-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see unavailability from admin's school
        school_ids = {item['school'] for item in response.data}
        self.assertEqual(school_ids, {self.school.id})
        self.assertNotIn(self.other_school.id, school_ids)

    def test_student_cannot_access_availability_apis(self):
        """Test that students cannot access teacher availability APIs."""
        self.client.force_authenticate(user=self.student1)
        
        # Try to access availability list
        url = reverse('teacher-availability-list')
        response = self.client.get(url)
        
        # Students should not have access to teacher availability management
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try to access unavailability list
        url = reverse('teacher-unavailability-list')
        response = self.client.get(url)
        
        # Students should not have access to teacher unavailability management
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)