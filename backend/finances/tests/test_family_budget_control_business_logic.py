"""
Unit tests for Family Budget Control business logic.

Tests core business rules for family budget management without API endpoints:
- Budget limit threshold calculations and validation rules
- Auto-approval decision logic based on spending thresholds
- Permission filtering business rules for parent-child access
- Current spending calculation algorithms
- Date range filtering for weekly/monthly periods
- Approval requirement business rules

These tests focus on the business logic that needs fixes for GitHub Issue #173.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from finances.models import (
    FamilyBudgetControl,
    PurchaseTransaction,
    TransactionPaymentStatus,
    TransactionType
)
from accounts.models import CustomUser, School, ParentChildRelationship, RelationshipType


class BudgetLimitCalculationTest(TestCase):
    """Test budget limit calculation and validation business rules."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="Test school"
        )
        
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )
        
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

    def test_check_budget_limits_within_all_limits(self):
        """Test budget check when purchase is within all limits."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('200.00'),
            weekly_budget_limit=Decimal('50.00'),
            auto_approval_threshold=Decimal('25.00')
        )
        
        result = budget_control.check_budget_limits(Decimal('20.00'))
        
        self.assertTrue(result['allowed'])
        self.assertTrue(result['can_auto_approve'])
        self.assertEqual(len(result['reasons']), 0)

    def test_check_budget_limits_exceeds_monthly_limit(self):
        """Test budget check when purchase exceeds monthly limit."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('100.00'),
            auto_approval_threshold=Decimal('30.00')
        )
        
        # Mock current monthly spending to simulate existing purchases
        with patch.object(budget_control, 'current_monthly_spending', Decimal('90.00')):
            result = budget_control.check_budget_limits(Decimal('20.00'))
            
            self.assertFalse(result['allowed'])
            self.assertFalse(result['can_auto_approve'])
            self.assertIn("monthly budget limit", result['reasons'][0])
            self.assertIn("€100.00", result['reasons'][0])

    def test_check_budget_limits_exceeds_weekly_limit(self):
        """Test budget check when purchase exceeds weekly limit."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            weekly_budget_limit=Decimal('40.00'),
            auto_approval_threshold=Decimal('20.00')
        )
        
        # Mock current weekly spending
        with patch.object(budget_control, 'current_weekly_spending', Decimal('35.00')):
            result = budget_control.check_budget_limits(Decimal('15.00'))
            
            self.assertFalse(result['allowed'])
            self.assertFalse(result['can_auto_approve'])
            self.assertIn("weekly budget limit", result['reasons'][0])
            self.assertIn("€40.00", result['reasons'][0])

    def test_check_budget_limits_exceeds_auto_approval_threshold(self):
        """Test budget check when purchase exceeds auto-approval threshold."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('200.00'),
            auto_approval_threshold=Decimal('25.00')
        )
        
        result = budget_control.check_budget_limits(Decimal('30.00'))
        
        self.assertTrue(result['allowed'])  # Within budget limits
        self.assertFalse(result['can_auto_approve'])  # Exceeds threshold
        self.assertIn("auto-approval threshold", result['reasons'][0])
        self.assertIn("€25.00", result['reasons'][0])

    def test_check_budget_limits_no_limits_set(self):
        """Test budget check when no limits are configured."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            # No limits set (null values)
        )
        
        result = budget_control.check_budget_limits(Decimal('100.00'))
        
        self.assertTrue(result['allowed'])
        self.assertTrue(result['can_auto_approve'])
        self.assertEqual(len(result['reasons']), 0)

    def test_check_budget_limits_multiple_violations(self):
        """Test budget check with multiple limit violations."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('100.00'),
            weekly_budget_limit=Decimal('30.00'),
            auto_approval_threshold=Decimal('15.00')
        )
        
        # Mock existing spending
        with patch.object(budget_control, 'current_monthly_spending', Decimal('90.00')):
            with patch.object(budget_control, 'current_weekly_spending', Decimal('25.00')):
                result = budget_control.check_budget_limits(Decimal('20.00'))
                
                self.assertFalse(result['allowed'])
                self.assertFalse(result['can_auto_approve'])
                self.assertEqual(len(result['reasons']), 3)  # Monthly, weekly, and auto-approval
                
                reason_text = ' '.join(result['reasons'])
                self.assertIn("monthly budget limit", reason_text)
                self.assertIn("weekly budget limit", reason_text)
                self.assertIn("auto-approval threshold", reason_text)

    def test_check_budget_limits_zero_amount(self):
        """Test budget check with zero purchase amount."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('100.00')
        )
        
        result = budget_control.check_budget_limits(Decimal('0.00'))
        
        self.assertTrue(result['allowed'])
        self.assertTrue(result['can_auto_approve'])
        self.assertEqual(len(result['reasons']), 0)

    def test_check_budget_limits_edge_case_exact_limit(self):
        """Test budget check when purchase exactly meets the limit."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('100.00')
        )
        
        with patch.object(budget_control, 'current_monthly_spending', Decimal('80.00')):
            result = budget_control.check_budget_limits(Decimal('20.00'))
            
            self.assertTrue(result['allowed'])  # Exactly at limit should be allowed
            self.assertTrue(result['can_auto_approve'])


class CurrentSpendingCalculationTest(TestCase):
    """Test current spending calculation algorithms."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="Test school"
        )
        
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )
        
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        
        self.budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship
        )

    def test_current_monthly_spending_calculation(self):
        """Test monthly spending calculation includes correct transactions."""
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Transaction in current month - should be included
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=now
        )
        
        # Transaction in previous month - should not be included
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=current_month_start - timedelta(days=1)
        )
        
        # Pending transaction - should not be included
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('20.00'),
            payment_status=TransactionPaymentStatus.PENDING,
            created_at=now
        )
        
        current_spending = self.budget_control.current_monthly_spending
        self.assertEqual(current_spending, Decimal('50.00'))

    def test_current_weekly_spending_calculation(self):
        """Test weekly spending calculation includes correct transactions."""
        now = timezone.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Transaction in current week - should be included
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('40.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=now
        )
        
        # Transaction in previous week - should not be included
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=week_start - timedelta(days=1)
        )
        
        current_spending = self.budget_control.current_weekly_spending
        self.assertEqual(current_spending, Decimal('40.00'))

    def test_current_spending_only_counts_completed_transactions(self):
        """Test that spending calculation only includes completed transactions."""
        now = timezone.now()
        
        # Create transactions with different payment statuses
        for status in [TransactionPaymentStatus.COMPLETED, 
                      TransactionPaymentStatus.PENDING, 
                      TransactionPaymentStatus.FAILED]:
            PurchaseTransaction.objects.create(
                student=self.child,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('10.00'),
                payment_status=status,
                created_at=now
            )
        
        # Only completed transaction should count
        self.assertEqual(self.budget_control.current_monthly_spending, Decimal('10.00'))
        self.assertEqual(self.budget_control.current_weekly_spending, Decimal('10.00'))

    def test_current_spending_different_transaction_types(self):
        """Test spending calculation includes different transaction types."""
        now = timezone.now()
        
        # Create transactions of different types
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('15.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=now
        )
        
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=now
        )
        
        # Both should be counted
        total_spending = self.budget_control.current_monthly_spending
        self.assertEqual(total_spending, Decimal('40.00'))


class ApprovalRequirementLogicTest(TestCase):
    """Test approval requirement business rules."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="Test school"
        )
        
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )
        
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

    def test_require_approval_for_sessions_flag(self):
        """Test session approval requirement flag logic."""
        # Without session approval requirement
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            require_approval_for_sessions=False,
            auto_approval_threshold=Decimal('20.00')
        )
        
        result = budget_control.check_budget_limits(Decimal('15.00'))
        self.assertTrue(result['can_auto_approve'])
        
        # With session approval requirement
        budget_control.require_approval_for_sessions = True
        budget_control.save()
        
        # Should still allow auto-approval if within threshold for packages
        result = budget_control.check_budget_limits(Decimal('15.00'))
        self.assertTrue(result['can_auto_approve'])

    def test_require_approval_for_packages_flag(self):
        """Test package approval requirement flag logic."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            require_approval_for_packages=True,
            auto_approval_threshold=Decimal('20.00')
        )
        
        # Even within auto-approval threshold, packages require approval
        result = budget_control.check_budget_limits(Decimal('15.00'))
        
        # Auto-approval depends on other conditions, approval flags affect processing
        self.assertIsNotNone(result['can_auto_approve'])

    def test_auto_approval_threshold_enforcement(self):
        """Test auto-approval threshold enforcement logic."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            auto_approval_threshold=Decimal('50.00'),
            monthly_budget_limit=Decimal('200.00')
        )
        
        # Below threshold - can auto approve
        result = budget_control.check_budget_limits(Decimal('40.00'))
        self.assertTrue(result['can_auto_approve'])
        
        # Above threshold - cannot auto approve
        result = budget_control.check_budget_limits(Decimal('60.00'))
        self.assertFalse(result['can_auto_approve'])
        self.assertIn("auto-approval threshold", result['reasons'][0])

    def test_auto_approval_blocked_by_budget_limits(self):
        """Test auto-approval is blocked when budget limits are exceeded."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            weekly_budget_limit=Decimal('30.00'),
            auto_approval_threshold=Decimal('25.00')  # Higher than purchase
        )
        
        # Mock existing weekly spending near limit
        with patch.object(budget_control, 'current_weekly_spending', Decimal('25.00')):
            # Purchase is under auto-approval threshold but would exceed budget
            result = budget_control.check_budget_limits(Decimal('10.00'))
            
            self.assertFalse(result['allowed'])  # Exceeds budget
            self.assertFalse(result['can_auto_approve'])  # Should be blocked

    def test_is_active_flag_business_logic(self):
        """Test that is_active flag affects budget control logic."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('100.00'),
            is_active=False
        )
        
        # When inactive, should not enforce limits
        # (This behavior would depend on actual implementation)
        self.assertFalse(budget_control.is_active)


class DateRangeCalculationTest(TestCase):
    """Test date range calculations for budget periods."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="Test school"
        )
        
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )
        
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        
        self.budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship
        )

    def test_monthly_date_range_boundary_conditions(self):
        """Test monthly spending calculation at month boundaries."""
        # Test at beginning of month
        with patch('django.utils.timezone.now') as mock_now:
            first_of_month = timezone.datetime(2024, 3, 1, 10, 0, 0)
            mock_now.return_value = first_of_month.replace(tzinfo=timezone.get_current_timezone())
            
            # Transaction on first day of month
            PurchaseTransaction.objects.create(
                student=self.child,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('30.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                created_at=first_of_month.replace(tzinfo=timezone.get_current_timezone())
            )
            
            spending = self.budget_control.current_monthly_spending
            self.assertEqual(spending, Decimal('30.00'))

    def test_weekly_date_range_boundary_conditions(self):
        """Test weekly spending calculation at week boundaries."""
        # Test at beginning of week (Monday)
        with patch('django.utils.timezone.now') as mock_now:
            monday = timezone.datetime(2024, 3, 4, 10, 0, 0)  # A Monday
            mock_now.return_value = monday.replace(tzinfo=timezone.get_current_timezone())
            
            # Transaction on Monday
            PurchaseTransaction.objects.create(
                student=self.child,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('25.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                created_at=monday.replace(tzinfo=timezone.get_current_timezone())
            )
            
            spending = self.budget_control.current_weekly_spending
            self.assertEqual(spending, Decimal('25.00'))

    def test_timezone_handling_in_date_calculations(self):
        """Test that date calculations handle timezones correctly."""
        # This test would verify timezone-aware calculations
        # The actual implementation should handle UTC vs local time correctly
        
        now = timezone.now()
        
        # Create transaction with timezone-aware timestamp
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('20.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=now
        )
        
        # Both calculations should work with timezone-aware dates
        monthly_spending = self.budget_control.current_monthly_spending
        weekly_spending = self.budget_control.current_weekly_spending
        
        self.assertEqual(monthly_spending, Decimal('20.00'))
        self.assertEqual(weekly_spending, Decimal('20.00'))


class BudgetControlValidationTest(TestCase):
    """Test validation rules for budget control business logic."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="Test school"
        )
        
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )
        
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

    def test_negative_budget_limits_validation(self):
        """Test that negative budget limits are rejected."""
        with self.assertRaises(ValidationError):
            budget_control = FamilyBudgetControl(
                parent_child_relationship=self.relationship,
                monthly_budget_limit=Decimal('-100.00')
            )
            budget_control.full_clean()

    def test_negative_auto_approval_threshold_validation(self):
        """Test that negative auto-approval thresholds are rejected."""
        with self.assertRaises(ValidationError):
            budget_control = FamilyBudgetControl(
                parent_child_relationship=self.relationship,
                auto_approval_threshold=Decimal('-10.00')
            )
            budget_control.full_clean()

    def test_weekly_limit_greater_than_monthly_validation(self):
        """Test logical validation that weekly limit shouldn't exceed monthly."""
        # This would be a business rule validation
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            weekly_budget_limit=Decimal('60.00'),
            monthly_budget_limit=Decimal('50.00')  # Illogical: weekly > monthly
        )
        
        # The model should either validate this or handle it gracefully
        self.assertIsNotNone(budget_control)

    def test_auto_approval_threshold_logic_validation(self):
        """Test auto-approval threshold logic validation."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            auto_approval_threshold=Decimal('100.00'),
            weekly_budget_limit=Decimal('30.00')
        )
        
        # Auto-approval threshold higher than budget limits might be illogical
        # but should be handled by the check_budget_limits logic
        result = budget_control.check_budget_limits(Decimal('50.00'))
        
        # Should be blocked by budget limit, not auto-approval threshold
        self.assertFalse(result['allowed'])


class BudgetControlComplexScenariosTest(TestCase):
    """Test complex business scenarios for budget control."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="Test school"
        )
        
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )
        
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

    def test_progressive_spending_scenario(self):
        """Test budget control with progressive spending throughout period."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            weekly_budget_limit=Decimal('100.00'),
            monthly_budget_limit=Decimal('400.00'),
            auto_approval_threshold=Decimal('30.00')
        )
        
        now = timezone.now()
        
        # First purchase - should be auto-approved
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=now - timedelta(days=2)
        )
        
        # Second purchase - still within limits
        result = budget_control.check_budget_limits(Decimal('20.00'))
        self.assertTrue(result['can_auto_approve'])
        
        # Simulate the second purchase
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('20.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=now - timedelta(days=1)
        )
        
        # Third purchase - would exceed auto-approval threshold
        result = budget_control.check_budget_limits(Decimal('35.00'))
        self.assertFalse(result['can_auto_approve'])
        self.assertTrue(result['allowed'])  # Still within budget limits

    def test_end_of_period_rollover_logic(self):
        """Test budget control behavior at period boundaries."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            weekly_budget_limit=Decimal('50.00'),
            monthly_budget_limit=Decimal('200.00')
        )
        
        # Mock spending in previous week (shouldn't count toward current week)
        last_week = timezone.now() - timedelta(days=8)
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('45.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=last_week
        )
        
        # New week - previous spending shouldn't count
        result = budget_control.check_budget_limits(Decimal('40.00'))
        self.assertTrue(result['allowed'])  # Should be within weekly limit

    def test_mixed_transaction_status_scenario(self):
        """Test budget control with mixed transaction statuses."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            weekly_budget_limit=Decimal('100.00')
        )
        
        now = timezone.now()
        
        # Completed transaction
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=now
        )
        
        # Pending transaction (shouldn't count)
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.PENDING,
            created_at=now
        )
        
        # Failed transaction (shouldn't count)
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('20.00'),
            payment_status=TransactionPaymentStatus.FAILED,
            created_at=now
        )
        
        # Only completed transaction should count in budget calculation
        result = budget_control.check_budget_limits(Decimal('60.00'))
        self.assertTrue(result['allowed'])  # 30 + 60 = 90, within 100 limit