from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from scheduling.models import ClassSession, ClassType


class PaymentPlan(models.Model):
    """
    Represents different payment plans available for students
    """

    PLAN_TYPE_CHOICES = [
        ("monthly", _("Monthly")),
        ("package", _("Package")),
    ]

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True)
    plan_type = models.CharField(
        _("plan type"), max_length=20, choices=PLAN_TYPE_CHOICES
    )
    rate = models.DecimalField(_("rate"), max_digits=10, decimal_places=2)
    hours_included = models.IntegerField(
        _("hours included"), default=0, help_text=_("For package plans")
    )
    expiration_period = models.IntegerField(
        _("expiration period"), default=0, help_text=_("Days until package expires")
    )
    class_type = models.ForeignKey(
        ClassType,
        on_delete=models.SET_NULL,
        related_name="payment_plans",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name


class StudentPayment(models.Model):
    """
    Tracks payments made by students for their lessons
    """

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
        limit_choices_to={"user_type": "student"},
    )
    payment_plan = models.ForeignKey(
        PaymentPlan, on_delete=models.CASCADE, related_name="student_payments"
    )
    amount_paid = models.DecimalField(_("amount paid"), max_digits=10, decimal_places=2)
    payment_date = models.DateField(_("payment date"))
    period_start = models.DateField(
        _("period start"), null=True, blank=True, help_text=_("For monthly plans")
    )
    period_end = models.DateField(
        _("period end"), null=True, blank=True, help_text=_("For monthly plans")
    )
    hours_purchased = models.DecimalField(
        _("hours purchased"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("For package plans"),
    )
    hours_used = models.DecimalField(
        _("hours used"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("For package plans"),
    )
    notes = models.TextField(_("notes"), blank=True)
    status = models.CharField(
        _("status"), max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    def __str__(self):
        return f"{self.student.name} - {self.payment_plan.name} - {self.payment_date}"

    @property
    def remaining_hours(self):
        """Calculate remaining hours in the package"""
        if self.payment_plan.plan_type == "package":
            return self.hours_purchased - self.hours_used
        return 0

    @property
    def is_expired(self):
        """Check if the payment plan has expired"""
        from datetime import date, timedelta

        if self.payment_plan.plan_type == "monthly":
            return date.today() > self.period_end
        elif (
            self.payment_plan.plan_type == "package"
            and self.payment_plan.expiration_period > 0
        ):
            expiration_date = self.payment_date + timedelta(
                days=self.payment_plan.expiration_period
            )
            return date.today() > expiration_date
        return False


class TeacherCompensation(models.Model):
    """
    Tracks compensation for teachers based on classes taught
    """

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="compensations",
        limit_choices_to={"user_type": "teacher"},
    )
    period_start = models.DateField(_("period start"))
    period_end = models.DateField(_("period end"))
    class_sessions = models.ManyToManyField(
        ClassSession, related_name="teacher_compensations"
    )
    hours_taught = models.DecimalField(
        _("hours taught"), max_digits=10, decimal_places=2
    )
    amount_owed = models.DecimalField(_("amount owed"), max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(
        _("amount paid"), max_digits=10, decimal_places=2, default=0
    )
    payment_date = models.DateField(_("payment date"), null=True, blank=True)
    notes = models.TextField(_("notes"), blank=True)
    status = models.CharField(
        _("status"), max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    def __str__(self):
        return f"{self.teacher.name} - {self.period_start} to {self.period_end}"

    @property
    def is_fully_paid(self):
        """Check if the compensation has been fully paid"""
        return self.amount_paid >= self.amount_owed
