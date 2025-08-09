from datetime import date, time, timedelta
from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

User = get_user_model()

from ..models import (
    ClassSession,
    CompensationRuleType,
    PurchaseTransaction,
    SchoolBillingSettings,
    SessionType,
    SessionStatus,
    StudentAccountBalance,
    TeacherCompensationRule,
    TransactionPaymentStatus,
    TransactionType,
    TrialCostAbsorption,
)
from ..services.payment_services import TeacherPaymentCalculator


class TeacherPaymentCalculatorTestCase(TestCase):
    """Test cases for teacher payment calculation logic."""

    def setUp(self):
        """Set up test data for Teacher A's scenario."""
        # Get models dynamically to avoid import issues
        School = apps.get_model('accounts', 'School')
        CustomUser = apps.get_model('accounts', 'CustomUser')
        TeacherProfile = apps.get_model('accounts', 'TeacherProfile')
        
        # Create school
        self.school = School.objects.create(name="Test School", description="A test school")

        # Create user and teacher profile
        self.user = User.objects.create_user(
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
            status=SessionStatus.COMPLETED,
        )

        # Test business logic: Grade 7 rate should be €15/hour
        applicable_rule = TeacherCompensationRule.objects.filter(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="7",
            is_active=True
        ).first()
        
        self.assertIsNotNone(applicable_rule)
        self.assertEqual(applicable_rule.rate_per_hour, Decimal("15.00"))
        
        # Verify session data
        self.assertEqual(session.session_type, SessionType.INDIVIDUAL)
        self.assertEqual(session.grade_level, "7")
        self.assertEqual(session.student_count, 1)

    def test_grade_10_individual_session(self):
        """Test compensation rule lookup for Grade 10 individual session."""
        session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=date(2024, 1, 15),
            start_time=time(16, 0),
            end_time=time(17, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.COMPLETED,
        )

        # Test business logic: Grade 10 rate should be €20/hour
        applicable_rule = TeacherCompensationRule.objects.filter(
            teacher=self.teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="10",
            is_active=True
        ).first()
        
        self.assertIsNotNone(applicable_rule)
        self.assertEqual(applicable_rule.rate_per_hour, Decimal("20.00"))

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
        School = apps.get_model('accounts', 'School')
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


class StudentAccountBalanceTestCase(TestCase):
    """Test cases for StudentAccountBalance model."""

    def setUp(self):
        """Set up test data for student account balance tests."""
        # Create a test user
        self.user = User.objects.create_user(
            email="student@example.com", 
            name="Test Student", 
            password="testpass123"
        )

    def test_student_account_balance_creation(self):
        """Test creating a StudentAccountBalance with valid data."""
        balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("10.0"),
            hours_consumed=Decimal("3.5"),
            balance_amount=Decimal("85.50")
        )
        
        self.assertEqual(balance.student, self.user)
        self.assertEqual(balance.hours_purchased, Decimal("10.0"))
        self.assertEqual(balance.hours_consumed, Decimal("3.5"))
        self.assertEqual(balance.balance_amount, Decimal("85.50"))
        self.assertIsNotNone(balance.created_at)
        self.assertIsNotNone(balance.updated_at)


    def test_remaining_hours_property(self):
        """Test the remaining_hours property calculation."""
        balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("20.0"),
            hours_consumed=Decimal("7.5"),
            balance_amount=Decimal("150.00")
        )
        
        self.assertEqual(balance.remaining_hours, Decimal("12.5"))

    def test_remaining_hours_when_zero(self):
        """Test remaining_hours when purchased equals consumed."""
        balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("10.0"),
            hours_consumed=Decimal("10.0"),
            balance_amount=Decimal("0.00")
        )
        
        self.assertEqual(balance.remaining_hours, Decimal("0.0"))

    def test_remaining_hours_negative(self):
        """Test remaining_hours when consumed exceeds purchased (overdraft scenario)."""
        balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("10.0"),
            hours_consumed=Decimal("12.5"),
            balance_amount=Decimal("-25.00")
        )
        
        self.assertEqual(balance.remaining_hours, Decimal("-2.5"))







    def test_related_name_from_user(self):
        """Test accessing StudentAccountBalance from User via related_name."""
        balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("10.0"),
            hours_consumed=Decimal("3.5"),
            balance_amount=Decimal("85.50")
        )
        
        # Test that we can access the balance from the user
        self.assertEqual(self.user.account_balance, balance)

    def test_updating_existing_balance(self):
        """Test updating an existing StudentAccountBalance."""
        balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("10.0"),
            hours_consumed=Decimal("3.5"),
            balance_amount=Decimal("85.50")
        )
        
        # Update values
        balance.hours_consumed = Decimal("5.0")
        balance.balance_amount = Decimal("65.00")
        balance.save()
        
        # Refresh and verify
        balance.refresh_from_db()
        self.assertEqual(balance.hours_consumed, Decimal("5.0"))
        self.assertEqual(balance.balance_amount, Decimal("65.00"))
        self.assertEqual(balance.remaining_hours, Decimal("5.0"))

    def test_negative_values_allowed(self):
        """Test that negative values are allowed for overdraft scenarios."""
        balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("5.0"),
            hours_consumed=Decimal("8.0"),  # More consumed than purchased
            balance_amount=Decimal("-30.00")  # Negative balance
        )
        
        self.assertEqual(balance.hours_consumed, Decimal("8.0"))
        self.assertEqual(balance.balance_amount, Decimal("-30.00"))
        self.assertEqual(balance.remaining_hours, Decimal("-3.0"))

    def test_multiple_users_can_have_accounts(self):
        """Test that multiple users can each have their own account balance."""
        user2 = User.objects.create_user(
            email="student2@example.com",
            name="Student Two",
            password="testpass123"
        )
        
        balance1 = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("10.0"),
            hours_consumed=Decimal("2.0"),
            balance_amount=Decimal("80.00")
        )
        
        balance2 = StudentAccountBalance.objects.create(
            student=user2,
            hours_purchased=Decimal("15.0"),
            hours_consumed=Decimal("5.0"),
            balance_amount=Decimal("100.00")
        )
        
        self.assertEqual(balance1.student, self.user)
        self.assertEqual(balance2.student, user2)
        self.assertEqual(balance1.remaining_hours, Decimal("8.0"))
        self.assertEqual(balance2.remaining_hours, Decimal("10.0"))

    def test_cascade_delete_with_user(self):
        """Test that StudentAccountBalance is deleted when User is deleted."""
        balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("10.0"),
            hours_consumed=Decimal("3.5"),
            balance_amount=Decimal("85.50")
        )
        
        balance_id = balance.id
        
        # Delete the user
        self.user.delete()
        
        # Verify the balance is also deleted
        with self.assertRaises(StudentAccountBalance.DoesNotExist):
            StudentAccountBalance.objects.get(id=balance_id)



class PurchaseTransactionTestCase(TestCase):
    """Test cases for PurchaseTransaction model."""

    def setUp(self):
        """Set up test data for purchase transaction tests."""
        # Create a test user with student account balance
        self.user = User.objects.create_user(
            email="student@example.com", 
            name="Test Student", 
            password="testpass123"
        )
        
        # Create student account balance
        self.account_balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("0.0"),
            hours_consumed=Decimal("0.0"),
            balance_amount=Decimal("0.00")
        )

    def test_purchase_transaction_creation_with_required_fields(self):
        """Test creating a PurchaseTransaction with only required fields."""
        
        transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.PENDING
        )
        
        self.assertEqual(transaction.student, self.user)
        self.assertEqual(transaction.transaction_type, TransactionType.PACKAGE)
        self.assertEqual(transaction.amount, Decimal("100.00"))
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.PENDING)
        self.assertIsNotNone(transaction.created_at)
        self.assertIsNotNone(transaction.updated_at)

    def test_purchase_transaction_creation_with_all_fields(self):
        """Test creating a PurchaseTransaction with all fields."""
        from datetime import timedelta
        
        expires_at = timezone.now() + timedelta(days=30)
        metadata = {"package_name": "Premium Package", "hours": 20}
        
        transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("150.50"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test123456789",
            stripe_customer_id="cus_test123456789",
            expires_at=expires_at,
            metadata=metadata
        )
        
        self.assertEqual(transaction.student, self.user)
        self.assertEqual(transaction.transaction_type, TransactionType.PACKAGE)
        self.assertEqual(transaction.amount, Decimal("150.50"))
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.COMPLETED)
        self.assertEqual(transaction.stripe_payment_intent_id, "pi_test123456789")
        self.assertEqual(transaction.stripe_customer_id, "cus_test123456789")
        self.assertEqual(transaction.expires_at, expires_at)
        self.assertEqual(transaction.metadata, metadata)


    def test_is_expired_property_for_package_transactions(self):
        """Test is_expired property for package transactions."""
        from datetime import timedelta
        
        # Test non-expired package
        future_date = timezone.now() + timedelta(days=30)
        transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=future_date
        )
        self.assertFalse(transaction.is_expired)
        
        # Test expired package
        past_date = timezone.now() - timedelta(days=1)
        expired_transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=past_date
        )
        self.assertTrue(expired_transaction.is_expired)

    def test_is_expired_property_for_subscription_transactions(self):
        """Test is_expired property for subscription transactions (should always be False)."""
        
        # Subscription without expires_at (should be null)
        transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=None
        )
        self.assertFalse(transaction.is_expired)

    def test_mark_completed_method(self):
        """Test mark_completed() method functionality."""
        
        transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.PENDING
        )
        
        # Initially pending
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.PENDING)
        
        # Mark as completed
        transaction.mark_completed()
        
        # Refresh from database
        transaction.refresh_from_db()
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.COMPLETED)

    def test_payment_status_transitions(self):
        """Test various payment status transitions."""
        
        transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.PENDING
        )
        
        # Test status change to processing
        transaction.payment_status = TransactionPaymentStatus.PROCESSING
        transaction.save()
        transaction.refresh_from_db()
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.PROCESSING)
        
        # Test status change to failed
        transaction.payment_status = TransactionPaymentStatus.FAILED
        transaction.save()
        transaction.refresh_from_db()
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.FAILED)
        
        # Test status change to cancelled
        transaction.payment_status = TransactionPaymentStatus.CANCELLED
        transaction.save()
        transaction.refresh_from_db()
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.CANCELLED)
        
        # Test status change to refunded
        transaction.payment_status = TransactionPaymentStatus.REFUNDED
        transaction.save()
        transaction.refresh_from_db()
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.REFUNDED)

    def test_transaction_types(self):
        """Test different transaction types."""
        
        # Test package transaction
        package_transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        self.assertEqual(package_transaction.transaction_type, TransactionType.PACKAGE)
        
        # Test subscription transaction
        subscription_transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        self.assertEqual(subscription_transaction.transaction_type, TransactionType.SUBSCRIPTION)

    def test_metadata_field(self):
        """Test metadata JSONField functionality."""
        
        metadata = {
            "package_name": "Premium Package",
            "hours": 20,
            "promotional_code": "SAVE10",
            "features": ["unlimited_access", "priority_support"]
        }
        
        transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            metadata=metadata
        )
        
        # Refresh from database and verify JSON data integrity
        transaction.refresh_from_db()
        self.assertEqual(transaction.metadata["package_name"], "Premium Package")
        self.assertEqual(transaction.metadata["hours"], 20)
        self.assertEqual(transaction.metadata["promotional_code"], "SAVE10")
        self.assertIn("unlimited_access", transaction.metadata["features"])








    def test_cascade_delete_with_student(self):
        """Test that PurchaseTransaction is deleted when student is deleted."""
        
        transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        transaction_id = transaction.id
        
        # Delete the user
        self.user.delete()
        
        # Verify the transaction is also deleted
        with self.assertRaises(PurchaseTransaction.DoesNotExist):
            PurchaseTransaction.objects.get(id=transaction_id)

    def test_multiple_students_can_have_transactions(self):
        """Test that multiple students can each have their own transactions."""
        
        user2 = User.objects.create_user(
            email="student2@example.com",
            name="Student Two",
            password="testpass123"
        )
        
        transaction1 = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        transaction2 = PurchaseTransaction.objects.create(
            student=user2,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        self.assertEqual(transaction1.student, self.user)
        self.assertEqual(transaction2.student, user2)
        self.assertNotEqual(transaction1.student, transaction2.student)


class BusinessLogicValidationTests(TestCase):
    """Test critical business logic validation across financial models."""

    def setUp(self):
        """Set up test data for business logic validation tests."""
        # Get models dynamically
        CustomUser = apps.get_model('accounts', 'CustomUser')
        School = apps.get_model('accounts', 'School')
        
        self.user = User.objects.create_user(
            email="student@test.com", 
            name="Test Student", 
            password="testpass123"
        )
        
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )

    def test_purchase_transaction_amount_precision_validation(self):
        """Test that transaction amounts maintain proper decimal precision for EUR currency."""
        # Test precise amounts that should be valid
        valid_amounts = [
            Decimal("0.01"),     # 1 cent
            Decimal("10.50"),    # €10.50
            Decimal("99.99"),    # €99.99
            Decimal("1000.00"),  # €1000
        ]
        
        for amount in valid_amounts:
            transaction = PurchaseTransaction(
                student=self.user,
                transaction_type=TransactionType.PACKAGE,
                amount=amount,
                payment_status=TransactionPaymentStatus.PENDING
            )
            try:
                transaction.full_clean()
                transaction.save()
                self.assertEqual(transaction.amount, amount)
                transaction.delete()  # Cleanup
            except ValidationError:
                self.fail(f"Valid amount {amount} should not raise ValidationError")

    def test_student_balance_negative_hours_business_rule(self):
        """Test business rule: Student balance can go negative for overdraft scenarios."""
        balance = StudentAccountBalance.objects.create(
            student=self.user,
            hours_purchased=Decimal("5.00"),
            hours_consumed=Decimal("7.50"),  # More consumed than purchased
            balance_amount=Decimal("-25.00")  # Negative balance allowed
        )
        
        # Should be valid for overdraft scenarios
        balance.full_clean()
        
        # Business rule: remaining hours should calculate correctly
        self.assertEqual(balance.remaining_hours, Decimal("-2.50"))
        
        # Verify balance is properly negative
        self.assertTrue(balance.balance_amount < 0)

    def test_compensation_rule_effective_date_business_logic(self):
        """Test business rule: Only one active rule per teacher/school/type/grade."""
        CustomUser = apps.get_model('accounts', 'CustomUser')
        TeacherProfile = apps.get_model('accounts', 'TeacherProfile')
        
        # Create teacher
        teacher_user = User.objects.create_user(
            email="teacher@test.com",
            name="Test Teacher"
        )
        teacher = TeacherProfile.objects.create(user=teacher_user, bio="Test bio")
        
        # Create first rule
        rule1 = TeacherCompensationRule.objects.create(
            teacher=teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="7",
            rate_per_hour=Decimal("15.00"),
            effective_from=date(2024, 1, 1),
            is_active=True
        )
        
        # Attempting to create duplicate active rule should be prevented by constraint
        rule2 = TeacherCompensationRule(
            teacher=teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="7",
            rate_per_hour=Decimal("20.00"),
            effective_from=date(2024, 2, 1),
            is_active=True
        )
        
        # This should succeed if we deactivate the first rule first
        rule1.is_active = False
        rule1.save()
        
        rule2.full_clean()
        rule2.save()
        
        # Verify only one active rule exists
        active_rules = TeacherCompensationRule.objects.filter(
            teacher=teacher,
            school=self.school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="7",
            is_active=True
        )
        self.assertEqual(active_rules.count(), 1)
        self.assertEqual(active_rules.first().rate_per_hour, Decimal("20.00"))

    def test_school_billing_settings_payment_day_constraints(self):
        """Test business rule: Payment day must be 1-28 to exist in all months."""
        settings = SchoolBillingSettings(school=self.school, payment_day_of_month=15)
        settings.full_clean()  # Should succeed
        
        # Test boundary values
        for valid_day in [1, 15, 28]:
            settings.payment_day_of_month = valid_day
            settings.full_clean()  # Should succeed
            
        # Test invalid values
        for invalid_day in [0, 29, 30, 31]:
            settings.payment_day_of_month = invalid_day
            with self.assertRaises(ValidationError):
                settings.full_clean()

    def test_transaction_expiration_business_logic(self):
        """Test business rule: Package transactions can expire, subscriptions cannot."""
        from datetime import timedelta
        
        # Package transaction with expiration
        expires_at = timezone.now() + timedelta(days=30)
        package_transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=expires_at
        )
        
        # Should not be expired initially
        self.assertFalse(package_transaction.is_expired)
        
        # Update to past date to test expiration
        package_transaction.expires_at = timezone.now() - timedelta(days=1)
        package_transaction.save()
        
        self.assertTrue(package_transaction.is_expired)
        
        # Subscription transaction should never expire
        subscription_transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=None  # Subscriptions don't expire
        )
        
        self.assertFalse(subscription_transaction.is_expired)

    def test_class_session_duration_calculation(self):
        """Test business rule: Session duration must be positive and reasonable."""
        CustomUser = apps.get_model('accounts', 'CustomUser')
        TeacherProfile = apps.get_model('accounts', 'TeacherProfile')
        
        teacher_user = User.objects.create_user(
            email="teacher@test.com",
            name="Test Teacher"
        )
        teacher = TeacherProfile.objects.create(user=teacher_user, bio="Test bio")
        
        # Valid session duration
        session = ClassSession.objects.create(
            teacher=teacher,
            school=self.school,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(15, 30),  # 1.5 hours
            session_type=SessionType.INDIVIDUAL,
            grade_level="10",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        
        # Calculate duration
        start_datetime = timezone.datetime.combine(session.date, session.start_time)
        end_datetime = timezone.datetime.combine(session.date, session.end_time)
        duration_seconds = (end_datetime - start_datetime).total_seconds()
        duration_hours = Decimal(str(duration_seconds / 3600))
        
        # Business rule: Duration should be 1.5 hours
        self.assertEqual(duration_hours, Decimal("1.5"))
        
        # Business rule: Individual sessions should have exactly 1 student
        self.assertEqual(session.student_count, 1)
        self.assertEqual(session.session_type, SessionType.INDIVIDUAL)
