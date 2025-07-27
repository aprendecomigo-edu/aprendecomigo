from decimal import Decimal

from accounts.models import CustomUser, School, TeacherProfile
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CompensationRuleType(models.TextChoices):
    """Types of compensation rules for teachers."""

    GRADE_SPECIFIC = "grade_specific", _("Grade Specific Rate")
    GROUP_CLASS = "group_class", _("Group Class Rate")
    FIXED_SALARY = "fixed_salary", _("Fixed Monthly Salary")
    BASE_PLUS_BONUS = "base_plus_bonus", _("Base Salary Plus Bonus")


class SessionType(models.TextChoices):
    """Types of class sessions."""

    INDIVIDUAL = "individual", _("Individual Session")
    GROUP = "group", _("Group Session")


class SessionStatus(models.TextChoices):
    """Status of class sessions."""

    SCHEDULED = "scheduled", _("Scheduled")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")
    NO_SHOW = "no_show", _("No Show")


class PaymentStatus(models.TextChoices):
    """Payment status for teacher compensation."""

    PENDING = "pending", _("Pending")
    CALCULATED = "calculated", _("Calculated")
    PAID = "paid", _("Paid")


class TrialCostAbsorption(models.TextChoices):
    """Who absorbs the cost of trial classes."""

    SCHOOL = "school", _("School Absorbs Cost")
    TEACHER = "teacher", _("Teacher Absorbs Cost")
    SPLIT = "split", _("Split Cost 50/50")


class PaymentFrequency(models.TextChoices):
    """How frequently teachers are paid."""

    WEEKLY = "weekly", _("Weekly")
    BIWEEKLY = "biweekly", _("Bi-weekly")
    MONTHLY = "monthly", _("Monthly")


class SchoolBillingSettings(models.Model):
    """Billing configuration settings for each school."""

    school: models.OneToOneField = models.OneToOneField(
        School, on_delete=models.CASCADE, related_name="billing_settings", verbose_name=_("school")
    )

    trial_cost_absorption: models.CharField = models.CharField(
        _("trial cost absorption"),
        max_length=20,
        choices=TrialCostAbsorption.choices,
        default=TrialCostAbsorption.SCHOOL,
        help_text=_("Who absorbs the cost of trial classes"),
    )

    teacher_payment_frequency: models.CharField = models.CharField(
        _("teacher payment frequency"),
        max_length=20,
        choices=PaymentFrequency.choices,
        default=PaymentFrequency.MONTHLY,
        help_text=_("How frequently teachers are paid"),
    )

    payment_day_of_month: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(
        _("payment day of month"),
        default=1,
        help_text=_("Day of the month when teachers are paid (1-28)"),
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("School Billing Settings")
        verbose_name_plural = _("School Billing Settings")

    def __str__(self) -> str:
        return f"Billing settings for {self.school.name}"

    def clean(self) -> None:
        """Validate payment day is between 1 and 28."""
        if self.payment_day_of_month < 1 or self.payment_day_of_month > 28:
            raise ValidationError(
                _("Payment day must be between 1 and 28 to ensure it exists in all months")
            )


class TeacherCompensationRule(models.Model):
    """Compensation rules for teachers based on different criteria."""

    teacher: models.ForeignKey = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="compensation_rules",
        verbose_name=_("teacher"),
    )

    school: models.ForeignKey = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="teacher_compensation_rules",
        verbose_name=_("school"),
    )

    rule_type: models.CharField = models.CharField(
        _("rule type"), max_length=20, choices=CompensationRuleType.choices
    )

    # For grade-specific rules
    grade_level: models.CharField = models.CharField(
        _("grade level"),
        max_length=10,
        blank=True,
        null=True,
        help_text=_("Grade level for grade-specific rules (e.g., '7', '10')"),
    )

    # For hourly rates
    rate_per_hour: models.DecimalField = models.DecimalField(
        _("rate per hour"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Hourly rate in euros"),
    )

    # For fixed salaries
    fixed_amount: models.DecimalField = models.DecimalField(
        _("fixed amount"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Fixed monthly amount in euros"),
    )

    # Additional configuration (JSON field for complex rules)
    conditions: models.JSONField = models.JSONField(
        _("conditions"),
        default=dict,
        blank=True,
        help_text=_("Additional conditions for this rule (JSON format)"),
    )

    is_active: models.BooleanField = models.BooleanField(_("is active"), default=True)

    effective_from: models.DateField = models.DateField(
        _("effective from"),
        default=timezone.now,
        help_text=_("Date from which this rule is effective"),
    )

    effective_until: models.DateField = models.DateField(
        _("effective until"),
        null=True,
        blank=True,
        help_text=_("Date until which this rule is effective (optional)"),
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Teacher Compensation Rule")
        verbose_name_plural = _("Teacher Compensation Rules")
        # Ensure only one active rule per teacher per school per rule type per grade
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "school", "rule_type", "grade_level"],
                condition=models.Q(is_active=True),
                name="unique_active_teacher_rule",
            )
        ]

    def __str__(self) -> str:
        rule_desc = f"{self.get_rule_type_display()}"
        if self.grade_level:
            rule_desc += f" (Grade {self.grade_level})"
        return f"{self.teacher.user.name} - {rule_desc} at {self.school.name}"

    def clean(self) -> None:
        """Validate rule configuration."""
        if self.rule_type == CompensationRuleType.GRADE_SPECIFIC:
            if not self.grade_level:
                raise ValidationError(_("Grade level is required for grade-specific rules"))
            if not self.rate_per_hour:
                raise ValidationError(_("Rate per hour is required for grade-specific rules"))
        elif self.rule_type == CompensationRuleType.GROUP_CLASS:
            if not self.rate_per_hour:
                raise ValidationError(_("Rate per hour is required for group class rules"))
        elif self.rule_type == CompensationRuleType.FIXED_SALARY:
            if not self.fixed_amount:
                raise ValidationError(_("Fixed amount is required for fixed salary rules"))


class ClassSession(models.Model):
    """Individual class sessions taught by teachers."""

    teacher: models.ForeignKey = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="class_sessions",
        verbose_name=_("teacher"),
    )

    school: models.ForeignKey = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="class_sessions", verbose_name=_("school")
    )

    # Session details
    date: models.DateField = models.DateField(_("date"))
    start_time: models.TimeField = models.TimeField(_("start time"))
    end_time: models.TimeField = models.TimeField(_("end time"))

    session_type: models.CharField = models.CharField(
        _("session type"), max_length=20, choices=SessionType.choices
    )

    grade_level: models.CharField = models.CharField(
        _("grade level"),
        max_length=10,
        help_text=_("Grade level of the session (e.g., '7', '10', 'mixed')"),
    )

    # Student information
    student_count: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(
        _("student count"), default=1, help_text=_("Number of students in this session")
    )

    students: models.ManyToManyField = models.ManyToManyField(
        CustomUser,
        related_name="attended_sessions",
        blank=True,
        help_text=_("Students who attended this session"),
    )

    # Session flags
    is_trial: models.BooleanField = models.BooleanField(
        _("is trial"), default=False, help_text=_("Whether this is a trial session")
    )

    is_makeup: models.BooleanField = models.BooleanField(
        _("is makeup"), default=False, help_text=_("Whether this is a makeup session")
    )

    status: models.CharField = models.CharField(
        _("status"), max_length=20, choices=SessionStatus.choices, default=SessionStatus.SCHEDULED
    )

    # Additional information
    notes: models.TextField = models.TextField(
        _("notes"), blank=True, help_text=_("Additional notes about this session")
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Class Session")
        verbose_name_plural = _("Class Sessions")
        ordering = ["-date", "-start_time"]

    def __str__(self) -> str:
        return (
            f"{self.teacher.user.name} - {self.get_session_type_display()} "
            f"Grade {self.grade_level} on {self.date}"
        )

    @property
    def duration_hours(self) -> Decimal:
        """Calculate session duration in hours."""
        from datetime import datetime, timedelta

        # Create datetime objects for calculation
        start_datetime = datetime.combine(self.date, self.start_time)
        end_datetime = datetime.combine(self.date, self.end_time)

        # Handle sessions that cross midnight
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)

        duration = end_datetime - start_datetime
        return Decimal(str(duration.total_seconds() / 3600))

    def clean(self) -> None:
        """Validate session data."""
        if self.end_time <= self.start_time:
            raise ValidationError(_("End time must be after start time"))

        if self.session_type == SessionType.INDIVIDUAL and self.student_count > 1:
            raise ValidationError(_("Individual sessions can only have 1 student"))


class TeacherPaymentEntry(models.Model):
    """Payment entries for teacher compensation calculations."""

    session: models.OneToOneField = models.OneToOneField(
        ClassSession,
        on_delete=models.CASCADE,
        related_name="payment_entry",
        verbose_name=_("session"),
    )

    teacher: models.ForeignKey = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="payment_entries",
        verbose_name=_("teacher"),
    )

    school: models.ForeignKey = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="teacher_payment_entries",
        verbose_name=_("school"),
    )

    # Payment calculation
    billing_period: models.CharField = models.CharField(
        _("billing period"),
        max_length=7,
        help_text=_("Billing period in YYYY-MM format (e.g., '2024-01')"),
    )

    hours_taught: models.DecimalField = models.DecimalField(
        _("hours taught"),
        max_digits=4,
        decimal_places=2,
        help_text=_("Number of hours taught in this session"),
    )

    rate_applied: models.DecimalField = models.DecimalField(
        _("rate applied"),
        max_digits=6,
        decimal_places=2,
        help_text=_("Hourly rate applied for this session"),
    )

    amount_earned: models.DecimalField = models.DecimalField(
        _("amount earned"),
        max_digits=8,
        decimal_places=2,
        help_text=_("Total amount earned for this session"),
    )

    compensation_rule: models.ForeignKey = models.ForeignKey(
        TeacherCompensationRule,
        on_delete=models.PROTECT,
        related_name="payment_entries",
        null=True,
        blank=True,
        verbose_name=_("compensation rule"),
        help_text=_("The compensation rule used for this calculation"),
    )

    payment_status: models.CharField = models.CharField(
        _("payment status"),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    # Additional information
    calculation_notes: models.TextField = models.TextField(
        _("calculation notes"),
        blank=True,
        help_text=_("Notes about how the payment was calculated"),
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Teacher Payment Entry")
        verbose_name_plural = _("Teacher Payment Entries")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.teacher.user.name} - €{self.amount_earned} for {self.session.date} session"


class StudentAccountBalance(models.Model):
    """
    Student account balance model to track hours purchased, consumed, and remaining balance.
    This is the core data structure for the student purchase system.
    """

    student: models.OneToOneField = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="account_balance",
        verbose_name=_("student"),
        help_text=_("Student who owns this account balance"),
    )

    hours_purchased: models.DecimalField = models.DecimalField(
        _("hours purchased"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Total hours purchased by the student"),
    )

    hours_consumed: models.DecimalField = models.DecimalField(
        _("hours consumed"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Total hours consumed by the student"),
    )

    balance_amount: models.DecimalField = models.DecimalField(
        _("balance amount"),
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Current account balance in euros"),
    )

    # Audit timestamps
    created_at: models.DateTimeField = models.DateTimeField(
        _("created at"), auto_now_add=True
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        _("updated at"), auto_now=True
    )

    class Meta:
        verbose_name = _("Student Account Balance")
        verbose_name_plural = _("Student Account Balances")
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        remaining = self.remaining_hours
        return f"Account Balance for {self.student.name}: €{self.balance_amount} ({remaining}h remaining)"

    @property
    def remaining_hours(self) -> Decimal:
        """
        Calculate remaining hours (purchased - consumed).
        Can be negative in overdraft scenarios.
        """
        return self.hours_purchased - self.hours_consumed


class TransactionType(models.TextChoices):
    """Types of purchase transactions."""

    PACKAGE = "package", _("Package")
    SUBSCRIPTION = "subscription", _("Subscription")


class TransactionPaymentStatus(models.TextChoices):
    """Payment status choices for purchase transactions."""

    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")
    REFUNDED = "refunded", _("Refunded")


class PurchaseTransaction(models.Model):
    """
    Comprehensive transaction tracking for all student purchases.
    Supports payment lifecycle tracking, Stripe integration, and package expiration management.
    """

    student: models.ForeignKey = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="purchase_transactions",
        verbose_name=_("student"),
        help_text=_("Student who made this purchase"),
    )

    transaction_type: models.CharField = models.CharField(
        _("transaction type"),
        max_length=20,
        choices=TransactionType.choices,
        help_text=_("Type of transaction (package or subscription)"),
    )

    amount: models.DecimalField = models.DecimalField(
        _("amount"),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Transaction amount in euros"),
    )

    payment_status: models.CharField = models.CharField(
        _("payment status"),
        max_length=20,
        choices=TransactionPaymentStatus.choices,
        default=TransactionPaymentStatus.PENDING,
        help_text=_("Current payment status"),
    )

    # Stripe integration fields
    stripe_payment_intent_id: models.CharField = models.CharField(
        _("Stripe payment intent ID"),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Stripe PaymentIntent ID for this transaction"),
    )

    stripe_customer_id: models.CharField = models.CharField(
        _("Stripe customer ID"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Stripe Customer ID associated with this transaction"),
    )

    # Package expiration management
    expires_at: models.DateTimeField = models.DateTimeField(
        _("expires at"),
        null=True,
        blank=True,
        help_text=_("Expiration date for packages (null for subscriptions)"),
    )

    # Extensible metadata storage
    metadata: models.JSONField = models.JSONField(
        _("metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional transaction data in JSON format"),
    )

    # Audit timestamps
    created_at: models.DateTimeField = models.DateTimeField(
        _("created at"), auto_now_add=True
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        _("updated at"), auto_now=True
    )

    class Meta:
        verbose_name = _("Purchase Transaction")
        verbose_name_plural = _("Purchase Transactions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "payment_status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["stripe_payment_intent_id"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"Transaction {self.id}: {self.student.name} - "
            f"€{self.amount} ({self.transaction_type.upper()} - {self.payment_status.upper()})"
        )

    @property
    def is_expired(self) -> bool:
        """
        Check if the transaction has expired.
        Returns False for subscriptions (no expiration) or if expires_at is None.
        Returns True if expires_at is in the past.
        """
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    def mark_completed(self) -> None:
        """
        Mark the transaction as completed and save to database.
        """
        self.payment_status = TransactionPaymentStatus.COMPLETED
        self.save(update_fields=["payment_status", "updated_at"])

    def clean(self) -> None:
        """Validate transaction data."""
        super().clean()
        
        # Ensure amount is not negative
        if self.amount < Decimal("0.00"):
            raise ValidationError(_("Transaction amount cannot be negative"))
        
        # For subscriptions, expires_at should be null
        if self.transaction_type == TransactionType.SUBSCRIPTION and self.expires_at is not None:
            raise ValidationError(
                _("Subscription transactions should not have an expiration date")
            )
