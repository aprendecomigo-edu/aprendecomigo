"""
API views for the finances app.
"""

import json
import logging
from decimal import Decimal

from accounts.models import School, TeacherProfile
from accounts.permissions import SchoolPermissionMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    ClassSession,
    SchoolBillingSettings,
    TeacherCompensationRule,
    TeacherPaymentEntry,
)
from .serializers import (
    BulkPaymentProcessorSerializer,
    ClassSessionSerializer,
    MonthlyPaymentSummarySerializer,
    PaymentCalculationSerializer,
    SchoolBillingSettingsSerializer,
    TeacherCompensationRuleSerializer,
    TeacherPaymentEntrySerializer,
)
from .services import BulkPaymentProcessor, TeacherPaymentCalculator
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


# Initialize logger for webhook handling
logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    
    This endpoint receives webhook events from Stripe and processes them
    according to the platform's business logic. The endpoint verifies
    the webhook signature and handles supported event types.
    """
    try:
        # Get the request body and Stripe signature
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            logger.warning("Missing Stripe signature header in webhook request")
            return HttpResponse("Missing signature", status=400)
        
        # Initialize Stripe service and construct event
        stripe_service = StripeService()
        result = stripe_service.construct_webhook_event(
            payload.decode('utf-8'), 
            sig_header
        )
        
        if not result['success']:
            logger.error(f"Webhook signature verification failed: {result['message']}")
            return HttpResponse("Invalid signature", status=400)
        
        event = result['event']
        event_type = event['type']
        
        # Check if event type is supported
        if not stripe_service.is_webhook_event_type_supported(event_type):
            logger.info(f"Unsupported webhook event type: {event_type}")
            return HttpResponse("Event type not supported", status=200)
        
        # Process the event based on type
        success = _process_webhook_event(event, event_type)
        
        if success:
            logger.info(f"Successfully processed webhook event: {event_type} ({event['id']})")
            return HttpResponse("Webhook processed successfully", status=200)
        else:
            logger.error(f"Failed to process webhook event: {event_type} ({event['id']})")
            return HttpResponse("Webhook processing failed", status=500)
            
    except Exception as e:
        logger.error(f"Unexpected error in Stripe webhook handler: {e}")
        return HttpResponse("Internal server error", status=500)


def _process_webhook_event(event, event_type):
    """
    Process individual webhook events based on their type.
    
    Args:
        event: The Stripe event object
        event_type: The type of the event
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        if event_type == 'payment_intent.succeeded':
            return _handle_payment_intent_succeeded(event)
        elif event_type == 'payment_intent.payment_failed':
            return _handle_payment_intent_failed(event)
        elif event_type in ['customer.created', 'customer.updated']:
            return _handle_customer_event(event, event_type)
        elif event_type in ['invoice.payment_succeeded', 'invoice.payment_failed']:
            return _handle_invoice_event(event, event_type)
        else:
            # For supported but not yet implemented event types
            logger.info(f"Event type {event_type} is supported but not yet implemented")
            return True
            
    except Exception as e:
        logger.error(f"Error processing {event_type} event: {e}")
        return False


def _handle_payment_intent_succeeded(event):
    """
    Handle successful payment intent events.
    
    Args:
        event: The Stripe event object
        
    Returns:
        bool: True if processing was successful
    """
    payment_intent = event['data']['object']
    payment_intent_id = payment_intent['id']
    
    logger.info(f"Processing successful payment intent: {payment_intent_id}")
    
    # TODO: Implement payment intent success logic
    # This would typically involve:
    # 1. Finding the associated PurchaseTransaction
    # 2. Updating the transaction status to 'completed'
    # 3. Adding hours to student account balance
    # 4. Sending confirmation notifications
    
    return True


def _handle_payment_intent_failed(event):
    """
    Handle failed payment intent events.
    
    Args:
        event: The Stripe event object
        
    Returns:
        bool: True if processing was successful
    """
    payment_intent = event['data']['object']
    payment_intent_id = payment_intent['id']
    
    logger.info(f"Processing failed payment intent: {payment_intent_id}")
    
    # TODO: Implement payment intent failure logic
    # This would typically involve:
    # 1. Finding the associated PurchaseTransaction
    # 2. Updating the transaction status to 'failed'
    # 3. Sending failure notifications
    # 4. Potentially retrying or handling recovery
    
    return True


def _handle_customer_event(event, event_type):
    """
    Handle customer-related events.
    
    Args:
        event: The Stripe event object
        event_type: The specific event type
        
    Returns:
        bool: True if processing was successful
    """
    customer = event['data']['object']
    customer_id = customer['id']
    
    logger.info(f"Processing customer event: {event_type} for {customer_id}")
    
    # TODO: Implement customer event logic
    # This would typically involve:
    # 1. Syncing customer data with local user records
    # 2. Updating customer information
    # 3. Handling customer deletions
    
    return True


def _handle_invoice_event(event, event_type):
    """
    Handle invoice-related events.
    
    Args:
        event: The Stripe event object
        event_type: The specific event type
        
    Returns:
        bool: True if processing was successful
    """
    invoice = event['data']['object']
    invoice_id = invoice['id']
    
    logger.info(f"Processing invoice event: {event_type} for {invoice_id}")
    
    # TODO: Implement invoice event logic
    # This would typically involve:
    # 1. Processing subscription renewals
    # 2. Handling invoice payment failures
    # 3. Managing subscription lifecycle
    
    return True


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
