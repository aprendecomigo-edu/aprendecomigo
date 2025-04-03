from datetime import timedelta

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.utils import timezone

from scheduling.models import ClassSession

from .models import StudentPayment, TeacherCompensation
from .services import (
    FinancialUtilities,
    StudentPaymentService,
    TeacherCompensationService,
)


@receiver(post_save, sender=ClassSession)
def update_financial_records_on_class_session_save(sender, instance, created, **kwargs):
    """
    Update financial records when a class session is saved or updated
    """
    # Skip if the class session is not attended
    if not instance.attended:
        return

    # Handle student payment updates only if class was attended
    if instance.attended:
        update_student_payments_for_class(instance)

    # Check if we need to update teacher compensation
    # Only update for recent sessions (within last 30 days)
    today = timezone.now().date()
    session_date = instance.start_time.date()
    if (today - session_date) <= timedelta(days=30):
        # Find any existing compensation records covering this session
        compensations = TeacherCompensation.objects.filter(
            teacher=instance.teacher,
            period_start__lte=session_date,
            period_end__gte=session_date,
        )

        # Update each compensation that includes this session
        for compensation in compensations:
            # Recalculate hours and amount
            sessions = compensation.class_sessions.all()
            if instance not in sessions:
                compensation.class_sessions.add(instance)
                sessions = list(sessions) + [instance]

            hours_taught = TeacherCompensationService.calculate_hours_taught(sessions)
            amount_owed = TeacherCompensationService.calculate_compensation_amount(
                instance.teacher, sessions
            )

            # Update compensation record
            compensation.hours_taught = hours_taught
            compensation.amount_owed = amount_owed
            compensation.save(update_fields=["hours_taught", "amount_owed"])


@receiver(m2m_changed, sender=ClassSession.students.through)
def update_student_payments_on_student_change(
    sender, instance, action, pk_set, **kwargs
):
    """
    Update student payments when students are added to or removed from a class session
    """
    # Only process for 'post_add' and 'post_remove' actions
    if action not in ["post_add", "post_remove"]:
        return

    # Skip if the class session is not attended
    if not instance.attended:
        return

    # Update payments for each student added or removed
    from accounts.models import CustomUser

    students = CustomUser.objects.filter(id__in=pk_set)

    # Calculate class duration
    class_duration = FinancialUtilities.calculate_class_duration(
        instance.start_time, instance.end_time
    )

    for student in students:
        # For added students, use hours as positive
        # For removed students, use hours as negative
        hours_change = class_duration if action == "post_add" else -class_duration

        # Get active payment plans for this student and class type
        active_plans = StudentPaymentService.get_active_payment_plans(
            student, instance.class_type
        )

        # Update the first available package plan
        for plan in active_plans:
            if plan.payment_plan.plan_type == "package":
                StudentPaymentService.update_hours_used(plan, hours_change)
                break


def update_student_payments_for_class(class_session):
    """
    Update student payments when a class session is marked as attended
    """
    # Calculate class duration
    class_duration = FinancialUtilities.calculate_class_duration(
        class_session.start_time, class_session.end_time
    )

    # Update payments for each student in the class
    for student in class_session.students.all():
        # Get active payment plans for this student and class type
        active_plans = StudentPaymentService.get_active_payment_plans(
            student, class_session.class_type
        )

        # Update the first available package plan
        for plan in active_plans:
            if plan.payment_plan.plan_type == "package":
                StudentPaymentService.update_hours_used(plan, class_duration)
                break


@receiver(post_save, sender=StudentPayment)
def check_payment_plan_expiration(sender, instance, **kwargs):
    """
    Check if payment plans have expired and update status accordingly
    """
    # Only check completed payments
    if instance.status != "completed":
        return

    # Check if the payment plan has expired
    if StudentPaymentService.is_payment_expired(instance):
        # If using all hours or expiration date passed, mark as completed
        if (
            instance.payment_plan.plan_type == "package"
            and instance.remaining_hours <= 0
        ):
            instance.status = "completed"
            instance.save(update_fields=["status"])
