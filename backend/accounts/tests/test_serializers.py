from django.test import TestCase
from accounts.serializers import OnboardingSerializer, UserSerializer, StudentSerializer, TeacherSerializer, EmailRequestSerializer, EmailVerifySerializer
from accounts.models import CustomUser, StudentProfile, TeacherProfile
import datetime


class TestOnboardingSerializer(TestCase):
    """Test suite for the OnboardingSerializer."""

    def test_valid_user_data(self):
        """Test serializer with valid user data."""
        data = {
            'user': {
                'name': 'Test User',
                'phone_number': '+1234567890'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_valid_school_data(self):
        """Test serializer with valid school data."""
        data = {
            'school': {
                'name': 'Test School',
                'description': 'A test school',
                'contact_email': 'school@example.com',
                'phone_number': '+1234567890',
                'website': 'https://example.com'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_valid_complete_data(self):
        """Test serializer with both valid user and school data."""
        data = {
            'user': {
                'name': 'Test User',
                'phone_number': '+1234567890'
            },
            'school': {
                'name': 'Test School',
                'description': 'A test school',
                'contact_email': 'school@example.com',
                'phone_number': '+1234567890',
                'website': 'https://example.com'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_empty_data(self):
        """Test serializer with empty data."""
        data = {}
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("At least one of 'user' or 'school' information must be provided",
                     str(serializer.errors))

    def test_invalid_user_name(self):
        """Test serializer with invalid user name."""
        # Test empty name
        data = {
            'user': {
                'name': '',
                'phone_number': '+1234567890'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors.get('user', {}))

        # Test too long name
        data = {
            'user': {
                'name': 'x' * 151,
                'phone_number': '+1234567890'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors.get('user', {}))

    def test_invalid_user_phone(self):
        """Test serializer with invalid user phone number."""
        data = {
            'user': {
                'name': 'Test User',
                'phone_number': 'invalid-phone'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors.get('user', {}))

        # Test too long phone number
        data = {
            'user': {
                'name': 'Test User',
                'phone_number': '+' + '1' * 30
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors.get('user', {}))

    def test_invalid_school_name(self):
        """Test serializer with invalid school name."""
        # Test empty name
        data = {
            'school': {
                'name': '',
                'description': 'A test school'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors.get('school', {}))

        # Test too long name
        data = {
            'school': {
                'name': 'x' * 151,
                'description': 'A test school'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors.get('school', {}))

    def test_invalid_school_email(self):
        """Test serializer with invalid school email."""
        data = {
            'school': {
                'name': 'Test School',
                'contact_email': 'invalid-email'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contact_email', serializer.errors.get('school', {}))

    def test_invalid_school_phone(self):
        """Test serializer with invalid school phone number."""
        data = {
            'school': {
                'name': 'Test School',
                'phone_number': 'invalid-phone'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors.get('school', {}))

    def test_invalid_school_website(self):
        """Test serializer with invalid school website."""
        data = {
            'school': {
                'name': 'Test School',
                'website': 'invalid-website'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('website', serializer.errors.get('school', {}))

    def test_extra_user_fields_ignored(self):
        """Test that extra user fields are ignored."""
        data = {
            'user': {
                'name': 'Test User',
                'extra_field': 'This should be ignored'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('extra_field', serializer.validated_data['user'])

    def test_extra_school_fields_ignored(self):
        """Test that extra school fields are ignored."""
        data = {
            'school': {
                'name': 'Test School',
                'extra_field': 'This should be ignored'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('extra_field', serializer.validated_data['school'])


class TestUserSerializer(TestCase):
    """Test suite for the UserSerializer."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="password123",
            name="Test User",
            phone_number="1234567890"
        )

    def test_user_serializer(self):
        """Test serializing a user."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['name'], self.user.name)
        self.assertEqual(data['phone_number'], self.user.phone_number)


class TestProfileSerializers(TestCase):
    """Test suite for the profile serializers."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="password123",
            name="Test User"
        )

        self.student = StudentProfile.objects.create(
            user=self.user,
            school_year="2024",
            birth_date=datetime.date(2000, 1, 1),
            address="Test Address"
        )

        self.teacher = TeacherProfile.objects.create(
            user=self.user,
            bio="Test Bio",
            specialty="Math",
            education="PhD"
        )

    def test_student_serializer(self):
        """Test serializing a student profile."""
        serializer = StudentSerializer(self.student)
        data = serializer.data
        self.assertEqual(data['user']['email'], self.user.email)
        self.assertEqual(data['school_year'], self.student.school_year)
        self.assertEqual(data['address'], self.student.address)

    def test_teacher_serializer(self):
        """Test serializing a teacher profile."""
        serializer = TeacherSerializer(self.teacher)
        data = serializer.data
        self.assertEqual(data['user']['email'], self.user.email)
        self.assertEqual(data['bio'], self.teacher.bio)
        self.assertEqual(data['specialty'], self.teacher.specialty)


class TestAuthSerializers(TestCase):
    """Test suite for authentication serializers."""

    def test_email_request_serializer_valid(self):
        """Test EmailRequestSerializer with valid data."""
        data = {"email": "test@example.com"}
        serializer = EmailRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_email_request_serializer_invalid(self):
        """Test EmailRequestSerializer with invalid data."""
        data = {"email": "invalid-email"}
        serializer = EmailRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_email_verify_serializer_valid(self):
        """Test EmailVerifySerializer with valid data."""
        data = {"email": "test@example.com", "code": "123456"}
        serializer = EmailVerifySerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_email_verify_serializer_invalid_code(self):
        """Test EmailVerifySerializer with invalid code."""
        data = {"email": "test@example.com", "code": "12345"}  # Code too short
        serializer = EmailVerifySerializer(data=data)
        self.assertFalse(serializer.is_valid())
