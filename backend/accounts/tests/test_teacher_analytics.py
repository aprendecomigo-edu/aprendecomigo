"""
Tests for TeacherAnalyticsView.
Following TDD methodology - tests are written first.
"""
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from accounts.models import (
    School, 
    SchoolMembership, 
    SchoolRole, 
    TeacherProfile,
    Course,
    EducationalSystem,
    TeacherCourse
)

User = get_user_model()


class TeacherAnalyticsViewTestCase(TestCase):
    """Test cases for TeacherAnalyticsView"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            name="Test Admin"
        )
        
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        # Make admin user a school admin
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Get or create educational system
        self.edu_system, created = EducationalSystem.objects.get_or_create(
            code="pt",
            defaults={
                "name": "Portugal"
            }
        )
        
        # Create courses
        self.course1 = Course.objects.create(
            name="Mathematics",
            code="MAT",
            educational_system=self.edu_system,
            education_level="ensino_basico_1_ciclo"
        )
        
        self.course2 = Course.objects.create(
            name="Physics",
            code="PHY",
            educational_system=self.edu_system,
            education_level="ensino_secundario"
        )
        
        self.course3 = Course.objects.create(
            name="Chemistry",
            code="CHE",
            educational_system=self.edu_system,
            education_level="ensino_secundario"
        )
        
        # Create teachers with different profile completion levels
        self.teachers = []
        for i in range(6):
            user = User.objects.create_user(
                email=f"teacher{i}@test.com",
                name=f"Teacher {i}",
                phone_number=f"+35112345678{i}"
            )
            
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER
            )
            
            # Create profiles with varying completion levels
            profile_data = {
                'user': user,
                'bio': f'Detailed bio for teacher {i}' if i < 4 else '',
                'specialty': f'Subject {i}' if i < 3 else '',
                'education': f'Education background {i}' if i < 5 else '',
                'hourly_rate': Decimal('25.00') if i < 4 else None,
                'availability': f'Monday to Friday {i}' if i < 2 else '',
                'teaching_subjects': [f'Subject{i}', f'Subject{i+1}'] if i < 3 else [],
                'profile_completion_score': [95.0, 80.0, 65.0, 50.0, 30.0, 10.0][i],
                'is_profile_complete': i < 2
            }
            
            profile = TeacherProfile.objects.create(**profile_data)
            self.teachers.append(profile)
            
            # Add courses to some teachers
            if i < 4:
                TeacherCourse.objects.create(
                    teacher=profile,
                    course=self.course1 if i % 2 == 0 else self.course2,
                    hourly_rate=Decimal('25.00')
                )
                
                if i < 2:  # Teachers with multiple courses
                    TeacherCourse.objects.create(
                        teacher=profile,
                        course=self.course3,
                        hourly_rate=Decimal('30.00')
                    )
        
        # Create another school for permission testing
        self.other_school = School.objects.create(
            name="Other School"
        )
        
        # Set up API client
        self.client = APIClient()
        self.url = reverse('accounts:teacher-analytics', kwargs={'school_id': self.school.id})
    
    def test_get_teacher_analytics_success(self):
        """Test successful teacher analytics retrieval"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('profile_completion_stats', response.data)
        self.assertIn('subject_coverage', response.data)
        self.assertIn('teacher_activity', response.data)
        self.assertIn('completion_distribution', response.data)
        
        # Check profile completion stats
        completion_stats = response.data['profile_completion_stats']
        self.assertIn('total_teachers', completion_stats)
        self.assertIn('average_completion', completion_stats)
        self.assertIn('complete_profiles', completion_stats)
        self.assertIn('incomplete_profiles', completion_stats)
        
        self.assertEqual(completion_stats['total_teachers'], 6)
        self.assertEqual(completion_stats['complete_profiles'], 2)
        self.assertEqual(completion_stats['incomplete_profiles'], 4)
        self.assertGreater(completion_stats['average_completion'], 0)
    
    def test_subject_coverage_analysis(self):
        """Test subject coverage analysis"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subject_coverage = response.data['subject_coverage']
        self.assertIn('total_subjects', subject_coverage)
        self.assertIn('covered_subjects', subject_coverage)
        self.assertIn('uncovered_subjects', subject_coverage)
        self.assertIn('subject_details', subject_coverage)
        
        # Should have coverage for Mathematics and Physics (from setup)
        self.assertGreater(subject_coverage['covered_subjects'], 0)
        
        # Check subject details structure
        for subject_detail in subject_coverage['subject_details']:
            self.assertIn('subject_name', subject_detail)
            self.assertIn('teacher_count', subject_detail)
            self.assertIn('education_level', subject_detail)
    
    def test_teacher_activity_metrics(self):
        """Test teacher activity metrics"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        activity_metrics = response.data['teacher_activity']
        self.assertIn('active_teachers', activity_metrics)
        self.assertIn('inactive_teachers', activity_metrics)
        self.assertIn('recently_updated_profiles', activity_metrics)
        self.assertIn('needs_attention', activity_metrics)
        
        # All teachers should be counted
        total_activity = activity_metrics['active_teachers'] + activity_metrics['inactive_teachers']
        self.assertEqual(total_activity, 6)
    
    def test_completion_distribution_analysis(self):
        """Test completion distribution analysis"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        distribution = response.data['completion_distribution']
        self.assertIn('0-25%', distribution)
        self.assertIn('26-50%', distribution)
        self.assertIn('51-75%', distribution)
        self.assertIn('76-100%', distribution)
        
        # Verify distribution adds up to total teachers
        total_distributed = sum(distribution.values())
        self.assertEqual(total_distributed, 6)
        
        # Based on our test data:
        # Teacher 0: 95% (76-100%)
        # Teacher 1: 80% (76-100%)
        # Teacher 2: 65% (51-75%)
        # Teacher 3: 50% (26-50%)
        # Teacher 4: 30% (26-50%)
        # Teacher 5: 10% (0-25%)
        self.assertEqual(distribution['76-100%'], 2)
        self.assertEqual(distribution['51-75%'], 1)
        self.assertEqual(distribution['26-50%'], 2)
        self.assertEqual(distribution['0-25%'], 1)
    
    def test_analytics_with_filters(self):
        """Test analytics with optional filters"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test with completion filter
        response = self.client.get(self.url, {'min_completion': 60})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include teachers with >= 60% completion (3 teachers)
        completion_stats = response.data['profile_completion_stats']
        self.assertLessEqual(completion_stats['total_teachers'], 3)
    
    def test_analytics_unauthorized_access(self):
        """Test that non-admin users cannot access analytics"""
        # Create a regular teacher user
        teacher_user = User.objects.create_user(
            email="regular.teacher@test.com",
            name="Regular Teacher"
        )
        
        SchoolMembership.objects.create(
            user=teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        self.client.force_authenticate(user=teacher_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_analytics_cross_school_permission(self):
        """Test that admin cannot access analytics for other schools"""
        self.client.force_authenticate(user=self.admin_user)
        
        other_school_url = reverse('accounts:teacher-analytics', kwargs={'school_id': self.other_school.id})
        response = self.client.get(other_school_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_analytics_unauthenticated(self):
        """Test that unauthenticated users cannot access analytics"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_analytics_nonexistent_school(self):
        """Test analytics for non-existent school"""
        self.client.force_authenticate(user=self.admin_user)
        
        nonexistent_url = reverse('accounts:teacher-analytics', kwargs={'school_id': 9999})
        response = self.client.get(nonexistent_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_analytics_empty_school(self):
        """Test analytics for school with no teachers"""
        # Create empty school and make admin manage it
        empty_school = School.objects.create(name="Empty School")
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=empty_school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        empty_school_url = reverse('accounts:teacher-analytics', kwargs={'school_id': empty_school.id})
        response = self.client.get(empty_school_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return zero values
        completion_stats = response.data['profile_completion_stats']
        self.assertEqual(completion_stats['total_teachers'], 0)
        self.assertEqual(completion_stats['average_completion'], 0.0)
    
    def test_analytics_performance(self):
        """Test that analytics perform efficiently with more data"""
        # Create additional teachers for performance testing
        additional_teachers = []
        for i in range(20):
            user = User.objects.create_user(
                email=f"perf.teacher{i}@test.com",
                name=f"Performance Teacher {i}"
            )
            
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER
            )
            
            profile = TeacherProfile.objects.create(
                user=user,
                bio=f"Performance bio {i}",
                profile_completion_score=50.0
            )
            additional_teachers.append(profile)
        
        self.client.force_authenticate(user=self.admin_user)
        
        import time
        start_time = time.time()
        
        response = self.client.get(self.url)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should complete within 1 second
        self.assertLess(execution_time, 1.0)
        
        # Should now have 26 total teachers (6 original + 20 additional)
        completion_stats = response.data['profile_completion_stats']
        self.assertEqual(completion_stats['total_teachers'], 26)
    
    def test_analytics_common_missing_fields(self):
        """Test identification of common missing fields"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include common missing fields analysis
        self.assertIn('common_missing_fields', response.data)
        
        missing_fields = response.data['common_missing_fields']
        self.assertIsInstance(missing_fields, list)
        
        # Each missing field should have field name, count, and percentage
        for field_info in missing_fields:
            self.assertIn('field', field_info)
            self.assertIn('count', field_info)
            self.assertIn('percentage', field_info)
    
    def test_analytics_recommendations(self):
        """Test that analytics include actionable recommendations"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include recommendations
        self.assertIn('recommendations', response.data)
        
        recommendations = response.data['recommendations']
        self.assertIsInstance(recommendations, list)
        
        # Each recommendation should have text and priority
        for recommendation in recommendations:
            self.assertIn('text', recommendation)
            self.assertIn('priority', recommendation)
            self.assertIn(recommendation['priority'], ['high', 'medium', 'low'])
    
    def test_analytics_export_data(self):
        """Test analytics data suitable for export"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {'include_export_data': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include detailed export data
        self.assertIn('teacher_details', response.data)
        
        teacher_details = response.data['teacher_details']
        self.assertEqual(len(teacher_details), 6)  # All teachers
        
        # Each teacher detail should have necessary fields
        for teacher in teacher_details:
            self.assertIn('id', teacher)
            self.assertIn('name', teacher)
            self.assertIn('email', teacher)
            self.assertIn('completion_percentage', teacher)
            self.assertIn('missing_fields_count', teacher)
            self.assertIn('courses_count', teacher)