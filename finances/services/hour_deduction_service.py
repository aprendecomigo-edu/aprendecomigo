"""
Hour deduction service for session booking integration.

This service handles the core business logic for deducting tutoring hours from student
accounts when sessions are booked, including validation, FIFO consumption from packages,
and refund processing for cancellations.

Following GitHub Issue #32: "Implement Session Booking Hour Deduction"
"""

from decimal import Decimal
import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from finances.models import (
    ClassSession,
    HourConsumption,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
)

logger = logging.getLogger(__name__)


class InsufficientBalanceError(ValidationError):
    """Raised when student has insufficient hours for session booking."""

    pass


class PackageExpiredError(ValidationError):
    """Raised when student's packages have expired."""

    pass


class HourDeductionService:
    """Service for managing hour deduction and refund operations."""

    @staticmethod
    def validate_and_deduct_hours_for_session(session: ClassSession) -> list[HourConsumption]:
        """
        Validate student balances and deduct hours for a new session.

        This is the main entry point for session booking hour deduction.
        It validates all students have sufficient balance, then deducts hours
        atomically for all students.

        Args:
            session: The ClassSession object to process

        Returns:
            List[HourConsumption]: Created consumption records

        Raises:
            InsufficientBalanceError: If any student has insufficient balance
            PackageExpiredError: If student packages have expired
            ValidationError: For other validation errors
        """
        # Skip trial sessions
        if session.is_trial:
            logger.info(f"Skipping hour deduction for trial session {session.id}")
            return []

        # Skip sessions with no students
        students = list(session.students.all())
        if not students:
            logger.info(f"Skipping hour deduction for session {session.id} with no students")
            return []

        # Calculate session duration in hours
        session_hours = session.duration_hours
        if session_hours <= Decimal("0.00"):
            raise ValidationError("Session duration must be greater than 0")

        # Validate all students have sufficient balance
        HourDeductionService._validate_all_students_balance(students, session_hours)

        # Deduct hours atomically for all students
        with transaction.atomic():
            consumption_records = []
            for student in students:
                consumption = HourDeductionService._deduct_hours_for_student(student, session, session_hours)
                consumption_records.append(consumption)

            logger.info(
                f"Successfully deducted {session_hours} hours for {len(students)} students in session {session.id}"
            )

        return consumption_records

    @staticmethod
    def _validate_all_students_balance(students: list, required_hours: Decimal) -> None:
        """
        Validate that all students have sufficient balance for the session.

        Args:
            students: List of student users
            required_hours: Hours required for the session

        Raises:
            InsufficientBalanceError: If any student has insufficient balance
            PackageExpiredError: If any student has expired packages
        """
        for student in students:
            HourDeductionService._validate_student_balance(student, required_hours)

    @staticmethod
    def _validate_student_balance(student, required_hours: Decimal) -> None:
        """
        Validate that a specific student has sufficient balance.

        Args:
            student: Student user object
            required_hours: Hours required for the session

        Raises:
            InsufficientBalanceError: If student has insufficient balance
            PackageExpiredError: If student has expired packages
        """
        # Get or create student balance
        balance, _created = StudentAccountBalance.objects.get_or_create(
            student=student,
            defaults={
                "hours_purchased": Decimal("0.00"),
                "hours_consumed": Decimal("0.00"),
                "balance_amount": Decimal("0.00"),
            },
        )

        # Check if student has any remaining hours
        remaining_hours = balance.remaining_hours
        if remaining_hours < required_hours:
            raise InsufficientBalanceError(
                f"Student {student.name} has insufficient balance. "
                f"Required: {required_hours}h, Available: {remaining_hours}h"
            )

        # Check if student has any active (non-expired) packages
        active_packages = HourDeductionService._get_active_packages_for_student(student)
        if not active_packages:
            # Check if student has any packages at all
            any_packages = PurchaseTransaction.objects.filter(
                student=student, payment_status=TransactionPaymentStatus.COMPLETED
            ).exists()

            if any_packages:
                raise PackageExpiredError(f"Student {student.name} has no active packages (all packages have expired)")
            else:
                raise InsufficientBalanceError(f"Student {student.name} has no tutoring packages purchased")

    @staticmethod
    def _get_active_packages_for_student(student) -> list[PurchaseTransaction]:
        """
        Get active (non-expired) packages for a student ordered by creation date (FIFO).

        Args:
            student: Student user object

        Returns:
            List[PurchaseTransaction]: Active packages in FIFO order
        """
        from django.db import models

        now = timezone.now()
        return list(
            PurchaseTransaction.objects.filter(student=student, payment_status=TransactionPaymentStatus.COMPLETED)
            .filter(
                # Include packages with no expiration (subscriptions) or not yet expired
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
            )
            .order_by("created_at")  # FIFO order
        )

    @staticmethod
    def _deduct_hours_for_student(student, session: ClassSession, hours: Decimal) -> HourConsumption:
        """
        Deduct hours from a specific student's account and create consumption record.

        Args:
            student: Student user object
            session: ClassSession object
            hours: Hours to deduct

        Returns:
            HourConsumption: Created consumption record
        """
        # Get student balance
        balance = StudentAccountBalance.objects.get(student=student)

        # Get the oldest active package (FIFO)
        active_packages = HourDeductionService._get_active_packages_for_student(student)
        if not active_packages:
            raise PackageExpiredError(f"No active packages found for student {student.name}")

        # Use oldest package for consumption tracking
        purchase_transaction = active_packages[0]

        # Create consumption record (this will automatically update balance via model save method)
        consumption = HourConsumption.objects.create(
            student_account=balance,
            class_session=session,
            purchase_transaction=purchase_transaction,
            hours_consumed=hours,
            hours_originally_reserved=hours,
        )

        logger.info(f"Deducted {hours} hours from {student.name}'s account (transaction {purchase_transaction.id})")

        return consumption

    @staticmethod
    def refund_hours_for_session(session: ClassSession, reason: str = "Session cancelled") -> dict:
        """
        Refund hours for a cancelled session.

        Args:
            session: ClassSession object to refund
            reason: Reason for the refund

        Returns:
            Dict: Summary of refund operation
        """
        # Get all consumption records for this session
        consumptions = HourConsumption.objects.filter(
            class_session=session,
            is_refunded=False,  # Only process non-refunded consumptions
        )

        if not consumptions.exists():
            logger.info(f"No consumption records found to refund for session {session.id}")
            return {"refunded_count": 0, "total_hours_refunded": Decimal("0.00"), "students_refunded": []}

        refund_summary = {"refunded_count": 0, "total_hours_refunded": Decimal("0.00"), "students_refunded": []}

        with transaction.atomic():
            for consumption in consumptions:
                # For session cancellation, refund all consumed hours
                refunded_hours = consumption.hours_consumed

                if refunded_hours > Decimal("0.00"):
                    # Update the student account balance
                    consumption.student_account.hours_consumed -= refunded_hours  # type: ignore[attr-defined]
                    consumption.student_account.save(update_fields=["hours_consumed", "updated_at"])  # type: ignore[attr-defined]

                    # Mark consumption as refunded
                    consumption.is_refunded = True
                    consumption.refund_reason = reason
                    consumption.save(update_fields=["is_refunded", "refund_reason", "updated_at"])

                    refund_summary["refunded_count"] += 1  # type: ignore[operator]
                    refund_summary["total_hours_refunded"] += refunded_hours
                    refund_summary["students_refunded"].append(  # type: ignore[attr-defined]
                        {"student_name": consumption.student_account.student.name, "hours_refunded": refunded_hours}  # type: ignore[attr-defined]
                    )

                    logger.info(
                        f"Refunded {refunded_hours} hours to {consumption.student_account.student.name} "  # type: ignore[attr-defined]
                        f"for session {session.id}"
                    )

        logger.info(
            f"Completed refund for session {session.id}: "
            f"{refund_summary['total_hours_refunded']} total hours refunded "
            f"to {refund_summary['refunded_count']} students"
        )

        return refund_summary

    @staticmethod
    def check_booking_eligibility(student, duration_hours: Decimal) -> dict:
        """
        Check if a student is eligible to book a session of given duration.

        Args:
            student: Student user object
            duration_hours: Required session duration in hours

        Returns:
            Dict: Eligibility information
        """
        try:
            # Get or create student balance
            balance, _created = StudentAccountBalance.objects.get_or_create(
                student=student,
                defaults={
                    "hours_purchased": Decimal("0.00"),
                    "hours_consumed": Decimal("0.00"),
                    "balance_amount": Decimal("0.00"),
                },
            )

            remaining_hours = balance.remaining_hours
            can_book = remaining_hours >= duration_hours

            # Check for active packages
            active_packages = HourDeductionService._get_active_packages_for_student(student)
            has_active_packages = len(active_packages) > 0

            result = {
                "can_book": can_book and has_active_packages,
                "hours_required": duration_hours,
                "hours_available": remaining_hours,
                "hours_remaining_after": remaining_hours - duration_hours if can_book else remaining_hours,
                "has_active_packages": has_active_packages,
                "active_package_count": len(active_packages),
            }

            # Add reason if booking is not allowed
            if not result["can_book"]:
                if not has_active_packages:
                    result["reason"] = "No active tutoring packages"
                elif remaining_hours < duration_hours:
                    result["reason"] = f"Insufficient hours (need {duration_hours}, have {remaining_hours})"
                else:
                    result["reason"] = "Unknown eligibility issue"

            return result

        except Exception as e:
            logger.error(f"Error checking booking eligibility for {student}: {e}")
            return {
                "can_book": False,
                "hours_required": duration_hours,
                "hours_available": Decimal("0.00"),
                "hours_remaining_after": Decimal("0.00"),
                "has_active_packages": False,
                "active_package_count": 0,
                "reason": f"Error checking eligibility: {e!s}",
            }

    @staticmethod
    @transaction.atomic
    def deduct_additional_hours_for_session(
        session: ClassSession, additional_hours: Decimal, reason: str = ""
    ) -> list[HourConsumption]:
        """
        Deduct additional hours for a session when duration is adjusted upward.

        Args:
            session: ClassSession object
            additional_hours: Additional hours to deduct
            reason: Reason for the additional deduction

        Returns:
            List[HourConsumption]: Created consumption records for additional hours
        """
        if additional_hours <= Decimal("0.00"):
            return []

        additional_consumption_records = []

        for student in session.students.all():
            # Validate student has sufficient balance for additional hours
            HourDeductionService._validate_student_balance(student, additional_hours)

            # Deduct additional hours
            consumption = HourDeductionService._deduct_hours_for_student(student, session, additional_hours)
            consumption.refund_reason = f"Additional hours: {reason}"
            consumption.save(update_fields=["refund_reason"])

            additional_consumption_records.append(consumption)

            logger.info(
                f"Deducted additional {additional_hours} hours from {student.name} for session {session.id}: {reason}"
            )

        return additional_consumption_records

    @staticmethod
    @transaction.atomic
    def refund_excess_hours_for_session(
        session: ClassSession, excess_hours: Decimal, reason: str = ""
    ) -> list[HourConsumption]:
        """
        Refund excess hours for a session when duration is adjusted downward.

        Args:
            session: ClassSession object
            excess_hours: Excess hours to refund
            reason: Reason for the refund

        Returns:
            List[HourConsumption]: Updated consumption records with partial refunds
        """
        if excess_hours <= Decimal("0.00"):
            return []

        # Get existing consumption records for this session
        consumptions = HourConsumption.objects.filter(session=session, is_refunded=False).select_related(  # type: ignore[misc]
            "student_account__student", "package"
        )

        updated_records = []

        for consumption in consumptions:
            if excess_hours <= Decimal("0.00"):
                break

            # Calculate refund amount (up to what was originally consumed)
            refund_amount = min(excess_hours, consumption.hours_consumed)

            if refund_amount > Decimal("0.00"):
                # Update student account balance
                consumption.student_account.hours_consumed -= refund_amount  # type: ignore[attr-defined]
                consumption.student_account.save(update_fields=["hours_consumed", "updated_at"])  # type: ignore[attr-defined]

                # Update consumption record
                consumption.hours_consumed -= refund_amount
                consumption.refund_reason = f"Partial refund: {reason}"
                consumption.save(update_fields=["hours_consumed", "refund_reason", "updated_at"])

                # If fully refunded, mark as refunded
                if consumption.hours_consumed <= Decimal("0.00"):
                    consumption.is_refunded = True
                    consumption.save(update_fields=["is_refunded"])

                updated_records.append(consumption)
                excess_hours -= refund_amount

                logger.info(
                    f"Refunded {refund_amount} excess hours to {consumption.student_account.student.name} "  # type: ignore[attr-defined]
                    f"for session {session.id}: {reason}"
                )

        return updated_records
