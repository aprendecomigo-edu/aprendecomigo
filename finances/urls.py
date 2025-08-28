"""
URL configuration for the finances app (PWA conversion).
"""

from django.urls import path

app_name = "finances"

from .views import (
    # Payment Views
    PaymentFormView,
    PaymentCreateView,
    PaymentConfirmView,
    PaymentSuccessView,
    
    # Balance Views
    BalanceOverviewView,
    BalanceRefreshView,
    TransactionHistoryView,
    TopUpFormView,
    
    # School Admin Views
    BillingSettingsView,
    BillingSettingsUpdateView,
    TeacherCompensationView,
    
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
    
    # =============================================================================
    # Financial Reports URLs (Legacy - TODO: Convert to Django views)
    # =============================================================================
    # TODO: Convert these financial report endpoints to Django CBVs with HTMX
    # path("analytics/school-overview/", school_financial_overview, name="analytics-school-overview"),
    # path("analytics/teacher-compensation/", teacher_compensation_report, name="analytics-teacher-compensation"),
    # path("analytics/revenue-trends/", revenue_trends_analysis, name="analytics-revenue-trends"),
    # path("analytics/student-spending/", student_spending_analytics, name="analytics-student-spending"),
    
    # Export endpoints
    # path("export/transactions/", export_transactions_fixed, name="export-transactions"),
    # path("test-export/", test_export_endpoint, name="test-export"),
    # path("export/student-balances/", ExportStudentBalancesAPIView.as_view(), name="export-student-balances"),
    # path("export/teacher-sessions/", ExportTeacherSessionsAPIView.as_view(), name="export-teacher-sessions"),
    
    # Receipt endpoints
    # path("receipts/generate/", generate_receipt, name="receipt-generate"),
    # path("receipts/", list_receipts, name="receipt-list"),
    # path("receipts/<int:pk>/download/", download_receipt, name="receipt-download"),
    
    # =============================================================================
    # Administrative URLs (Legacy - TODO: Convert to Django views)
    # =============================================================================
    # TODO: Convert these admin endpoints to Django CBVs with HTMX
    # Package Expiration Management Admin Endpoints
    # path("admin/expired-packages/", get_expired_packages, name="admin-expired-packages"),
    # path("admin/process-expired-packages/", process_expired_packages, name="admin-process-expired"),
    # path("admin/packages/<int:package_id>/extend/", extend_package, name="admin-extend-package"),
    # path("admin/expiration-analytics/", get_expiration_analytics, name="admin-expiration-analytics"),
    # path("admin/send-expiration-notifications/", send_expiration_notifications, name="admin-send-notifications"),
    # path("admin/packages-expiring-soon/", get_packages_expiring_soon, name="admin-packages-expiring-soon"),
    # path("admin/bulk-extend-packages/", bulk_extend_packages, name="admin-bulk-extend-packages"),
    
    # Payment Analytics and Monitoring Admin Endpoints
    # path("admin/payments/metrics/", payment_metrics, name="admin-payment-metrics"),
    # path("admin/payments/transactions/", AdminTransactionHistoryView.as_view(), name="admin-transaction-history"),
    # path("admin/webhooks/status/", WebhookStatusView.as_view(), name="admin-webhook-status"),
    # path("admin/students/<int:student_id>/analytics/", student_analytics, name="admin-student-analytics"),
    # path("admin/system/health/", system_health, name="admin-system-health"),
    
    # Administrative Payment Action APIs
    # path("admin/payments/refunds/", process_refund, name="admin-process-refund"),
    # path("admin/payments/refunds/<str:refund_id>/status/", get_refund_status, name="admin-refund-status"),
    # path(
    #     "admin/payments/transactions/<int:transaction_id>/refunds/",
    #     list_transaction_refunds,
    #     name="admin-transaction-refunds",
    # ),
    # path("admin/payments/disputes/sync/", sync_dispute_from_stripe, name="admin-sync-dispute"),
    # path("admin/payments/disputes/<int:dispute_id>/evidence/", submit_dispute_evidence, name="admin-submit-evidence"),
    # path("admin/payments/disputes/<str:stripe_dispute_id>/details/", get_dispute_details, name="admin-dispute-details"),
    # path("admin/payments/disputes/", list_disputes, name="admin-list-disputes"),
    # path("admin/payments/disputes/<int:dispute_id>/notes/", update_dispute_notes, name="admin-update-dispute-notes"),
    # path("admin/payments/disputes/overdue/", get_overdue_disputes, name="admin-overdue-disputes"),
    # path(
    #     "admin/payments/fraud/transactions/<int:transaction_id>/analyze/",
    #     analyze_transaction_fraud,
    #     name="admin-analyze-transaction-fraud",
    # ),
    # path("admin/payments/fraud/users/<int:user_id>/analyze/", analyze_user_fraud, name="admin-analyze-user-fraud"),
    # path("admin/payments/fraud/batch-analysis/", run_batch_fraud_analysis, name="admin-batch-fraud-analysis"),
    # path("admin/payments/fraud/alerts/", get_active_fraud_alerts, name="admin-fraud-alerts"),
    # path("admin/payments/retries/", retry_failed_payment, name="admin-retry-payment"),
    # path("admin/payments/audit-log/", get_admin_action_log, name="admin-action-log"),
]