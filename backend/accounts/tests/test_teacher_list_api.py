"""
Tests for teacher list API endpoints.

This module focuses on testing teacher list filtering and pending invitations
via GET /api/accounts/teachers/
"""

from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import (
    Course,
    CustomUser,
    EducationalSystem,
    School,
    SchoolMembership,
    SchoolRole,
    TeacherProfile,
)


class TeacherListBaseTest(TestCase):
    """Minimal base test class for teacher list tests."""

    def setUp(self):
        """Set up minimal test data for teacher list tests."""
        self.client = APIClient()

        # Create test schools
        self.school1 = School.objects.create(
            name="School 1", description="Test school 1", address="Address 1"
        )
        self.school2 = School.objects.create(
            name="School 2", description="Test school 2", address="Address 2"
        )

    def create_user_with_token(self, email, name, phone="+351912000000"):
        """Factory method to create user with auth token."""
        user = CustomUser.objects.create_user(email=email, name=name, phone_number=phone)
        token = AuthToken.objects.create(user)[1]
        return user, token

    def create_teacher_with_membership(self, email, name, phone, school, bio="Test bio", specialty="Test specialty"):
        """Factory method to create teacher with profile and membership."""
        user, token = self.create_user_with_token(email, name, phone)
        teacher_profile = TeacherProfile.objects.create(user=user, bio=bio, specialty=specialty)
        SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.TEACHER, is_active=True)
        return user, token, teacher_profile

    def create_school_membership(self, user, school, role):
        """Factory method to create school membership."""
        return SchoolMembership.objects.create(user=user, school=school, role=role, is_active=True)

    def authenticate_user(self, token):
        """Helper method to authenticate a user with their token."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def get_teachers_from_response(self, response):
        """Helper to extract teachers from potentially paginated response."""
        response_data = response.json()
        if "results" in response_data:
            return response_data["results"]
        return response_data


class TeacherListFilteringTest(TeacherListBaseTest):
    """Tests for teacher list filtering (GET /api/accounts/teachers/)."""

    def setUp(self):
        super().setUp()

        # Create school owner for both schools
        self.owner, self.owner_token = self.create_user_with_token(
            "owner@example.com", "School Owner", "+351912000001"
        )
        self.create_school_membership(self.owner, self.school1, SchoolRole.SCHOOL_OWNER)
        self.create_school_membership(self.owner, self.school2, SchoolRole.SCHOOL_OWNER)

        # Create school admin for school1 only
        self.admin, self.admin_token = self.create_user_with_token(
            "admin@example.com", "School Admin", "+351912000002"
        )
        self.create_school_membership(self.admin, self.school1, SchoolRole.SCHOOL_ADMIN)

        # Create teachers in different schools
        self.teacher1, self.teacher1_token, _ = self.create_teacher_with_membership(
            "teacher1@example.com", "Teacher One", "+351912000003", self.school1, "Teacher 1 bio", "Mathematics"
        )
        
        self.teacher2, self.teacher2_token, _ = self.create_teacher_with_membership(
            "teacher2@example.com", "Teacher Two", "+351912000004", self.school1, "Teacher 2 bio", "Physics"
        )
        
        self.teacher3, self.teacher3_token, _ = self.create_teacher_with_membership(
            "teacher3@example.com", "Teacher Three", "+351912000005", self.school2, "Teacher 3 bio", "Chemistry"
        )

        # Create regular user with no memberships
        self.regular_user, self.regular_token = self.create_user_with_token(
            "regular@example.com", "Regular User", "+351912000006"
        )

    def test_school_owner_sees_teachers_from_managed_schools(self):
        """Test that school owner sees teachers only from schools they manage."""
        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        teachers = self.get_teachers_from_response(response)
        teacher_emails = [t["user"]["email"] for t in teachers]

        # Should see teachers from both school1 and school2 (owner manages both)
        self.assertIn(self.teacher1.email, teacher_emails)  # school1
        self.assertIn(self.teacher2.email, teacher_emails)  # school1
        self.assertIn(self.teacher3.email, teacher_emails)  # school2

    def test_school_admin_sees_teachers_from_their_school_only(self):
        """Test that school admin sees teachers only from their school."""
        self.authenticate_user(self.admin_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        teachers = self.get_teachers_from_response(response)
        teacher_emails = [t["user"]["email"] for t in teachers]

        # Should see teachers from school1 only (admin only manages school1)
        self.assertIn(self.teacher1.email, teacher_emails)  # school1
        self.assertIn(self.teacher2.email, teacher_emails)  # school1
        self.assertNotIn(self.teacher3.email, teacher_emails)  # school2

    def test_teacher_sees_own_profile_only(self):
        """Test that teacher sees only their own profile."""
        self.authenticate_user(self.teacher2_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        teachers = self.get_teachers_from_response(response)
        self.assertEqual(len(teachers), 1)
        self.assertEqual(teachers[0]["user"]["email"], self.teacher2.email)

    def test_regular_user_sees_no_teachers(self):
        """Test that regular user (not teacher, not admin) sees no teachers."""
        self.authenticate_user(self.regular_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        teachers = self.get_teachers_from_response(response)
        self.assertEqual(len(teachers), 0)


class TeacherListWithPendingInvitationsTest(TeacherListBaseTest):
    """Tests for teacher list including pending invitations."""

    def setUp(self):
        super().setUp()

        # Create school owner
        self.owner, self.owner_token = self.create_user_with_token(
            "owner@example.com", "School Owner", "+351912000001"
        )
        self.create_school_membership(self.owner, self.school1, SchoolRole.SCHOOL_OWNER)

        # Create active teacher
        self.active_teacher, _, _ = self.create_teacher_with_membership(
            "teacher@example.com", "Active Teacher", "+351912000002", self.school1
        )

        # Create user for pending invitation
        self.invited_user, self.invited_token = self.create_user_with_token(
            "invited@example.com", "Invited User", "+351912000003"
        )

        # Create regular user for permissions test
        self.regular_user, self.regular_token = self.create_user_with_token(
            "regular@example.com", "Regular User", "+351912000004"
        )

    def create_pending_invitation(self, email, school, invited_by, expires_in_days=7):
        """Factory method to create a pending invitation."""
        from accounts.db_queries import create_school_invitation
        
        return create_school_invitation(
            school_id=school.id,
            email=email,
            invited_by=invited_by,
            role=SchoolRole.TEACHER,
        )

    def test_teacher_list_without_pending_flag(self):
        """Test that teacher list doesn't include pending invitations by default."""
        # Create pending invitation
        self.create_pending_invitation(self.invited_user.email, self.school1, self.owner)

        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teachers = self.get_teachers_from_response(response)

        teacher_emails = [t["user"]["email"] for t in teachers]
        self.assertIn(self.active_teacher.email, teacher_emails)  # Active teacher
        self.assertNotIn(self.invited_user.email, teacher_emails)  # Pending invitation

    def test_teacher_list_with_pending_flag(self):
        """Test that teacher list includes pending invitations when requested."""
        # Create pending invitation
        invitation = self.create_pending_invitation(self.invited_user.email, self.school1, self.owner)

        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teachers = response.json()

        # Should include both active teachers and pending invitations
        active_teachers = [t for t in teachers if t["status"] == "active"]
        pending_teachers = [t for t in teachers if t["status"] == "pending"]

        self.assertEqual(len(active_teachers), 1)  # active_teacher
        self.assertEqual(len(pending_teachers), 1)  # invited_user invitation

        # Check active teacher
        active_teacher = active_teachers[0]
        self.assertEqual(active_teacher["user"]["email"], self.active_teacher.email)
        self.assertIsNotNone(active_teacher["id"])  # Has teacher profile

        # Check pending teacher
        pending_teacher = pending_teachers[0]
        self.assertEqual(pending_teacher["user"]["email"], self.invited_user.email)
        self.assertIsNone(pending_teacher["id"])  # No teacher profile yet
        self.assertIn("invitation", pending_teacher)
        self.assertEqual(pending_teacher["invitation"]["token"], invitation.token)

    def test_pending_invitation_includes_invitation_details(self):
        """Test that pending invitations include all necessary invitation details."""
        invitation = self.create_pending_invitation(self.invited_user.email, self.school1, self.owner)

        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        teachers = response.json()
        pending_teachers = [t for t in teachers if t["status"] == "pending"]

        self.assertEqual(len(pending_teachers), 1)

        pending_teacher = pending_teachers[0]
        invitation_data = pending_teacher["invitation"]

        # Check invitation details
        self.assertEqual(invitation_data["id"], invitation.id)
        self.assertEqual(invitation_data["token"], invitation.token)
        self.assertIn("link", invitation_data)
        self.assertIn("expires_at", invitation_data)
        self.assertEqual(invitation_data["invited_by"], self.owner.name)

    def test_expired_invitations_not_included(self):
        """Test that expired invitations are not included in the list."""
        invitation = self.create_pending_invitation(self.invited_user.email, self.school1, self.owner)
        
        # Make the invitation expired
        invitation.expires_at = timezone.now() - timedelta(days=1)
        invitation.save()

        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        teachers = response.json()
        pending_teachers = [t for t in teachers if t["status"] == "pending"]

        # Expired invitation should not be included
        self.assertEqual(len(pending_teachers), 0)

    def test_accepted_invitations_not_included_as_pending(self):
        """Test that accepted invitations are not included as pending."""
        invitation = self.create_pending_invitation(self.invited_user.email, self.school1, self.owner)
        
        # Mark invitation as accepted
        invitation.is_accepted = True
        invitation.save()

        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        teachers = response.json()
        pending_teachers = [t for t in teachers if t["status"] == "pending"]

        # Accepted invitation should not be included as pending
        self.assertEqual(len(pending_teachers), 0)

    def test_regular_user_cannot_see_pending_invitations(self):
        """Test that regular users can't see pending invitations."""
        # Create pending invitation  
        self.create_pending_invitation(self.invited_user.email, self.school1, self.owner)

        self.authenticate_user(self.regular_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        teachers = response.json()

        # Regular user should see empty list (no teachers, no pending invitations)
        self.assertEqual(len(teachers), 0)