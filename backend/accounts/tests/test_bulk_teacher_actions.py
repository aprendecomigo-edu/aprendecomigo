"""
Tests for BulkTeacherActionsView.
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


class BulkTeacherActionsViewTestCase(TestCase):
    """Test cases for BulkTeacherActionsView"""
    
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
        
        # Create teacher users and profiles
        self.teachers = []
        for i in range(5):
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
            
            profile = TeacherProfile.objects.create(
                user=user,
                bio=f"Bio for teacher {i}",
                specialty=f"Subject {i}",
                hourly_rate=Decimal('25.00') if i % 2 == 0 else None
            )
            
            self.teachers.append(profile)
        
        # Create another school with different teachers (for permission testing)
        self.other_school = School.objects.create(
            name="Other School"
        )
        
        self.other_teacher_user = User.objects.create_user(
            email="other.teacher@test.com",
            name="Other Teacher"
        )
        
        SchoolMembership.objects.create(
            user=self.other_teacher_user,
            school=self.other_school,
            role=SchoolRole.TEACHER
        )
        
        self.other_teacher_profile = TeacherProfile.objects.create(
            user=self.other_teacher_user,
            bio="Other teacher bio"
        )
        
        # Set up API client
        self.client = APIClient()
        self.url = reverse('accounts:bulk-teacher-actions')
    
    def test_bulk_update_status_success(self):
        """Test successful bulk status update"""
        self.client.force_authenticate(user=self.admin_user)
        
        teacher_ids = [t.id for t in self.teachers[:3]]
        
        data = {
            'action': 'update_status',
            'teacher_ids': teacher_ids,
            'parameters': {
                'is_active': False
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('successful_count', response.data)
        self.assertIn('failed_count', response.data)
        self.assertIn('results', response.data)
        
        # Should have processed 3 teachers successfully
        self.assertEqual(response.data['successful_count'], 3)
        self.assertEqual(response.data['failed_count'], 0)
        
        # Check that memberships were deactivated
        for teacher_id in teacher_ids:
            teacher = TeacherProfile.objects.get(id=teacher_id)
            membership = SchoolMembership.objects.get(
                user=teacher.user,
                school=self.school,
                role=SchoolRole.TEACHER
            )
            self.assertFalse(membership.is_active)
    
    def test_bulk_send_message_success(self):
        """Test successful bulk message sending"""
        self.client.force_authenticate(user=self.admin_user)
        
        teacher_ids = [t.id for t in self.teachers[:2]]
        
        data = {
            'action': 'send_message',
            'teacher_ids': teacher_ids,
            'parameters': {
                'message': 'Please update your profile information.',
                'subject': 'Profile Update Request'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['successful_count'], 2)
        self.assertEqual(response.data['failed_count'], 0)
    
    def test_bulk_export_data_success(self):
        """Test successful bulk data export"""
        self.client.force_authenticate(user=self.admin_user)
        
        teacher_ids = [t.id for t in self.teachers]
        
        data = {
            'action': 'export_data',
            'teacher_ids': teacher_ids,
            'parameters': {
                'format': 'csv',
                'fields': ['name', 'email', 'bio', 'hourly_rate', 'profile_completion_score']
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('export_url', response.data)
        self.assertIn('file_size', response.data)
        self.assertEqual(response.data['successful_count'], 5)
    
    def test_bulk_actions_max_limit(self):
        """Test that bulk actions respect the 50 teacher limit"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Try to update 51 teachers (should fail)
        teacher_ids = list(range(1, 52))  # 51 IDs
        
        data = {
            'action': 'update_status',
            'teacher_ids': teacher_ids,
            'parameters': {'is_active': False}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Maximum 50 teachers allowed', str(response.data))
    
    def test_bulk_actions_cross_school_permission(self):
        """Test that admin cannot perform bulk actions on teachers from other schools"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Try to update teacher from another school
        teacher_ids = [self.other_teacher_profile.id]
        
        data = {
            'action': 'update_status',
            'teacher_ids': teacher_ids,
            'parameters': {'is_active': False}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have 0 successful and 1 failed (permission denied)
        self.assertEqual(response.data['successful_count'], 0)
        self.assertEqual(response.data['failed_count'], 1)
        
        # Check error details
        failed_result = response.data['results'][0]
        self.assertEqual(failed_result['status'], 'failed')
        self.assertIn('permission', failed_result['error'].lower())
    
    def test_bulk_actions_partial_failure(self):
        """Test bulk actions with partial failures"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Mix valid and invalid teacher IDs
        valid_teacher_ids = [t.id for t in self.teachers[:2]]
        invalid_teacher_ids = [9999, 9998]  # Non-existent IDs
        teacher_ids = valid_teacher_ids + invalid_teacher_ids
        
        data = {
            'action': 'update_status',
            'teacher_ids': teacher_ids,
            'parameters': {'is_active': False}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['successful_count'], 2)
        self.assertEqual(response.data['failed_count'], 2)
        
        # Check that we have detailed results for both success and failure
        results = response.data['results']
        successful_results = [r for r in results if r['status'] == 'success']
        failed_results = [r for r in results if r['status'] == 'failed']
        
        self.assertEqual(len(successful_results), 2)
        self.assertEqual(len(failed_results), 2)
    
    def test_bulk_actions_invalid_action(self):
        """Test handling of invalid action type"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'action': 'invalid_action',
            'teacher_ids': [self.teachers[0].id],
            'parameters': {}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_bulk_actions_unauthenticated(self):
        """Test that unauthenticated users cannot access bulk actions"""
        data = {
            'action': 'update_status',
            'teacher_ids': [self.teachers[0].id],
            'parameters': {'is_active': False}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_bulk_actions_unauthorized_user(self):
        """Test that non-admin users cannot perform bulk actions"""
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
        
        data = {
            'action': 'update_status',
            'teacher_ids': [self.teachers[0].id],
            'parameters': {'is_active': False}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_bulk_update_with_completion_recalculation(self):
        """Test that bulk updates trigger profile completion recalculation"""
        self.client.force_authenticate(user=self.admin_user)
        
        teacher_ids = [self.teachers[0].id]
        
        data = {
            'action': 'update_profile',
            'teacher_ids': teacher_ids,
            'parameters': {
                'bio': 'Updated comprehensive biography with extensive details about teaching experience and qualifications.',
                'hourly_rate': '35.00'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['successful_count'], 1)
        
        # Check that profile was updated and completion score recalculated
        teacher = TeacherProfile.objects.get(id=self.teachers[0].id)
        self.assertEqual(teacher.bio, data['parameters']['bio'])
        self.assertEqual(teacher.hourly_rate, Decimal('35.00'))
        # Completion score should have been updated
        self.assertGreater(teacher.profile_completion_score, 0)
    
    def test_bulk_actions_performance(self):
        """Test that bulk actions perform efficiently"""
        # Create more teachers for performance testing
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
                bio=f"Performance bio {i}"
            )
            additional_teachers.append(profile)
        
        self.client.force_authenticate(user=self.admin_user)
        
        teacher_ids = [t.id for t in additional_teachers]
        
        import time
        start_time = time.time()
        
        data = {
            'action': 'update_status',
            'teacher_ids': teacher_ids,
            'parameters': {'is_active': False}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['successful_count'], 20)
        
        # Should complete within 2 seconds as per requirements
        self.assertLess(execution_time, 2.0)
    
    def test_bulk_actions_detailed_error_reporting(self):
        """Test detailed error reporting for failed operations"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create a scenario with various types of failures
        data = {
            'action': 'update_profile',
            'teacher_ids': [
                self.teachers[0].id,  # Valid
                9999,  # Non-existent
                self.other_teacher_profile.id  # No permission
            ],
            'parameters': {
                'hourly_rate': 'invalid_rate'  # Invalid data
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check detailed error reporting
        results = response.data['results']
        self.assertEqual(len(results), 3)
        
        # Each result should have teacher_id, status, and error (for failures)
        for result in results:
            self.assertIn('teacher_id', result)
            self.assertIn('status', result)
            if result['status'] == 'failed':
                self.assertIn('error', result)
                # Error should be descriptive
                self.assertGreater(len(result['error']), 10)
    
    def test_bulk_message_template_support(self):
        """Test bulk messaging with template support"""
        self.client.force_authenticate(user=self.admin_user)
        
        teacher_ids = [t.id for t in self.teachers[:2]]
        
        data = {
            'action': 'send_message',
            'teacher_ids': teacher_ids,
            'parameters': {
                'template': 'profile_completion_reminder',
                'template_variables': {
                    'completion_threshold': 80,
                    'deadline': '2024-01-31'
                }
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['successful_count'], 2)
        
        # Should include information about template used
        self.assertIn('template_used', response.data)
        self.assertEqual(response.data['template_used'], 'profile_completion_reminder')