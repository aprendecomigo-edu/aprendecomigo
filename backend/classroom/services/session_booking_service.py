"""
Session Booking Service for classroom app.

This service handles the classroom-side operations for session booking and management,
integrating with the finances app for hour deduction logic.

Following TDD methodology and addressing code reviewer feedback for proper architecture.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import CustomUser
from finances.models import ClassSession, SessionStatus
from finances.services.hour_deduction_service import HourDeductionService

logger = logging.getLogger(__name__)


class SessionBookingError(ValidationError):
    """Base exception for session booking errors."""
    pass


class SessionCapacityError(SessionBookingError):
    """Raised when session capacity is exceeded."""
    pass


class SessionTimingError(SessionBookingError):
    """Raised when session timing conflicts occur."""
    pass


class SessionBookingService:
    """
    Service for managing session booking operations in the classroom context.
    
    This service coordinates between classroom functionality and finances integration,
    handling the complete session booking lifecycle including validation, creation,
    hour deduction, adjustments, and cancellation.
    """

    @staticmethod
    @transaction.atomic
    def book_session(
        teacher_id: int,
        school_id: int,
        date: str,
        start_time: str,
        end_time: str,
        session_type: str,
        grade_level: str,
        student_ids: List[int],
        is_trial: bool = False,
        is_makeup: bool = False,
        notes: str = ""
    ) -> Tuple[ClassSession, Dict]:
        """
        Book a new session with complete validation and hour deduction.
        
        Args:
            teacher_id: ID of the teacher
            school_id: ID of the school
            date: Session date (YYYY-MM-DD)
            start_time: Session start time (HH:MM:SS)
            end_time: Session end time (HH:MM:SS)
            session_type: Type of session (individual/group)
            grade_level: Grade level for the session
            student_ids: List of student IDs to book
            is_trial: Whether this is a trial session
            is_makeup: Whether this is a makeup session
            notes: Additional notes
            
        Returns:
            Tuple of (ClassSession instance, hour_deduction_info)
            
        Raises:
            SessionBookingError: For booking validation failures
            InsufficientBalanceError: When students lack sufficient hours
            PackageExpiredError: When student packages have expired
        """
        from accounts.models import TeacherProfile, School
        
        # Validate inputs
        try:
            teacher = TeacherProfile.objects.get(id=teacher_id)
            school = School.objects.get(id=school_id)
            students = CustomUser.objects.filter(id__in=student_ids)
        except (TeacherProfile.DoesNotExist, School.DoesNotExist):
            raise SessionBookingError("Invalid teacher or school ID")
        
        if len(students) != len(student_ids):
            raise SessionBookingError("One or more student IDs are invalid")
        
        # Validate session capacity
        SessionBookingService._validate_session_capacity(session_type, len(student_ids))
        
        # Validate teacher availability
        SessionBookingService._validate_teacher_availability(teacher, date, start_time, end_time)
        
        # Create the session
        session = ClassSession.objects.create(
            teacher=teacher,
            school=school,
            date=date,
            start_time=start_time,
            end_time=end_time,
            session_type=session_type,
            grade_level=grade_level,
            student_count=len(student_ids),
            is_trial=is_trial,
            is_makeup=is_makeup,
            status=SessionStatus.SCHEDULED,
            notes=notes,
            booking_confirmed_at=timezone.now()
        )
        
        # Add students to the session
        session.students.set(students)
        
        # Process hour deduction if not a trial session
        hour_deduction_info = {"hours_deducted": "0.00", "students_affected": 0, "consumption_records": []}
        
        if not is_trial:
            try:
                consumption_records = HourDeductionService.validate_and_deduct_hours_for_session(session)
                hour_deduction_info = {
                    "hours_deducted": f"{session.duration_hours:.2f}",
                    "students_affected": len(consumption_records),
                    "consumption_records": [
                        {
                            "student_id": record.student_account.student.id,
                            "student_name": record.student_account.student.name,
                            "hours_consumed": f"{record.hours_consumed:.2f}",
                            "package_id": record.purchase_transaction.id
                        }
                        for record in consumption_records
                    ]
                }
            except Exception as e:
                # Roll back session creation if hour deduction fails
                session.delete()
                raise
        
        logger.info(f"Session booked successfully: {session.id} for {len(student_ids)} students")
        return session, hour_deduction_info

    @staticmethod
    def _validate_session_capacity(session_type: str, student_count: int) -> None:
        """Validate session capacity based on type."""
        if session_type == "individual" and student_count != 1:
            raise SessionCapacityError("Individual sessions must have exactly 1 student")
        
        if session_type == "group" and student_count < 2:
            raise SessionCapacityError("Group sessions must have at least 2 students")
        
        if student_count > 10:  # Reasonable upper limit
            raise SessionCapacityError("Sessions cannot have more than 10 students")

    @staticmethod
    def _validate_teacher_availability(teacher, date: str, start_time: str, end_time: str) -> None:
        """Validate teacher availability for the requested time slot."""
        # Check for overlapping sessions
        overlapping_sessions = ClassSession.objects.filter(
            teacher=teacher,
            date=date,
            status__in=[SessionStatus.SCHEDULED, SessionStatus.IN_PROGRESS]
        ).exclude(
            end_time__lte=start_time
        ).exclude(
            start_time__gte=end_time
        )
        
        if overlapping_sessions.exists():
            raise SessionTimingError(f"Teacher has conflicting session at this time")

    @staticmethod
    @transaction.atomic
    def cancel_session(session_id: int, reason: str = "") -> Dict:
        """
        Cancel a session and process hour refunds.
        
        Args:
            session_id: ID of the session to cancel
            reason: Reason for cancellation
            
        Returns:
            Dictionary with cancellation details and refund information
            
        Raises:
            SessionBookingError: For cancellation validation failures
        """
        try:
            session = ClassSession.objects.get(id=session_id)
        except ClassSession.DoesNotExist:
            raise SessionBookingError(f"Session {session_id} not found")
        
        if session.status == SessionStatus.CANCELLED:
            raise SessionBookingError("Session is already cancelled")
        
        if session.status == SessionStatus.COMPLETED:
            raise SessionBookingError("Cannot cancel a completed session")
        
        old_status = session.status
        
        # Calculate refund info before changing status (since model.save() will handle refunds)
        refund_info = {"refunded_hours": "0.00", "students_affected": 0, "refund_records": []}
        
        if not session.is_trial:
            # Get consumption records to build refund info before they're processed
            from finances.models import HourConsumption
            consumption_records = list(HourConsumption.objects.filter(
                class_session=session,
                is_refunded=False
            ).select_related('student_account__student'))
            
            if consumption_records:
                total_refunded = sum(record.hours_consumed for record in consumption_records)
                refund_info = {
                    "refunded_hours": str(total_refunded),
                    "students_affected": len(consumption_records),
                    "refund_records": [
                        {
                            "student_name": record.student_account.student.name,
                            "hours_refunded": str(record.hours_consumed)
                        }
                        for record in consumption_records
                    ]
                }
        
        # Update session status (this will automatically trigger refund processing via model.save())
        session.status = SessionStatus.CANCELLED
        session.cancelled_at = timezone.now()
        if reason:
            session.notes = f"{session.notes}\nCancellation reason: {reason}".strip()
        session.save()  # This will automatically process refunds via _handle_session_status_change
        
        logger.info(f"Session {session_id} cancelled successfully")
        return {
            "session_id": session.id,
            "status": session.status,
            "cancelled_at": session.cancelled_at,
            "reason": reason,
            "refund_info": refund_info
        }

    @staticmethod
    @transaction.atomic
    def adjust_session_duration(session_id: int, actual_duration_hours: Decimal, reason: str = "") -> Dict:
        """
        Adjust session duration after completion and handle hour adjustments.
        
        Args:
            session_id: ID of the session to adjust
            actual_duration_hours: Actual duration in hours
            reason: Reason for adjustment
            
        Returns:
            Dictionary with adjustment details
            
        Raises:
            SessionBookingError: For adjustment validation failures
        """
        try:
            session = ClassSession.objects.get(id=session_id)
        except ClassSession.DoesNotExist:
            raise SessionBookingError(f"Session {session_id} not found")
        
        if session.status != SessionStatus.COMPLETED:
            raise SessionBookingError("Can only adjust duration for completed sessions")
        
        if session.is_trial:
            # Trial sessions don't affect hour consumption
            session.actual_duration_hours = actual_duration_hours
            session.save()
            return {
                "session_id": session.id,
                "actual_duration_hours": str(actual_duration_hours),
                "adjustment_applied": False,
                "reason": "Trial sessions don't affect hour consumption"
            }
        
        original_duration = session.duration_hours
        duration_difference = actual_duration_hours - original_duration
        
        # Update session with actual duration
        session.actual_duration_hours = actual_duration_hours
        if reason:
            session.notes = f"{session.notes}\nDuration adjusted: {reason}".strip()
        session.save()
        
        adjustment_info = {
            "session_id": session.id,
            "original_duration": str(original_duration),
            "actual_duration_hours": str(actual_duration_hours),
            "duration_difference": str(duration_difference),
            "adjustment_applied": False,
            "adjustment_records": []
        }
        
        # Apply hour adjustments if there's a significant difference (>= 0.1 hours)
        if abs(duration_difference) >= Decimal('0.1'):
            try:
                if duration_difference > 0:
                    # Session was longer, deduct additional hours
                    additional_consumption = HourDeductionService.deduct_additional_hours_for_session(
                        session, duration_difference, f"Duration adjustment: {reason}"
                    )
                    adjustment_info.update({
                        "adjustment_applied": True,
                        "adjustment_type": "additional_deduction",
                        "adjustment_records": [
                            {
                                "student_id": record.student.id,
                                "student_name": record.student.name,
                                "additional_hours": str(record.hours_consumed),
                                "package_id": record.package.id
                            }
                            for record in additional_consumption
                        ]
                    })
                else:
                    # Session was shorter, refund excess hours
                    refund_amount = abs(duration_difference)
                    refund_records = HourDeductionService.refund_excess_hours_for_session(
                        session, refund_amount, f"Duration adjustment: {reason}"
                    )
                    adjustment_info.update({
                        "adjustment_applied": True,
                        "adjustment_type": "partial_refund",
                        "adjustment_records": [
                            {
                                "student_id": record.student.id,
                                "student_name": record.student.name,
                                "refunded_hours": str(record.hours_consumed),
                                "package_id": record.package.id
                            }
                            for record in refund_records
                        ]
                    })
            except Exception as e:
                logger.error(f"Failed to process duration adjustment for session {session_id}: {e}")
                adjustment_info["adjustment_error"] = str(e)
        
        logger.info(f"Session {session_id} duration adjusted from {original_duration} to {actual_duration_hours}")
        return adjustment_info

    @staticmethod
    def get_session_booking_summary(session_id: int) -> Dict:
        """
        Get comprehensive booking summary for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dictionary with session and booking details
        """
        try:
            session = ClassSession.objects.select_related('teacher__user', 'school').prefetch_related('students').get(id=session_id)
        except ClassSession.DoesNotExist:
            raise SessionBookingError(f"Session {session_id} not found")
        
        return {
            "session_id": session.id,
            "teacher_name": session.teacher.user.name,
            "school_name": session.school.name,
            "date": str(session.date),
            "start_time": str(session.start_time),
            "end_time": str(session.end_time),
            "session_type": session.session_type,
            "grade_level": session.grade_level,
            "status": session.status,
            "student_count": session.student_count,
            "students": [
                {
                    "id": student.id,
                    "name": student.name,
                    "email": student.email
                }
                for student in session.students.all()
            ],
            "duration_hours": str(session.duration_hours),
            "actual_duration_hours": str(session.actual_duration_hours) if session.actual_duration_hours else None,
            "is_trial": session.is_trial,
            "is_makeup": session.is_makeup,
            "booking_confirmed_at": session.booking_confirmed_at.isoformat() if session.booking_confirmed_at else None,
            "cancelled_at": session.cancelled_at.isoformat() if session.cancelled_at else None,
            "notes": session.notes,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }