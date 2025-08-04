"""
Tests for Global Search API endpoints.
Following TDD methodology - tests written first before implementation.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole, 
    TeacherProfile, StudentProfile, Course, EducationalSystem
)
from accounts.tests.test_base import BaseTestCase


class GlobalSearchAPITestCase(BaseTestCase):
    """Test cases for global search API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Get or create educational system
        self.educational_system = self.default_educational_system  # Use default from BaseTestCase
        
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            description="A test school for global search"
        )
        
        # Create another school for isolation testing
        self.other_school = School.objects.create(
            name="Other School", 
            description="Should not appear in search results"
        )
        
        # Create a school admin user
        self.admin_user = CustomUser.objects.create_user(
            email="admin@testschool.com",
            name="Test Admin"
        )
        
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Create teachers
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@testschool.com",
            name="John Teacher"
        )
        
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Mathematics specialist with 10 years experience",
            specialty="Mathematics"
        )
        
        # Create students
        self.student_user = CustomUser.objects.create_user(
            email="student@testschool.com", 
            name="Jane Student"
        )
        
        SchoolMembership.objects.create(
            user=self.student_user,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        StudentProfile.objects.create(
            user=self.student_user,
            educational_system=self.educational_system,
            school_year="10",
            birth_date="2005-01-01"
        )
        
        # Create courses
        self.course = Course.objects.create(
            name="Advanced Mathematics",
            code="MATH_ADV",
            educational_system=self.educational_system,
            education_level="ensino_secundario",
            description="Advanced mathematical concepts for high school"
        )
        
        # Create users in other school (should not appear in search)
        self.other_teacher = CustomUser.objects.create_user(
            email="other@otherschool.com",
            name="Other Teacher"
        )
        
        SchoolMembership.objects.create(
            user=self.other_teacher,
            school=self.other_school,
            role=SchoolRole.TEACHER
        )
        
        # Authenticate admin user
        self.client.force_authenticate(user=self.admin_user)
    
    def test_global_search_teachers_success(self):
        """Test GET /api/search/global/ returns teachers from current school."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'John', 'types': 'teacher'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        
        teacher_result = data['results'][0]
        self.assertEqual(teacher_result['type'], 'teacher')
        self.assertEqual(teacher_result['title'], 'John Teacher')
        self.assertEqual(teacher_result['metadata']['email'], 'teacher@testschool.com')
        self.assertIn('specialty', teacher_result['metadata'])
        self.assertEqual(teacher_result['metadata']['specialty'], 'Mathematics')
    
    def test_global_search_students_success(self):
        """Test global search returns students from current school."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'Jane', 'types': 'student'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        
        student_result = data['results'][0]
        self.assertEqual(student_result['type'], 'student')
        self.assertEqual(student_result['title'], 'Jane Student')
        self.assertEqual(student_result['metadata']['email'], 'student@testschool.com')
        self.assertIn('school_year', student_result['metadata'])
        self.assertEqual(student_result['metadata']['school_year'], '10')
    
    def test_global_search_courses_success(self):
        """Test global search returns courses relevant to current school."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'Mathematics', 'types': 'class'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        
        course_result = data['results'][0]
        self.assertEqual(course_result['type'], 'class')
        self.assertEqual(course_result['title'], 'Advanced Mathematics')
        self.assertEqual(course_result['metadata']['code'], 'MATH_ADV')
        self.assertIn('description', course_result['metadata'])
    
    def test_global_search_multiple_types(self):
        """Test global search with multiple types."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'math', 'types': 'teacher,class'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertGreaterEqual(len(data['results']), 2)
        
        # Should find both teacher (specialty) and course
        types_found = [result['type'] for result in data['results']]
        self.assertIn('teacher', types_found)
        self.assertIn('class', types_found)
    
    def test_global_search_school_scoped(self):
        """Test that search results are scoped to user's current school."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'Other Teacher', 'types': 'teacher'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should not find teacher from other school
        self.assertEqual(len(data['results']), 0)
    
    def test_global_search_limit_parameter(self):
        """Test global search respects limit parameter."""
        # Create multiple teachers to test limit
        for i in range(15):
            user = CustomUser.objects.create_user(
                email=f"teacher{i}@testschool.com",
                name=f"Teacher {i}"
            )
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER
            )
        
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'Teacher', 'types': 'teacher', 'limit': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data['results']), 5)
    
    def test_global_search_default_limit(self):
        """Test global search uses default limit of 10."""
        # Create multiple teachers
        for i in range(15):
            user = CustomUser.objects.create_user(
                email=f"teacher{i}@testschool.com",
                name=f"Teacher {i}"
            )
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER
            )
        
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'Teacher', 'types': 'teacher'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data['results']), 10)  # Default limit
    
    def test_global_search_empty_query(self):
        """Test global search with empty query returns error."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'types': 'teacher'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('q', str(response.content))
    
    def test_global_search_invalid_types(self):
        """Test global search with invalid types returns error."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'test', 'types': 'invalid_type'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('types', str(response.content))
    
    def test_global_search_unauthorized(self):
        """Test that unauthenticated users cannot access endpoint."""
        self.client.force_authenticate(user=None)
        
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'test', 'types': 'teacher'})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_global_search_performance_target(self):
        """Test that API responds within 200ms performance target."""
        import time
        
        url = reverse('accounts:global-search')
        
        start_time = time.time()
        response = self.client.get(url, {'q': 'Teacher', 'types': 'teacher'})
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Performance target: <200ms for search
        response_time_ms = (end_time - start_time) * 1000
        self.assertLess(response_time_ms, 200, f"Response time {response_time_ms:.2f}ms exceeds 200ms target")
    
    def test_global_search_case_insensitive(self):
        """Test that search is case insensitive."""
        url = reverse('accounts:global-search')
        
        # Test lowercase
        response_lower = self.client.get(url, {'q': 'john', 'types': 'teacher'})
        self.assertEqual(response_lower.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_lower.json()['results']), 1)
        
        # Test uppercase  
        response_upper = self.client.get(url, {'q': 'JOHN', 'types': 'teacher'})
        self.assertEqual(response_upper.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_upper.json()['results']), 1)
        
        # Results should be the same
        self.assertEqual(
            response_lower.json()['results'][0]['title'],
            response_upper.json()['results'][0]['title']
        )
    
    def test_global_search_partial_matches(self):
        """Test that search finds partial matches."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'Jo', 'types': 'teacher'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'John Teacher')
    
    def test_global_search_no_results(self):
        """Test global search when no matches found."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'NonExistentName', 'types': 'teacher'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data['results']), 0)
        self.assertEqual(data['total_count'], 0)
    
    def test_global_search_all_types_default(self):
        """Test that search includes all types when types parameter not specified."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'Teacher'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should find the teacher user
        self.assertGreaterEqual(len(data['results']), 1)
    
    def test_global_search_response_format(self):
        """Test that search response has correct format matching frontend interface."""
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'q': 'John', 'types': 'teacher'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Check response structure matches GlobalSearchResponse interface
        self.assertIn('results', data)
        self.assertIn('total_count', data)
        self.assertIn('categories', data)
        
        # Check result item structure matches SearchResult interface
        if data['results']:
            result = data['results'][0]
            # Required fields
            self.assertIn('id', result)
            self.assertIn('type', result)
            self.assertIn('title', result)
            self.assertIn('route', result)
            
            # Optional fields
            self.assertTrue('subtitle' in result or result.get('subtitle') is None)
            self.assertTrue('avatar' in result or result.get('avatar') is None)
            self.assertTrue('metadata' in result or result.get('metadata') is None)
            
            # Validate type is one of expected values
            self.assertIn(result['type'], ['teacher', 'student', 'class', 'setting'])
            
            # Validate route is a proper path
            self.assertTrue(result['route'].startswith('/'))
            
            # Validate ID is string
            self.assertIsInstance(result['id'], str)