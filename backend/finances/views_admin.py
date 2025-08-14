"""
Administrative payment monitoring API views.

This module provides API endpoints for payment system monitoring and management
including analytics dashboard, transaction history, and webhook monitoring.
"""

import logging

from django.db.models import Q
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from finances.models import PurchaseTransaction, WebhookEventLog
from finances.serializers_admin import (
    AdminTransactionSerializer,
    AdminWebhookEventSerializer,
    PaymentMetricsQuerySerializer,
    PaymentMetricsSerializer,
    TransactionHistoryQuerySerializer,
    WebhookStatusQuerySerializer,
    WebhookStatusResponseSerializer,
)
from finances.services.payment_analytics_service import PaymentAnalyticsService

logger = logging.getLogger(__name__)


class AdminOnlyPermission(permissions.BasePermission):
    """Permission class that only allows access to superuser admins."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class AdminPagination(PageNumberPagination):
    """Custom pagination for admin endpoints."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


@swagger_auto_schema(
    method="get",
    operation_description="Get comprehensive payment metrics for administrative dashboard",
    query_serializer=PaymentMetricsQuerySerializer,
    responses={
        200: PaymentMetricsSerializer,
        400: "Invalid query parameters",
        401: "Authentication required",
        403: "Admin access required",
    },
    tags=["Admin Payment Analytics"],
)
@api_view(["GET"])
@permission_classes([AdminOnlyPermission])
def payment_metrics(request: Request) -> Response:
    """
    Get comprehensive payment metrics for administrative dashboard.

    This endpoint provides detailed analytics including:
    - Payment success rates and trends
    - Revenue analysis and breakdowns
    - Transaction value metrics
    - Webhook processing status
    - Failure analysis and patterns

    Supports time-based filtering to analyze specific periods.
    """
    try:
        # Validate query parameters
        query_serializer = PaymentMetricsQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response(
                {"error": "Invalid query parameters", "details": query_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = query_serializer.validated_data
        hours = validated_data.get("hours")
        days = validated_data.get("days")

        # Get analytics service and generate metrics
        analytics_service = PaymentAnalyticsService()
        metrics = analytics_service.get_dashboard_metrics(hours=hours, days=days)

        # Serialize response
        serializer = PaymentMetricsSerializer(metrics)

        logger.info(f"Payment metrics requested by admin {request.user.email}")

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error generating payment metrics: {e!s}", exc_info=True)
        return Response(
            {"error": "Internal server error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TransactionHistoryView(ListAPIView):
    """
    API view for administrative transaction history with search and filtering.
    """

    serializer_class = AdminTransactionSerializer
    permission_classes = [AdminOnlyPermission]
    pagination_class = AdminPagination

    def get_queryset(self):
        """Get filtered and searched transaction queryset."""
        queryset = PurchaseTransaction.objects.select_related("student").order_by("-created_at")

        # Apply filters from query parameters
        payment_status = self.request.query_params.get("payment_status")
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        transaction_type = self.request.query_params.get("transaction_type")
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        student_id = self.request.query_params.get("student")
        if student_id:
            try:
                queryset = queryset.filter(student_id=int(student_id))
            except (ValueError, TypeError):
                # Invalid student ID, return empty queryset
                return queryset.none()

        # Date range filtering
        date_from = self.request.query_params.get("date_from")
        if date_from:
            try:
                from django.utils.dateparse import parse_datetime

                parsed_date = parse_datetime(date_from)
                if parsed_date:
                    queryset = queryset.filter(created_at__gte=parsed_date)
            except ValueError:
                pass

        date_to = self.request.query_params.get("date_to")
        if date_to:
            try:
                from django.utils.dateparse import parse_datetime

                parsed_date = parse_datetime(date_to)
                if parsed_date:
                    queryset = queryset.filter(created_at__lte=parsed_date)
            except ValueError:
                pass

        # Search functionality
        search_term = self.request.query_params.get("search")
        if search_term:
            queryset = queryset.filter(
                Q(stripe_payment_intent_id__icontains=search_term)
                | Q(student__name__icontains=search_term)
                | Q(student__email__icontains=search_term)
            )

        # Ordering
        ordering = self.request.query_params.get("ordering", "-created_at")
        valid_orderings = [
            "created_at",
            "-created_at",
            "amount",
            "-amount",
            "payment_status",
            "-payment_status",
            "transaction_type",
            "-transaction_type",
            "updated_at",
            "-updated_at",
        ]

        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)

        return queryset

    @swagger_auto_schema(
        operation_description="Get paginated transaction history with search and filtering",
        query_serializer=TransactionHistoryQuerySerializer,
        responses={
            200: AdminTransactionSerializer(many=True),
            401: "Authentication required",
            403: "Admin access required",
        },
        tags=["Admin Payment Analytics"],
    )
    def get(self, request, *args, **kwargs):
        """Get transaction history with filtering and search."""
        logger.info(f"Transaction history requested by admin {request.user.email}")
        return super().get(request, *args, **kwargs)


class WebhookStatusView(ListAPIView):
    """
    API view for webhook processing status monitoring.
    """

    serializer_class = AdminWebhookEventSerializer
    permission_classes = [AdminOnlyPermission]
    pagination_class = AdminPagination

    def get_queryset(self):
        """Get filtered webhook event queryset."""
        queryset = WebhookEventLog.objects.order_by("-created_at")

        # Apply filters from query parameters
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type__icontains=event_type)

        # Date range filtering
        date_from = self.request.query_params.get("date_from")
        if date_from:
            try:
                from django.utils.dateparse import parse_datetime

                parsed_date = parse_datetime(date_from)
                if parsed_date:
                    queryset = queryset.filter(created_at__gte=parsed_date)
            except ValueError:
                pass

        date_to = self.request.query_params.get("date_to")
        if date_to:
            try:
                from django.utils.dateparse import parse_datetime

                parsed_date = parse_datetime(date_to)
                if parsed_date:
                    queryset = queryset.filter(created_at__lte=parsed_date)
            except ValueError:
                pass

        # Search functionality
        search_term = self.request.query_params.get("search")
        if search_term:
            queryset = queryset.filter(Q(stripe_event_id__icontains=search_term) | Q(event_type__icontains=search_term))

        # Ordering
        ordering = self.request.query_params.get("ordering", "-created_at")
        valid_orderings = [
            "created_at",
            "-created_at",
            "processed_at",
            "-processed_at",
            "status",
            "-status",
            "event_type",
            "-event_type",
            "retry_count",
            "-retry_count",
        ]

        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)

        return queryset

    def list(self, request, *args, **kwargs):
        """Get webhook status with summary statistics."""
        # Get paginated queryset response
        response = super().list(request, *args, **kwargs)

        # Add summary statistics
        analytics_service = PaymentAnalyticsService()
        webhook_metrics = analytics_service.get_webhook_metrics()
        processing_metrics = analytics_service.get_webhook_processing_metrics()

        # Combine metrics for summary
        summary = {**webhook_metrics, "average_processing_time": processing_metrics.get("average_processing_time", 0.0)}

        # Add summary to response
        response.data["summary"] = summary

        return response

    @swagger_auto_schema(
        operation_description="Get webhook processing status with monitoring data",
        query_serializer=WebhookStatusQuerySerializer,
        responses={200: WebhookStatusResponseSerializer, 401: "Authentication required", 403: "Admin access required"},
        tags=["Admin Payment Analytics"],
    )
    def get(self, request, *args, **kwargs):
        """Get webhook status with filtering and search."""
        logger.info(f"Webhook status requested by admin {request.user.email}")
        return self.list(request, *args, **kwargs)


@swagger_auto_schema(
    method="get",
    operation_description="Get analytics for a specific student",
    manual_parameters=[
        openapi.Parameter(
            "student_id",
            openapi.IN_PATH,
            description="ID of the student to analyze",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "days",
            openapi.IN_QUERY,
            description="Number of days to analyze (default: 30)",
            type=openapi.TYPE_INTEGER,
            default=30,
        ),
    ],
    responses={
        200: "Student analytics data",
        400: "Invalid parameters",
        401: "Authentication required",
        403: "Admin access required",
        404: "Student not found",
    },
    tags=["Admin Payment Analytics"],
)
@api_view(["GET"])
@permission_classes([AdminOnlyPermission])
def student_analytics(request: Request, student_id: int) -> Response:
    """
    Get payment analytics for a specific student.

    Provides detailed payment history and metrics for individual student accounts
    including transaction history, success rates, and account balance information.
    """
    try:
        # Validate student exists
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            student = User.objects.get(id=student_id)
        except User.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get analysis period
        days = request.query_params.get("days", 30)
        try:
            days = int(days)
            if days <= 0 or days > 365:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid days parameter. Must be between 1 and 365."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get analytics
        analytics_service = PaymentAnalyticsService()
        student_data = analytics_service.get_student_analytics(student_id, days)

        logger.info(f"Student analytics for {student_id} requested by admin {request.user.email}")

        return Response(student_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error generating student analytics: {e!s}", exc_info=True)
        return Response(
            {"error": "Internal server error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get system health check for payment monitoring",
    responses={200: "System health status", 401: "Authentication required", 403: "Admin access required"},
    tags=["Admin Payment Analytics"],
)
@api_view(["GET"])
@permission_classes([AdminOnlyPermission])
def system_health(request: Request) -> Response:
    """
    Get system health check for payment monitoring.

    Provides system status including database connectivity, recent activity,
    and potential issues that require administrative attention.
    """
    try:
        health_data = {"status": "healthy", "timestamp": timezone.now(), "checks": {}}

        # Check database connectivity
        try:
            transaction_count = PurchaseTransaction.objects.count()
            webhook_count = WebhookEventLog.objects.count()

            health_data["checks"]["database"] = {
                "status": "ok",
                "transaction_count": transaction_count,
                "webhook_count": webhook_count,
            }
        except Exception as e:
            health_data["checks"]["database"] = {"status": "error", "error": str(e)}
            health_data["status"] = "degraded"

        # Check recent webhook failures
        try:
            from datetime import timedelta

            recent_time = timezone.now() - timedelta(hours=1)

            failed_webhooks = WebhookEventLog.objects.filter(created_at__gte=recent_time, status="failed").count()

            health_data["checks"]["webhooks"] = {
                "status": "ok" if failed_webhooks < 5 else "warning",
                "recent_failures": failed_webhooks,
            }

            if failed_webhooks >= 5:
                health_data["status"] = "degraded"

        except Exception as e:
            health_data["checks"]["webhooks"] = {"status": "error", "error": str(e)}

        # Check analytics service
        try:
            analytics_service = PaymentAnalyticsService()
            metrics = analytics_service.get_success_rate_metrics()

            health_data["checks"]["analytics"] = {
                "status": "ok",
                "last_24h_transactions": metrics.get("total_transactions", 0),
            }
        except Exception as e:
            health_data["checks"]["analytics"] = {"status": "error", "error": str(e)}
            health_data["status"] = "degraded"

        logger.info(f"System health check requested by admin {request.user.email}")

        return Response(health_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in system health check: {e!s}", exc_info=True)
        return Response(
            {"status": "error", "timestamp": timezone.now(), "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
