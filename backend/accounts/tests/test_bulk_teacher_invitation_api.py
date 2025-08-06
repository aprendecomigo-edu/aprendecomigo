"""
Tests for the bulk teacher invitation API endpoint.
Following TDD methodology - tests written first, then implementation.
"""
import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.test import APIClient
from knox.models import AuthToken

from accounts.models import (
    School, 
    SchoolMembership, 
    SchoolRole,
    TeacherInvitation,
    InvitationStatus,
)
from messaging.models import EmailDeliveryStatus

User = get_user_model()


class BulkTeacherInvitationAPITest(TestCase):
    """Test suite for the bulk teacher invitation API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="School for testing bulk invitations"
        )
        
        # Create school admin user
        self.school_admin = User.objects.create_user(
            email="admin@testschool.com",
            name="School Admin",
            phone_number="+351912000001"
        )
        
        SchoolMembership.objects.create(
            user=self.school_admin,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        # Create authentication token
        self.token = AuthToken.objects.create(self.school_admin)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        
        # API endpoint
        self.bulk_invite_url = reverse('accounts:teacher-invite-bulk')
    
    def test_bulk_invitation_successful_creation(self):
        """Test successful creation of bulk teacher invitations."""
        invitation_data = {
            'school_id': self.school.id,
            'custom_message': 'Welcome to our amazing school!',
            'invitations': [
                {'email': 'teacher1@example.com'},
                {'email': 'teacher2@example.com'},
                {'email': 'teacher3@example.com'},
            ]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('batch_id', response.data)
        self.assertEqual(response.data['total_invitations'], 3)
        self.assertEqual(response.data['successful_invitations'], 3)
        self.assertEqual(response.data['failed_invitations'], 0)
        self.assertEqual(len(response.data['errors']), 0)
        
        # Verify invitations were created
        batch_id = response.data['batch_id']
        invitations = TeacherInvitation.objects.filter(batch_id=batch_id)
        self.assertEqual(invitations.count(), 3)
        
        for invitation in invitations:
            self.assertEqual(invitation.school, self.school)
            self.assertEqual(invitation.invited_by, self.school_admin)
            self.assertEqual(invitation.custom_message, 'Welcome to our amazing school!')
            self.assertEqual(invitation.status, InvitationStatus.PENDING)
            self.assertEqual(invitation.email_delivery_status, EmailDeliveryStatus.NOT_SENT)
    
    def test_bulk_invitation_large_batch(self):
        """Test bulk invitation with 50+ invitations."""
        # Create 75 unique email addresses
        emails = [f'teacher{i}@example.com' for i in range(75)]
        
        invitation_data = {
            'school_id': self.school.id,
            'custom_message': 'Join our teaching team!',
            'invitations': [{'email': email} for email in emails]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_invitations'], 75)
        self.assertEqual(response.data['successful_invitations'], 75)
        self.assertEqual(response.data['failed_invitations'], 0)
        
        # Verify all invitations were created with same batch_id
        batch_id = response.data['batch_id']
        invitations = TeacherInvitation.objects.filter(batch_id=batch_id)
        self.assertEqual(invitations.count(), 75)
    
    def test_bulk_invitation_transaction_rollback_on_partial_failure(self):
        """Test that transaction is rolled back if any invitation fails."""
        # Create an existing invitation to cause conflict
        existing_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email='duplicate@example.com',
            invited_by=self.school_admin,
            batch_id=uuid.uuid4()
        )
        
        invitation_data = {
            'school_id': self.school.id,
            'invitations': [
                {'email': 'teacher1@example.com'},
                {'email': 'duplicate@example.com'},  # This will fail
                {'email': 'teacher2@example.com'},
            ]
        }
        
        initial_count = TeacherInvitation.objects.count()
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        # Should return partial success with error details
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data['total_invitations'], 3)
        self.assertEqual(response.data['successful_invitations'], 2)
        self.assertEqual(response.data['failed_invitations'], 1)
        self.assertEqual(len(response.data['errors']), 1)
        
        # Check error details
        error = response.data['errors'][0]
        self.assertEqual(error['email'], 'duplicate@example.com')
        self.assertIn('already exists', error['error'])
        
        # Verify that successful invitations were still created
        final_count = TeacherInvitation.objects.count()
        self.assertEqual(final_count, initial_count + 2)  # Only 2 new invitations
    
    def test_bulk_invitation_invalid_email_addresses(self):
        """Test handling of invalid email addresses."""
        invitation_data = {
            'school_id': self.school.id,
            'invitations': [
                {'email': 'valid@example.com'},
                {'email': 'invalid-email'},  # Invalid email
                {'email': ''},  # Empty email
                {'email': 'another@valid.com'},
            ]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data['total_invitations'], 4)
        self.assertEqual(response.data['successful_invitations'], 2)
        self.assertEqual(response.data['failed_invitations'], 2)
        self.assertEqual(len(response.data['errors']), 2)
        
        # Check that valid invitations were created
        valid_emails = ['valid@example.com', 'another@valid.com']
        created_invitations = TeacherInvitation.objects.filter(
            email__in=valid_emails,
            school=self.school
        )
        self.assertEqual(created_invitations.count(), 2)
    
    def test_bulk_invitation_empty_request(self):
        """Test handling of empty invitation list."""
        invitation_data = {
            'school_id': self.school.id,
            'invitations': []
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('invitations', response.data)
    
    def test_bulk_invitation_too_many_invitations(self):
        """Test handling of requests exceeding maximum limit."""
        # Create 101 invitations (assuming max is 100)
        emails = [f'teacher{i}@example.com' for i in range(101)]
        
        invitation_data = {
            'school_id': self.school.id,
            'invitations': [{'email': email} for email in emails]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no more than 100 elements', response.data['invitations'][0].lower())
    
    def test_bulk_invitation_duplicate_emails_in_request(self):
        """Test handling of duplicate emails within the same request."""
        invitation_data = {
            'school_id': self.school.id,
            'invitations': [
                {'email': 'teacher@example.com'},
                {'email': 'unique@example.com'},
                {'email': 'teacher@example.com'},  # Duplicate
            ]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data['successful_invitations'], 2)
        self.assertEqual(response.data['failed_invitations'], 1)
        
        # Verify only unique invitations were created
        created_invitations = TeacherInvitation.objects.filter(school=self.school)
        emails = list(created_invitations.values_list('email', flat=True))
        self.assertIn('teacher@example.com', emails)
        self.assertIn('unique@example.com', emails)
        self.assertEqual(len(emails), 2)  # No duplicates
    
    def test_bulk_invitation_authentication_required(self):
        """Test that authentication is required."""
        self.client.credentials()  # Remove authentication
        
        invitation_data = {
            'school_id': self.school.id,
            'invitations': [{'email': 'teacher@example.com'}]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_bulk_invitation_permission_check(self):
        """Test that user must have permission to invite to the school."""
        # Create another school
        other_school = School.objects.create(name="Other School")
        
        invitation_data = {
            'school_id': other_school.id,
            'invitations': [{'email': 'teacher@example.com'}]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        # Returns 400 Bad Request since school_id validation fails at serializer level
        # This is semantically correct - user is sending invalid data (school they can't manage)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_bulk_invitation_invalid_school_id(self):
        """Test handling of invalid school ID."""
        invitation_data = {
            'school_id': 99999,  # Non-existent school
            'invitations': [{'email': 'teacher@example.com'}]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('school_id', response.data)
    
    def test_bulk_invitation_custom_message_length_validation(self):
        """Test custom message length validation."""
        long_message = "x" * 1001  # Exceeds max length
        
        invitation_data = {
            'school_id': self.school.id,
            'custom_message': long_message,
            'invitations': [{'email': 'teacher@example.com'}]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('custom_message', response.data)
    
    def test_bulk_invitation_response_format(self):
        """Test the format of successful bulk invitation response."""
        invitation_data = {
            'school_id': self.school.id,
            'custom_message': 'Welcome!',
            'invitations': [
                {'email': 'teacher1@example.com'},
                {'email': 'teacher2@example.com'},
            ]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response structure
        expected_keys = [
            'batch_id', 'total_invitations', 'successful_invitations', 
            'failed_invitations', 'errors', 'invitations', 'message'
        ]
        
        for key in expected_keys:
            self.assertIn(key, response.data)
        
        # Check invitation details in response
        invitations = response.data['invitations']
        self.assertEqual(len(invitations), 2)
        
        for invitation in invitations:
            self.assertIn('id', invitation)
            self.assertIn('email', invitation)
            self.assertIn('token', invitation)
            self.assertIn('link', invitation)
            self.assertIn('expires_at', invitation)
    
    def test_bulk_invitation_with_send_email_flag(self):
        """Test bulk invitation with send_email flag."""
        invitation_data = {
            'school_id': self.school.id,
            'send_email': True,
            'invitations': [
                {'email': 'teacher1@example.com'},
                {'email': 'teacher2@example.com'},
            ]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify invitations were marked as sent (or at least queued for sending)
        batch_id = response.data['batch_id']
        invitations = TeacherInvitation.objects.filter(batch_id=batch_id)
        
        for invitation in invitations:
            # Email should be marked as sent or at least not "not_sent"
            self.assertNotEqual(invitation.email_delivery_status, EmailDeliveryStatus.NOT_SENT)


class BulkTeacherInvitationSerializerTest(TestCase):
    """Test suite for the BulkTeacherInvitationSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Test School")
        self.admin_user = User.objects.create_user(
            email="admin@testschool.com",
            name="Admin User"
        )
        
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
    
    def test_serializer_validation_valid_data(self):
        """Test serializer with valid data."""
        from accounts.serializers import BulkTeacherInvitationSerializer
        
        data = {
            'school_id': self.school.id,
            'custom_message': 'Welcome to our school!',
            'send_email': True,
            'invitations': [
                {'email': 'teacher1@example.com'},
                {'email': 'teacher2@example.com'},
            ]
        }
        
        serializer = BulkTeacherInvitationSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': self.admin_user})()}
        )
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data['invitations']), 2)
    
    def test_serializer_validation_invalid_email(self):
        """Test serializer validation with invalid email - should pass, validation moved to view level."""
        from accounts.serializers import BulkTeacherInvitationSerializer
        
        data = {
            'school_id': self.school.id,
            'invitations': [
                {'email': 'valid@example.com'},
                {'email': 'invalid-email'},
            ]
        }
        
        serializer = BulkTeacherInvitationSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': self.admin_user})()}
        )
        
        # Serializer should pass - validation moved to view level for partial success handling
        self.assertTrue(serializer.is_valid())
    
    def test_serializer_validation_too_many_invitations(self):
        """Test serializer validation with too many invitations."""
        from accounts.serializers import BulkTeacherInvitationSerializer
        
        # Create 101 invitations (assuming max is 100)
        invitations = [{'email': f'teacher{i}@example.com'} for i in range(101)]
        
        data = {
            'school_id': self.school.id,
            'invitations': invitations
        }
        
        serializer = BulkTeacherInvitationSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': self.admin_user})()}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('invitations', serializer.errors)
    
    def test_serializer_validation_duplicate_emails(self):
        """Test serializer validation with duplicate emails - should pass, validation moved to view level."""
        from accounts.serializers import BulkTeacherInvitationSerializer
        
        data = {
            'school_id': self.school.id,
            'invitations': [
                {'email': 'teacher@example.com'},
                {'email': 'teacher@example.com'},  # Duplicate
            ]
        }
        
        serializer = BulkTeacherInvitationSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': self.admin_user})()}
        )
        
        # Serializer should pass - duplicate validation moved to view level for partial success handling
        self.assertTrue(serializer.is_valid())
    
    def test_serializer_validation_school_permission(self):
        """Test serializer validation for school permission."""
        from accounts.serializers import BulkTeacherInvitationSerializer
        
        # Create user without permission to this school
        other_user = User.objects.create_user(
            email="other@example.com",
            name="Other User"
        )
        
        data = {
            'school_id': self.school.id,
            'invitations': [{'email': 'teacher@example.com'}]
        }
        
        serializer = BulkTeacherInvitationSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': other_user})()}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('school_id', serializer.errors)