"""
Security tests for the Teacher Invitation System.

This test suite covers critical security vulnerabilities that were identified and fixed:
1. XSS prevention in email templates
2. Rate limiting protection
3. Token security validation
4. Input sanitization
5. Proper error handling without information leakage

Following TDD principles to ensure security fixes work correctly.
"""

import uuid
import time
from datetime import timedelta
from unittest.mock import patch, MagicMock

import pytest
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from knox.models import AuthToken

from accounts.models import (
    CustomUser, 
    School, 
    SchoolMembership, 
    SchoolRole,
    TeacherInvitation, 
    InvitationStatus, 
    EmailDeliveryStatus
)
from common.messaging import TeacherInvitationEmailService


class TeacherInvitationSecurityTest(TestCase):
    """Test cases for security vulnerabilities in teacher invitation system."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test school
        self.school = School.objects.create(
            name="Test School <script>alert('xss')</script>",
            description="School with potentially malicious content <img src=x onerror=alert('xss')>",
            contact_email="admin@testschool.com"
        )
        
        # Create school admin user
        self.school_admin = CustomUser.objects.create_user(
            email="admin@testschool.com",
            name="School Admin <script>alert('admin')</script>",
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
        
        # API endpoints
        self.bulk_invite_url = '/api/accounts/teachers/invite-bulk/'
        self.individual_invite_url = '/api/accounts/teachers/invite-existing/'
    
    def test_xss_prevention_in_email_templates(self):
        """Test that email templates properly escape malicious content."""
        mail.outbox = []
        
        # Create invitation with malicious content
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@test.com",
            invited_by=self.school_admin,
            role=SchoolRole.TEACHER,
            custom_message="<script>alert('xss')</script>Welcome! <img src=x onerror=alert('evil')>",
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Send invitation email
        result = TeacherInvitationEmailService.send_invitation_email(invitation)
        
        # Verify email was sent successfully
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        sent_email = mail.outbox[0]
        
        # Check both text and HTML versions
        email_body = sent_email.body
        html_content = sent_email.alternatives[0][0] if sent_email.alternatives else ""
        
        # Verify malicious scripts are escaped/removed in text version
        self.assertNotIn('<script>', email_body)
        self.assertNotIn('alert(', email_body)
        self.assertNotIn('onerror=', email_body)
        self.assertIn('Welcome!', email_body)  # Legitimate content should remain
        
        # Verify malicious scripts are escaped in HTML version
        self.assertNotIn('<script>', html_content)
        self.assertNotIn('alert(', html_content)
        self.assertNotIn('onerror=', html_content)
        self.assertIn('Welcome!', html_content)  # Legitimate content should remain
        
        # Verify school name and description are also escaped
        self.assertNotIn('<script>alert(\'xss\')</script>', email_body)
        self.assertNotIn('<img src=x onerror=alert(\'xss\')>', email_body)
    
    def test_token_security_cryptographic_strength(self):
        """Test that invitation tokens use cryptographically secure generation."""
        # Create multiple invitations to test token uniqueness and security
        invitations = []
        tokens = set()
        
        for i in range(10):
            invitation = TeacherInvitation.objects.create(
                school=self.school,
                email=f"teacher{i}@test.com",
                invited_by=self.school_admin,
                role=SchoolRole.TEACHER,
                batch_id=uuid.uuid4(),
                expires_at=timezone.now() + timedelta(days=7)
            )
            invitations.append(invitation)
            tokens.add(invitation.token)
        
        # Verify all tokens are unique
        self.assertEqual(len(tokens), 10)
        
        # Verify tokens are 64 characters (32 bytes hex)
        for invitation in invitations:
            self.assertEqual(len(invitation.token), 64)
            # Verify token contains only hexadecimal characters
            self.assertTrue(all(c in '0123456789abcdef' for c in invitation.token))
        
        # Verify tokens are not predictable (no patterns)
        token_list = list(tokens)
        for i in range(len(token_list) - 1):
            # Tokens should not have common prefixes (indicating predictable generation)
            common_prefix_length = 0
            for j in range(min(len(token_list[i]), len(token_list[i+1]))):
                if token_list[i][j] == token_list[i+1][j]:
                    common_prefix_length += 1
                else:
                    break
            # Should not have more than 2 common characters (very unlikely with secure random)
            self.assertLessEqual(common_prefix_length, 2)
    
    @patch('common.throttles.BulkInvitationThrottle.allow_request')
    def test_rate_limiting_bulk_invitations(self, mock_throttle):
        """Test that bulk invitation endpoint is properly rate limited."""
        # Test when rate limit is exceeded
        mock_throttle.return_value = False
        
        invitation_data = {
            'school_id': self.school.id,
            'invitations': [{'email': 'teacher@example.com'}]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        # Should be throttled
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Test when rate limit is not exceeded
        mock_throttle.return_value = True
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        # Should succeed (or fail for other reasons, but not throttling)
        self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    @patch('common.throttles.IndividualInvitationThrottle.allow_request')
    def test_rate_limiting_individual_invitations(self, mock_throttle):
        """Test that individual invitation endpoint is properly rate limited."""
        # Test when rate limit is exceeded
        mock_throttle.return_value = False
        
        invitation_data = {
            'school_id': self.school.id,
            'email': 'teacher@example.com'
        }
        
        response = self.client.post(self.individual_invite_url, invitation_data, format='json')
        
        # Should be throttled
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Test when rate limit is not exceeded
        mock_throttle.return_value = True
        
        response = self.client.post(self.individual_invite_url, invitation_data, format='json')
        
        # Should succeed (or fail for other reasons, but not throttling)
        self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_input_sanitization_custom_message(self):
        """Test that custom messages are properly sanitized."""
        malicious_payloads = [
            "<script>alert('xss')</script>Hello!",
            "<img src=x onerror=alert('xss')>Welcome",
            "<div onclick='alert(\"evil\")'>Click me</div>",
            "<iframe src='javascript:alert(1)'></iframe>Normal text",
            "Hello <b onclick='alert(1)'>bold</b> text",
        ]
        
        for payload in malicious_payloads:
            invitation_data = {
                'school_id': self.school.id,
                'custom_message': payload,
                'invitations': [{'email': 'teacher@example.com'}]
            }
            
            response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
            
            # Request should succeed (sanitization happens, doesn't reject)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_207_MULTI_STATUS])
            
            # Check that the created invitation has sanitized content
            if response.status_code in [status.HTTP_201_CREATED, status.HTTP_207_MULTI_STATUS]:
                batch_id = response.data.get('batch_id')
                if batch_id:
                    invitation = TeacherInvitation.objects.filter(batch_id=batch_id).first()
                    if invitation and invitation.custom_message:
                        # Verify dangerous content was removed
                        self.assertNotIn('<script>', invitation.custom_message)
                        self.assertNotIn('onerror=', invitation.custom_message)
                        self.assertNotIn('onclick=', invitation.custom_message)
                        self.assertNotIn('javascript:', invitation.custom_message)
                        # Verify legitimate content remains
                        self.assertTrue(
                            'Hello' in invitation.custom_message or 
                            'Welcome' in invitation.custom_message or 
                            'Click me' in invitation.custom_message or
                            'Normal text' in invitation.custom_message or
                            'bold' in invitation.custom_message
                        )
    
    def test_bulk_operations_transaction_integrity(self):
        """Test that bulk operations maintain transaction integrity."""
        # Create an existing invitation to cause a conflict
        TeacherInvitation.objects.create(
            school=self.school,
            email='existing@example.com',
            invited_by=self.school_admin,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        invitation_data = {
            'school_id': self.school.id,
            'invitations': [
                {'email': 'valid1@example.com'},
                {'email': 'valid2@example.com'},
                {'email': 'existing@example.com'},  # This will fail
                {'email': 'valid3@example.com'},
            ]
        }
        
        initial_count = TeacherInvitation.objects.count()
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        # Should return partial success
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        
        # Verify that successful invitations were created despite one failure
        final_count = TeacherInvitation.objects.count()
        self.assertEqual(final_count, initial_count + 3)  # 3 successful + 1 existing
        
        # Verify response contains error details
        self.assertEqual(response.data['successful_invitations'], 3)
        self.assertEqual(response.data['failed_invitations'], 1)
        self.assertEqual(len(response.data['errors']), 1)
        self.assertIn('existing@example.com', str(response.data['errors']))
    
    def test_error_handling_information_leakage_prevention(self):
        """Test that error messages don't leak sensitive information."""
        # Test with non-existent school
        invitation_data = {
            'school_id': 99999,
            'invitations': [{'email': 'teacher@example.com'}]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Error should be generic, not revealing internal details
        self.assertIn('school_id', response.data)
        self.assertNotIn('SELECT', str(response.data))  # No SQL queries exposed
        self.assertNotIn('Django', str(response.data))  # No framework details
        
        # Test with unauthorized access
        other_user = CustomUser.objects.create_user(
            email="other@example.com",
            name="Other User"
        )
        other_token = AuthToken.objects.create(other_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token}')
        
        invitation_data = {
            'school_id': self.school.id,
            'invitations': [{'email': 'teacher@example.com'}]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Error should not reveal details about the school
        error_message = str(response.data)
        self.assertNotIn(self.school.name, error_message)
        self.assertNotIn('admin@testschool.com', error_message)
    
    def test_bulk_update_efficiency_prevents_n_plus_1(self):
        """Test that bulk operations use efficient database queries."""
        with self.assertNumQueries(10):  # Should be roughly constant regardless of invitation count
            invitation_data = {
                'school_id': self.school.id,
                'send_email': True,  # This triggers the bulk update optimization
                'invitations': [{'email': f'teacher{i}@example.com'} for i in range(10)]
            }
            
            # Mock email sending to avoid external dependencies
            with patch('common.messaging.send_mail') as mock_send:
                mock_send.return_value = True
                response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['successful_invitations'], 10)
    
    def test_permission_checks_prevent_unauthorized_access(self):
        """Test that proper permission checks prevent unauthorized invitation creation."""
        # Create a user who is not a school admin
        regular_user = CustomUser.objects.create_user(
            email="regular@example.com",
            name="Regular User"
        )
        regular_token = AuthToken.objects.create(regular_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {regular_token}')
        
        invitation_data = {
            'school_id': self.school.id,
            'invitations': [{'email': 'teacher@example.com'}]
        }
        
        response = self.client.post(self.bulk_invite_url, invitation_data, format='json')
        
        # Should be forbidden
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Should not have created any invitations
        invitation_count = TeacherInvitation.objects.filter(school=self.school).count()
        self.assertEqual(invitation_count, 0)
    
    def test_email_template_context_security(self):
        """Test that email template context variables are properly secured."""
        # Create invitation with various potentially dangerous content
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@test.com",
            invited_by=self.school_admin,
            role=SchoolRole.TEACHER,
            custom_message="Normal message with <b>bold</b> text",
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        mail.outbox = []
        result = TeacherInvitationEmailService.send_invitation_email(invitation)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        sent_email = mail.outbox[0]
        
        # Verify that all template variables are present and safe
        email_body = sent_email.body
        html_content = sent_email.alternatives[0][0] if sent_email.alternatives else ""
        
        # Check that dangerous school content is escaped
        self.assertNotIn('<script>alert(\'xss\')</script>', email_body)
        self.assertNotIn('<img src=x onerror=alert(\'xss\')>', email_body)
        
        # Check that user name is escaped
        self.assertNotIn('<script>alert(\'admin\')</script>', email_body)
        
        # Verify legitimate content is preserved
        self.assertIn(self.school_admin.email, email_body)
        self.assertIn('teacher@test.com', email_body)
        self.assertIn('Normal message', email_body)


@pytest.mark.django_db
class TeacherInvitationSecurityIntegrationTest:
    """Integration tests for security features across the invitation system."""
    
    def test_end_to_end_security_validation(self):
        """Test complete security validation from API to email generation."""
        # Setup
        school = School.objects.create(
            name="Integration Test School",
            contact_email="admin@integration.com"
        )
        
        admin_user = CustomUser.objects.create_user(
            email="admin@integration.com",
            name="Integration Admin"
        )
        
        SchoolMembership.objects.create(
            user=admin_user,
            school=school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        client = APIClient()
        token = AuthToken.objects.create(admin_user)[1]
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Test with mixed legitimate and malicious content
        invitation_data = {
            'school_id': school.id,
            'custom_message': 'Welcome to our team! <script>alert("xss")</script> We are excited to have you.',
            'invitations': [
                {'email': 'legitimate@example.com'},
                {'email': 'another@example.com'},
            ]
        }
        
        # Clear email outbox
        mail.outbox = []
        
        # Make request
        response = client.post('/api/accounts/teachers/invite-bulk/', invitation_data, format='json')
        
        # Verify API response
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['successful_invitations'] == 2
        assert response.data['failed_invitations'] == 0
        
        # Verify invitations were created with sanitized content
        batch_id = response.data['batch_id']
        invitations = TeacherInvitation.objects.filter(batch_id=batch_id)
        assert invitations.count() == 2
        
        for invitation in invitations:
            # Custom message should be sanitized
            assert '<script>' not in invitation.custom_message
            assert 'Welcome to our team!' in invitation.custom_message
            assert 'We are excited to have you.' in invitation.custom_message
            
            # Token should be cryptographically secure
            assert len(invitation.token) == 64
            assert all(c in '0123456789abcdef' for c in invitation.token)
        
        # If emails were sent, verify they are safe
        if len(mail.outbox) > 0:
            for email in mail.outbox:
                email_content = email.body
                html_content = email.alternatives[0][0] if email.alternatives else ""
                
                # Verify no malicious content in emails
                assert '<script>' not in email_content
                assert 'alert(' not in email_content
                assert '<script>' not in html_content
                assert 'alert(' not in html_content
                
                # Verify legitimate content is present
                assert 'Welcome to our team!' in email_content
                assert school.name in email_content