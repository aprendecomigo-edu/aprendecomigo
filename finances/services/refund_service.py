"""
Refund Service for processing payment refunds through Stripe API.

This service handles complete refund processing including Stripe API integration,
local transaction updates, student balance adjustments, and comprehensive audit logging.
"""

from decimal import Decimal
import logging
from typing import Any

# Cross-app models will be loaded at runtime using apps.get_model()
from django.db import transaction
from django.utils import timezone
import stripe

from finances.models import (
    AdminAction,
    AdminActionType,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
)

from .rate_limiter import stripe_rate_limit
from .stripe_base import StripeService

logger = logging.getLogger(__name__)


class RefundService:
    """
    Service class for processing payment refunds with comprehensive audit logging.

    This service provides centralized refund processing functionality with
    Stripe integration, transaction consistency, and administrative audit trails.
    """

    def __init__(self):
        """
        Initialize RefundService with Stripe integration.

        Raises:
            ValueError: If Stripe configuration is invalid
        """
        self.stripe_service = StripeService()
        logger.info("RefundService initialized successfully")

    def process_refund(
        self,
        transaction_id: int,
        refund_amount: Decimal | None = None,
        reason: str = "",
        admin_user=None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Process a refund for a purchase transaction.

        Args:
            transaction_id: ID of the transaction to refund
            refund_amount: Amount to refund (if None, full refund)
            reason: Reason for the refund
            admin_user: Administrator processing the refund
            metadata: Additional refund metadata

        Returns:
            Dict containing success status and refund details
        """
        logger.info(f"Processing refund for transaction {transaction_id}")

        if metadata is None:
            metadata = {}

        try:
            # Get the transaction to refund
            try:
                purchase_transaction = PurchaseTransaction.objects.select_for_update().get(id=transaction_id)
            except PurchaseTransaction.DoesNotExist:
                logger.error(f"Transaction {transaction_id} not found for refund")
                return {"success": False, "error_type": "transaction_not_found", "message": "Transaction not found"}

            # Validate transaction state
            validation_result = self._validate_refund_eligibility(purchase_transaction, refund_amount)
            if not validation_result["success"]:
                return validation_result

            # Determine refund amount
            if refund_amount is None:
                refund_amount = purchase_transaction.amount

            # Use atomic transaction for consistency
            with transaction.atomic():
                # Process refund with Stripe
                stripe_result = self._process_stripe_refund(purchase_transaction, refund_amount, reason, metadata)

                if not stripe_result["success"]:
                    # Log failed admin action
                    if admin_user:
                        self._log_admin_action(
                            admin_user=admin_user,
                            action_type=AdminActionType.REFUND_FAILED,
                            target_transaction=purchase_transaction,
                            success=False,
                            amount_impacted=refund_amount,
                            result_message=stripe_result.get("message", "Stripe refund failed"),
                            stripe_reference_id=purchase_transaction.stripe_payment_intent_id,
                        )
                    return stripe_result  # type: ignore[no-any-return]

                # Update transaction status
                self._update_transaction_for_refund(purchase_transaction, refund_amount, stripe_result["refund"])

                # Adjust student balance
                self._adjust_student_balance_for_refund(purchase_transaction, refund_amount)

                # Log successful admin action
                if admin_user:
                    self._log_admin_action(
                        admin_user=admin_user,
                        action_type=AdminActionType.REFUND_CREATED,
                        target_transaction=purchase_transaction,
                        success=True,
                        amount_impacted=refund_amount,
                        result_message=f"Refund processed successfully: €{refund_amount}",
                        stripe_reference_id=stripe_result["refund"].id,
                    )

                logger.info(f"Refund processed successfully for transaction {transaction_id}: €{refund_amount}")

                return {
                    "success": True,
                    "refund_id": stripe_result["refund"].id,
                    "refund_amount": refund_amount,
                    "transaction_id": transaction_id,
                    "message": "Refund processed successfully",
                }

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            logger.error(f"Stripe error processing refund: {e}")
            error_result = self.stripe_service.handle_stripe_error(e)

            # Log failed admin action
            if admin_user:
                self._log_admin_action(
                    admin_user=admin_user,
                    action_type=AdminActionType.REFUND_FAILED,
                    target_transaction=purchase_transaction if "purchase_transaction" in locals() else None,
                    success=False,
                    amount_impacted=refund_amount,
                    result_message=f"Stripe error: {error_result.get('message', str(e))}",
                    stripe_reference_id=purchase_transaction.stripe_payment_intent_id  # type: ignore[arg-type]
                    if "purchase_transaction" in locals()
                    else None,
                )

            return error_result  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Unexpected error processing refund: {e}")

            # Log failed admin action
            if admin_user:
                self._log_admin_action(
                    admin_user=admin_user,
                    action_type=AdminActionType.REFUND_FAILED,
                    target_transaction=purchase_transaction if "purchase_transaction" in locals() else None,
                    success=False,
                    amount_impacted=refund_amount,
                    result_message=f"Unexpected error: {e!s}",
                    stripe_reference_id=purchase_transaction.stripe_payment_intent_id  # type: ignore[arg-type]
                    if "purchase_transaction" in locals()
                    else None,
                )

            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while processing refund",
            }

    @stripe_rate_limit("read_operations", "refund_service")
    def get_refund_status(self, refund_id: str) -> dict[str, Any]:
        """
        Get refund status from Stripe.

        Args:
            refund_id: Stripe Refund ID to check

        Returns:
            Dict containing refund status and details
        """
        logger.info(f"Retrieving refund status for refund {refund_id}")

        try:
            refund = stripe.Refund.retrieve(refund_id)

            return {
                "success": True,
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100,  # Convert from cents
                "currency": refund.currency,
                "created": refund.created,
                "reason": refund.reason,
            }

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            logger.error(f"Stripe error retrieving refund status: {e}")
            return self.stripe_service.handle_stripe_error(e)  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Unexpected error retrieving refund status: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while retrieving refund status",
            }

    @stripe_rate_limit("read_operations", "refund_service")
    def list_transaction_refunds(self, transaction_id: int) -> dict[str, Any]:
        """
        List all refunds for a specific transaction.

        Args:
            transaction_id: ID of the transaction to get refunds for

        Returns:
            Dict containing list of refunds or error details
        """
        logger.info(f"Listing refunds for transaction {transaction_id}")

        try:
            # Get the transaction
            try:
                purchase_transaction = PurchaseTransaction.objects.get(id=transaction_id)
            except PurchaseTransaction.DoesNotExist:
                return {"success": False, "error_type": "transaction_not_found", "message": "Transaction not found"}

            if not purchase_transaction.stripe_payment_intent_id:
                return {
                    "success": False,
                    "error_type": "no_payment_intent",
                    "message": "Transaction has no associated payment intent",
                }

            # Get refunds from Stripe
            refunds = stripe.Refund.list(payment_intent=purchase_transaction.stripe_payment_intent_id)

            refund_data = []
            for refund in refunds.data:
                refund_data.append(
                    {
                        "refund_id": refund.id,
                        "amount": refund.amount / 100,  # Convert from cents
                        "currency": refund.currency,
                        "status": refund.status,
                        "reason": refund.reason,
                        "created": refund.created,
                    }
                )

            return {
                "success": True,
                "transaction_id": transaction_id,
                "refunds": refund_data,
                "total_refunds": len(refund_data),
            }

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            logger.error(f"Stripe error listing refunds: {e}")
            return self.stripe_service.handle_stripe_error(e)  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Unexpected error listing refunds: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while listing refunds",
            }

    def _validate_refund_eligibility(
        self, purchase_transaction: PurchaseTransaction, refund_amount: Decimal | None
    ) -> dict[str, Any]:
        """
        Validate if a transaction is eligible for refund.

        Args:
            purchase_transaction: The transaction to validate
            refund_amount: Amount to refund (if None, validates full refund)

        Returns:
            Dict with validation result
        """
        # Check if transaction is completed
        if purchase_transaction.payment_status != TransactionPaymentStatus.COMPLETED:
            return {
                "success": False,
                "error_type": "invalid_transaction_state",
                "message": f"Transaction status is {purchase_transaction.payment_status}, only completed transactions can be refunded",
            }

        # Check if transaction has Stripe payment intent
        if not purchase_transaction.stripe_payment_intent_id:
            return {
                "success": False,
                "error_type": "no_payment_intent",
                "message": "Transaction has no associated Stripe payment intent",
            }

        # Validate refund amount
        if refund_amount is not None:
            if refund_amount <= 0:
                return {
                    "success": False,
                    "error_type": "invalid_refund_amount",
                    "message": "Refund amount must be greater than zero",
                }

            if refund_amount > purchase_transaction.amount:
                return {
                    "success": False,
                    "error_type": "invalid_refund_amount",
                    "message": "Refund amount cannot exceed transaction amount",
                }

        return {"success": True}

    @stripe_rate_limit("write_operations", "refund_service")
    def _process_stripe_refund(
        self, purchase_transaction: PurchaseTransaction, refund_amount: Decimal, reason: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process the actual refund with Stripe.

        Args:
            purchase_transaction: Transaction to refund
            refund_amount: Amount to refund
            reason: Refund reason
            metadata: Additional metadata

        Returns:
            Dict containing Stripe refund result
        """
        try:
            refund_data = {
                "payment_intent": purchase_transaction.stripe_payment_intent_id,
                "amount": int(refund_amount * 100),  # Convert to cents
                "reason": "requested_by_customer",
                "metadata": {
                    "transaction_id": str(purchase_transaction.id),
                    "student_id": str(purchase_transaction.student.id),  # type: ignore[attr-defined]
                    "refund_reason": reason,
                    **metadata,
                },
            }

            refund = stripe.Refund.create(**refund_data)

            logger.info(
                f"Stripe refund created: {refund.id} for payment intent {purchase_transaction.stripe_payment_intent_id}"
            )

            return {"success": True, "refund": refund, "message": "Stripe refund created successfully"}

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            logger.error(f"Stripe refund creation failed: {e}")
            return self.stripe_service.handle_stripe_error(e)  # type: ignore[no-any-return]

    def _update_transaction_for_refund(
        self, purchase_transaction: PurchaseTransaction, refund_amount: Decimal, stripe_refund: Any
    ) -> None:
        """
        Update transaction record for the refund.

        Args:
            purchase_transaction: Transaction being refunded
            refund_amount: Amount being refunded
            stripe_refund: Stripe refund object
        """
        # Update transaction status if it's a full refund
        if refund_amount >= purchase_transaction.amount:
            purchase_transaction.payment_status = TransactionPaymentStatus.REFUNDED

        # Add refund information to metadata
        refund_metadata = {
            "refund_processed_at": timezone.now().isoformat(),
            "refund_amount": str(refund_amount),
            "stripe_refund_id": stripe_refund.id,
            "refund_status": stripe_refund.status,
        }

        # Initialize refunds list if it doesn't exist
        if "refunds" not in purchase_transaction.metadata:
            purchase_transaction.metadata["refunds"] = []

        purchase_transaction.metadata["refunds"].append(refund_metadata)

        purchase_transaction.save(update_fields=["payment_status", "metadata", "updated_at"])

        logger.info(f"Transaction {purchase_transaction.id} updated for refund of €{refund_amount}")

    def _adjust_student_balance_for_refund(
        self, purchase_transaction: PurchaseTransaction, refund_amount: Decimal
    ) -> None:
        """
        Adjust student account balance for the refund.

        Args:
            purchase_transaction: Transaction being refunded
            refund_amount: Amount being refunded
        """
        try:
            student_balance = StudentAccountBalance.objects.get(student=purchase_transaction.student)  # type: ignore[misc]

            # Reduce balance by refund amount
            student_balance.balance_amount -= refund_amount

            # For package transactions, also reduce purchased hours proportionally
            if hasattr(purchase_transaction.metadata, "hours") and purchase_transaction.metadata.get("hours"):
                try:
                    package_hours = Decimal(str(purchase_transaction.metadata["hours"]))
                    refund_ratio = refund_amount / purchase_transaction.amount
                    hours_to_deduct = package_hours * refund_ratio

                    student_balance.hours_purchased -= hours_to_deduct

                    logger.info(
                        f"Deducted {hours_to_deduct} hours from student {purchase_transaction.student.id} balance"  # type: ignore[attr-defined]
                    )
                except (ValueError, TypeError, KeyError):
                    logger.warning(
                        f"Could not calculate hours deduction for refund on transaction {purchase_transaction.id}"
                    )

            student_balance.save(update_fields=["balance_amount", "hours_purchased", "updated_at"])

            logger.info(
                f"Student balance adjusted for refund: €{refund_amount} deducted from student {purchase_transaction.student.id}"  # type: ignore[attr-defined]
            )

        except StudentAccountBalance.DoesNotExist:
            logger.warning(
                f"No student balance found for student {purchase_transaction.student.id} during refund processing"  # type: ignore[attr-defined]
            )

    def _log_admin_action(
        self,
        admin_user,
        action_type: AdminActionType,
        target_transaction: PurchaseTransaction | None = None,
        success: bool = True,
        amount_impacted: Decimal | None = None,
        result_message: str = "",
        stripe_reference_id: str = "",
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> None:
        """
        Log administrative action for audit trail.

        Args:
            admin_user: Administrator performing the action
            action_type: Type of action being performed
            target_transaction: Transaction being affected
            success: Whether the action was successful
            amount_impacted: Financial amount affected
            result_message: Result or error message
            stripe_reference_id: Related Stripe object ID
            ip_address: IP address of the admin user
            user_agent: User agent string
        """
        try:
            AdminAction.objects.create(  # type: ignore[misc]
                action_type=action_type,
                action_description=f"Refund processing for transaction {target_transaction.id if target_transaction else 'unknown'}",
                admin_user=admin_user,
                target_user=target_transaction.student if target_transaction else None,
                target_transaction=target_transaction,
                success=success,
                result_message=result_message,
                amount_impacted=amount_impacted,
                stripe_reference_id=stripe_reference_id,
                ip_address=ip_address,
                user_agent=user_agent,
                action_data={
                    "refund_amount": str(amount_impacted) if amount_impacted else None,
                    "transaction_amount": str(target_transaction.amount) if target_transaction else None,
                    "student_email": target_transaction.student.email if target_transaction else None,  # type: ignore[attr-defined]
                },
            )

            logger.info(f"Admin action logged: {action_type} by {admin_user.email}")

        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
