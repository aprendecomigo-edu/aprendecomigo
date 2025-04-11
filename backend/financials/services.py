from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from scheduling.models import ClassSession

from .models import PaymentPlan, StudentPayment, TeacherCompensation


class StudentPaymentService:
    """
    Service for handling student payment operations and calculations
    """

    @staticmethod
    def calculate_remaining_hours(student_payment):
        """
        Calculate remaining hours for a student payment
        """
        if student_payment.payment_plan.plan_type != "package":
            return 0

        return student_payment.hours_purchased - student_payment.hours_used

    @staticmethod
    def is_payment_expired(student_payment):
        """
        Check if a student payment has expired
        """
        today = timezone.now().date()

        if student_payment.payment_plan.plan_type == "monthly":
            return today > student_payment.period_end

        if (
            student_payment.payment_plan.plan_type == "package"
            and student_payment.payment_plan.expiration_period > 0
        ):
            expiration_date = student_payment.payment_date + timedelta(
                days=student_payment.payment_plan.expiration_period
            )
            return today > expiration_date

        return False

    @staticmethod
    def update_hours_used(student_payment, hours_to_add):
        """
        Update hours used for a package payment plan
        """
        if student_payment.payment_plan.plan_type != "package":
            return False

        student_payment.hours_used += Decimal(str(hours_to_add))
        student_payment.save(update_fields=["hours_used"])
        return True

    @staticmethod
    def get_active_payment_plans(student, class_type=None):
        """
        Get active payment plans for a student
        """
        today = timezone.now().date()

        # Active monthly plans
        monthly_plans = StudentPayment.objects.filter(
            student=student,
            payment_plan__plan_type="monthly",
            period_start__lte=today,
            period_end__gte=today,
            status="completed",
        )

        # Active package plans
        package_plans = StudentPayment.objects.filter(
            student=student, payment_plan__plan_type="package", status="completed"
        )

        # Filter out expired package plans
        valid_package_plans = []
        for plan in package_plans:
            if (
                not StudentPaymentService.is_payment_expired(plan)
                and plan.remaining_hours > 0
            ):
                valid_package_plans.append(plan)

        # Combine all active plans
        active_plans = list(monthly_plans) + valid_package_plans

        # Filter by class type if provided
        if class_type:
            active_plans = [
                plan
                for plan in active_plans
                if plan.payment_plan.class_type is None
                or plan.payment_plan.class_type == class_type
            ]

        return active_plans

    @staticmethod
    def generate_payment_report(student=None, start_date=None, end_date=None):
        """
        Generate a payment report for a specific period
        """
        payments = StudentPayment.objects.all()

        if student:
            payments = payments.filter(student=student)

        if start_date:
            payments = payments.filter(payment_date__gte=start_date)

        if end_date:
            payments = payments.filter(payment_date__lte=end_date)

        total_amount = payments.aggregate(total=Sum("amount_paid"))["total"] or 0

        return {
            "payments": payments,
            "total_amount": total_amount,
            "count": payments.count(),
            "start_date": start_date,
            "end_date": end_date,
        }


class TeacherCompensationService:
    """
    Service for handling teacher compensation operations and calculations
    """

    @staticmethod
    def calculate_hours_taught(class_sessions):
        """
        Calculate total hours taught from a list of class sessions
        """
        if not class_sessions:
            return 0

        total_hours = Decimal("0.0")

        for session in class_sessions:
            # Calculate duration in hours
            duration = session.end_time - session.start_time
            hours = duration.total_seconds() / 3600
            total_hours += Decimal(str(hours))

        return total_hours.quantize(Decimal("0.01"))

    @staticmethod
    def calculate_compensation_amount(teacher, class_sessions):
        """
        Calculate compensation amount based on class types and hours taught
        """
        if not class_sessions:
            return Decimal("0.0")

        total_amount = Decimal("0.0")

        # Group sessions by class type to apply different rates
        sessions_by_type = {}
        for session in class_sessions:
            class_type = session.class_type
            if class_type not in sessions_by_type:
                sessions_by_type[class_type] = []
            sessions_by_type[class_type].append(session)

        # Calculate amount for each class type
        for class_type, sessions in sessions_by_type.items():
            hours = TeacherCompensationService.calculate_hours_taught(sessions)
            rate = class_type.hourly_rate
            amount = hours * rate
            total_amount += amount

        return total_amount.quantize(Decimal("0.01"))

    @staticmethod
    def create_compensation_for_period(teacher, start_date, end_date):
        """
        Create a compensation record for a specific period
        """
        # Get all classes in the period
        class_sessions = ClassSession.objects.filter(
            teacher=teacher,
            start_time__date__gte=start_date,
            end_time__date__lte=end_date,
            attended=True,
        )

        if not class_sessions.exists():
            return None

        # Calculate hours and amount
        hours_taught = TeacherCompensationService.calculate_hours_taught(class_sessions)
        amount_owed = TeacherCompensationService.calculate_compensation_amount(
            teacher, class_sessions
        )

        # Create compensation record
        compensation = TeacherCompensation.objects.create(
            teacher=teacher,
            period_start=start_date,
            period_end=end_date,
            hours_taught=hours_taught,
            amount_owed=amount_owed,
            status="pending",
        )

        # Add class sessions to the compensation
        compensation.class_sessions.set(class_sessions)

        return compensation

    @staticmethod
    def generate_compensation_report(teacher=None, start_date=None, end_date=None):
        """
        Generate a compensation report for a specific period
        """
        compensations = TeacherCompensation.objects.all()

        if teacher:
            compensations = compensations.filter(teacher=teacher)

        if start_date:
            compensations = compensations.filter(period_start__gte=start_date)

        if end_date:
            compensations = compensations.filter(period_end__lte=end_date)

        total_owed = compensations.aggregate(total=Sum("amount_owed"))["total"] or 0
        total_paid = compensations.aggregate(total=Sum("amount_paid"))["total"] or 0

        return {
            "compensations": compensations,
            "total_owed": total_owed,
            "total_paid": total_paid,
            "balance_due": total_owed - total_paid,
            "count": compensations.count(),
            "start_date": start_date,
            "end_date": end_date,
        }


class FinancialUtilities:
    """
    Utility functions for financial operations
    """

    @staticmethod
    def calculate_class_duration(start_time, end_time):
        """
        Calculate the duration of a class in hours
        """
        if not start_time or not end_time:
            return 0

        duration = end_time - start_time
        hours = duration.total_seconds() / 3600
        return Decimal(str(hours)).quantize(Decimal("0.01"))

    @staticmethod
    def validate_payment_plan(payment_plan):
        """
        Validate a payment plan is properly configured
        """
        errors = []

        if payment_plan.plan_type == "monthly":
            if payment_plan.hours_included > 0:
                errors.append("Monthly plans should not specify hours_included")
            if payment_plan.expiration_period > 0:
                errors.append("Monthly plans should not specify expiration_period")

        if payment_plan.plan_type == "package":
            if payment_plan.hours_included <= 0:
                errors.append("Package plans must specify hours_included")

        return errors

    @staticmethod
    def generate_financial_summary(start_date=None, end_date=None):
        """
        Generate a financial summary for the given period
        """
        # Default to current month if dates not provided
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            next_month = today.month + 1 if today.month < 12 else 1
            next_month_year = today.year if today.month < 12 else today.year + 1
            end_date = datetime(next_month_year, next_month, 1).date() - timedelta(
                days=1
            )

        # Get student payments in the period
        student_payments = StudentPayment.objects.filter(
            payment_date__gte=start_date, payment_date__lte=end_date, status="completed"
        )

        # Get teacher compensations in the period
        teacher_compensations = TeacherCompensation.objects.filter(
            period_start__gte=start_date, period_end__lte=end_date
        )

        # Calculate totals
        total_income = (
            student_payments.aggregate(total=Sum("amount_paid"))["total"] or 0
        )
        total_expenses = (
            teacher_compensations.aggregate(total=Sum("amount_owed"))["total"] or 0
        )
        net_income = total_income - total_expenses

        # Get payment plans statistics
        payment_plans = PaymentPlan.objects.all()
        plan_stats = {}

        for plan in payment_plans:
            plan_payments = student_payments.filter(payment_plan=plan)
            plan_stats[plan.name] = {
                "count": plan_payments.count(),
                "total": plan_payments.aggregate(total=Sum("amount_paid"))["total"]
                or 0,
            }

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "income": {
                "total": total_income,
                "count": student_payments.count(),
                "by_plan": plan_stats,
            },
            "expenses": {
                "total": total_expenses,
                "count": teacher_compensations.count(),
            },
            "net_income": net_income,
        }
