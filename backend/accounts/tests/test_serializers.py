import datetime

from django.test import TestCase
from rest_framework.test import APITestCase

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

    def test_user_serializer_read(self):
        """Test serializing a user for reading."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        # Verify all expected fields are present
        self.assertIn('id', data)
        self.assertIn('email', data)
        self.assertIn('name', data)
        self.assertIn('phone_number', data)
        
        # Verify field values
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["name"], self.user.name)
        self.assertEqual(data["phone_number"], self.user.phone_number)
        
        # Ensure sensitive fields are not exposed
        self.assertNotIn('password', data)
    
    def test_user_serializer_validation(self):
        """Test UserSerializer validation rules."""
        # Test valid data
        valid_data = {
            "email": "valid@example.com",
            "name": "Valid User",
            "phone_number": "+1234567890"
        }
        serializer = UserSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid email
        invalid_email_data = valid_data.copy()
        invalid_email_data["email"] = "invalid-email"
        serializer = UserSerializer(data=invalid_email_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        # Test missing required fields
        incomplete_data = {"email": "test@example.com"}
        serializer = UserSerializer(data=incomplete_data)
        self.assertFalse(serializer.is_valid())


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

    def test_request_code_serializer_valid_email(self):
        """Test RequestCodeSerializer accepts valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user+tag@domain.org", 
            "test.email@subdomain.example.co.uk"
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                data = {"email": email}
                serializer = RequestCodeSerializer(data=data)
                self.assertTrue(serializer.is_valid(), 
                               f"Should accept valid email: {email}")

    def test_request_code_serializer_invalid_email(self):
        """Test RequestCodeSerializer rejects invalid email addresses."""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user..double@domain.com",
            ""
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                data = {"email": email}
                serializer = RequestCodeSerializer(data=data)
                self.assertFalse(serializer.is_valid(),
                                f"Should reject invalid email: {email}")
                self.assertIn('email', serializer.errors)

    def test_verify_code_serializer_valid_data(self):
        """Test VerifyCodeSerializer accepts valid email and code combinations."""
        valid_data = {
            "email": "test@example.com", 
            "code": "123456"
        }
        serializer = VerifyCodeSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Verify cleaned data structure
        self.assertEqual(serializer.validated_data['email'], "test@example.com")
        self.assertEqual(serializer.validated_data['code'], "123456")

    def test_verify_code_serializer_invalid_code_length(self):
        """Test VerifyCodeSerializer rejects codes with wrong length."""
        invalid_codes = ["123", "12345", "1234567", ""]
        
        for code in invalid_codes:
            with self.subTest(code=code):
                data = {"email": "test@example.com", "code": code}
                serializer = VerifyCodeSerializer(data=data)
                self.assertFalse(serializer.is_valid(),
                                f"Should reject code with length {len(code)}")
                self.assertIn('code', serializer.errors)
    
    def test_verify_code_serializer_missing_fields(self):
        """Test VerifyCodeSerializer requires both email and code."""
        # Missing email
        data = {"code": "123456"}
        serializer = VerifyCodeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        # Missing code  
        data = {"email": "test@example.com"}
        serializer = VerifyCodeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)
