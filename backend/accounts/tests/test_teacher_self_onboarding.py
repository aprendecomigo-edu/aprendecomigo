"""
Tests for teacher self-onboarding endpoint.

This module focuses on testing the self-onboarding scenario where
current users become teachers by posting to /api/accounts/teachers/onboarding/
"""

from django.test import TestCase
from django.urls import reverse
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
    TeacherCourse,
    TeacherProfile,
)


class SelfOnboardingBaseTest(TestCase):
    """Minimal base test class for self-onboarding tests."""

    def setUp(self):
        """Set up minimal test data for self-onboarding tests."""
        self.client = APIClient()

        # Create test educational system
        self.educational_system = EducationalSystem.objects.create(
            name="Test System", code="test", description="Test system", is_active=True
        )

        # Create minimal test courses
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

    def authenticate_user(self, token):
        """Helper method to authenticate a user with their token."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def clear_authentication(self):
        """Helper method to clear authentication."""
        self.client.credentials()


class SelfOnboardingTest(SelfOnboardingBaseTest):
    """Tests for self-onboarding endpoint (POST /api/accounts/teachers/onboarding/)."""

    def setUp(self):
        super().setUp()
        
        # Create users only as needed
        self.regular_user, self.regular_token = self.create_user_with_token(
            "regular@example.com", "Regular User", "+351912000001"
        )
        
        self.school_owner, self.owner_token = self.create_user_with_token(
            "owner@example.com", "School Owner", "+351912000002"
        )
        self.create_school_membership(self.school_owner, SchoolRole.SCHOOL_OWNER)
        
        self.existing_teacher, self.teacher_token = self.create_user_with_token(
            "teacher@example.com", "Existing Teacher", "+351912000003"
        )
        TeacherProfile.objects.create(user=self.existing_teacher, bio="Existing teacher")
        self.create_school_membership(self.existing_teacher, SchoolRole.TEACHER)

    def test_successful_self_onboarding(self):
        """Test that a user can successfully onboard themselves as a teacher."""
        self.authenticate_user(self.regular_token)

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
        self.assertTrue(hasattr(self.regular_user, "teacher_profile"))
        teacher_profile = self.regular_user.teacher_profile
        self.assertEqual(teacher_profile.bio, data["bio"])
        self.assertEqual(teacher_profile.specialty, data["specialty"])

        # Check courses were associated
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile)
        self.assertEqual(teacher_courses.count(), 2)
        course_ids = [tc.course.id for tc in teacher_courses]
        self.assertIn(self.course1.id, course_ids)
        self.assertIn(self.course2.id, course_ids)

    def test_self_onboarding_minimal_data(self):
        """Test self-onboarding with minimal data (empty/no courses)."""
        self.authenticate_user(self.regular_token)

        # Test with minimal data
        data = {"bio": "New teacher", "specialty": "Science"}
        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertEqual(response_data["courses_added"], 0)

        # Test with completely empty data
        regular_user2, regular_token2 = self.create_user_with_token(
            "regular2@example.com", "Regular User 2", "+351912000004"
        )
        self.authenticate_user(regular_token2)
        
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check teacher profile was created with defaults
        teacher_profile = regular_user2.teacher_profile
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
        self.authenticate_user(self.regular_token)

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
        self.assertIn("teacher_memberships_created", response_data)
        self.assertIn("schools_added_as_teacher", response_data)
        self.assertEqual(response_data["teacher_memberships_created"], 1)
        self.assertEqual(response_data["schools_added_as_teacher"], [self.school.name])

        # Check teacher profile was created
        self.assertTrue(hasattr(self.school_owner, "teacher_profile"))
        teacher_profile = self.school_owner.teacher_profile
        self.assertEqual(teacher_profile.bio, data["bio"])

        # Check user now has both owner and teacher memberships
        memberships = SchoolMembership.objects.filter(
            user=self.school_owner, school=self.school, is_active=True
        )
        self.assertEqual(memberships.count(), 2)

        roles = [m.role for m in memberships]
        self.assertIn(SchoolRole.SCHOOL_OWNER, roles)
        self.assertIn(SchoolRole.TEACHER, roles)

    def test_school_admin_self_onboarding_creates_teacher_membership(self):
        """Test that school admin onboarding automatically creates teacher membership."""
        school_admin, admin_token = self.create_user_with_token(
            "admin@example.com", "School Admin", "+351912000005"
        )
        self.create_school_membership(school_admin, SchoolRole.SCHOOL_ADMIN)
        
        self.authenticate_user(admin_token)

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
            user=school_admin, school=self.school, is_active=True
        )
        self.assertEqual(memberships.count(), 2)

        roles = [m.role for m in memberships]
        self.assertIn(SchoolRole.SCHOOL_ADMIN, roles)
        self.assertIn(SchoolRole.TEACHER, roles)

    def test_multi_school_owner_self_onboarding(self):
        """Test that owner of multiple schools gets teacher memberships in all their schools."""
        # Create second school and make owner own both
        school2 = School.objects.create(
            name="Test School 2", description="Second test school", address="Test Address 2"
        )
        SchoolMembership.objects.create(
            user=self.school_owner, school=school2, role=SchoolRole.SCHOOL_OWNER, is_active=True
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
        self.assertIn(self.school.name, school_names)
        self.assertIn(school2.name, school_names)

        # Check teacher memberships were created for both schools
        teacher_memberships = SchoolMembership.objects.filter(
            user=self.school_owner, role=SchoolRole.TEACHER, is_active=True
        )
        self.assertEqual(teacher_memberships.count(), 2)

    def test_regular_user_self_onboarding_no_memberships(self):
        """Test that regular users (non-school-admins) don't get automatic memberships."""
        self.authenticate_user(self.regular_token)

        data = {"bio": "Regular user becoming teacher", "specialty": "Independent Teaching"}

        url = reverse("accounts:teacher-onboarding")
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response does NOT include membership info
        response_data = response.json()
        self.assertNotIn("teacher_memberships_created", response_data)
        self.assertNotIn("schools_added_as_teacher", response_data)

        # Check teacher profile was created
        self.assertTrue(hasattr(self.regular_user, "teacher_profile"))

        # Check no school memberships exist for this user
        memberships = SchoolMembership.objects.filter(user=self.regular_user)
        self.assertEqual(memberships.count(), 0)

    def test_owner_already_teacher_in_school_no_duplicate(self):
        """Test that if owner is already a teacher, no duplicate membership is created."""
        # Manually create teacher membership first
        SchoolMembership.objects.create(
            user=self.school_owner, school=self.school, role=SchoolRole.TEACHER, is_active=True
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
            user=self.school_owner, school=self.school, is_active=True
        )
        self.assertEqual(memberships.count(), 2)