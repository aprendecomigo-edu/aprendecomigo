"""
Tests for Notification Count API endpoints.
Following TDD methodology - tests written first before implementation.
"""
import json
import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole, 
    TeacherInvitation, InvitationStatus, SchoolInvitation
)
from tasks.models import Task


class NotificationCountAPITestCase(TestCase):
    """Test cases for notification count API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        # Create a school admin user
        self.admin_user = CustomUser.objects.create_user(
            email="admin@testschool.com",
            name="Test Admin",
            first_login_completed=True  # Admin has completed first login
        )
        
        # Create school membership
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Create some test data for counting
        self._create_test_data()
        
        # Authenticate user
        self.client.force_authenticate(user=self.admin_user)
    
    def _create_test_data(self):
        """Create test data for notification counting."""
        
        # Create pending teacher invitations
        for i in range(3):
            TeacherInvitation.objects.create(
                school=self.school,
                email=f"teacher{i}@test.com",
                invited_by=self.admin_user,
                role=SchoolRole.TEACHER,
                status=InvitationStatus.PENDING,
                expires_at=timezone.now() + timedelta(days=7),
                batch_id=uuid.uuid4()
            )
        
        # Create accepted invitation (should not count)
        TeacherInvitation.objects.create(
            school=self.school,
            email="accepted@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            status=InvitationStatus.ACCEPTED,
            is_accepted=True,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        # Create new user registrations (users with incomplete first login)
        for i in range(2):
            new_user = CustomUser.objects.create_user(
                email=f"newuser{i}@test.com",
                name=f"New User {i}",
                first_login_completed=False
            )
            SchoolMembership.objects.create(
                user=new_user,
                school=self.school,
                role=SchoolRole.STUDENT
            )
        
        # Create users with incomplete profiles
        for i in range(5):
            incomplete_user = CustomUser.objects.create_user(
                email=f"incomplete{i}@test.com",
                name=f"Incomplete User {i}",
                first_login_completed=True
            )
            SchoolMembership.objects.create(
                user=incomplete_user,
                school=self.school,
                role=SchoolRole.TEACHER
            )
            # Create incomplete profile task
            Task.objects.create(
                user=incomplete_user,
                title="Complete Your Profile",
                status="pending",
                task_type="onboarding",
                is_system_generated=True
            )
        
        # Create overdue tasks
        overdue_user = CustomUser.objects.create_user(
            email="overdue@test.com",
            name="Overdue User"
        )
        SchoolMembership.objects.create(
            user=overdue_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        Task.objects.create(
            user=overdue_user,
            title="Overdue Task",
            status="pending",
            due_date=timezone.now() - timedelta(days=1),
            task_type="assignment"
        )
    
    def test_get_notification_counts_success(self):
        """Test GET /api/notifications/counts/ returns correct counts."""
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Check all expected fields are present
        self.assertIn("pending_invitations", data)
        self.assertIn("new_registrations", data)
        self.assertIn("incomplete_profiles", data)
        self.assertIn("overdue_tasks", data)
        self.assertIn("total_unread", data)
        
        # Check counts are correct
        self.assertEqual(data["pending_invitations"], 3)  # 3 pending invitations
        self.assertEqual(data["new_registrations"], 2)    # 2 users with first_login_completed=False
        self.assertEqual(data["incomplete_profiles"], 5)   # 5 users with profile completion tasks
        self.assertEqual(data["overdue_tasks"], 1)        # 1 overdue task
        self.assertEqual(data["total_unread"], 11)        # Sum of all counts
    
    def test_get_notification_counts_empty_school(self):
        """Test notification counts for school with no notifications."""
        # Create a new school with no data
        empty_school = School.objects.create(
            name="Empty School",
            description="School with no notifications"
        )
        
        empty_admin = CustomUser.objects.create_user(
            email="empty@school.com",
            name="Empty Admin",
            first_login_completed=True  # Empty admin has completed first login
        )
        
        SchoolMembership.objects.create(
            user=empty_admin,
            school=empty_school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        self.client.force_authenticate(user=empty_admin)
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # All counts should be zero
        self.assertEqual(data["pending_invitations"], 0)
        self.assertEqual(data["new_registrations"], 0)
        self.assertEqual(data["incomplete_profiles"], 0)
        self.assertEqual(data["overdue_tasks"], 0)
        self.assertEqual(data["total_unread"], 0)
    
    def test_get_notification_counts_school_scoped(self):
        """Test that counts are properly scoped to user's school."""
        # Create another school with its own data
        other_school = School.objects.create(
            name="Other School",
            description="Another school"
        )
        
        other_admin = CustomUser.objects.create_user(
            email="other@school.com",
            name="Other Admin",
            first_login_completed=True  # Other admin has completed first login
        )
        
        SchoolMembership.objects.create(
            user=other_admin,
            school=other_school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Create some data for other school
        TeacherInvitation.objects.create(
            school=other_school,
            email="other_teacher@test.com",
            invited_by=other_admin,
            role=SchoolRole.TEACHER,
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        # Test that our admin only sees their school's counts
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should still be 3 pending invitations, not 4
        self.assertEqual(data["pending_invitations"], 3)
    
    def test_get_notification_counts_unauthorized(self):
        """Test that unauthenticated users cannot access endpoint."""
        self.client.force_authenticate(user=None)
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_notification_counts_non_admin_user(self):
        """Test that non-admin users get appropriate counts."""
        # Create a regular teacher user
        teacher_user = CustomUser.objects.create_user(
            email="teacher@testschool.com",
            name="Test Teacher",
            first_login_completed=True  # Teacher has completed first login
        )
        
        SchoolMembership.objects.create(
            user=teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        # Create a personal overdue task for the teacher
        Task.objects.create(
            user=teacher_user,
            title="Teacher's Overdue Task",
            status="pending",
            due_date=timezone.now() - timedelta(days=2),
            task_type="personal"
        )
        
        self.client.force_authenticate(user=teacher_user)
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Teachers should see limited data
        # They might not see pending invitations (admin-only)
        # But they should see their own overdue tasks
        self.assertIn("overdue_tasks", data)
        self.assertGreaterEqual(data["overdue_tasks"], 1)  # At least their own task
    
    def test_notification_counts_performance_target(self):
        """Test that API responds within 50ms performance target."""
        import time
        
        url = reverse('messaging:counts')
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Performance target: <50ms
        response_time_ms = (end_time - start_time) * 1000
        self.assertLess(response_time_ms, 50, f"Response time {response_time_ms:.2f}ms exceeds 50ms target")
    
    def test_notification_counts_handles_edge_cases(self):
        """Test notification counts handle edge cases properly."""
        # Create expired invitation (should not count)
        TeacherInvitation.objects.create(
            school=self.school,
            email="expired@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() - timedelta(days=1),  # Expired
            batch_id=uuid.uuid4()
        )
        
        # Create completed task (should not count as overdue)
        completed_user = CustomUser.objects.create_user(
            email="completed@test.com",
            name="Completed User",
            first_login_completed=True  # Completed user has finished first login
        )
        SchoolMembership.objects.create(
            user=completed_user,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        Task.objects.create(
            user=completed_user,
            title="Completed Task",
            status="completed",
            due_date=timezone.now() - timedelta(days=1),
            task_type="assignment"
        )
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Counts should remain the same as before (expired and completed don't count)
        self.assertEqual(data["pending_invitations"], 3)  # Still 3, not 4
        self.assertEqual(data["overdue_tasks"], 1)        # Still 1, completed doesn't count
    
    def test_notification_counts_only_get_method(self):
        """Test that only GET method is allowed."""
        url = reverse('messaging:counts')
        
        # Test POST is not allowed
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test PUT is not allowed
        response = self.client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test DELETE is not allowed
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)