"""
API views for the finances app.
"""

from datetime import timedelta
from decimal import Decimal
import logging

from django.apps import apps
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Cross-app models will be loaded at runtime using apps.get_model()
from accounts.permissions import SchoolPermissionMixin
from common.throttles import PurchaseInitiationEmailThrottle, PurchaseInitiationThrottle

from .models import (
    ClassSession,
    PlanType,
    PricingPlan,
    PurchaseTransaction,
    SchoolBillingSettings,
    StudentAccountBalance,
    TeacherCompensationRule,
    TeacherPaymentEntry,
    TransactionPaymentStatus,
    TransactionType,
)
from .serializers import (
    BulkPaymentProcessorSerializer,
    ClassSessionSerializer,
    EnhancedStudentBalanceSummarySerializer,
    MonthlyPaymentSummarySerializer,
    PaymentCalculationSerializer,
    PricingPlanSerializer,
    PurchaseHistorySerializer,
    PurchaseInitiationRequestSerializer,
    SchoolBillingSettingsSerializer,
    TeacherCompensationRuleSerializer,
    TeacherPaymentEntrySerializer,
    TransactionHistorySerializer,
)
from .services import BulkPaymentProcessor, TeacherPaymentCalculator
from .services.payment_service import PaymentService
from .services.stripe_base import StripeService


class SchoolBillingSettingsViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing school billing settings."""

    serializer_class = SchoolBillingSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter settings by user's schools."""
        user_schools = self.get_user_schools()
        return SchoolBillingSettings.objects.filter(school__in=user_schools)

    def perform_create(self, serializer):
        """Ensure the school belongs to the user."""
        school = serializer.validated_data["school"]
        user_schools = self.get_user_schools()

        if school not in user_schools:
            raise PermissionError("You don't have permission to create settings for this school")

        serializer.save()

    @action(detail=False, methods=["get"])
    def current_school(self, request):
        """
        Get billing settings for the user's primary school.
        If user manages multiple schools, returns the first one.
        Frontend can specify school_id parameter to override.
        """
        School = apps.get_model("accounts", "School")
        school_id = request.query_params.get("school_id")
        user_schools = self.get_user_schools()

        if not user_schools.exists():
            return Response(
                {"error": "You are not associated with any schools"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if school_id:
            try:
                school = user_schools.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {"error": "You don't have permission to access this school"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            # Use first school if user manages multiple schools
            school = user_schools.first()

        settings, created = SchoolBillingSettings.objects.get_or_create(
            school=school,
            defaults={
                "trial_cost_absorption": "school",
                "teacher_payment_frequency": "monthly",
                "payment_day_of_month": 1,
            },
        )

        serializer = self.get_serializer(settings)
        return Response(serializer.data)


class TeacherCompensationRuleViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing teacher compensation rules."""

    serializer_class = TeacherCompensationRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter rules by user's schools."""
        user_schools = self.get_user_schools()
        queryset = TeacherCompensationRule.objects.filter(school__in=user_schools)

        # Filter by teacher if specified
        teacher_id = self.request.query_params.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset.select_related("teacher__user", "school").order_by("-created_at")

    def perform_create(self, serializer):
        """Automatically set school based on user's permissions."""
        # If no school specified, use user's primary school
        if "school" not in serializer.validated_data:
            user_schools = self.get_user_schools()
            if not user_schools.exists():
                raise PermissionError("You are not associated with any schools")
            serializer.validated_data["school"] = user_schools.first()
        else:
            # Verify user has permission for specified school
            school = serializer.validated_data["school"]
            user_schools = self.get_user_schools()
            if school not in user_schools:
                raise PermissionError("You don't have permission to create rules for this school")

        serializer.save()

    @action(detail=False, methods=["get"])
    def for_teacher(self, request):
        """Get compensation rules for a specific teacher (in user's schools)."""
        teacher_id = request.query_params.get("teacher_id")

        if not teacher_id:
            return Response({"error": "teacher_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        user_schools = self.get_user_schools()
        rules = TeacherCompensationRule.objects.filter(
            teacher_id=teacher_id, school__in=user_schools, is_active=True
        ).select_related("teacher__user", "school")

        serializer = self.get_serializer(rules, many=True)
        return Response(serializer.data)


class ClassSessionViewSet(SchoolPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for managing class sessions."""

    serializer_class = ClassSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter sessions by user's schools."""
        user_schools = self.get_user_schools()
        queryset = ClassSession.objects.filter(school__in=user_schools)

        # Filter by teacher if specified
        teacher_id = self.request.query_params.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        # Filter by status
        session_status = self.request.query_params.get("status")
        if session_status:
            queryset = queryset.filter(status=session_status)

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        end_date = self.request.query_params.get("end_date")
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Filter by payment status
        payment_calculated = self.request.query_params.get("payment_calculated")
        if payment_calculated is not None:
            if payment_calculated.lower() == "true":
                queryset = queryset.filter(payment_entry__isnull=False)
            else:
                queryset = queryset.filter(payment_entry__isnull=True)

        return (
            queryset.select_related("teacher__user", "school", "payment_entry")
            .prefetch_related("students")
            .order_by("-date", "-start_time")
        )

    def perform_create(self, serializer):
        """Automatically set school based on user's permissions."""
        if "school" not in serializer.validated_data:
            user_schools = self.get_user_schools()
            if not user_schools.exists():
                raise PermissionError("You are not associated with any schools")
            serializer.validated_data["school"] = user_schools.first()
        else:
            # Verify user has permission for specified school
            school = serializer.validated_data["school"]
            user_schools = self.get_user_schools()
            if school not in user_schools:
                raise PermissionError("You don't have permission to create sessions for this school")

        serializer.save()

    def create(self, request, *args, **kwargs):
        """Create session using SessionBookingService."""
        from classroom.services.session_booking_service import SessionBookingError, SessionBookingService
        from finances.services.hour_deduction_service import InsufficientBalanceError, PackageExpiredError

        # Validate required fields
        required_fields = [
            "teacher",
            "school",
            "date",
            "start_time",
            "end_time",
            "session_type",
            "grade_level",
            "students",
        ]
        for field in required_fields:
            if field not in request.data:
                return Response({"error": f'Field "{field}" is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify user has permission for the specified school
        user_schools = self.get_user_schools()
        school_id = request.data.get("school")
        if school_id not in [school.id for school in user_schools]:
            return Response(
                {"error": "You don't have permission to create sessions for this school"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Use SessionBookingService to create the session
            session, hour_deduction_info = SessionBookingService.book_session(
                teacher_id=request.data["teacher"],
                school_id=request.data["school"],
                date=request.data["date"],
                start_time=request.data["start_time"],
                end_time=request.data["end_time"],
                session_type=request.data["session_type"],
                grade_level=request.data["grade_level"],
                student_ids=request.data["students"],
                is_trial=request.data.get("is_trial", False),
                is_makeup=request.data.get("is_makeup", False),
                notes=request.data.get("notes", ""),
            )

            # Serialize the created session
            serializer = self.get_serializer(session)
            response_data = serializer.data.copy()
            response_data["hour_deduction"] = hour_deduction_info

            headers = self.get_success_headers(response_data)
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

        except (InsufficientBalanceError, PackageExpiredError) as e:
            return Response(
                {
                    "error": str(e),
                    "error_type": "insufficient_balance"
                    if isinstance(e, InsufficientBalanceError)
                    else "package_expired",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except SessionBookingError as e:
            return Response({"error": str(e), "error_type": "booking_error"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during session booking: {e}")
            return Response(
                {"error": "An error occurred while booking the session", "error_type": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def calculate_payment(self, request, pk=None):
        """Calculate payment for a specific session."""
        session = self.get_object()

        if session.status != "completed":
            return Response(
                {"error": "Can only calculate payments for completed sessions"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(session, "payment_entry"):
            return Response(
                {"error": "Payment already calculated for this session"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment_entry = TeacherPaymentCalculator.calculate_session_payment(session)

            response_data = {
                "session_id": session.id,
                "payment_entry_id": payment_entry.id,
                "amount_calculated": payment_entry.amount_earned,
                "rate_applied": payment_entry.rate_applied,
                "hours": payment_entry.hours_taught,
                "notes": payment_entry.calculation_notes,
            }

            serializer = PaymentCalculationSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Error calculating payment: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def bulk_calculate_payments(self, request):
        """Calculate payments for multiple sessions in user's schools."""
        serializer = BulkPaymentProcessorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Process for all user's schools
        user_schools = self.get_user_schools()
        all_results = []

        for school in user_schools:
            try:
                result = BulkPaymentProcessor.process_completed_sessions(
                    school=school, start_date=start_date, end_date=end_date
                )
                result["school_id"] = school.id
                result["school_name"] = school.name
                all_results.append(result)

            except Exception as e:
                all_results.append(
                    {
                        "school_id": school.id,
                        "school_name": school.name,
                        "error": f"Error processing payments: {e!s}",
                        "total_sessions": 0,
                        "processed_count": 0,
                        "errors": [],
                    }
                )

        return Response({"results": all_results}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a session using SessionBookingService."""
        from classroom.services.session_booking_service import SessionBookingError, SessionBookingService

        session = self.get_object()
        reason = request.data.get("reason", "Session cancelled via API")

        try:
            cancellation_info = SessionBookingService.cancel_session(session.id, reason)

            response_data = {
                "session_id": cancellation_info["session_id"],
                "status": cancellation_info["status"],
                "cancelled_at": cancellation_info["cancelled_at"].isoformat()
                if cancellation_info["cancelled_at"]
                else None,
                "reason": cancellation_info["reason"],
                "refund_info": cancellation_info["refund_info"],
                "message": f"Session cancelled successfully. {cancellation_info['refund_info']['refunded_hours']} hours refunded to {cancellation_info['refund_info']['students_affected']} students.",
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except SessionBookingError as e:
            return Response({"error": str(e), "error_type": "booking_error"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error cancelling session {session.id}: {e}")
            return Response(
                {"error": "An error occurred while cancelling the session", "error_type": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def adjust_duration(self, request, pk=None):
        """Adjust session duration and handle hour adjustments."""
        from decimal import Decimal, InvalidOperation

        from classroom.services.session_booking_service import SessionBookingError, SessionBookingService

        session = self.get_object()

        # Validate required fields
        try:
            actual_duration_hours = Decimal(str(request.data.get("actual_duration_hours")))
        except (TypeError, InvalidOperation):
            return Response(
                {"error": "actual_duration_hours is required and must be a valid decimal"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "Duration adjusted via API")

        try:
            adjustment_info = SessionBookingService.adjust_session_duration(session.id, actual_duration_hours, reason)

            return Response(adjustment_info, status=status.HTTP_200_OK)

        except SessionBookingError as e:
            return Response({"error": str(e), "error_type": "booking_error"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error adjusting session duration for {session.id}: {e}")
            return Response(
                {"error": "An error occurred while adjusting session duration", "error_type": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def booking_summary(self, request, pk=None):
        """Get comprehensive booking summary for a session."""
        from classroom.services.session_booking_service import SessionBookingError, SessionBookingService

        session = self.get_object()

        try:
            summary = SessionBookingService.get_session_booking_summary(session.id)
            return Response(summary, status=status.HTTP_200_OK)

        except SessionBookingError as e:
            return Response({"error": str(e), "error_type": "booking_error"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error getting booking summary for session {session.id}: {e}")
            return Response(
                {"error": "An error occurred while getting booking summary", "error_type": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a session and process hour refunds."""
        from classroom.services.session_booking_service import SessionBookingError, SessionBookingService

        session = self.get_object()
        reason = request.data.get("reason", "")

        try:
            cancellation_info = SessionBookingService.cancel_session(session_id=session.id, reason=reason)

            return Response(
                {
                    "success": True,
                    "message": f"Session {session.id} cancelled successfully",
                    "cancellation_details": cancellation_info,
                },
                status=status.HTTP_200_OK,
            )

        except SessionBookingError as e:
            return Response({"error": str(e), "error_type": "booking_error"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error cancelling session {session.id}: {e}")
            return Response(
                {"error": "An error occurred while cancelling the session", "error_type": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TeacherPaymentEntryViewSet(SchoolPermissionMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing teacher payment entries (read-only)."""

    serializer_class = TeacherPaymentEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter payment entries by user's schools."""
        user_schools = self.get_user_schools()
        queryset = TeacherPaymentEntry.objects.filter(school__in=user_schools)

        # Filter by teacher if specified
        teacher_id = self.request.query_params.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        # Filter by billing period
        billing_period = self.request.query_params.get("billing_period")
        if billing_period:
            queryset = queryset.filter(billing_period=billing_period)

        # Filter by payment status
        payment_status = self.request.query_params.get("payment_status")
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        return queryset.select_related("teacher__user", "school", "session", "compensation_rule").order_by(
            "-created_at"
        )

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        """Update payment status (admin only action)."""
        payment_entry = self.get_object()
        new_status = request.data.get("payment_status")

        if new_status not in ["pending", "calculated", "paid"]:
            return Response({"error": "Invalid payment status"}, status=status.HTTP_400_BAD_REQUEST)

        payment_entry.payment_status = new_status
        payment_entry.save()

        serializer = self.get_serializer(payment_entry)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def monthly_summary(self, request):
        """Get monthly payment summary for a teacher."""
        TeacherProfile = apps.get_model("accounts", "TeacherProfile")

        teacher_id = request.query_params.get("teacher_id")
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        if not all([teacher_id, year, month]):
            return Response(
                {"error": "teacher_id, year, and month are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            year = int(year)
            month = int(month)
            teacher = TeacherProfile.objects.get(id=teacher_id)

            # Use user's primary school (could be extended to support multiple schools)
            user_schools = self.get_user_schools()
            if not user_schools.exists():
                return Response(
                    {"error": "You are not associated with any schools"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            school = user_schools.first()

            # Get monthly summary
            summary = TeacherPaymentCalculator.calculate_monthly_total(teacher, school, year, month)

            # Add payment status breakdown
            payment_entries = summary["payment_entries"]
            pending_amount = payment_entries.filter(payment_status="pending").aggregate(total=Sum("amount_earned"))[
                "total"
            ] or Decimal("0.00")
            calculated_amount = payment_entries.filter(payment_status="calculated").aggregate(
                total=Sum("amount_earned")
            )["total"] or Decimal("0.00")
            paid_amount = payment_entries.filter(payment_status="paid").aggregate(total=Sum("amount_earned"))[
                "total"
            ] or Decimal("0.00")

            # Format for serializer
            summary_data = {
                "billing_period": summary["billing_period"],
                "teacher_id": teacher.id,
                "teacher_name": teacher.user.name,
                "teacher_email": teacher.user.email,
                "school_id": school.id,
                "school_name": school.name,
                "total_hours": summary["total_hours"],
                "total_amount": summary["total_amount"],
                "session_count": summary["session_count"],
                "individual_sessions": summary["individual_sessions"],
                "group_sessions": summary["group_sessions"],
                "trial_sessions": summary["trial_sessions"],
                "pending_amount": pending_amount,
                "calculated_amount": calculated_amount,
                "paid_amount": paid_amount,
            }

            serializer = MonthlyPaymentSummarySerializer(summary_data)
            return Response(serializer.data)

        except (ValueError, TeacherProfile.DoesNotExist) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def generate_invoice(self, request):
        """Generate invoice data for a teacher for a specific period."""
        TeacherProfile = apps.get_model("accounts", "TeacherProfile")

        teacher_id = request.query_params.get("teacher_id")
        billing_period = request.query_params.get("billing_period")  # YYYY-MM format

        if not all([teacher_id, billing_period]):
            return Response(
                {"error": "teacher_id and billing_period are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            teacher = TeacherProfile.objects.get(id=teacher_id)

            # Use user's primary school
            user_schools = self.get_user_schools()
            if not user_schools.exists():
                return Response(
                    {"error": "You are not associated with any schools"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            school = user_schools.first()

            # Get payment entries for the period
            payment_entries = (
                TeacherPaymentEntry.objects.filter(teacher=teacher, school=school, billing_period=billing_period)
                .select_related("session", "compensation_rule")
                .order_by("session__date")
            )

            if not payment_entries.exists():
                return Response(
                    {"error": "No payment entries found for the specified period"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Calculate totals
            total_amount = payment_entries.aggregate(total=Sum("amount_earned"))["total"]
            total_hours = payment_entries.aggregate(total=Sum("hours_taught"))["total"]

            # Group by session type and payment rule
            individual_sessions = payment_entries.filter(session__session_type="individual")
            group_sessions = payment_entries.filter(session__session_type="group")
            trial_sessions = payment_entries.filter(session__is_trial=True)

            invoice_data = {
                "invoice_period": billing_period,
                "teacher": {
                    "id": teacher.id,
                    "name": teacher.user.name,
                    "email": teacher.user.email,
                },
                "school": {
                    "id": school.id,
                    "name": school.name,
                    "contact_email": school.contact_email,
                    "address": school.address,
                },
                "summary": {
                    "total_amount": total_amount,
                    "total_hours": total_hours,
                    "session_count": payment_entries.count(),
                    "individual_sessions": individual_sessions.count(),
                    "group_sessions": group_sessions.count(),
                    "trial_sessions": trial_sessions.count(),
                },
                "line_items": TeacherPaymentEntrySerializer(payment_entries, many=True).data,
                "generated_at": timezone.now().isoformat(),
            }

            return Response(invoice_data)

        except TeacherProfile.DoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([])  # Allow unauthenticated access
def active_pricing_plans(request):
    """
    API endpoint to fetch active pricing plans with caching.

    This endpoint provides public access to active pricing plans for
    the frontend pricing display. Results are cached for 1 hour to
    improve performance and reduce database load.

    Returns:
        Response: List of active pricing plans ordered by display_order

    Cache Strategy:
        - Cache key: 'active_pricing_plans'
        - Cache duration: 3600 seconds (1 hour)
        - Cache is cleared when pricing plans are modified via Django Admin
    """
    # Check cache first
    cache_key = "active_pricing_plans"
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return Response(cached_data)

    # Cache miss - fetch from database
    active_plans = PricingPlan.active.all()
    serializer = PricingPlanSerializer(active_plans, many=True)

    # Cache the result for 1 hour
    cache.set(cache_key, serializer.data, timeout=3600)

    return Response(serializer.data)


# Initialize logger for general finance views
logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events securely with comprehensive processing.

    This endpoint processes webhook events from Stripe including:
    - payment_intent.succeeded: Credit hours and update transaction status
    - payment_intent.payment_failed: Update transaction status with failure details
    - payment_intent.canceled: Handle payment cancellation

    Features:
    - Signature verification using STRIPE_WEBHOOK_SECRET
    - Idempotent processing to prevent duplicate updates
    - Comprehensive logging for all webhook events
    - Atomic database operations for consistency
    - Appropriate HTTP status codes for Stripe retry logic

    Args:
        request: Django HTTP request containing webhook payload and signature

    Returns:
        HttpResponse with appropriate status code:
        - 200: Successfully processed or already processed (idempotent)
        - 400: Invalid signature or malformed request
        - 500: Processing failure (triggers Stripe retry)
    """
    webhook_id = None
    event_type = None

    try:
        # Extract request data
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        if not sig_header:
            logger.warning("Webhook request missing Stripe signature header")
            return HttpResponse("Missing signature", status=400)

        if not payload:
            logger.warning("Webhook request missing payload")
            return HttpResponse("Missing payload", status=400)

        # Initialize Stripe service and verify webhook signature
        stripe_service = StripeService()
        result = stripe_service.construct_webhook_event(payload.decode("utf-8"), sig_header)

        if not result["success"]:
            logger.error(f"Webhook signature verification failed: {result.get('message', 'Unknown error')}")
            return HttpResponse("Invalid signature", status=400)

        event = result["event"]
        event_type = event.get("type")
        webhook_id = event.get("id")

        logger.info(f"Received webhook event: {event_type} (ID: {webhook_id})")

        # Check if event type is supported
        if not stripe_service.is_webhook_event_type_supported(event_type):
            logger.info(f"Unsupported webhook event type: {event_type} (ID: {webhook_id})")
            return HttpResponse("Event type not supported", status=200)

        # Process the event with atomic database operations
        with transaction.atomic():
            success = _process_webhook_event(event, event_type, webhook_id)

        if success:
            logger.info(f"Successfully processed webhook event: {event_type} (ID: {webhook_id})")
            return HttpResponse("Webhook processed successfully", status=200)
        else:
            logger.error(f"Failed to process webhook event: {event_type} (ID: {webhook_id})")
            return HttpResponse("Webhook processing failed", status=500)

    except Exception as e:
        logger.error(
            f"Unexpected error in Stripe webhook handler for event {event_type} (ID: {webhook_id}): {e!s}",
            exc_info=True,
        )
        return HttpResponse("Internal server error", status=500)


def _process_webhook_event(event, event_type, webhook_id):
    """
    Process individual webhook events based on their type with idempotent handling.

    Args:
        event: The Stripe event object
        event_type: The type of the event
        webhook_id: The webhook event ID for logging

    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # Map event types to handler functions
        event_handlers = {
            "payment_intent.succeeded": _handle_payment_intent_succeeded,
            "payment_intent.payment_failed": _handle_payment_intent_failed,
            "payment_intent.canceled": _handle_payment_intent_canceled,
        }

        handler = event_handlers.get(event_type)
        if handler:
            return handler(event, webhook_id)
        else:
            # For supported but not yet implemented event types
            logger.info(f"Event type {event_type} is supported but handler not implemented (ID: {webhook_id})")
            return True

    except Exception as e:
        logger.error(f"Error processing {event_type} event (ID: {webhook_id}): {e!s}", exc_info=True)
        return False


def _handle_payment_intent_succeeded(event, webhook_id):
    """
    Handle successful payment intent events with idempotent processing.

    This handler:
    1. Extracts payment intent ID from event
    2. Uses PaymentService to confirm payment completion
    3. Credits hours to student account
    4. Updates transaction status to completed
    5. Handles idempotent processing for duplicate events

    Args:
        event: The Stripe event object
        webhook_id: The webhook event ID for logging

    Returns:
        bool: True if processing was successful
    """
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]

    logger.info(f"Processing successful payment intent: {payment_intent_id} (Webhook ID: {webhook_id})")

    try:
        # Check if this payment intent has already been processed (idempotent check)
        try:
            from .models import PurchaseTransaction, TransactionPaymentStatus

            existing_transaction = PurchaseTransaction.objects.get(stripe_payment_intent_id=payment_intent_id)
            if existing_transaction.payment_status == TransactionPaymentStatus.COMPLETED:
                logger.info(
                    f"Payment intent {payment_intent_id} already completed, "
                    f"skipping processing (idempotent) (Webhook ID: {webhook_id})"
                )
                return True
        except PurchaseTransaction.DoesNotExist:
            logger.error(f"No transaction found for payment intent {payment_intent_id} (Webhook ID: {webhook_id})")
            return False

        # Use PaymentService to confirm payment completion
        payment_service = PaymentService()
        result = payment_service.confirm_payment_completion(payment_intent_id)

        if result["success"]:
            logger.info(
                f"Successfully processed payment completion for transaction "
                f"{result.get('transaction_id')} (Webhook ID: {webhook_id})"
            )
            return True
        else:
            # Handle the case where payment is already completed (idempotent)
            if result.get("error_type") == "invalid_transaction_state":
                logger.info(
                    f"Payment intent {payment_intent_id} already in completed state, "
                    f"treating as success (idempotent) (Webhook ID: {webhook_id})"
                )
                return True

            logger.error(
                f"Payment service failed to confirm completion for {payment_intent_id}: "
                f"{result.get('message')} (Webhook ID: {webhook_id})"
            )
            return False

    except Exception as e:
        logger.error(
            f"Unexpected error handling payment success for {payment_intent_id}: {e!s} (Webhook ID: {webhook_id})",
            exc_info=True,
        )
        return False


def _handle_payment_intent_failed(event, webhook_id):
    """
    Handle failed payment intent events with comprehensive error tracking.

    This handler:
    1. Extracts payment intent ID and error details from event
    2. Uses PaymentService to handle payment failure
    3. Updates transaction status to failed
    4. Adds failure metadata to transaction record
    5. Handles idempotent processing for duplicate events

    Args:
        event: The Stripe event object
        webhook_id: The webhook event ID for logging

    Returns:
        bool: True if processing was successful
    """
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]

    # Extract error message from payment intent
    error_message = "Payment failed"
    if payment_intent.get("last_payment_error"):
        error_message = payment_intent["last_payment_error"].get("message", error_message)

    logger.info(
        f"Processing failed payment intent: {payment_intent_id} with error: {error_message} (Webhook ID: {webhook_id})"
    )

    try:
        # Check if this payment intent has already been processed (idempotent check)
        try:
            from .models import PurchaseTransaction, TransactionPaymentStatus

            existing_transaction = PurchaseTransaction.objects.get(stripe_payment_intent_id=payment_intent_id)
            if existing_transaction.payment_status == TransactionPaymentStatus.FAILED:
                logger.info(
                    f"Payment intent {payment_intent_id} already marked as failed, "
                    f"skipping processing (idempotent) (Webhook ID: {webhook_id})"
                )
                return True
        except PurchaseTransaction.DoesNotExist:
            logger.error(f"No transaction found for payment intent {payment_intent_id} (Webhook ID: {webhook_id})")
            return False

        # Use PaymentService to handle payment failure
        payment_service = PaymentService()
        result = payment_service.handle_payment_failure(payment_intent_id, error_message)

        if result["success"]:
            logger.info(
                f"Successfully processed payment failure for transaction "
                f"{result.get('transaction_id')} (Webhook ID: {webhook_id})"
            )
            return True
        else:
            # Handle the case where payment is already failed (idempotent)
            if result.get("error_type") == "invalid_transaction_state":
                logger.info(
                    f"Payment intent {payment_intent_id} already in failed state, "
                    f"treating as success (idempotent) (Webhook ID: {webhook_id})"
                )
                return True

            logger.error(
                f"Payment service failed to handle failure for {payment_intent_id}: "
                f"{result.get('message')} (Webhook ID: {webhook_id})"
            )
            return False

    except Exception as e:
        logger.error(
            f"Unexpected error handling payment failure for {payment_intent_id}: {e!s} (Webhook ID: {webhook_id})",
            exc_info=True,
        )
        return False


def _handle_payment_intent_canceled(event, webhook_id):
    """
    Handle canceled payment intent events.

    This handler:
    1. Extracts payment intent ID from event
    2. Uses PaymentService to handle payment cancellation as a failure
    3. Updates transaction status to failed with cancellation reason
    4. Handles idempotent processing for duplicate events

    Args:
        event: The Stripe event object
        webhook_id: The webhook event ID for logging

    Returns:
        bool: True if processing was successful
    """
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]

    logger.info(f"Processing canceled payment intent: {payment_intent_id} (Webhook ID: {webhook_id})")

    try:
        # Check if this payment intent has already been processed (idempotent check)
        try:
            from .models import PurchaseTransaction, TransactionPaymentStatus

            existing_transaction = PurchaseTransaction.objects.get(stripe_payment_intent_id=payment_intent_id)
            if existing_transaction.payment_status in [
                TransactionPaymentStatus.FAILED,
                TransactionPaymentStatus.CANCELLED,
            ]:
                logger.info(
                    f"Payment intent {payment_intent_id} already marked as failed/cancelled, "
                    f"skipping processing (idempotent) (Webhook ID: {webhook_id})"
                )
                return True
        except PurchaseTransaction.DoesNotExist:
            logger.error(f"No transaction found for payment intent {payment_intent_id} (Webhook ID: {webhook_id})")
            return False

        # Handle cancellation as a payment failure
        payment_service = PaymentService()
        result = payment_service.handle_payment_failure(payment_intent_id, "Payment was canceled")

        if result["success"]:
            logger.info(
                f"Successfully processed payment cancellation for transaction "
                f"{result.get('transaction_id')} (Webhook ID: {webhook_id})"
            )
            return True
        else:
            # Handle the case where payment is already failed/cancelled (idempotent)
            if result.get("error_type") == "invalid_transaction_state":
                logger.info(
                    f"Payment intent {payment_intent_id} already in failed/cancelled state, "
                    f"treating as success (idempotent) (Webhook ID: {webhook_id})"
                )
                return True

            logger.error(
                f"Payment service failed to handle cancellation for {payment_intent_id}: "
                f"{result.get('message')} (Webhook ID: {webhook_id})"
            )
            return False

    except Exception as e:
        logger.error(
            f"Unexpected error handling payment cancellation for {payment_intent_id}: {e!s} (Webhook ID: {webhook_id})",
            exc_info=True,
        )
        return False


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stripe_config(request):
    """
    Get Stripe configuration for frontend use.

    Returns the public key and other safe configuration needed
    by the frontend to initialize Stripe.
    """
    try:
        stripe_service = StripeService()

        config_data = {"public_key": stripe_service.get_public_key(), "success": True}

        return Response(config_data)

    except Exception as e:
        logger.error(f"Error getting Stripe configuration: {e}")
        return Response(
            {"success": False, "error": "Unable to load payment configuration"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stripe_connection_test(request):
    """
    Test Stripe API connection.

    This endpoint allows administrators to verify that the Stripe
    integration is working correctly.
    """
    try:
        stripe_service = StripeService()
        result = stripe_service.verify_api_connection()

        if result["success"]:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    except Exception as e:
        logger.error(f"Error testing Stripe connection: {e}")
        return Response(
            {"success": False, "error": "Unable to test payment service connection"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([])  # Allow both authenticated and unauthenticated access
@throttle_classes([PurchaseInitiationThrottle, PurchaseInitiationEmailThrottle])
def purchase_initiate(request):
    """
    API endpoint to initiate tutoring hour purchases for students.

    This endpoint allows both authenticated users and guests to initiate purchases
    of tutoring hour packages or subscriptions. It integrates with Stripe to create
    payment intents and maintains transaction records for order management.

    Features:
    - Support for both package and subscription plan types
    - Guest user creation and management
    - Stripe payment intent creation with proper metadata
    - Atomic database transactions for consistency
    - Comprehensive validation and error handling
    - Security measures against common attacks
    - Rate limiting: 10 attempts/hour per IP, 5 attempts/hour per email

    Request Format:
    {
        "plan_id": 1,
        "student_info": {
            "name": "Student Name",
            "email": "student@example.com"
        }
    }

    Response Format (Success):
    {
        "success": true,
        "client_secret": "pi_xxx_secret_yyy",
        "transaction_id": 123,
        "payment_intent_id": "pi_xxx",
        "plan_details": {...},
        "message": "Purchase initiated successfully"
    }

    Response Format (Error):
    {
        "success": false,
        "error_type": "validation_error",
        "message": "Description of the error",
        "details": {...}
    }

    Args:
        request: Django HTTP request containing purchase data

    Returns:
        Response: JSON response with payment intent details or error information
    """
    logger.info(f"Purchase initiation request from user: {request.user if request.user.is_authenticated else 'Guest'}")

    try:
        # DRF automatically parses JSON, so we can just use request.data
        # Handle JSON parsing errors are automatically handled by DRF
        request_data = request.data

        # Validate request data using serializer
        serializer = PurchaseInitiationRequestSerializer(data=request_data)
        if not serializer.is_valid():
            logger.warning(f"Invalid purchase initiation request: {serializer.errors}")

            # Create a more descriptive error message
            error_message = "Invalid request data"
            if serializer.errors:
                # Get the first error to make message more specific
                first_field = next(iter(serializer.errors.keys()))
                field_errors = serializer.errors[first_field]
                if isinstance(field_errors, list) and field_errors:
                    first_error = str(field_errors[0])
                elif isinstance(field_errors, dict):
                    # Handle nested field errors (like student_info.email)
                    first_nested_field = next(iter(field_errors.keys()))
                    nested_errors = field_errors[first_nested_field]
                    if isinstance(nested_errors, list) and nested_errors:
                        first_error = str(nested_errors[0])
                        first_field = f"{first_field}.{first_nested_field}"
                    else:
                        first_error = "is invalid"
                else:
                    first_error = "is invalid"
                error_message = f"{first_field}: {first_error}"

            return Response(
                {
                    "success": False,
                    "error_type": "validation_error",
                    "message": error_message,
                    "field_errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        plan_id = validated_data["plan_id"]
        student_info = validated_data["student_info"]

        # Get the pricing plan
        try:
            pricing_plan = PricingPlan.objects.get(id=plan_id, is_active=True)
        except PricingPlan.DoesNotExist:
            logger.error(f"Pricing plan {plan_id} not found or inactive")
            return Response(
                {
                    "success": False,
                    "error_type": "validation_error",
                    "message": f"Pricing plan with ID {plan_id} not found or inactive",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Determine the student user
        student_user = _get_or_create_student_user(
            request.user if request.user.is_authenticated else None, student_info
        )

        # Ensure student has an account balance record
        student_balance, created = StudentAccountBalance.objects.get_or_create(
            student=student_user,
            defaults={
                "hours_purchased": Decimal("0.00"),
                "hours_consumed": Decimal("0.00"),
                "balance_amount": Decimal("0.00"),
            },
        )

        if created:
            logger.info(f"Created new student account balance for user {student_user.id}")

        # Prepare metadata for Stripe and transaction
        purchase_metadata = {
            "plan_id": pricing_plan.id,
            "plan_name": pricing_plan.name,
            "plan_type": pricing_plan.plan_type,
            "hours_included": str(pricing_plan.hours_included),
            "price_eur": str(pricing_plan.price_eur),
            "student_name": student_user.name,
            "student_email": student_user.email,
            "amount": str(pricing_plan.price_eur),
        }

        # Add subscription indicator for proper type detection
        if pricing_plan.plan_type == PlanType.SUBSCRIPTION:
            purchase_metadata["subscription_name"] = pricing_plan.name

        # Add validity information for packages
        if pricing_plan.plan_type == PlanType.PACKAGE and pricing_plan.validity_days:
            purchase_metadata["validity_days"] = pricing_plan.validity_days

        # Use atomic transaction for consistency
        with transaction.atomic():
            # Create payment intent using PaymentService
            payment_service = PaymentService()
            payment_result = payment_service.create_payment_intent(
                user=student_user, pricing_plan_id=str(pricing_plan.id), metadata=purchase_metadata
            )

            if not payment_result["success"]:
                logger.error(f"Payment service failed: {payment_result}")
                return _handle_payment_service_error(payment_result)

            # Update transaction status to PENDING for purchase initiation
            transaction_id = payment_result["transaction_id"]
            purchase_transaction = PurchaseTransaction.objects.get(id=transaction_id)
            purchase_transaction.payment_status = TransactionPaymentStatus.PENDING
            purchase_transaction.save(update_fields=["payment_status", "updated_at"])

        # Prepare successful response
        plan_details = {
            "id": pricing_plan.id,
            "name": pricing_plan.name,
            "description": pricing_plan.description,
            "plan_type": pricing_plan.plan_type,
            "hours_included": str(pricing_plan.hours_included),
            "price_eur": str(pricing_plan.price_eur),
            "validity_days": pricing_plan.validity_days,
            "price_per_hour": str(pricing_plan.price_per_hour) if pricing_plan.price_per_hour else None,
        }

        response_data = {
            "success": True,
            "client_secret": payment_result["client_secret"],
            "transaction_id": payment_result["transaction_id"],
            "payment_intent_id": payment_result["payment_intent_id"],
            "plan_details": plan_details,
            "message": f"Purchase of {pricing_plan.name} initiated successfully",
        }

        logger.info(
            f"Purchase initiated successfully for user {student_user.id}, "
            f"plan {pricing_plan.id}, transaction {payment_result['transaction_id']}"
        )

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Unexpected error in purchase initiation: {e!s}", exc_info=True)
        return Response(
            {
                "success": False,
                "error_type": "internal_error",
                "message": "An unexpected error occurred while processing your purchase",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _get_or_create_student_user(authenticated_user, student_info):
    """
    Get or create a student user based on authentication status and provided info.

    For authenticated users, uses the authenticated user if email matches,
    otherwise creates/finds user by email. For unauthenticated requests,
    creates a new user or finds existing user by email.

    Args:
        authenticated_user: The authenticated user or None for guests
        student_info: Dictionary containing name and email

    Returns:
        CustomUser: The student user to use for the transaction
    """
    CustomUser = apps.get_model("accounts", "CustomUser")

    student_email = student_info["email"]
    student_name = student_info["name"]

    # If user is authenticated and email matches, use authenticated user
    if authenticated_user and authenticated_user.email.lower() == student_email.lower():
        return authenticated_user

    # Try to find existing user by email
    try:
        existing_user = CustomUser.objects.get(email__iexact=student_email)
        logger.info(f"Found existing user for email {student_email}")
        return existing_user
    except CustomUser.DoesNotExist:
        pass

    # Create new user for guest purchase
    logger.info(f"Creating new user for guest purchase: {student_email}")
    new_user = CustomUser.objects.create_user(
        email=student_email,
        name=student_name,
        password=None,  # No password for guest users
    )

    return new_user


def _handle_payment_service_error(payment_result):
    """
    Handle errors from PaymentService and return appropriate HTTP response.

    Args:
        payment_result: Result dictionary from PaymentService

    Returns:
        Response: Appropriate HTTP response for the error type
    """
    error_type = payment_result.get("error_type", "unknown_error")
    error_message = payment_result.get("message", "Payment processing failed")

    # Map payment service error types to HTTP status codes
    status_code_mapping = {
        "validation_error": status.HTTP_400_BAD_REQUEST,
        "card_error": status.HTTP_400_BAD_REQUEST,
        "invalid_request_error": status.HTTP_400_BAD_REQUEST,
        "authentication_error": status.HTTP_401_UNAUTHORIZED,
        "api_connection_error": status.HTTP_503_SERVICE_UNAVAILABLE,
        "api_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "rate_limit_error": status.HTTP_429_TOO_MANY_REQUESTS,
        "unknown_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    http_status = status_code_mapping.get(error_type, status.HTTP_500_INTERNAL_SERVER_ERROR)

    error_response = {"success": False, "error_type": error_type, "message": error_message}

    # Add additional details if available
    if "details" in payment_result:
        error_response["details"] = payment_result["details"]

    return Response(error_response, status=http_status)


class StudentBalanceViewSet(viewsets.ViewSet):
    """
    ViewSet for student account balance management.

    Provides endpoints for students to view their tutoring hour balances,
    purchase history, and consumption tracking. Supports both authenticated
    users and admin email parameter lookups with proper security validation.
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Main endpoint for student balance - delegates to summary.
        """
        return self.summary(request)

    def _get_target_student(self, request):
        """
        Get the target student based on authentication and email parameter.

        Args:
            request: The HTTP request object

        Returns:
            tuple: (student_user, error_response)
                student_user: The target student user object or None
                error_response: Error response if any, or None
        """
        CustomUser = apps.get_model("accounts", "CustomUser")
        from django.core.validators import EmailValidator

        email_param = request.query_params.get("email")

        # If no email parameter, use authenticated user
        if not email_param:
            return request.user, None

        # Validate email format
        email_validator = EmailValidator()
        try:
            email_validator(email_param)
        except Exception:
            return None, Response({"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user is admin (can access any student's data)
        if not (request.user.is_staff or request.user.is_superuser):
            return None, Response(
                {"error": "Permission denied. Only administrators can access other students' data."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Find student by email
        try:
            student_user = CustomUser.objects.get(email__iexact=email_param)
            return student_user, None
        except CustomUser.DoesNotExist:
            return None, Response(
                {"error": f"Student with email {email_param} not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def _get_or_create_student_balance(self, student_user):
        """Get or create student account balance."""
        balance, created = StudentAccountBalance.objects.get_or_create(
            student=student_user,
            defaults={
                "hours_purchased": Decimal("0.00"),
                "hours_consumed": Decimal("0.00"),
                "balance_amount": Decimal("0.00"),
            },
        )
        return balance

    def _calculate_package_status(self, student_user):
        """Calculate active and expired package status."""
        from django.utils import timezone

        # Get all completed transactions for this student with optimized queries
        transactions = (
            PurchaseTransaction.objects.filter(student=student_user, payment_status=TransactionPaymentStatus.COMPLETED)
            .prefetch_related("hour_consumptions")
            .order_by("-created_at")
        )

        # Extract plan IDs from metadata to batch fetch pricing plans
        plan_ids = []
        for transaction in transactions:
            metadata = transaction.metadata or {}
            plan_id = metadata.get("plan_id")
            if plan_id:
                plan_ids.append(plan_id)

        # Batch fetch pricing plans to avoid N+1 queries
        pricing_plans = {plan.id: plan for plan in PricingPlan.objects.filter(id__in=plan_ids)}

        active_packages = []
        expired_packages = []

        for transaction in transactions:
            # Calculate hours consumed for this specific transaction
            consumed_hours = sum(
                consumption.hours_consumed for consumption in transaction.hour_consumptions.filter(is_refunded=False)
            )

            # Get plan details from metadata or database
            metadata = transaction.metadata or {}
            plan_id = metadata.get("plan_id")
            plan_name = metadata.get("plan_name", "Unknown Plan")
            hours_included = Decimal(metadata.get("hours_included", "0"))

            if plan_id and plan_id in pricing_plans:
                plan = pricing_plans[plan_id]
                plan_name = plan.name
                hours_included = plan.hours_included

            hours_remaining = max(hours_included - consumed_hours, Decimal("0"))

            # Calculate days until expiry
            days_until_expiry = None
            if transaction.expires_at:
                delta = transaction.expires_at.date() - timezone.now().date()
                days_until_expiry = delta.days

            package_data = {
                "transaction_id": transaction.id,
                "plan_name": plan_name,
                "hours_included": hours_included,
                "hours_consumed": consumed_hours,
                "hours_remaining": hours_remaining,
                "expires_at": transaction.expires_at,
                "days_until_expiry": days_until_expiry,
                "is_expired": transaction.is_expired,
            }

            if transaction.is_expired:
                expired_packages.append(package_data)
            else:
                active_packages.append(package_data)

        return {"active_packages": active_packages, "expired_packages": expired_packages}

    def _get_upcoming_expirations(self, student_user, days_ahead=30):
        """Get packages expiring within specified days."""
        from django.utils import timezone

        cutoff_date = timezone.now() + timezone.timedelta(days=days_ahead)

        upcoming = (
            PurchaseTransaction.objects.filter(
                student=student_user,
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at__isnull=False,
                expires_at__gte=timezone.now(),
                expires_at__lte=cutoff_date,
            )
            .prefetch_related("hour_consumptions")
            .order_by("expires_at")
        )

        # Extract plan IDs from metadata to batch fetch pricing plans
        plan_ids = []
        for transaction in upcoming:
            metadata = transaction.metadata or {}
            plan_id = metadata.get("plan_id")
            if plan_id:
                plan_ids.append(plan_id)

        # Batch fetch pricing plans to avoid N+1 queries
        pricing_plans = {plan.id: plan for plan in PricingPlan.objects.filter(id__in=plan_ids)}

        result = []
        for transaction in upcoming:
            # Calculate remaining hours
            consumed_hours = sum(
                consumption.hours_consumed for consumption in transaction.hour_consumptions.filter(is_refunded=False)
            )

            metadata = transaction.metadata or {}
            plan_name = metadata.get("plan_name", "Unknown Plan")
            hours_included = Decimal(metadata.get("hours_included", "0"))

            # Try to get actual plan data
            plan_id = metadata.get("plan_id")
            if plan_id and plan_id in pricing_plans:
                plan = pricing_plans[plan_id]
                plan_name = plan.name
                hours_included = plan.hours_included

            hours_remaining = max(hours_included - consumed_hours, Decimal("0"))

            # Only include if there are hours remaining
            if hours_remaining > 0:
                delta = transaction.expires_at.date() - timezone.now().date()
                result.append(
                    {
                        "transaction_id": transaction.id,
                        "plan_name": plan_name,
                        "hours_remaining": hours_remaining,
                        "expires_at": transaction.expires_at,
                        "days_until_expiry": delta.days,
                    }
                )

        return result

    def _get_subscription_info(self, student_user):
        """Get subscription information for the student."""
        from django.utils import timezone

        # Look for active subscription transactions
        subscription_transactions = PurchaseTransaction.objects.filter(
            student=student_user,
            transaction_type=TransactionType.SUBSCRIPTION,
            payment_status=TransactionPaymentStatus.COMPLETED,
        ).order_by("-created_at")

        if not subscription_transactions.exists():
            return {
                "is_active": False,
                "next_billing_date": None,
                "billing_cycle": None,
                "subscription_status": "inactive",
                "cancel_at_period_end": False,
                "current_period_start": None,
                "current_period_end": None,
            }

        # For simplicity, take the most recent subscription
        # In a real implementation, you'd integrate with Stripe subscriptions
        latest_subscription = subscription_transactions.first()

        # Basic subscription info (in a real implementation, this would come from Stripe)
        subscription_info = {
            "is_active": True,
            "subscription_status": "active",
            "cancel_at_period_end": False,
        }

        # Calculate billing cycle information
        # This is a simplified implementation - in reality, you'd get this from Stripe
        creation_date = latest_subscription.created_at.date()
        current_date = timezone.now().date()

        # Assume monthly billing cycle
        from datetime import timedelta

        from dateutil.relativedelta import relativedelta

        months_since_creation = (current_date.year - creation_date.year) * 12 + (
            current_date.month - creation_date.month
        )

        # Calculate current period
        current_period_start = creation_date + relativedelta(months=months_since_creation)
        current_period_end = current_period_start + relativedelta(months=1) - timedelta(days=1)
        next_billing_date = current_period_end + timedelta(days=1)

        # If current date is past the current period end, adjust
        if current_date > current_period_end:
            months_since_creation += 1
            current_period_start = creation_date + relativedelta(months=months_since_creation)
            current_period_end = current_period_start + relativedelta(months=1) - timedelta(days=1)
            next_billing_date = current_period_end + timedelta(days=1)

        subscription_info.update(
            {
                "billing_cycle": "monthly",
                "next_billing_date": next_billing_date,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
            }
        )

        return subscription_info

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """
        Get student account balance summary.

        Returns comprehensive balance information including:
        - Student information
        - Balance summary (hours purchased/consumed/remaining)
        - Package status (active/expired packages)
        - Upcoming expirations
        """
        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Get or create student balance
        student_balance = self._get_or_create_student_balance(student_user)

        # Calculate package status
        package_status = self._calculate_package_status(student_user)

        # Get upcoming expirations
        upcoming_expirations = self._get_upcoming_expirations(student_user, days_ahead=7)

        # Get subscription information
        subscription_info = self._get_subscription_info(student_user)

        # Prepare response data
        response_data = {
            "student_info": {
                "id": student_user.id,
                "name": student_user.name,
                "email": student_user.email,
            },
            "balance_summary": {
                "hours_purchased": student_balance.hours_purchased,
                "hours_consumed": student_balance.hours_consumed,
                "remaining_hours": student_balance.remaining_hours,
                "balance_amount": student_balance.balance_amount,
            },
            "package_status": package_status,
            "upcoming_expirations": upcoming_expirations,
            "subscription_info": subscription_info,
        }

        serializer = EnhancedStudentBalanceSummarySerializer(response_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        """
        Get student transaction history.

        Supports filtering by:
        - payment_status: completed, pending, failed, etc.
        - transaction_type: package, subscription
        - Pagination with page and page_size parameters
        """
        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Get queryset with filters
        queryset = PurchaseTransaction.objects.filter(student=student_user).order_by("-created_at")

        # Apply filters
        payment_status = request.query_params.get("payment_status")
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        transaction_type = request.query_params.get("transaction_type")
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        # Optimize queries
        queryset = queryset.prefetch_related("hour_consumptions")

        # Paginate results
        from rest_framework.pagination import PageNumberPagination

        paginator = PageNumberPagination()
        page_size = request.query_params.get("page_size", 20)
        try:
            paginator.page_size = min(int(page_size), 100)  # Max 100 items per page
        except (ValueError, TypeError):
            paginator.page_size = 20

        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = TransactionHistorySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = TransactionHistorySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="purchases")
    def purchases(self, request):
        """
        Get student purchase history with plan details and consumption tracking.

        Supports filtering by:
        - active_only: true/false - only show non-expired packages
        - include_consumption: true/false - include detailed consumption history
        - Pagination with page and page_size parameters
        """
        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Get queryset with filters
        queryset = PurchaseTransaction.objects.filter(
            student=student_user, payment_status=TransactionPaymentStatus.COMPLETED
        ).order_by("-created_at")

        # Filter by active status
        active_only = request.query_params.get("active_only", "").lower() == "true"
        if active_only:
            from django.db import models
            from django.utils import timezone

            queryset = queryset.filter(
                models.Q(expires_at__isnull=True)  # Subscriptions
                | models.Q(expires_at__gt=timezone.now())  # Non-expired packages
            )

        # Optimize queries
        queryset = queryset.prefetch_related("hour_consumptions__class_session").select_related()

        # Paginate results
        from rest_framework.pagination import PageNumberPagination

        paginator = PageNumberPagination()
        page_size = request.query_params.get("page_size", 20)
        try:
            paginator.page_size = min(int(page_size), 100)  # Max 100 items per page
        except (ValueError, TypeError):
            paginator.page_size = 20

        page = paginator.paginate_queryset(queryset, request)

        # Prepare serializer context
        context = {"request": request}

        if page is not None:
            serializer = PurchaseHistorySerializer(page, many=True, context=context)
            return paginator.get_paginated_response(serializer.data)

        serializer = PurchaseHistorySerializer(queryset, many=True, context=context)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="check-booking")
    def check_booking(self, request):
        """
        Check if a student can book a session of given duration.

        Query parameters:
        - duration_hours: Required session duration in hours
        - session_type: Session type (individual/group) - optional
        - email: Student email (for admin access) - optional
        """
        from decimal import Decimal, InvalidOperation

        from finances.services.hour_deduction_service import HourDeductionService

        # Get target student
        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Get and validate duration_hours parameter
        duration_hours_str = request.query_params.get("duration_hours")
        if not duration_hours_str:
            return Response({"error": "duration_hours parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            duration_hours = Decimal(duration_hours_str)
            if duration_hours <= 0:
                raise ValueError("Duration must be positive")
        except (InvalidOperation, ValueError):
            return Response({"error": "duration_hours must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)

        # Check booking eligibility
        eligibility = HourDeductionService.check_booking_eligibility(student_user, duration_hours)

        return Response(eligibility)

    @action(detail=False, methods=["get"], url_path="receipts")
    def receipts(self, request):
        """
        List all receipts for the authenticated student.

        Supports filtering by:
        - is_valid: true/false - only show valid receipts
        - start_date: YYYY-MM-DD - receipts generated after this date
        - end_date: YYYY-MM-DD - receipts generated before this date
        """
        from finances.services.receipt_service import ReceiptGenerationService

        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Parse filters
        filters = {}
        if request.query_params.get("is_valid"):
            filters["is_valid"] = request.query_params.get("is_valid").lower() == "true"

        if request.query_params.get("start_date"):
            try:
                from datetime import datetime

                filters["start_date"] = datetime.strptime(request.query_params["start_date"], "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid start_date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST
                )

        if request.query_params.get("end_date"):
            try:
                from datetime import datetime

                filters["end_date"] = datetime.strptime(request.query_params["end_date"], "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid end_date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST
                )

        # Get receipts using service
        result = ReceiptGenerationService.list_student_receipts(student_user, filters)

        if result["success"]:
            return Response(result)
        else:
            return Response({"error": result["message"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="receipts/generate")
    def generate_receipt(self, request):
        """
        Generate a new receipt for a completed transaction.

        Request body:
        {
            "transaction_id": 123
        }
        """
        from finances.serializers import ReceiptGenerationRequestSerializer
        from finances.services.receipt_service import ReceiptGenerationService

        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Validate request data
        serializer = ReceiptGenerationRequestSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        transaction_id = serializer.validated_data["transaction_id"]

        # Generate receipt using service
        result = ReceiptGenerationService.generate_receipt(
            transaction_id=transaction_id, force_regenerate=request.data.get("force_regenerate", False)
        )

        if result["success"]:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            error_status_map = {
                "not_found": status.HTTP_404_NOT_FOUND,
                "invalid_status": status.HTTP_400_BAD_REQUEST,
                "generation_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

            http_status = error_status_map.get(result.get("error_type"), status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"error": result["message"]}, status=http_status)

    @action(detail=True, methods=["get"], url_path="download")
    def download_receipt(self, request, pk=None):
        """
        Get download URL for a specific receipt.

        URL: /api/student-balance/receipts/{receipt_id}/download/
        """
        from finances.services.receipt_service import ReceiptGenerationService

        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Convert string URL parameter to integer for service method
        try:
            receipt_id = int(pk)
        except (ValueError, TypeError):
            return Response({"error": "Invalid receipt ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Get download URL using service
        result = ReceiptGenerationService.get_receipt_download_url(receipt_id=receipt_id, student_user=student_user)

        if result["success"]:
            return Response(result)
        else:
            error_status_map = {
                "not_found": status.HTTP_404_NOT_FOUND,
                "permission_denied": status.HTTP_403_FORBIDDEN,
                "invalid_receipt": status.HTTP_400_BAD_REQUEST,
                "file_missing": status.HTTP_404_NOT_FOUND,
                "download_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

            http_status = error_status_map.get(result.get("error_type"), status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"error": result["message"]}, status=http_status)

    @action(detail=False, methods=["get", "post"], url_path="payment-methods")
    def payment_methods(self, request):
        """
        Handle payment method operations for authenticated student.

        GET: List all stored payment methods
        Query parameters:
        - include_expired: true/false - include expired payment methods

        POST: Add a new stored payment method using Stripe tokenization
        Request body:
        {
            "stripe_payment_method_id": "pm_1234567890",
            "is_default": false
        }
        """
        from finances.services.payment_method_service import PaymentMethodService

        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        payment_service = PaymentMethodService()

        if request.method == "GET":
            # List payment methods
            include_expired = request.query_params.get("include_expired", "false").lower() == "true"
            result = payment_service.list_payment_methods(student_user, include_expired)

            if result["success"]:
                return Response(result)
            else:
                return Response({"error": result["message"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif request.method == "POST":
            # Add payment method
            from finances.serializers import PaymentMethodCreationRequestSerializer

            # Validate request data
            serializer = PaymentMethodCreationRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            stripe_payment_method_id = serializer.validated_data["stripe_payment_method_id"]
            is_default = serializer.validated_data.get("is_default", False)

            # Add payment method using service
            result = payment_service.add_payment_method(
                student_user=student_user, stripe_payment_method_id=stripe_payment_method_id, is_default=is_default
            )

            if result["success"]:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                error_status_map = {
                    "already_exists": status.HTTP_400_BAD_REQUEST,
                    "stripe_error": status.HTTP_400_BAD_REQUEST,
                    "validation_error": status.HTTP_400_BAD_REQUEST,
                    "creation_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
                }

                http_status = error_status_map.get(result.get("error_type"), status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({"error": result["message"]}, status=http_status)

    @action(detail=True, methods=["delete"])
    def remove_payment_method(self, request, pk=None):
        """
        Remove a stored payment method.

        URL: /api/student-balance/payment-methods/{payment_method_id}/
        """
        from finances.services.payment_method_service import PaymentMethodService

        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Convert string URL parameter to integer for service method
        try:
            payment_method_id = int(pk)
        except (ValueError, TypeError):
            return Response({"error": "Invalid payment method ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Remove payment method using service
        payment_service = PaymentMethodService()
        result = payment_service.remove_payment_method(student_user=student_user, payment_method_id=payment_method_id)

        if result["success"]:
            return Response(result)
        else:
            error_status_map = {
                "not_found": status.HTTP_404_NOT_FOUND,
                "removal_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

            http_status = error_status_map.get(result.get("error_type"), status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"error": result["message"]}, status=http_status)

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default_payment_method(self, request, pk=None):
        """
        Set a payment method as the default for the student.

        URL: /api/student-balance/payment-methods/{payment_method_id}/set-default/
        """
        from finances.services.payment_method_service import PaymentMethodService

        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Convert string URL parameter to integer for service method
        try:
            payment_method_id = int(pk)
        except (ValueError, TypeError):
            return Response({"error": "Invalid payment method ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Set default payment method using service
        payment_service = PaymentMethodService()
        result = payment_service.set_default_payment_method(
            student_user=student_user, payment_method_id=payment_method_id
        )

        if result["success"]:
            return Response(result)
        else:
            error_status_map = {
                "not_found": status.HTTP_404_NOT_FOUND,
                "expired": status.HTTP_400_BAD_REQUEST,
                "update_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

            http_status = error_status_map.get(result.get("error_type"), status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"error": result["message"]}, status=http_status)

    @action(detail=False, methods=["get"], url_path="topup-packages")
    def get_topup_packages(self, request):
        """
        Get available quick top-up packages.

        Returns list of available hour packages with pricing information.
        """
        from finances.serializers import QuickTopupPackageSerializer
        from finances.services.renewal_payment_service import RenewalPaymentService

        service = RenewalPaymentService()
        packages = service.get_available_topup_packages()

        serializer = QuickTopupPackageSerializer(packages, many=True)
        return Response({"success": True, "packages": serializer.data})

    @action(detail=False, methods=["post"], url_path="renew-subscription")
    def renew_subscription(self, request):
        """
        Renew an expired subscription using saved payment method.

        Request body:
        {
            "original_transaction_id": 123,
            "payment_method_id": 456  // optional, uses default if not provided
        }
        """
        from finances.serializers import RenewalResponseSerializer, SubscriptionRenewalRequestSerializer
        from finances.services.renewal_payment_service import RenewalPaymentService

        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Validate request data
        serializer = SubscriptionRenewalRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        original_transaction_id = serializer.validated_data["original_transaction_id"]
        payment_method_id = serializer.validated_data.get("payment_method_id")

        # Additional validation for payment method ownership
        if payment_method_id:
            from finances.models import StoredPaymentMethod

            try:
                StoredPaymentMethod.objects.get(id=payment_method_id, student=student_user, is_active=True)
            except StoredPaymentMethod.DoesNotExist:
                return Response(
                    {"error": "Payment method not found or not accessible"}, status=status.HTTP_404_NOT_FOUND
                )

        # Process renewal using service
        service = RenewalPaymentService()
        result = service.renew_subscription(
            student_user=student_user,
            original_transaction_id=original_transaction_id,
            payment_method_id=payment_method_id,
        )

        # Map service result to proper HTTP status
        if result["success"]:
            response_serializer = RenewalResponseSerializer(data=result)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(result, status=status.HTTP_201_CREATED)
        else:
            error_status_map = {
                "transaction_not_found": status.HTTP_404_NOT_FOUND,
                "invalid_transaction_status": status.HTTP_400_BAD_REQUEST,
                "invalid_transaction_type": status.HTTP_400_BAD_REQUEST,
                "no_default_payment_method": status.HTTP_400_BAD_REQUEST,
                "payment_method_not_found": status.HTTP_404_NOT_FOUND,
                "payment_method_expired": status.HTTP_400_BAD_REQUEST,
                "stripe_error": status.HTTP_400_BAD_REQUEST,
                "renewal_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

            http_status = error_status_map.get(result.get("error_type"), status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"error": result["message"], "error_type": result.get("error_type")}, status=http_status)

    @action(detail=False, methods=["post"], url_path="quick-topup")
    def quick_topup(self, request):
        """
        Purchase additional hours using quick top-up packages.

        Request body:
        {
            "hours": 5.00,
            "payment_method_id": 456  // optional, uses default if not provided
        }
        """
        from finances.serializers import QuickTopupRequestSerializer, RenewalResponseSerializer
        from finances.services.renewal_payment_service import RenewalPaymentService

        student_user, error_response = self._get_target_student(request)
        if error_response:
            return error_response

        # Validate request data
        serializer = QuickTopupRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        hours = serializer.validated_data["hours"]
        payment_method_id = serializer.validated_data.get("payment_method_id")

        # Additional validation for payment method ownership
        if payment_method_id:
            from finances.models import StoredPaymentMethod

            try:
                StoredPaymentMethod.objects.get(id=payment_method_id, student=student_user, is_active=True)
            except StoredPaymentMethod.DoesNotExist:
                return Response(
                    {"error": "Payment method not found or not accessible"}, status=status.HTTP_404_NOT_FOUND
                )

        # Process quick top-up using service
        service = RenewalPaymentService()
        result = service.quick_topup(student_user=student_user, hours=hours, payment_method_id=payment_method_id)

        # Map service result to proper HTTP status
        if result["success"]:
            response_serializer = RenewalResponseSerializer(data=result)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(result, status=status.HTTP_201_CREATED)
        else:
            error_status_map = {
                "invalid_package": status.HTTP_400_BAD_REQUEST,
                "no_default_payment_method": status.HTTP_400_BAD_REQUEST,
                "payment_method_not_found": status.HTTP_404_NOT_FOUND,
                "payment_method_expired": status.HTTP_400_BAD_REQUEST,
                "stripe_error": status.HTTP_400_BAD_REQUEST,
                "topup_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

            http_status = error_status_map.get(result.get("error_type"), status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"error": result["message"], "error_type": result.get("error_type")}, status=http_status)


# =======================
# PARENT-CHILD PURCHASE APPROVAL VIEWS (Issues #111 & #112)
# =======================


class FamilyBudgetControlViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing family budget controls.

    Allows parents to set and manage spending limits and approval settings
    for their children's purchases.
    """

    # Don't define queryset attribute - force use of get_queryset() method
    serializer_class = "FamilyBudgetControlSerializer"  # Set in get_serializer_class
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter budget controls by user permissions."""
        from accounts.models import ParentChildRelationship

        from .models import FamilyBudgetControl

        user = self.request.user

        # Check if user is a parent (has children relationships)
        parent_relationships_exist = ParentChildRelationship.objects.filter(parent=user).exists()

        if parent_relationships_exist:
            # Parents can access controls for their children only
            return FamilyBudgetControl.objects.filter(parent_child_relationship__parent=user).select_related(
                "parent_child_relationship__parent",
                "parent_child_relationship__child",
                "parent_child_relationship__school",
            )
        else:
            # Children and users without parent relationships should NOT be able to access ANY budget controls
            # This is a security measure - only parents can view or modify budget settings
            return FamilyBudgetControl.objects.none()

    def list(self, request, *args, **kwargs):
        """Override list method to ensure proper queryset filtering."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        from .serializers import FamilyBudgetControlSerializer

        return FamilyBudgetControlSerializer

    def perform_create(self, serializer):
        """Ensure user has permission to create budget control."""
        relationship = serializer.validated_data["parent_child_relationship"]

        # Only parents can create budget controls
        if relationship.parent != self.request.user:
            raise PermissionError("Only parents can create budget controls for their children")

        serializer.save()

    def perform_update(self, serializer):
        """Ensure user has permission to update budget control."""
        instance = self.get_object()

        # Only parents can update budget controls
        if instance.parent_child_relationship.parent != self.request.user:
            raise PermissionError("Only parents can update budget controls for their children")

        serializer.save()

    @action(detail=True, methods=["post"])
    def check_budget_limits(self, request, pk=None):
        """
        Check if a purchase amount would exceed budget limits.

        Request body:
        {
            "amount": "50.00"
        }
        """
        budget_control = self.get_object()

        try:
            amount = Decimal(request.data.get("amount", "0"))
        except (ValueError, TypeError):
            return Response({"error": "Invalid amount provided"}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Amount must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)

        # Check budget limits
        result = budget_control.check_budget_limits(amount)

        return Response(result)


class PurchaseApprovalRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase approval requests.

    Handles the approval workflow between parents and children for purchases.
    """

    serializer_class = "PurchaseApprovalRequestSerializer"  # Set in get_serializer_class
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ["requested_at", "amount"]
    ordering = ["-requested_at"]

    def get_queryset(self):
        """Filter approval requests by user permissions and query parameters."""
        from .models import PurchaseApprovalRequest

        # Base queryset - Parents see requests they need to approve, Children see their own requests
        queryset = PurchaseApprovalRequest.objects.filter(
            Q(parent=self.request.user) | Q(student=self.request.user)
        ).select_related("student", "parent", "parent_child_relationship", "pricing_plan", "class_session")

        # Apply manual filtering for status and request_type
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        request_type_filter = self.request.query_params.get("request_type")
        if request_type_filter:
            queryset = queryset.filter(request_type=request_type_filter)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        from .serializers import PurchaseApprovalRequestSerializer

        return PurchaseApprovalRequestSerializer

    def perform_create(self, serializer):
        """Ensure user has permission to create approval request."""
        student = serializer.validated_data["student"]

        # Only students can create their own requests
        if student != self.request.user:
            raise PermissionError("You can only create approval requests for yourself")

        serializer.save()

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """
        Approve or deny a purchase request.

        Request body:
        {
            "action": "approve|deny",
            "parent_notes": "Optional notes from parent"
        }
        """
        from .serializers import PurchaseApprovalActionSerializer

        approval_request = self.get_object()

        # Only parents can approve/deny requests
        if approval_request.parent != request.user:
            return Response(
                {"error": "Only the parent can approve or deny this request"}, status=status.HTTP_403_FORBIDDEN
            )

        # Validate action data
        serializer = PurchaseApprovalActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data["action"]
        parent_notes = serializer.validated_data.get("parent_notes", "")

        try:
            if action == "approve":
                approval_request.approve(parent_notes)

                # TODO: Integrate with payment processing here
                # If approved, initiate the actual purchase transaction

                return Response(
                    {
                        "success": True,
                        "message": "Purchase request approved successfully",
                        "status": approval_request.status,
                    }
                )
            else:  # deny
                approval_request.deny(parent_notes)
                return Response(
                    {"success": True, "message": "Purchase request denied", "status": approval_request.status}
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a purchase request (student-initiated)."""
        approval_request = self.get_object()

        # Only students can cancel their own requests
        if approval_request.student != request.user:
            return Response({"error": "You can only cancel your own requests"}, status=status.HTTP_403_FORBIDDEN)

        try:
            approval_request.cancel()
            return Response(
                {
                    "success": True,
                    "message": "Purchase request cancelled successfully",
                    "status": approval_request.status,
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StudentPurchaseRequestView(APIView):
    """
    API endpoint for students to initiate purchase requests.

    Handles budget limit checking, auto-approval logic, and parent notification.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new purchase request.

        Request body:
        {
            "amount": "100.00",
            "description": "10-hour tutoring package",
            "request_type": "hours|session|subscription",
            "pricing_plan_id": 123,  // optional
            "class_session_id": 456,  // optional
            "parent_id": 789
        }
        """
        from .models import FamilyBudgetControl, PurchaseApprovalRequest
        from .serializers import StudentPurchaseRequestSerializer

        ParentChildRelationship = apps.get_model("accounts", "ParentChildRelationship")

        # Validate input data
        serializer = StudentPurchaseRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        student = request.user
        parent_id = data["parent_id"]
        amount = data["amount"]

        try:
            # Find parent-child relationship
            try:
                parent_child_relationship = ParentChildRelationship.objects.get(
                    parent_id=parent_id, child=student, is_active=True
                )
            except ParentChildRelationship.DoesNotExist:
                return Response(
                    {"error": "Invalid parent or no active relationship found"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Get budget control
            try:
                budget_control = FamilyBudgetControl.objects.get(
                    parent_child_relationship=parent_child_relationship, is_active=True
                )
            except FamilyBudgetControl.DoesNotExist:
                # No budget control means no restrictions
                budget_control = None

            # Check budget limits
            if budget_control:
                budget_check = budget_control.check_budget_limits(amount)

                if not budget_check["allowed"]:
                    return Response(
                        {
                            "success": False,
                            "error": "Budget limit exceeded",
                            "message": "; ".join(budget_check["reasons"]),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                can_auto_approve = budget_check["can_auto_approve"]
            else:
                can_auto_approve = False  # No budget control means manual approval required

            # Create approval request
            approval_request_data = {
                "student": student,
                "parent_id": parent_id,
                "parent_child_relationship": parent_child_relationship,
                "amount": amount,
                "description": data["description"],
                "request_type": data["request_type"],
            }

            # Add optional fields
            if data.get("pricing_plan_id"):
                approval_request_data["pricing_plan_id"] = data["pricing_plan_id"]
            if data.get("class_session_id"):
                approval_request_data["class_session_id"] = data["class_session_id"]

            approval_request = PurchaseApprovalRequest.objects.create(**approval_request_data)

            # Auto-approve if within threshold
            if can_auto_approve:
                approval_request.approve("Auto-approved based on budget settings")

                # TODO: Integrate with payment processing here
                # Auto-approved requests should trigger immediate payment

                return Response(
                    {
                        "success": True,
                        "auto_approved": True,
                        "approval_request_id": approval_request.id,
                        "message": "Purchase approved automatically",
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                # TODO: Send notification to parent

                return Response(
                    {
                        "success": True,
                        "auto_approved": False,
                        "approval_request_id": approval_request.id,
                        "message": "Purchase request sent to parent for approval",
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            logger.error(f"Error creating purchase request: {e!s}")
            return Response(
                {"error": "An error occurred while processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ParentApprovalDashboardView(APIView):
    """
    API endpoint for parents to view aggregated approval dashboard data.

    Provides pending requests, children spending summaries, recent transactions,
    and budget alerts in a single comprehensive response.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get comprehensive parent dashboard data.

        Returns:
        {
            "pending_requests": [...],
            "children_summary": [...],
            "recent_transactions": [...],
            "budget_alerts": [...],
            "monthly_spending_total": "250.00"
        }
        """
        from .models import FamilyBudgetControl, PurchaseApprovalRequest, PurchaseTransaction
        from .serializers import ParentDashboardSerializer

        ParentChildRelationship = apps.get_model("accounts", "ParentChildRelationship")
        from datetime import datetime

        from django.utils import timezone

        parent = request.user

        try:
            # Get all parent-child relationships
            relationships = ParentChildRelationship.objects.filter(parent=parent, is_active=True).select_related(
                "child", "school"
            )

            children = [rel.child for rel in relationships]

            if not children:
                # No children found
                empty_data = {
                    "pending_requests": [],
                    "children_summary": [],
                    "recent_transactions": [],
                    "budget_alerts": [],
                    "monthly_spending_total": Decimal("0.00"),
                }
                serializer = ParentDashboardSerializer(empty_data)
                return Response(serializer.data)

            # Get pending approval requests
            pending_requests = PurchaseApprovalRequest.objects.filter(parent=parent, status="pending").order_by(
                "-requested_at"
            )

            # Get recent transactions (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_transactions = PurchaseTransaction.objects.filter(
                student__in=children, payment_status="completed", created_at__gte=thirty_days_ago
            ).order_by("-created_at")[:10]

            # Calculate current month spending
            now = timezone.now()
            start_of_month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)

            monthly_spending = PurchaseTransaction.objects.filter(
                student__in=children, payment_status="completed", created_at__gte=start_of_month
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

            # Build children summary
            children_summary = []
            budget_alerts = []

            for child in children:
                # Get child's monthly spending
                child_monthly_spending = PurchaseTransaction.objects.filter(
                    student=child, payment_status="completed", created_at__gte=start_of_month
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

                # Get budget control
                try:
                    relationship = relationships.get(child=child)
                    budget_control = FamilyBudgetControl.objects.get(
                        parent_child_relationship=relationship, is_active=True
                    )

                    # Check for budget alerts
                    if budget_control.monthly_budget_limit:
                        usage_percent = (child_monthly_spending / budget_control.monthly_budget_limit) * 100

                        if usage_percent >= 90:
                            budget_alerts.append(
                                {
                                    "type": "budget_high",
                                    "child_name": child.name,
                                    "message": f"{child.name} has used {usage_percent:.0f}% of their monthly budget",
                                    "severity": "high" if usage_percent >= 95 else "medium",
                                }
                            )
                        elif usage_percent >= 75:
                            budget_alerts.append(
                                {
                                    "type": "budget_warning",
                                    "child_name": child.name,
                                    "message": f"{child.name} has used {usage_percent:.0f}% of their monthly budget",
                                    "severity": "low",
                                }
                            )

                    monthly_limit = budget_control.monthly_budget_limit
                    auto_approval_threshold = budget_control.auto_approval_threshold

                except FamilyBudgetControl.DoesNotExist:
                    monthly_limit = None
                    auto_approval_threshold = None

                children_summary.append(
                    {
                        "id": child.id,
                        "name": child.name,
                        "monthly_spending": child_monthly_spending,
                        "monthly_limit": monthly_limit,
                        "auto_approval_threshold": auto_approval_threshold,
                        "pending_requests_count": pending_requests.filter(student=child).count(),
                    }
                )

            # Format recent transactions
            recent_transactions_data = []
            for transaction in recent_transactions:
                recent_transactions_data.append(
                    {
                        "id": transaction.id,
                        "student_name": transaction.student.name,
                        "amount": str(transaction.amount),
                        "transaction_type": transaction.get_transaction_type_display(),
                        "created_at": transaction.created_at.isoformat(),
                    }
                )

            # Build response data
            dashboard_data = {
                "pending_requests": [
                    {
                        "id": req.id,
                        "student_name": req.student.name,
                        "amount": str(req.amount),
                        "description": req.description,
                        "request_type": req.get_request_type_display(),
                        "requested_at": req.requested_at.isoformat(),
                        "time_remaining_hours": round(req.time_remaining.total_seconds() / 3600, 1)
                        if not req.is_expired
                        else 0,
                    }
                    for req in pending_requests
                ],
                "children_summary": children_summary,
                "recent_transactions": recent_transactions_data,
                "budget_alerts": budget_alerts,
                "monthly_spending_total": monthly_spending,
            }

            serializer = ParentDashboardSerializer(dashboard_data)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error getting parent dashboard: {e!s}")
            return Response(
                {"error": "An error occurred while loading dashboard data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FamilyMetricsView(APIView):
    """
    API endpoint for family financial metrics data.

    Provides spending summaries, budget tracking, and financial insights
    for family accounts across different timeframes.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get family financial metrics for the specified timeframe.

        Query Parameters:
        - timeframe: 'week', 'month', or 'quarter' (default: 'month')

        Returns:
        {
            "timeframe": "month",
            "total_spending": "450.00",
            "budget_remaining": "550.00",
            "children_count": 2,
            "transactions_count": 15,
            "avg_session_cost": "30.00",
            "spending_by_subject": {...},
            "spending_trend": [...]
        }
        """
        try:
            timeframe = request.query_params.get("timeframe", "month")

            # Validate timeframe parameter
            if timeframe not in ["week", "month", "quarter"]:
                return Response(
                    {"error": "Invalid timeframe. Must be week, month, or quarter."}, status=status.HTTP_400_BAD_REQUEST
                )

            # For now, return mock data since the parent dashboard features are being developed
            # TODO: Implement actual family metrics calculation
            mock_data = {
                "timeframe": timeframe,
                "total_spending": "450.00",
                "budget_remaining": "550.00",
                "children_count": 2,
                "transactions_count": 15,
                "avg_session_cost": "30.00",
                "spending_by_subject": {
                    "Mathematics": "180.00",
                    "Portuguese": "120.00",
                    "Sciences": "90.00",
                    "English": "60.00",
                },
                "spending_trend": [
                    {"date": "2025-01-01", "amount": "120.00"},
                    {"date": "2025-01-15", "amount": "180.00"},
                    {"date": "2025-02-01", "amount": "150.00"},
                ],
            }

            return Response(mock_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error getting family metrics: {e!s}")
            return Response(
                {"error": "An error occurred while loading family metrics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PackageExpirationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for package expiration management endpoints.

    Provides API endpoints for:
    - Getting expired packages
    - Getting expiration analytics
    - Extending package expiration
    - Processing expired packages
    - Sending expiration notifications

    Following GitHub Issue #167: Package Expiration Management API Endpoints
    """

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Admin-only permissions for all actions."""
        from rest_framework.permissions import IsAdminUser

        return [IsAdminUser()]

    @action(detail=False, methods=["get"], url_path="expired")
    def get_expired_packages(self, request):
        """Get all expired packages."""
        import logging

        from .serializers import PurchaseHistorySerializer
        from .services.package_expiration_service import PackageExpirationService

        logger = logging.getLogger(__name__)
        student_email = request.GET.get("student_email")

        try:
            if student_email:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                try:
                    student = User.objects.get(email=student_email)
                    expired_packages = PackageExpirationService.get_expired_packages_for_student(student)
                except User.DoesNotExist:
                    return Response(
                        {"error": f"Student with email {student_email} not found"}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                expired_packages = PackageExpirationService.get_expired_packages()

            serializer = PurchaseHistorySerializer(expired_packages, many=True)

            return Response({"expired_packages": serializer.data, "count": len(expired_packages)})

        except Exception as e:
            logger.error(f"Error getting expired packages: {e!s}")
            return Response(
                {"error": "An error occurred while retrieving expired packages"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="analytics")
    def get_expiration_analytics(self, request):
        """Get expiration analytics."""
        import logging

        from .services.package_expiration_service import PackageExpirationService

        logger = logging.getLogger(__name__)

        try:
            # Create basic analytics from available methods
            expired_packages = PackageExpirationService.get_expired_packages()
            expiring_soon = PackageExpirationService.get_packages_expiring_soon(days_ahead=7)

            analytics = {
                "total_packages": PurchaseTransaction.objects.filter(
                    transaction_type=TransactionType.PACKAGE, payment_status=TransactionPaymentStatus.COMPLETED
                ).count(),
                "expired_packages": len(expired_packages),
                "expiring_soon": len(expiring_soon),
                "expired_package_ids": [p.id for p in expired_packages[:10]],  # Limit for response size
                "expiring_soon_ids": [p.id for p in expiring_soon[:10]],
            }

            return Response({"summary": analytics, "generated_at": timezone.now().isoformat()})

        except Exception as e:
            logger.error(f"Error getting expiration analytics: {e!s}")
            return Response(
                {"error": "An error occurred while generating analytics"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="extend")
    def extend_package(self, request):
        """Extend package expiration."""
        import logging

        from .models import PurchaseTransaction
        from .services.package_expiration_service import PackageExpirationService

        logger = logging.getLogger(__name__)
        package_id = request.data.get("package_id")
        if not package_id:
            return Response({"error": "package_id is required"}, status=status.HTTP_400_BAD_REQUEST)

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
                        "message": result.audit_log,
                        "new_expiry_date": result.new_expiry.isoformat() if result.new_expiry else None,
                    }
                )
            else:
                return Response(
                    {"error": result.error_message or "Extension failed"}, status=status.HTTP_400_BAD_REQUEST
                )

        except PurchaseTransaction.DoesNotExist:
            return Response({"error": f"Package with ID {package_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error extending package {package_id}: {e!s}")
            return Response(
                {"error": "An error occurred while extending the package"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="process-expired")
    def process_expired_packages(self, request):
        """Process expired packages."""
        import logging

        from .services.package_expiration_service import PackageExpirationService

        logger = logging.getLogger(__name__)
        grace_hours = int(request.data.get("grace_hours", 24))
        student_email = request.data.get("student_email")

        try:
            if student_email:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                try:
                    student = User.objects.get(email=student_email)
                    expired_packages = PackageExpirationService.get_expired_packages_for_student(student)
                    results = []
                    for package in expired_packages:
                        result = PackageExpirationService.process_expired_package(package)
                        results.append(result)
                    processed_count = len([r for r in results if r.success])
                except User.DoesNotExist:
                    return Response(
                        {"error": f"Student with email {student_email} not found"}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                results = PackageExpirationService.process_bulk_expiration(grace_hours=grace_hours)
                processed_count = len([r for r in results if r.success])

            return Response(
                {
                    "processed_count": processed_count,
                    "success": True,
                    "message": f"Successfully processed {processed_count} expired packages",
                }
            )

        except Exception as e:
            logger.error(f"Error processing expired packages: {e!s}")
            return Response(
                {"error": "An error occurred while processing expired packages"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="send-notifications")
    def send_expiration_notifications(self, request):
        """Send expiration notifications."""
        import logging

        from .services.package_expiration_service import PackageExpirationService

        logger = logging.getLogger(__name__)
        days_ahead = int(request.data.get("days_ahead", 7))
        student_email = request.data.get("student_email")

        try:
            if student_email:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                try:
                    student = User.objects.get(email=student_email)
                    packages = PackageExpirationService.get_packages_expiring_soon(days_ahead=days_ahead)
                    student_packages = [p for p in packages if p.student == student]
                    notifications_sent = 0
                    for package in student_packages:
                        result = PackageExpirationService.send_expiration_warning(
                            package=package, days_until_expiry=days_ahead
                        )
                        if result.success:
                            notifications_sent += 1
                except User.DoesNotExist:
                    return Response(
                        {"error": f"Student with email {student_email} not found"}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                packages = PackageExpirationService.get_packages_expiring_soon(days_ahead=days_ahead)
                results = PackageExpirationService.send_batch_expiration_warnings(
                    packages=packages, days_until_expiry=days_ahead
                )
                notifications_sent = len([r for r in results if r.success])

            return Response(
                {
                    "notifications_sent": notifications_sent,
                    "success": True,
                    "message": f"Successfully sent {notifications_sent} expiration notifications",
                }
            )

        except Exception as e:
            logger.error(f"Error sending expiration notifications: {e!s}")
            return Response(
                {"error": "An error occurred while sending notifications"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
