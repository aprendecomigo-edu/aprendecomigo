"""
Django management command to create default pricing plans.

This command creates a set of default pricing plans for the tutoring platform,
including both package and subscription plans with sensible defaults that can
be customized through the Django Admin interface.

Usage:
    python manage.py create_default_pricing_plans
    python manage.py create_default_pricing_plans --force
    python manage.py create_default_pricing_plans --verbosity=2
"""

from decimal import Decimal
from typing import List, Dict, Any

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from finances.models import PricingPlan, PlanType


class Command(BaseCommand):
    """
    Management command to create default pricing plans.
    
    Creates a comprehensive set of default pricing plans including:
    - Various package options with different hour amounts and validity periods
    - Subscription options for regular users
    - Featured plans to highlight recommended options
    """
    
    help = "Create default pricing plans for the tutoring platform"
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Create plans even if some already exist (avoids duplicates)',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            default=True,
            help='Clear pricing plans cache after creation (default: True)',
        )
    
    def handle(self, *args, **options):
        """Main command execution."""
        verbosity = options['verbosity']
        force = options['force']
        clear_cache = options['clear_cache']
        
        if verbosity >= 1:
            self.stdout.write("Creating default pricing plans...")
        
        try:
            with transaction.atomic():
                created_count = self._create_default_plans(force, verbosity)
                
                if clear_cache:
                    self._clear_pricing_cache(verbosity)
                
                if created_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully created {created_count} default pricing plans."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "No new pricing plans were created. Use --force to override existing plans."
                        )
                    )
                    
        except Exception as e:
            raise CommandError(f"Error creating default pricing plans: {e}")
    
    def _create_default_plans(self, force: bool, verbosity: int) -> int:
        """
        Create the default pricing plans.
        
        Args:
            force: Whether to create plans even if some exist
            verbosity: Verbosity level for output
            
        Returns:
            Number of plans actually created
        """
        default_plans = self._get_default_plan_definitions()
        created_count = 0
        
        if not force and PricingPlan.objects.exists():
            if verbosity >= 1:
                self.stdout.write(
                    self.style.WARNING(
                        "Pricing plans already exist. Use --force to create anyway."
                    )
                )
            return 0
        
        for plan_data in default_plans:
            plan_name = plan_data['name']
            
            # Check if plan already exists (by name)
            if PricingPlan.objects.filter(name=plan_name).exists():
                if verbosity >= 2:
                    self.stdout.write(f"Plan '{plan_name}' already exists, skipping...")
                continue
            
            # Create the plan
            plan = PricingPlan.objects.create(**plan_data)
            created_count += 1
            
            if verbosity >= 2:
                self.stdout.write(f"Created plan: {plan.name} - €{plan.price_eur}")
        
        return created_count
    
    def _get_default_plan_definitions(self) -> List[Dict[str, Any]]:
        """
        Define the default pricing plans to create.
        
        Returns:
            List of dictionaries containing plan data
        """
        return [
            # Package Plans
            {
                'name': 'Basic Package',
                'description': 'Perfect for trying out our tutoring services. Includes 5 hours of one-on-one tutoring sessions.',
                'plan_type': PlanType.PACKAGE,
                'hours_included': Decimal('5.00'),
                'price_eur': Decimal('75.00'),
                'validity_days': 30,
                'display_order': 1,
                'is_featured': False,
                'is_active': True,
            },
            {
                'name': 'Standard Package',
                'description': 'Most popular choice! Get 10 hours of personalized tutoring with flexible scheduling.',
                'plan_type': PlanType.PACKAGE,
                'hours_included': Decimal('10.00'),
                'price_eur': Decimal('140.00'),
                'validity_days': 45,
                'display_order': 2,
                'is_featured': True,  # Mark as featured
                'is_active': True,
            },
            {
                'name': 'Premium Package',
                'description': 'Best value for serious students. 20 hours of tutoring with extended validity period.',
                'plan_type': PlanType.PACKAGE,
                'hours_included': Decimal('20.00'),
                'price_eur': Decimal('260.00'),
                'validity_days': 60,
                'display_order': 3,
                'is_featured': False,
                'is_active': True,
            },
            {
                'name': 'Intensive Package',
                'description': 'For exam preparation and intensive learning. 40 hours with maximum flexibility.',
                'plan_type': PlanType.PACKAGE,
                'hours_included': Decimal('40.00'),
                'price_eur': Decimal('480.00'),
                'validity_days': 90,
                'display_order': 4,
                'is_featured': False,
                'is_active': True,
            },
            
            # Subscription Plans
            {
                'name': 'Monthly Unlimited',
                'description': 'Unlimited access to tutoring sessions. Perfect for ongoing academic support.',
                'plan_type': PlanType.SUBSCRIPTION,
                'hours_included': Decimal('30.00'),  # Suggested monthly hours
                'price_eur': Decimal('199.00'),
                'validity_days': None,  # No expiration for subscriptions
                'display_order': 5,
                'is_featured': True,  # Mark as featured
                'is_active': True,
            },
            {
                'name': 'Student Subscription',
                'description': 'Affordable monthly subscription designed for students. Regular academic support.',
                'plan_type': PlanType.SUBSCRIPTION,
                'hours_included': Decimal('15.00'),  # Suggested monthly hours
                'price_eur': Decimal('119.00'),
                'validity_days': None,
                'display_order': 6,
                'is_featured': False,
                'is_active': True,
            },
            {
                'name': 'Family Subscription',
                'description': 'Perfect for multiple students in one family. Share tutoring hours across children.',
                'plan_type': PlanType.SUBSCRIPTION,
                'hours_included': Decimal('50.00'),  # Suggested monthly hours
                'price_eur': Decimal('299.00'),
                'validity_days': None,
                'display_order': 7,
                'is_featured': False,
                'is_active': True,
            },
        ]
    
    def _clear_pricing_cache(self, verbosity: int):
        """
        Clear the pricing plans cache.
        
        Args:
            verbosity: Verbosity level for output
        """
        cache_key = 'active_pricing_plans'
        cache.delete(cache_key)
        
        if verbosity >= 2:
            self.stdout.write("Cleared pricing plans cache.")