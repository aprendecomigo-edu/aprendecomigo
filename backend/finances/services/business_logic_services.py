from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.db import transaction

from common.financial_utils import FinancialCalculation


class CompensationService:
    @staticmethod
    def calculate_teacher_compensation(teacher_id: int, period_start, period_end):
        """Calculate teacher compensation for a given period using runtime model access."""
        # Get models at runtime to avoid circular imports
        Lesson = apps.get_model("classroom", "Lesson")
        User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
        TeacherCompensation = apps.get_model("finances", "TeacherCompensation")

        # Calculate completed lessons
        completed_lessons = Lesson.objects.filter(
            teacher_id=teacher_id, date__range=[period_start, period_end], status="completed"
        ).count()

        # Get teacher's hourly rate
        teacher = User.objects.get(id=teacher_id)
        hourly_rate = getattr(teacher.teacher_profile, "hourly_rate", Decimal("50.00"))

        # Calculate base amount with proper financial precision
        base_amount = FinancialCalculation.multiply_currency(completed_lessons, hourly_rate)
        bonus_amount = Decimal("0.00")

        # Apply bonus for high lesson count with proper rounding
        if completed_lessons >= 20:
            bonus_amount = FinancialCalculation.apply_percentage(base_amount, Decimal("0.10"))

        # Calculate total with proper financial precision
        total_amount = FinancialCalculation.add_currency(base_amount, bonus_amount)

        return {
            "base_amount": base_amount,
            "bonus_amount": bonus_amount,
            "total_amount": total_amount,
            "lessons_count": completed_lessons,
        }


class PaymentService:
    @staticmethod
    def process_lesson_payment(lesson_id: int, student_id: int) -> dict | None:
        """Process payment for a lesson using runtime model fetching."""
        # Runtime model fetching to avoid circular imports
        Lesson = apps.get_model("classroom", "Lesson")
        Payment = apps.get_model("finances", "Payment")
        User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

        try:
            lesson = Lesson.objects.get(id=lesson_id)
            student = User.objects.get(id=student_id)

            with transaction.atomic():
                # Ensure lesson price has proper financial precision
                payment_amount = FinancialCalculation.round_currency(lesson.price)

                payment = Payment.objects.create(
                    user=student, lesson=lesson, amount=payment_amount, status="pending", payment_method="credit_card"
                )

                # Create transaction record with proper financial precision
                Transaction = apps.get_model("finances", "Transaction")
                Transaction.objects.create(
                    payer=student,
                    payee=lesson.teacher,
                    amount=payment_amount,  # Use the properly rounded amount
                    transaction_type="lesson_payment",
                    description=f"Payment for lesson: {lesson.title}",
                    payment=payment,
                )

                return {"payment_id": payment.id, "amount": payment.amount, "status": payment.status}

        except Exception:
            # Handle any model not found exceptions
            return None
