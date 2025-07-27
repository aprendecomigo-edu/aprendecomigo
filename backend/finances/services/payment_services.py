"""
Services for calculating teacher payments and managing billing logic.
"""

from decimal import Decimal

from django.db import models, transaction

from ..models import (
    ClassSession,
    CompensationRuleType,
    SchoolBillingSettings,
    TeacherCompensationRule,
    TeacherPaymentEntry,
    TrialCostAbsorption,
)


class TeacherPaymentCalculator:
    """Service class for calculating teacher payments."""

    @staticmethod
    def get_applicable_rate(
        session: ClassSession,
    ) -> tuple[Decimal, TeacherCompensationRule | None]:
        """
        Get the applicable hourly rate for a given session.

        Args:
            session: The class session to calculate rate for

        Returns:
            Tuple of (rate, compensation_rule) where rate is the hourly rate
            and compensation_rule is the rule that was applied (or None for trial classes)
        """
        # Handle trial classes based on school settings
        if session.is_trial:
            try:
                billing_settings = SchoolBillingSettings.objects.get(school=session.school)
                if billing_settings.trial_cost_absorption == TrialCostAbsorption.SCHOOL:
                    return Decimal("0.00"), None
                elif billing_settings.trial_cost_absorption == TrialCostAbsorption.TEACHER:
                    # Continue with normal calculation
                    pass
                elif billing_settings.trial_cost_absorption == TrialCostAbsorption.SPLIT:
                    # Calculate normal rate and then split it
                    rate, rule = TeacherPaymentCalculator._get_session_rate(session)
                    return rate * Decimal("0.5"), rule
            except SchoolBillingSettings.DoesNotExist:
                # Default to school absorbing cost
                return Decimal("0.00"), None

        return TeacherPaymentCalculator._get_session_rate(session)

    @staticmethod
    def _get_session_rate(session: ClassSession) -> tuple[Decimal, TeacherCompensationRule | None]:
        """Internal method to get the base rate for a session."""
        # Get all active compensation rules for this teacher at this school
        rules = TeacherCompensationRule.objects.filter(
            teacher=session.teacher,
            school=session.school,
            is_active=True,
            effective_from__lte=session.date,
        ).filter(
            models.Q(effective_until__isnull=True) | models.Q(effective_until__gte=session.date)
        )

        # Priority 1: Group class rate (if it's a group session)
        if session.session_type == "group":
            group_rule = rules.filter(rule_type=CompensationRuleType.GROUP_CLASS).first()
            if group_rule and group_rule.rate_per_hour:
                return group_rule.rate_per_hour, group_rule

        # Priority 2: Grade-specific rate
        grade_rule = rules.filter(
            rule_type=CompensationRuleType.GRADE_SPECIFIC, grade_level=session.grade_level
        ).first()
        if grade_rule and grade_rule.rate_per_hour:
            return grade_rule.rate_per_hour, grade_rule

        # Priority 3: General grade-specific rate (if session has mixed grades)
        if session.grade_level == "mixed":
            # For mixed grade sessions, use the highest grade-specific rate available
            highest_grade_rule = (
                rules.filter(
                    rule_type=CompensationRuleType.GRADE_SPECIFIC, rate_per_hour__isnull=False
                )
                .order_by("-rate_per_hour")
                .first()
            )
            if highest_grade_rule:
                return highest_grade_rule.rate_per_hour, highest_grade_rule

        # Priority 4: Teacher's default hourly rate from TeacherProfile
        if session.teacher.hourly_rate:
            return session.teacher.hourly_rate, None

        # Default: No rate found
        return Decimal("0.00"), None

    @staticmethod
    @transaction.atomic
    def calculate_session_payment(session: ClassSession) -> TeacherPaymentEntry:
        """
        Calculate and create a payment entry for a given session.

        Args:
            session: The completed class session

        Returns:
            The created TeacherPaymentEntry
        """
        if session.status != "completed":
            raise ValueError("Can only calculate payments for completed sessions")

        # Check if payment entry already exists
        if hasattr(session, "payment_entry"):
            return session.payment_entry

        # Get the applicable rate
        rate, rule = TeacherPaymentCalculator.get_applicable_rate(session)

        # Calculate hours and amount
        hours = session.duration_hours
        amount = rate * hours

        # Determine billing period (YYYY-MM format)
        billing_period = session.date.strftime("%Y-%m")

        # Create calculation notes
        notes = f"Rate: €{rate}/hour, Hours: {hours}, Session: {session.get_session_type_display()}"
        if session.is_trial:
            notes += " (Trial session)"
        if rule:
            notes += f", Rule: {rule.get_rule_type_display()}"
            if rule.grade_level:
                notes += f" Grade {rule.grade_level}"

        # Create payment entry
        payment_entry = TeacherPaymentEntry.objects.create(
            session=session,
            teacher=session.teacher,
            school=session.school,
            billing_period=billing_period,
            hours_taught=hours,
            rate_applied=rate,
            amount_earned=amount,
            compensation_rule=rule,
            calculation_notes=notes,
        )

        return payment_entry

    @staticmethod
    def calculate_monthly_total(teacher, school, year: int, month: int) -> dict:
        """
        Calculate the total monthly payment for a teacher at a specific school.

        Args:
            teacher: TeacherProfile instance
            school: School instance
            year: Year (e.g., 2024)
            month: Month (1-12)

        Returns:
            Dictionary with payment breakdown
        """
        billing_period = f"{year:04d}-{month:02d}"

        # Get all payment entries for this period
        payment_entries = TeacherPaymentEntry.objects.filter(
            teacher=teacher, school=school, billing_period=billing_period
        )

        # Calculate totals
        total_hours = sum(entry.hours_taught for entry in payment_entries)
        total_amount = sum(entry.amount_earned for entry in payment_entries)
        session_count = payment_entries.count()

        # Break down by session type
        individual_entries = payment_entries.filter(session__session_type="individual")
        group_entries = payment_entries.filter(session__session_type="group")
        trial_entries = payment_entries.filter(session__is_trial=True)

        return {
            "billing_period": billing_period,
            "teacher": teacher,
            "school": school,
            "total_hours": total_hours,
            "total_amount": total_amount,
            "session_count": session_count,
            "individual_sessions": {
                "count": individual_entries.count(),
                "hours": sum(entry.hours_taught for entry in individual_entries),
                "amount": sum(entry.amount_earned for entry in individual_entries),
            },
            "group_sessions": {
                "count": group_entries.count(),
                "hours": sum(entry.hours_taught for entry in group_entries),
                "amount": sum(entry.amount_earned for entry in group_entries),
            },
            "trial_sessions": {
                "count": trial_entries.count(),
                "hours": sum(entry.hours_taught for entry in trial_entries),
                "amount": sum(entry.amount_earned for entry in trial_entries),
            },
            "payment_entries": payment_entries,
        }


class BulkPaymentProcessor:
    """Service for processing payments in bulk."""

    @staticmethod
    @transaction.atomic
    def process_completed_sessions(school=None, start_date=None, end_date=None) -> dict:
        """
        Process payment calculations for all completed sessions in a date range.

        Args:
            school: Optional school to filter by
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary with processing results
        """
        # Build query for completed sessions without payment entries
        sessions_query = ClassSession.objects.filter(status="completed", payment_entry__isnull=True)

        if school:
            sessions_query = sessions_query.filter(school=school)
        if start_date:
            sessions_query = sessions_query.filter(date__gte=start_date)
        if end_date:
            sessions_query = sessions_query.filter(date__lte=end_date)

        sessions = sessions_query.select_related("teacher", "school")

        processed_count = 0
        errors = []

        for session in sessions:
            try:
                TeacherPaymentCalculator.calculate_session_payment(session)
                processed_count += 1
            except Exception as e:
                errors.append({"session_id": session.id, "session": str(session), "error": str(e)})

        return {
            "total_sessions": sessions.count(),
            "processed_count": processed_count,
            "errors": errors,
        }
