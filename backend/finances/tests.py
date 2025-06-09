from datetime import date, time
from decimal import Decimal

from accounts.models import CustomUser, School, TeacherProfile
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import (
    ClassSession,
    CompensationRuleType,
    SchoolBillingSettings,
    SessionType,
    TeacherCompensationRule,
    TrialCostAbsorption,
)
from .services import TeacherPaymentCalculator


class TeacherPaymentCalculatorTestCase(TestCase):
    """Test cases for teacher payment calculation logic."""

    def setUp(self):
        """Set up test data for Teacher A's scenario."""
        # Create school
        self.school = School.objects.create(name="Test School", description="A test school")

        # Create user and teacher profile
        self.user = CustomUser.objects.create_user(
            email="teacher.a@example.com", name="Teacher A", password="testpass123"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.user,
            bio="Experienced teacher",
            hourly_rate=Decimal("12.00"),  # Fallback rate
        )

        # Create school billing settings
        self.billing_settings = SchoolBillingSettings.objects.create(
            school=self.school, trial_cost_absorption=TrialCostAbsorption.SCHOOL
        )

        # Create compensation rules for Teacher A
        # Grade 7 rate: €15/hour
        self.grade_7_rule = TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="7",
            rate_per_hour=Decimal("15.00"),
            effective_from=date(2024, 1, 1),
        )

        # Grade 10 rate: €20/hour
        self.grade_10_rule = TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="10",
            rate_per_hour=Decimal("20.00"),
            effective_from=date(2024, 1, 1),
        )

        # Group class rate: €10/hour regardless of student count
        self.group_rule = TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GROUP_CLASS,
            rate_per_hour=Decimal("10.00"),
            effective_from=date(2024, 1, 1),
        )

    def test_grade_7_individual_session(self):
        """Test payment calculation for Grade 7 individual session."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date(2024, 1, 15),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="7",
            student_count=1,
            status="completed",
        )

        rate, rule = TeacherPaymentCalculator.get_applicable_rate(session)

        self.assertEqual(rate, Decimal("15.00"))
        self.assertEqual(rule, self.grade_7_rule)

        # Calculate payment entry
        payment_entry = TeacherPaymentCalculator.calculate_session_payment(session)

        self.assertEqual(payment_entry.hours_taught, Decimal("1.0"))
        self.assertEqual(payment_entry.rate_applied, Decimal("15.00"))
        self.assertEqual(payment_entry.amount_earned, Decimal("15.00"))
        self.assertEqual(payment_entry.compensation_rule, self.grade_7_rule)

    def test_grade_10_individual_session(self):
        """Test payment calculation for Grade 10 individual session."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date(2024, 1, 15),
            start_time=time(16, 0),
            end_time=time(17, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status="completed",
        )

        rate, rule = TeacherPaymentCalculator.get_applicable_rate(session)

        self.assertEqual(rate, Decimal("20.00"))
        self.assertEqual(rule, self.grade_10_rule)

        # Calculate payment entry
        payment_entry = TeacherPaymentCalculator.calculate_session_payment(session)

        self.assertEqual(payment_entry.amount_earned, Decimal("20.00"))

    def test_group_session_rate_priority(self):
        """Test that group class rate takes priority over grade-specific rates."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date(2024, 1, 16),
            start_time=time(15, 0),
            end_time=time(16, 30),  # 1.5 hours
            session_type=SessionType.GROUP,
            grade_level="mixed",  # Mixed grades
            student_count=5,
            status="completed",
        )

        rate, rule = TeacherPaymentCalculator.get_applicable_rate(session)

        self.assertEqual(rate, Decimal("10.00"))
        self.assertEqual(rule, self.group_rule)

        # Calculate payment entry
        payment_entry = TeacherPaymentCalculator.calculate_session_payment(session)

        self.assertEqual(payment_entry.hours_taught, Decimal("1.5"))
        self.assertEqual(payment_entry.rate_applied, Decimal("10.00"))
        self.assertEqual(payment_entry.amount_earned, Decimal("15.00"))  # 1.5 * 10

    def test_trial_session_school_absorbs(self):
        """Test that trial sessions have zero cost when school absorbs the cost."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date(2024, 1, 17),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="7",
            student_count=1,
            is_trial=True,
            status="completed",
        )

        rate, rule = TeacherPaymentCalculator.get_applicable_rate(session)

        self.assertEqual(rate, Decimal("0.00"))
        self.assertIsNone(rule)

        # Calculate payment entry
        payment_entry = TeacherPaymentCalculator.calculate_session_payment(session)

        self.assertEqual(payment_entry.amount_earned, Decimal("0.00"))
        self.assertIn("Trial session", payment_entry.calculation_notes)

    def test_trial_session_teacher_absorbs(self):
        """Test trial sessions when teacher absorbs the cost."""
        # Change billing settings
        self.billing_settings.trial_cost_absorption = TrialCostAbsorption.TEACHER
        self.billing_settings.save()

        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date(2024, 1, 17),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="7",
            student_count=1,
            is_trial=True,
            status="completed",
        )

        rate, rule = TeacherPaymentCalculator.get_applicable_rate(session)

        # Should use normal grade 7 rate since teacher absorbs the cost
        self.assertEqual(rate, Decimal("15.00"))
        self.assertEqual(rule, self.grade_7_rule)

    def test_trial_session_split_cost(self):
        """Test trial sessions with split cost (50/50)."""
        # Change billing settings
        self.billing_settings.trial_cost_absorption = TrialCostAbsorption.SPLIT
        self.billing_settings.save()

        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date(2024, 1, 17),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="7",
            student_count=1,
            is_trial=True,
            status="completed",
        )

        rate, rule = TeacherPaymentCalculator.get_applicable_rate(session)

        # Should be half of the normal grade 7 rate
        self.assertEqual(rate, Decimal("7.50"))  # 15.00 * 0.5
        self.assertEqual(rule, self.grade_7_rule)

    def test_fallback_to_teacher_hourly_rate(self):
        """Test fallback to teacher's default hourly rate when no specific rule exists."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date(2024, 1, 15),
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="5",  # No specific rule for grade 5
            student_count=1,
            status="completed",
        )

        rate, rule = TeacherPaymentCalculator.get_applicable_rate(session)

        self.assertEqual(rate, Decimal("12.00"))  # Teacher's default rate
        self.assertIsNone(rule)

    def test_monthly_total_calculation(self):
        """Test calculating monthly totals for Teacher A."""
        # Create multiple sessions for January 2024
        sessions = [
            # Session 1: Grade 7, 1 hour = €15
            ClassSession.objects.create(
                teacher=self.teacher,
                school=self.school,
                date=date(2024, 1, 15),
                start_time=time(14, 0),
                end_time=time(15, 0),
                session_type=SessionType.INDIVIDUAL,
                grade_level="7",
                student_count=1,
                status="completed",
            ),
            # Session 2: Grade 10, 1 hour = €20
            ClassSession.objects.create(
                teacher=self.teacher,
                school=self.school,
                date=date(2024, 1, 15),
                start_time=time(16, 0),
                end_time=time(17, 0),
                session_type=SessionType.INDIVIDUAL,
                grade_level="10",
                student_count=1,
                status="completed",
            ),
            # Session 3: Group class, 1.5 hours = €15
            ClassSession.objects.create(
                teacher=self.teacher,
                school=self.school,
                date=date(2024, 1, 16),
                start_time=time(15, 0),
                end_time=time(16, 30),
                session_type=SessionType.GROUP,
                grade_level="mixed",
                student_count=5,
                status="completed",
            ),
            # Session 4: Trial class = €0
            ClassSession.objects.create(
                teacher=self.teacher,
                school=self.school,
                date=date(2024, 1, 17),
                start_time=time(14, 0),
                end_time=time(15, 0),
                session_type=SessionType.INDIVIDUAL,
                grade_level="7",
                student_count=1,
                is_trial=True,
                status="completed",
            ),
        ]

        # Calculate payments for all sessions
        for session in sessions:
            TeacherPaymentCalculator.calculate_session_payment(session)

        # Get monthly total
        monthly_total = TeacherPaymentCalculator.calculate_monthly_total(
            self.teacher, self.school, 2024, 1
        )

        # Verify totals
        self.assertEqual(monthly_total["total_hours"], Decimal("4.5"))
        self.assertEqual(monthly_total["total_amount"], Decimal("50.00"))  # 15 + 20 + 15 + 0
        self.assertEqual(monthly_total["session_count"], 4)

        # Verify breakdown
        self.assertEqual(monthly_total["individual_sessions"]["count"], 3)
        self.assertEqual(monthly_total["group_sessions"]["count"], 1)
        self.assertEqual(monthly_total["trial_sessions"]["count"], 1)

    def test_session_validation(self):
        """Test session model validation."""
        # Test invalid time range
        with self.assertRaises(ValidationError):
            session = ClassSession(
                teacher=self.teacher,
                school=self.school,
                date=date(2024, 1, 15),
                start_time=time(15, 0),
                end_time=time(14, 0),  # End before start
                session_type=SessionType.INDIVIDUAL,
                grade_level="7",
                student_count=1,
            )
            session.full_clean()

        # Test individual session with multiple students
        with self.assertRaises(ValidationError):
            session = ClassSession(
                teacher=self.teacher,
                school=self.school,
                date=date(2024, 1, 15),
                start_time=time(14, 0),
                end_time=time(15, 0),
                session_type=SessionType.INDIVIDUAL,
                grade_level="7",
                student_count=3,  # Invalid for individual session
            )
            session.full_clean()

    def test_compensation_rule_validation(self):
        """Test compensation rule validation."""
        # Test grade-specific rule without grade level
        with self.assertRaises(ValidationError):
            rule = TeacherCompensationRule(
                teacher=self.teacher,
                school=self.school,
                rule_type=CompensationRuleType.GRADE_SPECIFIC,
                # Missing grade_level
                rate_per_hour=Decimal("15.00"),
            )
            rule.full_clean()

        # Test grade-specific rule without rate
        with self.assertRaises(ValidationError):
            rule = TeacherCompensationRule(
                teacher=self.teacher,
                school=self.school,
                rule_type=CompensationRuleType.GRADE_SPECIFIC,
                grade_level="7",
                # Missing rate_per_hour
            )
            rule.full_clean()


class SchoolBillingSettingsTestCase(TestCase):
    """Test cases for school billing settings."""

    def test_payment_day_validation(self):
        """Test validation of payment day of month."""
        school = School.objects.create(name="Test School")

        # Valid payment day
        settings = SchoolBillingSettings(school=school, payment_day_of_month=15)
        settings.full_clean()  # Should not raise

        # Invalid payment day (too high)
        with self.assertRaises(ValidationError):
            settings = SchoolBillingSettings(
                school=school,
                payment_day_of_month=31,  # Invalid - not all months have 31 days
            )
            settings.full_clean()

        # Invalid payment day (too low)
        with self.assertRaises(ValidationError):
            settings = SchoolBillingSettings(school=school, payment_day_of_month=0)
            settings.full_clean()
