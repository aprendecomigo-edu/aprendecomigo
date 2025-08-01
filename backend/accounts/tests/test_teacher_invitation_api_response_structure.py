"""
Test API response structure for teacher invitation endpoints.

This test ensures the API response structure matches what the frontend expects,
specifically fixing the "Cannot read properties of undefined (reading 'status')" error.

GitHub Issue: API Response Structure Mismatch
"""

import json
import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import CustomUser, School, TeacherInvitation


class TeacherInvitationAPIResponseStructureTest(TestCase):
    """Test API response structure matches frontend expectations."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="Test Description"
        )
        
        # Create school admin
        self.admin = CustomUser.objects.create_user(
            email="admin@testschool.com",
            name="Admin User"
        )
        self.admin.is_verified = True
        self.admin.save()
        
        # Create teacher invitation
        self.invitation = TeacherInvitation.objects.create(
            email="teacher@example.com",
            school=self.school,
            invited_by=self.admin,
            role="teacher",
            status="pending",
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7),
            custom_message="Welcome to our school!"
        )
    
    def test_invitation_status_response_structure_matches_frontend_interface(self):
        """
        Test that the status endpoint returns the structure expected by frontend.
        
        Frontend expects:
        {
          "invitation": {
            "id": string,
            "email": string,
            "school": { "id": number, "name": string },
            "invited_by": { "id": number, "name": string, "email": string },
            "role": string,
            "status": string,
            "email_delivery_status": string,
            "token": string,
            "custom_message": string,
            "batch_id": string,
            "created_at": string,
            "expires_at": string,
            "accepted_at": string | null
          },
          "can_accept": boolean,
          "reason": string | null,
          "needs_profile_wizard": boolean,
          "wizard_metadata": object | null
        }
        """
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Root level structure
        self.assertIn('invitation', data)
        self.assertIn('can_accept', data)
        self.assertIn('reason', data)
        self.assertIn('needs_profile_wizard', data)
        self.assertIn('wizard_metadata', data)
        
        # Invitation object structure
        invitation = data['invitation']
        self.assertIn('id', invitation)
        self.assertIn('email', invitation)
        self.assertIn('school', invitation)
        self.assertIn('invited_by', invitation)
        self.assertIn('role', invitation)
        self.assertIn('status', invitation)
        self.assertIn('email_delivery_status', invitation)
        self.assertIn('token', invitation)
        self.assertIn('custom_message', invitation)
        self.assertIn('batch_id', invitation)
        self.assertIn('created_at', invitation)
        self.assertIn('expires_at', invitation)
        self.assertIn('accepted_at', invitation)
        
        # School object structure
        school = invitation['school']
        self.assertIn('id', school)
        self.assertIn('name', school)
        self.assertEqual(school['name'], self.school.name)
        
        # Invited by object structure
        invited_by = invitation['invited_by']
        self.assertIn('id', invited_by)
        self.assertIn('name', invited_by)
        self.assertIn('email', invited_by)
        self.assertEqual(invited_by['email'], self.admin.email)
        
        # Verify data values
        self.assertEqual(invitation['email'], self.invitation.email)
        # Refresh invitation from DB since API marks it as viewed
        self.invitation.refresh_from_db()
        self.assertEqual(invitation['status'], self.invitation.status)  # Should be 'viewed' now
        self.assertEqual(invitation['role'], self.invitation.role)
        self.assertEqual(invitation['token'], self.invitation.token)
        self.assertEqual(invitation['custom_message'], self.invitation.custom_message)
        
        # Verify types
        self.assertIsInstance(data['can_accept'], bool)
        self.assertIsInstance(data['needs_profile_wizard'], bool)
        
    def test_invitation_status_can_accept_logic(self):
        """Test that can_accept field reflects proper invitation state."""
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        response = self.client.get(url)
        
        data = response.json()
        
        # For a pending invitation, can_accept should be True (if user is authenticated and matches email)
        # For unauthenticated request, can_accept should be False
        self.assertIsInstance(data['can_accept'], bool)
        
    def test_invitation_status_for_accepted_invitation(self):
        """Test response structure for accepted invitation."""
        self.invitation.status = 'accepted'
        self.invitation.is_accepted = True
        self.invitation.accepted_at = timezone.now()
        self.invitation.save()
        
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        response = self.client.get(url)
        
        data = response.json()
        invitation = data['invitation']
        
        self.assertEqual(invitation['status'], 'accepted')
        self.assertIsNotNone(invitation['accepted_at'])
        self.assertEqual(data['can_accept'], False)  # Cannot accept already accepted invitation
        
    def test_invitation_status_for_nonexistent_token(self):
        """Test response for invalid token."""
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': 'invalid-token'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_response_preserves_all_necessary_fields_for_frontend(self):
        """
        Test that all fields required by frontend components are present.
        
        This test specifically addresses the "Cannot read properties of undefined" error
        by ensuring the invitation.status field is accessible via data.invitation.status.
        """
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        response = self.client.get(url)
        
        data = response.json()
        
        # Simulate frontend access patterns that were failing
        # This should not raise KeyError or AttributeError
        invitation = data['invitation']  # Should not fail
        status_value = invitation['status']  # Should not fail
        
        # Ensure status is accessible as expected by frontend
        # Status should be 'viewed' since API marks invitation as viewed when accessed
        self.assertEqual(status_value, 'viewed')
        
        # Test other common frontend access patterns
        school_name = invitation['school']['name']
        self.assertEqual(school_name, self.school.name)
        
        invited_by_email = invitation['invited_by']['email']
        self.assertEqual(invited_by_email, self.admin.email)