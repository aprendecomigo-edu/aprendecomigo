from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from knox.models import AuthToken

from accounts.models import CustomUser, School, SchoolMembership


class TestUserOnboardingView(TestCase):
    """Test suite for the UserOnboardingView."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = APIClient()
        
        # Create a test user
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            name='Test User',
        )
        
        # Create a default school for the user
        self.school = School.objects.create(
            name='Test School',
            description='Default test school',
            contact_email=self.user.email
        )
        
        # Create school membership
        self.membership = SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role='school_owner',
            is_active=True
        )
        
        # Create auth token for the user
        _, self.token = AuthToken.objects.create(self.user)
        
        # Set up auth header
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        
        # URL for onboarding
        self.url = reverse('user_onboarding')
    
    def test_onboarding_authentication_required(self):
        """Test that authentication is required."""
        # Clear credentials
        self.client.credentials()
        
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_user_only(self):
        """Test updating only user information."""
        data = {
            'user': {
                'name': 'Updated User Name',
                'phone_number': '+1234567890'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Onboarding completed successfully')
        
        # Verify user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated User Name')
        self.assertEqual(self.user.phone_number, '+1234567890')
        
        # Verify school remains unchanged
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'Test School')
    
    def test_update_school_only(self):
        """Test updating only school information."""
        data = {
            'school': {
                'name': 'Updated School Name',
                'description': 'Updated description',
                'website': 'https://example.com'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Onboarding completed successfully')
        
        # Verify school was updated
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'Updated School Name')
        self.assertEqual(self.school.description, 'Updated description')
        self.assertEqual(self.school.website, 'https://example.com')
        
        # Verify user remains unchanged
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Test User')
    
    def test_update_both_user_and_school(self):
        """Test updating both user and school information."""
        data = {
            'user': {
                'name': 'Updated User Name',
                'phone_number': '+1234567890'
            },
            'school': {
                'name': 'Updated School Name',
                'description': 'Updated description',
                'website': 'https://example.com'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Onboarding completed successfully')
        
        # Verify user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated User Name')
        self.assertEqual(self.user.phone_number, '+1234567890')
        
        # Verify school was updated
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'Updated School Name')
        self.assertEqual(self.school.description, 'Updated description')
        self.assertEqual(self.school.website, 'https://example.com')
    
    def test_empty_request(self):
        """Test empty request body."""
        response = self.client.post(self.url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("At least one of 'user' or 'school' information must be provided", 
                     str(response.data))
    
    def test_invalid_user_data(self):
        """Test with invalid user data."""
        data = {
            'user': {
                'name': '',  # Empty name is invalid
                'phone_number': '+1234567890'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', str(response.data))
    
    def test_invalid_school_data(self):
        """Test with invalid school data."""
        data = {
            'school': {
                'name': 'Valid School Name',
                'contact_email': 'invalid-email'  # Invalid email
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('contact_email', str(response.data))
    
    def test_create_school_if_none_exists(self):
        """Test school creation if user doesn't have one."""
        # Delete existing membership and school
        self.membership.delete()
        self.school.delete()
        
        data = {
            'school': {
                'name': 'New School',
                'description': 'Brand new school',
                'website': 'https://example.com'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Onboarding completed successfully')
        
        # Verify a new school was created
        self.assertEqual(School.objects.count(), 1)
        new_school = School.objects.first()
        self.assertEqual(new_school.name, 'New School')
        
        # Verify a new membership was created
        self.assertEqual(SchoolMembership.objects.count(), 1)
        new_membership = SchoolMembership.objects.first()
        self.assertEqual(new_membership.user, self.user)
        self.assertEqual(new_membership.school, new_school)
        self.assertEqual(new_membership.role, 'school_owner')
    
    def test_response_format(self):
        """Test the response format contains all expected fields."""
        data = {
            'user': {
                'name': 'Updated User Name'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('schools', response.data)
        
        # Check user data in response
        user_data = response.data['user']
        self.assertEqual(user_data['name'], 'Updated User Name')
        self.assertIn('roles', user_data)
        
        # Check roles data
        roles = user_data['roles']
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0]['role'], 'school_owner')
        
        # Check schools data
        schools = response.data['schools']
        self.assertEqual(len(schools), 1)
        self.assertEqual(schools[0]['name'], 'Test School') 