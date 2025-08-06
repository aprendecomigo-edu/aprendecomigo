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
    TeacherInvitation, InvitationStatus, EducationalSystem
)
from tasks.models import Task


class NotificationCountAPITestCase(TestCase):
    """Test cases for notification count API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Get or create educational system
        self.educational_system, _ = EducationalSystem.objects.get_or_create(
            code="pt",
            defaults={
                "name": "Portugal",
                "description": "Portuguese educational system"
            }
        )
        
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            description="A test school for notifications"
        )
        
        # Create another school for isolation testing
        self.other_school = School.objects.create(
            name="Other School", 
            description="Should not affect notification counts"
        )
        
        # Create a school admin user
        self.admin_user = CustomUser.objects.create_user(
            email="admin@testschool.com",
            name="Test Admin",
            first_login_completed=True
        )
        
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Create a regular user (teacher)
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@testschool.com",
            name="John Teacher",
            first_login_completed=True
        )
        
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        # Create users who haven't completed first login
        self.new_user1 = CustomUser.objects.create_user(
            email="new1@testschool.com",
            name="New User 1",
            first_login_completed=False
        )
        
        SchoolMembership.objects.create(
            user=self.new_user1,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        self.new_user2 = CustomUser.objects.create_user(
            email="new2@testschool.com",
            name="New User 2",
            first_login_completed=False
        )
        
        SchoolMembership.objects.create(
            user=self.new_user2,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        # Create user in other school (should not affect counts)
        self.other_user = CustomUser.objects.create_user(
            email="other@otherschool.com",
            name="Other User",
            first_login_completed=False
        )
        
        SchoolMembership.objects.create(
            user=self.other_user,
            school=self.other_school,
            role=SchoolRole.TEACHER
        )
        
        # Authenticate admin user
        self.client.force_authenticate(user=self.admin_user)
    
    def test_notification_counts_success_admin(self):
        """Test GET /api/notifications/counts/ returns correct counts for admin."""
        # Create pending invitations
        TeacherInvitation.objects.create(
            school=self.school,
            email="invite1@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        TeacherInvitation.objects.create(
            school=self.school,
            email="invite2@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.SENT,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Create profile completion tasks for incomplete profiles
        Task.objects.create(
            user=self.new_user1,
            title="Complete Your Profile",
            description="Finish setting up your profile",
            task_type="onboarding",
            status="pending",
            is_system_generated=True,
            due_date=timezone.now() + timedelta(days=3)
        )
        
        # Create overdue tasks
        Task.objects.create(
            user=self.admin_user,
            title="Overdue Task",
            description="This task is overdue",
            task_type="personal",
            status="pending",
            is_system_generated=False,
            due_date=timezone.now() - timedelta(days=1)
        )
        
        Task.objects.create(
            user=self.teacher_user,
            title="Another Overdue Task",
            description="Another overdue task in managed school",
            task_type="assignment",
            status="pending",
            is_system_generated=False,
            due_date=timezone.now() - timedelta(hours=2)
        )
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Verify counts
        self.assertEqual(data["pending_invitations"], 2)  # 2 pending invitations
        self.assertEqual(data["new_registrations"], 2)   # 2 users haven't completed first login
        self.assertEqual(data["incomplete_profiles"], 1)  # 1 user with profile completion task
        self.assertEqual(data["overdue_tasks"], 2)       # 2 overdue tasks in managed schools
        self.assertEqual(data["total_unread"], 7)        # Sum of all above
    
    def test_notification_counts_teacher_role(self):
        """Test notification counts for teacher role (limited visibility)."""
        self.client.force_authenticate(user=self.teacher_user)
        
        # Create pending invitations (teacher shouldn't see these)
        TeacherInvitation.objects.create(
            school=self.school,
            email="invite@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Create overdue task for teacher
        Task.objects.create(
            user=self.teacher_user,
            title="Teacher Overdue Task",
            description="Overdue task for teacher",
            task_type="personal",
            status="pending",
            is_system_generated=False,
            due_date=timezone.now() - timedelta(days=1)
        )
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Teacher should only see their own overdue tasks
        self.assertEqual(data["pending_invitations"], 0)
        self.assertEqual(data["new_registrations"], 0)
        self.assertEqual(data["incomplete_profiles"], 0)
        self.assertEqual(data["overdue_tasks"], 1)  # Only their own overdue task
        self.assertEqual(data["total_unread"], 1)
    
    def test_notification_counts_expired_invitations_excluded(self):
        """Test that expired invitations are not counted."""
        # Create expired invitation
        TeacherInvitation.objects.create(
            school=self.school,
            email="expired@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() - timedelta(days=1)  # Expired
        )
        
        # Create valid invitation
        TeacherInvitation.objects.create(
            school=self.school,
            email="valid@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=7)  # Not expired
        )
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data["pending_invitations"], 1)  # Only the valid one
    
    def test_notification_counts_accepted_invitations_excluded(self):
        """Test that accepted invitations are not counted."""
        # Create accepted invitation
        TeacherInvitation.objects.create(
            school=self.school,
            email="accepted@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.ACCEPTED,
            is_accepted=True,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Create pending invitation
        TeacherInvitation.objects.create(
            school=self.school,
            email="pending@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.PENDING,
            is_accepted=False,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data["pending_invitations"], 1)  # Only the pending one
    
    def test_notification_counts_school_scoped(self):
        """Test that counts are properly scoped to user's managed schools."""
        # Create invitation in other school (shouldn't be counted)
        TeacherInvitation.objects.create(
            school=self.other_school,
            email="other@example.com",
            invited_by=self.other_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Create invitation in managed school (should be counted)
        TeacherInvitation.objects.create(
            school=self.school,
            email="managed@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Should only count from managed school
        self.assertEqual(data["pending_invitations"], 1)
        # Should count new registrations from managed school only (2 users)
        self.assertEqual(data["new_registrations"], 2)
    
    def test_notification_counts_completed_tasks_excluded(self):
        """Test that completed tasks are not counted as overdue."""
        # Create completed overdue task (shouldn't be counted)
        Task.objects.create(
            user=self.admin_user,
            title="Completed Overdue Task",
            description="This task is completed even though overdue",
            task_type="personal",
            status="completed",
            is_system_generated=False,
            due_date=timezone.now() - timedelta(days=1)
        )
        
        # Create pending overdue task (should be counted)
        Task.objects.create(
            user=self.admin_user,
            title="Pending Overdue Task",
            description="This task is overdue",
            task_type="personal",
            status="pending",
            is_system_generated=False,
            due_date=timezone.now() - timedelta(days=1)
        )
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data["overdue_tasks"], 1)  # Only the pending one
    
    def test_notification_counts_unauthorized(self):
        """Test that unauthenticated users cannot access endpoint."""
        self.client.force_authenticate(user=None)
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_notification_counts_performance_target(self):
        """Test that API responds within 50ms performance target."""
        import time
        
        url = reverse('messaging:counts')
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Performance target: <50ms for notifications
        response_time_ms = (end_time - start_time) * 1000
        self.assertLess(response_time_ms, 50, f"Response time {response_time_ms:.2f}ms exceeds 50ms target")
    
    def test_notification_counts_response_format(self):
        """Test that response has correct format."""
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Check all required fields are present
        required_fields = [
            "pending_invitations",
            "new_registrations", 
            "incomplete_profiles",
            "overdue_tasks",
            "total_unread"
        ]
        
        for field in required_fields:
            self.assertIn(field, data)
            self.assertIsInstance(data[field], int)
    
    def test_notification_counts_zero_counts(self):
        """Test notification counts when no notifications exist."""
        # Ensure all users have completed first login
        self.new_user1.first_login_completed = True
        self.new_user1.save()
        self.new_user2.first_login_completed = True
        self.new_user2.save()
        
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
    
    def test_notification_counts_multiple_invitation_statuses(self):
        """Test that different valid invitation statuses are all counted."""
        statuses_to_count = [
            InvitationStatus.PENDING,
            InvitationStatus.SENT,
            InvitationStatus.DELIVERED,
            InvitationStatus.VIEWED,
        ]
        
        for i, status_value in enumerate(statuses_to_count):
            TeacherInvitation.objects.create(
                school=self.school,
                email=f"invite{i}@example.com",
                invited_by=self.admin_user,
                role=SchoolRole.TEACHER,
                batch_id=uuid.uuid4(),
                status=status_value,
                is_accepted=False,
                expires_at=timezone.now() + timedelta(days=7)
            )
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data["pending_invitations"], len(statuses_to_count))
    
    def test_notification_counts_declined_invitations_excluded(self):
        """Test that declined invitations are not counted."""
        # Create declined invitation
        TeacherInvitation.objects.create(
            school=self.school,
            email="declined@example.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            batch_id=uuid.uuid4(),
            status=InvitationStatus.DECLINED,
            is_accepted=False,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        url = reverse('messaging:counts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data["pending_invitations"], 0)  # Declined should not be counted