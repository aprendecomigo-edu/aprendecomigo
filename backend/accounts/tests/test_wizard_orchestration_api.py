"""
Tests for the Teacher Profile Wizard Orchestration API.

GitHub Issue #95: Backend wizard orchestration API for guided profile creation.

Test Coverage:
- Enhanced invitation acceptance with wizard metadata
- Step-by-step validation endpoints  
- Profile completion progress tracking
- School billing policy integration
- Backward compatibility with existing invitation flow
"""

import json
import uuid
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import (
    School,
    SchoolSettings,
    SchoolRole,
    TeacherInvitation,
    TeacherProfile,
    SchoolMembership,
    CustomUser
)

User = get_user_model()


class WizardOrchestrationAPITestCase(TestCase):
    """Base test case for wizard orchestration API tests."""
    
    def setUp(self):
        """Set up test data."""  
        self.client = APIClient()
        
        # Create test school with settings
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            contact_email="admin@testschool.com"
        )
        
        self.school_settings = SchoolSettings.objects.create(
            school=self.school,
            currency_code="EUR",
            working_hours_start="08:00",
            working_hours_end="18:00"
        )
        
        # Create school owner
        self.school_owner = User.objects.create_user(
            email="owner@testschool.com",
            name="School Owner",
        )
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        
        # Create invited teacher user (but no profile yet)
        self.invited_teacher = User.objects.create_user(
            email="teacher@example.com",
            name="Test Teacher"
        )
        
        # Create valid teacher invitation
        self.invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timezone.timedelta(days=7),
            custom_message="Welcome to our school!",
            batch_id=uuid.uuid4()
        )


class EnhancedInvitationAcceptanceTests(WizardOrchestrationAPITestCase):
    """Tests for enhanced invitation acceptance with wizard metadata."""
    
    def test_invitation_acceptance_returns_wizard_metadata(self):
        """Test that invitation acceptance returns wizard metadata for guided profile creation."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        data = {
            "bio": "I am a passionate teacher",
            "specialty": "Mathematics",
            "hourly_rate": "25.00"
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('success', response.data)
        self.assertIn('invitation_accepted', response.data)
        self.assertIn('teacher_profile', response.data)
        self.assertIn('wizard_metadata', response.data)
        
        # Check wizard metadata structure
        wizard_metadata = response.data['wizard_metadata']
        self.assertIn('steps', wizard_metadata)
        self.assertIn('current_step', wizard_metadata)
        self.assertIn('completion_status', wizard_metadata)
        self.assertIn('school_policies', wizard_metadata)
        
        # Verify invitation was accepted
        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.is_accepted)
        
        # Verify teacher profile was created
        self.assertTrue(hasattr(self.invited_teacher, 'teacher_profile'))
        teacher_profile = self.invited_teacher.teacher_profile
        self.assertEqual(teacher_profile.bio, "I am a passionate teacher")
        self.assertEqual(teacher_profile.specialty, "Mathematics")
        self.assertEqual(teacher_profile.hourly_rate, Decimal("25.00"))
    
    def test_wizard_steps_structure(self):
        """Test that wizard steps are properly structured."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        steps = response.data['wizard_metadata']['steps']
        self.assertIsInstance(steps, list)
        self.assertGreater(len(steps), 0)
        
        # Each step should have required fields
        for step in steps:
            self.assertIn('step_number', step)
            self.assertIn('title', step)
            self.assertIn('description', step)
            self.assertIn('fields', step)
            self.assertIn('is_required', step)
    
    def test_completion_status_tracking(self):
        """Test that completion status is properly tracked."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        data = {
            "bio": "I am a teacher",
            "specialty": "Mathematics",
            "teaching_subjects": ["math", "algebra"]
        }
        
        response = self.client.post(url, data, format='json')
        
        completion_status = response.data['wizard_metadata']['completion_status']
        
        self.assertIn('completion_percentage', completion_status)
        self.assertIn('missing_critical', completion_status)
        self.assertIn('missing_optional', completion_status)
        self.assertIn('is_complete', completion_status)
        self.assertIn('scores_breakdown', completion_status)
        
        # Verify completion percentage is calculated
        self.assertIsInstance(completion_status['completion_percentage'], float)
        self.assertGreaterEqual(completion_status['completion_percentage'], 0.0)
        self.assertLessEqual(completion_status['completion_percentage'], 100.0)
    
    def test_school_policies_included(self):
        """Test that school billing policies are included in wizard metadata."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        response = self.client.post(url, {}, format='json')
        
        school_policies = response.data['wizard_metadata']['school_policies']
        
        self.assertIn('currency_code', school_policies)
        self.assertIn('rate_constraints', school_policies)
        self.assertIn('working_hours', school_policies)
        
        # Verify school-specific data
        self.assertEqual(school_policies['currency_code'], 'EUR')
        self.assertIn('start', school_policies['working_hours'])
        self.assertIn('end', school_policies['working_hours'])
    
    def test_backward_compatibility_simple_acceptance(self):
        """Test that simple invitation acceptance still works (backward compatibility)."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        # Send minimal data like before
        data = {"bio": "Simple bio"}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should still create teacher profile
        self.assertTrue(hasattr(self.invited_teacher, 'teacher_profile'))
        
        # Should still return success (but now with wizard metadata)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['invitation_accepted'])


class StepValidationEndpointTests(WizardOrchestrationAPITestCase):
    """Tests for step-by-step validation endpoints."""
    
    def setUp(self):
        """Set up test data with teacher profile."""
        super().setUp()
        # Create teacher profile for step validation
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.invited_teacher,
            bio="Basic bio"
        )
        self.client.force_authenticate(user=self.invited_teacher)
    
    def test_validate_step_endpoint_exists(self):
        """Test that step validation endpoint exists and is accessible."""
        url = "/api/accounts/teacher-profile/validate-step/"
        data = {
            "step": 1,
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com"
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should not return 404 (endpoint exists)
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Should return either success or validation error
        self.assertIn(response.status_code, [
            status.HTTP_200_OK, 
            status.HTTP_400_BAD_REQUEST
        ])
    
    def test_validate_step_valid_data(self):
        """Test step validation with valid data."""
        url = "/api/accounts/teacher-profile/validate-step/"
        data = {
            "step": 1,
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "professional_bio": "I am an experienced teacher"
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_valid', response.data)
        self.assertTrue(response.data['is_valid'])
        self.assertIn('validated_data', response.data)
    
    def test_validate_step_invalid_data(self):
        """Test step validation with invalid data."""
        url = "/api/accounts/teacher-profile/validate-step/"
        data = {
            "step": 1,
            "data": {
                "first_name": "",  # Invalid: empty
                "last_name": "Doe",
                "email": "invalid-email"  # Invalid: bad format
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is_valid', response.data)
        self.assertFalse(response.data['is_valid'])
        self.assertIn('errors', response.data)
        self.assertIn('first_name', response.data['errors'])
        self.assertIn('email', response.data['errors'])
    
    def test_validate_step_security_validation(self):
        """Test that step validation includes security checks."""
        url = "/api/accounts/teacher-profile/validate-step/"
        data = {
            "step": 1,
            "data": {
                "first_name": "<script>alert('xss')</script>",
                "last_name": "Doe",
                "email": "test@example.com"
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('first_name', response.data['errors'])


class ProfileCompletionTrackingTests(WizardOrchestrationAPITestCase):
    """Tests for profile completion progress tracking."""
    
    def setUp(self):
        """Set up test data with teacher profile."""
        super().setUp()
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.invited_teacher,
            bio="Basic bio",
            specialty="Mathematics"
        )
        self.client.force_authenticate(user=self.invited_teacher)
    
    def test_completion_status_endpoint_exists(self):
        """Test that completion status endpoint exists."""
        url = "/api/accounts/teacher-profile/completion-status/"
        
        response = self.client.get(url)
        
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_completion_status_structure(self):
        """Test that completion status returns proper structure."""
        url = "/api/accounts/teacher-profile/completion-status/"
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required fields
        self.assertIn('completion_percentage', response.data)
        self.assertIn('missing_critical', response.data)
        self.assertIn('missing_optional', response.data)
        self.assertIn('is_complete', response.data)
        self.assertIn('scores_breakdown', response.data)
        self.assertIn('recommendations', response.data)
    
    def test_completion_percentage_calculation(self):
        """Test that completion percentage is calculated correctly."""
        url = "/api/accounts/teacher-profile/completion-status/"
        
        response = self.client.get(url)
        
        completion_percentage = response.data['completion_percentage']
        
        self.assertIsInstance(completion_percentage, float)
        self.assertGreaterEqual(completion_percentage, 0.0)
        self.assertLessEqual(completion_percentage, 100.0)
        
        # Since we have minimal profile data, should not be 100%
        self.assertLess(completion_percentage, 100.0)
    
    def test_completion_improvements_after_updates(self):
        """Test that completion percentage improves after profile updates."""
        url = "/api/accounts/teacher-profile/completion-status/"
        
        # Get initial completion
        response1 = self.client.get(url)
        initial_completion = response1.data['completion_percentage']
        
        # Update profile with more data
        self.teacher_profile.hourly_rate = Decimal("30.00")
        self.teacher_profile.teaching_subjects = ["mathematics", "algebra", "geometry"]
        self.teacher_profile.education_background = {
            "degree": "Master's in Mathematics",
            "institution": "University of Test"
        }
        self.teacher_profile.save()
        
        # Get updated completion
        response2 = self.client.get(url)
        updated_completion = response2.data['completion_percentage']
        
        # Should have improved
        self.assertGreater(updated_completion, initial_completion)


class SchoolPolicyIntegrationTests(WizardOrchestrationAPITestCase):
    """Tests for school billing policy integration."""
    
    def test_rate_constraints_from_school_settings(self):
        """Test that rate constraints are derived from school settings."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        response = self.client.post(url, {}, format='json')
        
        school_policies = response.data['wizard_metadata']['school_policies']
        rate_constraints = school_policies['rate_constraints']
        
        self.assertIn('currency', rate_constraints)
        self.assertEqual(rate_constraints['currency'], 'EUR')
        
        # Should include reasonable defaults or school-specific constraints
        self.assertIn('min_rate', rate_constraints)
        self.assertIn('max_rate', rate_constraints)
        self.assertIn('suggested_range', rate_constraints)
    
    def test_working_hours_from_school_settings(self):
        """Test that working hours are included from school settings."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        response = self.client.post(url, {}, format='json')
        
        school_policies = response.data['wizard_metadata']['school_policies']
        working_hours = school_policies['working_hours']
        
        self.assertEqual(working_hours['start'], '08:00')
        self.assertEqual(working_hours['end'], '18:00')
    
    def test_rate_validation_against_school_policies(self):
        """Test that rates are validated against school policies."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        # Try to set rate that's too high (assuming reasonable max of 100 EUR/hr)
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        data = {
            "hourly_rate": "500.00"  # Unreasonably high
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should either accept with warning or reject
        # Depending on implementation, both are acceptable
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('hourly_rate', str(response.data).lower())
        else:
            # If accepted, should include warning in wizard metadata
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class BackwardCompatibilityTests(WizardOrchestrationAPITestCase):
    """Tests to ensure backward compatibility with existing invitation flow."""
    
    def test_existing_clients_still_work(self):
        """Test that existing API clients continue to work without modification."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        # Use old-style API call (minimal data)
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        data = {
            "bio": "I am a teacher",
            "course_ids": []  # Old field that should still work
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should create teacher profile
        self.assertTrue(hasattr(self.invited_teacher, 'teacher_profile'))
        
        # Should accept invitation
        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.is_accepted)
    
    def test_response_includes_legacy_fields(self):
        """Test that response includes fields expected by existing clients."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        response = self.client.post(url, {}, format='json')
        
        # Should include legacy response fields
        self.assertIn('success', response.data)
        self.assertIn('invitation_accepted', response.data)
        self.assertIn('teacher_profile', response.data)
        
        # But also include new wizard metadata
        self.assertIn('wizard_metadata', response.data)
    
    def test_empty_request_body_handled(self):
        """Test that empty request body is handled gracefully."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        
        # Send empty body (like some existing clients might)
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should create minimal teacher profile
        self.assertTrue(hasattr(self.invited_teacher, 'teacher_profile'))
        
        # Should still provide wizard metadata for potential UI enhancement
        self.assertIn('wizard_metadata', response.data)


class ErrorHandlingTests(WizardOrchestrationAPITestCase):
    """Tests for comprehensive error handling in wizard orchestration."""
    
    def test_invalid_invitation_token(self):
        """Test handling of invalid invitation tokens."""
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = "/api/accounts/teacher-invitations/invalid-token/accept/"
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_expired_invitation(self):
        """Test handling of expired invitations."""
        # Make invitation expired
        self.invitation.expires_at = timezone.now() - timezone.timedelta(days=1)
        self.invitation.save()
        
        self.client.force_authenticate(user=self.invited_teacher)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expired', response.data['error']['message'].lower())
    
    def test_unauthorized_access(self):
        """Test handling of unauthorized access attempts."""
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_wrong_user_email(self):
        """Test handling when authenticated user email doesn't match invitation."""
        # Create different user
        other_user = User.objects.create_user(
            email="other@example.com",
            name="Other User"
        )
        
        self.client.force_authenticate(user=other_user)
        
        url = f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/"
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('not for your account', response.data['error']['message'])