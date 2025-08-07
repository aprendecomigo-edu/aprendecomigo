"""
Business logic tests for Teacher Invitation Email Service.

Focused on:
- Teacher invitation workflow business rules
- Bulk invitation processing logic
- Retry logic and failure handling
- Email template context business requirements
- Security validation (XSS prevention)
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
    
    def test_bulk_invitation_processing_business_rules(self):
        """Test business rule: bulk invitation processing handles multiple invitations systematically."""
        mail.outbox = []
        
        # Business scenario: school wants to invite multiple teachers at once
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
        
        # Business action: process bulk invitations
        result = TeacherInvitationEmailService.send_bulk_invitation_emails(invitations)
        
        # Business rule: service provides complete processing summary
        self.assertEqual(result['total_invitations'], 3)
        self.assertEqual(result['successful_emails'], 3)
        self.assertEqual(result['failed_emails'], 0)
        
        # Business rule: all emails are sent
        self.assertEqual(len(mail.outbox), 3)
        
        # Business rule: invitation states are updated after processing
        for invitation in invitations:
            invitation.refresh_from_db()
            self.assertEqual(invitation.email_delivery_status, EmailDeliveryStatus.SENT)
            self.assertEqual(invitation.status, InvitationStatus.SENT)
            self.assertIsNotNone(invitation.email_sent_at)
    
    @patch('common.messaging.TeacherInvitationEmailService.send_invitation_email')
    def test_bulk_processing_handles_partial_failures(self, mock_send_invitation):
        """Test business rule: bulk processing continues despite individual failures."""
        # Business scenario: multiple invitations with some delivery issues
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
        
        # Business scenario: mixed success/failure results
        mock_send_invitation.side_effect = [
            {'success': True, 'email': 'teacher0@test.com'},
            {'success': False, 'error': 'SMTP error', 'email': 'teacher1@test.com'},
            {'success': True, 'email': 'teacher2@test.com'}
        ]
        
        result = TeacherInvitationEmailService.send_bulk_invitation_emails(invitations)
        
        # Business rule: service provides accurate success/failure counts
        self.assertEqual(result['total_invitations'], 3)
        self.assertEqual(result['successful_emails'], 2)
        self.assertEqual(result['failed_emails'], 1)
        
        # Business rule: service tracks which invitations failed
        self.assertIn('teacher1@test.com', result['failed_emails_list'])
        self.assertIn('teacher0@test.com', result['successful_emails_list'])
        self.assertIn('teacher2@test.com', result['successful_emails_list'])
    
    def test_retry_mechanism_business_rules(self):
        """Test business rule: failed invitations can be retried with proper state management."""
        mail.outbox = []
        
        # Business scenario: invitation failed due to temporary infrastructure issue
        self.invitation.email_delivery_status = EmailDeliveryStatus.FAILED
        self.invitation.retry_count = 1
        self.invitation.email_failure_reason = "Previous SMTP error"
        self.invitation.save()
        
        # Business action: retry failed invitation
        result = TeacherInvitationEmailService.retry_failed_invitation_email(self.invitation)
        
        # Business rule: successful retry sends email
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        # Business rule: successful retry resets failure tracking
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.email_delivery_status, EmailDeliveryStatus.SENT)
        self.assertEqual(self.invitation.retry_count, 0)  # Reset on success
        self.assertIsNone(self.invitation.email_failure_reason)
    
    def test_retry_limit_business_constraint(self):
        """Test business rule: retry attempts are limited to prevent infinite loops."""
        # Business scenario: invitation has reached maximum retry limit
        self.invitation.email_delivery_status = EmailDeliveryStatus.FAILED
        self.invitation.retry_count = 3
        self.invitation.max_retries = 3
        self.invitation.save()
        
        # Business action: attempt to retry beyond limit
        result = TeacherInvitationEmailService.retry_failed_invitation_email(self.invitation)
        
        # Business rule: service prevents excessive retry attempts
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
    
    
    
    
    def test_xss_prevention_in_invitation_content(self):
        """Test business security rule: user-provided content is properly escaped to prevent XSS."""
        mail.outbox = []
        
        # Business security scenario: user enters malicious script in custom message
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
        
        # Business security rule: malicious content is neutralized
        email_body = sent_email.body
        self.assertIn("Welcome!", email_body)  # Safe content preserved
        self.assertNotIn('<script>', email_body)  # Dangerous content removed
        self.assertNotIn("alert('xss')", email_body)  # Script execution prevented
        self.assertIn("&lt;script&gt;", email_body)  # Content safely escaped
    
    def test_handle_empty_bulk_invitations(self):
        """Test business rule: service handles empty bulk invitation lists gracefully."""
        # Business scenario: no invitations to process
        result = TeacherInvitationEmailService.send_bulk_invitation_emails([])
        
        # Business rule: service returns consistent structure even with no work
        self.assertEqual(result['total_invitations'], 0)
        self.assertEqual(result['successful_emails'], 0)
        self.assertEqual(result['failed_emails'], 0)
        self.assertEqual(len(result['errors']), 0)

