"""
Education Payment Services for course enrollment and lesson payments.

This module provides payment processing specifically for educational features,
integrating with the existing Stripe infrastructure from the finances app.
"""

from decimal import Decimal
import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

from finances.services.payment_service import PaymentService

from .models import Course, Enrollment, Payment

logger = logging.getLogger("education.payments")
User = get_user_model()


class EducationPaymentService:
    """
    Service for handling course enrollment payments and educational transactions.

    This service bridges the existing payment infrastructure with education-specific
    business logic for course enrollments, lesson payments, and teacher compensation.
    """

    def __init__(self):
        """Initialize the education payment service with Stripe integration."""
        self.payment_service = PaymentService()
        logger.info("EducationPaymentService initialized")

    def create_enrollment_payment(
        self, student_user, course_id: int, enrollment_id: int | None = None
    ) -> dict[str, Any]:
        """
        Create a payment intent for course enrollment.

        Args:
            student_user: The student user enrolling in the course
            course_id: ID of the course to enroll in
            enrollment_id: Optional enrollment ID if already created

        Returns:
            Dict containing payment intent details or error information
        """
        try:
            # Get the course
            try:
                course = Course.objects.select_related("teacher", "subject").get(id=course_id, status="published")
            except Course.DoesNotExist:
                return {"success": False, "error": "Course not found or not available for enrollment"}

            # Check if course is full
            if course.is_full:
                return {"success": False, "error": "Course is full"}

            # Check if student is already enrolled
            if enrollment_id is None:
                existing_enrollment = Enrollment.objects.filter(
                    student__user=student_user, course=course, is_active=True
                ).first()

                if existing_enrollment:
                    return {"success": False, "error": "Already enrolled in this course"}

            # Calculate total price
            total_price = course.total_price

            # Create payment metadata
            metadata = {
                "amount": str(total_price),
                "course_id": str(course.id),
                "course_title": course.title,
                "teacher_id": str(course.teacher.id),
                "hours": str(course.total_hours),
                "payment_type": "course_enrollment",
            }

            if enrollment_id:
                metadata["enrollment_id"] = str(enrollment_id)

            # Create payment intent using existing payment service
            result = self.payment_service.create_payment_intent(
                user=student_user, pricing_plan_id=f"course_{course.id}", metadata=metadata
            )

            if result["success"]:
                logger.info(
                    f"Created payment intent for course enrollment - "
                    f"Student: {student_user.id}, Course: {course.id}, Amount: €{total_price}"
                )

            return result

        except Exception as e:
            logger.error(f"Error creating enrollment payment: {e}")
            return {"success": False, "error": "Failed to create payment intent"}

    def process_successful_enrollment_payment(
        self, payment_intent_id: str, student_user, course_id: int
    ) -> dict[str, Any]:
        """
        Process a successful enrollment payment and create/activate enrollment.

        Args:
            payment_intent_id: Stripe payment intent ID
            student_user: The student user
            course_id: ID of the course

        Returns:
            Dict containing enrollment details or error information
        """
        try:
            with transaction.atomic():
                # Confirm payment with existing payment service
                payment_result = self.payment_service.confirm_payment_completion(payment_intent_id)

                if not payment_result["success"]:
                    return payment_result

                # Get course and student profile
                course = Course.objects.select_related("teacher", "subject").get(id=course_id)
                student_profile = student_user.studentprofile

                # Create or update enrollment
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student_profile,
                    course=course,
                    defaults={"start_date": course.start_date, "status": "active", "is_paid": True, "is_active": True},
                )

                if not created:
                    # Update existing enrollment
                    enrollment.status = "active"
                    enrollment.is_paid = True
                    enrollment.is_active = True
                    enrollment.save()

                # Create payment record in education system
                education_payment = Payment.objects.create(
                    student=student_profile,
                    teacher=course.teacher,
                    enrollment=enrollment,
                    amount=course.total_price,
                    teacher_amount=self._calculate_teacher_amount(course.total_price),
                    platform_fee=self._calculate_platform_fee(course.total_price),
                    stripe_payment_intent_id=payment_intent_id,
                    status="completed",
                    payment_type="enrollment",
                    description=f"Enrollment in {course.title}",
                    currency="EUR",
                )

                # Calculate teacher amount and platform fee
                education_payment.calculate_teacher_amount()
                education_payment.save()

                logger.info(
                    f"Successfully processed enrollment payment - "
                    f"Student: {student_user.id}, Course: {course.id}, "
                    f"Enrollment: {enrollment.id}, Payment: {education_payment.id}"
                )

                return {
                    "success": True,
                    "enrollment_id": enrollment.id,
                    "payment_id": education_payment.id,
                    "course_title": course.title,
                    "amount_paid": str(course.total_price),
                }

        except Exception as e:
            logger.error(f"Error processing enrollment payment: {e}")
            return {"success": False, "error": "Failed to process enrollment payment"}

    def create_lesson_payment(
        self,
        student_user,
        teacher_user,
        lesson_hours: Decimal,
        hourly_rate: Decimal,
        description: str = "Individual lesson payment",
    ) -> dict[str, Any]:
        """
        Create a payment intent for individual lesson payment.

        Args:
            student_user: The student user
            teacher_user: The teacher user
            lesson_hours: Number of hours for the lesson
            hourly_rate: Hourly rate for the lesson
            description: Description of the lesson payment

        Returns:
            Dict containing payment intent details or error information
        """
        try:
            # Calculate total amount
            total_amount = lesson_hours * hourly_rate

            # Create payment metadata
            metadata = {
                "amount": str(total_amount),
                "lesson_hours": str(lesson_hours),
                "hourly_rate": str(hourly_rate),
                "teacher_id": str(teacher_user.teacherprofile.id),
                "payment_type": "individual_lesson",
            }

            # Create payment intent
            result = self.payment_service.create_payment_intent(
                user=student_user, pricing_plan_id=f"lesson_{teacher_user.id}", metadata=metadata
            )

            if result["success"]:
                logger.info(
                    f"Created payment intent for lesson - "
                    f"Student: {student_user.id}, Teacher: {teacher_user.id}, "
                    f"Hours: {lesson_hours}, Rate: €{hourly_rate}"
                )

            return result

        except Exception as e:
            logger.error(f"Error creating lesson payment: {e}")
            return {"success": False, "error": "Failed to create lesson payment intent"}

    def process_lesson_payment(
        self, payment_intent_id: str, student_user, teacher_user, lesson_hours: Decimal, hourly_rate: Decimal
    ) -> dict[str, Any]:
        """
        Process a successful lesson payment.

        Args:
            payment_intent_id: Stripe payment intent ID
            student_user: The student user
            teacher_user: The teacher user
            lesson_hours: Number of lesson hours
            hourly_rate: Hourly rate

        Returns:
            Dict containing payment details or error information
        """
        try:
            with transaction.atomic():
                # Confirm payment
                payment_result = self.payment_service.confirm_payment_completion(payment_intent_id)

                if not payment_result["success"]:
                    return payment_result

                # Calculate amounts
                total_amount = lesson_hours * hourly_rate

                # Create payment record
                education_payment = Payment.objects.create(
                    student=student_user.studentprofile,
                    teacher=teacher_user.teacherprofile,
                    amount=total_amount,
                    teacher_amount=self._calculate_teacher_amount(total_amount),
                    platform_fee=self._calculate_platform_fee(total_amount),
                    stripe_payment_intent_id=payment_intent_id,
                    status="completed",
                    payment_type="lesson",
                    description=f"Individual lesson - {lesson_hours} hours",
                    currency="EUR",
                )

                logger.info(
                    f"Successfully processed lesson payment - "
                    f"Student: {student_user.id}, Teacher: {teacher_user.id}, "
                    f"Amount: €{total_amount}, Payment: {education_payment.id}"
                )

                return {
                    "success": True,
                    "payment_id": education_payment.id,
                    "amount_paid": str(total_amount),
                    "lesson_hours": str(lesson_hours),
                }

        except Exception as e:
            logger.error(f"Error processing lesson payment: {e}")
            return {"success": False, "error": "Failed to process lesson payment"}

    def get_student_payment_history(self, student_user) -> dict[str, Any]:
        """
        Get payment history for a student.

        Args:
            student_user: The student user

        Returns:
            Dict containing payment history
        """
        try:
            payments = (
                Payment.objects.filter(student__user=student_user)
                .select_related("teacher__user", "enrollment__course")
                .order_by("-created_at")
            )

            payment_history = []
            total_spent = Decimal("0.00")

            for payment in payments:
                payment_data = {
                    "id": payment.id,
                    "amount": str(payment.amount),
                    "status": payment.status,
                    "payment_type": payment.payment_type,
                    "description": payment.description,
                    "teacher_name": payment.teacher.user.get_full_name(),
                    "created_at": payment.created_at.isoformat(),
                    "course_title": payment.enrollment.course.title if payment.enrollment else None,
                }
                payment_history.append(payment_data)

                if payment.status == "completed":
                    total_spent += payment.amount

            return {
                "success": True,
                "payments": payment_history,
                "total_spent": str(total_spent),
                "payment_count": len(payment_history),
            }

        except Exception as e:
            logger.error(f"Error getting payment history: {e}")
            return {"success": False, "error": "Failed to retrieve payment history"}

    def get_teacher_earnings(self, teacher_user) -> dict[str, Any]:
        """
        Get earnings summary for a teacher.

        Args:
            teacher_user: The teacher user

        Returns:
            Dict containing earnings information
        """
        try:
            payments = Payment.objects.filter(teacher__user=teacher_user, status="completed").select_related(
                "student__user", "enrollment__course"
            )

            total_earnings = Decimal("0.00")
            total_platform_fees = Decimal("0.00")
            payment_count = 0

            earnings_by_type = {
                "enrollment": Decimal("0.00"),
                "lesson": Decimal("0.00"),
                "materials": Decimal("0.00"),
                "other": Decimal("0.00"),
            }

            for payment in payments:
                total_earnings += payment.teacher_amount
                total_platform_fees += payment.platform_fee
                payment_count += 1

                # Categorize earnings by type
                if payment.payment_type in earnings_by_type:
                    earnings_by_type[payment.payment_type] += payment.teacher_amount
                else:
                    earnings_by_type["other"] += payment.teacher_amount

            return {
                "success": True,
                "total_earnings": str(total_earnings),
                "total_platform_fees": str(total_platform_fees),
                "payment_count": payment_count,
                "earnings_by_type": {k: str(v) for k, v in earnings_by_type.items()},
            }

        except Exception as e:
            logger.error(f"Error getting teacher earnings: {e}")
            return {"success": False, "error": "Failed to retrieve teacher earnings"}

    def _calculate_platform_fee(self, amount: Decimal) -> Decimal:
        """Calculate platform fee (5% of total amount)."""
        return amount * Decimal("0.05")

    def _calculate_teacher_amount(self, amount: Decimal) -> Decimal:
        """Calculate teacher amount after platform fee."""
        platform_fee = self._calculate_platform_fee(amount)
        return amount - platform_fee
