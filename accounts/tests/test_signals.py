"""
Comprehensive tests for accounts signals.

These tests verify that all signal handlers work correctly and maintain data integrity
throughout the system, particularly the critical ensure_user_has_school_membership signal.
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from accounts.models import (
    ActivityType,
    School,
    SchoolActivity,
    SchoolInvitation,
    SchoolMembership,
    SchoolRole,
)
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class EnsureUserHasSchoolMembershipSignalTest(TransactionTestCase):
    """Test the ensure_user_has_school_membership signal."""

    def test_superuser_creation_skips_signal(self):
        """Test that superuser creation does not trigger school creation."""
        initial_school_count = School.objects.count()
        initial_membership_count = SchoolMembership.objects.count()

        # Create superuser
        superuser = User.objects.create_superuser(email="admin@example.com", password="testpass123", name="Admin User")

        # No new schools or memberships should be created
        self.assertEqual(School.objects.count(), initial_school_count)
        self.assertEqual(SchoolMembership.objects.count(), initial_membership_count)
        self.assertTrue(superuser.is_superuser)

    def test_user_with_existing_membership_skips_signal(self):
        """Test that users with existing memberships don't trigger school creation."""
        # Create school and user separately
        school = School.objects.create(name="Existing School")
        user = User.objects.create_user(email="user@example.com", name="Test User")
        SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.TEACHER, is_active=True)

        initial_school_count = School.objects.count()

        # Trigger the signal by saving the user again
        user.save()

        # No new school should be created
        self.assertEqual(School.objects.count(), initial_school_count)

    def test_signal_skips_during_atomic_block(self):
        """Test that signal is skipped when in atomic transaction."""
        initial_school_count = School.objects.count()

        # Create user inside atomic block
        with transaction.atomic():
            user = User.objects.create_user(email="atomic@example.com", name="Atomic User")

        # Signal should have been skipped due to atomic block
        # but we should manually verify the user has no membership yet
        self.assertFalse(SchoolMembership.objects.filter(user=user, is_active=True).exists())


class SchoolActivitySignalsTest(BaseTestCase):
    """Test signals that create SchoolActivity records."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.school = School.objects.create(name="Test School")
        self.user = User.objects.create_user(email="user@example.com", name="Test User")
        self.inviter = User.objects.create_user(email="inviter@example.com", name="Inviter User")

    def test_student_membership_creates_activity(self):
        """Test that creating a student membership creates appropriate activity."""
        initial_activity_count = SchoolActivity.objects.count()

        # Create student membership
        membership = SchoolMembership.objects.create(
            user=self.user, school=self.school, role=SchoolRole.STUDENT, is_active=True
        )

        # Should create one activity record
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count + 1)

        # Verify activity details
        activity = SchoolActivity.objects.latest("timestamp")
        self.assertEqual(activity.school, self.school)
        self.assertEqual(activity.activity_type, ActivityType.STUDENT_JOINED)
        self.assertEqual(activity.actor, self.user)
        self.assertEqual(activity.target_user, self.user)
        self.assertIn("joined as a student", activity.description)
        self.assertEqual(activity.metadata["role"], SchoolRole.STUDENT)

    def test_teacher_membership_creates_activity(self):
        """Test that creating a teacher membership creates appropriate activity."""
        initial_activity_count = SchoolActivity.objects.count()

        # Create teacher membership
        membership = SchoolMembership.objects.create(
            user=self.user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

        # Should create one activity record
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count + 1)

        # Verify activity details
        activity = SchoolActivity.objects.latest("timestamp")
        self.assertEqual(activity.activity_type, ActivityType.TEACHER_JOINED)
        self.assertIn("joined as a teacher", activity.description)

    def test_admin_membership_does_not_create_activity(self):
        """Test that admin/owner memberships don't create activities."""
        initial_activity_count = SchoolActivity.objects.count()

        # Create admin membership
        SchoolMembership.objects.create(
            user=self.user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Create owner membership
        SchoolMembership.objects.create(
            user=self.inviter, school=self.school, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )

        # Should not create any activity records
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count)

    def test_inactive_membership_does_not_create_activity(self):
        """Test that inactive memberships don't create activities."""
        initial_activity_count = SchoolActivity.objects.count()

        # Create inactive membership
        SchoolMembership.objects.create(user=self.user, school=self.school, role=SchoolRole.STUDENT, is_active=False)

        # Should not create activity
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count)

    def test_invitation_sent_creates_activity(self):
        """Test that creating an invitation creates 'invitation sent' activity."""
        initial_activity_count = SchoolActivity.objects.count()

        # Create invitation
        invitation = SchoolInvitation.objects.create(
            school=self.school,
            email="newteacher@example.com",
            role=SchoolRole.TEACHER,
            invited_by=self.inviter,
            expires_at=timezone.now() + timedelta(days=7),
        )

        # Should create one activity record
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count + 1)

        # Verify activity details
        activity = SchoolActivity.objects.latest("timestamp")
        self.assertEqual(activity.school, self.school)
        self.assertEqual(activity.activity_type, ActivityType.INVITATION_SENT)
        self.assertEqual(activity.actor, self.inviter)
        self.assertEqual(activity.target_invitation, invitation)
        self.assertIn("invited newteacher@example.com", activity.description)
        self.assertEqual(activity.metadata["email"], "newteacher@example.com")
        self.assertEqual(activity.metadata["role"], SchoolRole.TEACHER)

    def test_invitation_acceptance_creates_activity(self):
        """Test that accepting an invitation creates appropriate activity."""
        # Create invitation first
        invitation = SchoolInvitation.objects.create(
            school=self.school,
            email=self.user.email,
            role=SchoolRole.TEACHER,
            invited_by=self.inviter,
            expires_at=timezone.now() + timedelta(days=7),
        )

        initial_activity_count = SchoolActivity.objects.count()

        # Accept invitation by updating it
        invitation.is_accepted = True
        invitation.save()

        # Should create additional activity record for acceptance
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count + 1)

        # Verify acceptance activity
        acceptance_activity = SchoolActivity.objects.latest("timestamp")
        self.assertEqual(acceptance_activity.activity_type, ActivityType.INVITATION_ACCEPTED)
        self.assertEqual(acceptance_activity.target_user, self.user)

    def test_invitation_acceptance_handles_missing_user(self):
        """Test that invitation acceptance handles cases where user doesn't exist yet."""
        # Create invitation for non-existent user
        invitation = SchoolInvitation.objects.create(
            school=self.school,
            email="nonexistent@example.com",
            role=SchoolRole.TEACHER,
            invited_by=self.inviter,
            expires_at=timezone.now() + timedelta(days=7),
        )

        initial_activity_count = SchoolActivity.objects.count()

        # Accept invitation
        invitation.is_accepted = True
        invitation.save()

        # Should still create activity, but without target_user
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count + 1)

        acceptance_activity = SchoolActivity.objects.latest("timestamp")
        self.assertIsNone(acceptance_activity.target_user)


class SignalIntegrationTest(BaseTestCase):
    """Test that signals work correctly together in realistic scenarios."""

    def test_complete_user_signup_flow_with_signals(self):
        """Test that signals work correctly during complete user signup."""
        initial_activity_count = SchoolActivity.objects.count()

        # Simulate normal signup flow (creates user + school atomically)
        with transaction.atomic():
            user = User.objects.create_user(email="newuser@example.com", name="New User")
            school = School.objects.create(name="New User's School", contact_email=user.email)
            membership = SchoolMembership.objects.create(
                user=user, school=school, role=SchoolRole.SCHOOL_OWNER, is_active=True
            )

        # Signal should not have created duplicate school (due to atomic block)
        self.assertEqual(user.school_memberships.filter(is_active=True).count(), 1)

        # No activity should be created for owner role
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count)

    def test_teacher_invitation_flow_with_signals(self):
        """Test signals work correctly in teacher invitation flow."""
        school = School.objects.create(name="School")
        owner = User.objects.create_user(email="owner@example.com", name="Owner")

        initial_activity_count = SchoolActivity.objects.count()

        # Send invitation
        invitation = SchoolInvitation.objects.create(
            school=school,
            email="teacher@example.com",
            role=SchoolRole.TEACHER,
            invited_by=owner,
            expires_at=timezone.now() + timedelta(days=7),
        )

        # Should create invitation sent activity
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count + 1)

        # Teacher accepts invitation
        teacher = User.objects.create_user(email="teacher@example.com", name="Teacher")

        # Teacher gets membership
        membership = SchoolMembership.objects.create(
            user=teacher, school=school, role=SchoolRole.TEACHER, is_active=True
        )

        # Accept invitation
        invitation.is_accepted = True
        invitation.save()

        # Should have created:
        # 1. Invitation sent activity
        # 2. Teacher joined activity (from membership)
        # 3. Invitation accepted activity
        self.assertEqual(SchoolActivity.objects.count(), initial_activity_count + 3)

        # Verify activity types
        activities = SchoolActivity.objects.order_by("timestamp")
        latest_activities = list(activities.values_list("activity_type", flat=True))[-3:]
        self.assertIn(ActivityType.INVITATION_SENT, latest_activities)
        self.assertIn(ActivityType.TEACHER_JOINED, latest_activities)
        self.assertIn(ActivityType.INVITATION_ACCEPTED, latest_activities)
