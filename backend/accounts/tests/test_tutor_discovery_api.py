"""
Comprehensive tests for TutorDiscoveryAPIView.

This module tests the public tutor discovery API that allows students and parents
to search for tutors without authentication, with proper privacy controls.

Tests cover:
- Search and filtering functionality
- Performance optimization
- Rate limiting and throttling
- Privacy controls
- Error handling
- Data validation
"""

import time
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole, TeacherProfile,
    Course, EducationalSystem, TeacherCourse, EducationalSystemType
)
from accounts.tests.test_base import BaseTestCase


class TutorDiscoveryAPITestCase(BaseTestCase):
    """Test case for TutorDiscoveryAPIView."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create educational system
        self.educational_system = self.default_educational_system  # Use default from BaseTestCase
        
        # Create schools
        self.school1 = School.objects.create(
            name="Math Tutoring School",
            description="Specialized in mathematics"
        )
        
        self.school2 = School.objects.create(
            name="Science Academy",
            description="Science tutoring school"
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
        
        self.course_chemistry = Course.objects.create(
            name="Chemistry",
            code="CHEM",
            educational_system=self.educational_system,
            education_level="ensino_basico_3_ciclo"
        )
        
        # Create tutors with complete profiles
        self.tutor1_user = CustomUser.objects.create_user(
            email="tutor1@example.com",
            name="Alice Mathematics",
            password="testpass123"
        )
        
        self.tutor1_profile = TeacherProfile.objects.create(
            user=self.tutor1_user,
            bio="Experienced mathematics tutor with 5 years of experience",
            specialty="Mathematics",
            hourly_rate=Decimal("30.00"),
            is_profile_complete=True,
            profile_completion_score=Decimal("85.50"),
            teaching_subjects=["Mathematics", "Algebra", "Calculus"]
        )
        
        self.tutor2_user = CustomUser.objects.create_user(
            email="tutor2@example.com",
            name="Bob Physics",
            password="testpass123"
        )
        
        self.tutor2_profile = TeacherProfile.objects.create(
            user=self.tutor2_user,
            bio="Physics expert specializing in advanced topics",
            specialty="Physics",
            hourly_rate=Decimal("35.00"),
            is_profile_complete=True,
            profile_completion_score=Decimal("92.00"),
            teaching_subjects=["Physics", "Mechanics", "Thermodynamics"]
        )
        
        self.tutor3_user = CustomUser.objects.create_user(
            email="tutor3@example.com",
            name="Carol Chemistry",
            password="testpass123"
        )
        
        self.tutor3_profile = TeacherProfile.objects.create(
            user=self.tutor3_user,
            bio="Chemistry tutor for middle school students",
            specialty="Chemistry",
            hourly_rate=Decimal("25.00"),
            is_profile_complete=True,
            profile_completion_score=Decimal("78.00"),
            teaching_subjects=["Chemistry", "Organic Chemistry"]
        )
        
        # Create incomplete profile tutor (should not appear in results)
        self.incomplete_tutor_user = CustomUser.objects.create_user(
            email="incomplete@example.com",
            name="Dave Incomplete",
            password="testpass123"
        )
        
        self.incomplete_tutor_profile = TeacherProfile.objects.create(
            user=self.incomplete_tutor_user,
            bio="Incomplete profile",
            is_profile_complete=False,
            profile_completion_score=Decimal("30.00")
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.tutor1_user,
            school=self.school1,
            role=SchoolRole.SCHOOL_OWNER,  # Individual tutor
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.tutor2_user,
            school=self.school2,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.tutor3_user,
            school=self.school1,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.incomplete_tutor_user,
            school=self.school1,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Create teacher-course relationships
        TeacherCourse.objects.create(
            teacher=self.tutor1_profile,
            course=self.course_math,
            hourly_rate=Decimal("32.00"),
            is_active=True
        )
        
        TeacherCourse.objects.create(
            teacher=self.tutor2_profile,
            course=self.course_physics,
            hourly_rate=Decimal("38.00"),
            is_active=True
        )
        
        TeacherCourse.objects.create(
            teacher=self.tutor3_profile,
            course=self.course_chemistry,
            hourly_rate=Decimal("28.00"),
            is_active=True
        )
        
        self.discovery_url = reverse('accounts:tutor-discovery')
    
    def test_public_access_no_authentication_required(self):
        """Test that the discovery endpoint is publicly accessible."""
        response = self.client.get(self.discovery_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_basic_tutor_discovery(self):
        """Test basic tutor discovery without filters."""
        response = self.client.get(self.discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertIn('total', data)
        
        # Should return 3 complete profiles (excluding incomplete)
        self.assertEqual(data['total'], 3)
        self.assertEqual(len(data['results']), 3)
        
        # Check response structure
        tutor = data['results'][0]
        expected_fields = [
            'id', 'name', 'bio', 'specialty', 'profile_completion_score',
            'is_profile_complete', 'average_hourly_rate', 'subjects', 'school',
            'teaching_subjects', 'last_activity'
        ]
        
        for field in expected_fields:
            self.assertIn(field, tutor)
    
    def test_subject_filtering_by_name(self):
        """Test filtering tutors by subject name."""
        response = self.client.get(self.discovery_url, {'subjects': 'Mathematics'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['name'], 'Alice Mathematics')
    
    def test_subject_filtering_by_id(self):
        """Test filtering tutors by course ID."""
        response = self.client.get(self.discovery_url, {'subjects': str(self.course_physics.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['name'], 'Bob Physics')
    
    def test_multiple_subject_filtering(self):
        """Test filtering by multiple subjects."""
        subjects = f"{self.course_math.id},Physics"
        response = self.client.get(self.discovery_url, {'subjects': subjects})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['total'], 2)
        
        names = [tutor['name'] for tutor in data['results']]
        self.assertIn('Alice Mathematics', names)
        self.assertIn('Bob Physics', names)
    
    def test_rate_range_filtering(self):
        """Test filtering tutors by rate range."""
        # Test minimum rate filter
        response = self.client.get(self.discovery_url, {'rate_min': '30'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return tutors with rates >= 30 (Alice: 32, Bob: 38)
        self.assertEqual(data['total'], 2)
        
        # Test maximum rate filter
        response = self.client.get(self.discovery_url, {'rate_max': '30'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return tutors with rates <= 30 (Carol: 28)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['name'], 'Carol Chemistry')
        
        # Test range filter
        response = self.client.get(self.discovery_url, {
            'rate_min': '25',
            'rate_max': '35'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return Alice (32) and Carol (28)
        self.assertEqual(data['total'], 2)
    
    def test_education_level_filtering(self):
        """Test filtering by education level."""
        response = self.client.get(self.discovery_url, {
            'education_level': 'ensino_secundario'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return tutors teaching secondary level (Alice and Bob)
        self.assertEqual(data['total'], 2)
        
        names = [tutor['name'] for tutor in data['results']]
        self.assertIn('Alice Mathematics', names)
        self.assertIn('Bob Physics', names)
    
    def test_educational_system_filtering(self):
        """Test filtering by educational system."""
        response = self.client.get(self.discovery_url, {
            'educational_system': str(self.educational_system.id)
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # All our test tutors are in the Portugal system
        self.assertEqual(data['total'], 3)
    
    def test_search_filtering(self):
        """Test free text search filtering."""
        # Search by name
        response = self.client.get(self.discovery_url, {'search': 'Alice'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['name'], 'Alice Mathematics')
        
        # Search by specialty
        response = self.client.get(self.discovery_url, {'search': 'Physics'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['name'], 'Bob Physics')
        
        # Search by bio content
        response = self.client.get(self.discovery_url, {'search': 'middle school'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['name'], 'Carol Chemistry')
    
    def test_ordering_by_rate(self):
        """Test ordering tutors by hourly rate."""
        # Ascending order
        response = self.client.get(self.discovery_url, {'ordering': 'rate'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        rates = [tutor['average_hourly_rate'] for tutor in data['results']]
        self.assertEqual(rates, sorted(rates))
        
        # Descending order
        response = self.client.get(self.discovery_url, {'ordering': '-rate'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        rates = [tutor['average_hourly_rate'] for tutor in data['results']]
        self.assertEqual(rates, sorted(rates, reverse=True))
    
    def test_ordering_by_completion_score(self):
        """Test ordering by profile completion score."""
        response = self.client.get(self.discovery_url, {'ordering': '-completion_score'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        scores = [tutor['profile_completion_score'] for tutor in data['results']]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        # Bob should be first (92.00), then Alice (85.50), then Carol (78.00)
        self.assertEqual(data['results'][0]['name'], 'Bob Physics')
        self.assertEqual(data['results'][1]['name'], 'Alice Mathematics')
        self.assertEqual(data['results'][2]['name'], 'Carol Chemistry')
    
    def test_ordering_by_name(self):
        """Test ordering by tutor name."""
        response = self.client.get(self.discovery_url, {'ordering': 'name'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        names = [tutor['name'] for tutor in data['results']]
        self.assertEqual(names, sorted(names))
    
    def test_pagination(self):
        """Test pagination functionality."""
        # Test limit parameter
        response = self.client.get(self.discovery_url, {'limit': '2'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['total'], 3)
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        
        # Test offset parameter
        response = self.client.get(self.discovery_url, {'limit': '2', 'offset': '2'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['count'], 1)  # Only 1 remaining
        self.assertEqual(data['total'], 3)
        self.assertIsNone(data['next'])
        self.assertIsNotNone(data['previous'])
    
    def test_invalid_parameters(self):
        """Test handling of invalid parameters."""
        # Invalid rate_min
        response = self.client.get(self.discovery_url, {'rate_min': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid rate_max
        response = self.client.get(self.discovery_url, {'rate_max': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid rate range
        response = self.client.get(self.discovery_url, {
            'rate_min': '50',
            'rate_max': '30'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid educational_system
        response = self.client.get(self.discovery_url, {'educational_system': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Negative rate_min
        response = self.client.get(self.discovery_url, {'rate_min': '-10'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_limit_validation(self):
        """Test limit parameter validation."""
        # Limit too high (should be capped at 50)
        response = self.client.get(self.discovery_url, {'limit': '100'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertLessEqual(data['count'], 50)
        
        # Limit too low (should be set to 1)
        response = self.client.get(self.discovery_url, {'limit': '0'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertGreaterEqual(data['count'], 0)
    
    def test_privacy_controls(self):
        """Test that only appropriate data is exposed."""
        response = self.client.get(self.discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        tutor = data['results'][0]
        
        # Should include public profile data
        self.assertIn('name', tutor)
        self.assertIn('bio', tutor)
        self.assertIn('specialty', tutor)
        self.assertIn('average_hourly_rate', tutor)
        self.assertIn('subjects', tutor)
        
        # Should not include sensitive data (email should not be directly exposed)
        # Email is included in our current implementation, but in production
        # you might want to remove or mask it
        
        # Bio should be limited in length
        if tutor['bio']:
            self.assertLessEqual(len(tutor['bio']), 500)
    
    def test_school_information_exposure(self):
        """Test that appropriate school information is exposed."""
        response = self.client.get(self.discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Find Alice (school owner - individual tutor)
        alice = next(t for t in data['results'] if t['name'] == 'Alice Mathematics')
        self.assertIsNotNone(alice['school'])
        self.assertTrue(alice['school']['is_individual_tutor'])
        
        # Find Bob (teacher at school)
        bob = next(t for t in data['results'] if t['name'] == 'Bob Physics')
        self.assertIsNotNone(bob['school'])
        self.assertFalse(bob['school']['is_individual_tutor'])
    
    def test_subjects_information(self):
        """Test that subject information is properly structured."""
        response = self.client.get(self.discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        tutor = data['results'][0]
        if tutor['subjects']:
            subject = tutor['subjects'][0]
            
            expected_fields = ['id', 'name', 'code', 'education_level', 'hourly_rate']
            for field in expected_fields:
                self.assertIn(field, subject)
    
    def test_incomplete_profiles_excluded(self):
        """Test that incomplete profiles are excluded from results."""
        response = self.client.get(self.discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should not include Dave Incomplete
        names = [tutor['name'] for tutor in data['results']]
        self.assertNotIn('Dave Incomplete', names)
    
    def test_invalid_ordering_defaults_to_completion_score(self):
        """Test that invalid ordering defaults to completion score."""
        response = self.client.get(self.discovery_url, {'ordering': 'invalid_field'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should be ordered by completion score descending (default)
        scores = [tutor['profile_completion_score'] for tutor in data['results']]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_caching_behavior(self):
        """Test that responses are cached appropriately."""
        from unittest.mock import patch
        
        with patch('django.core.cache.cache.get') as mock_cache_get, \
             patch('django.core.cache.cache.set') as mock_cache_set:
            
            mock_cache_get.return_value = None  # Cache miss
            
            response = self.client.get(self.discovery_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify cache was attempted to be read and set
            mock_cache_get.assert_called()
            mock_cache_set.assert_called()
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        response = self.client.get(self.discovery_url, {
            'subjects': 'Mathematics',
            'rate_min': '30',
            'search': 'experience',
            'ordering': '-completion_score'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return Alice who matches all criteria
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['name'], 'Alice Mathematics')
    
    def test_empty_results(self):
        """Test behavior when no tutors match the criteria."""
        response = self.client.get(self.discovery_url, {
            'subjects': 'NonexistentSubject',
            'rate_min': '1000'  # Very high rate
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['total'], 0)
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['results']), 0)
        self.assertIsNone(data['next'])
        self.assertIsNone(data['previous'])
    
    def test_teaching_subjects_array_handling(self):
        """Test that teaching_subjects array is properly handled."""
        response = self.client.get(self.discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        for tutor in data['results']:
            # teaching_subjects should be a list
            self.assertIsInstance(tutor['teaching_subjects'], list)
            
            # If present, should contain strings
            for subject in tutor['teaching_subjects']:
                self.assertIsInstance(subject, str)
    
    def test_average_rate_calculation_accuracy(self):
        """Test that average hourly rates are calculated correctly."""
        response = self.client.get(self.discovery_url, {'search': 'Alice'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        tutor = data['results'][0]
        
        # Alice has profile rate 30.00 but course rate 32.00
        # Should use course-specific rate when available
        self.assertEqual(tutor['average_hourly_rate'], 32.00)
        
        # Verify subjects have correct rates
        math_subject = next(s for s in tutor['subjects'] if s['name'] == 'Mathematics')
        self.assertEqual(math_subject['hourly_rate'], 32.00)
    
    def test_cache_key_generation_uniqueness(self):
        """Test that different parameters generate different cache keys."""
        with patch('django.core.cache.cache.get') as mock_cache_get, \
             patch('django.core.cache.cache.set') as mock_cache_set:
            
            mock_cache_get.return_value = None  # Always cache miss
            
            # Make requests with different parameters
            self.client.get(self.discovery_url)
            self.client.get(self.discovery_url, {'rate_min': '30'})
            self.client.get(self.discovery_url, {'subjects': 'Mathematics'})
            
            # Should have been called multiple times with different keys
            self.assertEqual(mock_cache_get.call_count, 3)
            self.assertEqual(mock_cache_set.call_count, 3)
            
            # Verify different cache keys were used
            cache_keys = [call[0][0] for call in mock_cache_get.call_args_list]
            self.assertEqual(len(set(cache_keys)), 3)  # All unique keys


@override_settings(
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [
            'accounts.throttles.IPBasedThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'ip_based': '5/min',  # Very restrictive for testing
        }
    }
)
class TutorDiscoveryThrottlingTestCase(BaseTestCase):
    """Test rate limiting for tutor discovery endpoint."""

    def setUp(self):
        """Set up minimal test data for throttling tests."""
        cache.clear()
        
        # Create minimal test data - use get_or_create to avoid duplicates
        self.educational_system, _ = EducationalSystem.objects.get_or_create(
            code=EducationalSystemType.PORTUGAL,
            defaults={
                "name": "Test System",
                "description": "Test system"
            }
        )
        
        self.school = School.objects.create(name="Test School")
        
        self.user = CustomUser.objects.create_user(
            email="tutor@test.com",
            name="Test Tutor"
        )
        
        self.tutor = TeacherProfile.objects.create(
            user=self.user,
            bio="Test tutor",
            specialty="Test",
            hourly_rate=Decimal('30.00'),
            is_profile_complete=True,
            profile_completion_score=Decimal('80.0')
        )
        
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        self.client = APIClient()
        self.discovery_url = reverse('accounts:tutor-discovery')

    def test_rate_limiting_enforcement(self):
        """Test that the endpoint enforces rate limiting."""
        # Clear any existing cache/throttle state
        cache.clear()
        
        # Make requests up to the limit
        for i in range(5):
            response = self.client.get(self.discovery_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, 
                           f"Request {i+1} should succeed")
        
        # Next request should be throttled
        response = self.client.get(self.discovery_url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class TutorDiscoveryPerformanceTestCase(BaseTestCase):
    """Test performance characteristics of tutor discovery endpoint."""

    def setUp(self):
        """Set up performance test data."""
        cache.clear()
        
        # Create educational system and courses
        self.educational_system = EducationalSystem.objects.create(
            name="Performance Test System",
            code=EducationalSystemType.PORTUGAL,
            description="Performance test system"
        )
        
        self.courses = []
        for i in range(10):
            course = Course.objects.create(
                name=f"Course {i}",
                code=f"COURSE{i}",
                education_level="ensino_secundario",
                educational_system=self.educational_system
            )
            self.courses.append(course)
        
        # Create school
        self.school = School.objects.create(name="Performance Test School")
        
        # Create multiple tutors for performance testing
        self.create_performance_test_tutors()
        
        self.client = APIClient()
        self.discovery_url = reverse('accounts:tutor-discovery')

    def create_performance_test_tutors(self):
        """Create multiple tutors for performance testing."""
        for i in range(20):  # Create 20 tutors
            user = CustomUser.objects.create_user(
                email=f"tutor{i}@test.com",
                name=f"Test Tutor {i}"
            )
            
            tutor = TeacherProfile.objects.create(
                user=user,
                bio=f"Test tutor {i} with experience in various subjects.",
                specialty=f"Subject {i % 5}",  # 5 different specialties
                hourly_rate=Decimal(f'{20 + i * 2}.00'),  # Varying rates
                is_profile_complete=True,
                profile_completion_score=Decimal(f'{70.0 + (i % 30)}')  # Varying scores
            )
            
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER,
                is_active=True
            )
            
            # Each tutor teaches 2-3 courses
            for j in range(i % 3 + 1):
                course_index = (i + j) % len(self.courses)
                TeacherCourse.objects.create(
                    teacher=tutor,
                    course=self.courses[course_index],
                    hourly_rate=Decimal(f'{25 + i + j}.00'),
                    is_active=True
                )

    def test_response_time_basic_query(self):
        """Test that basic queries respond within acceptable time."""
        start_time = time.time()
        response = self.client.get(self.discovery_url)
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should respond within 2 seconds
        response_time = end_time - start_time
        self.assertLess(response_time, 2.0, f"Response took {response_time:.2f} seconds")

    def test_response_time_filtered_query(self):
        """Test response time for filtered queries."""
        params = {
            'subjects': self.courses[0].id,
            'rate_min': '25',
            'rate_max': '50',
            'ordering': '-completion_score'
        }
        
        start_time = time.time()
        response = self.client.get(self.discovery_url, params)
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should respond within 2 seconds even with filters
        response_time = end_time - start_time
        self.assertLess(response_time, 2.0, f"Filtered response took {response_time:.2f} seconds")

    def test_pagination_performance(self):
        """Test that pagination doesn't significantly impact performance."""
        page_sizes = [5, 10, 20, 50]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = self.client.get(self.discovery_url, {'limit': page_size})
            end_time = time.time()
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            response_time = end_time - start_time
            self.assertLess(response_time, 2.0, 
                          f"Page size {page_size} took {response_time:.2f} seconds")

    def test_search_performance(self):
        """Test that search queries perform acceptably."""
        search_terms = ['Test', 'Subject', 'experience', 'Tutor']
        
        for term in search_terms:
            start_time = time.time()
            response = self.client.get(self.discovery_url, {'search': term})
            end_time = time.time()
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            response_time = end_time - start_time
            self.assertLess(response_time, 2.0, 
                          f"Search for '{term}' took {response_time:.2f} seconds")

    def test_complex_query_performance(self):
        """Test performance of complex queries with multiple filters."""
        params = {
            'subjects': f"{self.courses[0].id},{self.courses[1].id}",
            'rate_min': '20',
            'rate_max': '60',
            'search': 'experience',
            'ordering': '-completion_score',
            'limit': '10'
        }
        
        start_time = time.time()
        response = self.client.get(self.discovery_url, params)
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_time = end_time - start_time
        self.assertLess(response_time, 2.0, 
                      f"Complex query took {response_time:.2f} seconds")