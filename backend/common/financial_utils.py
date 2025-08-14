"""
Financial calculation utilities for ensuring consistent precision across all financial operations.

This module provides standardized financial calculation methods that ensure:
- All currency amounts use exactly 2 decimal places
- All hour calculations use 2 decimal places for consistency
- Proper rounding using ROUND_HALF_UP for financial accuracy
- Consistent behavior across all financial operations in the platform
"""

from decimal import ROUND_HALF_UP, Decimal


class FinancialCalculation:
    """Utility class for consistent financial calculations and rounding."""

    # Standard precision for different calculation types
    CURRENCY_PRECISION = Decimal("0.01")  # 2 decimal places for currency
    HOURS_PRECISION = Decimal("0.01")  # 2 decimal places for hours consistency

    @staticmethod
    def round_currency(amount):
        """
        Round currency amounts to exactly 2 decimal places using ROUND_HALF_UP.

        This ensures consistent financial precision across all monetary calculations
        in the platform, following standard financial rounding practices.

        Args:
            amount: Decimal or numeric value to round

        Returns:
            Decimal: Amount rounded to 2 decimal places

        Examples:
            >>> FinancialCalculation.round_currency(Decimal('25.555'))
            Decimal('25.56')
            >>> FinancialCalculation.round_currency(Decimal('107.555'))
            Decimal('107.56')
        """
        if amount is None:
            return Decimal("0.00")
        return Decimal(amount).quantize(FinancialCalculation.CURRENCY_PRECISION, rounding=ROUND_HALF_UP)

    @staticmethod
    def round_hours(hours):
        """
        Round hour values to exactly 2 decimal places for consistency.

        While hours could theoretically have more precision, we standardize
        to 2 decimal places to maintain consistency with currency calculations
        and avoid precision mismatches in business logic.

        Args:
            hours: Decimal or numeric value representing hours

        Returns:
            Decimal: Hours rounded to 2 decimal places

        Examples:
            >>> FinancialCalculation.round_hours(Decimal('1.555'))
            Decimal('1.56')
        """
        if hours is None:
            return Decimal("0.00")
        return Decimal(hours).quantize(FinancialCalculation.HOURS_PRECISION, rounding=ROUND_HALF_UP)

    @staticmethod
    def multiply_currency(amount1, amount2):
        """
        Multiply two values and round result to currency precision.

        This is used for calculations like hourly_rate * hours or applying
        percentage bonuses to base amounts.

        Args:
            amount1: First value (Decimal or numeric)
            amount2: Second value (Decimal or numeric)

        Returns:
            Decimal: Product rounded to 2 decimal places
        """
        if amount1 is None or amount2 is None:
            return Decimal("0.00")
        result = Decimal(amount1) * Decimal(amount2)
        return FinancialCalculation.round_currency(result)

    @staticmethod
    def add_currency(*amounts):
        """
        Add multiple currency amounts and round result to currency precision.

        Useful for combining base amounts, bonuses, fees, etc. while ensuring
        the final result maintains proper precision.

        Args:
            *amounts: Variable number of amounts to add

        Returns:
            Decimal: Sum rounded to 2 decimal places
        """
        total = Decimal("0.00")
        for amount in amounts:
            if amount is not None:
                total += Decimal(amount)
        return FinancialCalculation.round_currency(total)

    @staticmethod
    def subtract_currency(amount1, amount2):
        """
        Subtract two currency amounts and round result to currency precision.

        Args:
            amount1: Amount to subtract from (Decimal or numeric)
            amount2: Amount to subtract (Decimal or numeric)

        Returns:
            Decimal: Difference rounded to 2 decimal places
        """
        if amount1 is None:
            amount1 = Decimal("0.00")
        if amount2 is None:
            amount2 = Decimal("0.00")
        result = Decimal(amount1) - Decimal(amount2)
        return FinancialCalculation.round_currency(result)

    @staticmethod
    def divide_currency(amount, divisor):
        """
        Divide a currency amount and round result to currency precision.

        Used for prorated calculations, splitting amounts, etc.

        Args:
            amount: Amount to divide (Decimal or numeric)
            divisor: Value to divide by (Decimal or numeric)

        Returns:
            Decimal: Quotient rounded to 2 decimal places

        Raises:
            ValueError: If divisor is zero
        """
        if divisor is None or Decimal(divisor) == 0:
            raise ValueError("Cannot divide by zero")
        if amount is None:
            amount = Decimal("0.00")
        result = Decimal(amount) / Decimal(divisor)
        return FinancialCalculation.round_currency(result)

    @staticmethod
    def apply_percentage(base_amount, percentage):
        """
        Apply a percentage to a base amount with proper rounding.

        Used for calculating bonuses, discounts, taxes, etc.

        Args:
            base_amount: Base amount to apply percentage to
            percentage: Percentage as decimal (0.10 for 10%)

        Returns:
            Decimal: Percentage amount rounded to 2 decimal places
        """
        return FinancialCalculation.multiply_currency(base_amount, percentage)


# Legacy function aliases for backward compatibility
def round_currency(amount):
    """Legacy alias for FinancialCalculation.round_currency"""
    return FinancialCalculation.round_currency(amount)


def round_hours(hours):
    """Legacy alias for FinancialCalculation.round_hours"""
    return FinancialCalculation.round_hours(hours)
