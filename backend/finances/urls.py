"""
URL configuration for the finances app.
"""

from django.urls import include, path

app_name = 'finances'
from rest_framework.routers import DefaultRouter

from .views import (
    ClassSessionViewSet,
    SchoolBillingSettingsViewSet,
    StudentBalanceViewSet,
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

# URL patterns
urlpatterns = [
    path("api/", include(router.urls)),
    # Pricing plans endpoint
    path("api/pricing-plans/", active_pricing_plans, name="pricing-plans-list"),
    # Purchase initiation endpoint
    path("api/purchase/initiate/", purchase_initiate, name="purchase-initiate"),
    # Stripe integration endpoints
    path("api/stripe/config/", stripe_config, name="stripe-config"),
    path("api/stripe/test-connection/", stripe_connection_test, name="stripe-connection-test"),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    
    # Package Expiration Management Admin Endpoints
    path("api/admin/expired-packages/", get_expired_packages, name="admin-expired-packages"),
    path("api/admin/process-expired-packages/", process_expired_packages, name="admin-process-expired"),
    path("api/admin/packages/<int:package_id>/extend/", extend_package, name="admin-extend-package"),
    path("api/admin/expiration-analytics/", get_expiration_analytics, name="admin-expiration-analytics"),
    path("api/admin/send-expiration-notifications/", send_expiration_notifications, name="admin-send-notifications"),
    path("api/admin/packages-expiring-soon/", get_packages_expiring_soon, name="admin-packages-expiring-soon"),
    path("api/admin/bulk-extend-packages/", bulk_extend_packages, name="admin-bulk-extend-packages"),
    
    # TODO: Add subscription webhook endpoint when subscription features are implemented
    # path("webhooks/stripe/subscriptions/", subscription_webhook, name="subscription-webhook"),
]
