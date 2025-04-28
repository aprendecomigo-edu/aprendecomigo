from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

from accounts.models import CustomUser, School, SchoolMembership, EmailVerificationCode
from accounts.views import UserCreateView




class TestUserCreateView(TestCase):
    """Test suite for the UserCreateView (signup without authentication)."""

    def setUp(self):
        """Set up test environment."""
        self.client = APIClient()
        self.url = reverse('user_create')

        # Store original throttle classes and disable throttling for tests
        self.patcher = patch('accounts.views.EmailCodeRequestThrottle.allow_request', return_value=True)
        self.patcher.start()
        self.original_throttle_classes = UserCreateView.throttle_classes
        UserCreateView.throttle_classes = []

    def tearDown(self):
        """Clean up test environment."""
        # Restore original throttle classes
        UserCreateView.throttle_classes = self.original_throttle_classes
        self.patcher.stop()

    @patch('accounts.views.send_mail')
    def test_create_user_success(self, mock_send_mail):
        """Test successful user creation with all required fields."""
        data = {
            'name': 'New User',
            'email': 'newuser@example.com',
            'phone_number': '+1234567890',
            'primary_contact': 'email',
            'school': {
                'name': 'New School'
            }
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('school', response.data)

        # Verify user was created in database
        user = CustomUser.objects.get(email='newuser@example.com')
        self.assertEqual(user.name, 'New User')
        self.assertEqual(user.phone_number, '+1234567890')
        self.assertEqual(user.primary_contact, 'email')
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)

        # Verify school was created
        school = School.objects.get(name='New School')
        self.assertIsNotNone(school)

        # Verify school membership was created
        membership = SchoolMembership.objects.get(user=user, school=school)
        self.assertEqual(membership.role, 'school_owner')
        self.assertTrue(membership.is_active)

        # Verify verification code was created
        verification = EmailVerificationCode.objects.filter(email='newuser@example.com').first()
        self.assertIsNotNone(verification)

        # Verify email would have been sent
        mock_send_mail.assert_called_once()

    def test_create_user_existing_email(self):
        """Test user creation with an email that already exists."""
        # Create a user first
        CustomUser.objects.create_user(
            email='existing@example.com',
            name='Existing User',
        )

        data = {
            'name': 'New User',
            'email': 'existing@example.com',  # Already exists
            'phone_number': '+1234567890',
            'primary_contact': 'email'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('already exists', response.data['error'])

    def test_create_user_invalid_phone(self):
        """Test user creation with invalid phone number format."""
        data = {
            'name': 'New User',
            'email': 'newuser@example.com',
            'phone_number': 'not-a-phone-number',  # Invalid format
            'primary_contact': 'email'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', str(response.data))

    def test_create_user_phone_as_primary(self):
        """Test user creation with phone as the primary contact."""
        with patch('accounts.views.send_mail') as mock_send_mail:
            data = {
                'name': 'Phone User',
                'email': 'phoneuser@example.com',
                'phone_number': '+1234567890',
                'primary_contact': 'phone'
            }

            response = self.client.post(self.url, data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Verify user was created with phone as primary
            user = CustomUser.objects.get(email='phoneuser@example.com')
            self.assertEqual(user.primary_contact, 'phone')

            # Verify code was sent
            mock_send_mail.assert_called_once()

    def test_create_user_invalid_school_data(self):
        """Test user creation with invalid school data."""
        data = {
            'name': 'New User',
            'email': 'newuser@example.com',
            'phone_number': '+1234567890',
            'primary_contact': 'email',
            'school': {
                'name': '',  # Invalid - empty name
                'website': 'not-a-url'  # Invalid URL
            }
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('school', str(response.data))

    def test_create_user_no_school_data(self):
        """Test user creation without providing school data (default school should be created)."""
        with patch('accounts.views.send_mail') as mock_send_mail:
            data = {
                'name': 'No School User',
                'email': 'noschool@example.com',
                'phone_number': '+1234567890',
                'primary_contact': 'email'
            }

            response = self.client.post(self.url, data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Verify default school was created
            user = CustomUser.objects.get(email='noschool@example.com')
            schools = School.objects.filter(memberships__user=user, memberships__role='school_owner')

            self.assertEqual(schools.count(), 1)
            self.assertEqual(schools[0].name, "No School User's School")
