"""
Django views for the finances app (PWA conversion from DRF).
"""

from decimal import Decimal
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, TemplateView, UpdateView, View

from accounts.permissions import SchoolPermissionMixin

from .models import (
    PricingPlan,
    PurchaseTransaction,
    SchoolBillingSettings,
    StudentAccountBalance,
    TeacherCompensationRule,
    TeacherPaymentEntry,
    TransactionPaymentStatus,
)
from .services.payment_service import PaymentService
from .services.stripe_base import StripeService

logger = logging.getLogger(__name__)


# =============================================================================
# Payment Processing Views
# =============================================================================


class PaymentFormView(LoginRequiredMixin, TemplateView):
    """Display payment form with Stripe Elements."""

    template_name = "finances/payments/payment_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pricing_plans = PricingPlan.objects.filter(is_active=True)

        # Get Stripe public key for Elements
        try:
            stripe_service = StripeService()
            context["stripe_public_key"] = stripe_service.get_public_key()
        except Exception as e:
            logger.error(f"Failed to get Stripe public key: {e}")
            context["stripe_error"] = "Payment system temporarily unavailable"

        context.update(
            {
                "pricing_plans": pricing_plans,
                "user_balance": self._get_user_balance(),
            }
        )
        return context

    def _get_user_balance(self):
        """Get current user's balance."""
        try:
            balance = StudentAccountBalance.objects.get(student=self.request.user)
            return balance
        except StudentAccountBalance.DoesNotExist:
            return None


class PaymentCreateView(LoginRequiredMixin, View):
    """Process payment creation with Stripe."""

    def post(self, request, *args, **kwargs):
        try:
            plan_id = request.POST.get("plan_id")
            payment_method_id = request.POST.get("payment_method_id")

            if not plan_id:
                return JsonResponse({"error": "Plan ID is required"}, status=400)

            plan = get_object_or_404(PricingPlan, id=plan_id, is_active=True)

            # Initialize payment service
            payment_service = PaymentService()

            # Create payment intent
            result = payment_service.create_payment_intent(
                user=request.user, plan=plan, payment_method_id=payment_method_id
            )

            if result.get("error"):
                return JsonResponse({"error": result["error"]}, status=400)

            # Return client secret for confirmation
            return JsonResponse(
                {"client_secret": result["client_secret"], "payment_intent_id": result["payment_intent_id"]}
            )

        except Exception as e:
            logger.error(f"Payment creation error: {e}")
            return JsonResponse({"error": "Payment processing failed"}, status=500)


class PaymentConfirmView(LoginRequiredMixin, View):
    """Confirm payment and update balance."""

    def post(self, request, *args, **kwargs):
        try:
            payment_intent_id = request.POST.get("payment_intent_id")

            if not payment_intent_id:
                return JsonResponse({"error": "Payment intent ID is required"}, status=400)

            payment_service = PaymentService()
            result = payment_service.confirm_payment(payment_intent_id=payment_intent_id, user=request.user)

            if result.get("success"):
                # Render success partial for HTMX
                context = {"transaction": result.get("transaction"), "new_balance": result.get("new_balance")}
                return render(request, "finances/payments/partials/payment_success.html", context)
            else:
                return JsonResponse({"error": result.get("error", "Payment confirmation failed")}, status=400)

        except Exception as e:
            logger.error(f"Payment confirmation error: {e}")
            return JsonResponse({"error": "Payment confirmation failed"}, status=500)


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    """Display payment success page."""

    template_name = "finances/payments/payment_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction_id = self.kwargs.get("transaction_id")

        if transaction_id:
            try:
                transaction = PurchaseTransaction.objects.get(id=transaction_id, student=self.request.user)
                context["transaction"] = transaction
                context["new_balance"] = self._get_user_balance()
            except PurchaseTransaction.DoesNotExist:
                messages.error(self.request, "Transaction not found")

        return context

    def _get_user_balance(self):
        """Get current user's balance."""
        try:
            balance = StudentAccountBalance.objects.get(student=self.request.user)
            return balance
        except StudentAccountBalance.DoesNotExist:
            return None


# =============================================================================
# Balance Management Views
# =============================================================================


class BalanceOverviewView(LoginRequiredMixin, TemplateView):
    """Display student balance overview."""

    template_name = "finances/balance/balance_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get or create balance for user
        balance, _created = StudentAccountBalance.objects.get_or_create(
            student=self.request.user, defaults={"remaining_hours": Decimal("0.00")}
        )

        # Get recent transactions
        recent_transactions = PurchaseTransaction.objects.filter(student=self.request.user).order_by("-created_at")[:10]

        context.update(
            {
                "balance": balance,
                "recent_transactions": recent_transactions,
                "pricing_plans": PricingPlan.objects.filter(is_active=True),
            }
        )
        return context


class BalanceRefreshView(LoginRequiredMixin, View):
    """HTMX endpoint to refresh balance widget."""

    def get(self, request, *args, **kwargs):
        try:
            balance = StudentAccountBalance.objects.get(student=request.user)
        except StudentAccountBalance.DoesNotExist:
            balance = StudentAccountBalance.objects.create(student=request.user, remaining_hours=Decimal("0.00"))

        context = {"balance": balance}
        return render(request, "finances/balance/partials/balance_widget.html", context)


class TransactionHistoryView(LoginRequiredMixin, ListView):
    """Display transaction history with pagination."""

    model = PurchaseTransaction
    template_name = "finances/balance/transaction_history.html"
    context_object_name = "transactions"
    paginate_by = 20

    def get_queryset(self):
        return PurchaseTransaction.objects.filter(student=self.request.user).order_by("-created_at")


class TopUpFormView(LoginRequiredMixin, View):
    """HTMX form for top-up (quick purchase)."""

    def get(self, request, *args, **kwargs):
        pricing_plans = PricingPlan.objects.filter(is_active=True)
        context = {"pricing_plans": pricing_plans}
        return render(request, "finances/balance/partials/top_up_form.html", context)

    def post(self, request, *args, **kwargs):
        # Redirect to payment form with selected plan
        plan_id = request.POST.get("plan_id")
        if plan_id:
            return redirect("finances:payment-form", plan_id=plan_id)
        else:
            messages.error(request, "Please select a plan")
            return redirect("finances:balance-overview")


# =============================================================================
# School Billing Settings Views
# =============================================================================


class BillingSettingsView(LoginRequiredMixin, SchoolPermissionMixin, TemplateView):
    """Display and manage school billing settings."""

    template_name = "finances/admin/billing_settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_schools = self.get_user_schools()

        settings = SchoolBillingSettings.objects.filter(school__in=user_schools)

        context.update({"settings": settings, "user_schools": user_schools})
        return context


class BillingSettingsUpdateView(LoginRequiredMixin, SchoolPermissionMixin, UpdateView):
    """Update school billing settings."""

    model = SchoolBillingSettings
    template_name = "finances/admin/billing_settings_form.html"
    fields = ["stripe_account_id", "stripe_publishable_key", "default_currency"]

    def get_queryset(self):
        """Filter settings by user's schools."""
        user_schools = self.get_user_schools()
        return SchoolBillingSettings.objects.filter(school__in=user_schools)

    def get_success_url(self):
        return reverse("finances:billing-settings")


# =============================================================================
# Teacher Compensation Views
# =============================================================================


class TeacherCompensationView(LoginRequiredMixin, SchoolPermissionMixin, ListView):
    """Display teacher compensation rules and payments."""

    model = TeacherCompensationRule
    template_name = "finances/admin/teacher_compensation.html"
    context_object_name = "compensation_rules"

    def get_queryset(self):
        user_schools = self.get_user_schools()
        return TeacherCompensationRule.objects.filter(school__in=user_schools)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get recent payments
        user_schools = self.get_user_schools()
        recent_payments = TeacherPaymentEntry.objects.filter(teacher__school__in=user_schools).order_by("-created_at")[
            :10
        ]

        context["recent_payments"] = recent_payments
        return context


# =============================================================================
# Webhook Views
# =============================================================================


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    try:
        payload = request.body
        sig_header = request.headers.get("stripe-signature")

        stripe_service = StripeService()
        event = stripe_service.verify_webhook(payload, sig_header)

        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            # Process successful payment
            _process_payment_success(payment_intent)
        elif event["type"] == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            # Process failed payment
            _process_payment_failure(payment_intent)

        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return HttpResponse(status=400)


def _process_payment_success(payment_intent):
    """Process successful payment intent."""
    try:
        # Find the transaction by payment intent ID
        transaction = PurchaseTransaction.objects.get(stripe_payment_intent_id=payment_intent["id"])

        # Update transaction status
        transaction.payment_status = TransactionPaymentStatus.COMPLETED
        transaction.save()

        # Update student balance
        balance, _created = StudentAccountBalance.objects.get_or_create(student=transaction.student)
        balance.remaining_hours += transaction.tutoring_hours_purchased
        balance.save()

        logger.info(f"Payment processed successfully: {payment_intent['id']}")

    except PurchaseTransaction.DoesNotExist:
        logger.error(f"Transaction not found for payment intent: {payment_intent['id']}")
    except Exception as e:
        logger.error(f"Error processing payment success: {e}")


def _process_payment_failure(payment_intent):
    """Process failed payment intent."""
    try:
        transaction = PurchaseTransaction.objects.get(stripe_payment_intent_id=payment_intent["id"])

        transaction.payment_status = TransactionPaymentStatus.FAILED
        transaction.save()

        logger.warning(f"Payment failed: {payment_intent['id']}")

    except PurchaseTransaction.DoesNotExist:
        logger.error(f"Transaction not found for failed payment: {payment_intent['id']}")
    except Exception as e:
        logger.error(f"Error processing payment failure: {e}")


# =============================================================================
# Pricing Plans Views
# =============================================================================


@login_required
def pricing_plans_list(request):
    """List active pricing plans."""
    plans = PricingPlan.objects.filter(is_active=True).order_by("tutoring_hours")

    if request.headers.get("HX-Request"):
        return render(request, "finances/partials/pricing_plans_list.html", {"plans": plans})

    return render(request, "finances/pricing_plans.html", {"plans": plans})


# =============================================================================
# Utility Views
# =============================================================================


@login_required
def stripe_config(request):
    """Get Stripe configuration for frontend."""
    try:
        stripe_service = StripeService()
        config = {
            "public_key": stripe_service.get_public_key(),
        }
        return JsonResponse(config)
    except Exception as e:
        logger.error(f"Failed to get Stripe config: {e}")
        return JsonResponse({"error": "Configuration unavailable"}, status=500)


@login_required
def stripe_connection_test(request):
    """Test Stripe connection."""
    try:
        stripe_service = StripeService()
        result = stripe_service.test_connection()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Stripe connection test failed: {e}")
        return JsonResponse({"error": "Connection test failed"}, status=500)
