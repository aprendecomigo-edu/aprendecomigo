"""
Comprehensive unit tests for finances app models.

This test suite validates all models in the finances app including:
- Field validation and constraints
- Model methods and properties
- Business logic and relationships
- PCI compliance requirements
- Multi-tenant data isolation
- Financial calculations and currency handling

Tests follow the pattern: test_<component>_<scenario>_<expected_outcome>
"""

from datetime import date, time, timedelta, datetime
from decimal import Decimal
import json

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import IntegrityError
from django.utils import timezone
from unittest.mock import patch, MagicMock

from django.test import TestCase

from ..models import (
    # Enums and Choices
    CompensationRuleType,
    SessionType,
    SessionStatus,
    PaymentStatus,
    TrialCostAbsorption,
    PaymentFrequency,
    WebhookEventStatus,
    PlanType,
    TransactionType,
    TransactionPaymentStatus,
    PurchaseRequestType,
    PurchaseApprovalStatus,
    DisputeStatus,
    DisputeReason,
    AdminActionType,
    FraudAlertSeverity,
    FraudAlertStatus,
    
    # Models
    SchoolBillingSettings,
    TeacherCompensationRule,
    ClassSession,
    TeacherPaymentEntry,
    StudentAccountBalance,
    PurchaseTransaction,
    PricingPlan,
    HourConsumption,
    Receipt,
    StoredPaymentMethod,
    FamilyBudgetControl,
    PurchaseApprovalRequest,
    WebhookEventLog,
    PaymentDispute,
    AdminAction,
    FraudAlert,
)

User = get_user_model()


class SchoolBillingSettingsTestCase(TestCase):
    """Test cases for SchoolBillingSettings model."""

    def setUp(self):
        """Set up test data."""
        School = apps.get_model('accounts', 'School')
        self.school = School.objects.create(
            name="Test School",
            description="A test school for billing settings"
        )

    def test_school_billing_settings_creation_with_defaults(self):
        """Test creating SchoolBillingSettings with default values."""
        settings = SchoolBillingSettings.objects.create(school=self.school)
        
        self.assertEqual(settings.school, self.school)
        self.assertEqual(settings.trial_cost_absorption, TrialCostAbsorption.SCHOOL)
        self.assertEqual(settings.teacher_payment_frequency, PaymentFrequency.MONTHLY)
        self.assertEqual(settings.payment_day_of_month, 1)
        self.assertIsNotNone(settings.created_at)
        self.assertIsNotNone(settings.updated_at)

    def test_school_billing_settings_creation_with_custom_values(self):
        """Test creating SchoolBillingSettings with custom values."""
        settings = SchoolBillingSettings.objects.create(
            school=self.school,
            trial_cost_absorption=TrialCostAbsorption.TEACHER,
            teacher_payment_frequency=PaymentFrequency.WEEKLY,
            payment_day_of_month=15
        )
        
        self.assertEqual(settings.trial_cost_absorption, TrialCostAbsorption.TEACHER)
        self.assertEqual(settings.teacher_payment_frequency, PaymentFrequency.WEEKLY)
        self.assertEqual(settings.payment_day_of_month, 15)

    def test_school_billing_settings_payment_day_validation_valid_boundary_values(self):
        """Test payment day validation with valid boundary values (1 and 28)."""
        # Test minimum valid value
        settings = SchoolBillingSettings(school=self.school, payment_day_of_month=1)
        settings.full_clean()  # Should not raise
        
        # Test maximum valid value
        settings.payment_day_of_month = 28
        settings.full_clean()  # Should not raise

    def test_school_billing_settings_payment_day_validation_invalid_values(self):
        """Test payment day validation with invalid values."""
        settings = SchoolBillingSettings(school=self.school)
        
        # Test invalid values
        invalid_values = [0, 29, 30, 31, -1, 32]
        for invalid_day in invalid_values:
            with self.subTest(payment_day=invalid_day):
                settings.payment_day_of_month = invalid_day
                with self.assertRaises(ValidationError) as cm:
                    settings.full_clean()
                self.assertIn("Payment day must be between 1 and 28", str(cm.exception))

    def test_school_billing_settings_string_representation(self):
        """Test SchoolBillingSettings __str__ method."""
        settings = SchoolBillingSettings.objects.create(school=self.school)
        expected_str = f"Billing settings for {self.school.name}"
        self.assertEqual(str(settings), expected_str)

    def test_school_billing_settings_one_to_one_relationship(self):
        """Test that each school can only have one billing settings instance."""
        # Create first settings
        SchoolBillingSettings.objects.create(school=self.school)
        
        # Attempting to create a second should raise IntegrityError
        with self.assertRaises(IntegrityError):
            SchoolBillingSettings.objects.create(school=self.school)

    def test_school_billing_settings_cascade_delete(self):
        """Test that billing settings are deleted when school is deleted."""
        settings = SchoolBillingSettings.objects.create(school=self.school)
        settings_id = settings.id
        
        # Delete the school
        self.school.delete()
        
        # Verify settings are also deleted
        with self.assertRaises(SchoolBillingSettings.DoesNotExist):
            SchoolBillingSettings.objects.get(id=settings_id)


class TeacherCompensationRuleTestCase(TestCase):
    """Test cases for TeacherCompensationRule model."""

    def setUp(self):
        """Set up test data."""
        School = apps.get_model('accounts', 'School')
        TeacherProfile = apps.get_model('accounts', 'TeacherProfile')
        
        self.school = School.objects.create(name="Test School", description="Test")
        self.user = User.objects.create_user(
            email="teacher@test.com",
            name="Test Teacher",
            password="testpass123"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.user,
            bio="Experienced teacher"
        )

    def test_teacher_compensation_rule_grade_specific_creation(self):
        """Test creating a grade-specific compensation rule."""
        rule = TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="10",
            rate_per_hour=Decimal("20.00"),
            effective_from=date.today()
        )
        
        self.assertEqual(rule.teacher, self.teacher)
        self.assertEqual(rule.school, self.school)
        self.assertEqual(rule.rule_type, CompensationRuleType.GRADE_SPECIFIC)
        self.assertEqual(rule.grade_level, "10")
        self.assertEqual(rule.rate_per_hour, Decimal("20.00"))
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.effective_from, date.today())

    def test_teacher_compensation_rule_fixed_salary_creation(self):
        """Test creating a fixed salary compensation rule."""
        rule = TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.FIXED_SALARY,
            fixed_amount=Decimal("2500.00"),
            effective_from=date.today()
        )
        
        self.assertEqual(rule.rule_type, CompensationRuleType.FIXED_SALARY)
        self.assertEqual(rule.fixed_amount, Decimal("2500.00"))
        self.assertIsNone(rule.rate_per_hour)
        self.assertIsNone(rule.grade_level)

    def test_teacher_compensation_rule_validation_grade_specific_missing_grade(self):
        """Test validation error when grade-specific rule is missing grade level."""
        rule = TeacherCompensationRule(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            rate_per_hour=Decimal("15.00"),
            effective_from=date.today()
            # Missing grade_level
        )
        
        with self.assertRaises(ValidationError) as cm:
            rule.full_clean()
        self.assertIn("Grade level is required for grade-specific rules", str(cm.exception))

    def test_teacher_compensation_rule_validation_grade_specific_missing_rate(self):
        """Test validation error when grade-specific rule is missing hourly rate."""
        rule = TeacherCompensationRule(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="10",
            effective_from=date.today()
            # Missing rate_per_hour
        )
        
        with self.assertRaises(ValidationError) as cm:
            rule.full_clean()
        self.assertIn("Rate per hour is required for grade-specific rules", str(cm.exception))

    def test_teacher_compensation_rule_validation_fixed_salary_missing_amount(self):
        """Test validation error when fixed salary rule is missing fixed amount."""
        rule = TeacherCompensationRule(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.FIXED_SALARY,
            effective_from=date.today()
            # Missing fixed_amount
        )
        
        with self.assertRaises(ValidationError) as cm:
            rule.full_clean()
        self.assertIn("Fixed amount is required for fixed salary rules", str(cm.exception))

    def test_teacher_compensation_rule_unique_constraint_enforcement(self):
        """Test that unique constraint prevents duplicate active rules."""
        # Create first rule
        TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="10",
            rate_per_hour=Decimal("15.00"),
            effective_from=date.today(),
            is_active=True
        )
        
        # Attempt to create duplicate active rule should raise IntegrityError
        with self.assertRaises(IntegrityError):
            TeacherCompensationRule.objects.create(
                teacher=self.teacher,
                school=self.school,
                rule_type=CompensationRuleType.GRADE_SPECIFIC,
                grade_level="10",
                rate_per_hour=Decimal("20.00"),
                effective_from=date.today(),
                is_active=True
            )

    def test_teacher_compensation_rule_string_representation(self):
        """Test TeacherCompensationRule __str__ method."""
        rule = TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="10",
            rate_per_hour=Decimal("20.00"),
            effective_from=date.today()
        )
        
        expected_str = f"{self.teacher.user.name} - Grade Specific Rate (Grade 10) at {self.school.name}"
        self.assertEqual(str(rule), expected_str)

    def test_teacher_compensation_rule_conditions_json_field(self):
        """Test that conditions JSONField works correctly."""
        conditions = {
            "min_students": 3,
            "max_students": 8,
            "bonus_multiplier": 1.2
        }
        
        rule = TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GROUP_CLASS,
            rate_per_hour=Decimal("12.00"),
            conditions=conditions,
            effective_from=date.today()
        )
        
        # Refresh from database and verify JSON integrity
        rule.refresh_from_db()
        self.assertEqual(rule.conditions["min_students"], 3)
        self.assertEqual(rule.conditions["max_students"], 8)
        self.assertEqual(rule.conditions["bonus_multiplier"], 1.2)


class ClassSessionTestCase(TestCase):
    """Test cases for ClassSession model."""

    def setUp(self):
        """Set up test data."""
        School = apps.get_model('accounts', 'School')
        TeacherProfile = apps.get_model('accounts', 'TeacherProfile')
        
        self.school = School.objects.create(name="Test School", description="Test")
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com",
            name="Test Teacher",
            password="testpass123"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Experienced teacher"
        )
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )

    def test_class_session_creation_with_required_fields(self):
        """Test creating ClassSession with required fields only."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10"
        )
        
        self.assertEqual(session.teacher, self.teacher)
        self.assertEqual(session.school, self.school)
        self.assertEqual(session.session_type, SessionType.INDIVIDUAL)
        self.assertEqual(session.grade_level, "10")
        self.assertEqual(session.student_count, 1)  # Default value
        self.assertEqual(session.status, SessionStatus.SCHEDULED)  # Default value
        self.assertFalse(session.is_trial)  # Default value
        self.assertFalse(session.is_makeup)  # Default value

    def test_class_session_duration_hours_property_normal_session(self):
        """Test duration_hours property calculation for normal session."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 30),  # 1.5 hours
            session_type=SessionType.INDIVIDUAL,
            grade_level="10"
        )
        
        self.assertEqual(session.duration_hours, Decimal("1.50"))

    def test_class_session_duration_hours_property_cross_midnight(self):
        """Test duration_hours property for sessions crossing midnight."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(23, 30),
            end_time=time(1, 0),  # Crosses midnight, should be 1.5 hours
            session_type=SessionType.INDIVIDUAL,
            grade_level="10"
        )
        
        self.assertEqual(session.duration_hours, Decimal("1.50"))

    def test_class_session_validation_end_before_start_time(self):
        """Test validation error when end time is before start time."""
        session = ClassSession(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(15, 0),
            end_time=time(14, 0),  # End before start
            session_type=SessionType.INDIVIDUAL,
            grade_level="10"
        )
        
        with self.assertRaises(ValidationError) as cm:
            session.full_clean()
        self.assertIn("End time must be after start time", str(cm.exception))

    def test_class_session_validation_individual_session_multiple_students(self):
        """Test validation error when individual session has multiple students."""
        session = ClassSession(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=3  # Invalid for individual session
        )
        
        with self.assertRaises(ValidationError) as cm:
            session.full_clean()
        self.assertIn("Individual sessions can only have 1 student", str(cm.exception))

    def test_class_session_status_change_timestamps(self):
        """Test that status changes update appropriate timestamps."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            status=SessionStatus.SCHEDULED
        )
        
        # Initially should have booking_confirmed_at set since status is SCHEDULED
        self.assertIsNotNone(session.booking_confirmed_at)
        self.assertIsNone(session.cancelled_at)

    def test_class_session_string_representation(self):
        """Test ClassSession __str__ method."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date(2024, 3, 15),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10"
        )
        
        expected_str = f"{self.teacher.user.name} - Individual Session Grade 10 on 2024-03-15"
        self.assertEqual(str(session), expected_str)

    def test_class_session_students_many_to_many_relationship(self):
        """Test that students can be added to session via many-to-many relationship."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.GROUP,
            grade_level="mixed",
            student_count=2
        )
        
        # Add students to session
        session.students.add(self.student)
        
        # Verify relationship
        self.assertIn(self.student, session.students.all())
        self.assertIn(session, self.student.attended_sessions.all())

    @patch('finances.services.hour_deduction_service.HourDeductionService.validate_and_deduct_hours_for_session')
    def test_class_session_process_hour_deduction_non_trial(self, mock_deduct):
        """Test hour deduction processing for non-trial sessions."""
        mock_deduct.return_value = []
        
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            is_trial=False,
            status=SessionStatus.SCHEDULED
        )
        
        result = session.process_hour_deduction()
        
        # Should call the service for non-trial sessions
        mock_deduct.assert_called_once_with(session)
        self.assertEqual(result, [])

    def test_class_session_process_hour_deduction_trial_session(self):
        """Test hour deduction processing for trial sessions (should not deduct)."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            is_trial=True,
            status=SessionStatus.SCHEDULED
        )
        
        result = session.process_hour_deduction()
        
        # Should return empty list for trial sessions
        self.assertEqual(result, [])


class TeacherPaymentEntryTestCase(TestCase):
    """Test cases for TeacherPaymentEntry model."""

    def setUp(self):
        """Set up test data."""
        School = apps.get_model('accounts', 'School')
        TeacherProfile = apps.get_model('accounts', 'TeacherProfile')
        
        self.school = School.objects.create(name="Test School", description="Test")
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com",
            name="Test Teacher",
            password="testpass123"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Experienced teacher"
        )
        self.session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10"
        )
        self.compensation_rule = TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="10",
            rate_per_hour=Decimal("20.00"),
            effective_from=date.today()
        )

    def test_teacher_payment_entry_creation_with_required_fields(self):
        """Test creating TeacherPaymentEntry with required fields."""
        payment_entry = TeacherPaymentEntry.objects.create(
            session=self.session,
            teacher=self.teacher,
            school=self.school,
            billing_period="2024-03",
            hours_taught=Decimal("1.00"),
            rate_applied=Decimal("20.00"),
            amount_earned=Decimal("20.00")
        )
        
        self.assertEqual(payment_entry.session, self.session)
        self.assertEqual(payment_entry.teacher, self.teacher)
        self.assertEqual(payment_entry.school, self.school)
        self.assertEqual(payment_entry.billing_period, "2024-03")
        self.assertEqual(payment_entry.hours_taught, Decimal("1.00"))
        self.assertEqual(payment_entry.rate_applied, Decimal("20.00"))
        self.assertEqual(payment_entry.amount_earned, Decimal("20.00"))
        self.assertEqual(payment_entry.payment_status, PaymentStatus.PENDING)

    def test_teacher_payment_entry_with_compensation_rule(self):
        """Test creating TeacherPaymentEntry with compensation rule reference."""
        payment_entry = TeacherPaymentEntry.objects.create(
            session=self.session,
            teacher=self.teacher,
            school=self.school,
            billing_period="2024-03",
            hours_taught=Decimal("1.00"),
            rate_applied=Decimal("20.00"),
            amount_earned=Decimal("20.00"),
            compensation_rule=self.compensation_rule,
            calculation_notes="Applied grade 10 rate"
        )
        
        self.assertEqual(payment_entry.compensation_rule, self.compensation_rule)
        self.assertEqual(payment_entry.calculation_notes, "Applied grade 10 rate")

    def test_teacher_payment_entry_string_representation(self):
        """Test TeacherPaymentEntry __str__ method."""
        payment_entry = TeacherPaymentEntry.objects.create(
            session=self.session,
            teacher=self.teacher,
            school=self.school,
            billing_period="2024-03",
            hours_taught=Decimal("1.00"),
            rate_applied=Decimal("20.00"),
            amount_earned=Decimal("20.00")
        )
        
        expected_str = f"{self.teacher.user.name} - €20.00 for {self.session.date} session"
        self.assertEqual(str(payment_entry), expected_str)

    def test_teacher_payment_entry_one_to_one_with_session(self):
        """Test that each session can only have one payment entry."""
        # Create first payment entry
        TeacherPaymentEntry.objects.create(
            session=self.session,
            teacher=self.teacher,
            school=self.school,
            billing_period="2024-03",
            hours_taught=Decimal("1.00"),
            rate_applied=Decimal("20.00"),
            amount_earned=Decimal("20.00")
        )
        
        # Attempting to create a second should raise IntegrityError
        with self.assertRaises(IntegrityError):
            TeacherPaymentEntry.objects.create(
                session=self.session,
                teacher=self.teacher,
                school=self.school,
                billing_period="2024-03",
                hours_taught=Decimal("1.00"),
                rate_applied=Decimal("20.00"),
                amount_earned=Decimal("20.00")
            )


class StudentAccountBalanceTestCase(TestCase):
    """Test cases for StudentAccountBalance model."""

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )

    def test_student_account_balance_creation_with_defaults(self):
        """Test creating StudentAccountBalance with default values."""
        balance = StudentAccountBalance.objects.create(student=self.student)
        
        self.assertEqual(balance.student, self.student)
        self.assertEqual(balance.hours_purchased, Decimal("0.00"))
        self.assertEqual(balance.hours_consumed, Decimal("0.00"))
        self.assertEqual(balance.balance_amount, Decimal("0.00"))
        self.assertIsNotNone(balance.created_at)
        self.assertIsNotNone(balance.updated_at)

    def test_student_account_balance_remaining_hours_property_positive(self):
        """Test remaining_hours property with positive balance."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("3.50")
        )
        
        self.assertEqual(balance.remaining_hours, Decimal("6.50"))

    def test_student_account_balance_remaining_hours_property_zero(self):
        """Test remaining_hours property when exactly zero."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("5.00"),
            hours_consumed=Decimal("5.00")
        )
        
        self.assertEqual(balance.remaining_hours, Decimal("0.00"))

    def test_student_account_balance_remaining_hours_property_negative_overdraft(self):
        """Test remaining_hours property with negative balance (overdraft)."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("5.00"),
            hours_consumed=Decimal("7.50"),
            balance_amount=Decimal("-25.00")
        )
        
        self.assertEqual(balance.remaining_hours, Decimal("-2.50"))

    def test_student_account_balance_string_representation(self):
        """Test StudentAccountBalance __str__ method."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("3.50"),
            balance_amount=Decimal("65.00")
        )
        
        expected_str = f"Account Balance for {self.student.name}: €65.00 (6.50h remaining)"
        self.assertEqual(str(balance), expected_str)

    def test_student_account_balance_one_to_one_relationship(self):
        """Test that each student can only have one account balance."""
        # Create first balance
        StudentAccountBalance.objects.create(student=self.student)
        
        # Attempting to create a second should raise IntegrityError
        with self.assertRaises(IntegrityError):
            StudentAccountBalance.objects.create(student=self.student)

    def test_student_account_balance_cascade_delete_with_student(self):
        """Test that balance is deleted when student is deleted."""
        balance = StudentAccountBalance.objects.create(student=self.student)
        balance_id = balance.id
        
        # Delete the student
        self.student.delete()
        
        # Verify balance is also deleted
        with self.assertRaises(StudentAccountBalance.DoesNotExist):
            StudentAccountBalance.objects.get(id=balance_id)


class PurchaseTransactionTestCase(TestCase):
    """Test cases for PurchaseTransaction model."""

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )

    def test_purchase_transaction_creation_package_type(self):
        """Test creating a package transaction."""
        expires_at = timezone.now() + timedelta(days=30)
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            expires_at=expires_at
        )
        
        self.assertEqual(transaction.student, self.student)
        self.assertEqual(transaction.transaction_type, TransactionType.PACKAGE)
        self.assertEqual(transaction.amount, Decimal("100.00"))
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.PENDING)
        self.assertEqual(transaction.expires_at, expires_at)
        self.assertIsNotNone(transaction.created_at)

    def test_purchase_transaction_creation_subscription_type(self):
        """Test creating a subscription transaction."""
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("50.00")
        )
        
        self.assertEqual(transaction.transaction_type, TransactionType.SUBSCRIPTION)
        self.assertIsNone(transaction.expires_at)  # Subscriptions don't expire

    def test_purchase_transaction_is_expired_property_non_expired(self):
        """Test is_expired property for non-expired package."""
        future_date = timezone.now() + timedelta(days=30)
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            expires_at=future_date
        )
        
        self.assertFalse(transaction.is_expired)

    def test_purchase_transaction_is_expired_property_expired(self):
        """Test is_expired property for expired package."""
        past_date = timezone.now() - timedelta(days=1)
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            expires_at=past_date
        )
        
        self.assertTrue(transaction.is_expired)

    def test_purchase_transaction_is_expired_property_subscription(self):
        """Test is_expired property for subscription (should always be False)."""
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("50.00")
        )
        
        self.assertFalse(transaction.is_expired)

    def test_purchase_transaction_mark_completed_method(self):
        """Test mark_completed method functionality."""
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00")
        )
        
        # Initially pending
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.PENDING)
        
        # Mark as completed
        transaction.mark_completed()
        
        # Refresh and verify
        transaction.refresh_from_db()
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.COMPLETED)

    def test_purchase_transaction_validation_negative_amount(self):
        """Test validation error for negative transaction amount."""
        transaction = PurchaseTransaction(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("-10.00")
        )
        
        with self.assertRaises(ValidationError) as cm:
            transaction.full_clean()
        self.assertIn("Transaction amount cannot be negative", str(cm.exception))

    def test_purchase_transaction_validation_subscription_with_expiration(self):
        """Test validation error when subscription has expiration date."""
        expires_at = timezone.now() + timedelta(days=30)
        transaction = PurchaseTransaction(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("50.00"),
            expires_at=expires_at
        )
        
        with self.assertRaises(ValidationError) as cm:
            transaction.full_clean()
        self.assertIn("Subscription transactions should not have an expiration date", str(cm.exception))

    def test_purchase_transaction_string_representation(self):
        """Test PurchaseTransaction __str__ method."""
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00")
        )
        
        expected_str = f"Transaction {transaction.id}: {self.student.name} - €100.00 (PACKAGE - PENDING)"
        self.assertEqual(str(transaction), expected_str)

    def test_purchase_transaction_metadata_json_field(self):
        """Test metadata JSONField functionality."""
        metadata = {
            "package_name": "Premium Package",
            "hours": 20,
            "discount_applied": True
        }
        
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("90.00"),
            metadata=metadata
        )
        
        # Refresh and verify JSON integrity
        transaction.refresh_from_db()
        self.assertEqual(transaction.metadata["package_name"], "Premium Package")
        self.assertEqual(transaction.metadata["hours"], 20)
        self.assertTrue(transaction.metadata["discount_applied"])


class PricingPlanTestCase(TestCase):
    """Test cases for PricingPlan model."""

    def test_pricing_plan_creation_package_type(self):
        """Test creating a package-type pricing plan."""
        plan = PricingPlan.objects.create(
            name="Basic Package",
            description="10 hours of tutoring valid for 30 days",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1
        )
        
        self.assertEqual(plan.name, "Basic Package")
        self.assertEqual(plan.plan_type, PlanType.PACKAGE)
        self.assertEqual(plan.hours_included, Decimal("10.00"))
        self.assertEqual(plan.price_eur, Decimal("100.00"))
        self.assertEqual(plan.validity_days, 30)
        self.assertTrue(plan.is_active)
        self.assertFalse(plan.is_featured)

    def test_pricing_plan_creation_subscription_type(self):
        """Test creating a subscription-type pricing plan."""
        plan = PricingPlan.objects.create(
            name="Monthly Subscription",
            description="Unlimited tutoring sessions per month",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("40.00"),
            price_eur=Decimal("200.00"),
            display_order=1
        )
        
        self.assertEqual(plan.plan_type, PlanType.SUBSCRIPTION)
        self.assertIsNone(plan.validity_days)  # Subscriptions don't have validity

    def test_pricing_plan_price_per_hour_property(self):
        """Test price_per_hour property calculation."""
        plan = PricingPlan.objects.create(
            name="Test Package",
            description="Test",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1
        )
        
        self.assertEqual(plan.price_per_hour, Decimal("10.00"))  # 100/10

    def test_pricing_plan_price_per_hour_property_zero_hours(self):
        """Test price_per_hour property when hours_included is zero."""
        plan = PricingPlan.objects.create(
            name="Zero Hours Plan",
            description="Test",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("0.01"),  # Minimum allowed
            price_eur=Decimal("1.00"),
            validity_days=30,
            display_order=1
        )
        
        # Should calculate normally, not None
        self.assertEqual(plan.price_per_hour, Decimal("100.00"))  # 1.00/0.01

    def test_pricing_plan_validation_package_missing_validity_days(self):
        """Test validation error when package plan is missing validity_days."""
        plan = PricingPlan(
            name="Invalid Package",
            description="Test",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("100.00"),
            display_order=1
            # Missing validity_days
        )
        
        with self.assertRaises(ValidationError) as cm:
            plan.full_clean()
        self.assertIn("Package plans must have validity_days specified", str(cm.exception))

    def test_pricing_plan_validation_subscription_with_validity_days(self):
        """Test validation error when subscription plan has validity_days."""
        plan = PricingPlan(
            name="Invalid Subscription",
            description="Test",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("40.00"),
            price_eur=Decimal("200.00"),
            validity_days=30,  # Should not have this
            display_order=1
        )
        
        with self.assertRaises(ValidationError) as cm:
            plan.full_clean()
        self.assertIn("Subscription plans should not have validity_days", str(cm.exception))

    def test_pricing_plan_validation_zero_price(self):
        """Test validation error for zero price."""
        plan = PricingPlan(
            name="Free Plan",
            description="Test",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("0.00"),
            validity_days=30,
            display_order=1
        )
        
        with self.assertRaises(ValidationError) as cm:
            plan.full_clean()
        self.assertIn("Price must be greater than 0", str(cm.exception))

    def test_pricing_plan_validation_zero_hours(self):
        """Test validation error for zero hours."""
        plan = PricingPlan(
            name="No Hours Plan",
            description="Test",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("0.00"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1
        )
        
        with self.assertRaises(ValidationError) as cm:
            plan.full_clean()
        self.assertIn("Hours included must be greater than 0", str(cm.exception))

    def test_pricing_plan_string_representation(self):
        """Test PricingPlan __str__ method."""
        plan = PricingPlan.objects.create(
            name="Test Package",
            description="Test",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1
        )
        
        expected_str = "Test Package - €100.00 (10.00h, 30 days)"
        self.assertEqual(str(plan), expected_str)

    def test_pricing_plan_string_representation_subscription(self):
        """Test PricingPlan __str__ method for subscription."""
        plan = PricingPlan.objects.create(
            name="Monthly Plan",
            description="Test",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("40.00"),
            price_eur=Decimal("200.00"),
            display_order=1
        )
        
        expected_str = "Monthly Plan - €200.00 (40.00h, subscription)"
        self.assertEqual(str(plan), expected_str)

    def test_pricing_plan_managers(self):
        """Test custom managers for PricingPlan."""
        # Create active and inactive plans
        active_plan = PricingPlan.objects.create(
            name="Active Plan",
            description="Test",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_active=True
        )
        
        inactive_plan = PricingPlan.objects.create(
            name="Inactive Plan",
            description="Test",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("5.00"),
            price_eur=Decimal("50.00"),
            validity_days=15,
            display_order=2,
            is_active=False
        )
        
        # Test default manager returns all
        all_plans = PricingPlan.objects.all()
        self.assertEqual(all_plans.count(), 2)
        
        # Test active manager returns only active plans
        active_plans = PricingPlan.active.all()
        self.assertEqual(active_plans.count(), 1)
        self.assertEqual(active_plans.first(), active_plan)


class HourConsumptionTestCase(TestCase):
    """Test cases for HourConsumption model."""

    def setUp(self):
        """Set up test data."""
        School = apps.get_model('accounts', 'School')
        TeacherProfile = apps.get_model('accounts', 'TeacherProfile')
        
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )
        self.account_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("10.00"),
            balance_amount=Decimal("100.00")
        )
        
        self.school = School.objects.create(name="Test School", description="Test")
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com",
            name="Test Teacher"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Test teacher"
        )
        
        self.session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10"
        )
        self.session.students.add(self.student)
        
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

    def test_hour_consumption_creation(self):
        """Test creating HourConsumption record."""
        consumption = HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("0.80"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        self.assertEqual(consumption.student_account, self.account_balance)
        self.assertEqual(consumption.class_session, self.session)
        self.assertEqual(consumption.purchase_transaction, self.transaction)
        self.assertEqual(consumption.hours_consumed, Decimal("0.80"))
        self.assertEqual(consumption.hours_originally_reserved, Decimal("1.00"))
        self.assertFalse(consumption.is_refunded)
        self.assertEqual(consumption.refund_reason, "")

    def test_hour_consumption_hours_difference_property_refund_due(self):
        """Test hours_difference property when refund is due (early ending)."""
        consumption = HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("0.50"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Difference should be positive (refund due)
        self.assertEqual(consumption.hours_difference, Decimal("0.50"))

    def test_hour_consumption_hours_difference_property_overtime(self):
        """Test hours_difference property when session went overtime."""
        consumption = HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("1.25"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Difference should be negative (overtime)
        self.assertEqual(consumption.hours_difference, Decimal("-0.25"))

    def test_hour_consumption_hours_difference_property_exact_match(self):
        """Test hours_difference property when exactly as reserved."""
        consumption = HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Difference should be zero
        self.assertEqual(consumption.hours_difference, Decimal("0.00"))

    def test_hour_consumption_process_refund_early_ending(self):
        """Test process_refund method for early session ending."""
        initial_consumed = self.account_balance.hours_consumed
        
        consumption = HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("0.75"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        refund_hours = consumption.process_refund("Session ended early due to technical issues")
        
        # Should refund 0.25 hours
        self.assertEqual(refund_hours, Decimal("0.25"))
        
        # Consumption should be marked as refunded
        consumption.refresh_from_db()
        self.assertTrue(consumption.is_refunded)
        self.assertEqual(consumption.refund_reason, "Session ended early due to technical issues")
        
        # Account balance should be updated
        self.account_balance.refresh_from_db()
        expected_consumed = initial_consumed + Decimal("1.00") - Decimal("0.25")
        self.assertEqual(self.account_balance.hours_consumed, expected_consumed)

    def test_hour_consumption_process_refund_no_refund_due(self):
        """Test process_refund method when no refund is due."""
        consumption = HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        refund_hours = consumption.process_refund("Test refund attempt")
        
        # Should not refund anything
        self.assertEqual(refund_hours, Decimal("0.00"))
        
        # Should not be marked as refunded
        consumption.refresh_from_db()
        self.assertFalse(consumption.is_refunded)

    def test_hour_consumption_process_refund_already_refunded(self):
        """Test process_refund method when already refunded."""
        consumption = HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("0.75"),
            hours_originally_reserved=Decimal("1.00"),
            is_refunded=True
        )
        
        with self.assertRaises(ValueError) as cm:
            consumption.process_refund("Attempting double refund")
        
        self.assertIn("This consumption has already been refunded", str(cm.exception))

    def test_hour_consumption_save_updates_account_balance(self):
        """Test that saving HourConsumption updates student account balance."""
        initial_consumed = self.account_balance.hours_consumed
        
        HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("1.50"),
            hours_originally_reserved=Decimal("1.50")
        )
        
        # Account balance should be updated
        self.account_balance.refresh_from_db()
        self.assertEqual(self.account_balance.hours_consumed, initial_consumed + Decimal("1.50"))

    def test_hour_consumption_validation_student_not_in_session(self):
        """Test validation error when student account doesn't match session student."""
        other_student = User.objects.create_user(
            email="other@test.com",
            name="Other Student"
        )
        other_account = StudentAccountBalance.objects.create(
            student=other_student,
            hours_purchased=Decimal("5.00")
        )
        
        consumption = HourConsumption(
            student_account=other_account,  # Different student
            class_session=self.session,     # Session with different student
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        with self.assertRaises(ValidationError) as cm:
            consumption.full_clean()
        self.assertIn("Student account must belong to a student in the class session", str(cm.exception))

    def test_hour_consumption_unique_constraint(self):
        """Test unique constraint for student_account and class_session."""
        # Create first consumption
        HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        # Attempting to create second consumption for same student-session should fail
        with self.assertRaises(IntegrityError):
            HourConsumption.objects.create(
                student_account=self.account_balance,
                class_session=self.session,
                purchase_transaction=self.transaction,
                hours_consumed=Decimal("0.50"),
                hours_originally_reserved=Decimal("0.50")
            )

    def test_hour_consumption_string_representation(self):
        """Test HourConsumption __str__ method."""
        consumption = HourConsumption.objects.create(
            student_account=self.account_balance,
            class_session=self.session,
            purchase_transaction=self.transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00")
        )
        
        expected_str = (
            f"Hour consumption: {self.student.name} - "
            f"1.00h consumed for session on {self.session.date}"
        )
        self.assertEqual(str(consumption), expected_str)


class ReceiptTestCase(TestCase):
    """Test cases for Receipt model."""

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

    def test_receipt_creation_with_auto_generated_number(self):
        """Test creating Receipt with auto-generated receipt number."""
        receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal("100.00")
        )
        
        self.assertEqual(receipt.student, self.student)
        self.assertEqual(receipt.transaction, self.transaction)
        self.assertEqual(receipt.amount, Decimal("100.00"))
        self.assertTrue(receipt.is_valid)
        self.assertIsNotNone(receipt.receipt_number)
        self.assertTrue(receipt.receipt_number.startswith("RCP-"))
        self.assertIsNotNone(receipt.generated_at)

    def test_receipt_creation_with_custom_receipt_number(self):
        """Test creating Receipt with custom receipt number."""
        custom_number = "RCP-2024-CUSTOM01"
        receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal("100.00"),
            receipt_number=custom_number
        )
        
        self.assertEqual(receipt.receipt_number, custom_number)

    def test_receipt_validation_amount_mismatch_with_transaction(self):
        """Test validation error when receipt amount doesn't match transaction amount."""
        receipt = Receipt(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal("150.00")  # Different from transaction amount
        )
        
        with self.assertRaises(ValidationError) as cm:
            receipt.full_clean()
        self.assertIn("Receipt amount must match transaction amount", str(cm.exception))

    def test_receipt_validation_student_mismatch_with_transaction(self):
        """Test validation error when receipt student doesn't match transaction student."""
        other_student = User.objects.create_user(
            email="other@test.com",
            name="Other Student"
        )
        
        receipt = Receipt(
            student=other_student,  # Different student
            transaction=self.transaction,
            amount=Decimal("100.00")
        )
        
        with self.assertRaises(ValidationError) as cm:
            receipt.full_clean()
        self.assertIn("Receipt student must match transaction student", str(cm.exception))

    def test_receipt_string_representation(self):
        """Test Receipt __str__ method."""
        receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal("100.00"),
            receipt_number="RCP-2024-TEST01"
        )
        
        expected_str = f"Receipt RCP-2024-TEST01 - €100.00 for {self.student.name}"
        self.assertEqual(str(receipt), expected_str)

    def test_receipt_metadata_json_field(self):
        """Test metadata JSONField functionality."""
        metadata = {
            "generated_by": "automated_system",
            "payment_method": "card",
            "tax_rate": 0.21
        }
        
        receipt = Receipt.objects.create(
            student=self.student,
            transaction=self.transaction,
            amount=Decimal("100.00"),
            metadata=metadata
        )
        
        # Refresh and verify JSON integrity
        receipt.refresh_from_db()
        self.assertEqual(receipt.metadata["generated_by"], "automated_system")
        self.assertEqual(receipt.metadata["payment_method"], "card")
        self.assertEqual(receipt.metadata["tax_rate"], 0.21)


class StoredPaymentMethodTestCase(TestCase):
    """Test cases for StoredPaymentMethod model with PCI compliance."""

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )

    def test_stored_payment_method_creation_with_pci_compliant_data(self):
        """Test creating StoredPaymentMethod with PCI-compliant data."""
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id="pm_1234567890",
            stripe_customer_id="cus_1234567890",
            card_brand="visa",
            card_last4="X242",  # PCI-compliant masked format
            card_exp_month=12,
            card_exp_year=2025
        )
        
        self.assertEqual(payment_method.student, self.student)
        self.assertEqual(payment_method.stripe_payment_method_id, "pm_1234567890")
        self.assertEqual(payment_method.card_brand, "visa")
        self.assertEqual(payment_method.card_last4, "X242")
        self.assertEqual(payment_method.card_exp_month, 12)
        self.assertEqual(payment_method.card_exp_year, 2025)
        self.assertFalse(payment_method.is_default)  # Default value
        self.assertTrue(payment_method.is_active)    # Default value

    def test_stored_payment_method_pci_compliance_validation_raw_digits(self):
        """Test PCI compliance validation rejects raw card digits."""
        payment_method = StoredPaymentMethod(
            student=self.student,
            stripe_payment_method_id="pm_1234567890",
            card_brand="visa",
            card_last4="4242",  # Raw digits - PCI violation
            card_exp_month=12,
            card_exp_year=2025
        )
        
        with self.assertRaises(ValidationError) as cm:
            payment_method.full_clean()
        self.assertIn("Card last 4 digits cannot be stored in raw format for PCI compliance", str(cm.exception))

    def test_stored_payment_method_sanitization_on_save(self):
        """Test that raw card data is sanitized on save."""
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id="pm_1234567890",
            card_brand="visa",
            card_last4="4242",  # Raw digits
            card_exp_month=12,
            card_exp_year=2025
        )
        
        # Should be automatically sanitized to masked format
        payment_method.refresh_from_db()
        self.assertEqual(payment_method.card_last4, "X242")

    def test_stored_payment_method_card_display_property(self):
        """Test card_display property for PCI-compliant display."""
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id="pm_1234567890",
            card_brand="visa",
            card_last4="X242",
            card_exp_month=12,
            card_exp_year=2025
        )
        
        self.assertEqual(payment_method.card_display, "Visa ****X242")

    def test_stored_payment_method_is_expired_property_not_expired(self):
        """Test is_expired property for non-expired card."""
        future_year = timezone.now().year + 2
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id="pm_1234567890",
            card_brand="visa",
            card_last4="X242",
            card_exp_month=12,
            card_exp_year=future_year
        )
        
        self.assertFalse(payment_method.is_expired)

    def test_stored_payment_method_is_expired_property_expired_year(self):
        """Test is_expired property for card expired by year."""
        past_year = timezone.now().year - 1
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id="pm_1234567890",
            card_brand="visa",
            card_last4="X242",
            card_exp_month=12,
            card_exp_year=past_year
        )
        
        self.assertTrue(payment_method.is_expired)

    def test_stored_payment_method_is_expired_property_expired_month(self):
        """Test is_expired property for card expired by month."""
        current_year = timezone.now().year
        past_month = max(1, timezone.now().month - 1)
        
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id="pm_1234567890",
            card_brand="visa",
            card_last4="X242",
            card_exp_month=past_month,
            card_exp_year=current_year
        )
        
        # Only expired if we're past the expiration month in the current year
        if timezone.now().month > past_month:
            self.assertTrue(payment_method.is_expired)
        else:
            self.assertFalse(payment_method.is_expired)

    def test_stored_payment_method_default_constraint_enforcement(self):
        """Test that only one payment method per student can be default."""
        # Create first default payment method
        StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id="pm_1111111111",
            card_brand="visa",
            card_last4="X111",
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True
        )
        
        # Create second payment method as default
        second_payment = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id="pm_2222222222",
            card_brand="mastercard",
            card_last4="X222",
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True
        )
        
        # First payment method should no longer be default
        first_payment = StoredPaymentMethod.objects.get(stripe_payment_method_id="pm_1111111111")
        self.assertFalse(first_payment.is_default)
        self.assertTrue(second_payment.is_default)

    def test_stored_payment_method_validation_invalid_expiration_month(self):
        """Test validation error for invalid expiration month."""
        payment_method = StoredPaymentMethod(
            student=self.student,
            stripe_payment_method_id="pm_1234567890",
            card_brand="visa",
            card_last4="X242",
            card_exp_month=13,  # Invalid month
            card_exp_year=2025
        )
        
        with self.assertRaises(ValidationError) as cm:
            payment_method.full_clean()
        self.assertIn("Card expiration month must be between 1 and 12", str(cm.exception))

    def test_stored_payment_method_string_representation(self):
        """Test StoredPaymentMethod __str__ method."""
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id="pm_1234567890",
            card_brand="visa",
            card_last4="X242",
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True
        )
        
        expected_str = f"Visa ****X242 - {self.student.name} (Default)"
        self.assertEqual(str(payment_method), expected_str)


class FamilyBudgetControlTestCase(TestCase):
    """Test cases for FamilyBudgetControl model."""

    def setUp(self):
        """Set up test data."""
        ParentChildRelationship = apps.get_model('accounts', 'ParentChildRelationship')
        
        self.parent = User.objects.create_user(
            email="parent@test.com",
            name="Test Parent",
            password="testpass123"
        )
        self.child = User.objects.create_user(
            email="child@test.com",
            name="Test Child",
            password="testpass123"
        )
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child
        )

    def test_family_budget_control_creation_with_limits(self):
        """Test creating FamilyBudgetControl with budget limits."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal("200.00"),
            weekly_budget_limit=Decimal("50.00"),
            auto_approval_threshold=Decimal("25.00"),
            require_approval_for_sessions=True,
            require_approval_for_packages=True
        )
        
        self.assertEqual(budget_control.parent_child_relationship, self.relationship)
        self.assertEqual(budget_control.monthly_budget_limit, Decimal("200.00"))
        self.assertEqual(budget_control.weekly_budget_limit, Decimal("50.00"))
        self.assertEqual(budget_control.auto_approval_threshold, Decimal("25.00"))
        self.assertTrue(budget_control.require_approval_for_sessions)
        self.assertTrue(budget_control.require_approval_for_packages)
        self.assertTrue(budget_control.is_active)

    def test_family_budget_control_current_monthly_spending_calculation(self):
        """Test current_monthly_spending property calculation."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal("200.00")
        )
        
        # Create transactions for current month
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=current_month_start + timedelta(days=5)
        )
        
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("30.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=current_month_start + timedelta(days=10)
        )
        
        # Should sum to 80.00
        self.assertEqual(budget_control.current_monthly_spending, Decimal("80.00"))

    def test_family_budget_control_current_weekly_spending_calculation(self):
        """Test current_weekly_spending property calculation."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            weekly_budget_limit=Decimal("50.00")
        )
        
        # Create transaction for current week
        now = timezone.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("25.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=week_start + timedelta(days=2)
        )
        
        self.assertEqual(budget_control.current_weekly_spending, Decimal("25.00"))

    def test_family_budget_control_check_budget_limits_within_limits(self):
        """Test check_budget_limits method when within all limits."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal("200.00"),
            weekly_budget_limit=Decimal("50.00"),
            auto_approval_threshold=Decimal("25.00")
        )
        
        # Mock current spending to be low
        with patch.object(budget_control, 'current_monthly_spending', Decimal("50.00")), \
             patch.object(budget_control, 'current_weekly_spending', Decimal("10.00")):
            
            result = budget_control.check_budget_limits(Decimal("20.00"))
            
            self.assertTrue(result['allowed'])
            self.assertTrue(result['can_auto_approve'])  # Under auto-approval threshold
            self.assertEqual(result['reasons'], [])

    def test_family_budget_control_check_budget_limits_exceeds_monthly(self):
        """Test check_budget_limits method when exceeding monthly limit."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal("100.00"),
            auto_approval_threshold=Decimal("25.00")
        )
        
        # Mock current spending to be high
        with patch.object(budget_control, 'current_monthly_spending', Decimal("90.00")), \
             patch.object(budget_control, 'current_weekly_spending', Decimal("10.00")):
            
            result = budget_control.check_budget_limits(Decimal("20.00"))  # Would total 110.00
            
            self.assertFalse(result['allowed'])
            self.assertFalse(result['can_auto_approve'])
            self.assertIn("Would exceed monthly budget limit of €100.00", result['reasons'])

    def test_family_budget_control_check_budget_limits_over_auto_approval_threshold(self):
        """Test check_budget_limits when amount is over auto-approval threshold but within budget."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal("200.00"),
            auto_approval_threshold=Decimal("25.00")
        )
        
        # Mock current spending to be low
        with patch.object(budget_control, 'current_monthly_spending', Decimal("50.00")), \
             patch.object(budget_control, 'current_weekly_spending', Decimal("10.00")):
            
            result = budget_control.check_budget_limits(Decimal("30.00"))  # Over threshold
            
            self.assertTrue(result['allowed'])
            self.assertFalse(result['can_auto_approve'])  # Over auto-approval threshold
            self.assertEqual(result['reasons'], [])

    def test_family_budget_control_validation_auto_approval_exceeds_monthly_limit(self):
        """Test validation error when auto approval threshold exceeds monthly limit."""
        budget_control = FamilyBudgetControl(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal("100.00"),
            auto_approval_threshold=Decimal("150.00")  # Higher than monthly limit
        )
        
        with self.assertRaises(ValidationError) as cm:
            budget_control.full_clean()
        self.assertIn("Auto approval threshold cannot be greater than monthly budget limit", str(cm.exception))

    def test_family_budget_control_validation_auto_approval_exceeds_weekly_limit(self):
        """Test validation error when auto approval threshold exceeds weekly limit."""
        budget_control = FamilyBudgetControl(
            parent_child_relationship=self.relationship,
            weekly_budget_limit=Decimal("30.00"),
            auto_approval_threshold=Decimal("50.00")  # Higher than weekly limit
        )
        
        with self.assertRaises(ValidationError) as cm:
            budget_control.full_clean()
        self.assertIn("Auto approval threshold cannot be greater than weekly budget limit", str(cm.exception))

    def test_family_budget_control_string_representation(self):
        """Test FamilyBudgetControl __str__ method."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship
        )
        
        expected_str = f"Budget Control: {self.parent.name} -> {self.child.name}"
        self.assertEqual(str(budget_control), expected_str)


class PurchaseApprovalRequestTestCase(TestCase):
    """Test cases for PurchaseApprovalRequest model."""

    def setUp(self):
        """Set up test data."""
        ParentChildRelationship = apps.get_model('accounts', 'ParentChildRelationship')
        
        self.parent = User.objects.create_user(
            email="parent@test.com",
            name="Test Parent",
            password="testpass123"
        )
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.student
        )
        self.pricing_plan = PricingPlan.objects.create(
            name="Test Package",
            description="Test package for approval",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1
        )

    def test_purchase_approval_request_creation_with_auto_expiration(self):
        """Test creating PurchaseApprovalRequest with automatic expiration time."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("100.00"),
            description="10 hours tutoring package",
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )
        
        self.assertEqual(approval_request.student, self.student)
        self.assertEqual(approval_request.parent, self.parent)
        self.assertEqual(approval_request.amount, Decimal("100.00"))
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.PENDING)
        self.assertIsNotNone(approval_request.expires_at)
        self.assertIsNone(approval_request.responded_at)
        
        # Should expire in approximately 24 hours
        expected_expiration = timezone.now() + timedelta(hours=24)
        self.assertAlmostEqual(
            approval_request.expires_at, 
            expected_expiration, 
            delta=timedelta(minutes=1)
        )

    def test_purchase_approval_request_is_expired_property_not_expired(self):
        """Test is_expired property for non-expired request."""
        future_time = timezone.now() + timedelta(hours=12)
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("50.00"),
            description="Test request",
            request_type=PurchaseRequestType.SESSION,
            expires_at=future_time
        )
        
        self.assertFalse(approval_request.is_expired)

    def test_purchase_approval_request_is_expired_property_expired(self):
        """Test is_expired property for expired request."""
        past_time = timezone.now() - timedelta(hours=1)
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("50.00"),
            description="Test request",
            request_type=PurchaseRequestType.SESSION,
            expires_at=past_time
        )
        
        self.assertTrue(approval_request.is_expired)

    def test_purchase_approval_request_approve_method(self):
        """Test approve method functionality."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("50.00"),
            description="Test request",
            request_type=PurchaseRequestType.SESSION
        )
        
        approval_request.approve("Approved for educational purposes")
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.APPROVED)
        self.assertEqual(approval_request.parent_notes, "Approved for educational purposes")
        self.assertIsNotNone(approval_request.responded_at)

    def test_purchase_approval_request_deny_method(self):
        """Test deny method functionality."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("50.00"),
            description="Test request",
            request_type=PurchaseRequestType.SESSION
        )
        
        approval_request.deny("Not within budget this month")
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.DENIED)
        self.assertEqual(approval_request.parent_notes, "Not within budget this month")
        self.assertIsNotNone(approval_request.responded_at)

    def test_purchase_approval_request_cancel_method(self):
        """Test cancel method functionality."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("50.00"),
            description="Test request",
            request_type=PurchaseRequestType.SESSION
        )
        
        approval_request.cancel()
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.CANCELLED)
        self.assertIsNotNone(approval_request.responded_at)

    def test_purchase_approval_request_mark_expired_method(self):
        """Test mark_expired method functionality."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("50.00"),
            description="Test request",
            request_type=PurchaseRequestType.SESSION
        )
        
        approval_request.mark_expired()
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.EXPIRED)
        self.assertIsNotNone(approval_request.responded_at)

    def test_purchase_approval_request_approve_expired_request_fails(self):
        """Test that approving an expired request fails."""
        past_time = timezone.now() - timedelta(hours=1)
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("50.00"),
            description="Test request",
            request_type=PurchaseRequestType.SESSION,
            expires_at=past_time
        )
        
        with self.assertRaises(ValidationError) as cm:
            approval_request.approve("Trying to approve expired request")
        self.assertIn("Cannot approve an expired request", str(cm.exception))

    def test_purchase_approval_request_validation_same_student_and_parent(self):
        """Test validation error when student and parent are the same user."""
        approval_request = PurchaseApprovalRequest(
            student=self.student,
            parent=self.student,  # Same as student
            parent_child_relationship=self.relationship,
            amount=Decimal("50.00"),
            description="Test request",
            request_type=PurchaseRequestType.SESSION
        )
        
        with self.assertRaises(ValidationError) as cm:
            approval_request.full_clean()
        self.assertIn("Student and parent cannot be the same user", str(cm.exception))

    def test_purchase_approval_request_time_remaining_property(self):
        """Test time_remaining property calculation."""
        future_time = timezone.now() + timedelta(hours=6)
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("50.00"),
            description="Test request",
            request_type=PurchaseRequestType.SESSION,
            expires_at=future_time
        )
        
        remaining = approval_request.time_remaining
        # Should be approximately 6 hours
        self.assertAlmostEqual(remaining.total_seconds(), 6 * 3600, delta=60)

    def test_purchase_approval_request_string_representation(self):
        """Test PurchaseApprovalRequest __str__ method."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal("100.00"),
            description="Test request",
            request_type=PurchaseRequestType.HOURS
        )
        
        expected_str = f"Purchase Request: {self.student.name} -> {self.parent.name} (€100.00)"
        self.assertEqual(str(approval_request), expected_str)


class WebhookEventLogTestCase(TestCase):
    """Test cases for WebhookEventLog model."""

    def test_webhook_event_log_creation(self):
        """Test creating WebhookEventLog with required fields."""
        payload = {
            "id": "evt_test123",
            "object": "event",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test123"}}
        }
        
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload=payload
        )
        
        self.assertEqual(webhook_log.stripe_event_id, "evt_test123")
        self.assertEqual(webhook_log.event_type, "payment_intent.succeeded")
        self.assertEqual(webhook_log.status, WebhookEventStatus.RECEIVED)
        self.assertEqual(webhook_log.payload, payload)
        self.assertEqual(webhook_log.retry_count, 0)
        self.assertEqual(webhook_log.error_message, "")

    def test_webhook_event_log_mark_as_processing_method(self):
        """Test mark_as_processing method."""
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={}
        )
        
        webhook_log.mark_as_processing()
        
        webhook_log.refresh_from_db()
        self.assertEqual(webhook_log.status, WebhookEventStatus.PROCESSING)
        self.assertIsNotNone(webhook_log.processed_at)

    def test_webhook_event_log_mark_as_processed_method(self):
        """Test mark_as_processed method."""
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={}
        )
        
        webhook_log.mark_as_processed()
        
        webhook_log.refresh_from_db()
        self.assertEqual(webhook_log.status, WebhookEventStatus.PROCESSED)
        self.assertIsNotNone(webhook_log.processed_at)

    def test_webhook_event_log_mark_as_failed_method(self):
        """Test mark_as_failed method."""
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={}
        )
        
        error_message = "Failed to process payment intent"
        webhook_log.mark_as_failed(error_message)
        
        webhook_log.refresh_from_db()
        self.assertEqual(webhook_log.status, WebhookEventStatus.FAILED)
        self.assertEqual(webhook_log.error_message, error_message)
        self.assertIsNotNone(webhook_log.processed_at)

    def test_webhook_event_log_increment_retry_count_method(self):
        """Test increment_retry_count method."""
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={}
        )
        
        webhook_log.increment_retry_count()
        
        webhook_log.refresh_from_db()
        self.assertEqual(webhook_log.retry_count, 1)
        self.assertEqual(webhook_log.status, WebhookEventStatus.RETRYING)

    def test_webhook_event_log_is_retryable_method_retryable(self):
        """Test is_retryable method when event can be retried."""
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={},
            status=WebhookEventStatus.FAILED,
            retry_count=2
        )
        
        self.assertTrue(webhook_log.is_retryable())

    def test_webhook_event_log_is_retryable_method_max_retries_exceeded(self):
        """Test is_retryable method when max retries exceeded."""
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={},
            status=WebhookEventStatus.FAILED,
            retry_count=5  # Max retries exceeded
        )
        
        self.assertFalse(webhook_log.is_retryable())

    def test_webhook_event_log_is_retryable_method_already_processed(self):
        """Test is_retryable method when event already processed."""
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={},
            status=WebhookEventStatus.PROCESSED,
            retry_count=0
        )
        
        self.assertFalse(webhook_log.is_retryable())

    def test_webhook_event_log_get_processing_duration_method(self):
        """Test get_processing_duration method."""
        created_time = timezone.now()
        processed_time = created_time + timedelta(seconds=30)
        
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={},
            processed_at=processed_time
        )
        
        # Manually set created_at to control the duration calculation
        webhook_log.created_at = created_time
        webhook_log.save()
        
        duration = webhook_log.get_processing_duration()
        self.assertEqual(duration, timedelta(seconds=30))

    def test_webhook_event_log_processing_time_seconds_property(self):
        """Test processing_time_seconds property."""
        created_time = timezone.now()
        processed_time = created_time + timedelta(seconds=45)
        
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={},
            processed_at=processed_time
        )
        
        # Manually set created_at to control the duration calculation
        webhook_log.created_at = created_time
        webhook_log.save()
        
        self.assertEqual(webhook_log.processing_time_seconds, 45.0)

    def test_webhook_event_log_string_representation(self):
        """Test WebhookEventLog __str__ method."""
        webhook_log = WebhookEventLog.objects.create(
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={},
            status=WebhookEventStatus.PROCESSED
        )
        
        expected_str = "Webhook Event: evt_test123 (payment_intent.succeeded) - Processed"
        self.assertEqual(str(webhook_log), expected_str)


class PaymentDisputeTestCase(TestCase):
    """Test cases for PaymentDispute model."""

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

    def test_payment_dispute_creation(self):
        """Test creating PaymentDispute with required fields."""
        evidence_due = timezone.now() + timedelta(days=7)
        dispute = PaymentDispute.objects.create(
            stripe_dispute_id="dp_test123",
            purchase_transaction=self.transaction,
            amount=Decimal("100.00"),
            reason=DisputeReason.UNRECOGNIZED,
            status=DisputeStatus.NEEDS_RESPONSE,
            evidence_due_by=evidence_due
        )
        
        self.assertEqual(dispute.stripe_dispute_id, "dp_test123")
        self.assertEqual(dispute.purchase_transaction, self.transaction)
        self.assertEqual(dispute.amount, Decimal("100.00"))
        self.assertEqual(dispute.reason, DisputeReason.UNRECOGNIZED)
        self.assertEqual(dispute.status, DisputeStatus.NEEDS_RESPONSE)
        self.assertEqual(dispute.evidence_due_by, evidence_due)
        self.assertFalse(dispute.is_responded)

    def test_payment_dispute_is_evidence_overdue_property_not_overdue(self):
        """Test is_evidence_overdue property when evidence is not overdue."""
        future_time = timezone.now() + timedelta(days=3)
        dispute = PaymentDispute.objects.create(
            stripe_dispute_id="dp_test123",
            purchase_transaction=self.transaction,
            amount=Decimal("100.00"),
            reason=DisputeReason.UNRECOGNIZED,
            status=DisputeStatus.NEEDS_RESPONSE,
            evidence_due_by=future_time
        )
        
        self.assertFalse(dispute.is_evidence_overdue)

    def test_payment_dispute_is_evidence_overdue_property_overdue(self):
        """Test is_evidence_overdue property when evidence is overdue."""
        past_time = timezone.now() - timedelta(days=1)
        dispute = PaymentDispute.objects.create(
            stripe_dispute_id="dp_test123",
            purchase_transaction=self.transaction,
            amount=Decimal("100.00"),
            reason=DisputeReason.UNRECOGNIZED,
            status=DisputeStatus.NEEDS_RESPONSE,
            evidence_due_by=past_time
        )
        
        self.assertTrue(dispute.is_evidence_overdue)

    def test_payment_dispute_days_until_evidence_due_property(self):
        """Test days_until_evidence_due property calculation."""
        future_time = timezone.now() + timedelta(days=5, hours=12)
        dispute = PaymentDispute.objects.create(
            stripe_dispute_id="dp_test123",
            purchase_transaction=self.transaction,
            amount=Decimal("100.00"),
            reason=DisputeReason.UNRECOGNIZED,
            status=DisputeStatus.NEEDS_RESPONSE,
            evidence_due_by=future_time
        )
        
        # Should return 5 days (rounds down)
        self.assertEqual(dispute.days_until_evidence_due, 5)

    def test_payment_dispute_mark_responded_method(self):
        """Test mark_responded method."""
        dispute = PaymentDispute.objects.create(
            stripe_dispute_id="dp_test123",
            purchase_transaction=self.transaction,
            amount=Decimal("100.00"),
            reason=DisputeReason.UNRECOGNIZED,
            status=DisputeStatus.NEEDS_RESPONSE
        )
        
        dispute.mark_responded()
        
        dispute.refresh_from_db()
        self.assertTrue(dispute.is_responded)
        self.assertIsNotNone(dispute.response_submitted_at)

    def test_payment_dispute_string_representation(self):
        """Test PaymentDispute __str__ method."""
        dispute = PaymentDispute.objects.create(
            stripe_dispute_id="dp_test123",
            purchase_transaction=self.transaction,
            amount=Decimal("100.00"),
            reason=DisputeReason.UNRECOGNIZED,
            status=DisputeStatus.NEEDS_RESPONSE
        )
        
        expected_str = "Dispute dp_test123 - €100.00 (Needs Response)"
        self.assertEqual(str(dispute), expected_str)


class AdminActionTestCase(TestCase):
    """Test cases for AdminAction model."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            name="Test Admin",
            password="testpass123"
        )
        self.target_user = User.objects.create_user(
            email="user@test.com",
            name="Test User",
            password="testpass123"
        )

    def test_admin_action_creation_successful_action(self):
        """Test creating AdminAction for successful action."""
        admin_action = AdminAction.objects.create(
            action_type=AdminActionType.REFUND_CREATED,
            action_description="Created refund for user due to service issue",
            admin_user=self.admin_user,
            target_user=self.target_user,
            success=True,
            result_message="Refund of €50.00 processed successfully",
            amount_impacted=Decimal("50.00"),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Test Browser)",
            two_factor_verified=True
        )
        
        self.assertEqual(admin_action.action_type, AdminActionType.REFUND_CREATED)
        self.assertEqual(admin_action.admin_user, self.admin_user)
        self.assertEqual(admin_action.target_user, self.target_user)
        self.assertTrue(admin_action.success)
        self.assertEqual(admin_action.amount_impacted, Decimal("50.00"))
        self.assertTrue(admin_action.two_factor_verified)

    def test_admin_action_creation_failed_action(self):
        """Test creating AdminAction for failed action."""
        admin_action = AdminAction.objects.create(
            action_type=AdminActionType.PAYMENT_RETRY,
            action_description="Attempted to retry failed payment",
            admin_user=self.admin_user,
            target_user=self.target_user,
            success=False,
            result_message="Payment retry failed: insufficient funds",
            two_factor_verified=False
        )
        
        self.assertFalse(admin_action.success)
        self.assertEqual(admin_action.result_message, "Payment retry failed: insufficient funds")
        self.assertFalse(admin_action.two_factor_verified)

    def test_admin_action_with_action_data_json(self):
        """Test AdminAction with action_data JSONField."""
        action_data = {
            "original_amount": "100.00",
            "refund_amount": "50.00",
            "refund_reason": "partial_service",
            "stripe_refund_id": "re_test123"
        }
        
        admin_action = AdminAction.objects.create(
            action_type=AdminActionType.REFUND_CREATED,
            action_description="Processed partial refund",
            admin_user=self.admin_user,
            success=True,
            action_data=action_data
        )
        
        # Refresh and verify JSON integrity
        admin_action.refresh_from_db()
        self.assertEqual(admin_action.action_data["original_amount"], "100.00")
        self.assertEqual(admin_action.action_data["refund_amount"], "50.00")
        self.assertEqual(admin_action.action_data["stripe_refund_id"], "re_test123")

    def test_admin_action_string_representation_successful(self):
        """Test AdminAction __str__ method for successful action."""
        admin_action = AdminAction.objects.create(
            action_type=AdminActionType.REFUND_CREATED,
            action_description="Test action",
            admin_user=self.admin_user,
            success=True
        )
        
        expected_str = f"✓ Refund Created by {self.admin_user.name} at {admin_action.created_at}"
        self.assertEqual(str(admin_action), expected_str)

    def test_admin_action_string_representation_failed(self):
        """Test AdminAction __str__ method for failed action."""
        admin_action = AdminAction.objects.create(
            action_type=AdminActionType.PAYMENT_RETRY,
            action_description="Test failed action",
            admin_user=self.admin_user,
            success=False
        )
        
        expected_str = f"✗ Payment Retry by {self.admin_user.name} at {admin_action.created_at}"
        self.assertEqual(str(admin_action), expected_str)


class FraudAlertTestCase(TestCase):
    """Test cases for FraudAlert model."""

    def setUp(self):
        """Set up test data."""
        self.target_user = User.objects.create_user(
            email="user@test.com",
            name="Test User",
            password="testpass123"
        )
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            name="Test Admin",
            password="testpass123"
        )

    def test_fraud_alert_creation_with_auto_generated_id(self):
        """Test creating FraudAlert with auto-generated alert ID."""
        fraud_alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.HIGH,
            alert_type="multiple_failed_payments",
            description="Multiple payment failures detected within 30 minutes",
            target_user=self.target_user,
            risk_score=Decimal("85.50")
        )
        
        self.assertEqual(fraud_alert.severity, FraudAlertSeverity.HIGH)
        self.assertEqual(fraud_alert.status, FraudAlertStatus.ACTIVE)  # Default
        self.assertEqual(fraud_alert.target_user, self.target_user)
        self.assertEqual(fraud_alert.risk_score, Decimal("85.50"))
        self.assertIsNotNone(fraud_alert.alert_id)
        self.assertTrue(fraud_alert.alert_id.startswith("FA-"))

    def test_fraud_alert_with_detection_data_json(self):
        """Test FraudAlert with detection_data JSONField."""
        detection_data = {
            "failed_payment_count": 5,
            "time_window_minutes": 30,
            "ip_addresses": ["192.168.1.1", "10.0.0.1"],
            "user_agents": ["Browser A", "Browser B"],
            "payment_methods_attempted": ["pm_123", "pm_456"]
        }
        
        fraud_alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.CRITICAL,
            alert_type="payment_fraud_pattern",
            description="Suspicious payment pattern detected",
            target_user=self.target_user,
            detection_data=detection_data,
            risk_score=Decimal("95.00")
        )
        
        # Refresh and verify JSON integrity
        fraud_alert.refresh_from_db()
        self.assertEqual(fraud_alert.detection_data["failed_payment_count"], 5)
        self.assertEqual(fraud_alert.detection_data["time_window_minutes"], 30)
        self.assertIn("192.168.1.1", fraud_alert.detection_data["ip_addresses"])

    def test_fraud_alert_is_high_priority_property(self):
        """Test is_high_priority property for different severity levels."""
        high_alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.HIGH,
            alert_type="test_alert",
            description="High severity alert",
            risk_score=Decimal("80.00")
        )
        
        critical_alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.CRITICAL,
            alert_type="test_alert",
            description="Critical severity alert",
            risk_score=Decimal("95.00")
        )
        
        medium_alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.MEDIUM,
            alert_type="test_alert",
            description="Medium severity alert",
            risk_score=Decimal("60.00")
        )
        
        self.assertTrue(high_alert.is_high_priority)
        self.assertTrue(critical_alert.is_high_priority)
        self.assertFalse(medium_alert.is_high_priority)

    def test_fraud_alert_assign_to_investigator_method(self):
        """Test assign_to_investigator method."""
        fraud_alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.HIGH,
            alert_type="test_alert",
            description="Test alert for assignment",
            risk_score=Decimal("75.00")
        )
        
        fraud_alert.assign_to_investigator(self.admin_user)
        
        fraud_alert.refresh_from_db()
        self.assertEqual(fraud_alert.assigned_to, self.admin_user)
        self.assertEqual(fraud_alert.status, FraudAlertStatus.INVESTIGATING)

    def test_fraud_alert_mark_resolved_method(self):
        """Test mark_resolved method."""
        fraud_alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.HIGH,
            alert_type="test_alert",
            description="Test alert for resolution",
            risk_score=Decimal("75.00"),
            assigned_to=self.admin_user,
            status=FraudAlertStatus.INVESTIGATING
        )
        
        actions_taken = ["blocked_payment_method", "notified_user", "increased_monitoring"]
        fraud_alert.mark_resolved("False positive - user verified identity", actions_taken)
        
        fraud_alert.refresh_from_db()
        self.assertEqual(fraud_alert.status, FraudAlertStatus.RESOLVED)
        self.assertEqual(fraud_alert.resolution_notes, "False positive - user verified identity")
        self.assertEqual(fraud_alert.actions_taken, actions_taken)
        self.assertIsNotNone(fraud_alert.investigated_at)

    def test_fraud_alert_mark_false_positive_method(self):
        """Test mark_false_positive method."""
        fraud_alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.MEDIUM,
            alert_type="test_alert",
            description="Test alert for false positive",
            risk_score=Decimal("65.00")
        )
        
        fraud_alert.mark_false_positive("User behavior confirmed legitimate after investigation")
        
        fraud_alert.refresh_from_db()
        self.assertEqual(fraud_alert.status, FraudAlertStatus.FALSE_POSITIVE)
        self.assertEqual(fraud_alert.resolution_notes, "User behavior confirmed legitimate after investigation")
        self.assertIsNotNone(fraud_alert.investigated_at)

    def test_fraud_alert_days_since_created_property(self):
        """Test days_since_created property calculation."""
        # Create alert with specific creation time
        past_time = timezone.now() - timedelta(days=3, hours=12)
        fraud_alert = FraudAlert.objects.create(
            severity=FraudAlertSeverity.LOW,
            alert_type="test_alert",
            description="Test alert for age calculation",
            risk_score=Decimal("30.00")
        )
        
        # Manually set created_at to control the calculation
        fraud_alert.created_at = past_time
        fraud_alert.save()
        
        # Should return 3 days (rounds down)
        self.assertEqual(fraud_alert.days_since_created, 3)

    def test_fraud_alert_string_representation(self):
        """Test FraudAlert __str__ method."""
        fraud_alert = FraudAlert.objects.create(
            alert_id="FA-2024-TEST123",
            severity=FraudAlertSeverity.HIGH,
            status=FraudAlertStatus.INVESTIGATING,
            alert_type="test_alert",
            description="Test alert",
            risk_score=Decimal("80.00")
        )
        
        expected_str = "Fraud Alert FA-2024-TEST123 - High (Investigating)"
        self.assertEqual(str(fraud_alert), expected_str)