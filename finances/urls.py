"""
URL configuration for the finances app (PWA conversion).
"""

from django.urls import path

app_name = "finances"

from .views import (
    # Balance Views
    BalanceOverviewView,
    BalanceRefreshView,
    BillingSettingsUpdateView,
    # School Admin Views
    BillingSettingsView,
    PaymentConfirmView,
    PaymentCreateView,
    # Payment Views
    PaymentFormView,
    PaymentSuccessView,
    TeacherCompensationView,
    TopUpFormView,
    TransactionHistoryView,
    # Utility Views
    pricing_plans_list,
    stripe_config,
    stripe_connection_test,
    stripe_webhook,
)

# TODO: Convert admin views to Django CBVs
# Import admin views from admin_views.py (to be converted later)
# from .admin_views import (
#     analyze_transaction_fraud,
#     analyze_user_fraud,
#     bulk_extend_packages,
#     extend_package,
#     get_active_fraud_alerts,
#     get_admin_action_log,
#     get_dispute_details,
#     get_expiration_analytics,
#     get_expired_packages,
#     get_overdue_disputes,
#     get_packages_expiring_soon,
#     get_refund_status,
#     list_disputes,
#     list_transaction_refunds,
#     process_expired_packages,
#     process_refund,
#     retry_failed_payment,
#     run_batch_fraud_analysis,
#     send_expiration_notifications,
#     submit_dispute_evidence,
#     sync_dispute_from_stripe,
#     update_dispute_notes,
# )

# Import admin views from views_admin.py (to be converted later)
# from .views_admin import (
#     TransactionHistoryView as AdminTransactionHistoryView,
#     WebhookStatusView,
#     payment_metrics,
#     student_analytics,
#     system_health,
# )

# TODO: Convert financial report views to Django CBVs
# Import financial report views (to be converted later)
# from .views_financial_reports import (
#     ExportStudentBalancesAPIView,
#     ExportTeacherSessionsAPIView,
#     download_receipt,
#     export_transactions_fixed,
#     generate_receipt,
#     list_receipts,
#     revenue_trends_analysis,
#     school_financial_overview,
#     student_spending_analytics,
#     teacher_compensation_report,
#     test_export_endpoint,
# )

urlpatterns = [
    # =============================================================================
    # Payment Processing URLs
    # =============================================================================
    path("", BalanceOverviewView.as_view(), name="balance-overview"),
    path("payments/", PaymentFormView.as_view(), name="payment-form"),
    path("payments/create/", PaymentCreateView.as_view(), name="payment-create"),
    path("payments/confirm/", PaymentConfirmView.as_view(), name="payment-confirm"),
    path("payments/success/<int:transaction_id>/", PaymentSuccessView.as_view(), name="payment-success"),
    # =============================================================================
    # Balance Management URLs
    # =============================================================================
    path("balance/", BalanceOverviewView.as_view(), name="balance-overview"),
    path("balance/refresh/", BalanceRefreshView.as_view(), name="balance-refresh"),
    path("transactions/", TransactionHistoryView.as_view(), name="transaction-history"),
    path("top-up/form/", TopUpFormView.as_view(), name="top-up-form"),
    # =============================================================================
    # Pricing and Configuration URLs
    # =============================================================================
    path("pricing-plans/", pricing_plans_list, name="pricing-plans-list"),
    path("stripe/config/", stripe_config, name="stripe-config"),
    path("stripe/test-connection/", stripe_connection_test, name="stripe-connection-test"),
    # =============================================================================
    # Webhook URLs
    # =============================================================================
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    # =============================================================================
    # School Admin URLs
    # =============================================================================
    path("admin/", BillingSettingsView.as_view(), name="admin-dashboard"),
    path("admin/billing-settings/", BillingSettingsView.as_view(), name="billing-settings"),
    path("admin/billing-settings/<int:pk>/", BillingSettingsUpdateView.as_view(), name="billing-settings-update"),
    path("admin/teacher-compensation/", TeacherCompensationView.as_view(), name="teacher-compensation"),
]
