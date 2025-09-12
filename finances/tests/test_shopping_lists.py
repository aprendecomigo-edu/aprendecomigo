"""
Tests for shopping list functionality.

Tests the ShoppingList and ShoppingListItem models and their integration
with the family budget control system.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import CustomUser, ParentChildRelationship, School
from finances.models import (
    FamilyBudgetControl,
    ShoppingCategory,
    ShoppingItemStatus,
    ShoppingList,
    ShoppingListItem,
)


class ShoppingListModelTests(TestCase):
    """Test ShoppingList model functionality."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            address="Test Address",
            phone_number="+351234567890"
        )
        
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Test Parent",
            phone_number="+351234567891"
        )
        
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Test Child",
            phone_number="+351234567892"
        )
        
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            school=self.school,
            relationship_type="parent"
        )
        
        self.budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal("200.00"),
            weekly_budget_limit=Decimal("50.00"),
        )

    def test_shopping_list_creation(self):
        """Test creating a shopping list."""
        shopping_list = ShoppingList.objects.create(
            family_budget_control=self.budget_control,
            title="Test Shopping List",
            month_year=date.today(),
        )
        
        self.assertEqual(shopping_list.family_budget_control, self.budget_control)
        self.assertEqual(shopping_list.title, "Test Shopping List")
        self.assertEqual(shopping_list.estimated_total, Decimal("0.00"))
        self.assertEqual(shopping_list.actual_total, Decimal("0.00"))
        self.assertFalse(shopping_list.is_completed)

    def test_completion_percentage_calculation(self):
        """Test completion percentage calculation."""
        shopping_list = ShoppingList.objects.create(
            family_budget_control=self.budget_control,
            title="Test List",
            month_year=date.today(),
        )
        
        # No items - should return 0
        self.assertEqual(shopping_list.completion_percentage, 0.0)
        
        # Add some items
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            name="Apples",
            category=ShoppingCategory.FRUITS_VEGETABLES,
            quantity="1 kg",
            estimated_price=Decimal("2.50"),
            status=ShoppingItemStatus.PURCHASED,
        )
        
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            name="Bread",
            category=ShoppingCategory.GRAINS_CEREALS,
            quantity="1 unit",
            estimated_price=Decimal("1.20"),
            status=ShoppingItemStatus.PENDING,
        )
        
        # Should be 50% (1 out of 2 items purchased)
        self.assertEqual(shopping_list.completion_percentage, 50.0)

    def test_budget_remaining_calculation(self):
        """Test budget remaining calculation."""
        shopping_list = ShoppingList.objects.create(
            family_budget_control=self.budget_control,
            title="Test List",
            month_year=date.today(),
            actual_total=Decimal("30.00"),
        )
        
        # Monthly budget is 200, spent 30, so remaining should be 170
        expected_remaining = Decimal("200.00") - Decimal("30.00")
        self.assertEqual(shopping_list.budget_remaining, expected_remaining)


class ShoppingListItemModelTests(TestCase):
    """Test ShoppingListItem model functionality."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School", 
            address="Test Address",
            phone_number="+351234567890"
        )
        
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Test Parent",
            phone_number="+351234567891"
        )
        
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Test Child", 
            phone_number="+351234567892"
        )
        
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            school=self.school,
            relationship_type="parent"
        )
        
        self.budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal("200.00"),
        )
        
        self.shopping_list = ShoppingList.objects.create(
            family_budget_control=self.budget_control,
            title="Test List",
            month_year=date.today(),
        )

    def test_shopping_item_creation(self):
        """Test creating shopping list items."""
        item = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            name="Maçãs",
            category=ShoppingCategory.FRUITS_VEGETABLES,
            quantity="1 kg",
            estimated_price=Decimal("2.50"),
            health_benefits="Rica em fibra e vitaminas",
        )
        
        self.assertEqual(item.name, "Maçãs")
        self.assertEqual(item.category, ShoppingCategory.FRUITS_VEGETABLES)
        self.assertEqual(item.status, ShoppingItemStatus.PENDING)
        self.assertIsNone(item.actual_price)

    def test_mark_purchased(self):
        """Test marking an item as purchased."""
        item = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            name="Bread",
            category=ShoppingCategory.GRAINS_CEREALS,
            quantity="1 unit",
            estimated_price=Decimal("1.20"),
        )
        
        item.mark_purchased(Decimal("1.30"))
        
        item.refresh_from_db()
        self.assertEqual(item.status, ShoppingItemStatus.PURCHASED)
        self.assertEqual(item.actual_price, Decimal("1.30"))

    def test_mark_skipped(self):
        """Test marking an item as skipped."""
        item = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            name="Chocolate",
            category=ShoppingCategory.HEALTHY_SNACKS,
            quantity="1 bar",
            estimated_price=Decimal("2.00"),
        )
        
        item.mark_skipped("Too expensive")
        
        item.refresh_from_db()
        self.assertEqual(item.status, ShoppingItemStatus.SKIPPED)
        self.assertIn("Skipped: Too expensive", item.notes)