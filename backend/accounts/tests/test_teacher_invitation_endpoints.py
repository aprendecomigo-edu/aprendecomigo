"""
Tests for simplified Teacher Invitation API endpoints.

Tests cover:
- POST /api/accounts/teacher-invitations/{token}/accept/
- GET /api/accounts/teacher-invitations/{token}/status/
- GET /api/accounts/teacher-invitations/list_for_school/
- Authentication and permission handling
- Edge cases and error scenarios
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
    TeacherProfile,
    InvitationStatus,
    EmailDeliveryStatus,
)

User = get_user_model()


class TeacherInvitationEndpointsTest(APITestCase):
    """Test cases for simplified teacher invitation endpoints."""
    
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
    
    def test_accept_invitation_success(self):
        """Test successful invitation acceptance."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        # Authenticate as the teacher
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.post(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('invitation', response.data)
        self.assertIn('membership', response.data)
        
        # Verify invitation was accepted
        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.is_accepted)
        self.assertEqual(self.invitation.status, InvitationStatus.ACCEPTED)
        self.assertIsNotNone(self.invitation.accepted_at)
        
        # Verify school membership was created
        membership = SchoolMembership.objects.get(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        self.assertTrue(membership.is_active)
        
        # Verify teacher profile was created
        self.assertTrue(hasattr(self.teacher_user, 'teacher_profile'))
    
    def test_accept_invitation_invalid_token(self):
        """Test invitation acceptance with invalid token."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': 'invalid-token'})
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_accept_invitation_unauthenticated(self):
        """Test invitation acceptance without authentication."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertIn('invitation_details', response.data)
    
    def test_accept_invitation_wrong_user(self):
        """Test invitation acceptance by wrong user."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        # Authenticate as a different user
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token}')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
    
    def test_accept_invitation_already_accepted(self):
        """Test accepting an already accepted invitation."""
        # Mark invitation as accepted
        self.invitation.accept()
        
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already been accepted', response.data['error'])
    
    def test_accept_invitation_expired(self):
        """Test accepting an expired invitation."""
        # Make invitation expired
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()
        
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expired', response.data['error'])
    
    def test_accept_invitation_with_existing_teacher_profile(self):
        """Test accepting invitation when user already has teacher profile."""
        # Create existing teacher profile
        TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Existing bio",
            specialty="Math"
        )
        
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['teacher_profile_created'])
    
    def test_invitation_status_success(self):
        """Test successful invitation status check."""
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('invitation', response.data)
        self.assertIn('email_delivery', response.data)
        self.assertIn('user_context', response.data)
        
        # Verify invitation data
        invitation_data = response.data['invitation']
        self.assertEqual(invitation_data['id'], self.invitation.id)
        self.assertEqual(invitation_data['email'], self.invitation.email)
        self.assertEqual(invitation_data['status'], self.invitation.status)
        self.assertFalse(invitation_data['is_accepted'])
        self.assertTrue(invitation_data['is_valid'])
        
        # Verify school data
        self.assertEqual(invitation_data['school']['name'], self.school.name)
        
        # Verify user context for unauthenticated user
        user_context = response.data['user_context']
        self.assertFalse(user_context['is_authenticated'])
        self.assertFalse(user_context['is_correct_user'])
        self.assertFalse(user_context['can_accept'])
    
    def test_invitation_status_authenticated_correct_user(self):
        """Test invitation status check by the intended recipient."""
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user context for correct authenticated user
        user_context = response.data['user_context']
        self.assertTrue(user_context['is_authenticated'])
        self.assertTrue(user_context['is_correct_user'])
        self.assertTrue(user_context['can_accept'])
    
    def test_invitation_status_authenticated_wrong_user(self):
        """Test invitation status check by wrong authenticated user."""
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token}')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user context for wrong authenticated user
        user_context = response.data['user_context']
        self.assertTrue(user_context['is_authenticated'])
        self.assertFalse(user_context['is_correct_user'])
        self.assertFalse(user_context['can_accept'])
    
    def test_invitation_status_marks_as_viewed(self):
        """Test that checking status marks invitation as viewed."""
        self.assertIsNone(self.invitation.viewed_at)
        
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify invitation was marked as viewed
        self.invitation.refresh_from_db()
        self.assertIsNotNone(self.invitation.viewed_at)
        self.assertEqual(self.invitation.status, InvitationStatus.VIEWED)
    
    def test_invitation_status_with_custom_message(self):
        """Test invitation status includes custom message."""
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('custom_message', response.data['invitation'])
        self.assertEqual(response.data['invitation']['custom_message'], "Welcome to our team!")
    
    def test_invitation_status_invalid_token(self):
        """Test invitation status with invalid token."""
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': 'invalid-token'})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_list_invitations_for_school_admin(self):
        """Test listing invitations for school admin."""
        # Create additional invitations
        invitation2 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher2@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7),
            status=InvitationStatus.SENT,
            email_delivery_status=EmailDeliveryStatus.SENT
        )
        
        url = reverse('accounts:teacher-invitation-list-for-school')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('invitations', response.data)
        self.assertIn('summary', response.data)
        self.assertIn('filters_applied', response.data)
        
        # Verify invitations data
        invitations = response.data['invitations']
        self.assertEqual(len(invitations), 2)
        
        # Verify summary statistics
        summary = response.data['summary']
        self.assertEqual(summary['total_invitations'], 2)
        self.assertGreaterEqual(summary['pending_invitations'], 0)
    
    def test_list_invitations_with_school_filter(self):
        """Test listing invitations with school filter."""
        url = reverse('accounts:teacher-invitation-list-for-school')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        
        response = self.client.get(url, {'school_id': self.school.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filters_applied']['school_id'], self.school.id)
    
    def test_list_invitations_with_status_filter(self):
        """Test listing invitations with status filter."""
        url = reverse('accounts:teacher-invitation-list-for-school')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        
        response = self.client.get(url, {'status': InvitationStatus.PENDING})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filters_applied']['status'], InvitationStatus.PENDING)
    
    def test_list_invitations_with_email_status_filter(self):
        """Test listing invitations with email status filter."""
        url = reverse('accounts:teacher-invitation-list-for-school')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        
        response = self.client.get(url, {'email_status': EmailDeliveryStatus.NOT_SENT})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filters_applied']['email_status'], EmailDeliveryStatus.NOT_SENT)
    
    def test_list_invitations_invalid_school_filter(self):
        """Test listing invitations with invalid school filter."""
        url = reverse('accounts:teacher-invitation-list-for-school')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        
        response = self.client.get(url, {'school_id': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid school_id', response.data['error'])
    
    def test_list_invitations_invalid_status_filter(self):
        """Test listing invitations with invalid status filter."""
        url = reverse('accounts:teacher-invitation-list-for-school')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        
        response = self.client.get(url, {'status': 'invalid_status'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid status', response.data['error'])
    
    def test_list_invitations_permission_denied_for_non_admin(self):
        """Test that non-admin users cannot list invitations."""
        url = reverse('accounts:teacher-invitation-list-for-school')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_invitations_unauthorized(self):
        """Test that unauthenticated users cannot list invitations."""
        url = reverse('accounts:teacher-invitation-list-for-school')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_invitations_includes_action_info(self):
        """Test that listing invitations includes action information."""
        url = reverse('accounts:teacher-invitation-list-for-school')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        invitation_data = response.data['invitations'][0]
        self.assertIn('actions', invitation_data)
        
        actions = invitation_data['actions']
        self.assertIn('can_cancel', actions)
        self.assertIn('can_resend', actions)
        self.assertIn('invitation_link', actions)
        self.assertTrue(actions['can_cancel'])  # Should be true for valid invitation
    
    def test_invitation_queryset_filtering(self):
        """Test that users can only see appropriate invitations."""
        # Create another school and admin
        other_school = School.objects.create(name="Other School")
        other_admin = User.objects.create_user(email="other_admin@test.com", name="Other Admin")
        SchoolMembership.objects.create(
            user=other_admin,
            school=other_school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        # Create invitation for other school
        other_invitation = TeacherInvitation.objects.create(
            school=other_school,
            email="teacher3@test.com",
            invited_by=other_admin,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Admin should only see invitations for their school
        url = reverse('accounts:teacher-invitation-list-for-school')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invitations = response.data['invitations']
        
        # Should only see invitation for their school
        self.assertEqual(len(invitations), 1)
        self.assertEqual(invitations[0]['school']['id'], self.school.id)
    
    def test_email_delivery_status_in_responses(self):
        """Test that email delivery status is included in responses."""
        # Update invitation with email delivery info
        self.invitation.email_delivery_status = EmailDeliveryStatus.FAILED
        self.invitation.email_failure_reason = "SMTP error"
        self.invitation.retry_count = 1
        self.invitation.save()
        
        # Test status endpoint
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        email_delivery = response.data['email_delivery']
        self.assertEqual(email_delivery['status'], EmailDeliveryStatus.FAILED)
        self.assertEqual(email_delivery['failure_reason'], "SMTP error")
        self.assertEqual(email_delivery['retry_count'], 1)
        self.assertTrue(email_delivery['can_retry'])
    
    @patch('accounts.views.SchoolActivityService.create_activity')
    def test_accept_invitation_creates_activity_log(self, mock_create_activity):
        """Test that accepting invitation creates activity log."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify activity was logged
        mock_create_activity.assert_called_once()
        call_args = mock_create_activity.call_args
        self.assertEqual(call_args[1]['school'], self.invitation.school)
        self.assertEqual(call_args[1]['actor'], self.teacher_user)
        self.assertEqual(call_args[1]['target_user'], self.teacher_user)


class TeacherInvitationEndpointsIntegrationTest(TestCase):
    """Integration tests for teacher invitation endpoints."""
    
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
    
    def test_full_invitation_workflow(self):
        """Test complete invitation workflow from creation to acceptance."""
        from django.test import Client
        
        client = Client()
        
        # 1. Create bulk invitation (using existing bulk endpoint)
        admin_token = AuthToken.objects.create(self.admin_user)[1]
        
        bulk_url = reverse('accounts:teacher-invite-bulk')
        bulk_data = {
            'school_id': self.school.id,
            'custom_message': 'Join our team!',
            'send_email': False,  # Skip email for test
            'invitations': [
                {'email': 'teacher@integration.com'}
            ]
        }
        
        response = client.post(
            bulk_url,
            data=bulk_data,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {admin_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get the created invitation
        invitation_data = response.json()['invitations'][0]
        invitation_token = invitation_data['token']
        
        # 2. Check invitation status (public)
        status_url = reverse('accounts:teacher-invitation-status', kwargs={'token': invitation_token})
        response = client.get(status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        status_data = response.json()
        self.assertFalse(status_data['invitation']['is_accepted'])
        self.assertTrue(status_data['invitation']['is_valid'])
        
        # 3. Create user and accept invitation
        teacher_user = User.objects.create_user(
            email='teacher@integration.com',
            name='Integration Teacher'
        )
        teacher_token = AuthToken.objects.create(teacher_user)[1]
        
        accept_url = reverse('accounts:teacher-invitation-accept', kwargs={'token': invitation_token})
        response = client.post(
            accept_url,
            HTTP_AUTHORIZATION=f'Token {teacher_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        accept_data = response.json()
        self.assertIn('message', accept_data)
        self.assertTrue(accept_data['invitation']['school']['id'], self.school.id)
        
        # 4. Verify invitation is now accepted
        response = client.get(status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        final_status = response.json()
        self.assertTrue(final_status['invitation']['is_accepted'])
        
        # 5. Verify school membership was created
        membership = SchoolMembership.objects.get(
            user=teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        self.assertTrue(membership.is_active)
        
        # 6. Verify teacher profile was created
        self.assertTrue(hasattr(teacher_user, 'teacher_profile'))
        
        # 7. Admin can see the accepted invitation in list
        list_url = reverse('accounts:teacher-invitation-list-for-school')
        response = client.get(
            list_url,
            HTTP_AUTHORIZATION=f'Token {admin_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        list_data = response.json()
        self.assertEqual(list_data['summary']['accepted_invitations'], 1)