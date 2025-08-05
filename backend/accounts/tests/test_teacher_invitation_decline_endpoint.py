"""
Tests for Teacher Invitation Decline Endpoint.

Tests cover:
- POST /api/accounts/teacher-invitations/{token}/decline/
- Authentication and permission handling
- Edge cases and error scenarios
- Activity logging and status tracking
- Consistency with accept endpoint patterns

GitHub Issue #86: Implement Teacher Invitation Decline Endpoint
"""

import uuid
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from knox.models import AuthToken

from accounts.models import (
    School,
    SchoolMembership,
    SchoolRole,
    TeacherInvitation,
    InvitationStatus,
    EmailDeliveryStatus,
    ActivityType,
    SchoolActivity,
)

User = get_user_model()


class TeacherInvitationDeclineEndpointTest(APITestCase):
    """Test cases for teacher invitation decline endpoint."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            name="Admin User"
        )
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com", 
            name="Teacher User"
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
            name="Other User"
        )
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            contact_email="contact@testschool.com"
        )
        
        # Create admin membership
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        # Create test invitation
        self.invitation = TeacherInvitation.objects.create(
            school=self.school,
            email=self.teacher_user.email,
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            custom_message="Welcome to our team!",
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Create auth tokens
        self.admin_token = AuthToken.objects.create(self.admin_user)[1]
        self.teacher_token = AuthToken.objects.create(self.teacher_user)[1]
        self.other_token = AuthToken.objects.create(self.other_user)[1]
    
    def test_decline_invitation_success(self):
        """Test successful invitation decline."""
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        # Should work without authentication (AllowAny permission)
        response = self.client.post(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('invitation', response.data)
        
        # Verify invitation was declined
        self.invitation.refresh_from_db()
        self.assertFalse(self.invitation.is_accepted)
        self.assertEqual(self.invitation.status, InvitationStatus.DECLINED)
        self.assertIsNotNone(self.invitation.declined_at)
        
        # Verify invitation is no longer valid
        self.assertFalse(self.invitation.is_valid())
    
    def test_decline_invitation_authenticated_user(self):
        """Test invitation decline by authenticated user."""
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        # Authenticate as the teacher
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.post(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('invitation', response.data)
        
        # Verify invitation was declined
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, InvitationStatus.DECLINED)
        self.assertIsNotNone(self.invitation.declined_at)
    
    def test_decline_invitation_wrong_user_authenticated(self):
        """Test that wrong authenticated user can still decline (AllowAny permission)."""
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        # Authenticate as a different user
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token}')
        
        response = self.client.post(url)
        
        # Should still work with AllowAny permission
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, InvitationStatus.DECLINED)
    
    def test_decline_invitation_invalid_token(self):
        """Test invitation decline with invalid token."""
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': 'invalid-token'})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid invitation token')
    
    def test_decline_invitation_already_declined(self):
        """Test declining an already declined invitation."""
        # Mark invitation as declined
        self.invitation.decline()
        
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already been declined', response.data['error'])
    
    def test_decline_invitation_already_accepted(self):
        """Test declining an already accepted invitation."""
        # Mark invitation as accepted
        self.invitation.accept()
        
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already been processed', response.data['error'])
    
    def test_decline_invitation_expired(self):
        """Test declining an expired invitation."""
        # Make invitation expired
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()
        
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expired', response.data['error'])
    
    def test_decline_invitation_cancelled(self):
        """Test declining a cancelled invitation."""
        # Cancel the invitation
        self.invitation.cancel()
        
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no longer valid', response.data['error'])
    
    def test_decline_response_format_consistency(self):
        """Test that decline response format is consistent with accept endpoint."""
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure matches accept endpoint pattern
        self.assertIn('message', response.data)
        self.assertIn('invitation', response.data)
        self.assertIn('status', response.data)
        
        # Verify invitation data structure
        invitation_data = response.data['invitation']
        self.assertIn('id', invitation_data)
        self.assertIn('email', invitation_data)
        self.assertIn('status', invitation_data)
        self.assertIn('declined_at', invitation_data)
        self.assertIn('school', invitation_data)
        
        # Verify school data
        school_data = invitation_data['school']
        self.assertIn('id', school_data)
        self.assertIn('name', school_data)
        
        # Verify status field
        self.assertEqual(response.data['status'], 'declined')
    
    @patch('accounts.services.metrics_service.SchoolActivityService.create_activity')
    def test_decline_invitation_creates_activity_log(self, mock_create_activity):
        """Test that declining invitation creates activity log."""
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify activity was logged
        mock_create_activity.assert_called_once()
        call_args = mock_create_activity.call_args
        self.assertEqual(call_args[1]['school'], self.invitation.school)
        self.assertEqual(call_args[1]['activity_type'], ActivityType.INVITATION_DECLINED)
        # Note: target_invitation is None because SchoolActivity expects SchoolInvitation, not TeacherInvitation
        self.assertIsNone(call_args[1]['target_invitation'])
        self.assertIn('declined', call_args[1]['description'])
    
    def test_decline_invitation_updates_status(self):
        """Test that declining invitation updates all relevant status fields."""
        original_status = self.invitation.status
        original_updated_at = self.invitation.updated_at
        
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        self.invitation.refresh_from_db()
        
        # Verify status changes
        self.assertNotEqual(self.invitation.status, original_status)
        self.assertEqual(self.invitation.status, InvitationStatus.DECLINED)
        self.assertFalse(self.invitation.is_accepted)
        self.assertIsNotNone(self.invitation.declined_at)
        self.assertGreater(self.invitation.updated_at, original_updated_at)
    
    def test_decline_invitation_idempotent(self):
        """Test that declining an already declined invitation is handled gracefully."""
        # First decline
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        response1 = self.client.post(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Get the declined_at timestamp
        self.invitation.refresh_from_db()
        first_declined_at = self.invitation.declined_at
        
        # Second decline attempt
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already been declined', response2.data['error'])
        
        # Verify declined_at timestamp didn't change
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.declined_at, first_declined_at)
    
    def test_decline_endpoint_url_pattern(self):
        """Test that the decline endpoint URL follows expected pattern."""
        expected_pattern = '/api/accounts/teacher-invitations/{}/decline/'.format(self.invitation.token)
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        # Verify URL pattern
        self.assertTrue(url.endswith('decline/'))
        self.assertIn(self.invitation.token, url)
    
    def test_decline_invitation_no_side_effects(self):
        """Test that declining invitation doesn't create unwanted side effects."""
        # Store original counts
        original_membership_count = SchoolMembership.objects.count()
        original_teacher_profile_count = User.objects.filter(teacher_profile__isnull=False).count()
        
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify no memberships or profiles were created
        self.assertEqual(SchoolMembership.objects.count(), original_membership_count)
        self.assertEqual(
            User.objects.filter(teacher_profile__isnull=False).count(), 
            original_teacher_profile_count
        )
        
        # Verify user still doesn't have teacher profile
        self.teacher_user.refresh_from_db()
        self.assertFalse(hasattr(self.teacher_user, 'teacher_profile'))
    
    def test_decline_with_custom_message_preserved(self):
        """Test that custom message is preserved in decline response."""
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify custom message is included in response
        invitation_data = response.data['invitation']
        self.assertIn('custom_message', invitation_data)
        self.assertEqual(invitation_data['custom_message'], "Welcome to our team!")


class TeacherInvitationDeclineIntegrationTest(TestCase):
    """Integration tests for teacher invitation decline functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            email="admin@integration.com",
            name="Integration Admin"
        )
        self.school = School.objects.create(name="Integration School")
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
    
    def test_decline_after_view_workflow(self):
        """Test declining invitation after viewing it."""
        from django.test import Client
        
        client = Client()
        
        # 1. Create invitation
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email='teacher@integration.com',
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # 2. Check invitation status (marks as viewed)
        status_url = reverse('accounts:teacher-invitation-status', kwargs={'token': invitation.token})
        response = client.get(status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify invitation was marked as viewed
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatus.VIEWED)
        self.assertIsNotNone(invitation.viewed_at)
        
        # 3. Decline the invitation
        decline_url = reverse('accounts:teacher-invitation-decline', kwargs={'token': invitation.token})
        response = client.post(decline_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 4. Verify final status
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatus.DECLINED)
        self.assertIsNotNone(invitation.declined_at)
        self.assertIsNotNone(invitation.viewed_at)  # Should preserve viewed_at
        
        # 5. Verify status endpoint reflects decline
        response = client.get(status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        status_data = response.json()
        self.assertTrue(status_data['invitation']['status'] == InvitationStatus.DECLINED)
        self.assertFalse(status_data['invitation']['is_valid'])
    
    def test_decline_affects_school_admin_list(self):
        """Test that declined invitations appear correctly in admin list."""
        from django.test import Client
        
        client = Client()
        admin_token = AuthToken.objects.create(self.admin_user)[1]
        
        # Create invitation
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email='teacher@integration.com',
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Decline invitation
        decline_url = reverse('accounts:teacher-invitation-decline', kwargs={'token': invitation.token})
        response = client.post(decline_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check admin list shows declined invitation
        list_url = reverse('accounts:teacher-invitation-list-for-school')
        response = client.get(
            list_url,
            HTTP_AUTHORIZATION=f'Token {admin_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        list_data = response.json()
        
        # Should find the declined invitation
        declined_invitations = [
            inv for inv in list_data['invitations'] 
            if inv['status'] == InvitationStatus.DECLINED
        ]
        self.assertEqual(len(declined_invitations), 1)
        
        # Verify summary counts
        summary = list_data['summary']
        self.assertEqual(summary['declined_invitations'], 1)
        self.assertEqual(summary['pending_invitations'], 0)