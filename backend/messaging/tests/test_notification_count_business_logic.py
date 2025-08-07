"""
Business logic tests for notification counting functionality.

Tests the business rules for calculating various notification counts:
- Pending teacher invitations 
- New user registrations requiring first login
- Incomplete user profiles
- Overdue tasks
- Business rules for counting scope and filters
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


class NotificationCountBusinessLogicTest(TestCase):
    """Test business logic for calculating notification counts."""
    
    def setUp(self):
        """Set up test data."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        # Create school admin
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
    
    def test_count_pending_teacher_invitations(self):
        """Test business rule: count only pending, non-expired teacher invitations."""
        # Business scenario: school has sent various teacher invitations
        
        # Create pending invitations (should be counted)
        pending_invitations = []
        for i in range(3):
            invitation = TeacherInvitation.objects.create(
                school=self.school,
                email=f"teacher{i}@test.com",
                invited_by=self.admin_user,
                role=SchoolRole.TEACHER,
                status=InvitationStatus.PENDING,
                expires_at=timezone.now() + timedelta(days=7),
                batch_id=uuid.uuid4()
            )
            pending_invitations.append(invitation)
        
        # Create accepted invitation (should NOT be counted)
        TeacherInvitation.objects.create(
            school=self.school,
            email="accepted@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            status=InvitationStatus.ACCEPTED,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
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
        
        self.assertEqual(pending_count, 3)
    
    def test_count_new_registrations_requiring_first_login(self):
        """Test business rule: count users who haven't completed first login."""
        # Business scenario: school has new users who need to complete onboarding
        
        # Create users who haven't completed first login (should be counted)
        new_users = []
        for i in range(2):
            user = CustomUser.objects.create_user(
                email=f"newuser{i}@test.com",
                name=f"New User {i}",
                first_login_completed=False  # Key business state
            )
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.STUDENT
            )
            new_users.append(user)
        
        # Create user who has completed first login (should NOT be counted)
        existing_user = CustomUser.objects.create_user(
            email="existing@test.com",
            name="Existing User",
            first_login_completed=True
        )
        SchoolMembership.objects.create(
            user=existing_user,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        # Business rule: count only users who haven't completed first login
        new_registration_count = SchoolMembership.objects.filter(
            school=self.school,
            user__first_login_completed=False
        ).count()
        
        self.assertEqual(new_registration_count, 2)
    
    def test_count_incomplete_profiles(self):
        """Test business rule: count users with pending profile completion tasks."""
        # Business scenario: school has users with incomplete profiles
        
        # Create users with profile completion tasks (should be counted)
        users_with_incomplete_profiles = []
        for i in range(3):
            user = CustomUser.objects.create_user(
                email=f"incomplete{i}@test.com",
                name=f"Incomplete User {i}",
                first_login_completed=True
            )
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER
            )
            
            # Create profile completion task
            Task.objects.create(
                user=user,
                title="Complete Your Profile",
                status="pending",
                task_type="onboarding",
                is_system_generated=True
            )
            users_with_incomplete_profiles.append(user)
        
        # Create user without profile tasks (should NOT be counted)
        complete_user = CustomUser.objects.create_user(
            email="complete@test.com",
            name="Complete User",
            first_login_completed=True
        )
        SchoolMembership.objects.create(
            user=complete_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        # Business rule: count users with pending profile completion tasks
        school_users = [membership.user for membership in SchoolMembership.objects.filter(school=self.school)]
        incomplete_profile_count = Task.objects.filter(
            user__in=school_users,
            title__icontains="Complete Your Profile",
            status="pending",
            is_system_generated=True
        ).count()
        
        self.assertEqual(incomplete_profile_count, 3)
    
    def test_count_overdue_tasks(self):
        """Test business rule: count tasks that are past their due date."""
        # Business scenario: school has tasks that are overdue
        
        # Create overdue task (should be counted)
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
            due_date=timezone.now() - timedelta(days=1),  # Past due
            task_type="assignment"
        )
        
        # Create future task (should NOT be counted)
        future_user = CustomUser.objects.create_user(
            email="future@test.com",
            name="Future User"
        )
        SchoolMembership.objects.create(
            user=future_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        Task.objects.create(
            user=future_user,
            title="Future Task",
            status="pending",
            due_date=timezone.now() + timedelta(days=1),  # Future due date
            task_type="assignment"
        )
        
        # Create completed overdue task (should NOT be counted)
        completed_user = CustomUser.objects.create_user(
            email="completed@test.com",
            name="Completed User"
        )
        SchoolMembership.objects.create(
            user=completed_user,
            school=self.school,
            role=SchoolRole.TEACHER
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
        other_school = School.objects.create(
            name="Other School",
            description="Another school"
        )
        
        other_admin = CustomUser.objects.create_user(
            email="other@school.com",
            name="Other Admin"
        )
        
        SchoolMembership.objects.create(
            user=other_admin,
            school=other_school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
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
        TeacherInvitation.objects.create(
            school=self.school,
            email="our_teacher@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
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
    
    def test_total_notification_count_calculation(self):
        """Test business rule: total notification count sums all relevant counts."""
        # Business scenario: calculate total notifications for dashboard
        
        # Create test data for each notification type
        
        # 1 pending invitation
        TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@test.com",
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            status=InvitationStatus.PENDING,
            expires_at=timezone.now() + timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        # 1 new registration
        new_user = CustomUser.objects.create_user(
            email="newuser@test.com",
            name="New User",
            first_login_completed=False
        )
        SchoolMembership.objects.create(
            user=new_user,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        # 1 incomplete profile
        incomplete_user = CustomUser.objects.create_user(
            email="incomplete@test.com",
            name="Incomplete User",
            first_login_completed=True
        )
        SchoolMembership.objects.create(
            user=incomplete_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        Task.objects.create(
            user=incomplete_user,
            title="Complete Your Profile",
            status="pending",
            task_type="onboarding",
            is_system_generated=True
        )
        
        # 1 overdue task
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
        
        # Calculate individual counts
        pending_invitations = TeacherInvitation.objects.filter(
            school=self.school,
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now()
        ).count()
        
        new_registrations = SchoolMembership.objects.filter(
            school=self.school,
            user__first_login_completed=False
        ).count()
        
        school_users = [membership.user for membership in SchoolMembership.objects.filter(school=self.school)]
        incomplete_profiles = Task.objects.filter(
            user__in=school_users,
            title__icontains="Complete Your Profile",
            status="pending",
            is_system_generated=True
        ).count()
        
        overdue_tasks = Task.objects.filter(
            user__in=school_users,
            status="pending",
            due_date__lt=timezone.now()
        ).count()
        
        # Business rule: total is sum of all notification types
        total_count = pending_invitations + new_registrations + incomplete_profiles + overdue_tasks
        
        self.assertEqual(pending_invitations, 1)
        self.assertEqual(new_registrations, 1)
        self.assertEqual(incomplete_profiles, 1)
        self.assertEqual(overdue_tasks, 1)
        self.assertEqual(total_count, 4)