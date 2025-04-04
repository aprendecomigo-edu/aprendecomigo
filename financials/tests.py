from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from scheduling.models import ClassSession, ClassType

from .models import PaymentPlan, StudentPayment, TeacherCompensation

User = get_user_model()


class FinancialPermissionsTestCase(TestCase):
    """
    Test case for financial permissions to ensure proper access control
    """

    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="adminpass",
            name="Admin User",
            user_type="admin",
            is_admin=True,
            is_staff=True,
        )

        self.teacher_user = User.objects.create_user(
            email="teacher@test.com",
            password="teacherpass",
            name="Teacher User",
            user_type="teacher",
        )

        self.student_user = User.objects.create_user(
            email="student@test.com",
            password="studentpass",
            name="Student User",
            user_type="student",
        )

        self.other_teacher = User.objects.create_user(
            email="other.teacher@test.com",
            password="otherteacherpass",
            name="Other Teacher",
            user_type="teacher",
        )

        self.other_student = User.objects.create_user(
            email="other.student@test.com",
            password="otherstudentpass",
            name="Other Student",
            user_type="student",
        )

        # Create test class type
        self.class_type = ClassType.objects.create(
            name="Test Class", hourly_rate=Decimal("50.00")
        )

        # Create test payment plans with different names
        self.payment_plan = PaymentPlan.objects.create(
            name="Student A Package",
            description="Test payment plan for Student A",
            plan_type="package",
            rate=Decimal("500.00"),
            hours_included=10,
            expiration_period=30,
            class_type=self.class_type,
        )

        self.other_payment_plan = PaymentPlan.objects.create(
            name="Student B Package",
            description="Test payment plan for Student B",
            plan_type="package",
            rate=Decimal("550.00"),
            hours_included=12,
            expiration_period=30,
            class_type=self.class_type,
        )

        # Create student payments with different payment plans
        self.student_payment = StudentPayment.objects.create(
            student=self.student_user,
            payment_plan=self.payment_plan,
            amount_paid=Decimal("500.00"),
            payment_date=timezone.now().date(),
            hours_purchased=10,
            status="completed",
        )

        self.other_student_payment = StudentPayment.objects.create(
            student=self.other_student,
            payment_plan=self.other_payment_plan,
            amount_paid=Decimal("550.00"),
            payment_date=timezone.now().date(),
            hours_purchased=12,
            status="completed",
        )

        # Create subject for class sessions

        # Create class sessions
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=2)

        self.class_session = ClassSession.objects.create(
            title="Test Session",
            teacher=self.teacher_user,
            class_type=self.class_type,
            start_time=start_time,
            end_time=end_time,
            google_calendar_id="test123",
            attended=True,
        )
        self.class_session.students.add(self.student_user)

        self.other_class_session = ClassSession.objects.create(
            title="Other Session",
            teacher=self.other_teacher,
            class_type=self.class_type,
            start_time=start_time,
            end_time=end_time,
            google_calendar_id="test456",
            attended=True,
        )
        self.other_class_session.students.add(self.other_student)

        # Create teacher compensations with different amounts
        period_start = timezone.now().date() - timedelta(days=30)
        period_end = timezone.now().date()

        self.teacher_compensation = TeacherCompensation.objects.create(
            teacher=self.teacher_user,
            period_start=period_start,
            period_end=period_end,
            hours_taught=Decimal("2.00"),
            amount_owed=Decimal("80.00"),
            amount_paid=Decimal("0.00"),
            status="pending",
        )
        self.teacher_compensation.class_sessions.add(self.class_session)

        self.other_teacher_compensation = TeacherCompensation.objects.create(
            teacher=self.other_teacher,
            period_start=period_start,
            period_end=period_end,
            hours_taught=Decimal("2.00"),
            amount_owed=Decimal("100.00"),
            amount_paid=Decimal("0.00"),
            status="pending",
        )
        self.other_teacher_compensation.class_sessions.add(self.other_class_session)

        # Initialize test client
        self.client = Client()

    def test_student_payment_list_permissions(self):
        """Test permission restrictions for student payment list view"""
        url = reverse("financials:student_payment_list")

        # Anonymous user should be redirected to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/accounts/login/" in response.url)

        # Student user should be able to access but see only their payments
        self.client.login(email="student@test.com", password="studentpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student A Package")
        self.assertNotContains(response, "Student B Package")

        # Teacher user should get a 404 instead of 403
        self.client.login(email="teacher@test.com", password="teacherpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Admin user should be able to see all payments
        self.client.login(email="admin@test.com", password="adminpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student A Package")
        self.assertContains(response, "Student B Package")

    def test_student_payment_detail_permissions(self):
        """Test permission restrictions for student payment detail view"""
        url = reverse(
            "financials:student_payment_detail", args=[self.student_payment.id]
        )
        other_url = reverse(
            "financials:student_payment_detail", args=[self.other_student_payment.id]
        )

        # Anonymous user should be redirected to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/accounts/login/" in response.url)

        # Student user should be able to access their own payment details
        self.client.login(email="student@test.com", password="studentpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # But not another student's payment details (404)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 404)

        # Teacher user should not be able to see any student payment details (404)
        self.client.login(email="teacher@test.com", password="teacherpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 404)

        # Admin user should be able to see all payment details
        self.client.login(email="admin@test.com", password="adminpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 200)

    def test_student_payments_permissions(self):
        """Test permission restrictions for student payments view"""
        url = reverse("financials:student_payments", args=[self.student_user.id])
        other_url = reverse("financials:student_payments", args=[self.other_student.id])

        # Anonymous user should be redirected to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/accounts/login/" in response.url)

        # Student user should be able to access their own payments page
        self.client.login(email="student@test.com", password="studentpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # But not another student's payments page (404)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 404)

        # Teacher user should not be able to see any student payments page (404)
        self.client.login(email="teacher@test.com", password="teacherpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 404)

        # Admin user should be able to see all student payments pages
        self.client.login(email="admin@test.com", password="adminpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 200)

    def test_teacher_compensation_list_permissions(self):
        """Test permission restrictions for teacher compensation list view"""
        url = reverse("financials:teacher_compensation_list")

        # Anonymous user should be redirected to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/accounts/login/" in response.url)

        # Teacher user should be able to access but see only their compensations
        self.client.login(email="teacher@test.com", password="teacherpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "$80.00")
        self.assertNotContains(response, "$100.00")

        # Student user should not be able to see teacher compensations (404)
        self.client.login(email="student@test.com", password="studentpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Admin user should be able to see all compensations
        self.client.login(email="admin@test.com", password="adminpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "$80.00")
        self.assertContains(response, "$100.00")

    def test_teacher_compensation_detail_permissions(self):
        """Test permission restrictions for teacher compensation detail view"""
        url = reverse(
            "financials:teacher_compensation_detail",
            args=[self.teacher_compensation.id],
        )
        other_url = reverse(
            "financials:teacher_compensation_detail",
            args=[self.other_teacher_compensation.id],
        )

        # Anonymous user should be redirected to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/accounts/login/" in response.url)

        # Teacher user should be able to access their own compensation details
        self.client.login(email="teacher@test.com", password="teacherpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # But not another teacher's compensation details (404)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 404)

        # Student user should not be able to see any teacher compensation details (404)
        self.client.login(email="student@test.com", password="studentpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 404)

        # Admin user should be able to see all compensation details
        self.client.login(email="admin@test.com", password="adminpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 200)

    def test_teacher_compensations_permissions(self):
        """Test permission restrictions for teacher compensations view"""
        url = reverse("financials:teacher_compensations", args=[self.teacher_user.id])
        other_url = reverse(
            "financials:teacher_compensations", args=[self.other_teacher.id]
        )

        # Anonymous user should be redirected to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/accounts/login/" in response.url)

        # Teacher user should be able to access their own compensations page
        self.client.login(email="teacher@test.com", password="teacherpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # But not another teacher's compensations page (404)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 404)

        # Student user should not be able to see any teacher compensations page (404)
        self.client.login(email="student@test.com", password="studentpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 404)

        # Admin user should be able to see all teacher compensations pages
        self.client.login(email="admin@test.com", password="adminpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 200)

    def test_financial_reports_admin_only(self):
        """Test that financial reports are restricted to admin users only"""
        report_urls = [
            reverse("financials:payment_report"),
            reverse("financials:compensation_report"),
            reverse("financials:financial_summary"),
            reverse("financials:admin_dashboard"),
        ]

        # Test each report URL
        for i, url in enumerate(report_urls):
            print(f"\nTesting URL {i+1}: {url}")

            # Make sure we're logged out
            self.client.logout()

            # Anonymous user should be redirected to login
            response = self.client.get(url)
            print(f"Anonymous user response status: {response.status_code}")
            self.assertEqual(response.status_code, 302)
            self.assertTrue("/accounts/login/" in response.url)

            # Student user should get a 404 instead of redirect
            self.client.login(email="student@test.com", password="studentpass")
            response = self.client.get(url)
            print(f"Student user response status: {response.status_code}")
            self.assertEqual(response.status_code, 404)

            # Teacher user should get a 404 instead of redirect
            self.client.login(email="teacher@test.com", password="teacherpass")
            response = self.client.get(url)
            print(f"Teacher user response status: {response.status_code}")
            self.assertEqual(response.status_code, 404)

            # Admin user should be able to access all reports
            self.client.login(email="admin@test.com", password="adminpass")
            response = self.client.get(url)
            print(f"Admin user response status: {response.status_code}")
            self.assertEqual(response.status_code, 200)
