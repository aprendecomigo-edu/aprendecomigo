import datetime
from datetime import timedelta
from unittest.mock import patch

import pyotp
from accounts.models import EmailVerificationCode, Student, Teacher
from accounts.serializers import StudentSerializer, TeacherSerializer, UserSerializer
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class APIAuthTests(APITestCase):
    """Test authentication via the API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.request_code_url = reverse("request_email_code")
        self.verify_code_url = reverse("verify_email_code")
        self.email = "test@example.com"

    def test_request_email_code(self):
        """Test requesting an email verification code."""
        data = {"email": self.email}

        # Patch the send_mail method to avoid sending actual emails
        with patch("accounts.views.send_mail") as mock_send_mail:
            response = self.client.post(self.request_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verify a code was generated in the database
        code_obj = EmailVerificationCode.objects.filter(email=self.email).first()
        self.assertIsNotNone(code_obj)
        self.assertFalse(code_obj.is_used)

        # Verify an email would have been sent
        mock_send_mail.assert_called_once()

    def test_verify_email_code(self):
        """Test verifying an email code."""
        # Create a verification code
        verification = EmailVerificationCode.generate_code(self.email)

        # Get a valid TOTP code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        data = {"email": self.email, "code": valid_code}

        response = self.client.post(self.verify_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("token", response.data)

        # Verify the code is marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)

        # Verify a user was created
        user = User.objects.filter(email=self.email).first()
        self.assertIsNotNone(user)

    def test_verify_email_code_invalid(self):
        """Test verifying with an invalid code."""
        # We need to generate a code in the database for the email
        # even though we're not using the actual code in the test
        EmailVerificationCode.generate_code(self.email)

        data = {
            "email": self.email,
            "code": "000000",  # Wrong code
        }

        response = self.client.post(self.verify_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_verify_email_code_expired(self):
        """Test verifying with an expired code."""
        # Create a verification code
        verification = EmailVerificationCode.generate_code(self.email)

        # Get a valid TOTP code
        totp = pyotp.TOTP(verification.secret_key)
        valid_code = totp.now()

        # Set the creation time to 25 hours ago (codes expire after 24 hours)
        verification.created_at = timezone.now() - timedelta(hours=25)
        verification.save()

        data = {"email": self.email, "code": valid_code}

        response = self.client.post(self.verify_code_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("expired", response.data["error"])


class UserAPITests(APITestCase):
    """Test user-related API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create regular user
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            name="Regular User",
            user_type="student",
        )

        # Create admin user
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            name="Admin User",
            is_staff=True,
        )

        # Create teacher user
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="password123",
            name="Teacher User",
            user_type="teacher",
        )

        self.users_url = reverse("user-list")
        self.user_detail_url = reverse("user-detail", kwargs={"pk": self.user.pk})
        self.dashboard_info_url = reverse("user-dashboard-info")
        self.school_profile_url = reverse("user-school-profile")

    def authenticate_user(self, user):
        """Helper method to authenticate as a specific user."""
        self.client.force_authenticate(user=user)

    def test_list_users_as_admin(self):
        """Test that admin user can list all users."""
        self.authenticate_user(self.admin)
        response = self.client.get(self.users_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)  # 3 users total

    def test_list_users_as_regular_user(self):
        """Test that regular user can only see their own user."""
        self.authenticate_user(self.user)
        response = self.client.get(self.users_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.user.id)

    def test_retrieve_own_user(self):
        """Test retrieving your own user details."""
        self.authenticate_user(self.user)
        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["name"], self.user.name)

    def test_update_own_user(self):
        """Test updating your own user details."""
        self.authenticate_user(self.user)
        data = {"name": "Updated Name", "phone_number": "555-1234"}

        response = self.client.patch(self.user_detail_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Name")
        self.assertEqual(response.data["phone_number"], "555-1234")

        # Verify the changes in the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated Name")
        self.assertEqual(self.user.phone_number, "555-1234")

    def test_dashboard_info(self):
        """Test retrieving dashboard information."""
        self.authenticate_user(self.user)
        response = self.client.get(self.dashboard_info_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user_info", response.data)
        self.assertIn("stats", response.data)

        user_info = response.data["user_info"]
        self.assertEqual(user_info["id"], self.user.id)
        self.assertEqual(user_info["email"], self.user.email)
        self.assertEqual(user_info["name"], self.user.name)
        self.assertEqual(user_info["user_type"], "student")

    def test_school_profile(self):
        """Test retrieving school profile information."""
        self.authenticate_user(self.user)
        response = self.client.get(self.school_profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("stats", response.data)
        self.assertIn("school_info", response.data)

        stats = response.data["stats"]
        self.assertEqual(stats["students"], 1)  # One student user
        self.assertEqual(stats["teachers"], 1)  # One teacher user


class StudentAPITests(APITestCase):
    """Test student-related API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create a student user
        self.student_user = User.objects.create_user(
            email="student@example.com",
            password="password123",
            name="Student User",
            user_type="student",
        )

        # Create a student profile
        self.student = Student.objects.create(
            user=self.student_user,
            school_year="10",
            birth_date=datetime.date(2000, 1, 1),
            address="123 Test St, Test City, 12345",
            cc_number="123456789",
        )

        # Create another user without a student profile
        self.user_no_profile = User.objects.create_user(
            email="noprofile@example.com",
            password="password123",
            name="No Profile User",
            user_type="student",
        )

        # Create admin user
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            name="Admin User",
            is_staff=True,
        )

        self.students_url = reverse("student-list")
        self.student_detail_url = reverse(
            "student-detail", kwargs={"pk": self.student.pk}
        )
        self.onboarding_url = reverse("student-onboarding")

    def authenticate_user(self, user):
        """Helper method to authenticate as a specific user."""
        self.client.force_authenticate(user=user)

    def test_list_students_as_admin(self):
        """Test that admin user can list all students."""
        self.authenticate_user(self.admin)
        response = self.client.get(self.students_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)  # 1 student profile exists

    def test_list_students_as_student(self):
        """Test that student user can only see their own profile."""
        self.authenticate_user(self.student_user)
        response = self.client.get(self.students_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.student.id)

    def test_retrieve_own_student_profile(self):
        """Test retrieving your own student profile."""
        self.authenticate_user(self.student_user)
        response = self.client.get(self.student_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.student.id)
        self.assertEqual(response.data["school_year"], self.student.school_year)
        self.assertEqual(response.data["user"]["email"], self.student_user.email)

    def test_update_own_student_profile(self):
        """Test updating your own student profile."""
        self.authenticate_user(self.student_user)
        data = {"school_year": "11", "address": "New Address"}

        response = self.client.patch(self.student_detail_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["school_year"], "11")
        self.assertEqual(response.data["address"], "New Address")

        # Verify the changes in the database
        self.student.refresh_from_db()
        self.assertEqual(self.student.school_year, "11")
        self.assertEqual(self.student.address, "New Address")

    def test_onboarding_new_profile(self):
        """Test creating a new student profile via onboarding."""
        self.authenticate_user(self.user_no_profile)

        data = {
            "school_year": "12",
            "birth_date": "2001-02-03",
            "address": "456 New St, New City, 54321",
            "cc_number": "987654321",
        }

        response = self.client.post(self.onboarding_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["school_year"], "12")
        self.assertEqual(response.data["address"], "456 New St, New City, 54321")

        # Verify the profile was created in the database
        student_profile = Student.objects.get(user=self.user_no_profile)
        self.assertIsNotNone(student_profile)
        self.assertEqual(student_profile.school_year, "12")

    def test_onboarding_existing_profile(self):
        """Test onboarding when profile already exists."""
        self.authenticate_user(self.student_user)

        data = {
            "school_year": "12",
            "birth_date": "2001-02-03",
            "address": "456 New St, New City, 54321",
            "cc_number": "987654321",
        }

        response = self.client.post(self.onboarding_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Your profile is already complete.")


class TeacherAPITests(APITestCase):
    """Test teacher-related API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create a teacher user
        self.teacher_user = User.objects.create_user(
            email="teacher@example.com",
            password="password123",
            name="Teacher User",
            user_type="teacher",
        )

        # Create a teacher profile
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            bio="Test bio",
            specialty="Math",
            education="Test education",
            hourly_rate=50.0,
            availability="Weekdays",
            address="123 Teacher St, Teacher City",
            phone_number="555-1234",
        )

        # Create admin user
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            name="Admin User",
            is_staff=True,
        )

        self.teachers_url = reverse("teacher-list")
        self.teacher_detail_url = reverse(
            "teacher-detail", kwargs={"pk": self.teacher.pk}
        )

    def authenticate_user(self, user):
        """Helper method to authenticate as a specific user."""
        self.client.force_authenticate(user=user)

    def test_list_teachers_as_admin(self):
        """Test that admin user can list all teachers."""
        self.authenticate_user(self.admin)
        response = self.client.get(self.teachers_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)  # 1 teacher profile exists

    def test_list_teachers_as_teacher(self):
        """Test that teacher user can only see their own profile."""
        self.authenticate_user(self.teacher_user)
        response = self.client.get(self.teachers_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.teacher.id)

    def test_retrieve_own_teacher_profile(self):
        """Test retrieving your own teacher profile."""
        self.authenticate_user(self.teacher_user)
        response = self.client.get(self.teacher_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.teacher.id)
        self.assertEqual(response.data["specialty"], self.teacher.specialty)
        self.assertEqual(response.data["user"]["email"], self.teacher_user.email)

    def test_update_own_teacher_profile(self):
        """Test updating your own teacher profile."""
        self.authenticate_user(self.teacher_user)
        data = {"specialty": "Science", "hourly_rate": 60.0}

        response = self.client.patch(self.teacher_detail_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["specialty"], "Science")
        self.assertEqual(float(response.data["hourly_rate"]), 60.0)

        # Verify the changes in the database
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.specialty, "Science")
        self.assertEqual(float(self.teacher.hourly_rate), 60.0)


class SerializerTests(APITestCase):
    """Test serializers for API models."""

    def setUp(self):
        """Set up test data."""
        # Create a user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="Test User",
            phone_number="555-1234",
            user_type="student",
        )

        # Create a student profile
        self.student = Student.objects.create(
            user=self.user,
            school_year="10",
            birth_date=datetime.date(2000, 1, 1),
            address="123 Test St, Test City, 12345",
            cc_number="123456789",
        )

        # Create a teacher user
        self.teacher_user = User.objects.create_user(
            email="teacher@example.com",
            password="password123",
            name="Teacher User",
            user_type="teacher",
        )

        # Create a teacher profile
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            bio="Test bio",
            specialty="Math",
            education="Test education",
            hourly_rate=50.0,
            availability="Weekdays",
            address="123 Teacher St, Teacher City",
            phone_number="555-1234",
        )

    def test_user_serializer(self):
        """Test the UserSerializer."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["name"], self.user.name)
        self.assertEqual(data["phone_number"], self.user.phone_number)
        self.assertEqual(data["user_type"], self.user.user_type)

    def test_student_serializer(self):
        """Test the StudentSerializer."""
        serializer = StudentSerializer(self.student)
        data = serializer.data

        self.assertEqual(data["id"], self.student.id)
        self.assertEqual(data["school_year"], self.student.school_year)
        self.assertEqual(data["address"], self.student.address)
        self.assertEqual(data["cc_number"], self.student.cc_number)

        # Test nested user serialization
        self.assertEqual(data["user"]["email"], self.user.email)
        self.assertEqual(data["user"]["name"], self.user.name)

    def test_teacher_serializer(self):
        """Test the TeacherSerializer."""
        serializer = TeacherSerializer(self.teacher)
        data = serializer.data

        self.assertEqual(data["id"], self.teacher.id)
        self.assertEqual(data["bio"], self.teacher.bio)
        self.assertEqual(data["specialty"], self.teacher.specialty)
        self.assertEqual(data["education"], self.teacher.education)
        self.assertEqual(float(data["hourly_rate"]), float(self.teacher.hourly_rate))

        # Test nested user serialization
        self.assertEqual(data["user"]["email"], self.teacher_user.email)
        self.assertEqual(data["user"]["name"], self.teacher_user.name)

    def test_email_request_serializer_valid(self):
        """Test EmailRequestSerializer with valid data."""
        from accounts.serializers import EmailRequestSerializer

        data = {"email": "valid@example.com"}
        serializer = EmailRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_email_request_serializer_invalid(self):
        """Test EmailRequestSerializer with invalid data."""
        from accounts.serializers import EmailRequestSerializer

        data = {"email": "invalid-email"}
        serializer = EmailRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_email_verify_serializer_valid(self):
        """Test EmailVerifySerializer with valid data."""
        from accounts.serializers import EmailVerifySerializer

        data = {"email": "valid@example.com", "code": "123456"}
        serializer = EmailVerifySerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_email_verify_serializer_invalid_code(self):
        """Test EmailVerifySerializer with invalid code."""
        from accounts.serializers import EmailVerifySerializer

        data = {"email": "valid@example.com", "code": "12345"}  # Too short
        serializer = EmailVerifySerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)
