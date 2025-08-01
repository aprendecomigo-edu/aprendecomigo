"""
URL configuration for the finances app.
"""

from django.urls import include, path

app_name = 'finances'
from rest_framework.routers import DefaultRouter

from .views import (
    ClassSessionViewSet,
    FamilyBudgetControlViewSet,
    ParentApprovalDashboardView,
    PurchaseApprovalRequestViewSet,
    SchoolBillingSettingsViewSet,
    StudentBalanceViewSet,
    StudentPurchaseRequestView,
    TeacherCompensationRuleViewSet,
    TeacherPaymentEntryViewSet,
    TutorAnalyticsAPIView,
    TutorAnalyticsView,
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
router.register(r"student-balance", StudentBalanceViewSet, basename="student-balance")

# Parent-child approval system viewsets (Issues #111 & #112)
router.register(r"budget-controls", FamilyBudgetControlViewSet, basename="familybudgetcontrol")
router.register(r"approval-requests", PurchaseApprovalRequestViewSet, basename="purchaseapprovalrequest")

# URL patterns
urlpatterns = [
    path("", include(router.urls)),
    # Pricing plans endpoint
    path("pricing-plans/", active_pricing_plans, name="pricing-plans-list"),
    # Purchase initiation endpoint
    path("purchase/initiate/", purchase_initiate, name="purchase-initiate"),
    # Tutor analytics endpoint
    path("tutor-analytics/<int:school_id>/", TutorAnalyticsAPIView.as_view(), name="tutor-analytics"),
    
    # Parent-child approval system endpoints (Issues #111 & #112)
    path("student-purchase-request/", StudentPurchaseRequestView.as_view(), name="student-purchase-request"),
    path("parent-approval-dashboard/", ParentApprovalDashboardView.as_view(), name="parent-approval-dashboard"),
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
    
    # TODO: Add subscription webhook endpoint when subscription features are implemented
    # path("webhooks/stripe/subscriptions/", subscription_webhook, name="subscription-webhook"),
]
