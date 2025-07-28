"""
Tests for Navigation Preferences API endpoints.
Following TDD methodology - tests written first before implementation.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import CustomUser, School, SchoolMembership, SchoolRole


class NavigationPreferencesAPITestCase(TestCase):
    """Test cases for navigation preferences API endpoints."""
    
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
            tutorial_preferences={
                "quick_actions": ["invite_teacher", "add_student"],
                "default_landing_page": "dashboard",
                "navigation_style": "sidebar",
                "tutorial_auto_start": True
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
    
    def test_get_navigation_preferences_success(self):
        """Test GET /api/accounts/navigation-preferences/ returns current preferences."""
        url = reverse('accounts:user-navigation-preferences')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_data = {
            "quick_actions": ["invite_teacher", "add_student"],
            "default_landing_page": "dashboard",
            "navigation_style": "sidebar",
            "tutorial_auto_start": True
        }
        
        self.assertEqual(response.json(), expected_data)
    
    def test_get_navigation_preferences_empty_defaults(self):
        """Test GET preferences for user with no existing preferences."""
        # Create user with empty preferences
        user_no_prefs = CustomUser.objects.create_user(
            email="empty@testschool.com",
            name="Empty User",
            tutorial_preferences={}
        )
        
        SchoolMembership.objects.create(
            user=user_no_prefs,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        self.client.force_authenticate(user=user_no_prefs)
        
        url = reverse('accounts:user-navigation-preferences')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return empty dict or default values
        data = response.json()
        self.assertIsInstance(data, dict)
    
    def test_post_navigation_preferences_update_success(self):
        """Test POST /api/accounts/navigation-preferences/ updates preferences."""
        url = reverse('accounts:user-navigation-preferences')
        
        update_data = {
            "quick_actions": ["invite_teacher", "view_reports"],
            "default_landing_page": "students",
            "navigation_style": "top_nav",
            "tutorial_auto_start": False
        }
        
        response = self.client.post(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        # Check that preferences were updated
        self.assertEqual(
            self.user.tutorial_preferences["quick_actions"],
            ["invite_teacher", "view_reports"]
        )
        self.assertEqual(
            self.user.tutorial_preferences["default_landing_page"],
            "students"
        )
        self.assertEqual(
            self.user.tutorial_preferences["navigation_style"],
            "top_nav"
        )
        self.assertFalse(
            self.user.tutorial_preferences["tutorial_auto_start"]
        )
    
    def test_post_navigation_preferences_partial_update(self):
        """Test POST with partial preferences updates only specified fields."""
        url = reverse('accounts:user-navigation-preferences')
        
        # Update only quick_actions
        partial_data = {
            "quick_actions": ["manage_billing"]
        }
        
        response = self.client.post(url, partial_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        # Check that only quick_actions was updated
        self.assertEqual(
            self.user.tutorial_preferences["quick_actions"],
            ["manage_billing"]
        )
        # Other preferences should remain unchanged
        self.assertEqual(
            self.user.tutorial_preferences["default_landing_page"],
            "dashboard"
        )
        self.assertEqual(
            self.user.tutorial_preferences["navigation_style"],
            "sidebar"
        )
        self.assertTrue(
            self.user.tutorial_preferences["tutorial_auto_start"]
        )
    
    def test_post_navigation_preferences_invalid_data_types(self):
        """Test POST with invalid data types."""
        url = reverse('accounts:user-navigation-preferences')
        
        invalid_data = {
            "quick_actions": "not_a_list",  # Should be a list
            "tutorial_auto_start": "not_a_boolean"  # Should be boolean
        }
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quick_actions", str(response.content))
    
    def test_post_navigation_preferences_invalid_landing_page(self):
        """Test POST with invalid landing page value."""
        url = reverse('accounts:user-navigation-preferences')
        
        invalid_data = {
            "default_landing_page": "invalid_page"
        }
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("default_landing_page", str(response.content))
    
    def test_post_navigation_preferences_invalid_navigation_style(self):
        """Test POST with invalid navigation style."""
        url = reverse('accounts:user-navigation-preferences')
        
        invalid_data = {
            "navigation_style": "invalid_style"
        }
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("navigation_style", str(response.content))
    
    def test_navigation_preferences_unauthorized(self):
        """Test that unauthenticated users cannot access endpoint."""
        self.client.force_authenticate(user=None)
        
        url = reverse('accounts:user-navigation-preferences')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_navigation_preferences_performance_target(self):
        """Test that API responds within performance targets."""
        import time
        
        url = reverse('accounts:user-navigation-preferences')
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Performance target: <100ms for navigation preferences
        response_time_ms = (end_time - start_time) * 1000
        self.assertLess(response_time_ms, 100, f"Response time {response_time_ms:.2f}ms exceeds 100ms target")
    
    def test_navigation_preferences_school_context_aware(self):
        """Test that preferences can be context-aware for different schools."""
        # Create another school for multi-school scenario
        other_school = School.objects.create(
            name="Other School",
            description="Another school"
        )
        
        # Add user to other school
        SchoolMembership.objects.create(
            user=self.user,
            school=other_school,
            role=SchoolRole.TEACHER
        )
        
        url = reverse('accounts:user-navigation-preferences')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should still return user's global preferences
        data = response.json()
        self.assertEqual(data["navigation_style"], "sidebar")
    
    def test_post_navigation_preferences_empty_request(self):
        """Test POST with empty request body."""
        url = reverse('accounts:user-navigation-preferences')
        
        response = self.client.post(url, {}, format='json')
        
        # Should succeed and not change anything
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User preferences should remain unchanged
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.tutorial_preferences["navigation_style"],
            "sidebar"
        )
    
    def test_post_navigation_preferences_role_based_quick_actions(self):
        """Test that quick actions can be role-specific."""
        url = reverse('accounts:user-navigation-preferences')
        
        # Admin-specific quick actions
        admin_data = {
            "quick_actions": ["manage_billing", "view_analytics", "invite_teacher"]
        }
        
        response = self.client.post(url, admin_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify quick actions were saved
        self.user.refresh_from_db()
        self.assertEqual(
            set(self.user.tutorial_preferences["quick_actions"]),
            {"manage_billing", "view_analytics", "invite_teacher"}
        )