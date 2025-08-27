"""
Tests for education app - Milestone 3: Core Educational Features
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta

from accounts.models import School, TeacherProfile, StudentProfile
from .models import Subject, Course, Enrollment, Lesson, Assignment, Payment
from .services import EducationPaymentService

User = get_user_model()


class EducationModelsTest(TestCase):
    """Test education models functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            contact_email="test@school.com",
            phone_number="+1234567890"
        )
        
        # Create teacher user and profile
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com",
            first_name="Test",
            last_name="Teacher"
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Experienced math teacher",
            specialty="Mathematics",
            hourly_rate=Decimal("30.00")
        )
        
        # Create student user and profile
        self.student_user = User.objects.create_user(
            email="student@test.com",
            first_name="Test",
            last_name="Student"
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            school_year="10",
            birth_date="2008-01-01"
        )
        
        # Create subject
        self.subject = Subject.objects.create(
            name="Mathematics",
            code="MATH",
            description="Math subject"
        )
        
        # Create course
        self.course = Course.objects.create(
            title="Algebra Basics",
            description="Learn algebra",
            subject=self.subject,
            teacher=self.teacher_profile,
            price_per_hour=Decimal("25.00"),
            total_hours=10,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=60),
            status="published"
        )
    
    def test_subject_creation(self):
        """Test subject model"""
        self.assertEqual(str(self.subject), "Mathematics (MATH)")
        self.assertTrue(self.subject.is_active)
    
    def test_course_creation(self):
        """Test course model"""
        self.assertEqual(str(self.course), "Algebra Basics - Test Teacher")
        self.assertEqual(self.course.total_price, Decimal("250.00"))
        self.assertFalse(self.course.is_full)
    
    def test_enrollment_creation(self):
        """Test enrollment model"""
        enrollment = Enrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            start_date=self.course.start_date,
            status="active"
        )
        
        self.assertEqual(str(enrollment), "Test Student enrolled in Algebra Basics")
        self.assertEqual(enrollment.progress_percentage, 0)
        
        # Test progress update
        enrollment.hours_completed = Decimal("5.0")
        enrollment.update_progress()
        self.assertEqual(enrollment.progress_percentage, 50)
    
    def test_lesson_creation(self):
        """Test lesson model"""
        lesson = Lesson.objects.create(
            course=self.course,
            title="Introduction to Algebra",
            scheduled_date=timezone.now() + timedelta(days=1),
            duration_minutes=60
        )
        
        self.assertIn("Introduction to Algebra", str(lesson))
        self.assertEqual(lesson.actual_duration_minutes, 60)
    
    def test_assignment_creation(self):
        """Test assignment model"""
        assignment = Assignment.objects.create(
            course=self.course,
            title="Homework 1",
            description="Solve basic equations",
            due_date=timezone.now() + timedelta(days=7)
        )
        
        self.assertEqual(str(assignment), "Homework 1 - Algebra Basics")
        self.assertEqual(assignment.max_points, 100)
    
    def test_payment_creation(self):
        """Test payment model"""
        payment = Payment.objects.create(
            student=self.student_profile,
            teacher=self.teacher_profile,
            amount=Decimal("250.00"),
            teacher_amount=Decimal("237.50"),
            platform_fee=Decimal("12.50"),
            description="Course enrollment",
            status="completed"
        )
        
        self.assertIn("€250.00", str(payment))
        self.assertEqual(payment.calculate_teacher_amount(), Decimal("237.50"))


class EducationViewsTest(TestCase):
    """Test education views"""
    
    def setUp(self):
        """Set up test data"""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            contact_email="test@school.com",
            phone_number="+1234567890"
        )
        
        # Create teacher user and profile
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com",
            first_name="Test",
            last_name="Teacher"
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Experienced math teacher",
            specialty="Mathematics",
            hourly_rate=Decimal("30.00")
        )
        
        # Create student user and profile
        self.student_user = User.objects.create_user(
            email="student@test.com",
            first_name="Test",
            last_name="Student"
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            school_year="10",
            birth_date="2008-01-01"
        )
        
        self.client = Client()
    
    def test_teacher_dashboard_redirect(self):
        """Test teacher dashboard requires authentication"""
        response = self.client.get(reverse('education:teacher_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_teacher_dashboard_access(self):
        """Test authenticated teacher can access dashboard"""
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('education:teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Teacher Dashboard")
    
    def test_student_portal_redirect(self):
        """Test student portal requires authentication"""
        response = self.client.get(reverse('education:student_portal'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_student_portal_access(self):
        """Test authenticated student can access portal"""
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('education:student_portal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available Courses")


class EducationPaymentServiceTest(TestCase):
    """Test education payment service"""
    
    def setUp(self):
        """Set up test data"""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            contact_email="test@school.com",
            phone_number="+1234567890"
        )
        
        # Create teacher user and profile
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com",
            first_name="Test",
            last_name="Teacher"
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Experienced math teacher",
            specialty="Mathematics",
            hourly_rate=Decimal("30.00")
        )
        
        # Create student user and profile
        self.student_user = User.objects.create_user(
            email="student@test.com",
            first_name="Test",
            last_name="Student"
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            school_year="10",
            birth_date="2008-01-01"
        )
        
        # Create subject and course
        self.subject = Subject.objects.create(
            name="Mathematics",
            code="MATH"
        )
        
        self.course = Course.objects.create(
            title="Algebra Basics",
            description="Learn algebra",
            subject=self.subject,
            teacher=self.teacher_profile,
            price_per_hour=Decimal("25.00"),
            total_hours=10,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=60),
            status="published"
        )
        
        self.service = EducationPaymentService()
    
    def test_platform_fee_calculation(self):
        """Test platform fee calculation"""
        amount = Decimal("100.00")
        expected_fee = Decimal("5.00")  # 5%
        calculated_fee = self.service._calculate_platform_fee(amount)
        self.assertEqual(calculated_fee, expected_fee)
    
    def test_teacher_amount_calculation(self):
        """Test teacher amount calculation"""
        amount = Decimal("100.00")
        expected_amount = Decimal("95.00")  # 100 - 5% fee
        calculated_amount = self.service._calculate_teacher_amount(amount)
        self.assertEqual(calculated_amount, expected_amount)
    
    def test_payment_history_empty(self):
        """Test payment history for student with no payments"""
        result = self.service.get_student_payment_history(self.student_user)
        self.assertTrue(result['success'])
        self.assertEqual(result['payment_count'], 0)
        self.assertEqual(result['total_spent'], '0.00')
    
    def test_teacher_earnings_empty(self):
        """Test teacher earnings with no payments"""
        result = self.service.get_teacher_earnings(self.teacher_user)
        self.assertTrue(result['success'])
        self.assertEqual(result['payment_count'], 0)
        self.assertEqual(result['total_earnings'], '0.00')
