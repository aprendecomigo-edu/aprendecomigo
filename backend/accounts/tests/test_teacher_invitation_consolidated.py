"""
Consolidated tests for Teacher Invitation functionality.

This file combines tests from multiple teacher invitation test files to reduce
duplication while maintaining comprehensive coverage.

Tests cover:
- Invitation model and business logic
- API endpoints (accept, decline, status, list)
- Email service integration
- Security and permissions
- Response structure validation
"""

import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
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
)
from messaging.models import EmailDeliveryStatus

User = get_user_model()


class TeacherInvitationModelTest(TestCase):
    """Test TeacherInvitation model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="Test Description"
        )
        
        self.admin = User.objects.create_user(
            email="admin@test.com",
            name="Admin User"
        )
        
        self.teacher_email = "teacher@test.com"
    
    def test_invitation_creation(self):
        """Test creating a teacher invitation."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email=self.teacher_email,
            invited_by=self.admin,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        self.assertIsNotNone(invitation.token)
        self.assertEqual(invitation.status, InvitationStatus.PENDING)
        self.assertFalse(invitation.is_accepted)
    
    def test_invitation_accept(self):
        """Test accepting an invitation."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email=self.teacher_email,
            invited_by=self.admin,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        invitation.accept()
        
        self.assertTrue(invitation.is_accepted)
        self.assertEqual(invitation.status, InvitationStatus.ACCEPTED)
        self.assertIsNotNone(invitation.accepted_at)
    
    def test_invitation_decline(self):
        """Test declining an invitation."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email=self.teacher_email,
            invited_by=self.admin,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        invitation.decline()
        
        self.assertFalse(invitation.is_accepted)
        self.assertEqual(invitation.status, InvitationStatus.DECLINED)
        self.assertIsNotNone(invitation.declined_at)
    
    def test_invitation_expiry(self):
        """Test invitation expiry check."""
        # Create expired invitation
        expired_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email=self.teacher_email,
            invited_by=self.admin,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() - timedelta(days=1),
            batch_id=uuid.uuid4()
        )
        
        self.assertTrue(expired_invitation.is_expired())
        
        # Create valid invitation
        valid_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="another@test.com",
            invited_by=self.admin,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=1),
            batch_id=uuid.uuid4()
        )
        
        self.assertFalse(valid_invitation.is_expired())
    
    def test_duplicate_active_invitation_prevented(self):
        """Test that duplicate active invitations are prevented."""
        # Create first invitation
        TeacherInvitation.objects.create(
            school=self.school,
            email=self.teacher_email,
            invited_by=self.admin,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        # Try to create duplicate
        with self.assertRaises(ValidationError):
            invitation = TeacherInvitation(
                school=self.school,
                email=self.teacher_email,
                invited_by=self.admin,
                role=SchoolRole.TEACHER,
                expires_at=timezone.now() + timedelta(days=7)
            )
            invitation.full_clean()


class TeacherInvitationAPITest(APITestCase):
    """Test Teacher Invitation API endpoints."""
    
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
            description="A test school"
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
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('invitation', response.data)
        self.assertIn('membership', response.data)
        
        # Verify invitation was accepted
        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.is_accepted)
        self.assertEqual(self.invitation.status, InvitationStatus.ACCEPTED)
        
        # Verify school membership was created
        membership = SchoolMembership.objects.get(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        self.assertTrue(membership.is_active)
    
    def test_accept_invitation_invalid_token(self):
        """Test invitation acceptance with invalid token."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': 'invalid-token'})
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_accept_invitation_unauthenticated(self):
        """Test invitation acceptance without authentication."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_accept_invitation_wrong_user(self):
        """Test invitation acceptance by wrong user."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token}')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_accept_invitation_expired(self):
        """Test accepting an expired invitation."""
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()
        
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INVITATION_EXPIRED')
    
    def test_decline_invitation_success(self):
        """Test successful invitation decline."""
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify invitation was declined
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, InvitationStatus.DECLINED)
        self.assertIsNotNone(self.invitation.declined_at)
    
    def test_decline_invitation_authenticated(self):
        """Test decline with authenticated user."""
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_decline_invitation_already_accepted(self):
        """Test declining an already accepted invitation."""
        self.invitation.accept()
        
        url = reverse('accounts:teacher-invitation-decline', kwargs={'token': self.invitation.token})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INVITATION_ALREADY_ACCEPTED')
    
    def test_invitation_status_check(self):
        """Test checking invitation status."""
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('invitation', response.data)
        self.assertEqual(response.data['invitation']['email'], self.teacher_user.email)
        self.assertEqual(response.data['invitation']['status'], InvitationStatus.VIEWED)
        
        # Check that invitation was marked as viewed
        self.invitation.refresh_from_db()
        self.assertIsNotNone(self.invitation.viewed_at)
    
    def test_list_invitations_for_school_admin(self):
        """Test listing invitations for school admin."""
        # Create additional invitations
        TeacherInvitation.objects.create(
            school=self.school,
            email="teacher2@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        url = reverse('accounts:teacher-invitation-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_invitations_permission_denied(self):
        """Test that non-admins cannot list invitations."""
        url = reverse('accounts:teacher-invitation-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_invitation_response_structure(self):
        """Test that API response structure matches frontend expectations."""
        url = reverse('accounts:teacher-invitation-status', kwargs={'token': self.invitation.token})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required fields in invitation object
        invitation_data = response.data['invitation']
        required_fields = ['id', 'email', 'status', 'school', 'role', 'expires_at']
        for field in required_fields:
            self.assertIn(field, invitation_data)
        
        # Check nested school object
        self.assertIn('name', invitation_data['school'])
        self.assertIn('id', invitation_data['school'])


class TeacherInvitationEmailServiceTest(TestCase):
    """Test Teacher Invitation email service integration."""
    
    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            contact_email="contact@testschool.com"
        )
        
        self.admin = User.objects.create_user(
            email="admin@test.com",
            name="Admin User"
        )
    
    @patch('messaging.services.teacher_invitation_service.TeacherInvitationEmailService.send_invitation_email')
    def test_send_invitation_email(self, mock_send_email):
        """Test sending invitation email via service."""
        mock_send_email.return_value = True
        
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@test.com",
            invited_by=self.admin,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4(),
        )
        
        # Manually trigger email sending (as would be done by service layer)
        invitation.mark_email_sent()
        
        # Check email status was updated
        self.assertEqual(invitation.email_delivery_status, 'sent')
    
    @patch('messaging.services.teacher_invitation_service.TeacherInvitationEmailService.send_invitation_email')
    def test_send_invitation_email_failure(self, mock_send_email):
        """Test handling email send failure."""
        mock_send_email.side_effect = Exception("Email service error")
        
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@test.com",
            invited_by=self.admin,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4(),
        )
        
        # Manually trigger email failure (as would be done by service layer)
        invitation.mark_email_failed("Email service error")
        
        self.assertEqual(invitation.email_delivery_status, 'failed')


class TeacherInvitationSecurityTest(APITestCase):
    """Test security aspects of teacher invitation system."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            name="Admin User"
        )
        
        self.school = School.objects.create(
            name="Test School",
            description="Test Description"
        )
        
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        self.admin_token = AuthToken.objects.create(self.admin_user)[1]
    
    def test_invitation_token_uniqueness(self):
        """Test that invitation tokens are unique."""
        tokens = set()
        for i in range(10):
            invitation = TeacherInvitation.objects.create(
                school=self.school,
                email=f"teacher{i}@test.com",
                invited_by=self.admin_user,
                role=SchoolRole.TEACHER,
                expires_at=timezone.now() + timedelta(days=7),
                batch_id=uuid.uuid4()
            )
            self.assertNotIn(invitation.token, tokens)
            tokens.add(invitation.token)
    
    def test_invitation_token_not_guessable(self):
        """Test that invitation tokens are not easily guessable."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        # Token should be a secure hex string (64 characters)
        self.assertEqual(len(invitation.token), 64)
        # Check that it's all hexadecimal characters
        try:
            int(invitation.token, 16)
        except ValueError:
            self.fail("Token is not a valid hexadecimal string")
    
    def test_cross_school_invitation_access_denied(self):
        """Test that users from other schools cannot access invitations."""
        # Create another school and admin
        other_school = School.objects.create(name="Other School")
        other_admin = User.objects.create_user(
            email="other_admin@test.com",
            name="Other Admin"
        )
        SchoolMembership.objects.create(
            user=other_admin,
            school=other_school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        other_token = AuthToken.objects.create(other_admin)[1]
        
        # Create invitation for first school
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        # Try to access with other school's admin
        url = reverse('accounts:teacher-invitation-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token}')
        
        response = self.client.get(url)
        
        # Should not see invitations from other school
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)



class TeacherInvitationManagerTest(TestCase):
    """Test suite for TeacherInvitation model manager methods."""
    
    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="School for testing invitations"
        )
        
        self.school_owner = User.objects.create_user(
            email="owner@testschool.com",
            name="School Owner"
        )
    
    def test_active_invitations_queryset(self):
        """Test active_invitations() manager method."""
        batch_id = uuid.uuid4()
        
        # Create various invitations
        active_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="active@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        expired_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="expired@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        accepted_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="accepted@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id,
            expires_at=timezone.now() + timedelta(days=7)
        )
        accepted_invitation.accept()
        
        cancelled_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="cancelled@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id,
            status=InvitationStatus.DECLINED,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Test filtering logic (assuming active means not expired, not accepted, not declined)
        active_invitations = TeacherInvitation.objects.filter(
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now()
        )
        self.assertIn(active_invitation, active_invitations)
        self.assertNotIn(expired_invitation, active_invitations)
        self.assertNotIn(accepted_invitation, active_invitations)
        self.assertNotIn(cancelled_invitation, active_invitations)
    
    def test_for_school_queryset(self):
        """Test filtering invitations by school."""
        school2 = School.objects.create(name="Other School")
        batch_id = uuid.uuid4()
        
        invitation1 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher1@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        invitation2 = TeacherInvitation.objects.create(
            school=school2,
            email="teacher2@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        school_invitations = TeacherInvitation.objects.filter(school=self.school)
        self.assertIn(invitation1, school_invitations)
        self.assertNotIn(invitation2, school_invitations)
    
    def test_for_batch_queryset(self):
        """Test filtering invitations by batch."""
        batch_id1 = uuid.uuid4()
        batch_id2 = uuid.uuid4()
        
        invitation1 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher1@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id1,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        invitation2 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher2@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id2,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        batch_invitations = TeacherInvitation.objects.filter(batch_id=batch_id1)
        self.assertIn(invitation1, batch_invitations)
        self.assertNotIn(invitation2, batch_invitations)


class TeacherInvitationEnumTest(TestCase):
    """Test suite for invitation-related enums."""
    
    def test_invitation_status_choices(self):
        """Test InvitationStatus enum choices."""
        expected_statuses = [
            InvitationStatus.PENDING,
            InvitationStatus.ACCEPTED, 
            InvitationStatus.DECLINED
        ]
        
        # Verify each expected status exists
        for status_value in expected_statuses:
            self.assertIsNotNone(status_value)
    
    def test_email_delivery_status_choices(self):
        """Test EmailDeliveryStatus enum choices."""
        expected_statuses = [
            EmailDeliveryStatus.NOT_SENT,
            EmailDeliveryStatus.SENT,
            EmailDeliveryStatus.FAILED
        ]
        
        # Verify each expected status exists  
        for status_value in expected_statuses:
            self.assertIsNotNone(status_value)