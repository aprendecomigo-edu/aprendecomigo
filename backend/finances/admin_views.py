"""
Admin API views for comprehensive payment system management.

These views provide administrative interfaces for:
- Package expiration management
- Payment refund processing
- Dispute management and evidence submission
- Fraud detection and alert management
- Payment retry functionality
- Comprehensive audit logging

Following GitHub Issues #33 and #116
"""

from datetime import timedelta
from decimal import Decimal
import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from finances.models import AdminActionType, PurchaseTransaction
from finances.serializers import PurchaseHistorySerializer
from finances.services.package_expiration_service import PackageExpirationService

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_expired_packages(request):
    """
    Get all expired packages.

    Query Parameters:
    - grace_hours: Grace period in hours (default: 24)
    - student_email: Filter by specific student email
    """
    grace_hours = int(request.GET.get("grace_hours", 24))
    student_email = request.GET.get("student_email")

    try:
        if student_email:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                student = User.objects.get(email=student_email)
                expired_packages = PackageExpirationService.get_expired_packages_for_student(student)

                # Apply grace period filter
                grace_cutoff = timezone.now() - timedelta(hours=grace_hours)
                expired_packages = [pkg for pkg in expired_packages if pkg.expires_at < grace_cutoff]
            except User.DoesNotExist:
                return Response(
                    {"error": f"Student with email {student_email} not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            expired_packages = PackageExpirationService.get_expired_packages_outside_grace_period(
                grace_hours=grace_hours
            )

        serializer = PurchaseHistorySerializer(expired_packages, many=True)

        return Response(
            {"expired_packages": serializer.data, "count": len(expired_packages), "grace_hours": grace_hours}
        )

    except Exception as e:
        logger.error(f"Error retrieving expired packages: {e}")
        return Response({"error": "Failed to retrieve expired packages"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def process_expired_packages(request):
    """
    Process all expired packages.

    Body Parameters:
    - grace_hours: Grace period in hours (default: 24)
    - dry_run: If true, return what would be processed without making changes
    """
    grace_hours = int(request.data.get("grace_hours", 24))
    dry_run = request.data.get("dry_run", False)

    try:
        if dry_run:
            expired_packages = PackageExpirationService.get_expired_packages_outside_grace_period(
                grace_hours=grace_hours
            )

            total_hours = Decimal("0.00")
            for package in expired_packages:
                hours_to_expire = PackageExpirationService.calculate_hours_to_expire(package)
                total_hours += hours_to_expire

            return Response(
                {
                    "dry_run": True,
                    "packages_to_process": len(expired_packages),
                    "total_hours_to_expire": total_hours,
                    "grace_hours": grace_hours,
                }
            )
        else:
            results = PackageExpirationService.process_bulk_expiration(grace_hours=grace_hours)

            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]

            total_hours_expired = sum(r.hours_expired for r in successful)

            return Response(
                {
                    "processed_count": len(successful),
                    "failed_count": len(failed),
                    "total_hours_expired": total_hours_expired,
                    "grace_hours": grace_hours,
                    "results": [
                        {
                            "package_id": r.package_id,
                            "student_id": r.student_id,
                            "hours_expired": r.hours_expired,
                            "success": r.success,
                            "error_message": r.error_message,
                        }
                        for r in results
                    ],
                }
            )

    except Exception as e:
        logger.error(f"Error processing expired packages: {e}")
        return Response({"error": "Failed to process expired packages"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def extend_package(request, package_id):
    """
    Extend a package expiration date.

    Body Parameters:
    - extension_days: Number of days to extend (required)
    - reason: Reason for extension (optional)
    - extend_from_now: Whether to extend from now or original expiry (default: false)
    """
    try:
        package = PurchaseTransaction.objects.get(id=package_id)

        extension_days = request.data.get("extension_days")
        if not extension_days:
            return Response({"error": "extension_days is required"}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get("reason", "")
        extend_from_now = request.data.get("extend_from_now", False)

        result = PackageExpirationService.extend_package_expiration(
            package=package, extension_days=int(extension_days), reason=reason, extend_from_now=extend_from_now
        )

        if result.success:
            return Response(
                {
                    "success": True,
                    "package_id": result.package_id,
                    "original_expiry": result.original_expiry,
                    "new_expiry": result.new_expiry,
                    "extension_days": result.extension_days,
                    "audit_log": result.audit_log,
                }
            )
        else:
            return Response({"error": result.error_message}, status=status.HTTP_400_BAD_REQUEST)

    except PurchaseTransaction.DoesNotExist:
        return Response({"error": "Package not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error extending package {package_id}: {e}")
        return Response({"error": "Failed to extend package"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_expiration_analytics(request):
    """
    Get expiration analytics and metrics.

    Query Parameters:
    - period_days: Analysis period in days (default: 30)
    """
    period_days = int(request.GET.get("period_days", 30))

    try:
        # Get current analytics
        metrics = PackageExpirationService.calculate_expiration_metrics(period_days=period_days)

        # Get summary report
        start_date = timezone.now() - timedelta(days=period_days)
        end_date = timezone.now()

        summary = PackageExpirationService.generate_expiration_summary_report(start_date=start_date, end_date=end_date)

        # Get at-risk students
        at_risk_students = PackageExpirationService.identify_at_risk_students(
            min_expired_packages=2, timeframe_days=period_days
        )

        return Response(
            {
                "period_days": period_days,
                "metrics": metrics,
                "summary": summary,
                "at_risk_students": at_risk_students,
                "generated_at": timezone.now(),
            }
        )

    except Exception as e:
        logger.error(f"Error generating expiration analytics: {e}")
        return Response({"error": "Failed to generate analytics"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def send_expiration_notifications(request):
    """
    Send expiration warning notifications to students.

    Body Parameters:
    - days_ahead: Send notifications for packages expiring within N days (default: 7)
    - student_email: Send notification to specific student only (optional)
    """
    days_ahead = int(request.data.get("days_ahead", 7))
    student_email = request.data.get("student_email")

    try:
        if student_email:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                student = User.objects.get(email=student_email)

                # Get expiring packages for specific student
                expiring_packages = [
                    pkg
                    for pkg in PackageExpirationService.get_packages_expiring_soon(days_ahead)
                    if pkg.student == student
                ]
            except User.DoesNotExist:
                return Response(
                    {"error": f"Student with email {student_email} not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            expiring_packages = PackageExpirationService.get_packages_expiring_soon(days_ahead=days_ahead)

        if not expiring_packages:
            return Response({"notifications_sent": 0, "message": "No packages expiring soon", "days_ahead": days_ahead})

        results = PackageExpirationService.send_batch_expiration_warnings(
            expiring_packages, days_until_expiry=days_ahead
        )

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        return Response(
            {
                "notifications_sent": len(successful),
                "failed_notifications": len(failed),
                "days_ahead": days_ahead,
                "results": [
                    {"recipient": r.recipient, "success": r.success, "message": r.message, "sent_at": r.sent_at}
                    for r in results
                ],
            }
        )

    except Exception as e:
        logger.error(f"Error sending expiration notifications: {e}")
        return Response({"error": "Failed to send notifications"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_packages_expiring_soon(request):
    """
    Get packages expiring within specified timeframe.

    Query Parameters:
    - days_ahead: Number of days to look ahead (default: 7)
    """
    days_ahead = int(request.GET.get("days_ahead", 7))

    try:
        expiring_packages = PackageExpirationService.get_packages_expiring_soon(days_ahead=days_ahead)

        serializer = PurchaseHistorySerializer(expiring_packages, many=True)

        return Response(
            {"expiring_packages": serializer.data, "count": len(expiring_packages), "days_ahead": days_ahead}
        )

    except Exception as e:
        logger.error(f"Error retrieving packages expiring soon: {e}")
        return Response({"error": "Failed to retrieve expiring packages"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def bulk_extend_packages(request):
    """
    Extend multiple packages at once.

    Body Parameters:
    - package_ids: List of package IDs to extend (required)
    - extension_days: Number of days to extend (required)
    - reason: Reason for bulk extension (optional)
    """
    try:
        package_ids = request.data.get("package_ids", [])
        extension_days = request.data.get("extension_days")
        reason = request.data.get("reason", "Bulk extension via admin API")

        if not package_ids:
            return Response({"error": "package_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not extension_days:
            return Response({"error": "extension_days is required"}, status=status.HTTP_400_BAD_REQUEST)

        packages = PurchaseTransaction.objects.filter(id__in=package_ids)

        if len(packages) != len(package_ids):
            return Response({"error": "Some package IDs were not found"}, status=status.HTTP_404_NOT_FOUND)

        results = PackageExpirationService.bulk_extend_packages(
            packages=list(packages), extension_days=int(extension_days), reason=reason
        )

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        return Response(
            {
                "extended_count": len(successful),
                "failed_count": len(failed),
                "extension_days": extension_days,
                "results": [
                    {
                        "package_id": r.package_id,
                        "success": r.success,
                        "original_expiry": r.original_expiry,
                        "new_expiry": r.new_expiry,
                        "error_message": r.error_message,
                    }
                    for r in results
                ],
            }
        )

    except Exception as e:
        logger.error(f"Error bulk extending packages: {e}")
        return Response({"error": "Failed to bulk extend packages"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# ADMINISTRATIVE PAYMENT ACTION APIs (GitHub Issue #116)
# ============================================================================

from finances.models import AdminAction
from finances.services.dispute_service import DisputeService
from finances.services.fraud_detection_service import FraudDetectionService
from finances.services.refund_service import RefundService


@api_view(["POST"])
@permission_classes([IsAdminUser])
def process_refund(request):
    """
    Process a refund for a purchase transaction.

    Body Parameters:
    - transaction_id: ID of the transaction to refund (required)
    - refund_amount: Amount to refund (optional, defaults to full refund)
    - reason: Reason for the refund (optional)
    - metadata: Additional refund metadata (optional)
    """
    try:
        transaction_id = request.data.get("transaction_id")
        if not transaction_id:
            return Response({"error": "transaction_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        refund_amount = request.data.get("refund_amount")
        if refund_amount:
            refund_amount = Decimal(str(refund_amount))

        reason = request.data.get("reason", "")
        metadata = request.data.get("metadata", {})

        # Get client IP for audit logging
        ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        refund_service = RefundService()
        result = refund_service.process_refund(
            transaction_id=int(transaction_id),
            refund_amount=refund_amount,
            reason=reason,
            admin_user=request.user,
            metadata={**metadata, "ip_address": ip_address, "user_agent": user_agent},
        )

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({"error": f"Invalid input: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        return Response({"error": "Failed to process refund"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_refund_status(request, refund_id):
    """
    Get the status of a Stripe refund.

    Path Parameters:
    - refund_id: Stripe refund ID
    """
    try:
        refund_service = RefundService()
        result = refund_service.get_refund_status(refund_id)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error getting refund status: {e}")
        return Response({"error": "Failed to get refund status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_transaction_refunds(request, transaction_id):
    """
    List all refunds for a specific transaction.

    Path Parameters:
    - transaction_id: ID of the transaction
    """
    try:
        refund_service = RefundService()
        result = refund_service.list_transaction_refunds(int(transaction_id))

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({"error": f"Invalid transaction ID: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error listing transaction refunds: {e}")
        return Response({"error": "Failed to list transaction refunds"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def sync_dispute_from_stripe(request):
    """
    Sync a dispute from Stripe and create/update local record.

    Body Parameters:
    - stripe_dispute_id: Stripe dispute ID to sync (required)
    """
    try:
        stripe_dispute_id = request.data.get("stripe_dispute_id")
        if not stripe_dispute_id:
            return Response({"error": "stripe_dispute_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        dispute_service = DisputeService()
        result = dispute_service.sync_dispute_from_stripe(stripe_dispute_id=stripe_dispute_id, admin_user=request.user)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error syncing dispute from Stripe: {e}")
        return Response({"error": "Failed to sync dispute from Stripe"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def submit_dispute_evidence(request, dispute_id):
    """
    Submit evidence for a dispute to Stripe.

    Path Parameters:
    - dispute_id: Local dispute ID

    Body Parameters:
    - evidence_data: Evidence data to submit (required)
    """
    try:
        evidence_data = request.data.get("evidence_data")
        if not evidence_data:
            return Response({"error": "evidence_data is required"}, status=status.HTTP_400_BAD_REQUEST)

        dispute_service = DisputeService()
        result = dispute_service.submit_dispute_evidence(
            dispute_id=int(dispute_id), evidence_data=evidence_data, admin_user=request.user
        )

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({"error": f"Invalid dispute ID: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error submitting dispute evidence: {e}")
        return Response({"error": "Failed to submit dispute evidence"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_dispute_details(request, stripe_dispute_id):
    """
    Get detailed dispute information from Stripe.

    Path Parameters:
    - stripe_dispute_id: Stripe dispute ID
    """
    try:
        dispute_service = DisputeService()
        result = dispute_service.get_dispute_details(stripe_dispute_id)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error getting dispute details: {e}")
        return Response({"error": "Failed to get dispute details"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_disputes(request):
    """
    List disputes from Stripe with optional filtering.

    Query Parameters:
    - status: Filter by dispute status (optional)
    - limit: Maximum number of disputes to return (default: 50)
    - created_after: Filter disputes created after this timestamp (optional)
    """
    try:
        status_filter = request.GET.get("status")
        limit = int(request.GET.get("limit", 50))
        created_after = request.GET.get("created_after")

        if created_after:
            created_after = int(created_after)

        dispute_service = DisputeService()
        result = dispute_service.list_disputes(status=status_filter, limit=limit, created_after=created_after)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({"error": f"Invalid parameter: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error listing disputes: {e}")
        return Response({"error": "Failed to list disputes"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@permission_classes([IsAdminUser])
def update_dispute_notes(request, dispute_id):
    """
    Update internal notes for a dispute.

    Path Parameters:
    - dispute_id: Local dispute ID

    Body Parameters:
    - internal_notes: Internal notes to update (required)
    """
    try:
        internal_notes = request.data.get("internal_notes")
        if internal_notes is None:
            return Response({"error": "internal_notes is required"}, status=status.HTTP_400_BAD_REQUEST)

        dispute_service = DisputeService()
        result = dispute_service.update_dispute_notes(
            dispute_id=int(dispute_id), internal_notes=internal_notes, admin_user=request.user
        )

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({"error": f"Invalid dispute ID: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error updating dispute notes: {e}")
        return Response({"error": "Failed to update dispute notes"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_overdue_disputes(request):
    """
    Get disputes with overdue evidence submission.
    """
    try:
        dispute_service = DisputeService()
        result = dispute_service.get_overdue_disputes()

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error getting overdue disputes: {e}")
        return Response({"error": "Failed to get overdue disputes"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def analyze_transaction_fraud(request, transaction_id):
    """
    Analyze a single transaction for fraud indicators.

    Path Parameters:
    - transaction_id: ID of the transaction to analyze
    """
    try:
        from finances.models import PurchaseTransaction

        try:
            transaction = PurchaseTransaction.objects.get(id=int(transaction_id))
        except PurchaseTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

        fraud_service = FraudDetectionService()
        result = fraud_service.analyze_transaction(transaction=transaction, admin_user=request.user)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({"error": f"Invalid transaction ID: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error analyzing transaction for fraud: {e}")
        return Response(
            {"error": "Failed to analyze transaction for fraud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def analyze_user_fraud(request, user_id):
    """
    Analyze a user's activity for fraud patterns.

    Path Parameters:
    - user_id: ID of the user to analyze

    Body Parameters:
    - days_back: Number of days to look back (default: 30)
    """
    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            user = User.objects.get(id=int(user_id))
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        days_back = int(request.data.get("days_back", 30))

        fraud_service = FraudDetectionService()
        result = fraud_service.analyze_user_activity(user=user, days_back=days_back, admin_user=request.user)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({"error": f"Invalid input: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error analyzing user for fraud: {e}")
        return Response({"error": "Failed to analyze user for fraud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def run_batch_fraud_analysis(request):
    """
    Run batch fraud analysis on recent transactions.

    Body Parameters:
    - hours_back: Number of hours to look back (default: 24)
    """
    try:
        hours_back = int(request.data.get("hours_back", 24))

        fraud_service = FraudDetectionService()
        result = fraud_service.run_batch_analysis(hours_back=hours_back, admin_user=request.user)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({"error": f"Invalid input: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error running batch fraud analysis: {e}")
        return Response({"error": "Failed to run batch fraud analysis"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_active_fraud_alerts(request):
    """
    Get active fraud alerts with optional filtering.

    Query Parameters:
    - severity: Filter by alert severity (optional)
    - limit: Maximum number of alerts to return (default: 50)
    """
    try:
        severity = request.GET.get("severity")
        limit = int(request.GET.get("limit", 50))

        fraud_service = FraudDetectionService()
        result = fraud_service.get_active_alerts(severity=severity, limit=limit)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({"error": f"Invalid parameter: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error getting active fraud alerts: {e}")
        return Response({"error": "Failed to get active fraud alerts"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def retry_failed_payment(request):
    """
    Retry a failed payment with new payment method.

    Body Parameters:
    - transaction_id: ID of the failed transaction (required)
    - payment_method_id: New Stripe payment method ID (required)
    - metadata: Additional metadata for the retry (optional)
    """
    try:
        transaction_id = request.data.get("transaction_id")
        payment_method_id = request.data.get("payment_method_id")

        if not transaction_id:
            return Response({"error": "transaction_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not payment_method_id:
            return Response({"error": "payment_method_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        metadata = request.data.get("metadata", {})

        # Get the failed transaction
        from finances.models import PurchaseTransaction, TransactionPaymentStatus

        try:
            transaction = PurchaseTransaction.objects.get(
                id=int(transaction_id), payment_status=TransactionPaymentStatus.FAILED
            )
        except PurchaseTransaction.DoesNotExist:
            return Response({"error": "Failed transaction not found"}, status=status.HTTP_404_NOT_FOUND)

        # Use PaymentService to retry the payment
        import stripe

        from finances.services.payment_service import PaymentService

        try:
            # Create new payment intent with the new payment method
            stripe.PaymentIntent.modify(transaction.stripe_payment_intent_id, payment_method=payment_method_id)

            # Confirm the payment intent
            payment_intent = stripe.PaymentIntent.confirm(transaction.stripe_payment_intent_id)

            # Update transaction if successful
            if payment_intent.status == "succeeded":
                payment_service = PaymentService()
                result = payment_service.confirm_payment_completion(payment_intent.id)

                # Log admin action
                AdminAction.objects.create(
                    action_type=AdminActionType.PAYMENT_RETRY,
                    action_description=f"Payment retry for transaction {transaction_id}",
                    admin_user=request.user,
                    target_user=transaction.student,
                    target_transaction=transaction,
                    success=result["success"],
                    result_message=f"Payment retry {'successful' if result['success'] else 'failed'}",
                    stripe_reference_id=payment_intent.id,
                    action_data={"payment_method_id": payment_method_id, "retry_metadata": metadata},
                )

                return Response(
                    {
                        "success": True,
                        "transaction_id": transaction_id,
                        "payment_intent_id": payment_intent.id,
                        "status": payment_intent.status,
                        "message": "Payment retry successful",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "success": False,
                        "transaction_id": transaction_id,
                        "payment_intent_id": payment_intent.id,
                        "status": payment_intent.status,
                        "message": f"Payment retry failed with status: {payment_intent.status}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except stripe.error.StripeError as e:
            # Log failed admin action
            AdminAction.objects.create(
                action_type=AdminActionType.PAYMENT_RETRY,
                action_description=f"Payment retry for transaction {transaction_id}",
                admin_user=request.user,
                target_user=transaction.student,
                target_transaction=transaction,
                success=False,
                result_message=f"Stripe error during retry: {e!s}",
                stripe_reference_id=transaction.stripe_payment_intent_id,
                action_data={"payment_method_id": payment_method_id, "error": str(e)},
            )

            return Response(
                {"success": False, "error_type": "stripe_error", "message": f"Stripe error: {e!s}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except ValueError as e:
        return Response({"error": f"Invalid input: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error retrying failed payment: {e}")
        return Response({"error": "Failed to retry payment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_admin_action_log(request):
    """
    Get administrative action audit log.

    Query Parameters:
    - limit: Maximum number of actions to return (default: 100)
    - action_type: Filter by action type (optional)
    - admin_user_id: Filter by admin user ID (optional)
    - success: Filter by success status (optional)
    - days_back: Number of days to look back (default: 30)
    """
    try:
        limit = int(request.GET.get("limit", 100))
        action_type = request.GET.get("action_type")
        admin_user_id = request.GET.get("admin_user_id")
        success = request.GET.get("success")
        days_back = int(request.GET.get("days_back", 30))

        # Build query
        cutoff_date = timezone.now() - timedelta(days=days_back)
        actions = AdminAction.objects.filter(created_at__gte=cutoff_date).select_related(
            "admin_user", "target_user", "target_transaction", "target_dispute"
        )

        if action_type:
            actions = actions.filter(action_type=action_type)

        if admin_user_id:
            actions = actions.filter(admin_user_id=int(admin_user_id))

        if success is not None:
            actions = actions.filter(success=success.lower() == "true")

        actions = actions.order_by("-created_at")[:limit]

        action_data = []
        for action in actions:
            action_data.append(
                {
                    "id": action.id,
                    "action_type": action.action_type,
                    "action_description": action.action_description,
                    "admin_user": {
                        "id": action.admin_user.id,
                        "email": action.admin_user.email,
                        "name": action.admin_user.name,
                    },
                    "target_user": {
                        "id": action.target_user.id,
                        "email": action.target_user.email,
                        "name": action.target_user.name,
                    }
                    if action.target_user
                    else None,
                    "success": action.success,
                    "result_message": action.result_message,
                    "amount_impacted": action.amount_impacted,
                    "stripe_reference_id": action.stripe_reference_id,
                    "two_factor_verified": action.two_factor_verified,
                    "created_at": action.created_at,
                    "action_data": action.action_data,
                }
            )

        return Response(
            {
                "actions": action_data,
                "count": len(action_data),
                "total_actions": AdminAction.objects.filter(created_at__gte=cutoff_date).count(),
                "days_back": days_back,
            },
            status=status.HTTP_200_OK,
        )

    except ValueError as e:
        return Response({"error": f"Invalid parameter: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error getting admin action log: {e}")
        return Response({"error": "Failed to get admin action log"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
