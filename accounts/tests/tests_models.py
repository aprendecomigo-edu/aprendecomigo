import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import EmailVerificationCode, Student, Teacher

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
        self.assertEqual(student.calendar_iframe, "")
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
        Student.objects.create(**self.student_data)

        # Refresh the user from the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, "student")

    def test_related_name_access(self):
        """Test accessing student profile via related name."""
        student = Student.objects.create(**self.student_data)
        self.assertEqual(self.user.student_profile, student)


class TeacherModelTests(TestCase):
    """Test cases for the Teacher model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="teacher@example.com",
            password="teacherpass123",
            name="Teacher User",
        )

        self.teacher_data = {
            "user": self.user,
            "bio": "Test biography",
            "specialty": "Mathematics",
            "education": "PhD in Mathematics",
            "hourly_rate": 50.0,
            "availability": "Weekdays 9am-5pm",
            "address": "456 Teaching St, Teacher City, 54321",
            "phone_number": "555-123-4567",
        }

    def tearDown(self):
        """Clean up database connections after each test."""
        super().tearDown()

    def test_create_teacher(self):
        """Test creating a teacher profile."""
        teacher = Teacher.objects.create(**self.teacher_data)
        self.assertEqual(teacher.user, self.user)
        self.assertEqual(teacher.bio, self.teacher_data["bio"])
        self.assertEqual(teacher.specialty, self.teacher_data["specialty"])
        self.assertEqual(teacher.education, self.teacher_data["education"])
        self.assertEqual(float(teacher.hourly_rate), self.teacher_data["hourly_rate"])
        self.assertEqual(teacher.availability, self.teacher_data["availability"])
        self.assertEqual(teacher.address, self.teacher_data["address"])
        self.assertEqual(teacher.phone_number, self.teacher_data["phone_number"])
        self.assertEqual(teacher.calendar_iframe, "")

    def test_teacher_string_representation(self):
        """Test the string representation of a teacher."""
        teacher = Teacher.objects.create(**self.teacher_data)
        self.assertEqual(str(teacher), f"Teacher: {self.user.name}")

    def test_user_type_set_on_save(self):
        """Test that user type is set to 'teacher' on save."""
        # Initially the user is not a teacher
        self.assertNotEqual(self.user.user_type, "teacher")

        # Creating a teacher profile should update user_type
        Teacher.objects.create(**self.teacher_data)

        # Refresh the user from the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, "teacher")

    def test_related_name_access(self):
        """Test accessing teacher profile via related name."""
        teacher = Teacher.objects.create(**self.teacher_data)
        self.assertEqual(self.user.teacher_profile, teacher)


class EmailVerificationCodeTests(TestCase):
    """Test cases for the EmailVerificationCode model."""

    def setUp(self):
        """Set up test data."""
        self.email = "verify@example.com"

    def tearDown(self):
        """Clean up database connections after each test."""
        super().tearDown()

    def test_generate_code(self):
        """Test generating a verification code."""
        # Clear any existing codes
        EmailVerificationCode.objects.filter(email=self.email).delete()

        # Generate a new code
        verification = EmailVerificationCode.generate_code(self.email)

        # Verify the code is created correctly
        self.assertEqual(verification.email, self.email)
        self.assertEqual(len(verification.code), 6)
        self.assertTrue(verification.code.isdigit())
        self.assertFalse(verification.is_used)

        # Verify old codes are deleted
        old_verification = EmailVerificationCode.generate_code(self.email)
        self.assertEqual(
            EmailVerificationCode.objects.filter(email=self.email).count(), 1
        )
        self.assertEqual(
            EmailVerificationCode.objects.get(email=self.email).id, old_verification.id
        )

    def test_is_valid(self):
        """Test verification code validity checking."""
        # Create a code
        verification = EmailVerificationCode.generate_code(self.email)

        # New code should be valid
        self.assertTrue(verification.is_valid())

        # Used code should be invalid
        verification.is_used = True
        verification.save()
        self.assertFalse(verification.is_valid())

        # Reset for expired test
        verification.is_used = False
        verification.save()

        # Expired code should be invalid
        verification.created_at = timezone.now() - datetime.timedelta(minutes=11)
        verification.save()
        self.assertFalse(verification.is_valid())

    def test_use(self):
        """Test marking a code as used."""
        verification = EmailVerificationCode.generate_code(self.email)
        self.assertFalse(verification.is_used)

        verification.use()
        self.assertTrue(verification.is_used)

        # Verify database was updated
        refreshed = EmailVerificationCode.objects.get(id=verification.id)
        self.assertTrue(refreshed.is_used)
