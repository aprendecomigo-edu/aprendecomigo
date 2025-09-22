"""
Tests for PeopleView student details functionality.

These tests focus specifically on the HTMX student details view feature to prevent
database query errors and ensure proper data retrieval for different student types.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.models.profiles import GuardianProfile, StudentProfile

User = get_user_model()


class PeopleViewStudentDetailsTest(TestCase):
    """Integration tests for student details functionality in PeopleView."""

    def setUp(self):
        """Set up test data for student details tests."""
        # Create a test school
        self.school = School.objects.create(name="Test School", address="123 Test St", phone_number="+351234567890")

        # Create a teacher user who can access the people view
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com", name="Test Teacher", password="testpass123"
        )

        # Add teacher to school
        SchoolMembership.objects.create(user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER.value)

    def _create_regular_student(self, name, email, school_year="Year 7", educational_system="pt"):
        """Helper method to create a regular student with user account."""
        user = User.objects.create_user(email=email, name=name, password="studentpass123")

        # Create student membership
        SchoolMembership.objects.create(user=user, school=self.school, role=SchoolRole.STUDENT.value)

        # Create student profile with all required fields
        profile = StudentProfile.objects.create(
            user=user,
            name=name,
            birth_date=date(2010, 1, 1),
            school_year=school_year,
            educational_system=educational_system,
            account_type="ADULT_STUDENT",
        )

        return user, profile

    def _create_guardian_only_student(self, name, guardian_email, school_year="Year 7"):
        """Helper method to create a Guardian-Only student (no user account)."""
        # Create guardian user and profile
        guardian_user = User.objects.create_user(
            email=guardian_email, name=f"Guardian of {name}", password="guardianpass123"
        )
        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        # Create Guardian-Only student profile (no user field)
        profile = StudentProfile.objects.create(
            name=name,
            birth_date=date(2012, 6, 15),
            school_year=school_year,
            educational_system="pt",
            account_type="GUARDIAN_ONLY",
            guardian=guardian_profile,
        )

        return guardian_user, profile

    def test_get_regular_student_details_success(self):
        """
        Test that getting details for a regular student (with user account) works correctly.

        This test specifically addresses the bug where select_related with
        'educational_system' causes errors since it's not a foreign key field.
        """
        # Create a regular student
        student_user, _ = self._create_regular_student("João Silva", "joao.silva@test.com", "Year 10", "pt")

        # Login as teacher
        self.client.force_login(self.teacher_user)

        # Request student details via HTMX
        response = self.client.post(
            reverse("people"),
            {"action": "get_student_detail", "student_id": student_user.id},
            headers={"hx-request": "true"},
        )

        # Verify response is successful (should not have database errors)
        self.assertEqual(response.status_code, 200)

        # Check if response contains error about educational_system (the bug we're testing for)
        response_content = response.content.decode()

        # If the bug is present, we should see the select_related error
        self.assertNotIn("Non-relational field given in select_related: 'educational_system'", response_content)

        # Check if response is JSON or contains the student modal/data
        if response.get("Content-Type") == "application/json":
            # Parse the response data if it's JSON
            import json

            response_data = json.loads(response.content)

            # Verify student data is correctly included
            self.assertIn("student", response_data)
            student_data = response_data["student"]

            self.assertEqual(student_data["name"], "João Silva")
            self.assertEqual(student_data["email"], "joao.silva@test.com")
            self.assertEqual(student_data["school_year"], "Year 10")
            self.assertEqual(student_data["educational_system"], "pt")  # Should be string, not object
            self.assertEqual(student_data["account_type"], "ADULT_STUDENT")

            # Verify school membership data is included
            self.assertIn("school", student_data)
            self.assertEqual(student_data["school"]["name"], "Test School")
        else:
            # If it's HTML, check it contains the student data in HTML format
            self.assertIn("João Silva", response_content)
            self.assertIn("joao.silva@test.com", response_content)
            self.assertIn("Year 10", response_content)

    def test_get_guardian_only_student_details_success(self):
        """
        Test that getting details for a Guardian-Only student (no user account) works correctly.
        """
        # Create a Guardian-Only student
        _, student_profile = self._create_guardian_only_student("Maria Santos", "guardian.maria@test.com", "Year 5")

        # Login as teacher
        self.client.force_login(self.teacher_user)

        # Request student details via HTMX
        # Note: This might need to use the user ID of guardian-only students differently
        response = self.client.post(
            reverse("people"),
            {
                "action": "get_student_detail",
                "student_id": student_profile.user.id if student_profile.user else student_profile.id,
            },
            headers={"hx-request": "true"},
        )

        # Verify response is successful (no database errors)
        self.assertEqual(response.status_code, 200)

        # Check if response contains error about educational_system (the bug we're testing for)
        response_content = response.content.decode()
        self.assertNotIn("Non-relational field given in select_related: 'educational_system'", response_content)

        # Verify student data is present in the response (HTML or JSON)
        self.assertIn("Maria Santos", response_content)
        self.assertIn("Year 5", response_content)

        # If it's JSON format, check the structure
        if response.get("Content-Type") == "application/json":
            import json

            response_data = json.loads(response.content)

            # Verify student data is correctly included
            self.assertIn("student", response_data)
            student_data = response_data["student"]

            self.assertEqual(student_data["name"], "Maria Santos")
            self.assertEqual(student_data["school_year"], "Year 5")
            self.assertEqual(student_data["educational_system"], "pt")
            self.assertEqual(student_data["account_type"], "GUARDIAN_ONLY")

            # Verify guardian data is included if present
            if "guardian" in student_data:
                guardian_data = student_data["guardian"]
                self.assertIn("Guardian of Maria Santos", guardian_data["name"])

    def test_get_student_detail_missing_student_id(self):
        """Test that missing student_id parameter returns appropriate error."""
        self.client.force_login(self.teacher_user)

        response = self.client.post(
            reverse("people"),
            {"action": "get_student_detail"},  # Missing student_id
            headers={"hx-request": "true"},
        )

        # Should return error message partial
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student ID is required")

    def test_get_student_detail_nonexistent_student(self):
        """Test that requesting details for non-existent student handles gracefully."""
        self.client.force_login(self.teacher_user)

        response = self.client.post(
            reverse("people"),
            {
                "action": "get_student_detail",
                "student_id": 99999,  # Non-existent ID
            },
            headers={"hx-request": "true"},
        )

        # Should return error (500 or error partial)
        self.assertIn(response.status_code, [200, 404, 500])

        # If it returns 200, it should contain an error message
        if response.status_code == 200:
            response_content = response.content.decode()
            self.assertTrue("error" in response_content.lower() or "not found" in response_content.lower())

    def test_htmx_response_format(self):
        """Test that the student details endpoint returns proper JSON response."""
        # Create a test student
        student_user, _ = self._create_regular_student("Test Student", "test@test.com")

        self.client.force_login(self.teacher_user)

        # Perform HTMX request
        response = self.client.post(
            reverse("people"),
            {"action": "get_student_detail", "student_id": student_user.id},
            headers={"hx-request": "true"},
        )

        # Verify response is successful
        self.assertEqual(response.status_code, 200)

        # Verify it returns JSON, not HTML
        self.assertEqual(response["Content-Type"], "application/json")

        # Verify JSON structure is valid
        import json

        try:
            response_data = json.loads(response.content)
            self.assertIn("student", response_data)
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")

    def test_student_details_requires_authentication(self):
        """Test that student details endpoint requires user to be logged in."""
        student_user, _ = self._create_regular_student("Test Student", "test@test.com")

        response = self.client.post(
            reverse("people"),
            {"action": "get_student_detail", "student_id": student_user.id},
            headers={"hx-request": "true"},
        )

        # Should redirect to login (302) or return 401/403
        self.assertIn(response.status_code, [302, 401, 403])

    def test_educational_system_field_handling(self):
        """
        Test that educational_system field is properly handled as CharField, not foreign key.

        This is the specific test for the bug: educational_system is a CharField with choices,
        not a foreign key, so select_related() should not be used on it.
        """
        # Create student with different educational systems
        student1, _ = self._create_regular_student("Portuguese Student", "pt.student@test.com", educational_system="pt")
        student2, _ = self._create_regular_student(
            "Custom System Student", "custom.student@test.com", educational_system="custom"
        )

        self.client.force_login(self.teacher_user)

        # Test Portuguese system student - should not error
        response = self.client.post(
            reverse("people"),
            {"action": "get_student_detail", "student_id": student1.id},
            headers={"hx-request": "true"},
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # The main test: should NOT contain the select_related error about educational_system
        # This assertion will fail until the bug is fixed, proving the test works
        error_message = "Non-relational field given in select_related: &#x27;educational_system&#x27;"

        if error_message in response_content:
            self.fail(
                f"Bug detected: The view is incorrectly using select_related on 'educational_system', "
                f"which is a CharField, not a foreign key. This causes the error: {error_message}"
            )

        # Should contain the student data in some form (HTML or JSON) if bug is fixed
        self.assertIn("Portuguese Student", response_content)

        # Test custom system student - should also not error
        response = self.client.post(
            reverse("people"),
            {"action": "get_student_detail", "student_id": student2.id},
            headers={"hx-request": "true"},
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # The main test: should NOT contain the select_related error about educational_system
        error_message = "Non-relational field given in select_related: &#x27;educational_system&#x27;"

        if error_message in response_content:
            self.fail(
                f"Bug detected: The view is incorrectly using select_related on 'educational_system', "
                f"which is a CharField, not a foreign key. This causes the error: {error_message}"
            )

        # Should contain the student data in some form (HTML or JSON) if bug is fixed
        self.assertIn("Custom System Student", response_content)

    def test_student_details_database_query_regression(self):
        """
        Regression test specifically for the educational_system select_related bug.

        This test ensures that the student details view doesn't use select_related
        on the educational_system field, which is a CharField, not a foreign key.
        """
        # Create a student to test with
        student_user, _ = self._create_regular_student("Test Student", "test@test.com", educational_system="pt")

        self.client.force_login(self.teacher_user)

        # Make the request that should trigger the bug if it exists
        response = self.client.post(
            reverse("people"),
            {"action": "get_student_detail", "student_id": student_user.id},
            headers={"hx-request": "true"},
        )

        # Check the response for the specific database error
        response_content = response.content.decode()

        # This error indicates the bug is present - it should NOT appear
        self.assertNotIn(
            "Non-relational field given in select_related",
            response_content,
            "The view is incorrectly using select_related on a CharField field. "
            "Check the _handle_get_student_detail method in dashboard/views.py",
        )

        # If we get here, the database query worked properly
        self.assertEqual(response.status_code, 200)
