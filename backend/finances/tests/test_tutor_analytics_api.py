"""
Tests for TutorAnalyticsView API endpoint.

This module tests the individual tutor analytics functionality that provides
business metrics for tutors including revenue trends, student metrics, and 
session analytics.
"""

import json
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import (
    School, 
    SchoolMembership, 
    SchoolRole, 
    TeacherProfile, 
    Course,
    EducationalSystem,
    TeacherCourse
)
from finances.models import (
    ClassSession, 
    TeacherPaymentEntry, 
    SessionType, 
    SessionStatus,
    TeacherCompensationRule,
    CompensationRuleType,
    PaymentStatus
)

User = get_user_model()


class TutorAnalyticsAPITestCase(TestCase):
    """Test case for TutorAnalyticsView API."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create educational system
        self.educational_system, _ = EducationalSystem.objects.get_or_create(
            code="pt",
            defaults={
                "name": "Portugal",
                "description": "Portuguese educational system"
            }
        )
        
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        # Create tutor user and profile
        self.tutor_user = User.objects.create_user(
            email="tutor@example.com",
            name="John Tutor",
            password="testpass123"
        )
        
        self.tutor_profile = TeacherProfile.objects.create(
            user=self.tutor_user,
            bio="Experienced math tutor",
            specialty="Mathematics",
            hourly_rate=Decimal("25.00")
        )
        
        # Create school membership
        SchoolMembership.objects.create(
            user=self.tutor_user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Create courses
        self.course_math = Course.objects.create(
            name="Mathematics",
            code="MATH",
            educational_system=self.educational_system,
            education_level="ensino_secundario"
        )
        
        self.course_physics = Course.objects.create(
            name="Physics",
            code="PHYS",
            educational_system=self.educational_system,
            education_level="ensino_secundario"
        )
        
        # Associate tutor with courses
        TeacherCourse.objects.create(
            teacher=self.tutor_profile,
            course=self.course_math,
            hourly_rate=Decimal("30.00")
        )
        
        TeacherCourse.objects.create(
            teacher=self.tutor_profile,
            course=self.course_physics,
            hourly_rate=Decimal("25.00")
        )
        
        # Create compensation rule
        self.compensation_rule = TeacherCompensationRule.objects.create(
            teacher=self.tutor_profile,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="10",
            rate_per_hour=Decimal("25.00")
        )
        
        # Create students
        self.student1 = User.objects.create_user(
            email="student1@example.com",
            name="Student One"
        )
        
        self.student2 = User.objects.create_user(
            email="student2@example.com", 
            name="Student Two"
        )
        
        # Create class sessions with different dates for analytics
        self.session1 = self._create_session(
            date=date.today() - timedelta(days=30),
            session_type=SessionType.INDIVIDUAL,
            students=[self.student1],
            status=SessionStatus.COMPLETED,
            duration_hours=Decimal("1.5")
        )
        
        self.session2 = self._create_session(
            date=date.today() - timedelta(days=15),
            session_type=SessionType.GROUP,
            students=[self.student1, self.student2],
            status=SessionStatus.COMPLETED,
            duration_hours=Decimal("2.0")
        )
        
        self.session3 = self._create_session(
            date=date.today() - timedelta(days=5),
            session_type=SessionType.INDIVIDUAL,
            students=[self.student2],
            status=SessionStatus.COMPLETED,
            duration_hours=Decimal("1.0")
        )
        
        # Create payment entries
        self._create_payment_entry(self.session1, Decimal("37.50"))
        self._create_payment_entry(self.session2, Decimal("50.00"))
        self._create_payment_entry(self.session3, Decimal("25.00"))
        
        self.analytics_url = reverse('finances:tutor-analytics', kwargs={'school_id': self.school.id})
    
    def _create_session(self, date, session_type, students, status, duration_hours):
        """Helper to create a class session."""
        session = ClassSession.objects.create(
            teacher=self.tutor_profile,
            school=self.school,
            date=date,
            start_time=time(10, 0),  # 10:00 AM
            end_time=time(11, 30),   # 11:30 AM
            session_type=session_type,
            grade_level="10",
            student_count=len(students),
            status=status,
            actual_duration_hours=duration_hours
        )
        session.students.set(students)
        return session
    
    def _create_payment_entry(self, session, amount):
        """Helper to create a payment entry."""
        return TeacherPaymentEntry.objects.create(
            session=session,
            teacher=self.tutor_profile,
            school=self.school,
            billing_period=session.date.strftime("%Y-%m"),
            hours_taught=session.actual_duration_hours,
            rate_applied=Decimal("25.00"),
            amount_earned=amount,
            compensation_rule=self.compensation_rule,
            payment_status=PaymentStatus.PAID
        )
    
    def test_analytics_requires_authentication(self):
        """Test that analytics endpoint requires authentication."""
        response = self.client.get(self.analytics_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_analytics_basic_structure(self):
        """Test basic analytics response structure."""
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.get(self.analytics_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        required_keys = [
            'overview',
            'revenue',
            'sessions',
            'students',
            'trends',
            'projections',
            'meta'
        ]
        
        for key in required_keys:
            self.assertIn(key, data)
    
    def test_tutor_info_section(self):
        """Test tutor information section."""
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.get(self.analytics_url)
        
        data = response.json()
        tutor_info = data['tutor_info']
        
        expected_fields = ['id', 'name', 'email', 'profile_completion_score', 'schools']
        for field in expected_fields:
            self.assertIn(field, tutor_info)
        
        self.assertEqual(tutor_info['name'], self.tutor_user.name)
        self.assertEqual(tutor_info['email'], self.tutor_user.email)
        self.assertEqual(len(tutor_info['schools']), 1)
        self.assertEqual(tutor_info['schools'][0]['name'], self.school.name)
    
    def test_revenue_trends_calculation(self):
        """Test revenue trends calculation."""
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.get(self.analytics_url)
        
        data = response.json()
        revenue_trends = data['revenue_trends']
        
        # Check basic structure
        expected_fields = ['total_revenue', 'monthly_revenue', 'revenue_growth', 'average_hourly_rate']
        for field in expected_fields:
            self.assertIn(field, revenue_trends)
        
        # Check calculations
        self.assertEqual(float(revenue_trends['total_revenue']), 112.50)  # 37.50 + 50.00 + 25.00
        self.assertGreater(len(revenue_trends['monthly_revenue']), 0)
    
    def test_student_metrics_calculation(self):
        """Test student metrics calculation."""
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.get(self.analytics_url)
        
        data = response.json()
        student_metrics = data['student_metrics']
        
        expected_fields = ['total_students', 'active_students', 'new_students_this_month', 'retention_rate']
        for field in expected_fields:
            self.assertIn(field, student_metrics)
        
        self.assertEqual(student_metrics['total_students'], 2)
        self.assertEqual(student_metrics['active_students'], 2)
    
    def test_session_analytics_calculation(self):
        """Test session analytics calculation."""
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.get(self.analytics_url)
        
        data = response.json()
        session_analytics = data['session_analytics']
        
        expected_fields = ['total_sessions', 'total_hours_taught', 'individual_sessions', 'group_sessions', 'completion_rate']
        for field in expected_fields:
            self.assertIn(field, session_analytics)
        
        self.assertEqual(session_analytics['total_sessions'], 3)
        self.assertEqual(float(session_analytics['total_hours_taught']), 4.5)  # 1.5 + 2.0 + 1.0
        self.assertEqual(session_analytics['individual_sessions'], 2)
        self.assertEqual(session_analytics['group_sessions'], 1)
        self.assertEqual(session_analytics['completion_rate'], 100.0)  # All sessions completed
    
    def test_course_performance_calculation(self):
        """Test course performance calculation."""
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.get(self.analytics_url)
        
        data = response.json()
        course_performance = data['course_performance']
        
        self.assertIsInstance(course_performance, list)
        self.assertGreater(len(course_performance), 0)
        
        # Check structure of course performance data
        course_data = course_performance[0]
        expected_fields = ['course_id', 'course_name', 'sessions_count', 'total_hours', 'total_revenue', 'avg_rating']
        for field in expected_fields:
            self.assertIn(field, course_data)
    
    def test_monthly_breakdown_calculation(self):
        """Test monthly breakdown calculation."""
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.get(self.analytics_url)
        
        data = response.json()
        monthly_breakdown = data['monthly_breakdown']
        
        self.assertIsInstance(monthly_breakdown, list)
        self.assertGreater(len(monthly_breakdown), 0)
        
        # Check structure of monthly data
        month_data = monthly_breakdown[0]
        expected_fields = ['month', 'revenue', 'sessions', 'hours', 'students', 'avg_hourly_rate']
        for field in expected_fields:
            self.assertIn(field, month_data)
    
    def test_date_range_filtering(self):
        """Test filtering analytics by date range."""
        self.client.force_authenticate(user=self.tutor_user)
        
        # Test with specific date range
        start_date = (date.today() - timedelta(days=20)).isoformat()
        end_date = date.today().isoformat()
        
        response = self.client.get(self.analytics_url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should only include sessions within date range (session2 and session3)
        self.assertEqual(data['session_analytics']['total_sessions'], 2)
        self.assertEqual(float(data['revenue_trends']['total_revenue']), 75.00)  # 50.00 + 25.00
    
    def test_school_filtering(self):
        """Test filtering analytics by school."""
        # Create second school and membership
        school2 = School.objects.create(name="Second School")
        SchoolMembership.objects.create(
            user=self.tutor_user,
            school=school2,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.tutor_user)
        
        # Test with specific school filter
        response = self.client.get(self.analytics_url, {
            'school_id': self.school.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should only include data from the specified school
        self.assertEqual(data['session_analytics']['total_sessions'], 3)
    
    def test_analytics_caching(self):
        """Test that analytics responses are cached appropriately."""
        self.client.force_authenticate(user=self.tutor_user)
        
        with patch('django.core.cache.cache.get') as mock_cache_get, \
             patch('django.core.cache.cache.set') as mock_cache_set:
            
            mock_cache_get.return_value = None  # Cache miss
            
            response = self.client.get(self.analytics_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify cache was attempted to be read and set
            mock_cache_get.assert_called()
            mock_cache_set.assert_called()
    
    def test_empty_analytics_data(self):
        """Test analytics with no data."""
        # Create new tutor with no sessions
        empty_tutor = User.objects.create_user(
            email="empty@example.com",
            name="Empty Tutor"
        )
        
        empty_profile = TeacherProfile.objects.create(
            user=empty_tutor,
            bio="New tutor"
        )
        
        SchoolMembership.objects.create(
            user=empty_tutor,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        self.client.force_authenticate(user=empty_tutor)
        response = self.client.get(self.analytics_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(float(data['revenue_trends']['total_revenue']), 0.0)
        self.assertEqual(data['student_metrics']['total_students'], 0)
        self.assertEqual(data['session_analytics']['total_sessions'], 0)
    
    def test_invalid_date_range(self):
        """Test handling of invalid date ranges."""
        self.client.force_authenticate(user=self.tutor_user)
        
        # Test with invalid date format
        response = self.client.get(self.analytics_url, {
            'start_date': 'invalid-date',
            'end_date': 'also-invalid'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
    
    def test_unauthorized_school_access(self):
        """Test accessing analytics for school user doesn't belong to."""
        # Create another school
        other_school = School.objects.create(name="Other School")
        
        self.client.force_authenticate(user=self.tutor_user)
        
        response = self.client.get(self.analytics_url, {
            'school_id': other_school.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_performance_with_large_dataset(self):
        """Test analytics performance with larger dataset."""
        # Create additional sessions and data
        for i in range(50):
            session_date = date.today() - timedelta(days=i)
            session = self._create_session(
                date=session_date,
                session_type=SessionType.INDIVIDUAL,
                students=[self.student1],
                status=SessionStatus.COMPLETED,
                duration_hours=Decimal("1.0")
            )
            self._create_payment_entry(session, Decimal("25.00"))
        
        self.client.force_authenticate(user=self.tutor_user)
        
        start_time = datetime.now()
        response = self.client.get(self.analytics_url)
        end_time = datetime.now()
        
        # Response should be fast (under 2 seconds)
        self.assertLess((end_time - start_time).total_seconds(), 2.0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_analytics_data_accuracy(self):
        """Test accuracy of analytics calculations."""
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.get(self.analytics_url)
        
        data = response.json()
        
        # Verify total revenue calculation
        total_revenue = float(data['revenue_trends']['total_revenue'])
        expected_revenue = 37.50 + 50.00 + 25.00
        self.assertEqual(total_revenue, expected_revenue)
        
        # Verify hours calculation
        total_hours = float(data['session_analytics']['total_hours_taught'])
        expected_hours = 1.5 + 2.0 + 1.0
        self.assertEqual(total_hours, expected_hours)
        
        # Verify student count
        total_students = data['student_metrics']['total_students']
        self.assertEqual(total_students, 2)  # student1 and student2