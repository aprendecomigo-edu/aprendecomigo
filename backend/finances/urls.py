"""
URL configuration for the finances app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClassSessionViewSet,
    SchoolBillingSettingsViewSet,
    TeacherCompensationRuleViewSet,
    TeacherPaymentEntryViewSet,
    stripe_config,
    stripe_connection_test,
    stripe_webhook,
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

# URL patterns
urlpatterns = [
    path("api/", include(router.urls)),
    # Stripe integration endpoints
    path("api/stripe/config/", stripe_config, name="stripe-config"),
    path("api/stripe/test-connection/", stripe_connection_test, name="stripe-connection-test"),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
]
