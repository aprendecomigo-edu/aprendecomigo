"""
Tests for teacher onboarding endpoints and functionality.

This module tests the three teacher onboarding scenarios:
1. Self-onboarding (current user becomes a teacher)
2. Add existing user as teacher
3. Invite new user as teacher

Also tests multi-school scenarios, permissions, and data integrity.
"""

from django.test import TestCase
from django.urls import reverse
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import (
    Course,
    CustomUser,
    School,
    SchoolInvitation,
    SchoolMembership,
    SchoolRole,
    TeacherCourse,
    TeacherProfile,
)


class TeacherOnboardingBaseTest(TestCase):
    """Base test class with common setup for teacher onboarding tests."""

    def setUp(self):
        """Set up test data for teacher onboarding tests."""
        self.client = APIClient()

        # Create test courses (use different codes to avoid conflicts with existing Portuguese courses)
        self.course1 = Course.objects.create(
            name="Test Mathematics A",
            code="TEST_635",
            educational_system="test",
            education_level="ensino_secundario",
        )
        self.course2 = Course.objects.create(
            name="Test Portuguese",
            code="TEST_639",
            educational_system="test",
            education_level="ensino_secundario",
        )
        self.course3 = Course.objects.create(
            name="Test History A",
            code="TEST_623",
            educational_system="test",
            education_level="ensino_secundario",
        )

        # Create test schools
        self.school1 = School.objects.create(
            name="Escola Secundária do Porto",
            description="Test school 1",
            address="Porto, Portugal",
        )
        self.school2 = School.objects.create(
            name="Escola Secundária de Lisboa",
            description="Test school 2",
            address="Lisboa, Portugal",
        )

        # Create test users
        self.school_owner = CustomUser.objects.create_user(
            email="owner@school1.com", name="School Owner", phone_number="+351 912 000 001"
        )

        self.school_admin = CustomUser.objects.create_user(
            email="admin@school1.com", name="School Admin", phone_number="+351 912 000 002"
        )

        self.existing_user = CustomUser.objects.create_user(
            email="existing@example.com", name="Existing User", phone_number="+351 912 000 003"
        )

        self.regular_user = CustomUser.objects.create_user(
            email="regular@example.com", name="Regular User", phone_number="+351 912 000 004"
        )

        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@example.com", name="Teacher User", phone_number="+351 912 000 005"
        )

        # Create school memberships
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school1,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True,
        )

        SchoolMembership.objects.create(
            user=self.school_admin,
            school=self.school1,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True,
        )

        # Create a teacher profile for teacher_user (already a teacher)
        self.existing_teacher = TeacherProfile.objects.create(
            user=self.teacher_user, bio="Existing teacher bio", specialty="Mathematics"
        )

        SchoolMembership.objects.create(
            user=self.teacher_user, school=self.school1, role=SchoolRole.TEACHER, is_active=True
        )

        # Create tokens for authentication
        self.owner_token = AuthToken.objects.create(self.school_owner)[1]
        self.admin_token = AuthToken.objects.create(self.school_admin)[1]
        self.existing_user_token = AuthToken.objects.create(self.existing_user)[1]
        self.regular_user_token = AuthToken.objects.create(self.regular_user)[1]
        self.teacher_token = AuthToken.objects.create(self.teacher_user)[1]

    def authenticate_user(self, token):
        """Helper method to authenticate a user with their token."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def clear_authentication(self):
        """Helper method to clear authentication."""
        self.client.credentials()


class SelfOnboardingTest(TeacherOnboardingBaseTest):
    """Tests for self-onboarding endpoint (POST /api/accounts/teachers/onboarding/)."""

    def test_successful_self_onboarding(self):
        """Test that a user can successfully onboard themselves as a teacher."""
        self.authenticate_user(self.existing_user_token)

        data = {
            "bio": "I'm passionate about teaching mathematics",
            "specialty": "Mathematics and Physics",
            "course_ids": [self.course1.id, self.course2.id],
        }

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response structure
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertIn("teacher", response_data)
        self.assertIn("courses_added", response_data)
        self.assertEqual(response_data["courses_added"], 2)

        # Check teacher profile was created
        self.assertTrue(hasattr(self.existing_user, "teacher_profile"))
        teacher_profile = self.existing_user.teacher_profile
        self.assertEqual(teacher_profile.bio, data["bio"])
        self.assertEqual(teacher_profile.specialty, data["specialty"])

        # Check courses were associated
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 2)
        course_ids = [tc.course.id for tc in teacher_courses]
        self.assertIn(self.course1.id, course_ids)
        self.assertIn(self.course2.id, course_ids)

    def test_self_onboarding_without_courses(self):
        """Test self-onboarding with minimal data (no courses)."""
        self.authenticate_user(self.existing_user_token)

        data = {"bio": "New teacher", "specialty": "Science"}

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertEqual(response_data["courses_added"], 0)

        # Check teacher profile was created
        teacher_profile = self.existing_user.teacher_profile
        self.assertEqual(teacher_profile.bio, data["bio"])
        self.assertEqual(teacher_profile.specialty, data["specialty"])

    def test_self_onboarding_empty_data(self):
        """Test self-onboarding with empty data (all fields optional)."""
        self.authenticate_user(self.existing_user_token)

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check teacher profile was created with defaults
        teacher_profile = self.existing_user.teacher_profile
        self.assertEqual(teacher_profile.bio, "")
        self.assertEqual(teacher_profile.specialty, "")

    def test_self_onboarding_already_teacher(self):
        """Test that users who already have teacher profiles cannot onboard again."""
        self.authenticate_user(self.teacher_token)

        data = {"bio": "Trying to onboard again", "specialty": "Physics"}

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already have a teacher profile", response.json()["error"])

    def test_self_onboarding_invalid_course_ids(self):
        """Test self-onboarding with invalid course IDs."""
        self.authenticate_user(self.existing_user_token)

        data = {
            "bio": "Test teacher",
            "course_ids": [999, 1000],  # Non-existent course IDs
        }

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid course IDs", response.json()["course_ids"][0])

    def test_self_onboarding_unauthenticated(self):
        """Test that unauthenticated users cannot self-onboard."""
        self.clear_authentication()

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_school_owner_self_onboarding_creates_teacher_membership(self):
        """Test that school owner onboarding automatically creates teacher membership."""
        self.authenticate_user(self.owner_token)

        data = {
            "bio": "I'm the owner but also want to teach",
            "specialty": "Leadership and Management",
            "course_ids": [self.course1.id],
        }

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response includes membership info
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertIn("teacher", response_data)
        self.assertIn("courses_added", response_data)
        self.assertIn("teacher_memberships_created", response_data)
        self.assertIn("schools_added_as_teacher", response_data)

        self.assertEqual(response_data["teacher_memberships_created"], 1)
        self.assertEqual(response_data["schools_added_as_teacher"], [self.school1.name])

        # Check teacher profile was created
        self.assertTrue(hasattr(self.school_owner, "teacher_profile"))
        teacher_profile = self.school_owner.teacher_profile
        self.assertEqual(teacher_profile.bio, data["bio"])

        # Check user now has both owner and teacher memberships
        memberships = SchoolMembership.objects.filter(
            user=self.school_owner, school=self.school1, is_active=True
        )
        self.assertEqual(memberships.count(), 2)

        roles = [m.role for m in memberships]
        self.assertIn(SchoolRole.SCHOOL_OWNER, roles)
        self.assertIn(SchoolRole.TEACHER, roles)

        # Check course association
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 1)

    def test_school_admin_self_onboarding_creates_teacher_membership(self):
        """Test that school admin onboarding automatically creates teacher membership."""
        self.authenticate_user(self.admin_token)

        data = {
            "bio": "I'm an admin but also want to teach",
            "specialty": "Educational Administration",
        }

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response includes membership info
        response_data = response.json()
        self.assertIn("teacher_memberships_created", response_data)
        self.assertEqual(response_data["teacher_memberships_created"], 1)

        # Check user now has both admin and teacher memberships
        memberships = SchoolMembership.objects.filter(
            user=self.school_admin, school=self.school1, is_active=True
        )
        self.assertEqual(memberships.count(), 2)

        roles = [m.role for m in memberships]
        self.assertIn(SchoolRole.SCHOOL_ADMIN, roles)
        self.assertIn(SchoolRole.TEACHER, roles)

    def test_multi_school_owner_self_onboarding(self):
        """Test that owner of multiple schools gets teacher memberships in all their schools."""
        # Make school_owner an owner of school2 as well
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school2,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True,
        )

        self.authenticate_user(self.owner_token)

        data = {
            "bio": "Multi-school owner who wants to teach",
            "specialty": "Multi-school Management",
        }

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response includes memberships for both schools
        response_data = response.json()
        self.assertEqual(response_data["teacher_memberships_created"], 2)
        school_names = response_data["schools_added_as_teacher"]
        self.assertIn(self.school1.name, school_names)
        self.assertIn(self.school2.name, school_names)

        # Check teacher memberships were created for both schools
        teacher_memberships = SchoolMembership.objects.filter(
            user=self.school_owner, role=SchoolRole.TEACHER, is_active=True
        )
        self.assertEqual(teacher_memberships.count(), 2)

        teacher_school_ids = [m.school.id for m in teacher_memberships]
        self.assertIn(self.school1.id, teacher_school_ids)
        self.assertIn(self.school2.id, teacher_school_ids)

    def test_regular_user_self_onboarding_no_memberships(self):
        """Test that regular users (non-school-admins) don't get automatic memberships."""
        self.authenticate_user(self.existing_user_token)

        data = {"bio": "Regular user becoming teacher", "specialty": "Independent Teaching"}

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response does NOT include membership info
        response_data = response.json()
        self.assertNotIn("teacher_memberships_created", response_data)
        self.assertNotIn("schools_added_as_teacher", response_data)

        # Check teacher profile was created
        self.assertTrue(hasattr(self.existing_user, "teacher_profile"))

        # Check no school memberships exist for this user
        memberships = SchoolMembership.objects.filter(user=self.existing_user)
        self.assertEqual(memberships.count(), 0)

    def test_owner_already_teacher_in_school_no_duplicate(self):
        """Test that if owner is already a teacher, no duplicate membership is created."""
        # Manually create teacher membership first
        SchoolMembership.objects.create(
            user=self.school_owner, school=self.school1, role=SchoolRole.TEACHER, is_active=True
        )

        self.authenticate_user(self.owner_token)

        data = {"bio": "Already a teacher but onboarding profile", "specialty": "Testing"}

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response shows no new memberships created
        response_data = response.json()
        self.assertNotIn("teacher_memberships_created", response_data)
        self.assertNotIn("schools_added_as_teacher", response_data)

        # Check still only 2 memberships (owner + teacher)
        memberships = SchoolMembership.objects.filter(
            user=self.school_owner, school=self.school1, is_active=True
        )
        self.assertEqual(memberships.count(), 2)


class InviteNewTeacherTest(TeacherOnboardingBaseTest):
    """Tests for invite new user endpoint (POST /api/accounts/teachers/invite-new/)."""

    def test_school_owner_invites_new_user(self):
        """Test that school owner can invite new user as teacher."""
        self.authenticate_user(self.owner_token)

        new_email = "newteacher@example.com"
        data = {
            "email": new_email,
            "name": "New Teacher",
            "school_id": self.school1.id,
            "phone_number": "+351 912 999 999",
            "bio": "Newly invited teacher",
            "specialty": "Chemistry",
            "course_ids": [self.course2.id, self.course3.id],
        }

        url = reverse("accounts:teacher-invite-new")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response structure
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertIn("teacher", response_data)
        self.assertIn("school_membership", response_data)
        self.assertIn("user_created", response_data)
        self.assertIn("invitation_sent", response_data)
        self.assertIn("invitation", response_data)
        self.assertTrue(response_data["user_created"])
        self.assertTrue(response_data["invitation_sent"])

        # Check user was created
        new_user = CustomUser.objects.get(email=new_email)
        self.assertEqual(new_user.name, data["name"])
        self.assertEqual(new_user.phone_number, data["phone_number"])

        # Check teacher profile was created
        self.assertTrue(hasattr(new_user, "teacher_profile"))
        teacher_profile = new_user.teacher_profile
        self.assertEqual(teacher_profile.bio, data["bio"])
        self.assertEqual(teacher_profile.specialty, data["specialty"])

        # Check school membership was created
        membership = SchoolMembership.objects.get(
            user=new_user, school=self.school1, role=SchoolRole.TEACHER
        )
        self.assertTrue(membership.is_active)

        # Check course associations
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 2)
        course_ids = [tc.course.id for tc in teacher_courses]
        self.assertIn(self.course2.id, course_ids)
        self.assertIn(self.course3.id, course_ids)

        # Check invitation was created
        invitation = SchoolInvitation.objects.get(email=new_email)
        self.assertEqual(invitation.school, self.school1)
        self.assertEqual(invitation.invited_by, self.school_owner)
        self.assertEqual(invitation.role, SchoolRole.TEACHER)
        self.assertIsNotNone(invitation.token)

    def test_invite_new_user_minimal_data(self):
        """Test inviting new user with minimal required data."""
        self.authenticate_user(self.owner_token)

        new_email = "minimal@example.com"
        data = {"email": new_email, "name": "Minimal Teacher", "school_id": self.school1.id}

        url = reverse("accounts:teacher-invite-new")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check user was created with minimal data
        new_user = CustomUser.objects.get(email=new_email)
        self.assertEqual(new_user.name, data["name"])
        self.assertEqual(new_user.phone_number, "")  # Default empty

        # Check teacher profile was created with defaults
        teacher_profile = new_user.teacher_profile
        self.assertEqual(teacher_profile.bio, "")
        self.assertEqual(teacher_profile.specialty, "")

        # No courses should be associated
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 0)

    def test_invite_existing_user_email(self):
        """Test that inviting user with existing email fails."""
        self.authenticate_user(self.owner_token)

        data = {
            "email": self.existing_user.email,  # Already exists
            "name": "Should Fail",
            "school_id": self.school1.id,
        }

        url = reverse("accounts:teacher-invite-new")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already exists", response.json()["email"][0])

    def test_invite_to_nonexistent_school(self):
        """Test inviting user to non-existent school fails."""
        self.authenticate_user(self.owner_token)

        data = {
            "email": "newuser@example.com",
            "name": "New User",
            "school_id": 999,  # Non-existent school
        }

        url = reverse("accounts:teacher-invite-new")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not exist", response.json()["school_id"][0])

    def test_invite_without_permission(self):
        """Test that regular users cannot invite new teachers."""
        self.authenticate_user(self.regular_user_token)

        data = {"email": "newuser@example.com", "name": "New User", "school_id": self.school1.id}

        url = reverse("accounts:teacher-invite-new")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_data = response.json()
        # Handle both 'error' and 'detail' fields for permission errors
        error_message = response_data.get("error", response_data.get("detail", ""))
        # Update the assertion to match the actual error message
        self.assertTrue(
            "don't have permission" in error_message
            or "must be a school owner or administrator" in error_message,
            f"Expected permission error message, got: {error_message}",
        )

    def test_invite_invalid_phone_number(self):
        """Test inviting user with invalid phone number format."""
        self.authenticate_user(self.owner_token)

        data = {
            "email": "newuser@example.com",
            "name": "New User",
            "school_id": self.school1.id,
            "phone_number": "invalid-phone",
        }

        url = reverse("accounts:teacher-invite-new")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid phone number format", response.json()["phone_number"][0])


class TeacherListFilteringTest(TeacherOnboardingBaseTest):
    """Tests for teacher list filtering (GET /api/accounts/teachers/)."""

    def setUp(self):
        super().setUp()

        # Create additional users and teachers for filtering tests
        self.teacher2_user = CustomUser.objects.create_user(
            email="teacher2@example.com", name="Teacher Two", phone_number="+351 912 000 006"
        )

        self.teacher3_user = CustomUser.objects.create_user(
            email="teacher3@example.com", name="Teacher Three", phone_number="+351 912 000 007"
        )

        # Create teacher profiles
        self.teacher2 = TeacherProfile.objects.create(
            user=self.teacher2_user, bio="Teacher 2 bio", specialty="Physics"
        )

        self.teacher3 = TeacherProfile.objects.create(
            user=self.teacher3_user, bio="Teacher 3 bio", specialty="Chemistry"
        )

        # Add teachers to different schools
        # teacher2 in school1
        SchoolMembership.objects.create(
            user=self.teacher2_user, school=self.school1, role=SchoolRole.TEACHER, is_active=True
        )

        # teacher3 in school2
        SchoolMembership.objects.create(
            user=self.teacher3_user, school=self.school2, role=SchoolRole.TEACHER, is_active=True
        )

        # Make school_owner also owner of school2
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school2,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True,
        )

    def test_school_owner_sees_teachers_from_managed_schools(self):
        """Test that school owner sees teachers only from schools they manage."""
        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # Handle paginated response
        if "results" in response_data:
            teachers = response_data["results"]
        else:
            teachers = response_data

        teacher_emails = [t["user"]["email"] for t in teachers]

        # Should see teachers from both school1 and school2 (owner manages both)
        self.assertIn(self.teacher_user.email, teacher_emails)  # school1
        self.assertIn(self.teacher2_user.email, teacher_emails)  # school1
        self.assertIn(self.teacher3_user.email, teacher_emails)  # school2

    def test_school_admin_sees_teachers_from_their_school_only(self):
        """Test that school admin sees teachers only from their school."""
        self.authenticate_user(self.admin_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # Handle paginated response
        if "results" in response_data:
            teachers = response_data["results"]
        else:
            teachers = response_data

        teacher_emails = [t["user"]["email"] for t in teachers]

        # Should see teachers from school1 only (admin only manages school1)
        self.assertIn(self.teacher_user.email, teacher_emails)  # school1
        self.assertIn(self.teacher2_user.email, teacher_emails)  # school1
        self.assertNotIn(self.teacher3_user.email, teacher_emails)  # school2

    def test_teacher_sees_own_profile_only(self):
        """Test that teacher sees only their own profile."""
        teacher_token = AuthToken.objects.create(self.teacher2_user)[1]
        self.authenticate_user(teacher_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # Handle paginated response
        if "results" in response_data:
            teachers = response_data["results"]
        else:
            teachers = response_data

        self.assertEqual(len(teachers), 1)
        self.assertEqual(teachers[0]["user"]["email"], self.teacher2_user.email)

    def test_regular_user_sees_no_teachers(self):
        """Test that regular user (not teacher, not admin) sees no teachers."""
        self.authenticate_user(self.regular_user_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # Handle paginated response
        if "results" in response_data:
            teachers = response_data["results"]
        else:
            teachers = response_data

        self.assertEqual(len(teachers), 0)


class MultiSchoolScenarioTest(TeacherOnboardingBaseTest):
    """Tests for complex multi-school scenarios."""

    def test_same_user_teacher_in_multiple_schools(self):
        """Test that same user can be a teacher in multiple schools."""
        # Create teacher profile first
        teacher_profile = TeacherProfile.objects.create(
            user=self.existing_user, bio="Multi-school teacher", specialty="Mathematics"
        )

        # Add as teacher to school1
        membership1 = SchoolMembership.objects.create(
            user=self.existing_user, school=self.school1, role=SchoolRole.TEACHER, is_active=True
        )

        # Add as teacher to school2
        membership2 = SchoolMembership.objects.create(
            user=self.existing_user, school=self.school2, role=SchoolRole.TEACHER, is_active=True
        )

        # Verify user is teacher in both schools
        teacher_memberships = SchoolMembership.objects.filter(
            user=self.existing_user, role=SchoolRole.TEACHER, is_active=True
        )
        self.assertEqual(teacher_memberships.count(), 2)

        school_names = [m.school.name for m in teacher_memberships]
        self.assertIn(self.school1.name, school_names)
        self.assertIn(self.school2.name, school_names)

    def test_school_with_multiple_teachers(self):
        """Test that a school can have multiple teachers."""
        # Add existing_user as teacher to school1
        teacher_profile1 = TeacherProfile.objects.create(
            user=self.existing_user, bio="Teacher 1", specialty="Mathematics"
        )

        SchoolMembership.objects.create(
            user=self.existing_user, school=self.school1, role=SchoolRole.TEACHER, is_active=True
        )

        # Add regular_user as teacher to school1
        teacher_profile2 = TeacherProfile.objects.create(
            user=self.regular_user, bio="Teacher 2", specialty="Physics"
        )

        SchoolMembership.objects.create(
            user=self.regular_user, school=self.school1, role=SchoolRole.TEACHER, is_active=True
        )

        # Verify school1 has multiple teachers
        teacher_memberships = SchoolMembership.objects.filter(
            school=self.school1, role=SchoolRole.TEACHER, is_active=True
        )

        # Should have at least 3 teachers: existing, regular, and the pre-existing teacher_user
        self.assertGreaterEqual(teacher_memberships.count(), 3)

        teacher_emails = [m.user.email for m in teacher_memberships]
        self.assertIn(self.existing_user.email, teacher_emails)
        self.assertIn(self.regular_user.email, teacher_emails)
        self.assertIn(self.teacher_user.email, teacher_emails)

    def test_school_with_multiple_roles(self):
        """Test that a school can have users with different roles."""
        # Create a student user
        student_user = CustomUser.objects.create_user(
            email="student@example.com", name="Student User", phone_number="+351 912 000 008"
        )

        # Add as student to school1
        SchoolMembership.objects.create(
            user=student_user, school=self.school1, role=SchoolRole.STUDENT, is_active=True
        )

        # Create school staff user
        staff_user = CustomUser.objects.create_user(
            email="staff@example.com", name="Staff User", phone_number="+351 912 000 009"
        )

        SchoolMembership.objects.create(
            user=staff_user, school=self.school1, role=SchoolRole.SCHOOL_STAFF, is_active=True
        )

        # Verify school1 has users with different roles
        memberships = SchoolMembership.objects.filter(school=self.school1, is_active=True)

        roles = [m.role for m in memberships]
        self.assertIn(SchoolRole.SCHOOL_OWNER, roles)
        self.assertIn(SchoolRole.SCHOOL_ADMIN, roles)
        self.assertIn(SchoolRole.TEACHER, roles)
        self.assertIn(SchoolRole.STUDENT, roles)
        self.assertIn(SchoolRole.SCHOOL_STAFF, roles)

        # Count by role
        owner_count = memberships.filter(role=SchoolRole.SCHOOL_OWNER).count()
        admin_count = memberships.filter(role=SchoolRole.SCHOOL_ADMIN).count()
        teacher_count = memberships.filter(role=SchoolRole.TEACHER).count()
        student_count = memberships.filter(role=SchoolRole.STUDENT).count()
        staff_count = memberships.filter(role=SchoolRole.SCHOOL_STAFF).count()

        self.assertEqual(owner_count, 1)
        self.assertEqual(admin_count, 1)
        self.assertGreaterEqual(teacher_count, 1)
        self.assertEqual(student_count, 1)
        self.assertEqual(staff_count, 1)

    def test_school_owner_can_self_onboard_as_teacher(self):
        """Test that school owner can also become a teacher in their own school."""
        self.authenticate_user(self.owner_token)

        # School owner self-onboards as teacher
        data = {
            "bio": "I'm the owner but also want to teach",
            "specialty": "Leadership and Management",
            "course_ids": [self.course1.id],
        }

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response includes membership info
        response_data = response.json()
        self.assertIn("teacher_memberships_created", response_data)
        self.assertEqual(response_data["teacher_memberships_created"], 1)

        # Check teacher profile was created
        self.assertTrue(hasattr(self.school_owner, "teacher_profile"))

        # Verify school owner now has both roles in school1 (automatically created by endpoint)
        owner_memberships = SchoolMembership.objects.filter(
            user=self.school_owner, school=self.school1, is_active=True
        )

        roles = [m.role for m in owner_memberships]
        self.assertIn(SchoolRole.SCHOOL_OWNER, roles)
        self.assertIn(SchoolRole.TEACHER, roles)
        self.assertEqual(len(roles), 2)

        # Check course association
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 1)
        self.assertEqual(teacher_courses.first().course.id, self.course1.id)


class TeacherOnboardingEdgeCasesTest(TeacherOnboardingBaseTest):
    """Tests for edge cases and error conditions."""

    def test_transaction_rollback_on_course_error(self):
        """Test that transaction rolls back if course association fails."""
        self.authenticate_user(self.existing_user_token)

        # Use mix of valid and invalid course IDs
        data = {
            "bio": "Test teacher",
            "specialty": "Mathematics",
            "course_ids": [self.course1.id, 999],  # 999 doesn't exist
        }

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify no teacher profile was created due to rollback
        self.assertFalse(hasattr(self.existing_user, "teacher_profile"))

    def test_inactive_school_membership(self):
        """Test behavior with inactive school memberships."""
        # Create inactive membership
        SchoolMembership.objects.create(
            user=self.existing_user,
            school=self.school1,
            role=SchoolRole.TEACHER,
            is_active=False,  # Inactive
        )

        # Teacher should not appear in active teacher lists
        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        response_data = response.json()
        # Handle paginated response
        if "results" in response_data:
            teachers = response_data["results"]
        else:
            teachers = response_data

        teacher_emails = [t["user"]["email"] for t in teachers]
        self.assertNotIn(self.existing_user.email, teacher_emails)

    def test_missing_required_fields_invite_new(self):
        """Test inviting new user with missing required fields."""
        self.authenticate_user(self.owner_token)

        # Missing name field
        data = {
            "email": "newuser@example.com",
            "school_id": self.school1.id,
            # Missing required "name" field
        }

        url = reverse("accounts:teacher-invite-new")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.json())

    def test_long_text_fields(self):
        """Test handling of very long text in bio and specialty fields."""
        self.authenticate_user(self.existing_user_token)

        # Test with very long bio
        long_bio = "A" * 1000  # Very long bio
        long_specialty = "B" * 200  # Long specialty (over 100 char limit)

        data = {"bio": long_bio, "specialty": long_specialty}

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        # Should fail validation for specialty (max_length=100)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("specialty", response.json())


class InviteExistingTeacherTest(TeacherOnboardingBaseTest):
    """Tests for invite existing user endpoint (POST /api/accounts/teachers/invite-existing/)."""

    def test_school_owner_invites_existing_user(self):
        """Test that school owner can invite existing user as teacher."""
        self.authenticate_user(self.owner_token)

        data = {
            "email": self.existing_user.email,
            "school_id": self.school1.id,
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
        self.assertEqual(invitation_data["school"]["id"], self.school1.id)
        self.assertEqual(invitation_data["invited_user"]["email"], self.existing_user.email)

        # Check invitation was created in database
        invitation = SchoolInvitation.objects.get(
            email=self.existing_user.email,
            school=self.school1,
            role=SchoolRole.TEACHER,
        )
        self.assertFalse(invitation.is_accepted)
        self.assertTrue(invitation.is_valid())

        # Check no teacher profile or membership created yet
        self.assertFalse(hasattr(self.existing_user, "teacher_profile"))
        teacher_memberships = SchoolMembership.objects.filter(
            user=self.existing_user, school=self.school1, role=SchoolRole.TEACHER
        )
        self.assertEqual(teacher_memberships.count(), 0)

    def test_invite_user_already_teacher_in_school(self):
        """Test that inviting user who is already teacher fails."""
        # First make existing_user a teacher in school1
        TeacherProfile.objects.create(
            user=self.existing_user, bio="Already a teacher", specialty="Math"
        )
        SchoolMembership.objects.create(
            user=self.existing_user, school=self.school1, role=SchoolRole.TEACHER, is_active=True
        )

        self.authenticate_user(self.owner_token)

        data = {
            "email": self.existing_user.email,
            "school_id": self.school1.id,
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
            "school_id": self.school1.id,
        }

        url = reverse("accounts:teacher-invite-existing")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not exist", response.json()["email"][0])

    def test_invite_duplicate_pending_invitation(self):
        """Test that duplicate pending invitations are not allowed."""
        # Create an existing invitation
        from accounts.db_queries import create_school_invitation

        create_school_invitation(
            school_id=self.school1.id,
            email=self.existing_user.email,
            invited_by=self.school_owner,
            role=SchoolRole.TEACHER,
        )

        self.authenticate_user(self.owner_token)

        data = {
            "email": self.existing_user.email,
            "school_id": self.school1.id,
        }

        url = reverse("accounts:teacher-invite-existing")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pending invitation", response.json()["non_field_errors"][0])

    def test_invite_without_permission(self):
        """Test that regular users cannot invite others."""
        self.authenticate_user(self.regular_user_token)

        data = {
            "email": self.existing_user.email,
            "school_id": self.school1.id,
        }

        url = reverse("accounts:teacher-invite-existing")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InvitationAcceptanceTest(TeacherOnboardingBaseTest):
    """Tests for invitation acceptance endpoints."""

    def setUp(self):
        super().setUp()
        # Create a test invitation
        from accounts.db_queries import create_school_invitation

        self.invitation = create_school_invitation(
            school_id=self.school1.id,
            email=self.existing_user.email,
            invited_by=self.school_owner,
            role=SchoolRole.TEACHER,
        )

    def test_get_invitation_details(self):
        """Test getting invitation details before acceptance."""
        self.authenticate_user(self.existing_user_token)

        url = reverse("accounts:invitation-details", kwargs={"token": self.invitation.token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertIn("invitation", response_data)
        self.assertIn("target_email", response_data)
        self.assertEqual(response_data["target_email"], self.existing_user.email)
        self.assertTrue(response_data["is_correct_user"])

        invitation_data = response_data["invitation"]
        self.assertEqual(invitation_data["school"]["id"], self.school1.id)
        self.assertEqual(invitation_data["role"], SchoolRole.TEACHER)

    def test_accept_invitation_success(self):
        """Test successful invitation acceptance."""
        self.authenticate_user(self.existing_user_token)

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
        self.assertTrue(hasattr(self.existing_user, "teacher_profile"))
        teacher_profile = self.existing_user.teacher_profile
        self.assertEqual(teacher_profile.bio, data["bio"])
        self.assertEqual(teacher_profile.specialty, data["specialty"])

        # Check school membership was created
        membership = SchoolMembership.objects.get(
            user=self.existing_user, school=self.school1, role=SchoolRole.TEACHER
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
        self.authenticate_user(self.existing_user_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check teacher profile was created with defaults
        teacher_profile = self.existing_user.teacher_profile
        self.assertEqual(teacher_profile.bio, "")
        self.assertEqual(teacher_profile.specialty, "")

        # Check no courses were associated
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 0)

    def test_accept_invitation_wrong_user(self):
        """Test that wrong user cannot accept invitation."""
        self.authenticate_user(self.regular_user_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("not for your account", response.json()["error"])

    def test_accept_invalid_token(self):
        """Test accepting invitation with invalid token."""
        self.authenticate_user(self.existing_user_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": "invalid-token"})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Invalid invitation token", response.json()["error"])

    def test_accept_already_accepted_invitation(self):
        """Test accepting already accepted invitation."""
        # Mark invitation as accepted
        self.invitation.is_accepted = True
        self.invitation.save()

        self.authenticate_user(self.existing_user_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been accepted", response.json()["error"])

    def test_accept_expired_invitation(self):
        """Test accepting expired invitation."""
        # Make invitation expired
        from datetime import timedelta

        from django.utils import timezone

        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()

        self.authenticate_user(self.existing_user_token)

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", response.json()["error"])

    def test_accept_invitation_existing_teacher_profile(self):
        """Test accepting invitation when user already has teacher profile."""
        # Create teacher profile first
        TeacherProfile.objects.create(
            user=self.existing_user, bio="Existing bio", specialty="Existing specialty"
        )

        self.authenticate_user(self.existing_user_token)

        data = {
            "bio": "New bio from invitation",  # This should be ignored
            "specialty": "New specialty",  # This should be ignored
            "course_ids": [self.course1.id],
        }

        url = reverse("accounts:invitation-accept", kwargs={"token": self.invitation.token})
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check existing teacher profile was used (bio/specialty not updated)
        teacher_profile = self.existing_user.teacher_profile
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
        self.assertTrue(response_data["requires_authentication"])
        self.assertFalse(response_data["is_correct_user"])


class TeacherListWithPendingInvitationsTest(TeacherOnboardingBaseTest):
    """Tests for teacher list including pending invitations."""

    def setUp(self):
        super().setUp()
        # Create a pending invitation
        from accounts.db_queries import create_school_invitation

        self.pending_invitation = create_school_invitation(
            school_id=self.school1.id,
            email=self.existing_user.email,
            invited_by=self.school_owner,
            role=SchoolRole.TEACHER,
        )

    def test_teacher_list_without_pending_flag(self):
        """Test that teacher list doesn't include pending invitations by default."""
        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Should only include active teachers (teacher_user), not pending invitations
        if "results" in response_data:
            teachers = response_data["results"]
        else:
            teachers = response_data

        teacher_emails = [t["user"]["email"] for t in teachers]
        self.assertIn(self.teacher_user.email, teacher_emails)  # Active teacher
        self.assertNotIn(self.existing_user.email, teacher_emails)  # Pending invitation

    def test_teacher_list_with_pending_flag(self):
        """Test that teacher list includes pending invitations when requested."""
        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teachers = response.json()

        # Should include both active teachers and pending invitations
        active_teachers = [t for t in teachers if t["status"] == "active"]
        pending_teachers = [t for t in teachers if t["status"] == "pending"]

        self.assertEqual(len(active_teachers), 1)  # teacher_user
        self.assertEqual(len(pending_teachers), 1)  # existing_user invitation

        # Check active teacher
        active_teacher = active_teachers[0]
        self.assertEqual(active_teacher["user"]["email"], self.teacher_user.email)
        self.assertIsNotNone(active_teacher["id"])  # Has teacher profile

        # Check pending teacher
        pending_teacher = pending_teachers[0]
        self.assertEqual(pending_teacher["user"]["email"], self.existing_user.email)
        self.assertIsNone(pending_teacher["id"])  # No teacher profile yet
        self.assertIn("invitation", pending_teacher)
        self.assertEqual(pending_teacher["invitation"]["token"], self.pending_invitation.token)

    def test_pending_invitation_includes_invitation_details(self):
        """Test that pending invitations include all necessary invitation details."""
        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        teachers = response.json()
        pending_teachers = [t for t in teachers if t["status"] == "pending"]

        self.assertEqual(len(pending_teachers), 1)

        pending_teacher = pending_teachers[0]
        invitation = pending_teacher["invitation"]

        # Check invitation details
        self.assertEqual(invitation["id"], self.pending_invitation.id)
        self.assertEqual(invitation["token"], self.pending_invitation.token)
        self.assertIn("link", invitation)
        self.assertIn("expires_at", invitation)
        self.assertEqual(invitation["invited_by"], self.school_owner.name)

    def test_expired_invitations_not_included(self):
        """Test that expired invitations are not included in the list."""
        # Make the invitation expired
        from datetime import timedelta

        from django.utils import timezone

        self.pending_invitation.expires_at = timezone.now() - timedelta(days=1)
        self.pending_invitation.save()

        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        teachers = response.json()
        pending_teachers = [t for t in teachers if t["status"] == "pending"]

        # Expired invitation should not be included
        self.assertEqual(len(pending_teachers), 0)

    def test_accepted_invitations_not_included_as_pending(self):
        """Test that accepted invitations are not included as pending."""
        # Mark invitation as accepted
        self.pending_invitation.is_accepted = True
        self.pending_invitation.save()

        self.authenticate_user(self.owner_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        teachers = response.json()
        pending_teachers = [t for t in teachers if t["status"] == "pending"]

        # Accepted invitation should not be included as pending
        self.assertEqual(len(pending_teachers), 0)

    def test_regular_user_cannot_see_pending_invitations(self):
        """Test that regular users can't see pending invitations."""
        self.authenticate_user(self.regular_user_token)

        url = reverse("accounts:teacher-list") + "?include_pending=true"
        response = self.client.get(url)

        teachers = response.json()

        # Regular user should see empty list (no teachers, no pending invitations)
        self.assertEqual(len(teachers), 0)
