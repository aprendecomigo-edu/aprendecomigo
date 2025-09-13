"""
Payment Service for managing Stripe payment intents and student purchases.

This service handles the core payment processing logic for the Aprende Comigo platform,
including payment intent creation, completion confirmation, failure handling, and
transaction consistency management.
"""

from datetime import timedelta
from decimal import Decimal
import logging
from typing import Any

# Cross-app models will be loaded at runtime using apps.get_model()
from django.db import transaction
from django.utils import timezone
import stripe

from finances.models import (
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)

from .stripe_base import StripeService

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service class for managing payment intents and student purchases.

    This service provides centralized payment processing functionality with
    comprehensive error handling, atomic transactions, and audit logging.
    """

    def __init__(self):
        """
        Initialize PaymentService with Stripe integration.

        Raises:
            ValueError: If Stripe configuration is invalid
        """
        try:
            self.stripe_service = StripeService()
            logger.info("PaymentService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize StripeService: {e}")
            # Ensure stripe_service attribute exists even if initialization fails
            self.stripe_service = None
            raise ValueError(f"PaymentService initialization failed: {e}") from e

    def create_payment_intent(
        self,
        user,  # CustomUser instance
        pricing_plan_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a Stripe payment intent for a student purchase.

        Args:
            user: The student making the purchase
            pricing_plan_id: ID of the pricing plan being purchased
            metadata: Additional purchase metadata including amount and package details

        Returns:
            Dict containing client_secret and transaction_id on success, or error details
        """
        if metadata is None:
            metadata = {}

        logger.info(f"Creating payment intent for user {user.id} with plan {pricing_plan_id}")

        try:
            # Validate required metadata
            validation_result = self._validate_payment_metadata(metadata)
            if not validation_result["success"]:
                return validation_result

            # Check for duplicate payment intent prevention
            duplicate_check = self._check_for_duplicate_request(user, pricing_plan_id, metadata)
            if not duplicate_check["success"]:
                return duplicate_check

            amount = Decimal(str(metadata["amount"]))
            amount_cents = int(amount * 100)  # Convert to cents for Stripe

            # Determine transaction type based on metadata or pricing plan
            transaction_type = self._determine_transaction_type(metadata, pricing_plan_id)

            # Create payment intent with Stripe
            stripe_metadata = {
                "user_id": str(user.id),
                "pricing_plan_id": pricing_plan_id,
                "transaction_type": transaction_type,
            }

            # Add custom metadata
            for key, value in metadata.items():
                if key not in ["amount"]:  # Don't duplicate amount
                    stripe_metadata[f"custom_{key}"] = str(value)

            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="eur",
                automatic_payment_methods={
                    "enabled": True,
                },
                metadata=stripe_metadata,
            )

            # Create transaction record with atomic database operation
            with transaction.atomic():
                purchase_transaction = self._create_purchase_transaction(
                    user=user,
                    payment_intent=payment_intent,
                    transaction_type=transaction_type,
                    amount=amount,
                    metadata=metadata,
                )

            logger.info(
                f"Payment intent {payment_intent.id} created successfully for transaction {purchase_transaction.id}"
            )

            return {
                "success": True,
                "client_secret": payment_intent.client_secret,
                "transaction_id": purchase_transaction.id,
                "payment_intent_id": payment_intent.id,
            }

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            logger.error(f"Stripe error creating payment intent: {e}")
            if hasattr(self, "stripe_service") and self.stripe_service is not None:
                return self.stripe_service.handle_stripe_error(e)  # type: ignore[no-any-return]
            else:
                logger.error("StripeService not available for error handling")
                return {
                    "success": False,
                    "error_type": "stripe_error",
                    "message": "Payment processing failed - service unavailable",
                }
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while creating payment intent",
            }

    def confirm_payment_completion(self, payment_intent_id: str) -> dict[str, Any]:
        """
        Confirm payment completion and credit hours to student account.

        Args:
            payment_intent_id: Stripe PaymentIntent ID to confirm

        Returns:
            Dict containing success status and transaction details
        """
        logger.info(f"Confirming payment completion for payment intent {payment_intent_id}")

        try:
            # Retrieve payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status != "succeeded":
                logger.warning(f"Payment intent {payment_intent_id} status is {payment_intent.status}, not succeeded")
                return {
                    "success": False,
                    "error_type": "payment_not_completed",
                    "message": f"Payment status is {payment_intent.status}, expected succeeded",
                }

            # Find corresponding transaction in database
            try:
                purchase_transaction = PurchaseTransaction.objects.select_for_update().get(
                    stripe_payment_intent_id=payment_intent_id
                )
            except PurchaseTransaction.DoesNotExist:
                logger.error(f"Transaction not found for payment intent {payment_intent_id}")
                return {
                    "success": False,
                    "error_type": "transaction_not_found",
                    "message": "Transaction record not found in database",
                }

            # Check if transaction is already completed (idempotency)
            if purchase_transaction.payment_status == TransactionPaymentStatus.COMPLETED:
                logger.info(
                    f"Transaction {purchase_transaction.id} is already completed - returning success (idempotent)"
                )
                return {
                    "success": True,
                    "transaction_id": purchase_transaction.id,
                    "payment_intent_id": payment_intent_id,
                    "message": "Transaction already completed",
                }

            # Use atomic transaction for consistency
            with transaction.atomic():
                # Update transaction status
                purchase_transaction.payment_status = TransactionPaymentStatus.COMPLETED
                purchase_transaction.save(update_fields=["payment_status", "updated_at"])

                # Credit hours to student account if it's a package transaction
                if purchase_transaction.transaction_type == TransactionType.PACKAGE:
                    self._credit_hours_to_account(purchase_transaction)

                # Update account balance with payment amount
                self._update_account_balance(purchase_transaction)

            logger.info(f"Payment completion confirmed for transaction {purchase_transaction.id}")

            return {"success": True, "transaction_id": purchase_transaction.id, "payment_intent_id": payment_intent_id}

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            logger.error(f"Stripe error confirming payment: {e}")
            if hasattr(self, "stripe_service") and self.stripe_service is not None:
                return self.stripe_service.handle_stripe_error(e)  # type: ignore[no-any-return]
            else:
                logger.error("StripeService not available for error handling")
                return {
                    "success": False,
                    "error_type": "stripe_error",
                    "message": "Payment confirmation failed - service unavailable",
                }
        except Exception as e:
            logger.error(f"Unexpected error confirming payment completion: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while confirming payment",
            }

    def handle_payment_failure(self, payment_intent_id: str, error_message: str) -> dict[str, Any]:
        """
        Handle payment failure and update transaction status.

        Args:
            payment_intent_id: Stripe PaymentIntent ID that failed
            error_message: Error message describing the failure

        Returns:
            Dict containing success status and transaction details
        """
        logger.info(f"Handling payment failure for payment intent {payment_intent_id}")

        try:
            # Find corresponding transaction in database
            try:
                purchase_transaction = PurchaseTransaction.objects.select_for_update().get(
                    stripe_payment_intent_id=payment_intent_id
                )
            except PurchaseTransaction.DoesNotExist:
                logger.error(f"Transaction not found for failed payment intent {payment_intent_id}")
                return {
                    "success": False,
                    "error_type": "transaction_not_found",
                    "message": "Transaction record not found in database",
                }

            # Check if transaction is in a valid state for failure
            if purchase_transaction.payment_status == TransactionPaymentStatus.COMPLETED:
                logger.warning(f"Cannot mark completed transaction {purchase_transaction.id} as failed")
                return {
                    "success": False,
                    "error_type": "invalid_transaction_state",
                    "message": "Cannot mark already completed transaction as failed",
                }

            # Use atomic transaction for consistency
            with transaction.atomic():
                # Update transaction status and add failure details
                purchase_transaction.payment_status = TransactionPaymentStatus.FAILED

                # Add failure information to metadata
                failure_metadata = {"error_message": error_message, "failed_at": timezone.now().isoformat()}
                purchase_transaction.metadata.update(failure_metadata)

                purchase_transaction.save(update_fields=["payment_status", "metadata", "updated_at"])

            logger.info(f"Payment failure handled for transaction {purchase_transaction.id}")

            return {"success": True, "transaction_id": purchase_transaction.id, "payment_intent_id": payment_intent_id}

        except Exception as e:
            logger.error(f"Unexpected error handling payment failure: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while handling payment failure",
            }

    def get_payment_status(self, payment_intent_id: str) -> dict[str, Any]:
        """
        Get payment status from Stripe.

        Args:
            payment_intent_id: Stripe PaymentIntent ID to check

        Returns:
            Dict containing payment status and details
        """
        logger.info(f"Retrieving payment status for payment intent {payment_intent_id}")

        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "success": True,
                "payment_intent_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "created": payment_intent.created,
            }

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            logger.error(f"Stripe error retrieving payment status: {e}")
            if hasattr(self, "stripe_service") and self.stripe_service is not None:
                return self.stripe_service.handle_stripe_error(e)  # type: ignore[no-any-return]
            else:
                logger.error("StripeService not available for error handling")
                return {
                    "success": False,
                    "error_type": "stripe_error",
                    "message": "Payment status retrieval failed - service unavailable",
                }
        except Exception as e:
            logger.error(f"Unexpected error retrieving payment status: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while retrieving payment status",
            }

    def _find_best_source_transaction(self, user) -> PurchaseTransaction | None:  # user: CustomUser
        """
        Find the best source transaction for hour deduction using FIFO logic.

        Args:
            user: The student user

        Returns:
            The best source transaction or None if no suitable transaction found
        """
        # Get all completed package transactions for the user, ordered by creation date (FIFO)
        suitable_transactions = (
            PurchaseTransaction.objects.filter(
                student=user,
                transaction_type=TransactionType.PACKAGE,
                payment_status=TransactionPaymentStatus.COMPLETED,
            )
            .exclude(
                # Exclude expired transactions
                expires_at__lt=timezone.now()
            )
            .order_by("created_at")
        )  # FIFO: oldest first

        # Return the first (oldest) suitable transaction, or None if none exist
        return suitable_transactions.first()

    def _validate_payment_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Validate payment metadata for required fields and valid values.

        Args:
            metadata: Payment metadata to validate

        Returns:
            Dict with validation result
        """
        if "amount" not in metadata:
            return {"success": False, "error_type": "validation_error", "message": "Amount is required in metadata"}

        try:
            amount = Decimal(str(metadata["amount"]))
            if amount <= 0:
                return {
                    "success": False,
                    "error_type": "validation_error",
                    "message": "Amount must be greater than zero",
                }

            # Validate minimum amount (€0.50 as per Stripe requirements)
            if amount < Decimal("0.50"):
                return {
                    "success": False,
                    "error_type": "validation_error",
                    "message": "Amount must be at least €0.50 (minimum payment amount)",
                }

            # Validate maximum amount (€10,000 reasonable limit)
            if amount > Decimal("10000.00"):
                return {
                    "success": False,
                    "error_type": "validation_error",
                    "message": "Amount cannot exceed €10,000 (maximum payment amount)",
                }

        except (ValueError, TypeError):
            return {"success": False, "error_type": "validation_error", "message": "Invalid amount format"}

        return {"success": True}

    def _check_for_duplicate_request(self, user, pricing_plan_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Check for duplicate payment requests to prevent multiple payment intents.

        Args:
            user: The user making the request
            pricing_plan_id: The pricing plan ID
            metadata: Request metadata

        Returns:
            Dict with validation result
        """
        # Look for existing pending transactions for the same user and plan
        existing_transaction = (
            PurchaseTransaction.objects.filter(
                student=user, payment_status=TransactionPaymentStatus.PROCESSING, metadata__has_key="pricing_plan_id"
            )
            .filter(metadata__pricing_plan_id=pricing_plan_id)
            .first()
        )

        if existing_transaction:
            # Check if the transaction was created recently (within 10 minutes)
            recent_threshold = timezone.now() - timedelta(minutes=10)
            if existing_transaction.created_at > recent_threshold:
                return {
                    "success": False,
                    "error_type": "duplicate_request",
                    "message": "A payment request for this plan is already in progress",
                }

        return {"success": True}

    def _determine_transaction_type(self, metadata: dict[str, Any], pricing_plan_id: str) -> str:
        """
        Determine transaction type based on metadata and pricing plan.

        Args:
            metadata: Payment metadata
            pricing_plan_id: Pricing plan identifier

        Returns:
            Transaction type string
        """
        # Check metadata for explicit type
        if "subscription_name" in metadata or "billing_cycle" in metadata:
            return TransactionType.SUBSCRIPTION

        # Check pricing plan ID for subscription indicators
        if "subscription" in pricing_plan_id.lower() or "monthly" in pricing_plan_id.lower():
            return TransactionType.SUBSCRIPTION

        # Default to package
        return TransactionType.PACKAGE

    def _create_purchase_transaction(
        self,
        user,  # CustomUser instance
        payment_intent: Any,
        transaction_type: str,
        amount: Decimal,
        metadata: dict[str, Any],
    ) -> PurchaseTransaction:
        """
        Create a purchase transaction record in the database.

        Args:
            user: The student user
            payment_intent: Stripe PaymentIntent object
            transaction_type: Type of transaction
            amount: Transaction amount
            metadata: Additional metadata

        Returns:
            Created PurchaseTransaction instance
        """
        # Set expiration for package transactions (e.g., 1 year from now)
        expires_at = None
        if transaction_type == TransactionType.PACKAGE:
            expires_at = timezone.now() + timedelta(days=365)

        return PurchaseTransaction.objects.create(
            student=user,
            transaction_type=transaction_type,
            amount=amount,
            payment_status=TransactionPaymentStatus.PROCESSING,
            stripe_payment_intent_id=payment_intent.id,
            stripe_customer_id=payment_intent.customer if hasattr(payment_intent, "customer") else None,
            expires_at=expires_at,
            metadata=metadata,
        )

    def _credit_hours_to_account(self, purchase_transaction: PurchaseTransaction) -> None:
        """
        Credit hours to student account from completed package transaction.

        Args:
            purchase_transaction: Completed transaction containing hour information
        """
        # Get or create student account balance
        student_balance, _created = StudentAccountBalance.objects.get_or_create(
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

            logger.info(f"Added {hours_to_add} hours to account for student {purchase_transaction.student.id}")  # type: ignore[attr-defined]

    def _update_account_balance(self, purchase_transaction: PurchaseTransaction) -> None:
        """
        Update student account balance with payment amount.

        Args:
            purchase_transaction: Completed transaction
        """
        # Get or create student account balance
        student_balance, _created = StudentAccountBalance.objects.get_or_create(
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

        logger.info(f"Added €{purchase_transaction.amount} to balance for student {purchase_transaction.student.id}")  # type: ignore[attr-defined]
