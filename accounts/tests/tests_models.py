import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Student

User = get_user_model()


class CustomUserModelTests(TestCase):
    """Test cases for the CustomUser model."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "testpassword123",
        }

    def tearDown(self):
        """Clean up database connections after each test."""
        # Don't close the connection in tearDown - Django will handle this
        # Simply pass to clean up other resources
        super().tearDown()

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data["email"])
        self.assertEqual(user.name, self.user_data["name"])
        self.assertTrue(user.check_password(self.user_data["password"]))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_admin)

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin_user = User.objects.create_superuser(**self.user_data)
        self.assertEqual(admin_user.email, self.user_data["email"])
        self.assertEqual(admin_user.name, self.user_data["name"])
        self.assertTrue(admin_user.check_password(self.user_data["password"]))
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_admin)

    def test_user_string_representation(self):
        """Test the string representation of a user."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data["email"])

    def test_email_required(self):
        """Test that email is required."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="testpass123", name="Test User")

    def test_username_generation(self):
        """Test username is automatically generated from email."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, "test")

        # Test username uniqueness
        user2_data = self.user_data.copy()
        user2_data["email"] = "test@another.com"
        user2 = User.objects.create_user(**user2_data)
        self.assertEqual(user2.username, "test1")

    def test_user_type_default(self):
        """Test default user type."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.user_type, "admin")

    def test_update_user_type(self):
        """Test updating user type."""
        user = User.objects.create_user(**self.user_data)
        user.user_type = "student"
        user.save()
        self.assertEqual(user.user_type, "student")


class StudentModelTests(TestCase):
    """Test cases for the Student model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="student@example.com",
            password="studentpass123",
            name="Student User",
        )

        self.student_data = {
            "user": self.user,
            "school_year": "10",
            "birth_date": datetime.date(2000, 1, 1),
            "address": "123 Test St, Test City, 12345",
            "cc_number": "123456789",
        }

    def tearDown(self):
        """Clean up database connections after each test."""
        # Don't close the connection in tearDown - Django will handle this
        # Simply pass to clean up other resources
        super().tearDown()

    def test_create_student(self):
        """Test creating a student profile."""
        student = Student.objects.create(**self.student_data)
        self.assertEqual(student.user, self.user)
        self.assertEqual(student.school_year, self.student_data["school_year"])
        self.assertEqual(student.birth_date, self.student_data["birth_date"])
        self.assertEqual(student.address, self.student_data["address"])
        self.assertEqual(student.cc_number, self.student_data["cc_number"])
        self.assertEqual(student.calendar_url, "")
        self.assertFalse(
            bool(student.cc_photo)
        )  # Use assertFalse instead of assertEqual

    def test_student_string_representation(self):
        """Test the string representation of a student."""
        student = Student.objects.create(**self.student_data)
        self.assertEqual(str(student), f"Student: {self.user.name}")

    def test_user_type_set_on_save(self):
        """Test that user type is set to 'student' on save."""
        # Initially the user is not a student
        self.assertNotEqual(self.user.user_type, "student")

        # Creating a student profile should update user_type
        student = Student.objects.create(**self.student_data)

        # Refresh the user from the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, "student")

    def test_related_name_access(self):
        """Test accessing student profile via related name."""
        student = Student.objects.create(**self.student_data)
        self.assertEqual(self.user.student_profile, student)
