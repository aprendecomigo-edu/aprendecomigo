import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from knox.models import AuthToken

from accounts.models import (
    School, 
    SchoolSettings, 
    SchoolMembership, 
    SchoolRole,
    EducationalSystem,
    CurrencyChoices,
    LanguageChoices,
    TrialCostAbsorption,
    DataRetentionChoices
)
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class SchoolSettingsAPITestCase(BaseTestCase):
    """Test cases for school settings API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Use the default educational system from base class
        self.educational_system = self.default_educational_system
        
        # Create school owner user
        self.owner_user = User.objects.create_user(
            email='owner@school.com',
            name='School Owner',
            password='testpass123'
        )
        
        # Create school admin user
        self.admin_user = User.objects.create_user(
            email='admin@school.com',
            name='School Admin',
            password='testpass123'
        )
        
        # Create regular user (not admin)
        self.regular_user = User.objects.create_user(
            email='user@school.com',
            name='Regular User',
            password='testpass123'
        )
        
        # Create school
        self.school = School.objects.create(
            name='Test School',
            description='A test school',
            contact_email='contact@school.com',
            primary_color='#3B82F6',
            secondary_color='#1F2937'
        )
        
        # Create school settings
        self.school_settings = SchoolSettings.objects.create(
            school=self.school,
            educational_system=self.educational_system,
            grade_levels=['1', '2', '3'],
            trial_cost_absorption=TrialCostAbsorption.SCHOOL,
            currency_code=CurrencyChoices.EUR,
            language=LanguageChoices.PT,
            working_days=[0, 1, 2, 3, 4],
            data_retention_policy=DataRetentionChoices.TWO_YEARS
        )
        
        # Create memberships
        SchoolMembership.objects.create(
            user=self.owner_user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Create auth tokens
        self.owner_token = AuthToken.objects.create(self.owner_user)[1]
        self.admin_token = AuthToken.objects.create(self.admin_user)[1]
        self.regular_token = AuthToken.objects.create(self.regular_user)[1]
    
    def authenticate_as_owner(self):
        """Authenticate as school owner"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token}')
    
    def authenticate_as_admin(self):
        """Authenticate as school admin"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token}')
    
    def authenticate_as_regular_user(self):
        """Authenticate as regular user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.regular_token}')
    
    def test_get_school_settings_as_owner(self):
        """Test getting school settings as school owner"""
        self.authenticate_as_owner()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('school_profile', response.data)
        self.assertIn('settings', response.data)
        
        # Check school profile data
        school_profile = response.data['school_profile']
        self.assertEqual(school_profile['name'], 'Test School')
        self.assertEqual(school_profile['primary_color'], '#3B82F6')
        
        # Check settings data
        settings = response.data['settings']
        self.assertEqual(settings['educational_system'], self.educational_system.id)
        self.assertEqual(settings['currency_code'], CurrencyChoices.EUR)
        self.assertEqual(settings['grade_levels'], ['1', '2', '3'])
    
    def test_get_school_settings_as_admin(self):
        """Test getting school settings as school admin"""
        self.authenticate_as_admin()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('school_profile', response.data)
        self.assertIn('settings', response.data)
    
    def test_get_school_settings_unauthorized(self):
        """Test getting school settings without authorization"""
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_school_settings_forbidden(self):
        """Test getting school settings as regular user (should be not found due to queryset filtering)"""
        self.authenticate_as_regular_user()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        # Regular user gets 404 because they can't see schools they're not members of
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_school_settings_profile_only(self):
        """Test updating only school profile data"""
        self.authenticate_as_owner()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        data = {
            'school_profile': {
                'name': 'Updated School Name',
                'description': 'Updated description',
                'primary_color': '#FF5733',
                'secondary_color': '#C70039'
            }
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the school profile was updated
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'Updated School Name')
        self.assertEqual(self.school.description, 'Updated description')
        self.assertEqual(self.school.primary_color, '#FF5733')
        self.assertEqual(self.school.secondary_color, '#C70039')
    
    def test_update_school_settings_settings_only(self):
        """Test updating only settings data"""
        self.authenticate_as_owner()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        data = {
            'settings': {
                'trial_cost_absorption': TrialCostAbsorption.TEACHER,
                'default_session_duration': 90,
                'currency_code': CurrencyChoices.USD,
                'language': LanguageChoices.EN,
                'email_notifications_enabled': False,
                'grade_levels': ['4', '5', '6']
            }
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the settings were updated
        self.school_settings.refresh_from_db()
        self.assertEqual(self.school_settings.trial_cost_absorption, TrialCostAbsorption.TEACHER)
        self.assertEqual(self.school_settings.default_session_duration, 90)
        self.assertEqual(self.school_settings.currency_code, CurrencyChoices.USD)
        self.assertEqual(self.school_settings.language, LanguageChoices.EN)
        self.assertEqual(self.school_settings.email_notifications_enabled, False)
        self.assertEqual(self.school_settings.grade_levels, ['4', '5', '6'])
    
    def test_update_school_settings_validation_error(self):
        """Test validation errors when updating settings"""
        self.authenticate_as_owner()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        data = {
            'settings': {
                'working_hours_start': '18:00',
                'working_hours_end': '08:00',  # Invalid: end before start
            }
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('working_hours_start', str(response.data))
    
    def test_update_school_settings_invalid_color(self):
        """Test validation error for invalid color format"""
        self.authenticate_as_owner()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        data = {
            'school_profile': {
                'primary_color': 'invalid-color'  # Invalid hex color
            }
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_educational_systems(self):
        """Test getting available educational systems"""
        self.authenticate_as_owner()
        
        url = reverse('accounts:school-educational-systems', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        # Check that at least one educational system exists and that 'Portugal' is among them
        self.assertGreaterEqual(len(response.data), 1)
        portugal_system = next((sys for sys in response.data if sys['code'] == 'pt'), None)
        self.assertIsNotNone(portugal_system, "Portugal educational system should be in the response")
        self.assertEqual(portugal_system['name'], 'Portugal')
    
    def test_update_settings_creates_activity_log(self):
        """Test that updating settings creates an activity log entry"""
        self.authenticate_as_owner()
        
        # Count initial activities
        initial_activity_count = self.school.activities.count()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        data = {
            'school_profile': {
                'name': 'New School Name'
            }
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify activity was created
        final_activity_count = self.school.activities.count()
        self.assertEqual(final_activity_count, initial_activity_count + 1)
        
        # Check the activity details
        activity = self.school.activities.first()
        self.assertEqual(activity.activity_type, 'settings_updated')
        self.assertEqual(activity.actor, self.owner_user)
        self.assertIn('school.name', activity.description)
    
    def test_working_days_validation(self):
        """Test validation of working days array"""
        self.authenticate_as_owner()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        
        # Test valid working days
        data = {
            'settings': {
                'working_days': [0, 1, 2, 3, 4]  # Monday to Friday
            }
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test invalid working days (out of range)
        data = {
            'settings': {
                'working_days': [0, 1, 2, 3, 4, 7]  # 7 is invalid (should be 0-6)
            }
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_grade_levels_validation_with_educational_system(self):
        """Test that grade levels are validated against the educational system"""
        self.authenticate_as_owner()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        
        # This should work with the Portugal system (assuming it has these levels)
        data = {
            'settings': {
                'educational_system': self.educational_system.id,
                'grade_levels': ['1', '2', '3']
            }
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_integration_settings_validation(self):
        """Test validation of integration settings"""
        self.authenticate_as_owner()
        
        url = reverse('accounts:school-school-settings', kwargs={'pk': self.school.id})
        
        # Test that integration type is required when integration is enabled
        data = {
            'settings': {
                'enable_calendar_integration': True,
                'calendar_integration_type': ''  # Should be required
            }
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test valid integration settings
        data = {
            'settings': {
                'enable_calendar_integration': True,
                'calendar_integration_type': 'google'
            }
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)