"""
Test teacher authentication and routing functionality.

This test verifies that teachers receive proper user_type data 
in authentication responses for correct frontend routing.
"""

import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from ..models import (
    CustomUser,
    School,
    SchoolMembership,
    SchoolRole,
    TeacherInvitation,
    TeacherProfile,
    VerificationCode,
)


class TeacherAuthenticationRoutingTest(TestCase):
    """Test cases for teacher authentication and routing."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            contact_email="admin@testschool.com"
        )
        
        # Create a school owner
        self.school_owner = CustomUser.objects.create(
            email="owner@testschool.com",
            name="School Owner",
            email_verified=True
        )
        
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
        # Create a teacher user
        self.teacher_email = "teacher@testschool.com"
        self.teacher = CustomUser.objects.create(
            email=self.teacher_email,
            name="Test Teacher",
            email_verified=True
        )
        
        # Create teacher profile
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            bio="Test teacher bio",
            specialty="Mathematics"
        )
        
        # Create teacher membership
        SchoolMembership.objects.create(
            user=self.teacher,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
    
    def test_authentication_response_includes_user_type_for_teacher(self):
        """Test that authentication response includes user_type for teachers."""
        # Create a verification code for the teacher
        verification = VerificationCode.generate_code(self.teacher_email)
        code = verification.get_current_code()
        
        # Mock the code verification to avoid time-based issues
        with patch.object(VerificationCode, 'is_valid', return_value=True):
            response = self.client.post(
                reverse('verify-code'),
                {
                    'email': self.teacher_email,
                    'code': code
                }
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that response includes user_type
        self.assertIn('user', response.data)
        user_data = response.data['user']
        
        # This should pass after the fix
        self.assertIn('user_type', user_data, 
                     "Authentication response should include user_type for frontend routing")
        self.assertEqual(user_data['user_type'], 'teacher',
                        "Teacher should have user_type='teacher' for proper routing")
    
    def test_authentication_response_includes_roles_for_teacher(self):
        """Test that authentication response includes role information."""
        # Create a verification code for the teacher
        verification = VerificationCode.generate_code(self.teacher_email)
        code = verification.get_current_code()
        
        # Mock the code verification to avoid time-based issues
        with patch.object(VerificationCode, 'is_valid', return_value=True):
            response = self.client.post(
                reverse('verify-code'),
                {
                    'email': self.teacher_email,
                    'code': code
                }
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that response includes role information
        self.assertIn('user', response.data)
        user_data = response.data['user']
        
        # Should include roles for context
        self.assertIn('roles', user_data,
                     "Authentication response should include roles for context")
        
        roles = user_data['roles']
        self.assertIsInstance(roles, list)
        self.assertGreater(len(roles), 0, "Teacher should have at least one role")
        
        # Check teacher role exists
        teacher_role_found = False
        for role in roles:
            if role['role'] == SchoolRole.TEACHER:
                teacher_role_found = True
                self.assertEqual(role['school']['id'], self.school.id)
                break
        
        self.assertTrue(teacher_role_found, "Teacher role should be present in roles")
    
    def test_authentication_response_for_school_owner(self):
        """Test that school owners get correct user_type."""
        # Create a verification code for the school owner
        verification = VerificationCode.generate_code(self.school_owner.email)
        code = verification.get_current_code()
        
        # Mock the code verification to avoid time-based issues
        with patch.object(VerificationCode, 'is_valid', return_value=True):
            response = self.client.post(
                reverse('verify-code'),
                {
                    'email': self.school_owner.email,
                    'code': code
                }
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that response includes user_type for admin/owner
        self.assertIn('user', response.data)
        user_data = response.data['user']
        
        # School owners should be routed to admin dashboard
        self.assertIn('user_type', user_data)
        self.assertEqual(user_data['user_type'], 'admin',
                        "School owner should have user_type='admin' for admin dashboard routing")
    
    def test_dashboard_info_endpoint_works_correctly(self):
        """Test that the dashboard_info endpoint correctly determines user_type."""
        # Login as teacher first
        verification = VerificationCode.generate_code(self.teacher_email)
        code = verification.get_current_code()
        
        with patch.object(VerificationCode, 'is_valid', return_value=True):
            auth_response = self.client.post(
                reverse('verify-code'),
                {
                    'email': self.teacher_email,
                    'code': code
                }
            )
        
        # Use the token to call dashboard_info
        token = auth_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        response = self.client.get(reverse('user-dashboard-info'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that dashboard_info correctly identifies teacher
        user_info = response.data['user_info']
        self.assertEqual(user_info['user_type'], 'teacher')
        
        # Check roles are present
        self.assertIn('roles', user_info)
        self.assertGreater(len(user_info['roles']), 0)
    
    def test_teacher_after_invitation_acceptance_has_correct_type(self):
        """Test that teachers who accepted invitations have correct user_type."""
        # Create a new teacher via invitation
        new_teacher_email = "newteacher@testschool.com"
        new_teacher = CustomUser.objects.create(
            email=new_teacher_email,
            name="New Teacher",
            email_verified=True
        )
        
        # Create teacher invitation
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email=new_teacher_email,
            invited_by=self.school_owner,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Accept the invitation (simulate profile creation)
        teacher_profile = TeacherProfile.objects.create(
            user=new_teacher,
            bio="New teacher bio",
            specialty="Science"
        )
        
        # Create membership as would happen during acceptance
        SchoolMembership.objects.create(
            user=new_teacher,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Mark invitation as accepted
        invitation.accept()
        
        # Now test authentication
        verification = VerificationCode.generate_code(new_teacher_email)
        code = verification.get_current_code()
        
        with patch.object(VerificationCode, 'is_valid', return_value=True):
            response = self.client.post(
                reverse('verify-code'),
                {
                    'email': new_teacher_email,
                    'code': code
                }
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the newly accepted teacher has correct user_type
        user_data = response.data['user']
        self.assertIn('user_type', user_data)
        self.assertEqual(user_data['user_type'], 'teacher',
                        "Newly accepted teacher should have user_type='teacher'")