"""
Tests for Communication API endpoints.
Following TDD methodology - these tests should fail initially.
"""

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


class CommunicationAPITestCase(APITestCase):
    """Base test case for communication API tests."""
    
    def setUp(self):
        """Set up test data."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com"
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
        
        # Create test email template
        self.email_template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.INVITATION,
            name="Welcome Teacher Template",
            subject_template="Welcome to {{school_name}}!",
            html_content="<p>Welcome {{teacher_name}} to {{school_name}}!</p>",
            text_content="Welcome {{teacher_name}} to {{school_name}}!",
            created_by=self.school_admin
        )
        
        # Create test email sequence
        self.email_sequence = EmailSequence.objects.create(
            school=self.school,
            name="Teacher Onboarding Sequence",
            description="Automated teacher onboarding emails",
            is_active=True,
            trigger_event="invitation_sent"
        )
        
        # Create test sequence step
        self.sequence_step = EmailSequenceStep.objects.create(
            sequence=self.email_sequence,
            step_number=1,
            template=self.email_template,
            delay_hours=0
        )
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.auth_token}')


class SchoolEmailTemplateAPITest(CommunicationAPITestCase):
    """Tests for SchoolEmailTemplate API endpoints."""
    
    def test_list_email_templates(self):
        """Test listing email templates for a school."""
        url = reverse('accounts:email-templates-list')
        response = self.client.get(url)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Welcome Teacher Template")
    
    def test_create_email_template(self):
        """Test creating a new email template."""
        url = reverse('accounts:email-templates-list')
        data = {
            'template_type': EmailTemplateType.WELCOME,
            'name': 'New Welcome Template',
            'subject_template': 'Welcome {{teacher_name}}!',
            'html_content': '<h1>Welcome {{teacher_name}}!</h1>',
            'text_content': 'Welcome {{teacher_name}}!',
            'use_school_branding': True
        }
        
        response = self.client.post(url, data, format='json')
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Welcome Template')
    
    def test_retrieve_email_template(self):
        """Test retrieving a specific email template."""
        url = reverse('accounts:email-templates-detail', kwargs={'pk': self.email_template.pk})
        response = self.client.get(url)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Welcome Teacher Template")
    
    def test_update_email_template(self):
        """Test updating an email template."""
        url = reverse('accounts:email-templates-detail', kwargs={'pk': self.email_template.pk})
        data = {
            'name': 'Updated Template Name',
            'subject_template': 'Updated subject for {{teacher_name}}!'
        }
        
        response = self.client.patch(url, data, format='json')
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Template Name')
    
    def test_delete_email_template(self):
        """Test deleting an email template."""
        url = reverse('accounts:email-templates-detail', kwargs={'pk': self.email_template.pk})
        response = self.client.delete(url)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_email_template_preview(self):
        """Test previewing an email template with variables."""
        url = reverse('accounts:email-templates-preview', kwargs={'pk': self.email_template.pk})
        data = {
            'template_variables': {
                'teacher_name': 'John Doe',
                'school_name': 'Amazing School'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rendered_subject', response.data)
        self.assertIn('rendered_html', response.data)
        self.assertIn('rendered_text', response.data)


class EmailSequenceAPITest(CommunicationAPITestCase):
    """Tests for EmailSequence API endpoints."""
    
    def test_list_email_sequences(self):
        """Test listing email sequences for a school."""
        url = reverse('accounts:email-sequences-list')
        response = self.client.get(url)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Teacher Onboarding Sequence")
    
    def test_create_email_sequence(self):
        """Test creating a new email sequence."""
        url = reverse('accounts:email-sequences-list')
        data = {
            'name': 'Student Welcome Sequence',
            'description': 'Welcome sequence for new students',
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Student Welcome Sequence')
    
    def test_retrieve_email_sequence(self):
        """Test retrieving a specific email sequence."""
        url = reverse('accounts:email-sequences-detail', kwargs={'pk': self.email_sequence.pk})
        response = self.client.get(url)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Teacher Onboarding Sequence")
    
    def test_activate_email_sequence(self):
        """Test activating/deactivating an email sequence."""
        url = reverse('accounts:email-sequences-activate', kwargs={'pk': self.email_sequence.pk})
        data = {'is_active': False}
        
        response = self.client.post(url, data, format='json')
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_active'], False)


class EmailCommunicationAPITest(CommunicationAPITestCase):  
    """Tests for EmailCommunication API endpoints."""
    
    def setUp(self):
        super().setUp()
        
        # Create test communication record
        self.email_communication = EmailCommunication.objects.create(
            school=self.school,
            recipient_email="teacher@example.com",
            communication_type=EmailCommunicationType.MANUAL,
            subject="Welcome to our school!",
            html_content="<p>Welcome!</p>",
            text_content="Welcome!",
            sent_by=self.school_admin
        )
    
    def test_list_email_communications(self):
        """Test listing email communications for a school."""
        url = reverse('accounts:email-communications-list')
        response = self.client.get(url)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['recipient_email'], "teacher@example.com")
    
    def test_retrieve_email_communication(self):
        """Test retrieving a specific email communication."""
        url = reverse('accounts:email-communications-detail', kwargs={'pk': self.email_communication.pk})
        response = self.client.get(url)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['recipient_email'], "teacher@example.com")
    
    def test_email_communications_analytics(self):
        """Test getting email communication analytics."""
        url = reverse('accounts:email-communications-analytics')
        response = self.client.get(url)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sent', response.data)
        self.assertIn('delivery_rate', response.data)
        self.assertIn('open_rate', response.data)


class CommunicationPermissionsTest(CommunicationAPITestCase):
    """Tests for communication API permissions."""
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users can't access communication APIs."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('accounts:email-templates-list')
        response = self.client.get(url)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_non_school_member_access_denied(self):
        """Test that users not in the school can't access school communications."""
        # Create another user not in the school
        other_user = CustomUser.objects.create_user(
            email="other@example.com",
            first_name="Other",
            last_name="User"
        )
        other_token = AuthToken.objects.create(other_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token}')
        
        url = reverse('accounts:email-templates-list')
        response = self.client.get(url)
        
        # This should fail initially since endpoint doesn't exist  
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CommunicationAPIFilteringTest(CommunicationAPITestCase):
    """Tests for communication API filtering and search."""
    
    def test_filter_templates_by_type(self):
        """Test filtering email templates by type."""
        url = reverse('accounts:email-templates-list')
        response = self.client.get(url, {'template_type': EmailTemplateType.INVITATION})
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_search_templates_by_name(self):
        """Test searching email templates by name."""
        url = reverse('accounts:email-templates-list')
        response = self.client.get(url, {'search': 'Welcome'})
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_communications_by_date(self):
        """Test filtering communications by date range."""
        url = reverse('accounts:email-communications-list')
        params = {
            'sent_after': '2025-01-01',
            'sent_before': '2025-12-31'
        }
        response = self.client.get(url, params)
        
        # This should fail initially since endpoint doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)