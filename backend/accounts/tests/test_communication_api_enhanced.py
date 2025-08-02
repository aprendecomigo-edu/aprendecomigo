"""
Enhanced tests for Communication API endpoints.
Following TDD methodology - tests written first for the required frontend functionality.
"""

import json
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from knox.models import AuthToken

from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolEmailTemplate, 
    EmailSequence, EmailSequenceStep, EmailCommunication,
    EmailTemplateType, EmailCommunicationType, SchoolRole
)


class CommunicationAPIEnhancedTestCase(APITestCase):
    """Enhanced test case for communication API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create test school with branding
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com",
            primary_color="#3B82F6",
            secondary_color="#10B981",
            text_color="#1F2937",
            background_color="#F9FAFB"
        )
        
        # Create test user (school admin)
        self.school_admin = CustomUser.objects.create_user(
            email="admin@school.com",
            first_name="Admin",
            last_name="User"
        )
        
        # Create school membership
        SchoolMembership.objects.create(
            user=self.school_admin,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Create authentication token
        self.auth_token = AuthToken.objects.create(self.school_admin)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.auth_token}')
        
        # Create test email templates
        self.invitation_template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.INVITATION,
            name="Teacher Invitation",
            subject_template="Join {{school_name}} as a Teacher",
            html_content="<p>Welcome {{teacher_name}} to {{school_name}}!</p>",
            text_content="Welcome {{teacher_name}} to {{school_name}}!",
            created_by=self.school_admin
        )
        
        self.welcome_template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Welcome Message",
            subject_template="Welcome to {{school_name}}!",
            html_content="<p>Welcome {{teacher_name}}!</p>",
            text_content="Welcome {{teacher_name}}!",
            created_by=self.school_admin
        )
        
        # Create test email communication
        self.email_communication = EmailCommunication.objects.create(
            school=self.school,
            recipient_email="teacher@example.com",
            communication_type=EmailCommunicationType.MANUAL,
            template=self.invitation_template,
            subject="Test Subject",
            html_content="<p>Test HTML content</p>",
            text_content="Test text content",
            sent_by=self.school_admin
        )


class TemplateManagementAPITests(CommunicationAPIEnhancedTestCase):
    """Tests for Template Management APIs."""
    
    def test_list_templates(self):
        """Test GET /api/accounts/email-templates/ - List all templates for school."""
        url = reverse('accounts:email-templates-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return templates for the user's school
        self.assertEqual(len(data), 2)
        template_names = [template['name'] for template in data]
        self.assertIn("Teacher Invitation", template_names)
        self.assertIn("Welcome Message", template_names)
    
    def test_create_template(self):
        """Test POST /api/accounts/email-templates/ - Create new template."""
        url = reverse('accounts:email-templates-list')
        data = {
            'school': self.school.id,
            'template_type': EmailTemplateType.REMINDER,
            'name': 'Profile Reminder',
            'subject_template': 'Complete Your Profile - {{school_name}}',
            'html_content': '<p>Hi {{teacher_name}}, please complete your profile.</p>',
            'text_content': 'Hi {{teacher_name}}, please complete your profile.',
            'use_school_branding': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_template = SchoolEmailTemplate.objects.get(name='Profile Reminder')
        self.assertEqual(created_template.school, self.school)
        self.assertEqual(created_template.created_by, self.school_admin)
    
    def test_get_specific_template(self):
        """Test GET /api/accounts/email-templates/{id}/ - Get specific template."""
        url = reverse('accounts:email-templates-detail', kwargs={'pk': self.invitation_template.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['id'], self.invitation_template.id)
        self.assertEqual(data['name'], 'Teacher Invitation')
        self.assertEqual(data['template_type'], EmailTemplateType.INVITATION)
    
    def test_update_template(self):
        """Test PUT /api/accounts/email-templates/{id}/ - Update template."""
        url = reverse('accounts:email-templates-detail', kwargs={'pk': self.invitation_template.id})
        data = {
            'school': self.school.id,
            'template_type': EmailTemplateType.INVITATION,
            'name': 'Updated Teacher Invitation',
            'subject_template': 'Updated: Join {{school_name}} as a Teacher',
            'html_content': '<p>Updated: Welcome {{teacher_name}} to {{school_name}}!</p>',
            'text_content': 'Updated: Welcome {{teacher_name}} to {{school_name}}!',
            'use_school_branding': True
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_template = SchoolEmailTemplate.objects.get(id=self.invitation_template.id)
        self.assertEqual(updated_template.name, 'Updated Teacher Invitation')
    
    def test_delete_template(self):
        """Test DELETE /api/accounts/email-templates/{id}/ - Delete template."""
        url = reverse('accounts:email-templates-detail', kwargs={'pk': self.invitation_template.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SchoolEmailTemplate.objects.filter(id=self.invitation_template.id).exists())


class TemplatePreviewTestingAPITests(CommunicationAPIEnhancedTestCase):
    """Tests for Template Preview & Testing APIs."""
    
    @patch('accounts.services.email_template_service.EmailTemplateRenderingService.render_template')
    def test_template_preview(self):
        """Test POST /api/accounts/email-templates/{id}/preview/ - Generate template preview."""
        url = reverse('accounts:email-templates-preview', kwargs={'pk': self.invitation_template.id})
        data = {
            'variables': {
                'teacher_name': 'John Doe',
                'school_name': 'Test School'
            }
        }
        
        # Mock the rendering service
        mock_rendered = {
            'subject': 'Join Test School as a Teacher',
            'html_content': '<p>Welcome John Doe to Test School!</p>',
            'text_content': 'Welcome John Doe to Test School!'
        }
        
        with patch('accounts.services.email_template_service.EmailTemplateRenderingService.render_template', return_value=mock_rendered):
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['subject'], 'Join Test School as a Teacher')
        self.assertIn('John Doe', data['html_content'])
        self.assertIn('Test School', data['html_content'])
    
    @patch('accounts.services.enhanced_email_service.EnhancedEmailService.send_template_email')
    def test_send_test_email(self):
        """Test POST /api/accounts/email-templates/{id}/send-test/ - Send test email."""
        url = reverse('accounts:email-templates-send-test', kwargs={'pk': self.invitation_template.id})
        data = {
            'test_email': 'test@example.com',
            'variables': {
                'teacher_name': 'John Doe',
                'school_name': 'Test School'
            }
        }
        
        # Mock the email service
        with patch('accounts.services.enhanced_email_service.EnhancedEmailService.send_template_email', return_value=True):
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Test email sent successfully')


class SchoolBrandingAPITests(CommunicationAPIEnhancedTestCase):
    """Tests for School Branding APIs."""
    
    def test_get_school_branding(self):
        """Test GET /api/accounts/communication/branding/ - Get school branding settings."""
        url = reverse('accounts:communication-branding')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['primary_color'], '#3B82F6')
        self.assertEqual(data['secondary_color'], '#10B981')
        self.assertEqual(data['text_color'], '#1F2937')
        self.assertEqual(data['background_color'], '#F9FAFB')
    
    def test_update_school_branding(self):
        """Test PUT /api/accounts/communication/branding/ - Update school branding."""
        url = reverse('accounts:communication-branding')
        data = {
            'primary_color': '#EF4444',
            'secondary_color': '#F59E0B',
            'text_color': '#111827',
            'background_color': '#F3F4F6'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_school = School.objects.get(id=self.school.id)
        self.assertEqual(updated_school.primary_color, '#EF4444')
        self.assertEqual(updated_school.secondary_color, '#F59E0B')


class AnalyticsAPITests(CommunicationAPIEnhancedTestCase):
    """Tests for Analytics APIs."""
    
    def test_get_communication_analytics(self):
        """Test GET /api/accounts/communication/analytics/ - Get email performance metrics."""
        url = reverse('accounts:communication-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return analytics structure
        self.assertIn('total_sent', data)
        self.assertIn('delivery_rate', data)
        self.assertIn('open_rate', data)
        self.assertIn('click_rate', data)
        self.assertIn('recent_communications', data)
    
    def test_get_template_analytics(self):
        """Test GET /api/accounts/communication/analytics/templates/ - Template-specific stats."""
        url = reverse('accounts:communication-analytics-templates')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return template analytics
        self.assertIsInstance(data, list)
        if len(data) > 0:
            template_stats = data[0]
            self.assertIn('template_id', template_stats)
            self.assertIn('template_name', template_stats)
            self.assertIn('usage_count', template_stats)
            self.assertIn('success_rate', template_stats)


class CommunicationSettingsAPITests(CommunicationAPIEnhancedTestCase):
    """Tests for Communication Settings APIs."""
    
    def test_get_communication_settings(self):
        """Test GET /api/accounts/communication/settings/ - Get communication preferences."""
        url = reverse('accounts:communication-settings')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return settings structure
        self.assertIn('default_from_email', data)
        self.assertIn('email_signature', data)
        self.assertIn('auto_sequence_enabled', data)
        self.assertIn('notification_preferences', data)
    
    def test_update_communication_settings(self):
        """Test PUT /api/accounts/communication/settings/ - Update communication settings."""
        url = reverse('accounts:communication-settings')
        data = {
            'default_from_email': 'noreply@testschool.com',
            'email_signature': 'Best regards,\nTest School Team',
            'auto_sequence_enabled': True,
            'notification_preferences': {
                'email_delivery_notifications': True,
                'bounce_notifications': True
            }
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Settings should be saved (implementation will determine storage method)


class PermissionsTestCase(CommunicationAPIEnhancedTestCase):
    """Test permission controls for communication APIs."""
    
    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access APIs."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('accounts:email-templates-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cross_school_template_access(self):
        """Test that users cannot access templates from other schools."""
        # Create another school and template
        other_school = School.objects.create(name="Other School")
        other_template = SchoolEmailTemplate.objects.create(
            school=other_school,
            template_type=EmailTemplateType.WELCOME,
            name="Other School Template",
            subject_template="Welcome to {{school_name}}",
            html_content="<p>Welcome!</p>",
            text_content="Welcome!"
        )
        
        # Try to access other school's template
        url = reverse('accounts:email-templates-detail', kwargs={'pk': other_template.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)