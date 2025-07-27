"""
Test cases for HourConsumption model.

This module follows TDD methodology and tests all functionality of the HourConsumption model
including creation, validation, refund processing, and integration with other models.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, date

from accounts.models import CustomUser, School, TeacherProfile
from finances.models import (
    ClassSession, 
    StudentAccountBalance, 
    PurchaseTransaction,
    HourConsumption,
    SessionStatus,
    SessionType,
    TransactionType,
    TransactionPaymentStatus,
)


class HourConsumptionModelTest(TestCase):
    """Test suite for HourConsumption model functionality."""

    def setUp(self):
        """Set up test data for each test method."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            contact_email="test@school.com"
        )
        
        # Create student user
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            username="student1",
            name="Test Student"
        )
        
        # Create teacher user and profile
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            username="teacher1",
            name="Test Teacher"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Experienced teacher"
        )
        
        # Create student account balance
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
            metadata={"hours_purchased": "10.00"}
        )
        
        # Create class session
        self.class_session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.COMPLETED
        )
        self.class_session.students.add(self.student)

    def test_hour_consumption_creation(self):
        """Test creating a basic HourConsumption record."""
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        self.assertEqual(consumption.student_account, self.student_balance)
        self.assertEqual(consumption.class_session, self.class_session)
        self.assertEqual(consumption.purchase_transaction, self.purchase_transaction)
        self.assertEqual(consumption.hours_consumed, Decimal("1.00"))
        self.assertEqual(consumption.hours_originally_reserved, Decimal("1.00"))
        self.assertFalse(consumption.is_refunded)
        self.assertEqual(consumption.refund_reason, "")
        self.assertIsNotNone(consumption.consumed_at)

    def test_hour_consumption_required_fields(self):
        """Test that all required fields are enforced."""
        # Test missing student_account
        with self.assertRaises(ValidationError):
            consumption = HourConsumption(
                class_session=self.class_session,
                purchase_transaction=self.purchase_transaction,
                hours_consumed=Decimal("1.00"),
                hours_originally_reserved=Decimal("1.00")
            )
            consumption.full_clean()
        
        # Test missing class_session
        with self.assertRaises(ValidationError):
            consumption = HourConsumption(
                student_account=self.student_balance,
                purchase_transaction=self.purchase_transaction,
                hours_consumed=Decimal("1.00"),
                hours_originally_reserved=Decimal("1.00")
            )
            consumption.full_clean()
        
        # Test missing purchase_transaction
        with self.assertRaises(ValidationError):
            consumption = HourConsumption(
                student_account=self.student_balance,
                class_session=self.class_session,
                hours_consumed=Decimal("1.00"),
                hours_originally_reserved=Decimal("1.00")
            )
            consumption.full_clean()

    def test_hours_difference_property(self):
        """Test the hours_difference property calculation."""
        # Test case: early session ending (positive difference = refund due)
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("0.75"),  # Session ended early
            hours_originally_reserved=Decimal("1.00")
        )
        self.assertEqual(consumption.hours_difference, Decimal("0.25"))
        
        # Test case: session ran longer (negative difference = extra time)
        # Create a new session for this test case
        overtime_session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(16, 0),  # Different time
            end_time=time(17, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.COMPLETED
        )
        overtime_session.students.add(self.student)
        
        consumption_overtime = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=overtime_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("1.25"),  # Session ran longer
            hours_originally_reserved=Decimal("1.00")
        )
        self.assertEqual(consumption_overtime.hours_difference, Decimal("-0.25"))
        
        # Test case: exact match (zero difference)
        # Create another new session for this test case
        exact_session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(18, 0),  # Different time
            end_time=time(19, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.COMPLETED
        )
        exact_session.students.add(self.student)
        
        consumption_exact = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=exact_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        self.assertEqual(consumption_exact.hours_difference, Decimal("0.00"))

    def test_process_refund_method(self):
        """Test the process_refund method functionality."""
        # Create consumption record with early ending (refund due)
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("0.75"),  # 15 minutes early
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Store initial balance
        initial_hours_consumed = self.student_balance.hours_consumed
        
        # Process refund
        refund_hours = consumption.process_refund("Session ended early")
        
        # Refresh from database
        consumption.refresh_from_db()
        self.student_balance.refresh_from_db()
        
        # Verify refund was processed
        self.assertTrue(consumption.is_refunded)
        self.assertEqual(consumption.refund_reason, "Session ended early")
        self.assertEqual(refund_hours, Decimal("0.25"))
        
        # Verify student balance was updated
        expected_hours_consumed = initial_hours_consumed - Decimal("0.25")
        self.assertEqual(self.student_balance.hours_consumed, expected_hours_consumed)

    def test_process_refund_no_refund_due(self):
        """Test process_refund when no refund is due."""
        # Create consumption record with exact hours
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Process refund when none is due
        refund_hours = consumption.process_refund("Manual refund request")
        
        # Refresh from database
        consumption.refresh_from_db()
        
        # Verify no refund was processed
        self.assertFalse(consumption.is_refunded)
        self.assertEqual(consumption.refund_reason, "")
        self.assertEqual(refund_hours, Decimal("0.00"))

    def test_process_refund_already_refunded(self):
        """Test that processing refund twice raises an error."""
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("0.75"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Process first refund
        consumption.process_refund("Session ended early")
        
        # Attempt second refund should raise error
        with self.assertRaises(ValueError) as context:
            consumption.process_refund("Another refund attempt")
        
        self.assertIn("already been refunded", str(context.exception))

    def test_one_to_one_relationship_with_class_session(self):
        """Test that HourConsumption has a one-to-one relationship with ClassSession."""
        # Create first consumption record
        consumption1 = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Attempting to create second consumption for same session should fail
        with self.assertRaises(ValidationError):
            consumption2 = HourConsumption(
                student_account=self.student_balance,
                class_session=self.class_session,  # Same session
                purchase_transaction=self.purchase_transaction,
                hours_consumed=Decimal("0.50"),
                hours_originally_reserved=Decimal("1.00")
            )
            consumption2.full_clean()

    def test_str_representation(self):
        """Test the string representation of HourConsumption."""
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        expected_str = f"Hour consumption: {self.student.name} - 1.00h consumed for session on {self.class_session.date}"
        self.assertEqual(str(consumption), expected_str)

    def test_negative_hours_validation(self):
        """Test validation for negative hours values."""
        # Test negative hours_consumed
        with self.assertRaises(ValidationError):
            consumption = HourConsumption(
                student_account=self.student_balance,
                class_session=self.class_session,
                purchase_transaction=self.purchase_transaction,
                hours_consumed=Decimal("-1.00"),  # Negative value
                hours_originally_reserved=Decimal("1.00")
            )
            consumption.full_clean()
        
        # Test negative hours_originally_reserved
        with self.assertRaises(ValidationError):
            consumption = HourConsumption(
                student_account=self.student_balance,
                class_session=self.class_session,
                purchase_transaction=self.purchase_transaction,
                hours_consumed=Decimal("1.00"),
                hours_originally_reserved=Decimal("-1.00")  # Negative value
            )
            consumption.full_clean()

    def test_integration_with_student_account_balance_update(self):
        """Test that creating consumption updates student account balance."""
        initial_hours_consumed = self.student_balance.hours_consumed
        
        # Create consumption record
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("2.00"),
            hours_originally_reserved=Decimal("2.00")
        )
        
        # Verify that student balance was updated
        self.student_balance.refresh_from_db()
        expected_hours_consumed = initial_hours_consumed + Decimal("2.00")
        self.assertEqual(self.student_balance.hours_consumed, expected_hours_consumed)

    def test_audit_trail_functionality(self):
        """Test that the audit trail is properly maintained."""
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Verify audit fields are populated
        self.assertIsNotNone(consumption.consumed_at)
        self.assertIsNotNone(consumption.created_at)
        self.assertIsNotNone(consumption.updated_at)
        
        # Verify consumed_at is close to creation time
        time_diff = abs((consumption.consumed_at - consumption.created_at).total_seconds())
        self.assertLess(time_diff, 1.0)  # Within 1 second

    def test_meta_options(self):
        """Test model meta options."""
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.purchase_transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Test verbose names
        self.assertEqual(consumption._meta.verbose_name, "Hour Consumption")
        self.assertEqual(consumption._meta.verbose_name_plural, "Hour Consumptions")
        
        # Test ordering
        self.assertEqual(consumption._meta.ordering, ["-consumed_at"])


class HourConsumptionIntegrationTest(TestCase):
    """Integration tests for HourConsumption with other models."""

    def setUp(self):
        """Set up test data for integration tests."""
        # Create school
        self.school = School.objects.create(
            name="Integration Test School",
            contact_email="integration@test.com"
        )
        
        # Create student
        self.student = CustomUser.objects.create_user(
            email="student@integration.com",
            username="student_int",
            name="Integration Student"
        )
        
        # Create teacher
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@integration.com",
            username="teacher_int",
            name="Integration Teacher"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Integration teacher"
        )
        
        # Create student balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("20.00"),
            hours_consumed=Decimal("0.00"),
            balance_amount=Decimal("200.00")
        )

    def test_multiple_consumptions_for_different_sessions(self):
        """Test creating multiple consumption records for different sessions."""
        # Create multiple purchase transactions
        transaction1 = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        transaction2 = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        # Create multiple class sessions
        session1 = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            status=SessionStatus.COMPLETED
        )
        
        session2 = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(16, 0),
            end_time=time(17, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            status=SessionStatus.COMPLETED
        )
        
        # Create consumption records
        consumption1 = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=session1,
            purchase_transaction=transaction1,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        consumption2 = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=session2,
            purchase_transaction=transaction2,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Verify both consumptions exist
        self.assertEqual(HourConsumption.objects.count(), 2)
        
        # Verify student balance reflects both consumptions
        self.student_balance.refresh_from_db()
        self.assertEqual(self.student_balance.hours_consumed, Decimal("2.00"))

    def test_partial_refund_scenario(self):
        """Test partial refund scenario with early session ending."""
        # Create transaction and session
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 30),  # 1.5 hour session
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            status=SessionStatus.COMPLETED
        )
        
        # Create consumption with early ending
        consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=session,
            purchase_transaction=transaction,
            hours_consumed=Decimal("1.00"),  # Ended 30 minutes early
            hours_originally_reserved=Decimal("1.50")
        )
        
        # Store initial consumed hours
        initial_consumed = self.student_balance.hours_consumed
        
        # Process partial refund
        refund_amount = consumption.process_refund("Student left early")
        
        # Verify refund
        self.assertEqual(refund_amount, Decimal("0.50"))
        self.assertTrue(consumption.is_refunded)
        
        # Verify balance adjustment
        self.student_balance.refresh_from_db()
        expected_consumed = initial_consumed - Decimal("0.50")
        self.assertEqual(self.student_balance.hours_consumed, expected_consumed)