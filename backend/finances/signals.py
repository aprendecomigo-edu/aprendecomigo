import logging

from django.apps import apps

logger = logging.getLogger(__name__)


def handle_lesson_completion(sender, instance, created, **kwargs):
    """Handle compensation calculation when lesson is completed."""
    if not created and instance.status == "completed":
        try:
            # Use apps.get_model for cross-app access
            TeacherCompensation = apps.get_model("finances", "TeacherCompensation")

            # Trigger compensation calculation for the teacher
            # Calculate monthly compensation
            import datetime

            from .services import CompensationService

            today = datetime.date.today()
            month_start = today.replace(day=1)

            compensation_data = CompensationService.calculate_teacher_compensation(
                teacher_id=instance.teacher_id, period_start=month_start, period_end=today
            )

            # Update or create compensation record
            TeacherCompensation.objects.update_or_create(
                teacher_id=instance.teacher_id, period_start=month_start, period_end=today, defaults=compensation_data
            )

        except Exception as e:
            logger.error(f"Error calculating compensation: {e}")


def setup_user_payment_profile(sender, instance, created, **kwargs):
    """Set up payment profile for new users."""
    if created and hasattr(instance, "is_student") and instance.is_student:
        try:
            PaymentProfile = apps.get_model("finances", "PaymentProfile")
            PaymentProfile.objects.get_or_create(user=instance, defaults={"payment_method_preference": "credit_card"})
        except Exception as e:
            logger.error(f"Error setting up payment profile: {e}")


# Note: Signal connections are handled in apps.py ready() method
