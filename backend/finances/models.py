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


class PlanType(models.TextChoices):
    """Types of pricing plans."""

    PACKAGE = "package", _("Package")
    SUBSCRIPTION = "subscription", _("Subscription")


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

    # Session tracking fields
    actual_duration_hours: models.DecimalField = models.DecimalField(
        _("actual duration hours"),
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Actual duration in hours when session was completed"),
    )
    
    booking_confirmed_at: models.DateTimeField = models.DateTimeField(
        _("booking confirmed at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when the session booking was confirmed"),
    )
    
    cancelled_at: models.DateTimeField = models.DateTimeField(
        _("cancelled at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when the session was cancelled"),
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

    def save(self, *args, **kwargs):
        """Override save to handle status changes and timestamps for existing sessions."""
        from django.utils import timezone
        
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            # Get the old status to detect status changes
            try:
                old_session = ClassSession.objects.get(pk=self.pk)
                old_status = old_session.status
            except ClassSession.DoesNotExist:
                pass
        
        # Handle timestamp updates based on status changes
        if old_status != self.status:
            if self.status == SessionStatus.SCHEDULED and not self.booking_confirmed_at:
                self.booking_confirmed_at = timezone.now()
            elif self.status == SessionStatus.CANCELLED and not self.cancelled_at:
                self.cancelled_at = timezone.now()
            elif self.status == SessionStatus.COMPLETED and not self.actual_duration_hours:
                # Set actual duration to calculated duration if not specified
                self.actual_duration_hours = self.duration_hours
        
        # Save the session first
        super().save(*args, **kwargs)
        
        # Handle status changes for existing sessions
        if not is_new and old_status != self.status:
            self._handle_session_status_change(old_status)

    def _handle_session_status_change(self, old_status):
        """Handle status changes for existing sessions."""
        from finances.services.hour_deduction_service import HourDeductionService
        
        # Handle cancellation
        if self.status == SessionStatus.CANCELLED and old_status != SessionStatus.CANCELLED:
            HourDeductionService.refund_hours_for_session(
                self, 
                reason=f"Session cancelled (changed from {old_status})"
            )

    def process_hour_deduction(self):
        """
        Process hour deduction for this session.
        
        This method is called explicitly after students are added to handle
        hour deduction logic properly.
        """
        if self.is_trial:
            return []
        
        if self.status != SessionStatus.SCHEDULED:
            return []
        
        from finances.services.hour_deduction_service import HourDeductionService
        return HourDeductionService.validate_and_deduct_hours_for_session(self)


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


class PricingPlanManager(models.Manager):
    """Manager for PricingPlan model."""
    
    def get_queryset(self):
        """Return queryset ordered by display_order and name."""
        return super().get_queryset().order_by('display_order', 'name')


class ActivePricingPlanManager(models.Manager):
    """Manager for active pricing plans only."""
    
    def get_queryset(self):
        """Return only active plans ordered by display_order and name."""
        return super().get_queryset().filter(is_active=True).order_by('display_order', 'name')


class PricingPlan(models.Model):
    """
    Pricing plan configuration model for different tutoring packages and subscriptions.
    
    This model allows business users to configure pricing plans through the Django Admin
    interface without requiring code changes. Supports both package-based plans with
    validity periods and subscription-based plans.
    """
    
    name: models.CharField = models.CharField(
        _("plan name"),
        max_length=100,
        help_text=_("Display name for the pricing plan")
    )
    
    description: models.TextField = models.TextField(
        _("description"),
        help_text=_("Detailed description of what the plan includes")
    )
    
    plan_type: models.CharField = models.CharField(
        _("plan type"),
        max_length=20,
        choices=PlanType.choices,
        help_text=_("Type of plan: package (expires) or subscription (recurring)")
    )
    
    hours_included: models.DecimalField = models.DecimalField(
        _("hours included"),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Number of tutoring hours included in this plan")
    )
    
    price_eur: models.DecimalField = models.DecimalField(
        _("price (EUR)"),
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Price of the plan in euros")
    )
    
    validity_days: models.PositiveIntegerField = models.PositiveIntegerField(
        _("validity days"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_("Number of days the plan is valid (null for subscriptions)")
    )
    
    # Display and organization fields
    display_order: models.PositiveIntegerField = models.PositiveIntegerField(
        _("display order"),
        default=1,
        help_text=_("Order in which plans should be displayed (lower numbers first)")
    )
    
    is_featured: models.BooleanField = models.BooleanField(
        _("is featured"),
        default=False,
        help_text=_("Whether this plan should be highlighted as featured/recommended")
    )
    
    is_active: models.BooleanField = models.BooleanField(
        _("is active"),
        default=True,
        help_text=_("Whether this plan is currently available for purchase")
    )
    
    # Audit timestamps
    created_at: models.DateTimeField = models.DateTimeField(
        _("created at"), auto_now_add=True
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        _("updated at"), auto_now=True
    )
    
    # Managers
    objects = PricingPlanManager()
    active = ActivePricingPlanManager()
    
    class Meta:
        verbose_name = _("Pricing Plan")
        verbose_name_plural = _("Pricing Plans")
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "display_order"]),
            models.Index(fields=["plan_type", "is_active"]),
            models.Index(fields=["is_featured", "is_active"]),
        ]
    
    def __str__(self) -> str:
        validity_str = f"{self.validity_days} days" if self.validity_days else "subscription"
        return f"{self.name} - €{self.price_eur} ({self.hours_included}h, {validity_str})"
    
    @property
    def price_per_hour(self) -> Decimal | None:
        """
        Calculate the price per hour for this plan.
        
        Returns:
            Decimal: Price per hour, or None if hours_included is zero
        """
        if self.hours_included > 0:
            return self.price_eur / self.hours_included
        return None
    
    def clean(self) -> None:
        """Validate the pricing plan configuration."""
        super().clean()
        
        # Package plans must have validity_days specified
        if self.plan_type == PlanType.PACKAGE and not self.validity_days:
            raise ValidationError(
                _("Package plans must have validity_days specified")
            )
        
        # Subscription plans should not have validity_days
        if self.plan_type == PlanType.SUBSCRIPTION and self.validity_days is not None:
            raise ValidationError(
                _("Subscription plans should not have validity_days")
            )
        
        # Ensure price is positive
        if self.price_eur <= Decimal("0"):
            raise ValidationError(
                _("Price must be greater than 0")
            )
        
        # Ensure hours_included is positive
        if self.hours_included <= Decimal("0"):
            raise ValidationError(
                _("Hours included must be greater than 0")
            )
        
        # Ensure validity_days is positive when specified
        if self.validity_days is not None and self.validity_days <= 0:
            raise ValidationError(
                _("Validity days must be greater than 0")
            )


class HourConsumption(models.Model):
    """
    Hour consumption tracking model that links sessions to hour usage.
    
    This model maintains an audit trail linking consumption back to original purchase 
    transactions and provides refund functionality for early session endings.
    """

    student_account: models.ForeignKey = models.ForeignKey(
        StudentAccountBalance,
        on_delete=models.CASCADE,
        related_name="hour_consumptions",
        verbose_name=_("student account"),
        help_text=_("Student account that this consumption is associated with"),
    )

    class_session: models.ForeignKey = models.ForeignKey(
        ClassSession,
        on_delete=models.CASCADE,
        related_name="hour_consumptions",
        verbose_name=_("class session"),
        help_text=_("The class session for which hours were consumed"),
    )

    purchase_transaction: models.ForeignKey = models.ForeignKey(
        PurchaseTransaction,
        on_delete=models.CASCADE,
        related_name="hour_consumptions",
        verbose_name=_("purchase transaction"),
        help_text=_("Original purchase transaction from which hours were consumed"),
    )

    hours_consumed: models.DecimalField = models.DecimalField(
        _("hours consumed"),
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Actual hours consumed during the session"),
    )

    hours_originally_reserved: models.DecimalField = models.DecimalField(
        _("hours originally reserved"),
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Hours originally reserved/scheduled for the session"),
    )

    consumed_at: models.DateTimeField = models.DateTimeField(
        _("consumed at"),
        auto_now_add=True,
        help_text=_("Timestamp when the consumption was recorded"),
    )

    # Refund functionality
    is_refunded: models.BooleanField = models.BooleanField(
        _("is refunded"),
        default=False,
        help_text=_("Whether this consumption has been refunded"),
    )

    refund_reason: models.TextField = models.TextField(
        _("refund reason"),
        blank=True,
        help_text=_("Reason for the refund (if applicable)"),
    )

    # Audit timestamps
    created_at: models.DateTimeField = models.DateTimeField(
        _("created at"), auto_now_add=True
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        _("updated at"), auto_now=True
    )

    class Meta:
        verbose_name = _("Hour Consumption")
        verbose_name_plural = _("Hour Consumptions")
        ordering = ["-consumed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student_account", "class_session"],
                name="unique_student_session_consumption"
            )
        ]
        indexes = [
            models.Index(fields=["student_account", "consumed_at"]),
            models.Index(fields=["class_session"]),
            models.Index(fields=["purchase_transaction"]),
            models.Index(fields=["is_refunded"]),
        ]

    def __str__(self) -> str:
        return (
            f"Hour consumption: {self.student_account.student.name} - "
            f"{self.hours_consumed}h consumed for session on {self.class_session.date}"
        )

    @property
    def hours_difference(self) -> Decimal:
        """
        Calculate the difference between originally reserved and actually consumed hours.
        
        Returns:
            Decimal: Positive value indicates refund due (early ending),
                    negative value indicates overtime,
                    zero indicates exact match.
        """
        return self.hours_originally_reserved - self.hours_consumed

    def process_refund(self, reason: str) -> Decimal:
        """
        Process a refund for this consumption record.
        
        Args:
            reason: The reason for the refund
            
        Returns:
            Decimal: The amount of hours refunded (0 if no refund due)
            
        Raises:
            ValueError: If consumption has already been refunded
        """
        if self.is_refunded:
            raise ValueError("This consumption has already been refunded")
        
        refund_hours = self.hours_difference
        
        # Only process refund if there are hours to refund (positive difference)
        if refund_hours > Decimal("0.00"):
            # Update the student account balance
            self.student_account.hours_consumed -= refund_hours
            self.student_account.save(update_fields=["hours_consumed", "updated_at"])
            
            # Mark this consumption as refunded
            self.is_refunded = True
            self.refund_reason = reason
            self.save(update_fields=["is_refunded", "refund_reason", "updated_at"])
            
            return refund_hours
        
        # No refund due
        return Decimal("0.00")

    def save(self, *args, **kwargs):
        """
        Override save to update student account balance when consumption is created.
        """
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Update student account balance on creation
        if is_new:
            self.student_account.hours_consumed += self.hours_consumed
            self.student_account.save(update_fields=["hours_consumed", "updated_at"])

    def clean(self) -> None:
        """Validate consumption data."""
        super().clean()
        
        # Ensure hours are not negative (already handled by validators, but double-check)
        if self.hours_consumed < Decimal("0.00"):
            raise ValidationError(_("Hours consumed cannot be negative"))
        
        if self.hours_originally_reserved < Decimal("0.00"):
            raise ValidationError(_("Hours originally reserved cannot be negative"))
        
        # Ensure the student account belongs to one of the session students
        if hasattr(self, 'class_session') and hasattr(self, 'student_account'):
            session_students = self.class_session.students.all()
            if self.student_account.student not in session_students:
                raise ValidationError(
                    _("Student account must belong to a student in the class session")
                )


class Receipt(models.Model):
    """
    Receipt model for tracking generated receipts for student purchases.
    
    Provides audit trail and PDF storage for all generated receipts,
    supporting both automatic and manual receipt generation.
    """
    
    student: models.ForeignKey = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="receipts",
        verbose_name=_("student"),
        help_text=_("Student who received this receipt"),
    )
    
    transaction: models.ForeignKey = models.ForeignKey(
        PurchaseTransaction,
        on_delete=models.CASCADE,
        related_name="receipts",
        verbose_name=_("transaction"),
        help_text=_("Purchase transaction this receipt is for"),
    )
    
    receipt_number: models.CharField = models.CharField(
        _("receipt number"),
        max_length=50,
        unique=True,
        help_text=_("Unique receipt identifier"),
    )
    
    amount: models.DecimalField = models.DecimalField(
        _("amount"),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Receipt amount in euros"),
    )
    
    generated_at: models.DateTimeField = models.DateTimeField(
        _("generated at"),
        auto_now_add=True,
        help_text=_("When the receipt was generated"),
    )
    
    pdf_file: models.FileField = models.FileField(
        _("PDF file"),
        upload_to="receipts/%Y/%m/",
        null=True,
        blank=True,
        help_text=_("Generated PDF receipt file"),
    )
    
    is_valid: models.BooleanField = models.BooleanField(
        _("is valid"),
        default=True,
        help_text=_("Whether this receipt is still valid"),
    )
    
    metadata: models.JSONField = models.JSONField(
        _("metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional receipt data in JSON format"),
    )
    
    # Audit timestamps
    created_at: models.DateTimeField = models.DateTimeField(
        _("created at"), auto_now_add=True
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        _("updated at"), auto_now=True
    )
    
    class Meta:
        verbose_name = _("Receipt")
        verbose_name_plural = _("Receipts")
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["student", "generated_at"]),
            models.Index(fields=["receipt_number"]),
            models.Index(fields=["transaction"]),
        ]
    
    def __str__(self) -> str:
        return f"Receipt {self.receipt_number} - €{self.amount} for {self.student.name}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate receipt number if not provided."""
        if not self.receipt_number:
            self.receipt_number = self._generate_receipt_number()
        super().save(*args, **kwargs)
    
    def _generate_receipt_number(self) -> str:
        """Generate unique receipt number."""
        import uuid
        from django.utils import timezone
        
        # Format: RCP-YYYY-XXXXXXXX (e.g., RCP-2025-A1B2C3D4)
        year = timezone.now().year
        unique_id = str(uuid.uuid4()).replace('-', '').upper()[:8]
        return f"RCP-{year}-{unique_id}"
    
    def clean(self) -> None:
        """Validate receipt data."""
        super().clean()
        
        # Ensure amount matches transaction amount
        if self.transaction and self.amount != self.transaction.amount:
            raise ValidationError(
                _("Receipt amount must match transaction amount")
            )
        
        # Ensure transaction belongs to the same student
        if self.transaction and self.student != self.transaction.student:
            raise ValidationError(
                _("Receipt student must match transaction student")
            )


class StoredPaymentMethod(models.Model):
    """
    Stored payment method model for secure payment method management.
    
    Uses Stripe tokenization to securely store payment methods without
    handling sensitive card data directly, maintaining PCI compliance.
    """
    
    student: models.ForeignKey = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="stored_payment_methods",
        verbose_name=_("student"),
        help_text=_("Student who owns this payment method"),
    )
    
    stripe_payment_method_id: models.CharField = models.CharField(
        _("Stripe payment method ID"),
        max_length=255,
        unique=True,
        help_text=_("Stripe PaymentMethod ID for secure storage"),
    )
    
    card_brand: models.CharField = models.CharField(
        _("card brand"),
        max_length=20,
        blank=True,
        help_text=_("Card brand (e.g., visa, mastercard)"),
    )
    
    card_last4: models.CharField = models.CharField(
        _("card last 4 digits"),
        max_length=4,
        blank=True,
        help_text=_("Last 4 digits of the card for display"),
    )
    
    card_exp_month: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(
        _("card expiration month"),
        null=True,
        blank=True,
        help_text=_("Card expiration month (1-12)"),
    )
    
    card_exp_year: models.PositiveIntegerField = models.PositiveIntegerField(
        _("card expiration year"),
        null=True,
        blank=True,
        help_text=_("Card expiration year"),
    )
    
    is_default: models.BooleanField = models.BooleanField(
        _("is default"),
        default=False,
        help_text=_("Whether this is the default payment method"),
    )
    
    is_active: models.BooleanField = models.BooleanField(
        _("is active"),
        default=True,
        help_text=_("Whether this payment method is active"),
    )
    
    # Audit timestamps
    created_at: models.DateTimeField = models.DateTimeField(
        _("created at"), auto_now_add=True
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        _("updated at"), auto_now=True
    )
    
    class Meta:
        verbose_name = _("Stored Payment Method")
        verbose_name_plural = _("Stored Payment Methods")
        ordering = ["-is_default", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student"],
                condition=models.Q(is_default=True),
                name="unique_default_payment_method_per_student"
            )
        ]
        indexes = [
            models.Index(fields=["student", "is_active"]),
            models.Index(fields=["stripe_payment_method_id"]),
        ]
    
    def __str__(self) -> str:
        default_text = " (Default)" if self.is_default else ""
        return f"{self.card_brand.title()} ****{self.card_last4} - {self.student.name}{default_text}"
    
    @property
    def is_expired(self) -> bool:
        """Check if the payment method is expired."""
        if not self.card_exp_month or not self.card_exp_year:
            return False
        
        from django.utils import timezone
        now = timezone.now()
        
        # Card expires at the end of the expiration month
        if self.card_exp_year < now.year:
            return True
        elif self.card_exp_year == now.year and self.card_exp_month < now.month:
            return True
        
        return False
    
    def save(self, *args, **kwargs):
        """Override save to handle default payment method logic."""
        # If this is being set as default, unset other defaults for the same student
        if self.is_default:
            StoredPaymentMethod.objects.filter(
                student=self.student,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def clean(self) -> None:
        """Validate payment method data."""
        super().clean()
        
        # Validate expiration month
        if self.card_exp_month is not None and (self.card_exp_month < 1 or self.card_exp_month > 12):
            raise ValidationError(
                _("Card expiration month must be between 1 and 12")
            )
        
        # Validate last 4 digits format
        if self.card_last4 and not self.card_last4.isdigit():
            raise ValidationError(
                _("Card last 4 digits must contain only numbers")
            )
