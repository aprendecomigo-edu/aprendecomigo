"""
Test cases for session booking hour deduction functionality.

This module follows TDD methodology and tests the integration of the tutoring hour 
purchase system with session booking functionality, including:
- Hour deduction during session creation
- Balance validation before booking
- Session cancellation with refunds
- Group session hour calculations
- Package expiration handling
- Comprehensive error scenarios

Following GitHub Issue #32: "Implement Session Booking Hour Deduction"
"""

from decimal import Decimal
from datetime import date, time, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from accounts.models import School, TeacherProfile

User = get_user_model()

from finances.models import (
    ClassSession,
    StudentAccountBalance,
    PurchaseTransaction,
    HourConsumption,
    SessionStatus,
    SessionType,
    TransactionType,
    TransactionPaymentStatus,
    PricingPlan,
    PlanType,
)


class SessionBookingHourDeductionTestCase(TestCase):
    """Test suite for session booking hour deduction functionality."""

    def setUp(self):
        """Set up test data for each test method."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school for hour deduction",
            contact_email="test@school.com"
        )
        
        # Create student user
        self.student = User.objects.create_user(
            email="student@test.com",
            username="student1",
            name="Test Student"
        )
        
        # Create additional student for group sessions
        self.student2 = User.objects.create_user(
            email="student2@test.com",
            username="student2",
            name="Test Student 2"
        )
        
        # Create teacher user and profile
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com",
            username="teacher1",
            name="Test Teacher"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Experienced teacher"
        )
        
        # Create pricing plan
        self.pricing_plan = PricingPlan.objects.create(
            name="10 Hour Package",
            description="10 tutoring hours",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            is_active=True
        )
        
        # Create student account balance with sufficient hours
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("0.00"),
            balance_amount=Decimal("100.00")
        )
        
        # Create student2 account balance
        self.student2_balance = StudentAccountBalance.objects.create(
            student=self.student2,
            hours_purchased=Decimal("5.00"),
            hours_consumed=Decimal("0.00"),
            balance_amount=Decimal("50.00")
        )
        
        # Create completed purchase transaction
        self.purchase_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(days=30),
            metadata={
                "plan_id": self.pricing_plan.id,
                "plan_name": self.pricing_plan.name,
                "hours_included": "10.00"
            }
        )
        
        # Create purchase transaction for student2
        self.purchase_transaction2 = PurchaseTransaction.objects.create(
            student=self.student2,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(days=30),
            metadata={
                "plan_id": self.pricing_plan.id,
                "plan_name": self.pricing_plan.name,
                "hours_included": "5.00"
            }
        )

    def test_session_creation_should_deduct_hours_individual_session(self):
        """Test that creating an individual session deducts hours from student balance."""
        # Create a 1-hour individual session
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),  # 1 hour
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student)
        
        # Process hour deduction for the session
        session.process_hour_deduction()
        
        # Refresh balance from database
        self.student_balance.refresh_from_db()
        
        # Verify hours were deducted
        expected_hours_consumed = Decimal("1.00")
        self.assertEqual(
            self.student_balance.hours_consumed, 
            expected_hours_consumed,
            "Hours should be deducted when session is created"
        )
        
        # Verify HourConsumption record was created
        consumption = HourConsumption.objects.filter(
            student_account=self.student_balance,
            class_session=session
        ).first()
        
        self.assertIsNotNone(consumption, "HourConsumption record should be created")
        self.assertEqual(consumption.hours_consumed, Decimal("1.00"))
        self.assertEqual(consumption.hours_originally_reserved, Decimal("1.00"))
        self.assertEqual(consumption.purchase_transaction, self.purchase_transaction)

    def test_session_creation_should_deduct_hours_group_session(self):
        """Test that creating a group session deducts hours from each student."""
        # Create a 1.5-hour group session
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 30),  # 1.5 hours
            session_type=SessionType.GROUP,
            grade_level="10",
            student_count=2,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student, self.student2)
        
        # Process hour deduction for the session
        session.process_hour_deduction()
        
        # Refresh balances from database
        self.student_balance.refresh_from_db()
        self.student2_balance.refresh_from_db()
        
        # Verify hours were deducted from both students
        expected_hours_consumed = Decimal("1.50")
        self.assertEqual(
            self.student_balance.hours_consumed,
            expected_hours_consumed,
            "Hours should be deducted from first student"
        )
        self.assertEqual(
            self.student2_balance.hours_consumed,
            expected_hours_consumed,
            "Hours should be deducted from second student"
        )
        
        # Verify HourConsumption records were created for both students
        consumption1 = HourConsumption.objects.filter(
            student_account=self.student_balance,
            class_session=session
        ).first()
        consumption2 = HourConsumption.objects.filter(
            student_account=self.student2_balance,
            class_session=session
        ).first()
        
        self.assertIsNotNone(consumption1, "HourConsumption record should be created for student 1")
        self.assertIsNotNone(consumption2, "HourConsumption record should be created for student 2")
        self.assertEqual(consumption1.hours_consumed, Decimal("1.50"))
        self.assertEqual(consumption2.hours_consumed, Decimal("1.50"))

    def test_session_creation_insufficient_balance_should_fail(self):
        """Test that session creation fails when student has insufficient balance."""
        # Reduce student balance to insufficient level
        self.student_balance.hours_consumed = Decimal("9.50")  # Only 0.5 hours remaining
        self.student_balance.save()
        
        # Attempt to create a 1-hour session should fail
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),  # 1 hour needed, but only 0.5 available
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student)
        
        # Process hour deduction - this should fail
        with self.assertRaises(ValidationError) as context:
            session.process_hour_deduction()
        
        # Verify appropriate error message
        self.assertIn("insufficient balance", str(context.exception).lower())
        
        # Verify no HourConsumption record was created
        self.assertEqual(
            HourConsumption.objects.filter(student_account=self.student_balance).count(),
            0,
            "No HourConsumption record should be created for failed booking"
        )

    def test_session_creation_one_student_insufficient_balance_group_session(self):
        """Test group session creation fails if any student has insufficient balance."""
        # Make student2 have insufficient balance
        self.student2_balance.hours_consumed = Decimal("4.50")  # Only 0.5 hours remaining
        self.student2_balance.save()
        
        # Attempt to create 1-hour group session should fail
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),  # 1 hour
            session_type=SessionType.GROUP,
            grade_level="10",
            student_count=2,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student, self.student2)
        
        # Process hour deduction - this should fail
        with self.assertRaises(ValidationError) as context:
            session.process_hour_deduction()
        
        # Verify appropriate error message
        self.assertIn("insufficient balance", str(context.exception).lower())
        
        # Verify no hours were deducted from any student
        self.student_balance.refresh_from_db()
        self.student2_balance.refresh_from_db()
        self.assertEqual(self.student_balance.hours_consumed, Decimal("0.00"))
        self.assertEqual(self.student2_balance.hours_consumed, Decimal("4.50"))  # Unchanged

    def test_session_cancellation_should_refund_hours(self):
        """Test that cancelling a session refunds hours to student account."""
        # First create a session (this will deduct hours)
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),  # 1 hour
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student)
        
        # Process hour deduction for the session
        session.process_hour_deduction()
        
        # Verify hours were deducted
        self.student_balance.refresh_from_db()
        self.assertEqual(self.student_balance.hours_consumed, Decimal("1.00"))
        
        # Cancel the session
        session.status = SessionStatus.CANCELLED
        session.save()
        
        # Verify hours were refunded
        self.student_balance.refresh_from_db()
        self.assertEqual(
            self.student_balance.hours_consumed,
            Decimal("0.00"),
            "Hours should be refunded when session is cancelled"
        )
        
        # Verify HourConsumption record shows refund
        consumption = HourConsumption.objects.filter(
            student_account=self.student_balance,
            class_session=session
        ).first()
        
        self.assertIsNotNone(consumption)
        self.assertTrue(consumption.is_refunded, "HourConsumption should be marked as refunded")
        self.assertIn("cancelled", consumption.refund_reason.lower())

    def test_session_completion_no_refund(self):
        """Test that completing a session does not trigger refund."""
        # Create a session
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),  # 1 hour
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student)
        
        # Process hour deduction for the session
        session.process_hour_deduction()
        
        # Complete the session
        session.status = SessionStatus.COMPLETED
        session.save()
        
        # Verify hours remain consumed
        self.student_balance.refresh_from_db()
        self.assertEqual(
            self.student_balance.hours_consumed,
            Decimal("1.00"),
            "Hours should remain consumed when session is completed"
        )
        
        # Verify HourConsumption record is not refunded
        consumption = HourConsumption.objects.filter(
            student_account=self.student_balance,
            class_session=session
        ).first()
        
        self.assertIsNotNone(consumption)
        self.assertFalse(consumption.is_refunded, "HourConsumption should not be refunded for completed session")

    def test_session_duration_calculation_accuracy(self):
        """Test accurate hour calculation for different session durations."""
        test_cases = [
            # (start_time, end_time, expected_hours)
            (time(14, 0), time(15, 0), Decimal("1.00")),  # 1 hour
            (time(14, 0), time(14, 30), Decimal("0.50")),  # 30 minutes
            (time(14, 0), time(15, 30), Decimal("1.50")),  # 1.5 hours
            (time(14, 15), time(15, 0), Decimal("0.75")),  # 45 minutes
            (time(14, 0), time(16, 15), Decimal("2.25")),  # 2.25 hours
        ]
        
        for i, (start_time, end_time, expected_hours) in enumerate(test_cases):
            with self.subTest(case=i, start=start_time, end=end_time):
                # Create unique session for each test case
                session = ClassSession.objects.create(
                    teacher=self.teacher,
                    school=self.school,
                    date=date.today() + timedelta(days=i),  # Different dates to avoid conflicts
                    start_time=start_time,
                    end_time=end_time,
                    session_type=SessionType.INDIVIDUAL,
                    grade_level="10",
                    student_count=1,
                    status=SessionStatus.SCHEDULED
                )
                
                # Create new student for each test to avoid balance conflicts
                student = User.objects.create_user(
                    email=f"student{i}@test.com",
                    username=f"student{i}",
                    name=f"Test Student {i}"
                )
                student_balance = StudentAccountBalance.objects.create(
                    student=student,
                    hours_purchased=Decimal("10.00"),
                    hours_consumed=Decimal("0.00"),
                    balance_amount=Decimal("100.00")
                )
                
                session.students.add(student)
                
                # Process hour deduction for the session
                session.process_hour_deduction()
                
                # Verify correct hours were deducted
                student_balance.refresh_from_db()
                self.assertEqual(
                    student_balance.hours_consumed,
                    expected_hours,
                    f"Expected {expected_hours} hours to be deducted for session from {start_time} to {end_time}"
                )

    def test_package_expiration_during_booking_should_fail(self):
        """Test that booking fails if student's package has expired."""
        # Set purchase transaction to expired
        self.purchase_transaction.expires_at = timezone.now() - timedelta(days=1)
        self.purchase_transaction.save()
        
        # Create session and attempt hour deduction (should fail)
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student)
        
        # Attempt hour deduction should fail
        with self.assertRaises(ValidationError) as context:
            session.process_hour_deduction()
        
        # Verify appropriate error message
        self.assertIn("expired", str(context.exception).lower())

    def test_multiple_active_packages_hour_deduction_fifo(self):
        """Test that hours are deducted from oldest package first (FIFO)."""
        # Create a second, newer purchase transaction
        newer_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(days=60),  # Expires later
            metadata={
                "plan_id": self.pricing_plan.id,
                "plan_name": "5 Hour Package",
                "hours_included": "5.00"
            },
            created_at=timezone.now() + timedelta(seconds=1)  # Created after first transaction
        )
        
        # Update student balance to reflect both packages
        self.student_balance.hours_purchased = Decimal("15.00")  # 10 + 5
        self.student_balance.save()
        
        # Create session
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),  # 1 hour
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student)
        
        # Process hour deduction for the session
        session.process_hour_deduction()
        
        # Verify hour consumption record references the older transaction
        consumption = HourConsumption.objects.filter(
            student_account=self.student_balance,
            class_session=session
        ).first()
        
        self.assertIsNotNone(consumption)
        self.assertEqual(
            consumption.purchase_transaction,
            self.purchase_transaction,  # Should be the older transaction
            "Hours should be deducted from oldest package first (FIFO)"
        )

    def test_no_show_session_keeps_hours_consumed(self):
        """Test that no-show sessions keep hours consumed (no refund)."""
        # Create session
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student)
        
        # Process hour deduction for the session
        session.process_hour_deduction()
        
        # Mark as no-show
        session.status = SessionStatus.NO_SHOW
        session.save()
        
        # Verify hours remain consumed
        self.student_balance.refresh_from_db()
        self.assertEqual(
            self.student_balance.hours_consumed,
            Decimal("1.00"),
            "Hours should remain consumed for no-show sessions"
        )
        
        # Verify no refund was processed
        consumption = HourConsumption.objects.filter(
            student_account=self.student_balance,
            class_session=session
        ).first()
        
        self.assertIsNotNone(consumption)
        self.assertFalse(consumption.is_refunded, "No refund should be processed for no-show sessions")

    def test_trial_session_no_hour_deduction(self):
        """Test that trial sessions do not deduct hours from student balance."""
        # Create trial session
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED,
            is_trial=True  # This is a trial session
        )
        session.students.add(self.student)
        
        # Process hour deduction for the session (should skip trial sessions)
        session.process_hour_deduction()
        
        # Verify no hours were deducted
        self.student_balance.refresh_from_db()
        self.assertEqual(
            self.student_balance.hours_consumed,
            Decimal("0.00"),
            "Trial sessions should not deduct hours"
        )
        
        # Verify no HourConsumption record was created
        consumption_count = HourConsumption.objects.filter(
            student_account=self.student_balance,
            class_session=session
        ).count()
        
        self.assertEqual(consumption_count, 0, "No HourConsumption record should be created for trial sessions")

    def test_zero_duration_session_should_fail(self):
        """Test that sessions with zero duration fail validation."""
        with self.assertRaises(ValidationError):
            session = ClassSession.objects.create(
                teacher=self.teacher,
                school=self.school,
                date=date.today(),
                start_time=time(14, 0),
                end_time=time(14, 0),  # Same start and end time
                session_type=SessionType.INDIVIDUAL,
                grade_level="10",
                student_count=1,
                status=SessionStatus.SCHEDULED
            )
            session.students.add(self.student)

    def test_session_with_no_students_no_hour_deduction(self):
        """Test that sessions with no students do not trigger hour deduction."""
        # Create session without adding students
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=0,  # No students
            status=SessionStatus.SCHEDULED
        )
        
        # Process hour deduction (should be skipped for sessions with no students)
        session.process_hour_deduction()
        
        # Verify no hours were deducted from any student
        self.student_balance.refresh_from_db()
        self.assertEqual(self.student_balance.hours_consumed, Decimal("0.00"))
        
        # Verify no HourConsumption records were created
        self.assertEqual(HourConsumption.objects.count(), 0)

    def test_hour_deduction_atomic_transaction(self):
        """Test that hour deduction is atomic - all students or none."""
        # Create a scenario where the second student has insufficient balance
        # but the deduction process should be atomic
        self.student2_balance.hours_consumed = Decimal("4.50")  # Only 0.5 hours left
        self.student2_balance.save()
        
        # Mock a database error during the second student's deduction
        with patch('finances.models.StudentAccountBalance.save') as mock_save:
            # Make save fail on second call (for student2)
            mock_save.side_effect = [None, Exception("Database error")]
            
            with self.assertRaises(Exception):
                session = ClassSession.objects.create(
                    teacher=self.teacher,
                    school=self.school,
                    date=date.today(),
                    start_time=time(14, 0),
                    end_time=time(15, 0),
                    session_type=SessionType.GROUP,
                    grade_level="10",
                    student_count=2,
                    status=SessionStatus.SCHEDULED
                )
                session.students.add(self.student, self.student2)
        
        # Verify that no changes were committed due to transaction rollback
        self.student_balance.refresh_from_db()
        self.student2_balance.refresh_from_db()
        self.assertEqual(self.student_balance.hours_consumed, Decimal("0.00"))
        self.assertEqual(self.student2_balance.hours_consumed, Decimal("4.50"))  # Unchanged
        self.assertEqual(HourConsumption.objects.count(), 0)


class SessionBookingHourDeductionAPITestCase(APITestCase):
    """Test suite for API endpoints related to session booking hour deduction."""

    def setUp(self):
        """Set up test data for API tests."""
        # Create school
        self.school = School.objects.create(
            name="API Test School",
            description="A test school for API testing",
            contact_email="api@test.com"
        )
        
        # Create student user
        self.student = User.objects.create_user(
            email="student@api.test.com",
            username="api_student",
            name="API Test Student"
        )
        
        # Create teacher user and profile
        self.teacher_user = User.objects.create_user(
            email="teacher@api.test.com",
            username="api_teacher",
            name="API Test Teacher"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="API test teacher"
        )
        
        # Create student balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("0.00"),
            balance_amount=Decimal("100.00")
        )
        
        # Create purchase transaction
        self.purchase_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(days=30)
        )

    def test_api_session_creation_deducts_hours(self):
        """Test session creation via API deducts hours properly."""
        self.client.force_authenticate(user=self.teacher_user)
        
        session_data = {
            "teacher": self.teacher.id,
            "school": self.school.id,
            "date": date.today().isoformat(),
            "start_time": "14:00:00",
            "end_time": "15:00:00",
            "session_type": SessionType.INDIVIDUAL,
            "grade_level": "10",
            "student_count": 1,
            "students": [self.student.id],
            "status": SessionStatus.SCHEDULED
        }
        
        response = self.client.post('/api/finances/api/sessions/', session_data, format='json')
        
        # This test will initially fail until we implement the API integration
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify hours were deducted
        self.student_balance.refresh_from_db()
        self.assertEqual(self.student_balance.hours_consumed, Decimal("1.00"))
        
        # Verify response includes hour deduction information
        response_data = response.json()
        self.assertIn('hour_deduction', response_data)
        self.assertEqual(response_data['hour_deduction']['hours_deducted'], "1.00")

    def test_api_session_creation_insufficient_balance_returns_error(self):
        """Test API returns proper error for insufficient balance."""
        # Set insufficient balance
        self.student_balance.hours_consumed = Decimal("9.50")  # Only 0.5 hours left
        self.student_balance.save()
        
        self.client.force_authenticate(user=self.teacher_user)
        
        session_data = {
            "teacher": self.teacher.id,
            "school": self.school.id,
            "date": date.today().isoformat(),
            "start_time": "14:00:00",
            "end_time": "15:00:00",  # Needs 1 hour, but only 0.5 available
            "session_type": SessionType.INDIVIDUAL,
            "grade_level": "10",
            "student_count": 1,
            "students": [self.student.id],
            "status": SessionStatus.SCHEDULED
        }
        
        response = self.client.post('/api/finances/api/sessions/', session_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify error message is clear and helpful
        response_data = response.json()
        self.assertIn('insufficient', response_data['error'].lower())
        self.assertIn('balance', response_data['error'].lower())

    def test_api_session_cancellation_endpoint(self):
        """Test API endpoint for session cancellation with hour refund."""
        # First create a session
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        session.students.add(self.student)
        
        self.client.force_authenticate(user=self.teacher_user)
        
        # Call cancellation endpoint
        response = self.client.post(f'/api/finances/api/sessions/{session.id}/cancel/', {
            'reason': 'Teacher unavailable'
        })
        
        # This test will initially fail until we implement the cancellation endpoint
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify session is cancelled
        session.refresh_from_db()
        self.assertEqual(session.status, SessionStatus.CANCELLED)
        
        # Verify hours were refunded
        self.student_balance.refresh_from_db()
        self.assertEqual(self.student_balance.hours_consumed, Decimal("0.00"))
        
        # Verify response includes refund information
        response_data = response.json()
        self.assertIn('refund', response_data)
        self.assertEqual(response_data['refund']['hours_refunded'], "1.00")

    def test_api_balance_check_endpoint(self):
        """Test API endpoint for checking student balance before booking."""
        self.client.force_authenticate(user=self.student)
        
        response = self.client.get('/api/finances/api/student-balance/check-booking/', {
            'duration_hours': '1.5',
            'session_type': SessionType.INDIVIDUAL
        })
        
        # This test will initially fail until we implement the endpoint
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['can_book'])
        self.assertEqual(response_data['hours_required'], 1.5)
        self.assertEqual(response_data['hours_available'], Decimal("10.0"))
        self.assertEqual(response_data['hours_remaining_after'], Decimal("8.5"))

    def test_api_bulk_session_creation_atomic(self):
        """Test bulk session creation is atomic across all students."""
        # Create second student with insufficient balance
        student2 = User.objects.create_user(
            email="student2@api.test.com",
            username="api_student2", 
            name="API Test Student 2"
        )
        student2_balance = StudentAccountBalance.objects.create(
            student=student2,
            hours_purchased=Decimal("1.00"),
            hours_consumed=Decimal("0.50"),  # Only 0.5 hours available
            balance_amount=Decimal("10.00")
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        
        # Try to create session requiring 1 hour for both students
        session_data = {
            "teacher": self.teacher.id,
            "school": self.school.id,
            "date": date.today().isoformat(),
            "start_time": "14:00:00",
            "end_time": "15:00:00",  # 1 hour needed
            "session_type": SessionType.GROUP,
            "grade_level": "10",
            "student_count": 2,
            "students": [self.student.id, student2.id],
            "status": SessionStatus.SCHEDULED
        }
        
        response = self.client.post('/api/finances/api/sessions/', session_data, format='json')
        
        # Should fail due to student2's insufficient balance
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify no hours were deducted from either student (atomic failure)
        self.student_balance.refresh_from_db()
        student2_balance.refresh_from_db()
        self.assertEqual(self.student_balance.hours_consumed, Decimal("0.00"))
        self.assertEqual(student2_balance.hours_consumed, Decimal("0.50"))  # Unchanged