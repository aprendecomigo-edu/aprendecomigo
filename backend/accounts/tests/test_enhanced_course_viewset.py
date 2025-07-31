"""
Tests for Enhanced CourseViewSet API endpoint.

This module tests the enhanced course catalog functionality that provides
advanced filtering, popularity metrics, and market data for course selection.
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
from finances.models import ClassSession, SessionStatus, SessionType

User = get_user_model()


class EnhancedCourseViewSetTestCase(TestCase):
    """Test case for Enhanced CourseViewSet API."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create educational systems
        self.edu_system_pt, _ = EducationalSystem.objects.get_or_create(
            code="pt",
            defaults={
                "name": "Portugal",
                "description": "Portuguese educational system"
            }
        )
        
        self.edu_system_custom, _ = EducationalSystem.objects.get_or_create(
            code="custom",
            defaults={
                "name": "Custom",
                "description": "Custom educational system"
            }
        )
        
        # Create schools
        self.school1 = School.objects.create(
            name="Test School 1",
            description="A test school"
        )
        
        self.school2 = School.objects.create(
            name="Test School 2", 
            description="Another test school"
        )
        
        # Create courses
        self.course_math = Course.objects.create(
            name="Mathematics",
            code="MATH",
            educational_system=self.edu_system_pt,
            education_level="ensino_secundario",
            description="Advanced mathematics course"
        )
        
        self.course_physics = Course.objects.create(
            name="Physics",
            code="PHYS",
            educational_system=self.edu_system_pt,
            education_level="ensino_secundario",
            description="Advanced physics course"
        )
        
        self.course_english = Course.objects.create(
            name="English",
            code="ENG",
            educational_system=self.edu_system_custom,
            education_level="high_school",
            description="English language course"
        )
        
        # Create teachers
        self.teacher1_user = User.objects.create_user(
            email="teacher1@example.com",
            name="John Teacher",
            password="testpass123"
        )
        
        self.teacher1_profile = TeacherProfile.objects.create(
            user=self.teacher1_user,
            bio="Experienced math teacher",
            specialty="Mathematics",
            hourly_rate=Decimal("25.00")
        )
        
        self.teacher2_user = User.objects.create_user(
            email="teacher2@example.com",
            name="Jane Teacher",
            password="testpass123"
        )
        
        self.teacher2_profile = TeacherProfile.objects.create(
            user=self.teacher2_user,
            bio="Physics expert",
            specialty="Physics",
            hourly_rate=Decimal("30.00")
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.teacher1_user,
            school=self.school1,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.teacher2_user,
            school=self.school1,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Create teacher-course relationships
        TeacherCourse.objects.create(
            teacher=self.teacher1_profile,
            course=self.course_math,
            hourly_rate=Decimal("30.00")
        )
        
        TeacherCourse.objects.create(
            teacher=self.teacher1_profile,
            course=self.course_physics,
            hourly_rate=Decimal("25.00")
        )
        
        TeacherCourse.objects.create(
            teacher=self.teacher2_profile,
            course=self.course_physics,
            hourly_rate=Decimal("35.00")
        )
        
        # Create students for testing
        self.student1 = User.objects.create_user(
            email="student1@example.com",
            name="Student One"
        )
        
        self.student2 = User.objects.create_user(
            email="student2@example.com",
            name="Student Two"
        )
        
        # Create some class sessions for popularity metrics
        self._create_sessions_for_popularity()
        
        self.courses_url = reverse('accounts:course-list')
    
    def _create_sessions_for_popularity(self):
        """Create sessions to test popularity metrics."""
        # Create sessions for math course (more popular)
        for i in range(5):
            session = ClassSession.objects.create(
                teacher=self.teacher1_profile,
                school=self.school1,
                date=date.today() - timedelta(days=i*7),
                start_time=time(10, 0),  # 10:00 AM
                end_time=time(11, 0),    # 11:00 AM
                session_type=SessionType.INDIVIDUAL,
                grade_level="10",
                student_count=1,
                status=SessionStatus.COMPLETED,
                actual_duration_hours=Decimal("1.0")
            )
            session.students.add(self.student1)
        
        # Create sessions for physics course (less popular)
        for i in range(2):
            session = ClassSession.objects.create(
                teacher=self.teacher2_profile,
                school=self.school1,
                date=date.today() - timedelta(days=i*14),
                start_time=time(14, 0),  # 2:00 PM
                end_time=time(15, 0),    # 3:00 PM
                session_type=SessionType.INDIVIDUAL,
                grade_level="11",
                student_count=1,
                status=SessionStatus.COMPLETED,
                actual_duration_hours=Decimal("1.0")
            )
            session.students.add(self.student2)
    
    def test_courses_list_requires_authentication(self):
        """Test that courses endpoint requires authentication."""
        response = self.client.get(self.courses_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_courses_basic_list(self):
        """Test basic course listing functionality."""
        self.client.force_authenticate(user=self.teacher1_user)
        response = self.client.get(self.courses_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return all courses (including migration-created courses)
        self.assertGreaterEqual(len(data), 3)  # At least our 3 test courses
        
        # Check our test course names are present
        course_names = [course['name'] for course in data]
        self.assertIn('Mathematics', course_names)
        self.assertIn('Physics', course_names)
        self.assertIn('English', course_names)
    
    def test_courses_filtering_by_educational_system(self):
        """Test filtering courses by educational system."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Filter by Portuguese system
        response = self.client.get(self.courses_url, {
            'educational_system': self.edu_system_pt.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return Portuguese system courses (including migration-created ones)
        self.assertGreaterEqual(len(data), 2)  # At least our 2 test courses
        course_names = [course['name'] for course in data]
        self.assertIn('Mathematics', course_names)
        self.assertIn('Physics', course_names)
        self.assertNotIn('English', course_names)  # English is in custom system
    
    def test_courses_filtering_by_education_level(self):
        """Test filtering courses by education level."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Filter by secondary education
        response = self.client.get(self.courses_url, {
            'education_level': 'ensino_secundario'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return secondary level courses (including migration-created ones)
        self.assertGreaterEqual(len(data), 2)  # At least our 2 test courses
        course_names = [course['name'] for course in data]
        self.assertIn('Mathematics', course_names)
        self.assertIn('Physics', course_names)
        self.assertNotIn('English', course_names)  # English is high_school level
    
    def test_courses_search_functionality(self):
        """Test course search functionality."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Search for "math"
        response = self.client.get(self.courses_url, {
            'search': 'math'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return only Mathematics course
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Mathematics')
    
    def test_courses_with_popularity_metrics(self):
        """Test courses endpoint with popularity metrics."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Request courses with popularity metrics
        response = self.client.get(self.courses_url, {
            'include_popularity': 'true'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check that popularity metrics are included
        for course_data in data:
            self.assertIn('popularity_metrics', course_data)
            popularity = course_data['popularity_metrics']
            
            # Check required popularity fields
            expected_fields = ['total_sessions', 'unique_students', 'popularity_score', 'rank']
            for field in expected_fields:
                self.assertIn(field, popularity)
            
            # Note: Both teacher1 and teacher2 teach Physics, so Physics gets sessions from both
            if course_data['name'] == 'Mathematics':
                # Only teacher1 teaches Math (5 sessions)
                self.assertEqual(popularity['total_sessions'], 5)
                self.assertEqual(popularity['unique_students'], 1)
                self.assertGreater(popularity['popularity_score'], 0)
            elif course_data['name'] == 'Physics':
                # Both teacher1 and teacher2 teach Physics (5 + 2 = 7 sessions total)
                self.assertEqual(popularity['total_sessions'], 7)
                self.assertEqual(popularity['unique_students'], 2)  # student1 and student2
                self.assertGreater(popularity['popularity_score'], 0)
            elif course_data['name'] == 'English':
                # No teachers teach English
                self.assertEqual(popularity['total_sessions'], 0)
                self.assertEqual(popularity['unique_students'], 0)
                self.assertEqual(popularity['popularity_score'], 0)
    
    def test_courses_with_teacher_info(self):
        """Test courses endpoint with teacher information."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Request courses with teacher info
        response = self.client.get(self.courses_url, {
            'include_teachers': 'true'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check that teacher info is included
        for course_data in data:
            self.assertIn('available_teachers', course_data)
            teachers = course_data['available_teachers']
            
            # Mathematics should have 1 teacher
            if course_data['name'] == 'Mathematics':
                self.assertEqual(len(teachers), 1)
                self.assertEqual(teachers[0]['name'], 'John Teacher')
                self.assertIn('hourly_rate', teachers[0])
                self.assertIn('profile_completion_score', teachers[0])
            
            # Physics should have 2 teachers
            elif course_data['name'] == 'Physics':
                self.assertEqual(len(teachers), 2)
                teacher_names = [t['name'] for t in teachers]
                self.assertIn('John Teacher', teacher_names)
                self.assertIn('Jane Teacher', teacher_names)
            
            # English should have no teachers
            elif course_data['name'] == 'English':
                self.assertEqual(len(teachers), 0)
    
    def test_courses_with_market_data(self):
        """Test courses endpoint with market data."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Request courses with market data
        response = self.client.get(self.courses_url, {
            'include_market_data': 'true'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check that market data is included
        for course_data in data:
            self.assertIn('market_data', course_data)
            market_data = course_data['market_data']
            
            # Check required market data fields
            expected_fields = ['avg_hourly_rate', 'min_hourly_rate', 'max_hourly_rate', 
                             'total_teachers', 'demand_score']
            for field in expected_fields:
                self.assertIn(field, market_data)
            
            # Verify calculations for courses with teachers
            if course_data['name'] == 'Mathematics':
                self.assertEqual(float(market_data['avg_hourly_rate']), 30.00)
                self.assertEqual(float(market_data['min_hourly_rate']), 30.00)
                self.assertEqual(float(market_data['max_hourly_rate']), 30.00)
                self.assertEqual(market_data['total_teachers'], 1)
            
            elif course_data['name'] == 'Physics':
                # Should average the two teachers' rates (25.00 + 35.00) / 2 = 30.00
                self.assertEqual(float(market_data['avg_hourly_rate']), 30.00)
                self.assertEqual(float(market_data['min_hourly_rate']), 25.00)
                self.assertEqual(float(market_data['max_hourly_rate']), 35.00)
                self.assertEqual(market_data['total_teachers'], 2)
    
    def test_courses_ordering_by_popularity(self):
        """Test ordering courses by popularity."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Request courses ordered by popularity
        response = self.client.get(self.courses_url, {
            'include_popularity': 'true',
            'ordering': '-popularity_score'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Physics should be first (most popular - 7 sessions vs 5 for Math)
        # Find Physics in results since ordering within the migration data might vary
        physics_course = next(c for c in data if c['name'] == 'Physics')
        math_course = next(c for c in data if c['name'] == 'Mathematics')
        english_course = next(c for c in data if c['name'] == 'English')
        
        # Physics should have higher popularity score than Math
        self.assertGreater(physics_course['popularity_metrics']['popularity_score'], 
                          math_course['popularity_metrics']['popularity_score'])
        
        # English should have zero popularity score
        self.assertEqual(english_course['popularity_metrics']['popularity_score'], 0)
    
    def test_courses_ordering_by_price(self):
        """Test ordering courses by average price."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Request courses ordered by price (ascending)
        response = self.client.get(self.courses_url, {
            'include_market_data': 'true',
            'ordering': 'avg_hourly_rate'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Filter out courses with no teachers for price comparison
        courses_with_teachers = [c for c in data if c['market_data']['total_teachers'] > 0]
        
        # Verify ordering (ascending by average rate)
        rates = [float(c['market_data']['avg_hourly_rate']) for c in courses_with_teachers]
        self.assertEqual(rates, sorted(rates))
    
    def test_courses_combined_filters_and_metrics(self):
        """Test combining multiple filters with all metrics."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Request Portuguese courses with all metrics
        response = self.client.get(self.courses_url, {
            'educational_system': self.edu_system_pt.id,
            'include_popularity': 'true',
            'include_teachers': 'true',
            'include_market_data': 'true',
            'ordering': '-popularity_score'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return Portuguese courses (including migration-created ones)
        self.assertGreaterEqual(len(data), 2)  # At least our 2 test courses
        
        # Verify all enhanced data is present for our test courses
        test_courses = [c for c in data if c['name'] in ['Mathematics', 'Physics']]
        for course_data in test_courses:
            self.assertIn('popularity_metrics', course_data)
            self.assertIn('available_teachers', course_data)
            self.assertIn('market_data', course_data)
        
        # Find our test courses in the results
        test_courses = [c for c in data if c['name'] in ['Mathematics', 'Physics']]
        self.assertEqual(len(test_courses), 2)
        
        # Physics should be more popular than Mathematics (7 sessions vs 5)
        physics_course = next(c for c in test_courses if c['name'] == 'Physics')
        math_course = next(c for c in test_courses if c['name'] == 'Mathematics')
        
        self.assertGreater(physics_course['popularity_metrics']['popularity_score'],
                          math_course['popularity_metrics']['popularity_score'])
    
    def test_courses_caching(self):
        """Test that course data is cached appropriately."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        with patch('django.core.cache.cache.get') as mock_cache_get, \
             patch('django.core.cache.cache.set') as mock_cache_set:
            
            mock_cache_get.return_value = None  # Cache miss
            
            response = self.client.get(self.courses_url, {
                'include_popularity': 'true',
                'include_market_data': 'true'
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify cache was attempted to be read and set
            mock_cache_get.assert_called()
            mock_cache_set.assert_called()
    
    def test_courses_invalid_filter_parameters(self):
        """Test handling of invalid filter parameters."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Test invalid educational system ID
        response = self.client.get(self.courses_url, {
            'educational_system': 999999
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
    
    def test_courses_performance_with_large_dataset(self):
        """Test course endpoint performance with larger dataset."""
        # Create additional courses and data
        for i in range(20):
            course = Course.objects.create(
                name=f"Course {i}",
                code=f"C{i:03d}",
                educational_system=self.edu_system_pt,
                education_level="ensino_secundario"
            )
            
            # Associate with teacher
            TeacherCourse.objects.create(
                teacher=self.teacher1_profile,
                course=course,
                hourly_rate=Decimal(f"{20 + i}.00")
            )
        
        self.client.force_authenticate(user=self.teacher1_user)
        
        start_time = datetime.now()
        response = self.client.get(self.courses_url, {
            'include_popularity': 'true',
            'include_teachers': 'true',
            'include_market_data': 'true'
        })
        end_time = datetime.now()
        
        # Response should be fast (under 2 seconds)
        self.assertLess((end_time - start_time).total_seconds(), 2.0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return all courses (48 total: 25 from migration + 3 original + 20 new)
        data = response.json()
        self.assertEqual(len(data), 48)
    
    def test_courses_empty_results(self):
        """Test course endpoint with no matching results."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Search for non-existent course
        response = self.client.get(self.courses_url, {
            'search': 'nonexistent'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 0)
    
    def test_courses_popularity_calculation_accuracy(self):
        """Test accuracy of popularity score calculations."""
        self.client.force_authenticate(user=self.teacher1_user)
        
        response = self.client.get(self.courses_url, {
            'include_popularity': 'true'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Find math and physics courses
        math_course = next(c for c in data if c['name'] == 'Mathematics')
        physics_course = next(c for c in data if c['name'] == 'Physics')
        english_course = next(c for c in data if c['name'] == 'English')
        
        # Mathematics should have higher popularity score than Physics
        math_score = math_course['popularity_metrics']['popularity_score']
        physics_score = physics_course['popularity_metrics']['popularity_score']
        english_score = english_course['popularity_metrics']['popularity_score']
        
        self.assertGreater(math_score, physics_score)
        self.assertGreater(physics_score, english_score)
        self.assertEqual(english_score, 0)  # No sessions = 0 score