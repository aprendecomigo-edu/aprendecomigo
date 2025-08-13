"""
Business logic tests for notification counting functionality.

Tests core business rules for:
- Pending teacher invitations counting
- New user registrations counting
- Task-based notification counting
- School-scoped counting rules
"""

import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole, 
    TeacherInvitation, InvitationStatus
)
from tasks.models import Task
from messaging.tests.test_base import MessagingTestBase


class NotificationCountBusinessLogicTest(MessagingTestBase):
    """Test business logic for calculating notification counts."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Base class provides self.school and self.admin_user
    
    def test_count_pending_teacher_invitations(self):
        """Test business rule: count only pending, non-expired teacher invitations."""
        # Create pending invitation (should be counted)
        self.create_teacher_invitation(
            email="pending@test.com",
            status=InvitationStatus.PENDING,
            expires_in_days=7
        )
        
        # Create accepted invitation (should NOT be counted)
        self.create_teacher_invitation(
            email="accepted@test.com",
            status=InvitationStatus.ACCEPTED,
            expires_in_days=7
        )
        
        # Create expired invitation (should NOT be counted)  
        TeacherInvitation.objects.create(
            school=self.school,
            email="expired@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() - timedelta(days=1),  # Expired
            batch_id=uuid.uuid4()
        )
        
        # Business rule: only count pending, non-expired invitations
        pending_count = TeacherInvitation.objects.filter(
            school=self.school,
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now()
        ).count()
        
        self.assertEqual(pending_count, 1)
    
    def test_count_new_registrations_requiring_first_login(self):
        """Test business rule: count users who haven't completed first login."""
        # Create user who hasn't completed first login (should be counted)
        self.create_student_user(
            email="newuser@test.com",
            name="New User",
            first_login_completed=False  # Key business state
        )
        
        # Create user who has completed first login (should NOT be counted)
        self.create_student_user(
            email="existing@test.com",
            name="Existing User",
            first_login_completed=True
        )
        
        # Business rule: count only users who haven't completed first login
        new_registration_count = SchoolMembership.objects.filter(
            school=self.school,
            user__first_login_completed=False
        ).count()
        
        self.assertEqual(new_registration_count, 1)
    
    def test_count_incomplete_profiles(self):
        """Test business rule: count users with pending profile completion tasks."""
        # Create user with incomplete profile task (should be counted)
        incomplete_user = self.create_teacher_user(
            email="incomplete@test.com",
            name="Incomplete User",
            first_login_completed=True
        )
        
        Task.objects.create(
            user=incomplete_user,
            title="Complete Your Profile",
            status="pending",
            task_type="onboarding",
            is_system_generated=True
        )
        
        # Create user without profile tasks (should NOT be counted)
        complete_user = self.create_teacher_user(
            email="complete@test.com",
            name="Complete User",
            first_login_completed=True
        )
        
        # Business rule: count users with pending profile completion tasks
        school_users = [membership.user for membership in SchoolMembership.objects.filter(school=self.school)]
        incomplete_profile_count = Task.objects.filter(
            user__in=school_users,
            title__icontains="Complete Your Profile",
            status="pending",
            is_system_generated=True
        ).count()
        
        self.assertEqual(incomplete_profile_count, 1)
    
    def test_count_overdue_tasks(self):
        """Test business rule: count tasks that are past their due date."""
        # Business scenario: school has tasks that are overdue
        
        # Create overdue task (should be counted)
        overdue_user = self.create_teacher_user(
            email="overdue@test.com",
            name="Overdue User"
        )
        Task.objects.create(
            user=overdue_user,
            title="Overdue Task",
            status="pending",
            due_date=timezone.now() - timedelta(days=1),  # Past due
            task_type="assignment"
        )
        
        # Create future task (should NOT be counted)
        future_user = self.create_teacher_user(
            email="future@test.com",
            name="Future User"
        )
        Task.objects.create(
            user=future_user,
            title="Future Task",
            status="pending",
            due_date=timezone.now() + timedelta(days=1),  # Future due date
            task_type="assignment"
        )
        
        # Create completed overdue task (should NOT be counted)
        completed_user = self.create_teacher_user(
            email="completed@test.com",
            name="Completed User"
        )
        Task.objects.create(
            user=completed_user,
            title="Completed Task",
            status="completed",  # Completed
            due_date=timezone.now() - timedelta(days=2),
            task_type="assignment"
        )
        
        # Business rule: count only pending tasks past their due date
        school_users = [membership.user for membership in SchoolMembership.objects.filter(school=self.school)]
        overdue_count = Task.objects.filter(
            user__in=school_users,
            status="pending",
            due_date__lt=timezone.now()
        ).count()
        
        self.assertEqual(overdue_count, 1)
    
    def test_school_scoped_counting(self):
        """Test business rule: notification counts are scoped to specific school."""
        # Business scenario: system has multiple schools, counts should be isolated
        
        # Create another school with its own data
        other_school, other_admin = self.create_other_school()
        
        # Create invitation for other school  
        TeacherInvitation.objects.create(
            school=other_school,
            email="other_teacher@test.com",
            invited_by=other_admin,
            role=SchoolRole.TEACHER,
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        # Create invitation for our school
        self.create_teacher_invitation(
            email="our_teacher@test.com",
            status=InvitationStatus.PENDING,
            expires_in_days=7
        )
        
        # Business rule: counts should be scoped to specific school
        our_school_count = TeacherInvitation.objects.filter(
            school=self.school,
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now()
        ).count()
        
        other_school_count = TeacherInvitation.objects.filter(
            school=other_school,
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now()
        ).count()
        
        self.assertEqual(our_school_count, 1)
        self.assertEqual(other_school_count, 1)
    
    def test_multiple_notification_types_counted_correctly(self):
        """Test business rule: different notification types are counted independently."""
        # Create one of each notification type
        self.create_teacher_invitation(status=InvitationStatus.PENDING, expires_in_days=7)
        self.create_student_user("new@test.com", "New User", first_login_completed=False)
        
        # Calculate counts
        pending_invitations = TeacherInvitation.objects.filter(
            school=self.school,
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now()
        ).count()
        
        new_registrations = SchoolMembership.objects.filter(
            school=self.school,
            user__first_login_completed=False
        ).count()
        
        self.assertEqual(pending_invitations, 1)
        self.assertEqual(new_registrations, 1)