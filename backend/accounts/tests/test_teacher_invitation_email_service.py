"""
Tests for Teacher Invitation Email Service functionality.

Tests cover:
- Email template rendering
- Single invitation email sending
- Bulk invitation email processing
- Email retry logic
- Error handling scenarios
"""

import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

import pytest
from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import (
    CustomUser, 
    School, 
    TeacherInvitation, 
    InvitationStatus, 
    EmailDeliveryStatus,
    SchoolRole
)
from common.messaging import TeacherInvitationEmailService


class TeacherInvitationEmailServiceTest(TestCase):
    """Test cases for TeacherInvitationEmailService."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            name="Admin User"
        )
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school for teacher invitations",
            contact_email="contact@testschool.com"
        )
        
        # Create test invitation
        self.invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            custom_message="Welcome to our team!",
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
    
    def test_send_invitation_email_success(self):
        """Test successful single invitation email sending."""
        # Clear the test outbox
        mail.outbox = []
        
        # Send the invitation email
        result = TeacherInvitationEmailService.send_invitation_email(self.invitation)
        
        # Verify success
        self.assertTrue(result['success'])
        self.assertEqual(result['email'], 'teacher@test.com')
        self.assertIn('Email sent successfully', result['message'])
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        
        # Verify email properties
        expected_subject = f"Teacher Invitation: Join {self.school.name} on Aprende Comigo"
        self.assertEqual(sent_email.subject, expected_subject)
        self.assertEqual(sent_email.to, ['teacher@test.com'])
        self.assertEqual(sent_email.from_email, settings.DEFAULT_FROM_EMAIL)
        
        # Verify email content contains key information
        email_body = sent_email.body
        self.assertIn(self.school.name, email_body)
        self.assertIn("Welcome to our team!", email_body)  # Custom message
        self.assertIn("Admin User", email_body)  # Invited by name
        self.assertIn("accept-teacher-invitation", email_body)  # Invitation link
        
        # Verify HTML content exists
        self.assertIsNotNone(sent_email.alternatives)
        html_content = sent_email.alternatives[0][0]
        self.assertIn(self.school.name, html_content)
        self.assertIn("Welcome to our team!", html_content)
    
    def test_send_invitation_email_template_context(self):
        """Test that email templates receive correct context variables."""
        mail.outbox = []
        
        # Create invitation with all optional fields
        invitation_with_all_fields = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher2@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            custom_message="Join our excellent teaching team!",
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=14)
        )
        
        result = TeacherInvitationEmailService.send_invitation_email(invitation_with_all_fields)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        sent_email = mail.outbox[0]
        email_body = sent_email.body
        
        # Verify all context variables are present
        self.assertIn(self.school.name, email_body)
        self.assertIn(self.school.description, email_body)
        self.assertIn("Teacher", email_body)  # Role display
        self.assertIn("Join our excellent teaching team!", email_body)  # Custom message
        self.assertIn("Admin User", email_body)  # Invited by name
        self.assertIn("admin@test.com", email_body)  # Invited by email
        self.assertIn("teacher2@test.com", email_body)  # Recipient email
        self.assertIn("accept-teacher-invitation", email_body)  # Invitation link
    
    @patch('common.messaging.send_mail')
    def test_send_invitation_email_failure(self, mock_send_mail):
        """Test handling of email sending failure."""
        # Mock send_mail to return False (failure)
        mock_send_mail.return_value = False
        
        result = TeacherInvitationEmailService.send_invitation_email(self.invitation)
        
        # Verify failure response
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Email sending failed')
        self.assertEqual(result['email'], 'teacher@test.com')
    
    @patch('common.messaging.send_mail')
    def test_send_invitation_email_exception(self, mock_send_mail):
        """Test handling of email sending exception."""
        # Mock send_mail to raise an exception
        mock_send_mail.side_effect = Exception("SMTP server error")
        
        result = TeacherInvitationEmailService.send_invitation_email(self.invitation)
        
        # Verify exception handling
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'SMTP server error')
        self.assertEqual(result['email'], 'teacher@test.com')
    
    def test_send_bulk_invitation_emails_success(self):
        """Test successful bulk invitation email sending."""
        mail.outbox = []
        
        # Create multiple invitations
        invitations = []
        for i in range(3):
            invitation = TeacherInvitation.objects.create(
                school=self.school,
                email=f"teacher{i}@test.com",
                invited_by=self.admin_user,
                role=SchoolRole.TEACHER,
                batch_id=uuid.uuid4(),
                expires_at=timezone.now() + timedelta(days=7)
            )
            invitations.append(invitation)
        
        # Send bulk emails
        result = TeacherInvitationEmailService.send_bulk_invitation_emails(invitations)
        
        # Verify bulk results
        self.assertEqual(result['total_invitations'], 3)
        self.assertEqual(result['successful_emails'], 3)
        self.assertEqual(result['failed_emails'], 0)
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(len(result['successful_emails_list']), 3)
        self.assertEqual(len(result['failed_emails_list']), 0)
        
        # Verify all emails were sent
        self.assertEqual(len(mail.outbox), 3)
        
        # Verify invitation statuses were updated
        for invitation in invitations:
            invitation.refresh_from_db()
            self.assertEqual(invitation.email_delivery_status, EmailDeliveryStatus.SENT)
            self.assertEqual(invitation.status, InvitationStatus.SENT)
            self.assertIsNotNone(invitation.email_sent_at)
    
    @patch('common.messaging.TeacherInvitationEmailService.send_invitation_email')
    def test_send_bulk_invitation_emails_partial_failure(self, mock_send_invitation):
        """Test bulk email sending with partial failures."""
        # Create multiple invitations
        invitations = []
        for i in range(3):
            invitation = TeacherInvitation.objects.create(
                school=self.school,
                email=f"teacher{i}@test.com",
                invited_by=self.admin_user,
                role=SchoolRole.TEACHER,
                batch_id=uuid.uuid4(),
                expires_at=timezone.now() + timedelta(days=7)
            )
            invitations.append(invitation)
        
        # Mock responses: first succeeds, second fails, third succeeds
        mock_send_invitation.side_effect = [
            {'success': True, 'email': 'teacher0@test.com'},
            {'success': False, 'error': 'SMTP error', 'email': 'teacher1@test.com'},
            {'success': True, 'email': 'teacher2@test.com'}
        ]
        
        # Send bulk emails
        result = TeacherInvitationEmailService.send_bulk_invitation_emails(invitations)
        
        # Verify partial failure results
        self.assertEqual(result['total_invitations'], 3)
        self.assertEqual(result['successful_emails'], 2)
        self.assertEqual(result['failed_emails'], 1)
        self.assertEqual(len(result['errors']), 1)
        self.assertIn('teacher1@test.com', result['failed_emails_list'])
        self.assertIn('teacher0@test.com', result['successful_emails_list'])
        self.assertIn('teacher2@test.com', result['successful_emails_list'])
    
    def test_retry_failed_invitation_email_success(self):
        """Test successful retry of failed invitation email."""
        mail.outbox = []
        
        # Set invitation to failed state
        self.invitation.email_delivery_status = EmailDeliveryStatus.FAILED
        self.invitation.retry_count = 1
        self.invitation.email_failure_reason = "Previous SMTP error"
        self.invitation.save()
        
        # Retry sending
        result = TeacherInvitationEmailService.retry_failed_invitation_email(self.invitation)
        
        # Verify retry success
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        # Verify invitation status was updated
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.email_delivery_status, EmailDeliveryStatus.SENT)
        self.assertEqual(self.invitation.retry_count, 0)  # Reset on success
        self.assertIsNone(self.invitation.email_failure_reason)
    
    def test_retry_failed_invitation_email_max_attempts_exceeded(self):
        """Test retry failure when max attempts exceeded."""
        # Set invitation to failed state with max retries
        self.invitation.email_delivery_status = EmailDeliveryStatus.FAILED
        self.invitation.retry_count = 3
        self.invitation.max_retries = 3
        self.invitation.save()
        
        # Attempt retry
        result = TeacherInvitationEmailService.retry_failed_invitation_email(self.invitation)
        
        # Verify retry blocked
        self.assertFalse(result['success'])
        self.assertIn('Maximum retry attempts', result['error'])
        self.assertEqual(result['retry_count'], 3)
    
    @patch('common.messaging.TeacherInvitationEmailService.send_invitation_email')
    def test_retry_failed_invitation_email_still_fails(self, mock_send_invitation):
        """Test retry that still fails."""
        # Mock continued failure
        mock_send_invitation.return_value = {
            'success': False, 
            'error': 'SMTP still down',
            'email': 'teacher@test.com'
        }
        
        # Set invitation to failed state
        self.invitation.email_delivery_status = EmailDeliveryStatus.FAILED
        self.invitation.retry_count = 1
        self.invitation.save()
        
        # Attempt retry
        result = TeacherInvitationEmailService.retry_failed_invitation_email(self.invitation)
        
        # Verify retry failure handling
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'SMTP still down')
        
        # Verify retry count was incremented
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.retry_count, 2)
        self.assertIn('SMTP still down', self.invitation.email_failure_reason)
    
    def test_invitation_email_without_custom_message(self):
        """Test email generation when no custom message is provided."""
        mail.outbox = []
        
        # Create invitation without custom message
        invitation_no_message = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher3@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
            # No custom_message provided
        )
        
        result = TeacherInvitationEmailService.send_invitation_email(invitation_no_message)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        # Email should still be sent successfully without custom message
        sent_email = mail.outbox[0]
        self.assertIn(self.school.name, sent_email.body)
        self.assertIn("Admin User", sent_email.body)
    
    def test_invitation_email_without_school_description(self):
        """Test email generation when school has no description."""
        mail.outbox = []
        
        # Create school without description
        school_no_desc = School.objects.create(
            name="Minimal School",
            contact_email="minimal@test.com"
            # No description provided
        )
        
        invitation = TeacherInvitation.objects.create(
            school=school_no_desc,
            email="teacher4@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        result = TeacherInvitationEmailService.send_invitation_email(invitation)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        # Email should still be sent successfully without school description
        sent_email = mail.outbox[0]
        self.assertIn("Minimal School", sent_email.body)
    
    @override_settings(DEBUG=True)
    def test_email_service_in_debug_mode(self):
        """Test that email service works correctly in DEBUG mode."""
        mail.outbox = []
        
        result = TeacherInvitationEmailService.send_invitation_email(self.invitation)
        
        # Should still work in DEBUG mode
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
    
    def test_email_content_escaping(self):
        """Test that email content is properly escaped to prevent XSS."""
        mail.outbox = []
        
        # Create invitation with potentially malicious content
        malicious_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="test@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            custom_message="<script>alert('xss')</script>Welcome!",
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        result = TeacherInvitationEmailService.send_invitation_email(malicious_invitation)
        
        self.assertTrue(result['success'])
        sent_email = mail.outbox[0]
        
        # Verify script tags are properly escaped or handled
        email_body = sent_email.body
        self.assertIn("Welcome!", email_body)
        # Script tags should be escaped in the email content
        self.assertNotIn('<script>', email_body)
        # Alert should be escaped (may contain &#x27; instead of ')
        self.assertNotIn("alert('xss')", email_body)
        # Verify content is actually escaped
        self.assertIn("&lt;script&gt;", email_body)  # Escaped script tags
        
        # HTML version should also be safe
        if sent_email.alternatives:
            html_content = sent_email.alternatives[0][0]
            self.assertIn("Welcome!", html_content)
            # Script tags should be escaped in HTML version too
            self.assertNotIn('<script>', html_content)
            self.assertNotIn("alert('xss')", html_content)
            # Verify content is actually escaped in HTML too
            self.assertIn("&lt;script&gt;", html_content)  # Escaped script tags


@pytest.mark.django_db
class TeacherInvitationEmailServicePyTest:
    """PyTest-style tests for additional edge cases."""
    
    def test_bulk_email_empty_list(self):
        """Test bulk email processing with empty invitation list."""
        result = TeacherInvitationEmailService.send_bulk_invitation_emails([])
        
        assert result['total_invitations'] == 0
        assert result['successful_emails'] == 0
        assert result['failed_emails'] == 0
        assert len(result['errors']) == 0
    
    def test_email_service_invalid_invitation(self):
        """Test email service with invalid invitation object."""
        # Create a mock invitation-like object without required attributes
        class MockInvitation:
            pass
        
        mock_invitation = MockInvitation()
        
        result = TeacherInvitationEmailService.send_invitation_email(mock_invitation)
        
        assert not result['success']
        assert 'error' in result
    
    @patch('common.messaging.render_to_string')
    def test_template_rendering_error(self, mock_render):
        """Test handling of template rendering errors."""
        # Mock template rendering to raise an exception
        mock_render.side_effect = Exception("Template not found")
        
        # Create minimal test data
        admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            name="Admin"
        )
        school = School.objects.create(name="Test School")
        invitation = TeacherInvitation.objects.create(
            school=school,
            email="test@test.com",
            invited_by=admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        result = TeacherInvitationEmailService.send_invitation_email(invitation)
        
        assert not result['success']
        assert 'Template not found' in result['error']