"""
Renewal Payment Service for handling one-click renewals and quick top-ups.

This service provides renewal functionality for existing subscriptions and
quick hour top-up purchases using saved payment methods with Stripe Customer objects.
"""

from decimal import Decimal
import logging
from typing import Any, ClassVar

# Cross-app models will be loaded at runtime using apps.get_model()
from django.db import transaction
from django.utils import timezone
import stripe

from finances.models import (
    PurchaseTransaction,
    StoredPaymentMethod,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)

from .payment_method_service import PaymentMethodService
from .stripe_base import StripeService

logger = logging.getLogger(__name__)


class RenewalPaymentService:
    """
    Service for managing subscription renewals and quick hour top-ups.

    Features:
    - One-click subscription renewal using saved payment methods
    - Quick hour top-up with predefined packages (5, 10, 20 hours)
    - Secure payment processing using Stripe Customers and saved payment methods
    - Comprehensive error handling and transaction safety
    - Integration with existing pricing and balance systems
    """

    # Predefined quick top-up packages (hours: price)
    QUICK_TOPUP_PACKAGES: ClassVar = {
        Decimal("5.00"): Decimal("50.00"),  # 5 hours for €50
        Decimal("10.00"): Decimal("95.00"),  # 10 hours for €95 (5% discount)
        Decimal("20.00"): Decimal("180.00"),  # 20 hours for €180 (10% discount)
    }

    def __init__(self):
        """Initialize the service with Stripe and payment method services."""
        self.stripe_service = StripeService()
        self.payment_method_service = PaymentMethodService()

    def renew_subscription(
        self, student_user, original_transaction_id: int, payment_method_id: int | None = None
    ) -> dict[str, Any]:
        """
        Renew an expired subscription using the same plan configuration.

        Args:
            student_user: Student user renewing the subscription
            original_transaction_id: ID of the original transaction to renew
            payment_method_id: Optional specific payment method ID (uses default if None)

        Returns:
            Dict containing success status, new transaction details, or error information
        """
        logger.info(
            f"Starting subscription renewal for student {student_user.id}, "
            f"original transaction {original_transaction_id}"
        )

        try:
            # Validate and get original transaction
            original_transaction = self._get_renewable_transaction(student_user, original_transaction_id)
            if isinstance(original_transaction, dict):  # Error case
                return original_transaction

            # Get payment method
            payment_method = self._get_payment_method_for_renewal(student_user, payment_method_id)
            if isinstance(payment_method, dict):  # Error case
                return payment_method

            # Create renewal payment intent
            renewal_intent = self._create_renewal_payment_intent(
                student_user=student_user, original_transaction=original_transaction, payment_method=payment_method
            )

            if not renewal_intent["success"]:
                return renewal_intent

            # Confirm payment immediately for saved payment methods
            confirmation_result = self._confirm_renewal_payment(
                renewal_intent["payment_intent_id"], payment_method.stripe_payment_method_id
            )

            if not confirmation_result["success"]:
                return confirmation_result

            return {
                "success": True,
                "transaction_id": renewal_intent["transaction_id"],
                "payment_intent_id": renewal_intent["payment_intent_id"],
                "message": "Subscription renewed successfully",
            }

        except Exception as e:
            logger.error(
                f"Unexpected error during subscription renewal for student {student_user.id}: {e}", exc_info=True
            )
            return {"success": False, "error_type": "renewal_error", "message": f"Subscription renewal failed: {e!s}"}

    def quick_topup(self, student_user, hours: Decimal, payment_method_id: int | None = None) -> dict[str, Any]:
        """
        Purchase additional hours using quick top-up packages.

        Args:
            student_user: Student user purchasing additional hours
            hours: Number of hours to purchase (must be in QUICK_TOPUP_PACKAGES)
            payment_method_id: Optional specific payment method ID (uses default if None)

        Returns:
            Dict containing success status, transaction details, or error information
        """
        logger.info(f"Starting quick top-up for student {student_user.id}, hours: {hours}")

        try:
            # Validate hours package
            if hours not in self.QUICK_TOPUP_PACKAGES:
                return {
                    "success": False,
                    "error_type": "invalid_package",
                    "message": f"Invalid hours package. Available: {list(self.QUICK_TOPUP_PACKAGES.keys())}",
                }

            price = self.QUICK_TOPUP_PACKAGES[hours]

            # Get payment method
            payment_method = self._get_payment_method_for_renewal(student_user, payment_method_id)
            if isinstance(payment_method, dict):  # Error case
                return payment_method

            # Create quick top-up payment intent
            topup_intent = self._create_topup_payment_intent(
                student_user=student_user, hours=hours, price=price, payment_method=payment_method
            )

            if not topup_intent["success"]:
                return topup_intent

            # Confirm payment immediately for saved payment methods
            confirmation_result = self._confirm_renewal_payment(
                topup_intent["payment_intent_id"], payment_method.stripe_payment_method_id
            )

            if not confirmation_result["success"]:
                return confirmation_result

            return {
                "success": True,
                "transaction_id": topup_intent["transaction_id"],
                "payment_intent_id": topup_intent["payment_intent_id"],
                "hours_purchased": hours,
                "amount_paid": price,
                "message": f"Successfully purchased {hours} hours for €{price}",
            }

        except Exception as e:
            logger.error(f"Unexpected error during quick top-up for student {student_user.id}: {e}", exc_info=True)
            return {"success": False, "error_type": "topup_error", "message": f"Quick top-up failed: {e!s}"}

    def get_available_topup_packages(self) -> list[dict[str, Any]]:
        """
        Get list of available quick top-up packages.

        Returns:
            List of dictionaries containing package details
        """
        packages = []
        for hours, price in self.QUICK_TOPUP_PACKAGES.items():
            packages.append(
                {
                    "hours": float(hours),
                    "price": float(price),
                    "price_per_hour": float(price / hours),
                    "savings_percent": self._calculate_savings_percent(hours, price),
                }
            )

        return packages

    def _get_renewable_transaction(self, student_user, transaction_id: int) -> dict[str, Any] | PurchaseTransaction:
        """
        Get and validate a transaction for renewal.

        Args:
            student_user: Student user requesting renewal
            transaction_id: Transaction ID to renew

        Returns:
            PurchaseTransaction instance or error dict
        """
        try:
            transaction = PurchaseTransaction.objects.get(id=transaction_id, student=student_user)
        except PurchaseTransaction.DoesNotExist:
            return {
                "success": False,
                "error_type": "transaction_not_found",
                "message": "Original transaction not found",
            }

        # Validate transaction is renewable
        if transaction.payment_status != TransactionPaymentStatus.COMPLETED:
            return {
                "success": False,
                "error_type": "invalid_transaction_status",
                "message": "Only completed transactions can be renewed",
            }

        if transaction.transaction_type != TransactionType.SUBSCRIPTION:
            return {
                "success": False,
                "error_type": "invalid_transaction_type",
                "message": "Only subscription transactions can be renewed",
            }

        return transaction

    def _get_payment_method_for_renewal(
        self, student_user, payment_method_id: int | None
    ) -> dict[str, Any] | StoredPaymentMethod:
        """
        Get and validate payment method for renewal.

        Args:
            student_user: Student user making the payment
            payment_method_id: Optional specific payment method ID

        Returns:
            StoredPaymentMethod instance or error dict
        """
        if payment_method_id:
            try:
                payment_method = StoredPaymentMethod.objects.get(
                    id=payment_method_id, student=student_user, is_active=True
                )
            except StoredPaymentMethod.DoesNotExist:
                return {
                    "success": False,
                    "error_type": "payment_method_not_found",
                    "message": "Specified payment method not found",
                }
        else:
            # Use default payment method
            payment_method = self.payment_method_service.get_default_payment_method(student_user)

            if not payment_method:
                return {
                    "success": False,
                    "error_type": "no_default_payment_method",
                    "message": "No default payment method found. Please add a payment method first.",
                }

        # Check if payment method is expired
        if payment_method.is_expired:
            return {
                "success": False,
                "error_type": "payment_method_expired",
                "message": "Payment method has expired. Please update your payment method.",
            }

        return payment_method

    def _create_renewal_payment_intent(
        self, student_user, original_transaction: PurchaseTransaction, payment_method: StoredPaymentMethod
    ) -> dict[str, Any]:
        """
        Create a Stripe payment intent for subscription renewal.

        Args:
            student_user: Student user making the renewal
            original_transaction: Original transaction being renewed
            payment_method: Payment method to use for renewal

        Returns:
            Dict containing payment intent details or error information
        """
        try:
            amount_cents = int(original_transaction.amount * 100)

            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="eur",
                customer=payment_method.stripe_customer_id,
                payment_method=payment_method.stripe_payment_method_id,
                confirmation_method="manual",
                confirm=False,  # We'll confirm manually after creating transaction
                metadata={
                    "renewal_type": "subscription",
                    "original_transaction_id": str(original_transaction.id),
                    "student_id": str(student_user.id),
                    "payment_method_id": str(payment_method.id),
                },
            )

            # Create new transaction record
            with transaction.atomic():
                new_transaction = PurchaseTransaction.objects.create(
                    student=student_user,
                    transaction_type=original_transaction.transaction_type,
                    amount=original_transaction.amount,
                    payment_status=TransactionPaymentStatus.PROCESSING,
                    stripe_payment_intent_id=payment_intent.id,
                    stripe_customer_id=payment_method.stripe_customer_id,
                    expires_at=original_transaction.expires_at,
                    metadata={
                        **original_transaction.metadata,
                        "renewal_type": "subscription",
                        "original_transaction_id": original_transaction.id,
                        "renewal_created_at": timezone.now().isoformat(),
                    },
                )

            logger.info(f"Created renewal payment intent {payment_intent.id} for transaction {new_transaction.id}")

            return {
                "success": True,
                "payment_intent_id": payment_intent.id,
                "transaction_id": new_transaction.id,
                "client_secret": payment_intent.client_secret,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating renewal payment intent: {e}")
            return self.stripe_service.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Error creating renewal payment intent: {e}")
            return {
                "success": False,
                "error_type": "payment_intent_creation_error",
                "message": f"Failed to create renewal payment intent: {e!s}",
            }

    def _create_topup_payment_intent(
        self, student_user, hours: Decimal, price: Decimal, payment_method: StoredPaymentMethod
    ) -> dict[str, Any]:
        """
        Create a Stripe payment intent for quick top-up.

        Args:
            student_user: Student user making the top-up
            hours: Number of hours being purchased
            price: Price for the hours
            payment_method: Payment method to use for payment

        Returns:
            Dict containing payment intent details or error information
        """
        try:
            amount_cents = int(price * 100)

            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="eur",
                customer=payment_method.stripe_customer_id,
                payment_method=payment_method.stripe_payment_method_id,
                confirmation_method="manual",
                confirm=False,  # We'll confirm manually after creating transaction
                metadata={
                    "renewal_type": "quick_topup",
                    "hours": str(hours),
                    "student_id": str(student_user.id),
                    "payment_method_id": str(payment_method.id),
                },
            )

            # Create new transaction record
            with transaction.atomic():
                # Set expiration for quick top-up (1 year from now)
                expires_at = timezone.now() + timezone.timedelta(days=365)

                new_transaction = PurchaseTransaction.objects.create(
                    student=student_user,
                    transaction_type=TransactionType.PACKAGE,
                    amount=price,
                    payment_status=TransactionPaymentStatus.PROCESSING,
                    stripe_payment_intent_id=payment_intent.id,
                    stripe_customer_id=payment_method.stripe_customer_id,
                    expires_at=expires_at,
                    metadata={
                        "renewal_type": "quick_topup",
                        "hours": str(hours),
                        "package_type": "quick_topup",
                        "topup_created_at": timezone.now().isoformat(),
                    },
                )

            logger.info(
                f"Created quick top-up payment intent {payment_intent.id} "
                f"for transaction {new_transaction.id} ({hours} hours)"
            )

            return {
                "success": True,
                "payment_intent_id": payment_intent.id,
                "transaction_id": new_transaction.id,
                "client_secret": payment_intent.client_secret,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating top-up payment intent: {e}")
            return self.stripe_service.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Error creating top-up payment intent: {e}")
            return {
                "success": False,
                "error_type": "payment_intent_creation_error",
                "message": f"Failed to create top-up payment intent: {e!s}",
            }

    def _confirm_renewal_payment(self, payment_intent_id: str, stripe_payment_method_id: str) -> dict[str, Any]:
        """
        Confirm a renewal payment using the saved payment method.

        Args:
            payment_intent_id: Stripe PaymentIntent ID to confirm
            stripe_payment_method_id: Stripe PaymentMethod ID to use

        Returns:
            Dict containing confirmation result
        """
        try:
            # Confirm the payment intent
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id, payment_method=stripe_payment_method_id)

            # Check if confirmation was successful
            if payment_intent.status == "succeeded":
                logger.info(f"Payment intent {payment_intent_id} confirmed successfully")

                # Update transaction status (this will be handled by webhook in production)
                # For immediate response, we update here too
                try:
                    with transaction.atomic():
                        purchase_transaction = PurchaseTransaction.objects.get(
                            stripe_payment_intent_id=payment_intent_id
                        )
                        purchase_transaction.payment_status = TransactionPaymentStatus.COMPLETED
                        purchase_transaction.save(update_fields=["payment_status", "updated_at"])

                        # Credit hours to student account if it's a package
                        if purchase_transaction.transaction_type == TransactionType.PACKAGE:
                            self._credit_hours_to_account(purchase_transaction)

                        # Update account balance
                        self._update_account_balance(purchase_transaction)

                except PurchaseTransaction.DoesNotExist:
                    logger.error(f"Transaction not found for payment intent {payment_intent_id}")

                return {"success": True, "payment_intent_id": payment_intent_id, "status": payment_intent.status}
            else:
                logger.warning(
                    f"Payment intent {payment_intent_id} confirmation failed with status: {payment_intent.status}"
                )
                return {
                    "success": False,
                    "error_type": "payment_confirmation_failed",
                    "message": f"Payment confirmation failed: {payment_intent.status}",
                }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment {payment_intent_id}: {e}")
            return self.stripe_service.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Error confirming payment {payment_intent_id}: {e}")
            return {
                "success": False,
                "error_type": "payment_confirmation_error",
                "message": f"Failed to confirm payment: {e!s}",
            }

    def _credit_hours_to_account(self, purchase_transaction: PurchaseTransaction) -> None:
        """
        Credit hours to student account from completed package transaction.

        Args:
            purchase_transaction: Completed transaction containing hour information
        """
        # Get or create student account balance
        student_balance, created = StudentAccountBalance.objects.get_or_create(
            student=purchase_transaction.student,
            defaults={
                "hours_purchased": Decimal("0.00"),
                "hours_consumed": Decimal("0.00"),
                "balance_amount": Decimal("0.00"),
            },
        )

        # Extract hours from metadata
        hours_to_add = Decimal("0.00")
        if "hours" in purchase_transaction.metadata:
            try:
                hours_to_add = Decimal(str(purchase_transaction.metadata["hours"]))
            except (ValueError, TypeError):
                logger.warning(f"Invalid hours value in transaction {purchase_transaction.id} metadata")

        # Add hours to account
        if hours_to_add > 0:
            student_balance.hours_purchased += hours_to_add
            student_balance.save(update_fields=["hours_purchased", "updated_at"])

            logger.info(f"Added {hours_to_add} hours to account for student {purchase_transaction.student.id}")

    def _update_account_balance(self, purchase_transaction: PurchaseTransaction) -> None:
        """
        Update student account balance with payment amount.

        Args:
            purchase_transaction: Completed transaction
        """
        # Get or create student account balance
        student_balance, created = StudentAccountBalance.objects.get_or_create(
            student=purchase_transaction.student,
            defaults={
                "hours_purchased": Decimal("0.00"),
                "hours_consumed": Decimal("0.00"),
                "balance_amount": Decimal("0.00"),
            },
        )

        # Add payment amount to balance
        student_balance.balance_amount += purchase_transaction.amount
        student_balance.save(update_fields=["balance_amount", "updated_at"])

        logger.info(f"Added €{purchase_transaction.amount} to balance for student {purchase_transaction.student.id}")

    def _calculate_savings_percent(self, hours: Decimal, price: Decimal) -> float:
        """
        Calculate savings percentage compared to base rate.

        Args:
            hours: Number of hours in package
            price: Price of the package

        Returns:
            float: Savings percentage (0 if no savings)
        """
        # Assume base rate of €10/hour for savings calculation
        base_rate = Decimal("10.00")
        base_price = hours * base_rate

        if base_price <= price:
            return 0.0

        savings = base_price - price
        return float((savings / base_price) * 100)


class RenewalPaymentError(Exception):
    """Exception raised for renewal payment errors."""

    pass
