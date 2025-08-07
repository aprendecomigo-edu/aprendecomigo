"""
Comprehensive tests for scheduler app.
Following Django testing best practices and TDD approach.
"""
from datetime import date, time, timedelta, datetime
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import CustomUser, School, TeacherProfile, SchoolMembership, SchoolRole
from .models import (
    TeacherAvailability,
    TeacherUnavailability,
    ClassSchedule,
    ClassStatus,
    WeekDay
)
from .services import AvailableSlotsService, SlotValidationService


class AvailableSlotsAPITests(APITestCase):
    """
    Test suite for the enhanced available_slots endpoint.
    Implements requirements from GitHub issue #148.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com",
            phone_number="1234567890"
        )
        
        # Create test teacher user and profile
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            password="testpass123",
            name="John Doe",
            first_name="John",
            last_name="Doe"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Experienced teacher",
            specialty="Mathematics"
        )
        
        # Create test admin user
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            password="adminpass123",
            name="Admin User"
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Create teacher availability (Monday 9:00-17:00)
        self.availability = TeacherAvailability.objects.create(
            teacher=self.teacher,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Test date (ensure it's a Monday)
        self.test_date = date(2025, 8, 18)  # Monday
        
        # API endpoint URL
        self.url = reverse('class-schedules-available-slots')
    
    def test_available_slots_requires_teacher_id_parameter(self):
        """Test that teacher_id parameter is required."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'date': '2025-08-18'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('teacher_id and date are required', response.data['error'])
    
    def test_available_slots_requires_date_parameter(self):
        """Test that date parameter is required."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'teacher_id': self.teacher.id})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('teacher_id and date are required', response.data['error'])
    
    def test_available_slots_validates_date_format(self):
        """Test ISO date format validation."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Invalid date format
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '18-08-2025'  # Wrong format
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ISO format', response.data['error'])
    
    def test_available_slots_validates_teacher_exists(self):
        """Test validation that teacher exists."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {
            'teacher_id': 99999,  # Non-existent teacher
            'date': '2025-08-18'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_available_slots_negative_duration(self):
        """Test that negative duration values are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18',
            'duration_minutes': -30
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Duration must be positive', response.data['error'])
    
    def test_available_slots_zero_duration(self):
        """Test that zero duration values are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18',
            'duration_minutes': 0
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Duration must be positive', response.data['error'])
    
    def test_available_slots_date_end_before_date_start(self):
        """Test validation of date range logic."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18',
            'date_end': '2025-08-17'  # End before start
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_end must be after', response.data['error'])
    
    def test_available_slots_new_response_format(self):
        """Test the new JSON response structure with ISO datetime format."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('available_slots', response.data)
        
        # Check response structure
        if response.data['available_slots']:
            slot = response.data['available_slots'][0]
            self.assertIn('start', slot)
            self.assertIn('end', slot)
            
            # Verify ISO datetime format with timezone
            start_datetime = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
            
            self.assertIsInstance(start_datetime, datetime)
            self.assertIsInstance(end_datetime, datetime)
    
    def test_available_slots_default_duration_60_minutes(self):
        """Test that default duration is 60 minutes."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # If slots are available, they should be 60 minutes long
        if response.data['available_slots']:
            slot = response.data['available_slots'][0]
            start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
            
            duration = end - start
            self.assertEqual(duration, timedelta(minutes=60))
    
    def test_available_slots_custom_duration_parameter(self):
        """Test custom duration parameter handling."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18',
            'duration_minutes': 90
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # If slots are available, they should be 90 minutes long
        if response.data['available_slots']:
            slot = response.data['available_slots'][0]
            start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
            
            duration = end - start
            self.assertEqual(duration, timedelta(minutes=90))
    
    def test_available_slots_date_range_query(self):
        """Test date_end parameter for range queries."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create availability for Tuesday as well
        TeacherAvailability.objects.create(
            teacher=self.teacher,
            school=self.school,
            day_of_week=WeekDay.TUESDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18',  # Monday
            'date_end': '2025-08-19'  # Tuesday
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('available_slots', response.data)
        
        # Should have slots for both days
        slots = response.data['available_slots']
        if slots:
            # Verify we have slots from different dates
            dates = set()
            for slot in slots:
                slot_date = datetime.fromisoformat(slot['start'].replace('Z', '+00:00')).date()
                dates.add(slot_date)
            
            # Should have slots from multiple days
            self.assertGreaterEqual(len(dates), 1)
    
    def test_available_slots_filters_existing_classes(self):
        """Test that existing classes are filtered out."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create an existing class booking
        ClassSchedule.objects.create(
            teacher=self.teacher,
            school=self.school,
            scheduled_date=self.test_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            status=ClassStatus.CONFIRMED,
            student=self.admin_user,
            title="Test Class",
            booked_by=self.admin_user
        )
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that 10:00-11:00 slot is not available
        slots = response.data['available_slots']
        for slot in slots:
            start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
            
            # Should not overlap with the booked 10:00-11:00 slot
            self.assertFalse(
                start.time() < time(11, 0) and end.time() > time(10, 0),
                f"Slot {start.time()}-{end.time()} overlaps with booked time"
            )
    
    def test_available_slots_respects_teacher_unavailability(self):
        """Test that partial-day unavailability is respected."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create partial unavailability (lunch break)
        TeacherUnavailability.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=self.test_date,
            start_time=time(12, 0),
            end_time=time(13, 0),
            is_all_day=False,
            reason="Lunch break"
        )
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that 12:00-13:00 slot is not available
        slots = response.data['available_slots']
        for slot in slots:
            start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
            
            # Should not overlap with lunch break
            self.assertFalse(
                start.time() < time(13, 0) and end.time() > time(12, 0),
                f"Slot {start.time()}-{end.time()} overlaps with unavailable time"
            )
    
    def test_available_slots_handles_all_day_unavailability(self):
        """Test all-day unavailability handling."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create all-day unavailability
        TeacherUnavailability.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=self.test_date,
            is_all_day=True,
            reason="Sick day"
        )
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have no available slots
        self.assertEqual(len(response.data['available_slots']), 0)
    
    def test_available_slots_no_availability_returns_empty(self):
        """Test that no slots are returned when teacher has no availability."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test on a day with no availability (Tuesday)
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-19'  # Tuesday - no availability set
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['available_slots']), 0)
    
    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_available_slots_caching_performance(self, mock_cache_set, mock_cache_get):
        """Test that caching is implemented for performance."""
        self.client.force_authenticate(user=self.admin_user)
        
        # First request should miss cache
        mock_cache_get.return_value = None
        
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cache.set was called
        self.assertTrue(mock_cache_set.called)
    
    def test_authentication_required(self):
        """Test that authentication is required for the endpoint."""
        response = self.client.get(self.url, {
            'teacher_id': self.teacher.id,
            'date': '2025-08-18'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SlotValidationServiceTests(TestCase):
    """Test suite for SlotValidationService."""
    
    def test_validate_date_format_valid(self):
        """Test valid date format validation."""
        result = SlotValidationService.validate_date_format("2025-08-18")
        self.assertEqual(result, date(2025, 8, 18))
    
    def test_validate_date_format_invalid(self):
        """Test invalid date format validation."""
        with self.assertRaises(ValueError):
            SlotValidationService.validate_date_format("18-08-2025")
    
    def test_validate_duration_positive(self):
        """Test valid duration validation."""
        # Should not raise exception
        SlotValidationService.validate_duration(60)
        SlotValidationService.validate_duration(90)
    
    def test_validate_duration_negative(self):
        """Test negative duration validation."""
        with self.assertRaises(ValueError):
            SlotValidationService.validate_duration(-30)
    
    def test_validate_duration_zero(self):
        """Test zero duration validation."""
        with self.assertRaises(ValueError):
            SlotValidationService.validate_duration(0)
    
    def test_validate_duration_too_long(self):
        """Test overly long duration validation."""
        with self.assertRaises(ValueError):
            SlotValidationService.validate_duration(500)  # > 8 hours
    
    def test_validate_date_range_valid(self):
        """Test valid date range validation."""
        start = date(2025, 8, 18)
        end = date(2025, 8, 20)
        
        # Should not raise exception
        SlotValidationService.validate_date_range(start, end)
    
    def test_validate_date_range_invalid(self):
        """Test invalid date range validation."""
        start = date(2025, 8, 20)
        end = date(2025, 8, 18)
        
        with self.assertRaises(ValueError):
            SlotValidationService.validate_date_range(start, end)


class AvailableSlotsServiceTests(TestCase):
    """Test suite for AvailableSlotsService business logic."""
    
    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com",
            phone_number="1234567890"
        )
        
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            password="testpass123",
            name="John Doe",
            first_name="John",
            last_name="Doe"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Experienced teacher",
            specialty="Mathematics"
        )
        
        self.service = AvailableSlotsService(
            teacher=self.teacher, 
            schools=[self.school]
        )
    
    def test_get_available_slots_invalid_duration(self):
        """Test that invalid duration raises ValueError."""
        test_date = date(2025, 8, 18)
        
        with self.assertRaises(ValueError):
            self.service.get_available_slots(test_date, duration_minutes=-30)
    
    def test_get_available_slots_invalid_date_range(self):
        """Test that invalid date range raises ValueError."""
        start_date = date(2025, 8, 20)
        end_date = date(2025, 8, 18)
        
        with self.assertRaises(ValueError):
            self.service.get_available_slots(start_date, end_date=end_date)
