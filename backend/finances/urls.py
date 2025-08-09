"""
URL configuration for the finances app.
"""

from django.urls import include, path

app_name = 'finances'
from rest_framework.routers import DefaultRouter

from .views import (
    ClassSessionViewSet,
    FamilyBudgetControlViewSet,
    FamilyMetricsView,
    PackageExpirationViewSet,
    ParentApprovalDashboardView,
    PurchaseApprovalRequestViewSet,
    SchoolBillingSettingsViewSet,
    StudentBalanceViewSet,
    StudentPurchaseRequestView,
    TeacherCompensationRuleViewSet,
    TeacherPaymentEntryViewSet,
    active_pricing_plans,
    purchase_initiate,
    stripe_config,
    stripe_connection_test,
    stripe_webhook,
)

from .admin_views import (
    get_expired_packages,
    process_expired_packages,
    extend_package,
    get_expiration_analytics,
    send_expiration_notifications,
    get_packages_expiring_soon,
    bulk_extend_packages,
    # Administrative Payment Action APIs (Issue #116)
    process_refund,
    get_refund_status,
    list_transaction_refunds,
    sync_dispute_from_stripe,
    submit_dispute_evidence,
    get_dispute_details,
    list_disputes,
    update_dispute_notes,
    get_overdue_disputes,
    analyze_transaction_fraud,
    analyze_user_fraud,
    run_batch_fraud_analysis,
    get_active_fraud_alerts,
    retry_failed_payment,
    get_admin_action_log,
)

from .views_admin import (
    payment_metrics,
    TransactionHistoryView,
    WebhookStatusView,
    student_analytics,
    system_health,
)

# Create a router and register our viewsets
router = DefaultRouter()

# Register viewsets with the router
router.register(
    r"billing-settings", SchoolBillingSettingsViewSet, basename="school-billing-settings"
)
router.register(
    r"compensation-rules", TeacherCompensationRuleViewSet, basename="teacher-compensation-rules"
)
router.register(r"sessions", ClassSessionViewSet, basename="class-sessions")
router.register(r"payments", TeacherPaymentEntryViewSet, basename="teacher-payments")
router.register(r"studentbalance", StudentBalanceViewSet, basename="studentbalance")

# Parent-child approval system viewsets (Issues #111 & #112)
router.register(r"budget-controls", FamilyBudgetControlViewSet, basename="familybudgetcontrol")
router.register(r"approval-requests", PurchaseApprovalRequestViewSet, basename="purchaseapprovalrequest")

# Package expiration management viewset (Issue #167)
router.register(r'package-expiration', PackageExpirationViewSet, basename='package-expiration')

# URL patterns
urlpatterns = [
    path("", include(router.urls)),
    # Pricing plans endpoint
    path("pricing-plans/", active_pricing_plans, name="pricing-plans-list"),
    # Purchase initiation endpoint
    path("purchase/initiate/", purchase_initiate, name="purchase-initiate"),
    # Parent-child approval system endpoints (Issues #111 & #112)
    path("student-purchase-request/", StudentPurchaseRequestView.as_view(), name="student-purchase-request"),
    path("parent-approval-dashboard/", ParentApprovalDashboardView.as_view(), name="parent-approval-dashboard"),
    path("family-metrics/", FamilyMetricsView.as_view(), name="family-metrics"),
    # Stripe integration endpoints
    path("stripe/config/", stripe_config, name="stripe-config"),
    path("stripe/test-connection/", stripe_connection_test, name="stripe-connection-test"),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    
    # Package Expiration Management Admin Endpoints
    path("admin/expired-packages/", get_expired_packages, name="admin-expired-packages"),
    path("admin/process-expired-packages/", process_expired_packages, name="admin-process-expired"),
    path("admin/packages/<int:package_id>/extend/", extend_package, name="admin-extend-package"),
    path("admin/expiration-analytics/", get_expiration_analytics, name="admin-expiration-analytics"),
    path("admin/send-expiration-notifications/", send_expiration_notifications, name="admin-send-notifications"),
    path("admin/packages-expiring-soon/", get_packages_expiring_soon, name="admin-packages-expiring-soon"),
    path("admin/bulk-extend-packages/", bulk_extend_packages, name="admin-bulk-extend-packages"),
    
    # Payment Analytics and Monitoring Admin Endpoints (Issues #115 & #116)
    path("admin/payments/metrics/", payment_metrics, name="admin-payment-metrics"),
    path("admin/payments/transactions/", TransactionHistoryView.as_view(), name="admin-transaction-history"),
    path("admin/webhooks/status/", WebhookStatusView.as_view(), name="admin-webhook-status"),
    path("admin/students/<int:student_id>/analytics/", student_analytics, name="admin-student-analytics"),
    path("admin/system/health/", system_health, name="admin-system-health"),
    
    # Administrative Payment Action APIs (Issue #116)
    path("admin/payments/refunds/", process_refund, name="admin-process-refund"),
    path("admin/payments/refunds/<str:refund_id>/status/", get_refund_status, name="admin-refund-status"),
    path("admin/payments/transactions/<int:transaction_id>/refunds/", list_transaction_refunds, name="admin-transaction-refunds"),
    
    path("admin/payments/disputes/sync/", sync_dispute_from_stripe, name="admin-sync-dispute"),
    path("admin/payments/disputes/<int:dispute_id>/evidence/", submit_dispute_evidence, name="admin-submit-evidence"),
    path("admin/payments/disputes/<str:stripe_dispute_id>/details/", get_dispute_details, name="admin-dispute-details"),
    path("admin/payments/disputes/", list_disputes, name="admin-list-disputes"),
    path("admin/payments/disputes/<int:dispute_id>/notes/", update_dispute_notes, name="admin-update-dispute-notes"),
    path("admin/payments/disputes/overdue/", get_overdue_disputes, name="admin-overdue-disputes"),
    
    path("admin/payments/fraud/transactions/<int:transaction_id>/analyze/", analyze_transaction_fraud, name="admin-analyze-transaction-fraud"),
    path("admin/payments/fraud/users/<int:user_id>/analyze/", analyze_user_fraud, name="admin-analyze-user-fraud"),
    path("admin/payments/fraud/batch-analysis/", run_batch_fraud_analysis, name="admin-batch-fraud-analysis"),
    path("admin/payments/fraud/alerts/", get_active_fraud_alerts, name="admin-fraud-alerts"),
    
    path("admin/payments/retries/", retry_failed_payment, name="admin-retry-payment"),
    path("admin/payments/audit-log/", get_admin_action_log, name="admin-action-log"),
    
    # TODO: Add subscription webhook endpoint when subscription features are implemented
    # path("webhooks/stripe/subscriptions/", subscription_webhook, name="subscription-webhook"),
]
