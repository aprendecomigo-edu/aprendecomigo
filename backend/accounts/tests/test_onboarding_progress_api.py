"""
Tests for Onboarding Progress API endpoints.
Following TDD methodology - tests written first before implementation.
"""
import json
from datetime import datetime
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import CustomUser, School, SchoolMembership, SchoolRole


class OnboardingProgressAPITestCase(TestCase):
    """Test cases for onboarding progress API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        # Create a school admin user
        self.user = CustomUser.objects.create_user(
            email="admin@testschool.com",
            name="Test Admin",
            onboarding_completed=False,
            onboarding_progress={
                "steps_completed": ["profile"],
                "current_step": "invite_teacher",
                "completion_percentage": 20,
                "skipped": False
            },
            tutorial_preferences={
                "auto_start": True,
                "show_hints": True
            }
        )
        
        # Create school membership
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
    
    def test_get_onboarding_progress_success(self):
        """Test GET /api/accounts/onboarding-progress/ returns current progress."""
        url = reverse('accounts:user-onboarding-progress')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_data = {
            "steps_completed": ["profile"],
            "current_step": "invite_teacher",
            "completion_percentage": 20,
            "skipped": False,
            "completed_at": None,
            "onboarding_completed": False
        }
        
        self.assertEqual(response.json(), expected_data)
    
    def test_get_onboarding_progress_completed_user(self):
        """Test GET progress for user who completed onboarding."""
        # Update user to completed state
        self.user.onboarding_completed = True
        self.user.onboarding_progress = {
            "steps_completed": ["profile", "invite_teacher", "add_student"],
            "current_step": "completed",
            "completion_percentage": 100,
            "skipped": False,
            "completed_at": "2024-01-15T10:30:00Z"
        }
        self.user.save()
        
        url = reverse('accounts:user-onboarding-progress')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data["onboarding_completed"])
        self.assertEqual(data["completion_percentage"], 100)
        self.assertEqual(data["current_step"], "completed")
        self.assertIsNotNone(data["completed_at"])
    
    def test_post_onboarding_progress_update_success(self):
        """Test POST /api/accounts/onboarding-progress/ updates progress."""
        url = reverse('accounts:user-onboarding-progress')
        
        update_data = {
            "steps_completed": ["profile", "invite_teacher"],
            "current_step": "add_student",
            "completion_percentage": 40,
            "skipped": False
        }
        
        response = self.client.post(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        # Check that progress was updated
        self.assertEqual(
            self.user.onboarding_progress["steps_completed"],
            ["profile", "invite_teacher"]
        )
        self.assertEqual(
            self.user.onboarding_progress["current_step"],
            "add_student"
        )
        self.assertEqual(
            self.user.onboarding_progress["completion_percentage"],
            40
        )
    
    def test_post_onboarding_progress_complete_onboarding(self):
        """Test POST completing onboarding sets completed flag."""
        url = reverse('accounts:user-onboarding-progress')
        
        complete_data = {
            "steps_completed": ["profile", "invite_teacher", "add_student"],
            "current_step": "completed",
            "completion_percentage": 100,
            "skipped": False
        }
        
        response = self.client.post(url, complete_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        # Check that onboarding is marked as completed
        self.assertTrue(self.user.onboarding_completed)
        self.assertEqual(self.user.onboarding_progress["completion_percentage"], 100)
        self.assertIsNotNone(self.user.onboarding_progress.get("completed_at"))
    
    def test_post_onboarding_progress_skip_onboarding(self):
        """Test POST skipping onboarding."""
        url = reverse('accounts:user-onboarding-progress')
        
        skip_data = {
            "steps_completed": ["profile"],
            "current_step": "skipped",
            "completion_percentage": 20,
            "skipped": True
        }
        
        response = self.client.post(url, skip_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        # Check that onboarding is marked as skipped but not completed
        self.assertFalse(self.user.onboarding_completed)
        self.assertTrue(self.user.onboarding_progress["skipped"])
        self.assertEqual(self.user.onboarding_progress["current_step"], "skipped")
    
    def test_post_onboarding_progress_invalid_percentage(self):
        """Test POST with invalid completion percentage."""
        url = reverse('accounts:user-onboarding-progress')
        
        invalid_data = {
            "steps_completed": ["profile"],
            "current_step": "invite_teacher",
            "completion_percentage": 150,  # Invalid - over 100
            "skipped": False
        }
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("completion_percentage", str(response.content))
    
    def test_post_onboarding_progress_missing_required_fields(self):
        """Test POST with missing required fields."""
        url = reverse('accounts:user-onboarding-progress')
        
        incomplete_data = {
            "steps_completed": ["profile"],
            # Missing current_step and completion_percentage
        }
        
        response = self.client.post(url, incomplete_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_onboarding_progress_unauthorized(self):
        """Test that unauthenticated users cannot access endpoint."""
        self.client.force_authenticate(user=None)
        
        url = reverse('accounts:user-onboarding-progress')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_onboarding_progress_performance_target(self):
        """Test that API responds within 100ms performance target."""
        import time
        
        url = reverse('accounts:user-onboarding-progress')
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Performance target: <100ms
        response_time_ms = (end_time - start_time) * 1000
        self.assertLess(response_time_ms, 100, f"Response time {response_time_ms:.2f}ms exceeds 100ms target")
    
    def test_onboarding_progress_school_scoped(self):
        """Test that progress is scoped to user's current school context."""
        # Create another school and user
        other_school = School.objects.create(
            name="Other School",
            description="Another school"
        )
        
        other_user = CustomUser.objects.create_user(
            email="other@school.com",
            name="Other User",
            onboarding_progress={"different": "progress"}
        )
        
        SchoolMembership.objects.create(
            user=other_user,
            school=other_school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Test that our user can only see their own progress
        url = reverse('accounts:user-onboarding-progress')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return our user's progress, not other user's
        data = response.json()
        self.assertEqual(data["steps_completed"], ["profile"])
        self.assertNotIn("different", data)