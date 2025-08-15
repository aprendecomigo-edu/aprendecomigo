"""
Dispute Service for managing payment disputes through Stripe API.

This service handles dispute management including evidence submission, response tracking,
and local dispute record maintenance with comprehensive audit logging.
"""

from datetime import UTC
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
    DisputeReason,
    DisputeStatus,
    PaymentDispute,
    PurchaseTransaction,
)

from .stripe_base import StripeService

logger = logging.getLogger(__name__)


class DisputeService:
    """
    Service class for managing payment disputes with Stripe integration.

    This service provides comprehensive dispute management functionality including
    evidence submission, response tracking, and local dispute record maintenance.
    """

    def __init__(self):
        """
        Initialize DisputeService with Stripe integration.

        Raises:
            ValueError: If Stripe configuration is invalid
        """
        self.stripe_service = StripeService()
        logger.info("DisputeService initialized successfully")

    def sync_dispute_from_stripe(self, stripe_dispute_id: str, admin_user=None) -> dict[str, Any]:
        """
        Sync a dispute from Stripe and create/update local record.

        Args:
            stripe_dispute_id: Stripe dispute ID to sync
            admin_user: Administrator performing the sync

        Returns:
            Dict containing success status and dispute details
        """
        logger.info(f"Syncing dispute {stripe_dispute_id} from Stripe")

        try:
            # Retrieve dispute from Stripe
            stripe_dispute = stripe.Dispute.retrieve(stripe_dispute_id)

            # Find related transaction
            payment_intent_id = stripe_dispute.payment_intent
            try:
                purchase_transaction = PurchaseTransaction.objects.get(stripe_payment_intent_id=payment_intent_id)
            except PurchaseTransaction.DoesNotExist:
                logger.error(f"No transaction found for payment intent {payment_intent_id}")
                return {
                    "success": False,
                    "error_type": "transaction_not_found",
                    "message": f"No local transaction found for payment intent {payment_intent_id}",
                }

            # Create or update local dispute record
            with transaction.atomic():
                dispute, created = PaymentDispute.objects.update_or_create(
                    stripe_dispute_id=stripe_dispute_id,
                    defaults=self._extract_dispute_data(stripe_dispute, purchase_transaction),
                )

                # Log admin action
                if admin_user:
                    self._log_admin_action(
                        admin_user=admin_user,
                        action_type=AdminActionType.DISPUTE_RESPONSE,
                        target_dispute=dispute,
                        success=True,
                        result_message=f"Dispute {'created' if created else 'updated'} from Stripe sync",
                        stripe_reference_id=stripe_dispute_id,
                    )

                logger.info(f"Dispute {stripe_dispute_id} {'created' if created else 'updated'} locally")

                return {
                    "success": True,
                    "dispute_id": dispute.id,
                    "stripe_dispute_id": stripe_dispute_id,
                    "created": created,
                    "message": f"Dispute {'created' if created else 'updated'} successfully",
                }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error syncing dispute: {e}")
            error_result = self.stripe_service.handle_stripe_error(e)

            # Log failed admin action
            if admin_user:
                self._log_admin_action(
                    admin_user=admin_user,
                    action_type=AdminActionType.DISPUTE_RESPONSE,
                    success=False,
                    result_message=f"Failed to sync dispute: {error_result.get('message', str(e))}",
                    stripe_reference_id=stripe_dispute_id,
                )

            return error_result
        except Exception as e:
            logger.error(f"Unexpected error syncing dispute: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while syncing dispute",
            }

    def submit_dispute_evidence(
        self, dispute_id: int, evidence_data: dict[str, Any], admin_user=None
    ) -> dict[str, Any]:
        """
        Submit evidence for a dispute to Stripe.

        Args:
            dispute_id: Local dispute ID
            evidence_data: Evidence data to submit
            admin_user: Administrator submitting evidence

        Returns:
            Dict containing success status and submission details
        """
        logger.info(f"Submitting evidence for dispute {dispute_id}")

        try:
            # Get local dispute record
            try:
                dispute = PaymentDispute.objects.select_for_update().get(id=dispute_id)
            except PaymentDispute.DoesNotExist:
                return {"success": False, "error_type": "dispute_not_found", "message": "Dispute not found"}

            # Validate dispute state
            if dispute.is_responded:
                return {
                    "success": False,
                    "error_type": "already_responded",
                    "message": "Evidence has already been submitted for this dispute",
                }

            # Submit evidence to Stripe
            with transaction.atomic():
                stripe_result = self._submit_stripe_evidence(dispute.stripe_dispute_id, evidence_data)

                if not stripe_result["success"]:
                    # Log failed admin action
                    if admin_user:
                        self._log_admin_action(
                            admin_user=admin_user,
                            action_type=AdminActionType.DISPUTE_RESPONSE,
                            target_dispute=dispute,
                            success=False,
                            result_message=stripe_result.get("message", "Evidence submission failed"),
                            stripe_reference_id=dispute.stripe_dispute_id,
                        )
                    return stripe_result

                # Update local dispute record
                dispute.evidence_details = evidence_data
                dispute.mark_responded()

                # Log successful admin action
                if admin_user:
                    self._log_admin_action(
                        admin_user=admin_user,
                        action_type=AdminActionType.DISPUTE_RESPONSE,
                        target_dispute=dispute,
                        success=True,
                        result_message="Evidence submitted successfully",
                        stripe_reference_id=dispute.stripe_dispute_id,
                    )

                logger.info(f"Evidence submitted successfully for dispute {dispute_id}")

                return {
                    "success": True,
                    "dispute_id": dispute_id,
                    "stripe_dispute_id": dispute.stripe_dispute_id,
                    "message": "Evidence submitted successfully",
                }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error submitting evidence: {e}")
            error_result = self.stripe_service.handle_stripe_error(e)

            # Log failed admin action
            if admin_user:
                self._log_admin_action(
                    admin_user=admin_user,
                    action_type=AdminActionType.DISPUTE_RESPONSE,
                    target_dispute=dispute if "dispute" in locals() else None,
                    success=False,
                    result_message=f"Stripe error: {error_result.get('message', str(e))}",
                    stripe_reference_id=dispute.stripe_dispute_id if "dispute" in locals() else None,
                )

            return error_result
        except Exception as e:
            logger.error(f"Unexpected error submitting evidence: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while submitting evidence",
            }

    def get_dispute_details(self, stripe_dispute_id: str) -> dict[str, Any]:
        """
        Get detailed dispute information from Stripe.

        Args:
            stripe_dispute_id: Stripe dispute ID to retrieve

        Returns:
            Dict containing dispute details
        """
        logger.info(f"Retrieving dispute details for {stripe_dispute_id}")

        try:
            dispute = stripe.Dispute.retrieve(stripe_dispute_id)

            dispute_data = {
                "dispute_id": dispute.id,
                "amount": dispute.amount / 100,  # Convert from cents
                "currency": dispute.currency,
                "reason": dispute.reason,
                "status": dispute.status,
                "created": dispute.created,
                "evidence_due_by": dispute.evidence_details.due_by if dispute.evidence_details else None,
                "evidence_submission_count": dispute.evidence_details.submission_count
                if dispute.evidence_details
                else 0,
                "is_charge_refundable": dispute.is_charge_refundable,
                "payment_intent": dispute.payment_intent,
                "evidence_details": dispute.evidence_details.to_dict_recursive() if dispute.evidence_details else {},
                "metadata": dispute.metadata,
            }

            return {"success": True, "dispute": dispute_data, "message": "Dispute details retrieved successfully"}

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving dispute details: {e}")
            return self.stripe_service.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error retrieving dispute details: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while retrieving dispute details",
            }

    def list_disputes(
        self, status: str | None = None, limit: int = 50, created_after: int | None = None
    ) -> dict[str, Any]:
        """
        List disputes from Stripe with optional filtering.

        Args:
            status: Filter by dispute status
            limit: Maximum number of disputes to return
            created_after: Filter disputes created after this timestamp

        Returns:
            Dict containing list of disputes
        """
        logger.info(f"Listing disputes with status={status}, limit={limit}")

        try:
            list_params = {"limit": limit}

            if status:
                list_params["status"] = status

            if created_after:
                list_params["created"] = {"gte": created_after}

            disputes = stripe.Dispute.list(**list_params)

            dispute_list = []
            for dispute in disputes.data:
                dispute_list.append(
                    {
                        "dispute_id": dispute.id,
                        "amount": dispute.amount / 100,
                        "currency": dispute.currency,
                        "reason": dispute.reason,
                        "status": dispute.status,
                        "created": dispute.created,
                        "payment_intent": dispute.payment_intent,
                        "evidence_due_by": dispute.evidence_details.due_by if dispute.evidence_details else None,
                    }
                )

            return {
                "success": True,
                "disputes": dispute_list,
                "count": len(dispute_list),
                "has_more": disputes.has_more,
                "message": "Disputes retrieved successfully",
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error listing disputes: {e}")
            return self.stripe_service.handle_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error listing disputes: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while listing disputes",
            }

    def update_dispute_notes(self, dispute_id: int, internal_notes: str, admin_user=None) -> dict[str, Any]:
        """
        Update internal notes for a dispute.

        Args:
            dispute_id: Local dispute ID
            internal_notes: Internal notes to update
            admin_user: Administrator updating notes

        Returns:
            Dict containing success status
        """
        logger.info(f"Updating notes for dispute {dispute_id}")

        try:
            # Get local dispute record
            try:
                dispute = PaymentDispute.objects.get(id=dispute_id)
            except PaymentDispute.DoesNotExist:
                return {"success": False, "error_type": "dispute_not_found", "message": "Dispute not found"}

            # Update notes
            dispute.internal_notes = internal_notes
            dispute.save(update_fields=["internal_notes", "updated_at"])

            # Log admin action
            if admin_user:
                self._log_admin_action(
                    admin_user=admin_user,
                    action_type=AdminActionType.DISPUTE_RESPONSE,
                    target_dispute=dispute,
                    success=True,
                    result_message="Dispute notes updated",
                    stripe_reference_id=dispute.stripe_dispute_id,
                )

            logger.info(f"Notes updated for dispute {dispute_id}")

            return {"success": True, "dispute_id": dispute_id, "message": "Dispute notes updated successfully"}

        except Exception as e:
            logger.error(f"Error updating dispute notes: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while updating dispute notes",
            }

    def get_overdue_disputes(self) -> dict[str, Any]:
        """
        Get disputes with overdue evidence submission.

        Returns:
            Dict containing list of overdue disputes
        """
        logger.info("Retrieving overdue disputes")

        try:
            overdue_disputes = PaymentDispute.objects.filter(
                evidence_due_by__lt=timezone.now(),
                is_responded=False,
                status__in=[DisputeStatus.NEEDS_RESPONSE, DisputeStatus.WARNING_NEEDS_RESPONSE],
            ).select_related("purchase_transaction__student")

            dispute_list = []
            for dispute in overdue_disputes:
                dispute_list.append(
                    {
                        "dispute_id": dispute.id,
                        "stripe_dispute_id": dispute.stripe_dispute_id,
                        "amount": dispute.amount,
                        "reason": dispute.reason,
                        "status": dispute.status,
                        "evidence_due_by": dispute.evidence_due_by,
                        "days_overdue": dispute.days_until_evidence_due * -1,  # Negative for overdue
                        "student_email": dispute.purchase_transaction.student.email,
                        "transaction_id": dispute.purchase_transaction.id,
                    }
                )

            return {
                "success": True,
                "overdue_disputes": dispute_list,
                "count": len(dispute_list),
                "message": "Overdue disputes retrieved successfully",
            }

        except Exception as e:
            logger.error(f"Error retrieving overdue disputes: {e}")
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "An unexpected error occurred while retrieving overdue disputes",
            }

    def _extract_dispute_data(self, stripe_dispute: Any, purchase_transaction: PurchaseTransaction) -> dict[str, Any]:
        """
        Extract dispute data from Stripe dispute object.

        Args:
            stripe_dispute: Stripe dispute object
            purchase_transaction: Related purchase transaction

        Returns:
            Dict containing dispute data for local record
        """
        # Map Stripe reason to local enum
        reason_mapping = {
            "duplicate": DisputeReason.DUPLICATE,
            "fraudulent": DisputeReason.FRAUDULENT,
            "subscription_canceled": DisputeReason.SUBSCRIPTION_CANCELED,
            "product_unacceptable": DisputeReason.PRODUCT_UNACCEPTABLE,
            "product_not_received": DisputeReason.PRODUCT_NOT_RECEIVED,
            "unrecognized": DisputeReason.UNRECOGNIZED,
            "credit_not_processed": DisputeReason.CREDIT_NOT_PROCESSED,
            "general": DisputeReason.GENERAL,
        }

        # Map Stripe status to local enum
        status_mapping = {
            "warning_needs_response": DisputeStatus.WARNING_NEEDS_RESPONSE,
            "warning_under_review": DisputeStatus.WARNING_UNDER_REVIEW,
            "warning_closed": DisputeStatus.WARNING_CLOSED,
            "needs_response": DisputeStatus.NEEDS_RESPONSE,
            "under_review": DisputeStatus.UNDER_REVIEW,
            "charge_refunded": DisputeStatus.CHARGE_REFUNDED,
            "won": DisputeStatus.WON,
            "lost": DisputeStatus.LOST,
        }

        return {
            "purchase_transaction": purchase_transaction,
            "amount": Decimal(str(stripe_dispute.amount / 100)),  # Convert from cents
            "currency": stripe_dispute.currency,
            "reason": reason_mapping.get(stripe_dispute.reason, DisputeReason.GENERAL),
            "status": status_mapping.get(stripe_dispute.status, DisputeStatus.NEEDS_RESPONSE),
            "evidence_due_by": timezone.datetime.fromtimestamp(stripe_dispute.evidence_details.due_by, tz=UTC)
            if stripe_dispute.evidence_details and stripe_dispute.evidence_details.due_by
            else None,
            "stripe_metadata": stripe_dispute.to_dict_recursive(),
        }

    def _submit_stripe_evidence(self, stripe_dispute_id: str, evidence_data: dict[str, Any]) -> dict[str, Any]:
        """
        Submit evidence to Stripe for a dispute.

        Args:
            stripe_dispute_id: Stripe dispute ID
            evidence_data: Evidence data to submit

        Returns:
            Dict containing submission result
        """
        try:
            # Update dispute evidence in Stripe
            dispute = stripe.Dispute.modify(stripe_dispute_id, evidence=evidence_data)

            logger.info(f"Evidence submitted to Stripe for dispute {stripe_dispute_id}")

            return {"success": True, "dispute": dispute, "message": "Evidence submitted to Stripe successfully"}

        except stripe.error.StripeError as e:
            logger.error(f"Stripe evidence submission failed: {e}")
            return self.stripe_service.handle_stripe_error(e)

    def _log_admin_action(
        self,
        admin_user,
        action_type: AdminActionType,
        target_dispute: PaymentDispute | None = None,
        success: bool = True,
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
            target_dispute: Dispute being affected
            success: Whether the action was successful
            result_message: Result or error message
            stripe_reference_id: Related Stripe object ID
            ip_address: IP address of the admin user
            user_agent: User agent string
        """
        try:
            AdminAction.objects.create(
                action_type=action_type,
                action_description=f"Dispute management for dispute {target_dispute.id if target_dispute else 'unknown'}",
                admin_user=admin_user,
                target_user=target_dispute.purchase_transaction.student if target_dispute else None,
                target_transaction=target_dispute.purchase_transaction if target_dispute else None,
                target_dispute=target_dispute,
                success=success,
                result_message=result_message,
                stripe_reference_id=stripe_reference_id,
                ip_address=ip_address,
                user_agent=user_agent,
                action_data={
                    "dispute_amount": str(target_dispute.amount) if target_dispute else None,
                    "dispute_reason": target_dispute.reason if target_dispute else None,
                    "dispute_status": target_dispute.status if target_dispute else None,
                    "student_email": target_dispute.purchase_transaction.student.email if target_dispute else None,
                },
            )

            logger.info(f"Admin action logged: {action_type} by {admin_user.email}")

        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
