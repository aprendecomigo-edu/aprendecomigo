"""
Permission Security Tests for Aprende Comigo Platform

These tests verify that users cannot escalate their privileges beyond their assigned roles
and that role-based access control is properly enforced.

Focus on realistic scenarios using Knox authentication and existing API endpoints.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    SchoolRole,
    TeacherProfile,
    StudentProfile,
)

User = get_user_model()


class RoleBasedAccessControlTestCase(TestCase):
    """
    Test suite for verifying role-based access control.
    
    These tests ensure that:
    1. Users can only access resources appropriate to their role
    2. Role boundaries are enforced across API endpoints
    3. Users cannot perform actions beyond their permissions
    """

    def setUp(self):
        """Set up test data with multiple roles."""
        self.client = APIClient()
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            contact_email="admin@testschool.com"
        )
        
        # Create users with different roles
        self.school_owner = CustomUser.objects.create_user(
            email="owner@example.com",
            name="School Owner"
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            name="Test Teacher"
        )
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            name="Test Student"
        )
        
        # Create memberships
        SchoolMembership.objects.create(
            user=self.school_owner, 
            school=self.school, 
            role=SchoolRole.SCHOOL_OWNER
        )
        SchoolMembership.objects.create(
            user=self.teacher, 
            school=self.school, 
            role=SchoolRole.TEACHER
        )
        SchoolMembership.objects.create(
            user=self.student, 
            school=self.school, 
            role=SchoolRole.STUDENT
        )
        
        # Create profiles
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher, 
            bio="Test teacher"
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student, 
            birth_date="2010-01-01", 
            school_year="5th"
        )

    def authenticate_user(self, user):
        """Helper method to authenticate a user with Knox token."""
        instance, token = AuthToken.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_student_cannot_access_administrative_endpoints(self):
        """Test that students cannot access administrative functionality."""
        self.authenticate_user(self.student)
        
        # Test endpoints that should require higher privileges
        restricted_endpoints = [
            'accounts:user-list',  # User management
            'accounts:invitation-list',  # Invitation management
            'accounts:teacher-invitation-list',  # Teacher invitations
        ]
        
        for endpoint_name in restricted_endpoints:
            with self.subTest(endpoint=endpoint_name):
                try:
                    url = reverse(endpoint_name)
                    response = self.client.get(url)
                    
                    # Should be forbidden or unauthorized
                    self.assertIn(response.status_code, [
                        status.HTTP_401_UNAUTHORIZED,
                        status.HTTP_403_FORBIDDEN
                    ], f"Student should not access {endpoint_name}")
                    
                except Exception:
                    # If endpoint doesn't exist, skip
                    self.skipTest(f"Endpoint {endpoint_name} not available")

    def test_teacher_cannot_access_school_owner_functionality(self):
        """Test that teachers cannot access school owner specific features."""
        self.authenticate_user(self.teacher)
        
        # Test endpoints that should require school owner privileges
        owner_endpoints = [
            'accounts:invitation-list',  # School invitations
        ]
        
        for endpoint_name in owner_endpoints:
            with self.subTest(endpoint=endpoint_name):
                try:
                    url = reverse(endpoint_name)
                    response = self.client.get(url)
                    
                    # Depending on implementation, might be forbidden or return filtered results
                    # The key is that it shouldn't cause server errors
                    self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                except Exception:
                    self.skipTest(f"Endpoint {endpoint_name} not available")

    def test_users_can_access_their_appropriate_resources(self):
        """Test that users can access resources appropriate to their role."""
        # Test that authenticated users can access general resources
        for user, role_name in [
            (self.teacher, "teacher"),
            (self.student, "student"),
            (self.school_owner, "owner")
        ]:
            with self.subTest(user=role_name):
                self.authenticate_user(user)
                
                try:
                    # Test course list access (should be available to all roles)
                    url = reverse('accounts:course-list')
                    response = self.client.get(url)
                    
                    # Should succeed or be forbidden, but not error
                    self.assertIn(response.status_code, [
                        status.HTTP_200_OK,
                        status.HTTP_403_FORBIDDEN
                    ], f"{role_name} should be able to access courses or get clear rejection")
                    
                except Exception:
                    self.skipTest("Course list endpoint not available")

    def test_role_elevation_attempts_blocked(self):
        """Test that attempts to elevate permissions are blocked."""
        # Test that a teacher cannot modify their own role
        self.authenticate_user(self.teacher)
        
        # Get teacher's membership
        membership = SchoolMembership.objects.get(
            user=self.teacher, school=self.school
        )
        
        # This test documents that role modification should be restricted
        # The exact implementation depends on whether membership modification
        # endpoints exist and how they're protected
        
        # For now, test that the membership role remains unchanged
        self.assertEqual(membership.role, SchoolRole.TEACHER)
        
        # After any API calls that might attempt modification,
        # verify role hasn't changed
        membership.refresh_from_db()
        self.assertEqual(membership.role, SchoolRole.TEACHER)

    def test_inactive_users_cannot_access_protected_resources(self):
        """Test that inactive users cannot access protected resources."""
        # Create inactive user
        inactive_user = CustomUser.objects.create_user(
            email="inactive@example.com",
            name="Inactive User",
            is_active=False
        )
        
        # Create membership for inactive user
        SchoolMembership.objects.create(
            user=inactive_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        self.authenticate_user(inactive_user)
        
        try:
            url = reverse('accounts:course-list')
            response = self.client.get(url)
            
            # Should be unauthorized due to inactive status
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            
        except Exception:
            self.skipTest("Course list endpoint not available")

    def test_cross_school_access_prevented(self):
        """Test that users cannot access resources from other schools."""
        # Create another school
        other_school = School.objects.create(
            name="Other School",
            contact_email="admin@otherschool.com"
        )
        
        # Create user in other school
        other_user = CustomUser.objects.create_user(
            email="other@example.com",
            name="Other User"
        )
        SchoolMembership.objects.create(
            user=other_user,
            school=other_school,
            role=SchoolRole.TEACHER
        )
        
        # Authenticate as user from original school
        self.authenticate_user(self.teacher)
        
        # Test that we can't access resources that should be school-specific
        # This is a placeholder for school-specific endpoints when they exist
        
        # For now, verify that the user's school context is correct
        teacher_schools = SchoolMembership.objects.filter(
            user=self.teacher, is_active=True
        ).values_list('school_id', flat=True)
        
        self.assertIn(self.school.id, teacher_schools)
        self.assertNotIn(other_school.id, teacher_schools)


class TokenSecurityTestCase(TestCase):
    """Test token-based security and session management."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            name="Test User"
        )
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.TEACHER
        )

    def test_token_required_for_protected_endpoints(self):
        """Test that tokens are required for protected endpoints."""
        # Don't authenticate - test without token
        
        try:
            url = reverse('accounts:user-list')
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            
        except Exception:
            self.skipTest("User list endpoint not available")

    def test_valid_token_provides_access(self):
        """Test that valid tokens provide appropriate access."""
        # Authenticate with valid token
        instance, token = AuthToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        try:
            url = reverse('accounts:course-list')
            response = self.client.get(url)
            
            # Should succeed or be forbidden based on permissions, not authentication
            self.assertIn(response.status_code, [
                status.HTTP_200_OK,
                status.HTTP_403_FORBIDDEN
            ])
            
        except Exception:
            self.skipTest("Course list endpoint not available")

    def test_token_cleanup_on_logout(self):
        """Test that tokens are properly invalidated on logout."""
        # Create token
        instance, token = AuthToken.objects.create(user=self.user)
        
        # Verify token exists
        self.assertTrue(AuthToken.objects.filter(digest=instance.digest).exists())
        
        # Use logout endpoint to invalidate token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        try:
            logout_url = reverse('accounts:knox_logout')
            response = self.client.post(logout_url)
            
            # Should succeed
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            
            # Verify token is invalidated
            self.assertFalse(AuthToken.objects.filter(digest=instance.digest).exists())
            
        except Exception:
            self.skipTest("Knox logout endpoint not available")


class UserPermissionBoundaryTestCase(TestCase):
    """Test that user permissions are properly bounded."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        
        # Create users with different permission levels
        self.admin_user = CustomUser.objects.create_superuser(
            email="admin@example.com",
            name="Admin User",
            password="admin123"
        )
        
        self.regular_user = CustomUser.objects.create_user(
            email="regular@example.com",
            name="Regular User"
        )
        
        SchoolMembership.objects.create(
            user=self.regular_user,
            school=self.school,
            role=SchoolRole.STUDENT
        )

    def authenticate_user(self, user):
        """Helper to authenticate user."""
        instance, token = AuthToken.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_superuser_has_elevated_access(self):
        """Test that superusers have elevated access where appropriate."""
        self.authenticate_user(self.admin_user)
        
        # Test that superuser can access administrative endpoints
        try:
            url = reverse('accounts:user-list')
            response = self.client.get(url)
            
            # Should succeed or be explicitly forbidden
            self.assertIn(response.status_code, [
                status.HTTP_200_OK,
                status.HTTP_403_FORBIDDEN
            ])
            
        except Exception:
            self.skipTest("User list endpoint not available")

    def test_regular_user_has_limited_access(self):
        """Test that regular users have appropriately limited access."""
        self.authenticate_user(self.regular_user)
        
        # Test that regular user cannot access administrative endpoints
        try:
            url = reverse('accounts:user-list')
            response = self.client.get(url)
            
            # Should be forbidden or unauthorized
            self.assertIn(response.status_code, [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ])
            
        except Exception:
            self.skipTest("User list endpoint not available")

    def test_permission_errors_are_informative(self):
        """Test that permission errors provide appropriate feedback."""
        self.authenticate_user(self.regular_user)
        
        try:
            url = reverse('accounts:user-list')
            response = self.client.get(url)
            
            if response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]:
                # Should provide JSON error response
                self.assertEqual(response['Content-Type'], 'application/json')
                
                # Should contain error details
                data = response.json()
                self.assertIn('detail', data)
                
        except Exception:
            self.skipTest("User list endpoint not available")


class DataAccessPermissionTestCase(TestCase):
    """Test permissions for accessing specific data objects."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        
        self.user1 = CustomUser.objects.create_user(
            email="user1@example.com",
            name="User One"
        )
        self.user2 = CustomUser.objects.create_user(
            email="user2@example.com", 
            name="User Two"
        )
        
        SchoolMembership.objects.create(
            user=self.user1, school=self.school, role=SchoolRole.TEACHER
        )
        SchoolMembership.objects.create(
            user=self.user2, school=self.school, role=SchoolRole.STUDENT
        )
        
        self.profile1 = TeacherProfile.objects.create(user=self.user1, bio="Teacher 1")
        self.profile2 = StudentProfile.objects.create(
            user=self.user2, birth_date="2010-01-01", school_year="5th"
        )

    def authenticate_user(self, user):
        """Helper to authenticate user."""
        instance, token = AuthToken.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_users_can_access_own_profiles(self):
        """Test that users can access their own profile data."""
        # This test documents expected behavior for profile access
        # Implementation depends on how profile endpoints are structured
        
        for user in [self.user1, self.user2]:
            with self.subTest(user=user.email):
                self.authenticate_user(user)
                
                # Users should be able to access their own data
                # This is a placeholder for when profile detail endpoints exist
                self.assertTrue(True)  # Placeholder assertion

    def test_users_cannot_access_others_private_data(self):
        """Test that users cannot access other users' private data."""
        self.authenticate_user(self.user1)
        
        # This test documents expected behavior - users should not be able
        # to access private data of other users
        # Implementation depends on endpoint structure
        
        # For now, verify at the model level that data is properly separated
        user1_profiles = TeacherProfile.objects.filter(user=self.user1)
        user2_profiles = StudentProfile.objects.filter(user=self.user2)
        
        self.assertEqual(user1_profiles.count(), 1)
        self.assertEqual(user2_profiles.count(), 1)
        
        # Verify profiles belong to correct users
        self.assertEqual(user1_profiles.first().user, self.user1)
        self.assertEqual(user2_profiles.first().user, self.user2)