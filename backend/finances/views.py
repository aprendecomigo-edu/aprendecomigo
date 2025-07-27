"""
API views for the finances app.
"""

import json
import logging
from decimal import Decimal

from accounts.models import School, TeacherProfile
from accounts.permissions import SchoolPermissionMixin
from django.core.cache import cache
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from common.throttles import PurchaseInitiationThrottle, PurchaseInitiationEmailThrottle

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
)
from .serializers import (
    BulkPaymentProcessorSerializer,
    ClassSessionSerializer,
    MonthlyPaymentSummarySerializer,
    PaymentCalculationSerializer,
    PricingPlanSerializer,
    PurchaseInitiationRequestSerializer,
    PurchaseInitiationResponseSerializer,
    PurchaseInitiationErrorSerializer,
    SchoolBillingSettingsSerializer,
    TeacherCompensationRuleSerializer,
    TeacherPaymentEntrySerializer,
)
from .services import BulkPaymentProcessor, TeacherPaymentCalculator
from .services.stripe_base import StripeService
from .services.payment_service import PaymentService


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
            return Response(
                {"error": "teacher_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

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
                raise PermissionError(
                    "You don't have permission to create sessions for this school"
                )

        serializer.save()

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
            return Response(
                {"error": f"Error calculating payment: {e!s}"}, status=status.HTTP_400_BAD_REQUEST
            )

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

        return queryset.select_related(
            "teacher__user", "school", "session", "compensation_rule"
        ).order_by("-created_at")

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
            pending_amount = payment_entries.filter(payment_status="pending").aggregate(
                total=Sum("amount_earned")
            )["total"] or Decimal("0.00")
            calculated_amount = payment_entries.filter(payment_status="calculated").aggregate(
                total=Sum("amount_earned")
            )["total"] or Decimal("0.00")
            paid_amount = payment_entries.filter(payment_status="paid").aggregate(
                total=Sum("amount_earned")
            )["total"] or Decimal("0.00")

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
                TeacherPaymentEntry.objects.filter(
                    teacher=teacher, school=school, billing_period=billing_period
                )
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


@api_view(['GET'])
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
    cache_key = 'active_pricing_plans'
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
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            logger.warning("Webhook request missing Stripe signature header")
            return HttpResponse("Missing signature", status=400)
        
        if not payload:
            logger.warning("Webhook request missing payload")
            return HttpResponse("Missing payload", status=400)
        
        # Initialize Stripe service and verify webhook signature
        stripe_service = StripeService()
        result = stripe_service.construct_webhook_event(
            payload.decode('utf-8'), 
            sig_header
        )
        
        if not result['success']:
            logger.error(f"Webhook signature verification failed: {result.get('message', 'Unknown error')}")
            return HttpResponse("Invalid signature", status=400)
        
        event = result['event']
        event_type = event.get('type')
        webhook_id = event.get('id')
        
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
            f"Unexpected error in Stripe webhook handler for event {event_type} "
            f"(ID: {webhook_id}): {str(e)}", 
            exc_info=True
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
            'payment_intent.succeeded': _handle_payment_intent_succeeded,
            'payment_intent.payment_failed': _handle_payment_intent_failed,
            'payment_intent.canceled': _handle_payment_intent_canceled,
        }
        
        handler = event_handlers.get(event_type)
        if handler:
            return handler(event, webhook_id)
        else:
            # For supported but not yet implemented event types
            logger.info(f"Event type {event_type} is supported but handler not implemented (ID: {webhook_id})")
            return True
            
    except Exception as e:
        logger.error(f"Error processing {event_type} event (ID: {webhook_id}): {str(e)}", exc_info=True)
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
    payment_intent = event['data']['object']
    payment_intent_id = payment_intent['id']
    
    logger.info(f"Processing successful payment intent: {payment_intent_id} (Webhook ID: {webhook_id})")
    
    try:
        # Check if this payment intent has already been processed (idempotent check)
        try:
            from .models import PurchaseTransaction, TransactionPaymentStatus
            existing_transaction = PurchaseTransaction.objects.get(
                stripe_payment_intent_id=payment_intent_id
            )
            if existing_transaction.payment_status == TransactionPaymentStatus.COMPLETED:
                logger.info(
                    f"Payment intent {payment_intent_id} already completed, "
                    f"skipping processing (idempotent) (Webhook ID: {webhook_id})"
                )
                return True
        except PurchaseTransaction.DoesNotExist:
            logger.error(
                f"No transaction found for payment intent {payment_intent_id} "
                f"(Webhook ID: {webhook_id})"
            )
            return False
        
        # Use PaymentService to confirm payment completion
        payment_service = PaymentService()
        result = payment_service.confirm_payment_completion(payment_intent_id)
        
        if result['success']:
            logger.info(
                f"Successfully processed payment completion for transaction "
                f"{result.get('transaction_id')} (Webhook ID: {webhook_id})"
            )
            return True
        else:
            # Handle the case where payment is already completed (idempotent)
            if result.get('error_type') == 'invalid_transaction_state':
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
            f"Unexpected error handling payment success for {payment_intent_id}: "
            f"{str(e)} (Webhook ID: {webhook_id})", 
            exc_info=True
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
    payment_intent = event['data']['object']
    payment_intent_id = payment_intent['id']
    
    # Extract error message from payment intent
    error_message = "Payment failed"
    if 'last_payment_error' in payment_intent and payment_intent['last_payment_error']:
        error_message = payment_intent['last_payment_error'].get('message', error_message)
    
    logger.info(
        f"Processing failed payment intent: {payment_intent_id} "
        f"with error: {error_message} (Webhook ID: {webhook_id})"
    )
    
    try:
        # Check if this payment intent has already been processed (idempotent check)
        try:
            from .models import PurchaseTransaction, TransactionPaymentStatus
            existing_transaction = PurchaseTransaction.objects.get(
                stripe_payment_intent_id=payment_intent_id
            )
            if existing_transaction.payment_status == TransactionPaymentStatus.FAILED:
                logger.info(
                    f"Payment intent {payment_intent_id} already marked as failed, "
                    f"skipping processing (idempotent) (Webhook ID: {webhook_id})"
                )
                return True
        except PurchaseTransaction.DoesNotExist:
            logger.error(
                f"No transaction found for payment intent {payment_intent_id} "
                f"(Webhook ID: {webhook_id})"
            )
            return False
        
        # Use PaymentService to handle payment failure
        payment_service = PaymentService()
        result = payment_service.handle_payment_failure(payment_intent_id, error_message)
        
        if result['success']:
            logger.info(
                f"Successfully processed payment failure for transaction "
                f"{result.get('transaction_id')} (Webhook ID: {webhook_id})"
            )
            return True
        else:
            # Handle the case where payment is already failed (idempotent)
            if result.get('error_type') == 'invalid_transaction_state':
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
            f"Unexpected error handling payment failure for {payment_intent_id}: "
            f"{str(e)} (Webhook ID: {webhook_id})", 
            exc_info=True
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
    payment_intent = event['data']['object']
    payment_intent_id = payment_intent['id']
    
    logger.info(f"Processing canceled payment intent: {payment_intent_id} (Webhook ID: {webhook_id})")
    
    try:
        # Check if this payment intent has already been processed (idempotent check)
        try:
            from .models import PurchaseTransaction, TransactionPaymentStatus
            existing_transaction = PurchaseTransaction.objects.get(
                stripe_payment_intent_id=payment_intent_id
            )
            if existing_transaction.payment_status in [
                TransactionPaymentStatus.FAILED, 
                TransactionPaymentStatus.CANCELLED
            ]:
                logger.info(
                    f"Payment intent {payment_intent_id} already marked as failed/cancelled, "
                    f"skipping processing (idempotent) (Webhook ID: {webhook_id})"
                )
                return True
        except PurchaseTransaction.DoesNotExist:
            logger.error(
                f"No transaction found for payment intent {payment_intent_id} "
                f"(Webhook ID: {webhook_id})"
            )
            return False
        
        # Handle cancellation as a payment failure
        payment_service = PaymentService()
        result = payment_service.handle_payment_failure(
            payment_intent_id, 
            "Payment was canceled"
        )
        
        if result['success']:
            logger.info(
                f"Successfully processed payment cancellation for transaction "
                f"{result.get('transaction_id')} (Webhook ID: {webhook_id})"
            )
            return True
        else:
            # Handle the case where payment is already failed/cancelled (idempotent)
            if result.get('error_type') == 'invalid_transaction_state':
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
            f"Unexpected error handling payment cancellation for {payment_intent_id}: "
            f"{str(e)} (Webhook ID: {webhook_id})", 
            exc_info=True
        )
        return False


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stripe_config(request):
    """
    Get Stripe configuration for frontend use.
    
    Returns the public key and other safe configuration needed
    by the frontend to initialize Stripe.
    """
    try:
        stripe_service = StripeService()
        
        config_data = {
            'public_key': stripe_service.get_public_key(),
            'success': True
        }
        
        return Response(config_data)
        
    except Exception as e:
        logger.error(f"Error getting Stripe configuration: {e}")
        return Response(
            {
                'success': False,
                'error': 'Unable to load payment configuration'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
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
        
        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Error testing Stripe connection: {e}")
        return Response(
            {
                'success': False,
                'error': 'Unable to test payment service connection'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
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
                    'success': False,
                    'error_type': 'validation_error',
                    'message': error_message,
                    'field_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        plan_id = validated_data['plan_id']
        student_info = validated_data['student_info']
        
        # Get the pricing plan
        try:
            pricing_plan = PricingPlan.objects.get(id=plan_id, is_active=True)
        except PricingPlan.DoesNotExist:
            logger.error(f"Pricing plan {plan_id} not found or inactive")
            return Response(
                {
                    'success': False,
                    'error_type': 'validation_error',
                    'message': f'Pricing plan with ID {plan_id} not found or inactive'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine the student user
        student_user = _get_or_create_student_user(
            request.user if request.user.is_authenticated else None,
            student_info
        )
        
        # Ensure student has an account balance record
        student_balance, created = StudentAccountBalance.objects.get_or_create(
            student=student_user,
            defaults={
                'hours_purchased': Decimal('0.00'),
                'hours_consumed': Decimal('0.00'),
                'balance_amount': Decimal('0.00')
            }
        )
        
        if created:
            logger.info(f"Created new student account balance for user {student_user.id}")
        
        # Prepare metadata for Stripe and transaction
        purchase_metadata = {
            'plan_id': pricing_plan.id,
            'plan_name': pricing_plan.name,
            'plan_type': pricing_plan.plan_type,
            'hours_included': str(pricing_plan.hours_included),
            'price_eur': str(pricing_plan.price_eur),
            'student_name': student_user.name,
            'student_email': student_user.email,
            'amount': str(pricing_plan.price_eur)
        }
        
        # Add subscription indicator for proper type detection
        if pricing_plan.plan_type == PlanType.SUBSCRIPTION:
            purchase_metadata['subscription_name'] = pricing_plan.name
        
        # Add validity information for packages
        if pricing_plan.plan_type == PlanType.PACKAGE and pricing_plan.validity_days:
            purchase_metadata['validity_days'] = pricing_plan.validity_days
        
        # Use atomic transaction for consistency
        with transaction.atomic():
            # Create payment intent using PaymentService
            payment_service = PaymentService()
            payment_result = payment_service.create_payment_intent(
                user=student_user,
                pricing_plan_id=str(pricing_plan.id),
                metadata=purchase_metadata
            )
            
            if not payment_result['success']:
                logger.error(f"Payment service failed: {payment_result}")
                return _handle_payment_service_error(payment_result)
            
            # Update transaction status to PENDING for purchase initiation
            transaction_id = payment_result['transaction_id']
            purchase_transaction = PurchaseTransaction.objects.get(id=transaction_id)
            purchase_transaction.payment_status = TransactionPaymentStatus.PENDING
            purchase_transaction.save(update_fields=['payment_status', 'updated_at'])
        
        # Prepare successful response
        plan_details = {
            'id': pricing_plan.id,
            'name': pricing_plan.name,
            'description': pricing_plan.description,
            'plan_type': pricing_plan.plan_type,
            'hours_included': str(pricing_plan.hours_included),
            'price_eur': str(pricing_plan.price_eur),
            'validity_days': pricing_plan.validity_days,
            'price_per_hour': str(pricing_plan.price_per_hour) if pricing_plan.price_per_hour else None
        }
        
        response_data = {
            'success': True,
            'client_secret': payment_result['client_secret'],
            'transaction_id': payment_result['transaction_id'],
            'payment_intent_id': payment_result['payment_intent_id'],
            'plan_details': plan_details,
            'message': f'Purchase of {pricing_plan.name} initiated successfully'
        }
        
        logger.info(
            f"Purchase initiated successfully for user {student_user.id}, "
            f"plan {pricing_plan.id}, transaction {payment_result['transaction_id']}"
        )
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Unexpected error in purchase initiation: {str(e)}", exc_info=True)
        return Response(
            {
                'success': False,
                'error_type': 'internal_error',
                'message': 'An unexpected error occurred while processing your purchase'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
    from accounts.models import CustomUser
    
    student_email = student_info['email']
    student_name = student_info['name']
    
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
        password=None  # No password for guest users
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
    error_type = payment_result.get('error_type', 'unknown_error')
    error_message = payment_result.get('message', 'Payment processing failed')
    
    # Map payment service error types to HTTP status codes
    status_code_mapping = {
        'validation_error': status.HTTP_400_BAD_REQUEST,
        'card_error': status.HTTP_400_BAD_REQUEST,
        'invalid_request_error': status.HTTP_400_BAD_REQUEST,
        'authentication_error': status.HTTP_401_UNAUTHORIZED,
        'api_connection_error': status.HTTP_503_SERVICE_UNAVAILABLE,
        'api_error': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'rate_limit_error': status.HTTP_429_TOO_MANY_REQUESTS,
        'unknown_error': status.HTTP_500_INTERNAL_SERVER_ERROR
    }
    
    http_status = status_code_mapping.get(error_type, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    error_response = {
        'success': False,
        'error_type': error_type,
        'message': error_message
    }
    
    # Add additional details if available
    if 'details' in payment_result:
        error_response['details'] = payment_result['details']
    
    return Response(error_response, status=http_status)
