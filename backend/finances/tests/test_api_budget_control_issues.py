"""
DRF API tests for GitHub issue #170: Family Budget Control Logic bugs.

These tests focus ONLY on the specific failing scenarios mentioned:
- Budget limit enforcement fails: can_auto_approve returns True when should be False
- Permission filtering broken: children see all budget controls instead of 0, parents see all instead of filtered
- Approval request creation fails with HTTP 400

These tests will initially FAIL to establish TDD red state, then pass once bugs are fixed.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from knox.models import AuthToken

from accounts.models import School, ParentChildRelationship, RelationshipType
from finances.models import (
    FamilyBudgetControl,
    PurchaseApprovalRequest,
    PurchaseTransaction,
    PricingPlan,
    TransactionPaymentStatus,
    PurchaseRequestType,
    PlanType,
)

User = get_user_model()


class BudgetControlPermissionFilteringTest(TestCase):
    """
    Test permission filtering bugs in FamilyBudgetControlViewSet.
    
    Failing tests from issue #170:
    - test_child_cannot_access_budget_control: Expected 0 results, got 4
    - test_list_budget_controls_as_parent: Expected 1 result, got 4
    """

    def setUp(self):
        """Set up test data with multiple families and budget controls."""
        # Create schools
        self.school1 = School.objects.create(
            name="School One", description="First school"
        )
        self.school2 = School.objects.create(
            name="School Two", description="Second school"
        )

        # Create Family 1: Parent1 -> Child1
        self.parent1 = User.objects.create_user(
            email="parent1@test.com", name="Parent One"
        )
        self.child1 = User.objects.create_user(
            email="child1@test.com", name="Child One"
        )
        self.relationship1 = ParentChildRelationship.objects.create(
            parent=self.parent1,
            child=self.child1,
            relationship_type=RelationshipType.PARENT,
            school=self.school1
        )

        # Create Family 2: Parent2 -> Child2
        self.parent2 = User.objects.create_user(
            email="parent2@test.com", name="Parent Two"
        )
        self.child2 = User.objects.create_user(
            email="child2@test.com", name="Child Two"
        )
        self.relationship2 = ParentChildRelationship.objects.create(
            parent=self.parent2,
            child=self.child2,
            relationship_type=RelationshipType.PARENT,
            school=self.school2
        )

        # Create Family 3: Parent1 -> Child3 (same parent, different child)
        self.child3 = User.objects.create_user(
            email="child3@test.com", name="Child Three"
        )
        self.relationship3 = ParentChildRelationship.objects.create(
            parent=self.parent1,
            child=self.child3,
            relationship_type=RelationshipType.PARENT,
            school=self.school1
        )

        # Create Family 4: Parent3 -> Child4 (completely separate)
        self.parent3 = User.objects.create_user(
            email="parent3@test.com", name="Parent Three"
        )
        self.child4 = User.objects.create_user(
            email="child4@test.com", name="Child Four"
        )
        self.relationship4 = ParentChildRelationship.objects.create(
            parent=self.parent3,
            child=self.child4,
            relationship_type=RelationshipType.PARENT,
            school=self.school2
        )

        # Create budget controls for all relationships
        self.budget_control1 = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship1,
            monthly_budget_limit=Decimal('100.00'),
            auto_approval_threshold=Decimal('20.00')
        )
        self.budget_control2 = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship2,
            monthly_budget_limit=Decimal('150.00'),
            auto_approval_threshold=Decimal('30.00')
        )
        self.budget_control3 = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship3,
            monthly_budget_limit=Decimal('200.00'),
            auto_approval_threshold=Decimal('25.00')
        )
        self.budget_control4 = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship4,
            monthly_budget_limit=Decimal('80.00'),
            auto_approval_threshold=Decimal('15.00')
        )

        # API clients
        self.parent1_client = APIClient()
        self.parent1_token = AuthToken.objects.create(self.parent1)[1]

        self.child1_client = APIClient()
        self.child1_token = AuthToken.objects.create(self.child1)[1]

    def test_child_cannot_access_budget_control(self):
        """
        Test that child users cannot access ANY budget controls.
        
        FAILING TEST from issue #170:
        Expected 0 results, but currently returns 4 (all budget controls).
        Children should have NO access to budget control endpoints.
        """
        self.child1_client.credentials(HTTP_AUTHORIZATION=f'Token {self.child1_token}')
        
        url = reverse('finances:familybudgetcontrol-list')
        response = self.child1_client.get(url)

        # This test SHOULD PASS but currently FAILS
        # Bug: Currently returns all 4 budget controls instead of 0
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0, 
                        "Child user should not see any budget controls but sees all of them")

    def test_list_budget_controls_as_parent(self):
        """
        Test that parents only see budget controls for THEIR children.
        
        FAILING TEST from issue #170:
        Expected 1 result (only controls for their children), but currently returns 4 (all controls).
        Parent1 should only see budget_control1 and budget_control3 (their 2 children).
        """
        self.parent1_client.credentials(HTTP_AUTHORIZATION=f'Token {self.parent1_token}')
        
        url = reverse('finances:familybudgetcontrol-list')
        response = self.parent1_client.get(url)

        # This test SHOULD PASS but currently FAILS  
        # Bug: Currently returns all 4 budget controls instead of only the parent's 2
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2, 
                        "Parent1 should only see budget controls for their 2 children, not all 4")
        
        # Verify the correct budget controls are returned
        returned_ids = {item['id'] for item in response.data}
        expected_ids = {self.budget_control1.id, self.budget_control3.id}
        self.assertEqual(returned_ids, expected_ids,
                        f"Expected controls {expected_ids}, but got {returned_ids}")


class BudgetLimitEnforcementTest(TestCase):
    """
    Test budget limit enforcement bugs in FamilyBudgetControl.check_budget_limits().
    
    Failing test from issue #170:
    - test_check_budget_limits_exceeds_weekly: Expected can_auto_approve=False, got True
    """

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School", description="A test school"
        )
        self.parent = User.objects.create_user(
            email="parent@test.com", name="Parent User"
        )
        self.child = User.objects.create_user(
            email="child@test.com", name="Child User"
        )
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

        self.client = APIClient()
        self.parent_token = AuthToken.objects.create(self.parent)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.parent_token}')

    def test_check_budget_limits_exceeds_weekly(self):
        """
        Test budget limit check when purchase exceeds weekly limit.
        
        FAILING TEST from issue #170:
        Expected can_auto_approve=False when weekly limit is exceeded, but got True.
        
        Bug: can_auto_approve should be False when budget limits are exceeded, 
        regardless of auto_approval_threshold.
        """
        # Create budget control with weekly limit
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            weekly_budget_limit=Decimal('50.00'),
            auto_approval_threshold=Decimal('30.00')  # Higher than the purchase amount
        )

        # Create existing spending this week that approaches the limit
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type='package',
            amount=Decimal('40.00'),  # 40 + 25 = 65, exceeds 50 weekly limit
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        # Test amount that would exceed weekly limit but is under auto_approval_threshold
        url = reverse('finances:familybudgetcontrol-check-budget-limits', kwargs={'pk': budget_control.id})
        data = {'amount': '25.00'}  # Under threshold but exceeds weekly limit

        response = self.client.post(url, data, format='json')

        # This test SHOULD PASS but currently FAILS
        # Bug: can_auto_approve returns True because amount < auto_approval_threshold
        # But it should be False because the purchase would exceed the weekly budget limit
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['allowed'], 
                        "Purchase should not be allowed as it exceeds weekly budget limit")
        self.assertFalse(response.data['can_auto_approve'], 
                        "Cannot auto-approve when purchase exceeds budget limits, regardless of threshold")
        self.assertGreater(len(response.data['reasons']), 0,
                          "Should have reasons explaining why purchase is not allowed")


class ApprovalRequestCreationTest(TestCase):
    """
    Test approval request creation bugs in PurchaseApprovalRequestViewSet.
    
    Failing test from issue #170:
    - test_create_approval_request_as_child: Expected HTTP 201, got HTTP 400
    """

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School", description="A test school"
        )
        self.parent = User.objects.create_user(
            email="parent@test.com", name="Parent User"
        )
        self.child = User.objects.create_user(
            email="child@test.com", name="Child User"
        )
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

        # Create pricing plan
        self.pricing_plan = PricingPlan.objects.create(
            name="Test Package",
            description="A test hour package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('10.00'),
            price_eur=Decimal('100.00'),
            validity_days=30
        )

        self.child_client = APIClient()
        self.child_token = AuthToken.objects.create(self.child)[1]

    def test_create_approval_request_as_child(self):
        """
        Test creating a purchase approval request as a child user.
        
        FAILING TEST from issue #170:
        Expected HTTP 201 (successful creation), but currently gets HTTP 400.
        
        Bug: Valid approval request data is being rejected with validation errors.
        """
        self.child_client.credentials(HTTP_AUTHORIZATION=f'Token {self.child_token}')

        url = reverse('finances:purchaseapprovalrequest-list')
        data = {
            'student': self.child.id,
            'parent': self.parent.id,
            'parent_child_relationship': self.relationship.id,
            'amount': '100.00',
            'description': 'Request for 10-hour package',
            'request_type': PurchaseRequestType.HOURS,
            'pricing_plan': self.pricing_plan.id
        }

        response = self.child_client.post(url, data, format='json')

        # This test SHOULD PASS but currently FAILS
        # Bug: Returns HTTP 400 instead of HTTP 201 due to validation issues
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                        f"Expected HTTP 201 but got {response.status_code}. Error: {getattr(response, 'data', 'No error data')}")
        self.assertEqual(PurchaseApprovalRequest.objects.count(), 1)
        
        approval_request = PurchaseApprovalRequest.objects.first()
        self.assertEqual(approval_request.student, self.child)
        self.assertEqual(approval_request.parent, self.parent)
        self.assertEqual(approval_request.amount, Decimal('100.00'))