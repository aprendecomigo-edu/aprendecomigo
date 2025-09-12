"""
Unit tests for Session Booking business logic.

Tests core business rules for session booking without API endpoints:
- Session capacity validation rules
- Teacher availability and timing conflict detection
- Booking eligibility business logic
- Session adjustment and refund algorithms
- Cancellation and refund processing

These tests focus on business logic validation without excessive mocking.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase

from scheduler.services.session_booking_service import (
    SessionBookingError,
    SessionBookingService,
    SessionCapacityError,
    SessionTimingError,
)
from finances.services.hour_deduction_service import HourDeductionService, InsufficientBalanceError, PackageExpiredError


class SessionCapacityValidationTest(TestCase):
    """Test session capacity validation business rules."""

    def test_individual_session_requires_exactly_one_student(self):
        """Test individual session validation accepts exactly 1 student."""
        # Valid capacity
        SessionBookingService._validate_session_capacity("individual", 1)

        # Invalid capacities
        with self.assertRaises(SessionCapacityError) as cm:
            SessionBookingService._validate_session_capacity("individual", 0)
        self.assertIn("exactly 1 student", str(cm.exception))

        with self.assertRaises(SessionCapacityError) as cm:
            SessionBookingService._validate_session_capacity("individual", 2)
        self.assertIn("exactly 1 student", str(cm.exception))

    def test_group_session_requires_at_least_two_students(self):
        """Test group session validation requires at least 2 students."""
        # Valid capacities
        SessionBookingService._validate_session_capacity("group", 2)
        SessionBookingService._validate_session_capacity("group", 5)
        SessionBookingService._validate_session_capacity("group", 10)

        # Invalid capacity
        with self.assertRaises(SessionCapacityError) as cm:
            SessionBookingService._validate_session_capacity("group", 1)
        self.assertIn("at least 2 students", str(cm.exception))

    def test_session_capacity_maximum_limit_enforced(self):
        """Test session capacity cannot exceed 10 students."""
        with self.assertRaises(SessionCapacityError) as cm:
            SessionBookingService._validate_session_capacity("group", 11)
        self.assertIn("more than 10 students", str(cm.exception))

        # Individual sessions also enforce the 10 student limit (after checking for exactly 1)
        with self.assertRaises(SessionCapacityError):
            SessionBookingService._validate_session_capacity("individual", 15)


class TeacherAvailabilityValidationTest(TestCase):
    """Test teacher availability validation business rules."""

    def setUp(self):
        """Set up test data."""
        self.teacher = Mock()
        self.teacher.id = 1

    @patch("scheduler.services.session_booking_service.ClassSession.objects.filter")
    def test_teacher_availability_conflict_detection(self, mock_filter):
        """Test teacher availability properly detects conflicts."""
        # No conflicts - should succeed
        mock_filter.return_value.exclude.return_value.exclude.return_value.exists.return_value = False

        SessionBookingService._validate_teacher_availability(self.teacher, "2024-03-15", "14:00:00", "15:00:00")

        # Conflict detected - should raise error
        mock_filter.return_value.exclude.return_value.exclude.return_value.exists.return_value = True

        with self.assertRaises(SessionTimingError) as cm:
            SessionBookingService._validate_teacher_availability(self.teacher, "2024-03-15", "14:00:00", "15:00:00")
        self.assertIn("conflicting session", str(cm.exception))


class HourDeductionValidationTest(TestCase):
    """Test hour deduction validation business rules."""

    def setUp(self):
        """Set up test data."""
        self.student = Mock()
        self.student.id = 1
        self.student.name = "Test Student"

    @patch("finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create")
    def test_validate_student_balance_sufficient_vs_insufficient(self, mock_get_or_create):
        """Test validation correctly identifies sufficient vs insufficient balance."""
        balance = Mock()
        mock_get_or_create.return_value = (balance, False)

        # Sufficient balance
        balance.remaining_hours = Decimal("5.00")
        with patch(
            "finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student",
            return_value=[Mock()],
        ):
            HourDeductionService._validate_student_balance(self.student, Decimal("3.00"))

        # Insufficient balance
        balance.remaining_hours = Decimal("2.00")
        with patch(
            "finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student",
            return_value=[Mock()],
        ):
            with self.assertRaises(InsufficientBalanceError) as cm:
                HourDeductionService._validate_student_balance(self.student, Decimal("5.00"))

            self.assertIn("insufficient balance", str(cm.exception))
            self.assertIn("Required: 5.00h", str(cm.exception))
            self.assertIn("Available: 2.00h", str(cm.exception))

    @patch("finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create")
    @patch("finances.services.hour_deduction_service.PurchaseTransaction.objects.filter")
    def test_validate_student_balance_expired_packages(self, mock_filter, mock_get_or_create):
        """Test validation handles expired packages correctly."""
        balance = Mock()
        balance.remaining_hours = Decimal("5.00")
        mock_get_or_create.return_value = (balance, False)
        mock_filter.return_value.exists.return_value = True

        # Has packages but none active (all expired)
        with patch(
            "finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student",
            return_value=[],
        ):
            with self.assertRaises(PackageExpiredError) as cm:
                HourDeductionService._validate_student_balance(self.student, Decimal("3.00"))

            self.assertIn("no active packages", str(cm.exception))
            self.assertIn("all packages have expired", str(cm.exception))


class BookingEligibilityLogicTest(TestCase):
    """Test booking eligibility business logic."""

    def setUp(self):
        """Set up test data."""
        self.student = Mock()
        self.student.id = 1

    @patch("finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create")
    def test_check_booking_eligibility_scenarios(self, mock_get_or_create):
        """Test booking eligibility for different scenarios."""
        balance = Mock()
        mock_get_or_create.return_value = (balance, False)

        # Scenario 1: Eligible (sufficient balance and active packages)
        balance.remaining_hours = Decimal("10.00")
        active_package = Mock()
        with patch(
            "finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student",
            return_value=[active_package],
        ):
            result = HourDeductionService.check_booking_eligibility(self.student, Decimal("3.00"))

            self.assertTrue(result["can_book"])
            self.assertEqual(result["hours_required"], Decimal("3.00"))
            self.assertEqual(result["hours_available"], Decimal("10.00"))
            self.assertEqual(result["hours_remaining_after"], Decimal("7.00"))
            self.assertTrue(result["has_active_packages"])
            self.assertEqual(result["active_package_count"], 1)

        # Scenario 2: Insufficient hours
        balance.remaining_hours = Decimal("2.00")
        with patch(
            "finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student",
            return_value=[active_package],
        ):
            result = HourDeductionService.check_booking_eligibility(self.student, Decimal("5.00"))

            self.assertFalse(result["can_book"])
            self.assertEqual(result["hours_available"], Decimal("2.00"))
            self.assertIn("Insufficient hours", result["reason"])
            self.assertIn("need 5.00, have 2.00", result["reason"])

        # Scenario 3: No active packages
        balance.remaining_hours = Decimal("10.00")
        with patch(
            "finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student",
            return_value=[],
        ):
            result = HourDeductionService.check_booking_eligibility(self.student, Decimal("3.00"))

            self.assertFalse(result["can_book"])
            self.assertFalse(result["has_active_packages"])
            self.assertEqual(result["active_package_count"], 0)
            self.assertEqual(result["reason"], "No active tutoring packages")


class SessionAdjustmentLogicTest(TestCase):
    """Test session duration adjustment business logic."""

    def setUp(self):
        """Set up test data."""
        self.session = Mock()
        self.session.id = 1
        self.session.status = "completed"
        self.session.is_trial = False
        self.session.duration_hours = Decimal("2.00")

    @patch("scheduler.services.session_booking_service.ClassSession.objects.get")
    def test_adjust_session_duration_trial_sessions_ignored(self, mock_get):
        """Test trial session duration adjustments don't affect hours."""
        self.session.is_trial = True
        mock_get.return_value = self.session

        result = SessionBookingService.adjust_session_duration(1, Decimal("2.5"), "Session ran longer")

        self.assertEqual(result["session_id"], 1)
        self.assertEqual(result["actual_duration_hours"], "2.5")
        self.assertFalse(result["adjustment_applied"])
        self.assertIn("Trial sessions don't affect", result["reason"])

    @patch("scheduler.services.session_booking_service.ClassSession.objects.get")
    def test_adjust_session_duration_insufficient_difference_ignored(self, mock_get):
        """Test small duration differences are ignored."""
        mock_get.return_value = self.session

        # Small difference (< 0.1 hours)
        result = SessionBookingService.adjust_session_duration(1, Decimal("2.05"), "Minor adjustment")

        self.assertFalse(result["adjustment_applied"])
        self.assertEqual(result["duration_difference"], "0.05")

    @patch("scheduler.services.session_booking_service.ClassSession.objects.get")
    def test_adjust_session_duration_invalid_status_rejected(self, mock_get):
        """Test adjustment rejects non-completed sessions."""
        self.session.status = "scheduled"
        mock_get.return_value = self.session

        with self.assertRaises(SessionBookingError) as cm:
            SessionBookingService.adjust_session_duration(1, Decimal("2.5"), "Invalid adjustment")

        self.assertIn("completed sessions", str(cm.exception))


class SessionCancellationLogicTest(TestCase):
    """Test session cancellation business logic."""

    def setUp(self):
        """Set up test data."""
        self.session = Mock()
        self.session.id = 1
        self.session.status = "scheduled"
        self.session.is_trial = False
        self.session.duration_hours = Decimal("2.00")
        self.session.notes = "Original notes"

    @patch("scheduler.services.session_booking_service.ClassSession.objects.get")
    def test_cancel_session_status_validation(self, mock_get):
        """Test session cancellation validates current status."""
        # Already cancelled
        self.session.status = "cancelled"
        mock_get.return_value = self.session

        with self.assertRaises(SessionBookingError) as cm:
            SessionBookingService.cancel_session(1, "Duplicate request")
        self.assertIn("already cancelled", str(cm.exception))

        # Already completed
        self.session.status = "completed"
        mock_get.return_value = self.session

        with self.assertRaises(SessionBookingError) as cm:
            SessionBookingService.cancel_session(1, "Late cancellation")
        self.assertIn("Cannot cancel a completed session", str(cm.exception))

    @patch("scheduler.services.session_booking_service.ClassSession.objects.get")
    def test_cancel_session_not_found(self, mock_get):
        """Test cancellation handles non-existent sessions."""
        from finances.models import ClassSession

        mock_get.side_effect = ClassSession.DoesNotExist("Session not found")

        with self.assertRaises(SessionBookingError) as cm:
            SessionBookingService.cancel_session(999, "Invalid session")

        self.assertIn("Session 999 not found", str(cm.exception))


class HourDeductionEdgeCasesTest(TestCase):
    """Test edge cases in hour deduction business logic."""

    def setUp(self):
        """Set up test data."""
        self.session = Mock()
        self.session.id = 1

        self.student = Mock()
        self.student.id = 1
        self.student.name = "Test Student"

        self.session.students.all.return_value = [self.student]

    def test_deduct_additional_hours_zero_and_negative_amounts(self):
        """Test additional hour deduction handles zero and negative amounts."""
        # Zero amount
        result = HourDeductionService.deduct_additional_hours_for_session(
            self.session, Decimal("0.00"), "No additional hours"
        )
        self.assertEqual(result, [])

        # Negative amount
        result = HourDeductionService.deduct_additional_hours_for_session(
            self.session, Decimal("-0.5"), "Invalid amount"
        )
        self.assertEqual(result, [])

    def test_refund_excess_hours_zero_amount(self):
        """Test excess hour refund handles zero amount."""
        result = HourDeductionService.refund_excess_hours_for_session(self.session, Decimal("0.00"), "No refund")
        self.assertEqual(result, [])
