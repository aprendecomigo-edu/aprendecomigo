"""
Test cases for PricingPlan model and related functionality.

This module contains comprehensive tests for:
- PricingPlan model creation, validation, and properties
- Django Admin interface for PricingPlan
- API endpoint for fetching active pricing plans with caching
- Management command for creating default pricing plans
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command, CommandError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser
from ..models import PricingPlan, PlanType


class PricingPlanModelTestCase(TestCase):
    """Test cases for PricingPlan model."""

    def test_package_plan_creation_with_required_fields(self):
        """Test creating a package PricingPlan with required fields."""
        plan = PricingPlan.objects.create(
            name="Basic Package",
            description="10 hours of tutoring",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        self.assertEqual(plan.name, "Basic Package")
        self.assertEqual(plan.description, "10 hours of tutoring")
        self.assertEqual(plan.plan_type, PlanType.PACKAGE)
        self.assertEqual(plan.hours_included, Decimal("10.0"))
        self.assertEqual(plan.price_eur, Decimal("100.00"))
        self.assertEqual(plan.validity_days, 30)
        self.assertEqual(plan.display_order, 1)
        self.assertFalse(plan.is_featured)
        self.assertTrue(plan.is_active)
        self.assertIsNotNone(plan.created_at)
        self.assertIsNotNone(plan.updated_at)

    def test_subscription_plan_creation(self):
        """Test creating a subscription PricingPlan."""
        plan = PricingPlan.objects.create(
            name="Monthly Subscription",
            description="Unlimited tutoring access",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("20.0"),
            price_eur=Decimal("150.00"),
            validity_days=None,  # Subscriptions should not have validity_days
            display_order=2,
            is_featured=True,
            is_active=True
        )
        
        self.assertEqual(plan.plan_type, PlanType.SUBSCRIPTION)
        self.assertIsNone(plan.validity_days)
        self.assertTrue(plan.is_featured)

    def test_price_per_hour_property_calculation(self):
        """Test price_per_hour property method calculation."""
        plan = PricingPlan.objects.create(
            name="Test Package",
            description="Test description",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("120.00"),
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        # price_per_hour = 120.00 / 10.0 = 12.00
        self.assertEqual(plan.price_per_hour, Decimal("12.00"))

    def test_price_per_hour_property_with_zero_hours(self):
        """Test price_per_hour property when hours_included is zero."""
        plan = PricingPlan.objects.create(
            name="Test Package",
            description="Test description",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("0.0"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        # Should return None when hours_included is zero to avoid division by zero
        self.assertIsNone(plan.price_per_hour)

    def test_package_validation_requires_validity_days(self):
        """Test that package plans must have validity_days specified."""
        plan = PricingPlan(
            name="Invalid Package",
            description="Package without validity days",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=None,  # Invalid for packages
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        with self.assertRaises(ValidationError) as context:
            plan.full_clean()
        
        self.assertIn("Package plans must have validity_days specified", str(context.exception))

    def test_subscription_validation_should_not_have_validity_days(self):
        """Test that subscription plans should not have validity_days."""
        plan = PricingPlan(
            name="Invalid Subscription",
            description="Subscription with validity days",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("20.0"),
            price_eur=Decimal("150.00"),
            validity_days=30,  # Invalid for subscriptions
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        with self.assertRaises(ValidationError) as context:
            plan.full_clean()
        
        self.assertIn("Subscription plans should not have validity_days", str(context.exception))

    def test_positive_price_validation(self):
        """Test that price_eur must be positive."""
        plan = PricingPlan(
            name="Free Package",
            description="Invalid free package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("0.00"),  # Invalid - must be positive
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        with self.assertRaises(ValidationError) as context:
            plan.full_clean()
        
        self.assertIn("Price must be greater than 0", str(context.exception))

    def test_negative_price_validation(self):
        """Test that price_eur cannot be negative."""
        plan = PricingPlan(
            name="Negative Price Package",
            description="Invalid negative price",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("-50.00"),  # Invalid - cannot be negative
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        with self.assertRaises(ValidationError) as context:
            plan.full_clean()
        
        self.assertIn("Price must be greater than 0", str(context.exception))

    def test_positive_hours_validation(self):
        """Test that hours_included must be positive."""
        plan = PricingPlan(
            name="Zero Hours Package",
            description="Invalid zero hours package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("0.0"),  # Invalid - must be positive
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        with self.assertRaises(ValidationError) as context:
            plan.full_clean()
        
        self.assertIn("Hours included must be greater than 0", str(context.exception))

    def test_negative_hours_validation(self):
        """Test that hours_included cannot be negative."""
        plan = PricingPlan(
            name="Negative Hours Package",
            description="Invalid negative hours",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("-5.0"),  # Invalid - cannot be negative
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        with self.assertRaises(ValidationError) as context:
            plan.full_clean()
        
        self.assertIn("Hours included must be greater than 0", str(context.exception))

    def test_positive_validity_days_validation(self):
        """Test that validity_days must be positive when specified."""
        plan = PricingPlan(
            name="Zero Validity Package",
            description="Invalid zero validity",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=0,  # Invalid - must be positive
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        with self.assertRaises(ValidationError) as context:
            plan.full_clean()
        
        # Check that validation error occurred (Django validator message)
        self.assertIn("Ensure this value is greater than or equal to 1", str(context.exception))

    def test_negative_validity_days_validation(self):
        """Test that validity_days cannot be negative."""
        plan = PricingPlan(
            name="Negative Validity Package",
            description="Invalid negative validity",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=-10,  # Invalid - cannot be negative
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        with self.assertRaises(ValidationError) as context:
            plan.full_clean()
        
        # Check that validation error occurred (Django validator message)
        self.assertIn("Ensure this value is greater than or equal to 1", str(context.exception))

    def test_string_representation(self):
        """Test string representation of PricingPlan."""
        plan = PricingPlan.objects.create(
            name="Premium Package",
            description="20 hours of tutoring",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("20.0"),
            price_eur=Decimal("180.00"),
            validity_days=60,
            display_order=1,
            is_featured=True,
            is_active=True
        )
        
        expected_str = "Premium Package - €180.00 (20.0h, 60 days)"
        self.assertEqual(str(plan), expected_str)

    def test_string_representation_subscription(self):
        """Test string representation of subscription PricingPlan."""
        plan = PricingPlan.objects.create(
            name="Monthly Unlimited",
            description="Unlimited access",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("30.0"),
            price_eur=Decimal("200.00"),
            validity_days=None,
            display_order=1,
            is_featured=True,
            is_active=True
        )
        
        expected_str = "Monthly Unlimited - €200.00 (30.0h, subscription)"
        self.assertEqual(str(plan), expected_str)

    def test_model_meta_properties(self):
        """Test model meta properties like verbose names and ordering."""
        meta = PricingPlan._meta
        
        self.assertEqual(meta.verbose_name, "Pricing Plan")
        self.assertEqual(meta.verbose_name_plural, "Pricing Plans")
        self.assertEqual(meta.ordering, ["display_order", "name"])

    def test_active_plans_manager(self):
        """Test that active plans manager returns only active plans."""
        # Create active plan
        active_plan = PricingPlan.objects.create(
            name="Active Package",
            description="Active plan",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        # Create inactive plan
        inactive_plan = PricingPlan.objects.create(
            name="Inactive Package",
            description="Inactive plan",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=2,
            is_featured=False,
            is_active=False
        )
        
        # Test active manager
        active_plans = PricingPlan.active.all()
        self.assertIn(active_plan, active_plans)
        self.assertNotIn(inactive_plan, active_plans)
        self.assertEqual(len(active_plans), 1)

    def test_decimal_field_precision(self):
        """Test that decimal fields maintain proper precision."""
        plan = PricingPlan.objects.create(
            name="Precision Test",
            description="Test decimal precision",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.555"),  # Will be rounded to 2 decimal places
            price_eur=Decimal("123.456"),  # Will be rounded to 2 decimal places
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        # Refresh from database to check actual stored values
        plan.refresh_from_db()
        
        # Both fields have 2 decimal places
        self.assertEqual(plan.hours_included, Decimal("10.56"))
        self.assertEqual(plan.price_eur, Decimal("123.46"))

    def test_display_order_functionality(self):
        """Test that display_order affects plan ordering."""
        plan1 = PricingPlan.objects.create(
            name="Third Plan",
            description="Should be third",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=3,
            is_featured=False,
            is_active=True
        )
        
        plan2 = PricingPlan.objects.create(
            name="First Plan",
            description="Should be first",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("15.0"),
            price_eur=Decimal("150.00"),
            validity_days=45,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        plan3 = PricingPlan.objects.create(
            name="Second Plan",
            description="Should be second",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("20.0"),
            price_eur=Decimal("200.00"),
            validity_days=60,
            display_order=2,
            is_featured=False,
            is_active=True
        )
        
        # Test ordering
        plans = list(PricingPlan.objects.all())
        self.assertEqual(plans[0], plan2)  # display_order=1
        self.assertEqual(plans[1], plan3)  # display_order=2
        self.assertEqual(plans[2], plan1)  # display_order=3

    def test_featured_plan_functionality(self):
        """Test is_featured flag functionality."""
        featured_plan = PricingPlan.objects.create(
            name="Featured Plan",
            description="This is featured",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_featured=True,
            is_active=True
        )
        
        regular_plan = PricingPlan.objects.create(
            name="Regular Plan",
            description="Not featured",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=2,
            is_featured=False,
            is_active=True
        )
        
        # Test filtering by featured status
        featured_plans = PricingPlan.objects.filter(is_featured=True)
        regular_plans = PricingPlan.objects.filter(is_featured=False)
        
        self.assertIn(featured_plan, featured_plans)
        self.assertNotIn(regular_plan, featured_plans)
        self.assertIn(regular_plan, regular_plans)
        self.assertNotIn(featured_plan, regular_plans)

    def test_large_values_handling(self):
        """Test handling of large decimal values within field limits."""
        plan = PricingPlan.objects.create(
            name="Large Values Test",
            description="Test large values",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("999.99"),  # 5 digits, 2 decimal places
            price_eur=Decimal("9999.99"),  # 6 digits, 2 decimal places
            validity_days=999,  # Large but valid integer
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        self.assertEqual(plan.hours_included, Decimal("999.99"))
        self.assertEqual(plan.price_eur, Decimal("9999.99"))
        self.assertEqual(plan.validity_days, 999)


class PricingPlanAPITestCase(APITestCase):
    """Test cases for PricingPlan API endpoints."""

    def setUp(self):
        """Set up test data for API tests."""
        # Create a test user
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        
        # Create test pricing plans
        self.active_package = PricingPlan.objects.create(
            name="Active Package",
            description="10 hours package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        self.featured_subscription = PricingPlan.objects.create(
            name="Featured Subscription",
            description="Unlimited access",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("30.0"),
            price_eur=Decimal("200.00"),
            validity_days=None,
            display_order=2,
            is_featured=True,
            is_active=True
        )
        
        self.inactive_plan = PricingPlan.objects.create(
            name="Inactive Plan",
            description="Should not appear",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("5.0"),
            price_eur=Decimal("50.00"),
            validity_days=15,
            display_order=3,
            is_featured=False,
            is_active=False
        )

    def test_get_active_pricing_plans_unauthenticated(self):
        """Test that unauthenticated users can access pricing plans."""
        url = reverse('finances:pricing-plans-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only active plans
        
        # Check that plans are ordered correctly
        self.assertEqual(response.data[0]['name'], 'Active Package')
        self.assertEqual(response.data[1]['name'], 'Featured Subscription')
        
        # Check that inactive plan is not included
        plan_names = [plan['name'] for plan in response.data]
        self.assertNotIn('Inactive Plan', plan_names)

    def test_get_active_pricing_plans_authenticated(self):
        """Test that authenticated users can access pricing plans."""
        self.client.force_authenticate(user=self.user)
        url = reverse('finances:pricing-plans-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_pricing_plans_response_structure(self):
        """Test the structure of pricing plans API response."""
        url = reverse('finances:pricing-plans-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
        # Find our Active Package in the response
        active_package_data = None
        for plan in response.data:
            if plan['name'] == 'Active Package':
                active_package_data = plan
                break
        
        self.assertIsNotNone(active_package_data, "Active Package should be in response")
        
        # Check plan structure
        expected_fields = [
            'id', 'name', 'description', 'plan_type', 'hours_included',
            'price_eur', 'validity_days', 'display_order', 'is_featured',
            'price_per_hour'
        ]
        
        for field in expected_fields:
            self.assertIn(field, active_package_data)
        
        # Check data types and values for Active Package
        self.assertEqual(active_package_data['name'], 'Active Package')
        self.assertEqual(active_package_data['plan_type'], 'package')
        self.assertEqual(float(active_package_data['hours_included']), 10.0)
        self.assertEqual(float(active_package_data['price_eur']), 100.0)
        self.assertEqual(active_package_data['validity_days'], 30)
        self.assertFalse(active_package_data['is_featured'])
        self.assertEqual(float(active_package_data['price_per_hour']), 10.0)

    def test_pricing_plans_subscription_response(self):
        """Test subscription plan specific fields in response."""
        url = reverse('finances:pricing-plans-list')
        response = self.client.get(url)
        
        # Find subscription plan in response
        subscription_plan = None
        for plan in response.data:
            if plan['plan_type'] == 'subscription':
                subscription_plan = plan
                break
        
        self.assertIsNotNone(subscription_plan)
        self.assertEqual(subscription_plan['name'], 'Featured Subscription')
        self.assertIsNone(subscription_plan['validity_days'])
        self.assertTrue(subscription_plan['is_featured'])

    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_pricing_plans_caching(self, mock_cache_set, mock_cache_get):
        """Test that pricing plans API response is cached."""
        # First request - cache miss
        mock_cache_get.return_value = None
        
        url = reverse('finances:pricing-plans-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cache.get was called
        mock_cache_get.assert_called_with('active_pricing_plans')
        
        # Verify cache.set was called with correct data
        mock_cache_set.assert_called_once()
        call_args = mock_cache_set.call_args
        self.assertEqual(call_args[0][0], 'active_pricing_plans')  # cache key
        self.assertEqual(call_args[1]['timeout'], 3600)  # 1 hour timeout

    @patch('django.core.cache.cache.get')
    def test_pricing_plans_cache_hit(self, mock_cache_get):
        """Test API response when cache hit occurs."""
        # Mock cached data
        cached_data = [
            {
                'id': 1,
                'name': 'Cached Plan',
                'description': 'From cache',
                'plan_type': 'package',
                'hours_included': '10.00',
                'price_eur': '100.00',
                'validity_days': 30,
                'display_order': 1,
                'is_featured': False,
                'price_per_hour': '10.00'
            }
        ]
        mock_cache_get.return_value = cached_data
        
        url = reverse('finances:pricing-plans-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, cached_data)
        
        # Verify cache.get was called
        mock_cache_get.assert_called_with('active_pricing_plans')

    def test_pricing_plans_ordering(self):
        """Test that pricing plans are returned in correct order."""
        # Clear cache to ensure fresh data
        cache.clear()
        
        # Create additional plan with different display_order
        PricingPlan.objects.create(
            name="First Plan",
            description="Should be first",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("5.0"),
            price_eur=Decimal("50.00"),
            validity_days=15,
            display_order=0,  # Lower than existing plans
            is_featured=False,
            is_active=True
        )
        
        url = reverse('finances:pricing-plans-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 3)  # At least 3 plans expected
        
        # Check that the first plan has display_order=0 (our newly created plan)
        self.assertEqual(response.data[0]['name'], 'First Plan')  # display_order=0
        self.assertEqual(response.data[0]['display_order'], 0)
        
        # Verify ordering is ascending by display_order
        for i in range(1, len(response.data)):
            self.assertGreaterEqual(response.data[i]['display_order'], 
                                   response.data[i-1]['display_order'])


class PricingPlanManagementCommandTestCase(TransactionTestCase):
    """Test cases for create_default_pricing_plans management command."""

    def setUp(self):
        """Set up test environment."""
        # Clear any existing pricing plans
        PricingPlan.objects.all().delete()
        
        # Clear cache
        cache.clear()

    def test_create_default_pricing_plans_success(self):
        """Test successful creation of default pricing plans."""
        # Ensure no plans exist initially
        self.assertEqual(PricingPlan.objects.count(), 0)
        
        # Run the command
        call_command('create_default_pricing_plans')
        
        # Check that plans were created
        self.assertGreater(PricingPlan.objects.count(), 0)
        
        # Verify that we have both package and subscription plans
        packages = PricingPlan.objects.filter(plan_type=PlanType.PACKAGE)
        subscriptions = PricingPlan.objects.filter(plan_type=PlanType.SUBSCRIPTION)
        
        self.assertGreater(packages.count(), 0)
        self.assertGreater(subscriptions.count(), 0)

    def test_create_default_pricing_plans_specific_plans(self):
        """Test that specific default plans are created with correct data."""
        call_command('create_default_pricing_plans')
        
        # Check for specific expected plans
        basic_package = PricingPlan.objects.filter(name="Basic Package").first()
        self.assertIsNotNone(basic_package)
        self.assertEqual(basic_package.plan_type, PlanType.PACKAGE)
        self.assertGreater(basic_package.hours_included, Decimal("0"))
        self.assertGreater(basic_package.price_eur, Decimal("0"))
        self.assertIsNotNone(basic_package.validity_days)
        self.assertTrue(basic_package.is_active)
        
        # Check for a subscription plan
        subscription_plans = PricingPlan.objects.filter(plan_type=PlanType.SUBSCRIPTION)
        self.assertGreater(subscription_plans.count(), 0)
        
        subscription = subscription_plans.first()
        self.assertIsNone(subscription.validity_days)
        self.assertTrue(subscription.is_active)

    def test_create_default_pricing_plans_idempotent(self):
        """Test that running the command multiple times doesn't create duplicates."""
        # Run command first time
        call_command('create_default_pricing_plans')
        first_count = PricingPlan.objects.count()
        
        # Run command second time
        call_command('create_default_pricing_plans')
        second_count = PricingPlan.objects.count()
        
        # Count should be the same (no duplicates created)
        self.assertEqual(first_count, second_count)

    def test_create_default_pricing_plans_validation(self):
        """Test that created plans pass model validation."""
        call_command('create_default_pricing_plans')
        
        # Validate all created plans
        for plan in PricingPlan.objects.all():
            try:
                plan.full_clean()
            except ValidationError as e:
                self.fail(f"Created plan {plan.name} failed validation: {e}")

    def test_create_default_pricing_plans_featured_plans(self):
        """Test that some default plans are marked as featured."""
        call_command('create_default_pricing_plans')
        
        featured_plans = PricingPlan.objects.filter(is_featured=True)
        self.assertGreater(featured_plans.count(), 0)
        
        # Ensure not all plans are featured
        non_featured_plans = PricingPlan.objects.filter(is_featured=False)
        self.assertGreater(non_featured_plans.count(), 0)

    def test_create_default_pricing_plans_display_order(self):
        """Test that default plans have proper display_order values."""
        call_command('create_default_pricing_plans')
        
        plans = PricingPlan.objects.all().order_by('display_order')
        
        # Check that display orders are sequential and start from 1
        for i, plan in enumerate(plans, 1):
            self.assertEqual(plan.display_order, i)

    def test_create_default_pricing_plans_with_force_option(self):
        """Test create_default_pricing_plans command with --force option."""
        # Create a plan manually first
        PricingPlan.objects.create(
            name="Existing Plan",
            description="Already exists",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.0"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_featured=False,
            is_active=True
        )
        
        initial_count = PricingPlan.objects.count()
        
        # Run command with --force option
        call_command('create_default_pricing_plans', '--force')
        
        final_count = PricingPlan.objects.count()
        
        # Should have more plans now (existing + defaults)
        self.assertGreater(final_count, initial_count)

    def test_create_default_pricing_plans_verbose_output(self):
        """Test command verbose output."""
        from io import StringIO
        from django.core.management import call_command
        
        out = StringIO()
        call_command('create_default_pricing_plans', '--verbosity=2', stdout=out)
        
        output = out.getvalue()
        self.assertIn("Creating default pricing plans", output)
        self.assertIn("Successfully created", output)