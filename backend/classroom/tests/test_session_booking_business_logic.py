"""
Unit tests for Session Booking business logic.

Tests core business rules for session booking without API endpoints:
- Hour deduction validation and FIFO consumption rules
- Session capacity validation rules
- Teacher availability and timing conflict detection
- Booking eligibility business logic
- Session adjustment and refund algorithms
- Cancellation and refund processing

These tests focus on the business logic that needs fixes for GitHub Issue #173.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from classroom.services.session_booking_service import (
    SessionBookingService,
    SessionBookingError,
    SessionCapacityError,
    SessionTimingError
)
from finances.services.hour_deduction_service import (
    HourDeductionService,
    InsufficientBalanceError,
    PackageExpiredError
)
from finances.models import (
    ClassSession,
    StudentAccountBalance,
    PurchaseTransaction,
    HourConsumption,
    SessionStatus,
    TransactionPaymentStatus
)
from accounts.models import CustomUser


class SessionCapacityValidationTest(TestCase):
    """Test session capacity validation business rules."""

    def test_individual_session_valid_capacity(self):
        """Test individual session allows exactly 1 student."""
        # Should not raise exception
        SessionBookingService._validate_session_capacity("individual", 1)

    def test_individual_session_no_students(self):
        """Test individual session rejects 0 students."""
        with self.assertRaises(SessionCapacityError) as cm:
            SessionBookingService._validate_session_capacity("individual", 0)
        
        self.assertIn("exactly 1 student", str(cm.exception))

    def test_individual_session_multiple_students(self):
        """Test individual session rejects multiple students."""
        with self.assertRaises(SessionCapacityError) as cm:
            SessionBookingService._validate_session_capacity("individual", 3)
        
        self.assertIn("exactly 1 student", str(cm.exception))

    def test_group_session_valid_capacity(self):
        """Test group session allows multiple students."""
        # Should not raise exception
        SessionBookingService._validate_session_capacity("group", 3)
        SessionBookingService._validate_session_capacity("group", 10)

    def test_group_session_insufficient_students(self):
        """Test group session rejects single student."""
        with self.assertRaises(SessionCapacityError) as cm:
            SessionBookingService._validate_session_capacity("group", 1)
        
        self.assertIn("at least 2 students", str(cm.exception))

    def test_session_capacity_maximum_limit(self):
        """Test session capacity maximum limit enforcement."""
        with self.assertRaises(SessionCapacityError) as cm:
            SessionBookingService._validate_session_capacity("group", 15)
        
        self.assertIn("more than 10 students", str(cm.exception))

    def test_session_capacity_boundary_values(self):
        """Test boundary values for session capacity."""
        # These should not raise exceptions
        SessionBookingService._validate_session_capacity("group", 2)  # Min group
        SessionBookingService._validate_session_capacity("group", 10)  # Max allowed


class TeacherAvailabilityValidationTest(TestCase):
    """Test teacher availability validation business rules."""

    def setUp(self):
        """Set up test data."""
        self.teacher = Mock()
        self.teacher.id = 1

    @patch('classroom.services.session_booking_service.ClassSession.objects.filter')
    def test_teacher_availability_no_conflicts(self, mock_filter):
        """Test teacher availability when no conflicts exist."""
        mock_filter.return_value.exclude.return_value.exclude.return_value.exists.return_value = False
        
        # Should not raise exception
        SessionBookingService._validate_teacher_availability(
            self.teacher, "2024-03-15", "14:00:00", "15:00:00"
        )

    @patch('classroom.services.session_booking_service.ClassSession.objects.filter')
    def test_teacher_availability_conflict_detected(self, mock_filter):
        """Test teacher availability conflict detection."""
        mock_filter.return_value.exclude.return_value.exclude.return_value.exists.return_value = True
        
        with self.assertRaises(SessionTimingError) as cm:
            SessionBookingService._validate_teacher_availability(
                self.teacher, "2024-03-15", "14:00:00", "15:00:00"
            )
        
        self.assertIn("conflicting session", str(cm.exception))

    @patch('classroom.services.session_booking_service.ClassSession.objects.filter')
    def test_teacher_availability_query_filters(self, mock_filter):
        """Test teacher availability query uses correct filters."""
        mock_queryset = Mock()
        mock_exclude1 = Mock()
        mock_exclude2 = Mock()
        
        mock_filter.return_value = mock_queryset
        mock_queryset.exclude.return_value = mock_exclude1
        mock_exclude1.exclude.return_value = mock_exclude2
        mock_exclude2.exists.return_value = False
        
        SessionBookingService._validate_teacher_availability(
            self.teacher, "2024-03-15", "14:00:00", "15:00:00"
        )
        
        # Verify filter was called with correct parameters
        mock_filter.assert_called_once()
        call_kwargs = mock_filter.call_args[1]
        self.assertEqual(call_kwargs['teacher'], self.teacher)
        self.assertEqual(call_kwargs['date'], "2024-03-15")
        self.assertIn('status__in', call_kwargs)

    @patch('classroom.services.session_booking_service.ClassSession.objects.filter')
    def test_teacher_availability_time_exclusions(self, mock_filter):
        """Test teacher availability excludes non-overlapping sessions correctly."""
        mock_queryset = Mock()
        mock_filter.return_value = mock_queryset
        mock_queryset.exclude.return_value = mock_queryset
        mock_queryset.exists.return_value = False
        
        SessionBookingService._validate_teacher_availability(
            self.teacher, "2024-03-15", "14:00:00", "15:00:00"
        )
        
        # Should exclude sessions that end before start time and start after end time
        self.assertEqual(mock_queryset.exclude.call_count, 2)


class HourDeductionValidationTest(TestCase):
    """Test hour deduction validation business rules."""

    def setUp(self):
        """Set up test data."""
        self.student = Mock()
        self.student.id = 1
        self.student.name = "Test Student"

    @patch('finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create')
    def test_validate_student_balance_sufficient_hours(self, mock_get_or_create):
        """Test validation passes when student has sufficient hours."""
        balance = Mock()
        balance.remaining_hours = Decimal('5.00')
        mock_get_or_create.return_value = (balance, False)
        
        with patch('finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student', return_value=[Mock()]):
            # Should not raise exception
            HourDeductionService._validate_student_balance(self.student, Decimal('3.00'))

    @patch('finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create')
    def test_validate_student_balance_insufficient_hours(self, mock_get_or_create):
        """Test validation fails when student has insufficient hours."""
        balance = Mock()
        balance.remaining_hours = Decimal('2.00')
        mock_get_or_create.return_value = (balance, False)
        
        with patch('finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student', return_value=[Mock()]):
            with self.assertRaises(InsufficientBalanceError) as cm:
                HourDeductionService._validate_student_balance(self.student, Decimal('5.00'))
            
            self.assertIn("insufficient balance", str(cm.exception))
            self.assertIn("Required: 5.00h", str(cm.exception))
            self.assertIn("Available: 2.00h", str(cm.exception))

    @patch('finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create')
    @patch('finances.services.hour_deduction_service.PurchaseTransaction.objects.filter')
    def test_validate_student_balance_no_active_packages_with_expired(self, mock_filter, mock_get_or_create):
        """Test validation fails when student has expired packages."""
        balance = Mock()
        balance.remaining_hours = Decimal('5.00')
        mock_get_or_create.return_value = (balance, False)
        
        # Mock has packages but none active
        mock_filter.return_value.exists.return_value = True
        
        with patch('finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student', return_value=[]):
            with self.assertRaises(PackageExpiredError) as cm:
                HourDeductionService._validate_student_balance(self.student, Decimal('3.00'))
            
            self.assertIn("no active packages", str(cm.exception))
            self.assertIn("all packages have expired", str(cm.exception))

    @patch('finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create')
    @patch('finances.services.hour_deduction_service.PurchaseTransaction.objects.filter')
    def test_validate_student_balance_no_packages_purchased(self, mock_filter, mock_get_or_create):
        """Test validation fails when student has no packages."""
        balance = Mock()
        balance.remaining_hours = Decimal('0.00')
        mock_get_or_create.return_value = (balance, False)
        
        # Mock has no packages at all
        mock_filter.return_value.exists.return_value = False
        
        with patch('finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student', return_value=[]):
            with self.assertRaises(InsufficientBalanceError) as cm:
                HourDeductionService._validate_student_balance(self.student, Decimal('3.00'))
            
            self.assertIn("no tutoring packages purchased", str(cm.exception))


class FIFOConsumptionRulesTest(TestCase):
    """Test FIFO (First In, First Out) consumption business rules."""

    def setUp(self):
        """Set up test data."""
        self.student = Mock()
        self.student.id = 1

    @patch('finances.services.hour_deduction_service.PurchaseTransaction.objects.filter')
    def test_get_active_packages_fifo_ordering(self, mock_filter):
        """Test active packages are returned in FIFO order."""
        # Create mock packages with different creation dates
        package1 = Mock()
        package1.created_at = timezone.now() - timedelta(days=10)
        
        package2 = Mock()
        package2.created_at = timezone.now() - timedelta(days=5)
        
        package3 = Mock()
        package3.created_at = timezone.now() - timedelta(days=1)
        
        mock_queryset = Mock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.order_by.return_value = [package1, package2, package3]
        mock_filter.return_value = mock_queryset
        
        result = HourDeductionService._get_active_packages_for_student(self.student)
        
        # Verify ordering by created_at (FIFO)
        mock_queryset.order_by.assert_called_with('created_at')
        self.assertEqual(result, [package1, package2, package3])

    @patch('finances.services.hour_deduction_service.PurchaseTransaction.objects.filter')
    def test_get_active_packages_expiration_filter(self, mock_filter):
        """Test active packages filter excludes expired packages."""
        mock_queryset = Mock()
        mock_filter.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.order_by.return_value = []
        
        HourDeductionService._get_active_packages_for_student(self.student)
        
        # Verify expiration filtering
        filter_calls = mock_queryset.filter.call_args_list
        self.assertTrue(any('expires_at' in str(call) for call in filter_calls))

    @patch('finances.services.hour_deduction_service.StudentAccountBalance.objects.get')
    def test_deduct_hours_uses_oldest_package(self, mock_balance_get):
        """Test hour deduction uses oldest package (FIFO)."""
        session = Mock()
        balance = Mock()
        mock_balance_get.return_value = balance
        
        # Mock oldest package
        oldest_package = Mock()
        oldest_package.id = 1
        
        newer_package = Mock()
        newer_package.id = 2
        
        with patch('finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student', return_value=[oldest_package, newer_package]):
            with patch('finances.services.hour_deduction_service.HourConsumption.objects.create') as mock_create:
                HourDeductionService._deduct_hours_for_student(
                    self.student, session, Decimal('2.00')
                )
                
                # Verify consumption record uses oldest package
                mock_create.assert_called_once()
                create_kwargs = mock_create.call_args[1]
                self.assertEqual(create_kwargs['purchase_transaction'], oldest_package)


class BookingEligibilityLogicTest(TestCase):
    """Test booking eligibility business logic."""

    def setUp(self):
        """Set up test data."""
        self.student = Mock()
        self.student.id = 1

    @patch('finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create')
    def test_check_booking_eligibility_sufficient_balance_and_packages(self, mock_get_or_create):
        """Test booking eligibility when student has sufficient balance and active packages."""
        balance = Mock()
        balance.remaining_hours = Decimal('10.00')
        mock_get_or_create.return_value = (balance, False)
        
        active_package = Mock()
        with patch('finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student', return_value=[active_package]):
            result = HourDeductionService.check_booking_eligibility(
                self.student, Decimal('3.00')
            )
            
            self.assertTrue(result['can_book'])
            self.assertEqual(result['hours_required'], Decimal('3.00'))
            self.assertEqual(result['hours_available'], Decimal('10.00'))
            self.assertEqual(result['hours_remaining_after'], Decimal('7.00'))
            self.assertTrue(result['has_active_packages'])
            self.assertEqual(result['active_package_count'], 1)

    @patch('finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create')
    def test_check_booking_eligibility_insufficient_hours(self, mock_get_or_create):
        """Test booking eligibility when student has insufficient hours."""
        balance = Mock()
        balance.remaining_hours = Decimal('2.00')
        mock_get_or_create.return_value = (balance, False)
        
        active_package = Mock()
        with patch('finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student', return_value=[active_package]):
            result = HourDeductionService.check_booking_eligibility(
                self.student, Decimal('5.00')
            )
            
            self.assertFalse(result['can_book'])
            self.assertEqual(result['hours_available'], Decimal('2.00'))
            self.assertIn('Insufficient hours', result['reason'])
            self.assertIn('need 5.00, have 2.00', result['reason'])

    @patch('finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create')
    def test_check_booking_eligibility_no_active_packages(self, mock_get_or_create):
        """Test booking eligibility when student has no active packages."""
        balance = Mock()
        balance.remaining_hours = Decimal('10.00')
        mock_get_or_create.return_value = (balance, False)
        
        with patch('finances.services.hour_deduction_service.HourDeductionService._get_active_packages_for_student', return_value=[]):
            result = HourDeductionService.check_booking_eligibility(
                self.student, Decimal('3.00')
            )
            
            self.assertFalse(result['can_book'])
            self.assertFalse(result['has_active_packages'])
            self.assertEqual(result['active_package_count'], 0)
            self.assertEqual(result['reason'], 'No active tutoring packages')

    @patch('finances.services.hour_deduction_service.StudentAccountBalance.objects.get_or_create')
    def test_check_booking_eligibility_exception_handling(self, mock_get_or_create):
        """Test booking eligibility exception handling."""
        mock_get_or_create.side_effect = Exception("Database error")
        
        result = HourDeductionService.check_booking_eligibility(
            self.student, Decimal('3.00')
        )
        
        self.assertFalse(result['can_book'])
        self.assertIn('Error checking eligibility', result['reason'])


class SessionAdjustmentLogicTest(TestCase):
    """Test session duration adjustment business logic."""

    def setUp(self):
        """Set up test data."""
        self.session = Mock()
        self.session.id = 1
        self.session.status = SessionStatus.COMPLETED
        self.session.is_trial = False
        self.session.duration_hours = Decimal('2.00')

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    def test_adjust_session_duration_trial_session(self, mock_get):
        """Test trial session duration adjustment doesn't affect hours."""
        self.session.is_trial = True
        mock_get.return_value = self.session
        
        result = SessionBookingService.adjust_session_duration(
            1, Decimal('2.5'), "Session ran longer"
        )
        
        self.assertEqual(result['session_id'], 1)
        self.assertEqual(result['actual_duration_hours'], '2.5')
        self.assertFalse(result['adjustment_applied'])
        self.assertIn("Trial sessions don't affect", result['reason'])

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    def test_adjust_session_duration_insufficient_difference(self, mock_get):
        """Test adjustment with insufficient duration difference."""
        mock_get.return_value = self.session
        
        # Small difference (< 0.1 hours)
        result = SessionBookingService.adjust_session_duration(
            1, Decimal('2.05'), "Minor adjustment"
        )
        
        self.assertFalse(result['adjustment_applied'])
        self.assertEqual(result['duration_difference'], '0.05')

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    @patch('finances.services.hour_deduction_service.HourDeductionService.deduct_additional_hours_for_session')
    def test_adjust_session_duration_longer_session(self, mock_deduct, mock_get):
        """Test adjustment when session ran longer."""
        mock_get.return_value = self.session
        
        # Mock additional consumption
        consumption_record = Mock()
        consumption_record.student = Mock()
        consumption_record.student.id = 1
        consumption_record.student.name = "Test Student"
        consumption_record.hours_consumed = Decimal('0.5')
        consumption_record.package = Mock()
        consumption_record.package.id = 1
        mock_deduct.return_value = [consumption_record]
        
        result = SessionBookingService.adjust_session_duration(
            1, Decimal('2.5'), "Session ran longer"
        )
        
        self.assertTrue(result['adjustment_applied'])
        self.assertEqual(result['adjustment_type'], 'additional_deduction')
        self.assertEqual(result['duration_difference'], '0.5')
        
        # Verify additional hours were deducted
        mock_deduct.assert_called_once_with(
            self.session, Decimal('0.5'), "Duration adjustment: Session ran longer"
        )

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    @patch('finances.services.hour_deduction_service.HourDeductionService.refund_excess_hours_for_session')
    def test_adjust_session_duration_shorter_session(self, mock_refund, mock_get):
        """Test adjustment when session ran shorter."""
        mock_get.return_value = self.session
        
        # Mock refund records
        refund_record = Mock()
        refund_record.student_account = Mock()
        refund_record.student_account.student = Mock()
        refund_record.student_account.student.id = 1
        refund_record.student_account.student.name = "Test Student"
        refund_record.hours_consumed = Decimal('0.3')
        refund_record.package = Mock()
        refund_record.package.id = 1
        mock_refund.return_value = [refund_record]
        
        result = SessionBookingService.adjust_session_duration(
            1, Decimal('1.7'), "Session ended early"
        )
        
        self.assertTrue(result['adjustment_applied'])
        self.assertEqual(result['adjustment_type'], 'partial_refund')
        self.assertEqual(result['duration_difference'], '-0.3')
        
        # Verify excess hours were refunded
        mock_refund.assert_called_once_with(
            self.session, Decimal('0.3'), "Duration adjustment: Session ended early"
        )

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    def test_adjust_session_duration_invalid_status(self, mock_get):
        """Test adjustment rejects non-completed sessions."""
        self.session.status = SessionStatus.SCHEDULED
        mock_get.return_value = self.session
        
        with self.assertRaises(SessionBookingError) as cm:
            SessionBookingService.adjust_session_duration(
                1, Decimal('2.5'), "Invalid adjustment"
            )
        
        self.assertIn("completed sessions", str(cm.exception))


class SessionCancellationLogicTest(TestCase):
    """Test session cancellation business logic."""

    def setUp(self):
        """Set up test data."""
        self.session = Mock()
        self.session.id = 1
        self.session.status = SessionStatus.SCHEDULED
        self.session.is_trial = False
        self.session.duration_hours = Decimal('2.00')
        self.session.notes = "Original notes"

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    @patch('finances.services.hour_deduction_service.HourDeductionService.refund_hours_for_session')
    def test_cancel_session_with_refund(self, mock_refund, mock_get):
        """Test session cancellation with hour refund."""
        mock_get.return_value = self.session
        
        # Mock refund records
        refund_record = Mock()
        refund_record.student = Mock()
        refund_record.student.id = 1
        refund_record.student.name = "Test Student"
        refund_record.hours_consumed = Decimal('2.00')
        refund_record.package = Mock()
        refund_record.package.id = 1
        mock_refund.return_value = [refund_record]
        
        result = SessionBookingService.cancel_session(1, "Teacher unavailable")
        
        self.assertEqual(result['session_id'], 1)
        self.assertEqual(result['status'], SessionStatus.CANCELLED)
        self.assertEqual(result['reason'], "Teacher unavailable")
        self.assertIsNotNone(result['cancelled_at'])
        
        # Verify refund processing
        self.assertEqual(result['refund_info']['refunded_hours'], '2.00')
        self.assertEqual(result['refund_info']['students_affected'], 1)
        
        # Verify session was updated
        self.assertEqual(self.session.status, SessionStatus.CANCELLED)
        self.assertIn("Teacher unavailable", self.session.notes)

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    def test_cancel_session_trial_no_refund(self, mock_get):
        """Test trial session cancellation without refund processing."""
        self.session.is_trial = True
        mock_get.return_value = self.session
        
        result = SessionBookingService.cancel_session(1, "Student request")
        
        self.assertEqual(result['session_id'], 1)
        
        # Trial sessions should have minimal refund info
        self.assertEqual(result['refund_info']['refunded_hours'], '0.00')
        self.assertEqual(result['refund_info']['students_affected'], 0)

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    def test_cancel_session_already_cancelled(self, mock_get):
        """Test cancellation of already cancelled session."""
        self.session.status = SessionStatus.CANCELLED
        mock_get.return_value = self.session
        
        with self.assertRaises(SessionBookingError) as cm:
            SessionBookingService.cancel_session(1, "Duplicate request")
        
        self.assertIn("already cancelled", str(cm.exception))

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    def test_cancel_session_completed_status(self, mock_get):
        """Test cancellation of completed session."""
        self.session.status = SessionStatus.COMPLETED
        mock_get.return_value = self.session
        
        with self.assertRaises(SessionBookingError) as cm:
            SessionBookingService.cancel_session(1, "Late cancellation")
        
        self.assertIn("Cannot cancel a completed session", str(cm.exception))

    @patch('classroom.services.session_booking_service.ClassSession.objects.get')
    def test_cancel_session_not_found(self, mock_get):
        """Test cancellation of non-existent session."""
        mock_get.side_effect = Exception("Session not found")
        
        with self.assertRaises(SessionBookingError) as cm:
            SessionBookingService.cancel_session(999, "Invalid session")
        
        self.assertIn("Session 999 not found", str(cm.exception))


class AdditionalHourDeductionTest(TestCase):
    """Test additional hour deduction business logic."""

    def setUp(self):
        """Set up test data."""
        self.session = Mock()
        self.session.id = 1
        
        self.student = Mock()
        self.student.id = 1
        self.student.name = "Test Student"
        
        self.session.students.all.return_value = [self.student]

    @patch('finances.services.hour_deduction_service.HourDeductionService._validate_student_balance')
    @patch('finances.services.hour_deduction_service.HourDeductionService._deduct_hours_for_student')
    def test_deduct_additional_hours_success(self, mock_deduct, mock_validate):
        """Test successful additional hour deduction."""
        # Mock consumption record
        consumption = Mock()
        consumption.refund_reason = ""
        mock_deduct.return_value = consumption
        
        result = HourDeductionService.deduct_additional_hours_for_session(
            self.session, Decimal('1.5'), "Session extended"
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], consumption)
        
        # Verify validation and deduction were called
        mock_validate.assert_called_once_with(self.student, Decimal('1.5'))
        mock_deduct.assert_called_once_with(self.student, self.session, Decimal('1.5'))

    def test_deduct_additional_hours_zero_amount(self):
        """Test additional hour deduction with zero amount."""
        result = HourDeductionService.deduct_additional_hours_for_session(
            self.session, Decimal('0.00'), "No additional hours"
        )
        
        self.assertEqual(result, [])

    def test_deduct_additional_hours_negative_amount(self):
        """Test additional hour deduction with negative amount."""
        result = HourDeductionService.deduct_additional_hours_for_session(
            self.session, Decimal('-0.5'), "Invalid amount"
        )
        
        self.assertEqual(result, [])


class ExcessHourRefundTest(TestCase):
    """Test excess hour refund business logic."""

    def setUp(self):
        """Set up test data."""
        self.session = Mock()
        self.session.id = 1

    @patch('finances.services.hour_deduction_service.HourConsumption.objects.filter')
    def test_refund_excess_hours_success(self, mock_filter):
        """Test successful excess hour refund."""
        # Mock consumption record
        consumption = Mock()
        consumption.hours_consumed = Decimal('2.00')
        consumption.student_account = Mock()
        consumption.student_account.hours_consumed = Decimal('10.00')
        consumption.student_account.student = Mock()
        consumption.student_account.student.name = "Test Student"
        consumption.package = Mock()
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value = [consumption]
        mock_filter.return_value = mock_queryset
        
        result = HourDeductionService.refund_excess_hours_for_session(
            self.session, Decimal('1.5'), "Session ended early"
        )
        
        self.assertEqual(len(result), 1)
        
        # Verify balance was updated (reduced by refund amount)
        self.assertEqual(consumption.student_account.hours_consumed, Decimal('8.5'))
        
        # Verify consumption record was updated
        self.assertEqual(consumption.hours_consumed, Decimal('0.5'))
        consumption.save.assert_called()

    @patch('finances.services.hour_deduction_service.HourConsumption.objects.filter')
    def test_refund_excess_hours_full_refund(self, mock_filter):
        """Test excess hour refund that fully refunds consumption."""
        consumption = Mock()
        consumption.hours_consumed = Decimal('1.00')
        consumption.student_account = Mock()
        consumption.student_account.hours_consumed = Decimal('10.00')
        consumption.student_account.student = Mock()
        consumption.student_account.student.name = "Test Student"
        consumption.package = Mock()
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value = [consumption]
        mock_filter.return_value = mock_queryset
        
        result = HourDeductionService.refund_excess_hours_for_session(
            self.session, Decimal('1.5'), "Large refund"
        )
        
        # Should fully refund the 1.00 hours
        self.assertEqual(consumption.hours_consumed, Decimal('0.00'))
        self.assertTrue(consumption.is_refunded)

    def test_refund_excess_hours_zero_amount(self):
        """Test excess hour refund with zero amount."""
        result = HourDeductionService.refund_excess_hours_for_session(
            self.session, Decimal('0.00'), "No refund"
        )
        
        self.assertEqual(result, [])