import datetime

from django.test import TestCase

from accounts.models import CustomUser, StudentProfile, TeacherProfile
from accounts.serializers import (
    RequestCodeSerializer,
    StudentSerializer,
    TeacherSerializer,
    UserSerializer,
    VerifyCodeSerializer,
)


class TestUserSerializer(TestCase):
    """Test suite for the UserSerializer."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="password123",
            name="Test User",
            phone_number="1234567890",
        )

    def test_user_serializer(self):
        """Test serializing a user."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["name"], self.user.name)
        self.assertEqual(data["phone_number"], self.user.phone_number)


class TestProfileSerializers(TestCase):
    """Test suite for the profile serializers."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com", password="password123", name="Test User"
        )

        self.student = StudentProfile.objects.create(
            user=self.user,
            school_year="2024",
            birth_date=datetime.date(2000, 1, 1),
            address="Test Address",
        )

        self.teacher = TeacherProfile.objects.create(
            user=self.user, bio="Test Bio", specialty="Math", education="PhD"
        )

    def test_student_serializer(self):
        """Test serializing a student profile."""
        serializer = StudentSerializer(self.student)
        data = serializer.data
        self.assertEqual(data["user"]["email"], self.user.email)
        self.assertEqual(data["school_year"], self.student.school_year)
        self.assertEqual(data["address"], self.student.address)

    def test_teacher_serializer(self):
        """Test serializing a teacher profile."""
        serializer = TeacherSerializer(self.teacher)
        data = serializer.data
        self.assertEqual(data["user"]["email"], self.user.email)
        self.assertEqual(data["bio"], self.teacher.bio)
        self.assertEqual(data["specialty"], self.teacher.specialty)


class TestAuthSerializers(TestCase):
    """Test suite for authentication serializers."""

    def test_email_request_serializer_valid(self):
        """Test EmailRequestSerializer with valid data."""
        data = {"email": "test@example.com"}
        serializer = RequestCodeSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_email_request_serializer_invalid(self):
        """Test EmailRequestSerializer with invalid data."""
        data = {"email": "invalid-email"}
        serializer = RequestCodeSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_email_verify_serializer_valid(self):
        """Test EmailVerifySerializer with valid data."""
        data = {"email": "test@example.com", "code": "123456"}
        serializer = VerifyCodeSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_email_verify_serializer_invalid_code(self):
        """Test EmailVerifySerializer with invalid code."""
        data = {"email": "test@example.com", "code": "12345"}  # Code too short
        serializer = VerifyCodeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
