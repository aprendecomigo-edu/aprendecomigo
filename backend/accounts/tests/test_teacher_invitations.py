"""
Tests for teacher invitation endpoints.

This module focuses on testing teacher invitation creation and acceptance:
- POST /api/accounts/teachers/invite-existing/
- GET /api/accounts/invitations/{token}/details/
- POST /api/accounts/invitations/{token}/accept/
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
    SchoolInvitation,
    SchoolMembership,
    SchoolRole,
    TeacherCourse,
    TeacherProfile,
)


class TeacherInvitationBaseTest(TestCase):
    """Minimal base test class for teacher invitation tests."""

    def setUp(self):
        """Set up minimal test data for invitation tests."""
        self.client = APIClient()

        # Create test educational system and courses
        self.educational_system = EducationalSystem.objects.create(
            name="Test System", code="test", description="Test system", is_active=True
        )
        self.course1 = Course.objects.create(
            name="Test Math", code="TEST_635",
            educational_system=self.educational_system, education_level="elementary"
        )
        self.course2 = Course.objects.create(
            name="Test Portuguese", code="TEST_639",
            educational_system=self.educational_system, education_level="elementary"
        )

        # Create test school
        self.school = School.objects.create(
            name="Test School", description="Test school", address="Test Address"
        )

    def create_user_with_token(self, email, name, phone="+351912000000"):
        """Factory method to create user with auth token."""
        user = CustomUser.objects.create_user(email=email, name=name, phone_number=phone)
        token = AuthToken.objects.create(user)[1]
        return user, token

    def create_school_membership(self, user, role):
        """Factory method to create school membership."""
        return SchoolMembership.objects.create(
            user=user, school=self.school, role=role, is_active=True
        )

    def create_invitation(self, email, invited_by, expires_in_days=7):
        """Factory method to create a school invitation."""
        from accounts.db_queries import create_school_invitation
        
        return create_school_invitation(
            school_id=self.school.id,
            email=email,
            invited_by=invited_by,
            role=SchoolRole.TEACHER,
        )

    def authenticate_user(self, token):
        """Helper method to authenticate a user with their token."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def clear_authentication(self):
        """Helper method to clear authentication."""
        self.client.credentials()


class InviteExistingTeacherTest(TeacherInvitationBaseTest):
    """Tests for invite existing user endpoint (POST /api/accounts/teachers/invite-existing/)."""

    def setUp(self):
        super().setUp()
        
        # Create school owner
        self.owner, self.owner_token = self.create_user_with_token(
            "owner@example.com", "School Owner", "+351912000001"
        )
        self.create_school_membership(self.owner, SchoolRole.SCHOOL_OWNER)

        # Create users to invite
        self.invitee, _ = self.create_user_with_token(
            "invitee@example.com", "Invitee User", "+351912000002"
        )
        
        self.existing_teacher, _ = self.create_user_with_token(
            "teacher@example.com", "Existing Teacher", "+351912000003"
        )
        TeacherProfile.objects.create(user=self.existing_teacher, bio="Already a teacher")
        self.create_school_membership(self.existing_teacher, SchoolRole.TEACHER)

        # Create regular user without permission
        self.regular_user, self.regular_token = self.create_user_with_token(
            "regular@example.com", "Regular User", "+351912000004"
        )

    def test_school_owner_invites_existing_user(self):
        """Test that school owner can invite existing user as teacher."""
        self.authenticate_user(self.owner_token)

        data = {
            "email": self.invitee.email,
            "school_id": self.school.id,
            "send_email": False,
            "send_sms": False,
        }

        url = reverse("accounts:teacher-invite-existing")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response structure
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertIn("invitation", response_data)
        self.assertIn("notifications_sent", response_data)

        invitation_data = response_data["invitation"]
        self.assertIn("token", invitation_data)
        self.assertIn("link", invitation_data)
        self.assertIn("expires_at", invitation_data)
        self.assertEqual(invitation_data["school"]["id"], self.school.id)
        self.assertEqual(invitation_data["invited_user"]["email"], self.invitee.email)

        # Check invitation was created in database
        invitation = SchoolInvitation.objects.get(
            email=self.invitee.email,
            school=self.school,
            role=SchoolRole.TEACHER,
        )
        self.assertFalse(invitation.is_accepted)
        self.assertTrue(invitation.is_valid())

        # Check no teacher profile or membership created yet
        self.assertFalse(hasattr(self.invitee, "teacher_profile"))
        teacher_memberships = SchoolMembership.objects.filter(
            user=self.invitee, school=self.school, role=SchoolRole.TEACHER
        )
        self.assertEqual(teacher_memberships.count(), 0)

    def test_invite_user_already_teacher_in_school(self):
        """Test that inviting user who is already teacher fails."""
        self.authenticate_user(self.owner_token)

        data = {
            "email": self.existing_teacher.email,
            "school_id": self.school.id,
        }

        url = reverse("accounts:teacher-invite-existing")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already a teacher", response.json()["non_field_errors"][0])

    def test_invite_nonexistent_user(self):
        """Test inviting non-existent user fails."""
        self.authenticate_user(self.owner_token)

        data = {
            "email": "nonexistent@example.com",
            "school_id": self.school.id,
        }

        url = reverse("accounts:teacher-invite-existing")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not exist", response.json()["email"][0])

    def test_invite_duplicate_pending_invitation(self):
        """Test that duplicate pending invitations are not allowed."""
        # Create an existing invitation
        self.create_invitation(self.invitee.email, self.owner)

        self.authenticate_user(self.owner_token)

        data = {
            "email": self.invitee.email,
            "school_id": self.school.id,
        }

        url = reverse("accounts:teacher-invite-existing")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pending invitation", response.json()["non_field_errors"][0])

    def test_invite_without_permission(self):
        """Test that regular users cannot invite others."""
        self.authenticate_user(self.regular_token)

        data = {
            "email": self.invitee.email,
            "school_id": self.school.id,
        }

        url = reverse("accounts:teacher-invite-existing")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InvitationAcceptanceTest(TeacherInvitationBaseTest):
    """Tests for invitation acceptance endpoints."""

    def setUp(self):
        super().setUp()
        
        # Create school owner and invitee
        self.owner, _ = self.create_user_with_token(
            "owner@example.com", "School Owner", "+351912000001"
        )
        self.create_school_membership(self.owner, SchoolRole.SCHOOL_OWNER)

        self.invitee, self.invitee_token = self.create_user_with_token(
            "invitee@example.com", "Invitee User", "+351912000002"
        )
        
        self.wrong_user, self.wrong_user_token = self.create_user_with_token(
            "wrong@example.com", "Wrong User", "+351912000003"
        )

        # Create a test invitation
        self.invitation = self.create_invitation(self.invitee.email, self.owner)

    def test_get_invitation_details(self):
        """Test getting invitation details before acceptance."""
        self.authenticate_user(self.invitee_token)

        url = reverse("accounts:invitation-details", kwargs={"token": self.invitation.token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertIn("invitation", response_data)
        self.assertIn("can_accept", response_data)
        self.assertTrue(response_data["can_accept"])

        invitation_data = response_data["invitation"]
        self.assertEqual(invitation_data["school"]["id"], self.school.id)
        self.assertEqual(invitation_data["role"], SchoolRole.TEACHER)

    def test_accept_invitation_success(self):
        """Test successful invitation acceptance."""
        self.authenticate_user(self.invitee_token)

        data = {
            "bio": "Accepted invitation, excited to teach!",
            "specialty": "Mathematics",
            "course_ids": [self.course1.id, self.course2.id],
        }

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertIn("teacher", response_data)
        self.assertIn("school_membership", response_data)
        self.assertIn("courses_added", response_data)
        self.assertEqual(response_data["courses_added"], 2)

        # Check teacher profile was created
        self.assertTrue(hasattr(self.invitee, "teacher_profile"))
        teacher_profile = self.invitee.teacher_profile
        self.assertEqual(teacher_profile.bio, data["bio"])
        self.assertEqual(teacher_profile.specialty, data["specialty"])

        # Check school membership was created
        membership = SchoolMembership.objects.get(
            user=self.invitee, school=self.school, role=SchoolRole.TEACHER
        )
        self.assertTrue(membership.is_active)

        # Check course associations
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 2)

        # Check invitation was marked as accepted
        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.is_accepted)

    def test_accept_invitation_minimal_data(self):
        """Test accepting invitation with minimal data."""
        self.authenticate_user(self.invitee_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check teacher profile was created with defaults
        teacher_profile = self.invitee.teacher_profile
        self.assertEqual(teacher_profile.bio, "")
        self.assertEqual(teacher_profile.specialty, "")

        # Check no courses were associated
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 0)

    def test_accept_invitation_wrong_user(self):
        """Test that wrong user cannot accept invitation."""
        self.authenticate_user(self.wrong_user_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("not for your account", response.json()["error"])

    def test_accept_invalid_token(self):
        """Test accepting invitation with invalid token."""
        self.authenticate_user(self.invitee_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": "invalid-token"})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Invalid invitation token", response.json()["error"])

    def test_accept_already_accepted_invitation(self):
        """Test accepting already accepted invitation."""
        # Mark invitation as accepted
        self.invitation.is_accepted = True
        self.invitation.save()

        self.authenticate_user(self.invitee_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been accepted", response.json()["error"])

    def test_accept_expired_invitation(self):
        """Test accepting expired invitation."""
        # Make invitation expired
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()

        self.authenticate_user(self.invitee_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", response.json()["error"])

    def test_accept_invitation_existing_teacher_profile(self):
        """Test accepting invitation when user already has teacher profile."""
        # Create teacher profile first
        TeacherProfile.objects.create(
            user=self.invitee, bio="Existing bio", specialty="Existing specialty"
        )

        self.authenticate_user(self.invitee_token)

        data = {
            "bio": "New bio from invitation",  # This should be ignored
            "specialty": "New specialty",  # This should be ignored
            "course_ids": [self.course1.id],
        }

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check existing teacher profile was used (bio/specialty not updated)
        teacher_profile = self.invitee.teacher_profile
        self.assertEqual(teacher_profile.bio, "Existing bio")
        self.assertEqual(teacher_profile.specialty, "Existing specialty")

        # But courses should still be added
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 1)

    def test_unauthenticated_access_invitation_details(self):
        """Test that unauthenticated users can view invitation details."""
        self.clear_authentication()

        url = reverse("accounts:invitation-details", kwargs={"token": self.invitation.token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertIn("invitation", response_data)
        self.assertIn("can_accept", response_data)
        self.assertFalse(response_data["can_accept"])
        self.assertIn("reason", response_data)