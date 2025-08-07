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
from messaging.tests.test_base import MessagingTestBase


class TeacherInvitationEmailServiceTest(MessagingTestBase):
    """Test cases for TeacherInvitationEmailService."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create test invitation using base class utility
        self.invitation = self.create_teacher_invitation(
            email="teacher@test.com",
            custom_message="Welcome to our team!",
            expires_in_days=7
        )
    
    def test_successful_invitation_email_sending_includes_all_required_content(self):
        """Test business rule: successful invitation emails contain all required information for teacher onboarding."""
        # Clear the test outbox
        mail.outbox = []
        
        # Business action: send invitation email
        result = TeacherInvitationEmailService.send_invitation_email(self.invitation)
        
        # Business rule: service reports success with clear status
        self.assertTrue(result['success'])
        self.assertEqual(result['email'], 'teacher@test.com')
        self.assertIn('Email sent successfully', result['message'])
        
        # Business rule: email is actually sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        
        # Business rule: email has proper metadata
        expected_subject = f"Teacher Invitation: Join {self.school.name} on Aprende Comigo"
        self.assertEqual(sent_email.subject, expected_subject)
        self.assertEqual(sent_email.to, ['teacher@test.com'])
        self.assertEqual(sent_email.from_email, settings.DEFAULT_FROM_EMAIL)
        
        # Business rule: email contains essential onboarding information
        self._assert_email_contains_required_content(sent_email)
    
    def _assert_email_contains_required_content(self, sent_email):
        """Helper method to verify email contains all required content."""
        email_body = sent_email.body
        
        # Essential business information
        self.assertIn(self.school.name, email_body)
        self.assertIn("Welcome to our team!", email_body)  # Custom message
        self.assertIn("Test Admin", email_body)  # Invited by name 
        self.assertIn("accept-teacher-invitation", email_body)  # Invitation link
        
        # HTML version also contains required content
        self.assertIsNotNone(sent_email.alternatives)
        html_content = sent_email.alternatives[0][0]
        self.assertIn(self.school.name, html_content)
        self.assertIn("Welcome to our team!", html_content)
    
    def test_email_template_context_includes_all_business_variables(self):
        """Test business rule: email templates receive complete context for personalized invitations."""
        mail.outbox = []
        
        # Create invitation with all optional fields
        invitation_with_all_fields = self.create_teacher_invitation(
            email="teacher2@test.com",
            custom_message="Join our excellent teaching team!",
            expires_in_days=14
        )
        
        result = TeacherInvitationEmailService.send_invitation_email(invitation_with_all_fields)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        sent_email = mail.outbox[0]
        email_body = sent_email.body
        
        # Business rule: all context variables are properly rendered
        required_context_elements = [
            self.school.name,
            self.school.description, 
            "Teacher",  # Role display
            "Join our excellent teaching team!",  # Custom message
            "Test Admin",  # Invited by name
            "admin@testschool.com",  # Invited by email
            "teacher2@test.com",  # Recipient email
            "accept-teacher-invitation",  # Invitation link
        ]
        
        for element in required_context_elements:
            with self.subTest(element=element):
                self.assertIn(element, email_body)
    
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
    
    def test_bulk_invitation_processing_handles_multiple_teachers_systematically(self):
        """Test business rule: bulk processing efficiently handles multiple teacher invitations with proper state tracking."""
        mail.outbox = []
        
        # Business scenario: school wants to invite multiple teachers at once
        invitations = [
            self.create_teacher_invitation(email=f"teacher{i}@test.com", expires_in_days=7)
            for i in range(3)
        ]
        
        # Business action: process bulk invitations
        result = TeacherInvitationEmailService.send_bulk_invitation_emails(invitations)
        
        # Business rule: service provides complete processing summary
        self.assertEqual(result['total_invitations'], 3)
        self.assertEqual(result['successful_emails'], 3)
        self.assertEqual(result['failed_emails'], 0)
        
        # Business rule: all emails are physically sent
        self.assertEqual(len(mail.outbox), 3)
        
        # Business rule: invitation states are updated after processing
        self._assert_invitations_properly_processed(invitations)
    
    def _assert_invitations_properly_processed(self, invitations):
        """Helper method to verify invitations are properly processed."""
        for invitation in invitations:
            invitation.refresh_from_db()
            self.assertEqual(invitation.email_delivery_status, EmailDeliveryStatus.SENT)
            self.assertEqual(invitation.status, InvitationStatus.SENT)
            self.assertIsNotNone(invitation.email_sent_at)
    
    @patch('common.messaging.TeacherInvitationEmailService.send_invitation_email')
    def test_bulk_processing_resilience_continues_despite_individual_failures(self, mock_send_invitation):
        """Test business rule: bulk processing is resilient and continues processing even when some individual invitations fail."""
        # Business scenario: multiple invitations with some delivery issues
        invitations = [
            self.create_teacher_invitation(email=f"teacher{i}@test.com", expires_in_days=7)
            for i in range(3)
        ]
        
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
        
        # Business rule: service tracks which invitations failed for follow-up
        self.assertIn('teacher1@test.com', result['failed_emails_list'])
        self.assertIn('teacher0@test.com', result['successful_emails_list'])
        self.assertIn('teacher2@test.com', result['successful_emails_list'])
    
    def test_retry_mechanism_handles_temporary_failures_with_proper_state_management(self):
        """Test business rule: failed invitations can be retried with proper state tracking to ensure delivery."""
        mail.outbox = []
        
        # Business scenario: invitation failed due to temporary infrastructure issue
        self._setup_failed_invitation_state()
        
        # Business action: retry failed invitation
        result = TeacherInvitationEmailService.retry_failed_invitation_email(self.invitation)
        
        # Business rule: successful retry sends email and resets failure state
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        self._assert_successful_retry_state_reset()
    
    def _setup_failed_invitation_state(self):
        """Helper method to set up invitation in failed state."""
        self.invitation.email_delivery_status = EmailDeliveryStatus.FAILED
        self.invitation.retry_count = 1
        self.invitation.email_failure_reason = "Previous SMTP error"
        self.invitation.save()
    
    def _assert_successful_retry_state_reset(self):
        """Helper method to verify successful retry resets failure tracking."""
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.email_delivery_status, EmailDeliveryStatus.SENT)
        self.assertEqual(self.invitation.retry_count, 0)  # Reset on success
        self.assertIsNone(self.invitation.email_failure_reason)
    
    def test_retry_limit_prevents_infinite_retry_loops(self):
        """Test business rule: retry attempts are limited to prevent infinite loops and resource waste."""
        # Business scenario: invitation has reached maximum retry limit
        self._setup_max_retry_reached_state()
        
        # Business action: attempt to retry beyond limit
        result = TeacherInvitationEmailService.retry_failed_invitation_email(self.invitation)
        
        # Business rule: service prevents excessive retry attempts
        self.assertFalse(result['success'])
        self.assertIn('Maximum retry attempts', result['error'])
        self.assertEqual(result['retry_count'], 3)
    
    def _setup_max_retry_reached_state(self):
        """Helper method to set up invitation that has reached max retries."""
        self.invitation.email_delivery_status = EmailDeliveryStatus.FAILED
        self.invitation.retry_count = 3
        self.invitation.max_retries = 3
        self.invitation.save()
    
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

