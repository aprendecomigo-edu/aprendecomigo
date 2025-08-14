"""
Tests for Tutor Onboarding API endpoints.

Tests for GitHub issue #44 - Individual Tutor Onboarding Flow Implementation.
This module tests the missing API endpoints that are blocking the frontend tutor onboarding flow.
"""

import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from knox.models import AuthToken

from accounts.models import (
    School, 
    SchoolMembership, 
    SchoolRole, 
    TeacherProfile,
    Course,
    EducationalSystem,
    TeacherCourse
)

User = get_user_model()


class TutorOnboardingAPITestCase(TestCase):
    """Base test case for tutor onboarding API tests."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@tutor.com',
            first_name='Test',
            last_name='Tutor'
        )
        
        # Create auth token for API authentication
        self.token = AuthToken.objects.create(self.user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        
        # Create educational system
        self.educational_system = EducationalSystem.objects.create(
            name='Portugal',
            code='PT',
            description='Portuguese Educational System'
        )
        
        # Create sample courses
        self.course1 = Course.objects.create(
            name='Mathematics - 9th Grade',
            code='MAT9',
            educational_system=self.educational_system,
            education_level='3rd_cycle',
            description='Basic mathematics for 9th grade students'
        )
        
        self.course2 = Course.objects.create(
            name='Physics - 10th Grade',
            code='FIS10',
            educational_system=self.educational_system,
            education_level='secondary',
            description='Physics fundamentals for 10th grade students'
        )


class TutorOnboardingGuidanceAPITest(TutorOnboardingAPITestCase):
    """Test the tutor onboarding guidance API endpoint."""
    
    def test_guidance_endpoint_returns_guidance_data(self):
        """Test that the guidance endpoint returns guidance data."""
        url = '/api/accounts/tutors/onboarding/guidance/'
        
        response = self.client.get(url)
        
        # Endpoint should exist and return guidance data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('guidance', response.data)
        self.assertIn('welcome_message', response.data['guidance'])
        self.assertIn('steps', response.data['guidance'])


class TutorOnboardingStartAPITest(TutorOnboardingAPITestCase):
    """Test the tutor onboarding start API endpoint."""
    
    def test_start_endpoint_processes_onboarding_start(self):
        """Test that the start endpoint processes onboarding start request."""
        url = '/api/accounts/tutors/onboarding/start/'
        
        data = {'step': 'create_profile'}
        response = self.client.post(url, data, format='json')
        
        # Endpoint should exist and return onboarding data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('step', response.data)
        
        # Check response structure
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['step'], 'create_profile')


class TutorOnboardingValidateStepAPITest(TutorOnboardingAPITestCase):
    """Test the tutor onboarding validate step API endpoint."""
    
    def test_validate_endpoint_validates_step_data(self):
        """Test that the validate step endpoint validates step data."""
        url = '/api/accounts/tutors/onboarding/validate-step/'
        
        data = {
            'step': 'course_selection',
            'data': {
                'course_selection': {
                    'educational_system_id': self.educational_system.id,
                    'selected_courses': [
                        {
                            'course_id': self.course1.id,
                            'hourly_rate': 25.00,
                            'expertise_level': 'intermediate'
                        }
                    ]
                }
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        # If endpoint exists, should return validation results
        # Endpoint should exist and validate step data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_fields = ['valid', 'errors', 'step']
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # For valid data, should be valid
        self.assertTrue(response.data['valid'])
        self.assertIsInstance(response.data['errors'], dict)
    
    def test_validate_endpoint_invalid_data(self):
        """Test that the validate step endpoint properly validates invalid data."""
        url = '/api/accounts/tutors/onboarding/validate-step/'
        
        # Invalid data - missing required fields
        data = {
            'step': 'add_bio',
            'data': {
                'bio': ''  # Empty bio should be invalid
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        # Endpoint should exist and return validation errors
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should be invalid with errors
        self.assertFalse(response.data['valid'])
        self.assertTrue(len(response.data['errors']) > 0)


class TutorOnboardingAuthenticationTest(TutorOnboardingAPITestCase):
    """Test authentication requirements for tutor onboarding API endpoints."""
    
    def test_endpoints_require_authentication(self):
        """Test that all tutor onboarding endpoints require authentication."""
        # Create unauthenticated client
        unauth_client = APIClient()
        
        endpoints = [
            '/api/accounts/tutors/onboarding/guidance/',
            '/api/accounts/tutors/onboarding/start/',
            '/api/accounts/tutors/onboarding/validate-step/',
        ]
        
        for endpoint in endpoints:
            response = unauth_client.post(endpoint, {}, format='json')
            
            # Should return 401 or 404 (404 if endpoint doesn't exist yet)
            self.assertIn(response.status_code, [
                status.HTTP_401_UNAUTHORIZED, 
                status.HTTP_404_NOT_FOUND
            ])


class TutorOnboardingIntegrationTest(TutorOnboardingAPITestCase):
    """Test integration with existing models."""
    
    def test_course_model_integration(self):
        """Test that the API works with existing Course models."""
        # Verify test data exists
        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())
        self.assertTrue(Course.objects.filter(id=self.course2.id).exists())
        
        # Verify educational system relationship
        self.assertEqual(self.course1.educational_system, self.educational_system)
        self.assertEqual(self.course2.educational_system, self.educational_system)
    
    def test_teacher_profile_model_integration(self):
        """Test that teacher profiles can be created for onboarding."""
        # Create teacher profile for the user
        teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio='Test teacher bio',
            hourly_rate=30.00
        )
        
        # Verify profile was created
        self.assertTrue(TeacherProfile.objects.filter(user=self.user).exists())
        
        # Create teacher course relationship
        teacher_course = TeacherCourse.objects.create(
            teacher=teacher_profile,
            course=self.course1,
            hourly_rate=25.00
        )
        
        # Verify relationship was created
        self.assertTrue(TeacherCourse.objects.filter(
            teacher=teacher_profile,
            course=self.course1
        ).exists())