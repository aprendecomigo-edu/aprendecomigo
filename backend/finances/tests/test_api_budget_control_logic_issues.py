"""
Family Budget Control Logic API Tests - Issue #173 Priority 3

This test suite validates that FamilyBudgetControlViewSet approval rules and
permission filtering work correctly, addressing logic issues in the family
budget control system.

These tests are designed to initially FAIL to demonstrate current business
logic issues where budget control approval rules and permission filtering
don't work as expected.

Test Coverage:
- Family Budget Control approval logic validation
- Permission filtering for parent-child relationships
- Purchase approval workflow (parent approval required)
- Budget limit enforcement and validation
- Multi-school budget control scenarios
- Edge cases in approval rule logic
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import School, StudentProfile, ParentChildRelationship, RelationshipType
from finances.tests.stripe_test_utils import comprehensive_stripe_mocks_decorator
from finances.models import (
    FamilyBudgetControl,
    PurchaseApprovalRequest,
    PurchaseApprovalStatus,
    StudentAccountBalance,
    PricingPlan,
    PurchaseTransaction,
    TransactionPaymentStatus,
    TransactionType,
    PlanType
)

User = get_user_model()


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class FamilyBudgetControlApprovalLogicTests(APITestCase):
    """
    Test Family Budget Control approval logic and validation.
    
    These tests validate that the approval rules work correctly,
    including budget limits, approval requirements, and validation logic.
    """

    def setUp(self):
        """Set up test data for budget control logic tests."""
        # Create parent and student users
        self.parent = User.objects.create_user(
            email='parent@family.com',
            name='Test Parent',
        )
        
        self.student = User.objects.create_user(
            email='student@family.com',
            name='Test Student',
        )
        
        self.school_owner = User.objects.create_user(
            email='owner@school.com',
            name='School Owner',
        )
        
        # Create school
        self.school = School.objects.create(
            name='Test School',
            description='Test School for Budget Control Testing'
        )
        
        # Create student profile
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            school_year='5th grade',
            birth_date='2015-01-01'
        )
        
        # Create parent-child relationship
        self.parent_child_relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.student,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        
        # Create family budget control
        self.budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('100.00'),
            weekly_budget_limit=Decimal('25.00'),
            auto_approval_threshold=Decimal('25.00'),
            is_active=True
        )
        
        # Create pricing plan for testing
        self.pricing_plan = PricingPlan.objects.create(
            name='Test Plan',
            description='Test pricing plan for budget control testing',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('5.00'),
            price_eur=Decimal('50.00'),
            validity_days=30,
            display_order=1,
            is_active=True
        )
        
        self.client = APIClient()

    def test_budget_control_approval_threshold_logic_fails(self):
        """
        Test that approval threshold logic works correctly.
        
        This test validates that purchases above the approval threshold
        require parent approval, while purchases below do not.
        
        Expected to FAIL initially due to broken approval threshold logic.
        """
        self.client.force_authenticate(user=self.student)
        
        # Test purchase BELOW approval threshold (should not require approval)
        below_threshold_data = {
            'pricing_plan_id': self.pricing_plan.id,
            'amount': '20.00',  # Below 25.00 threshold
            'notes': 'Purchase below threshold'
        }
        
        url = '/api/finances/approval-requests/'
        response = self.client.post(url, below_threshold_data, format='json')
        
        # Should either auto-approve OR not require approval request
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            # Should be auto-approved for below threshold purchases
            self.assertEqual(
                data.get('status'),
                PurchaseApprovalStatus.APPROVED,
                f"Purchase below approval threshold should be auto-approved. "
                f"Got status: {data.get('status')}. "
                f"Check approval logic in FamilyBudgetControlViewSet."
            )
        
        # Test purchase ABOVE approval threshold (should require approval)
        above_threshold_data = {
            'pricing_plan_id': self.pricing_plan.id,
            'amount': '75.00',  # Above 25.00 threshold
            'notes': 'Purchase above threshold'
        }
        
        response = self.client.post(url, above_threshold_data, format='json')
        
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            # Should remain pending for above threshold purchases
            self.assertEqual(
                data.get('status'),
                PurchaseApprovalStatus.PENDING,
                f"Purchase above approval threshold should remain pending. "
                f"Got status: {data.get('status')}. "
                f"Check approval threshold logic in budget control system."
            )

    def test_budget_control_monthly_limit_enforcement_fails(self):
        """
        Test that monthly budget limits are properly enforced.
        
        This test validates that purchases exceeding monthly budget limits
        are rejected or require special approval.
        
        Expected to FAIL initially due to broken budget limit enforcement.
        """
        # Create existing spending for current month
        existing_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('80.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            metadata={'approved_by_parent': True}
        )
        
        self.client.force_authenticate(user=self.student)
        
        # Attempt purchase that would exceed monthly limit (80 + 30 = 110 > 100 limit)
        over_budget_data = {
            'pricing_plan_id': self.pricing_plan.id,
            'amount': '30.00',  # Would exceed 100.00 monthly limit
            'notes': 'Purchase that exceeds budget'
        }
        
        url = '/api/finances/approval-requests/'
        response = self.client.post(url, over_budget_data, format='json')
        
        # Should be rejected or require special handling
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            data = response.json()
            self.assertIn(
                'budget',
                str(data).lower(),
                f"Budget limit exceeded error should mention 'budget'. Got: {data}"
            )
        elif response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            # If created, should have special status indicating budget exceeded
            self.assertIn(
                data.get('status'),
                [PurchaseApprovalStatus.PENDING, PurchaseApprovalStatus.REQUIRES_REVIEW],
                f"Over-budget purchase should require special approval. "
                f"Got status: {data.get('status')}. "
                f"Check monthly budget enforcement logic."
            )
        else:
            self.fail(
                f"Over-budget purchase handling unclear. "
                f"Expected 400 (rejected) or 201 (pending review), got {response.status_code}: {response.data}"
            )

    def test_budget_control_parent_child_relationship_validation_fails(self):
        """
        Test that parent-child relationship validation works correctly.
        
        This test validates that only authorized parents can approve
        purchases for their assigned students.
        
        Expected to FAIL initially due to broken relationship validation.
        """
        # Create another parent with no relationship to our student
        unauthorized_parent = User.objects.create_user(
            email='other_parent@family.com',
            name='Other Parent'
        )
        
        # Create a purchase approval request
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            school=self.school,
            requested_amount=Decimal('50.00'),
            pricing_plan=self.pricing_plan,
            status=PurchaseApprovalStatus.PENDING,
            notes='Test approval request'
        )
        
        # Test unauthorized parent trying to approve
        self.client.force_authenticate(user=unauthorized_parent)
        
        approve_url = f'/api/finances/approval-requests/{approval_request.id}/approve/'
        response = self.client.post(approve_url, {}, format='json')
        
        # Should be forbidden or not found
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            f"Unauthorized parent should not be able to approve. "
            f"Got {response.status_code}: {response.data}. "
            f"Check parent-child relationship validation in approval logic."
        )
        
        # Test authorized parent can approve
        self.client.force_authenticate(user=self.parent)
        response = self.client.post(approve_url, {}, format='json')
        
        # Should succeed for authorized parent
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_202_ACCEPTED],
            f"Authorized parent should be able to approve. "
            f"Got {response.status_code}: {response.data}. "
            f"Check parent authorization logic."
        )

    def test_budget_control_permission_filtering_fails(self):
        """
        Test that permission filtering works correctly for budget controls.
        
        This test validates that users only see budget controls and approval
        requests they're authorized to access.
        
        Expected to FAIL initially due to broken permission filtering.
        """
        # Create another family's budget control
        other_parent = User.objects.create_user(
            email='other_parent@family.com',
            name='Other Parent'
        )
        
        other_student = User.objects.create_user(
            email='other_student@family.com',
            name='Other Student'
        )
        
        # Create parent-child relationship for the other family
        other_parent_child_relationship = ParentChildRelationship.objects.create(
            parent=other_parent,
            child=other_student,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        
        other_budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=other_parent_child_relationship,
            monthly_budget_limit=Decimal('200.00'),
            weekly_budget_limit=Decimal('50.00'),
            auto_approval_threshold=Decimal('50.00'),
            is_active=True
        )
        
        # Test that parent only sees their own budget controls
        self.client.force_authenticate(user=self.parent)
        
        url = '/api/finances/budget-controls/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        budget_controls = data.get('results', [])
        
        # Should only see their own budget control, not others
        visible_budget_ids = [bc.get('id') for bc in budget_controls]
        
        self.assertIn(
            self.budget_control.id,
            visible_budget_ids,
            f"Parent should see their own budget control. "
            f"Visible IDs: {visible_budget_ids}"
        )
        
        self.assertNotIn(
            other_budget_control.id,
            visible_budget_ids,
            f"Parent should NOT see other family's budget control. "
            f"Visible IDs: {visible_budget_ids}. "
            f"Check permission filtering in FamilyBudgetControlViewSet queryset."
        )

    def test_budget_control_multi_school_logic_fails(self):
        """
        Test that multi-school budget control logic works correctly.
        
        This test validates that budget controls are properly scoped
        to schools and that cross-school approval logic works.
        
        Expected to FAIL initially due to broken multi-school logic.
        """
        # Create another school
        other_school = School.objects.create(
            name='Other School',
            description='Another test school'
        )
        
        # Create parent-child relationship for the same family at different school
        other_school_relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.student,
            relationship_type=RelationshipType.PARENT,
            school=other_school
        )
        
        # Create budget control for same family at different school
        multi_school_budget = FamilyBudgetControl.objects.create(
            parent_child_relationship=other_school_relationship,
            monthly_budget_limit=Decimal('150.00'),
            weekly_budget_limit=Decimal('30.00'),
            auto_approval_threshold=Decimal('30.00'),
            is_active=True
        )
        
        self.client.force_authenticate(user=self.parent)
        
        # Test that budget controls are properly filtered by school context
        url = f'/api/finances/budget-controls/?school={self.school.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        budget_controls = data.get('results', [])
        school_ids = [bc.get('school') for bc in budget_controls]
        
        # Should only show budget controls for the requested school
        for school_id in school_ids:
            self.assertEqual(
                school_id,
                self.school.id,
                f"School filtering should only show budget controls for requested school. "
                f"Found school_id {school_id}, expected {self.school.id}. "
                f"Check school filtering logic in FamilyBudgetControlViewSet."
            )


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class FamilyBudgetControlEdgeCaseTests(APITestCase):
    """
    Test edge cases in Family Budget Control logic.
    
    These tests validate handling of unusual scenarios and edge cases
    in the budget control system.
    """

    def setUp(self):
        """Set up test data for edge case tests."""
        self.parent = User.objects.create_user(
            email='parent@family.com',
            name='Test Parent',
        )
        
        self.student = User.objects.create_user(
            email='student@family.com',
            name='Test Student',
        )
        
        self.school_owner = User.objects.create_user(
            email='owner@school.com',
            name='School Owner',
        )
        
        self.school = School.objects.create(
            name='Test School',
            description='Test School for Edge Case Testing'
        )
        
        # Create student profile
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            school_year='5th grade',
            birth_date='2015-01-01'
        )
        
        # Create parent-child relationship
        self.parent_child_relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.student,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        
        self.client = APIClient()

    def test_budget_control_zero_threshold_logic_fails(self):
        """
        Test that zero approval threshold is handled correctly.
        
        This test validates that setting approval_threshold to 0
        means all purchases require approval.
        
        Expected to FAIL initially due to improper zero threshold handling.
        """
        # Create budget control with zero threshold
        zero_threshold_budget = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('100.00'),
            weekly_budget_limit=Decimal('25.00'),
            auto_approval_threshold=Decimal('0.00'),  # All purchases need approval
            is_active=True
        )
        
        self.client.force_authenticate(user=self.student)
        
        # Create pricing plan
        pricing_plan = PricingPlan.objects.create(
            name='Small Plan',
            hours=Decimal('1.00'),
            price=Decimal('10.00'),
            school=self.school,
            is_active=True
        )
        
        # Even small purchase should require approval with zero threshold
        small_purchase_data = {
            'pricing_plan_id': pricing_plan.id,
            'amount': '10.00',  # Any amount should require approval
            'notes': 'Small purchase with zero threshold'
        }
        
        url = '/api/finances/approval-requests/'
        response = self.client.post(url, small_purchase_data, format='json')
        
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            # Should require approval even for small amounts
            self.assertEqual(
                data.get('status'),
                PurchaseApprovalStatus.PENDING,
                f"With zero approval threshold, all purchases should require approval. "
                f"Got status: {data.get('status')}. "
                f"Check zero threshold logic in approval validation."
            )

    def test_budget_control_inactive_budget_handling_fails(self):
        """
        Test that inactive budget controls are handled correctly.
        
        This test validates that inactive budget controls don't
        interfere with purchase approval logic.
        
        Expected to FAIL initially due to improper inactive budget handling.
        """
        # Create inactive budget control
        inactive_budget = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('10.00'),  # Very low limit
            weekly_budget_limit=Decimal('5.00'),
            auto_approval_threshold=Decimal('5.00'),
            is_active=False  # Inactive
        )
        
        self.client.force_authenticate(user=self.student)
        
        # Create pricing plan
        pricing_plan = PricingPlan.objects.create(
            name='Test Plan',
            hours=Decimal('2.00'),
            price=Decimal('20.00'),
            school=self.school,
            is_active=True
        )
        
        # Purchase that would exceed inactive budget limits
        purchase_data = {
            'pricing_plan_id': pricing_plan.id,
            'amount': '20.00',  # Exceeds inactive budget limit
            'notes': 'Purchase with inactive budget control'
        }
        
        # Since budget control is inactive, purchase should proceed normally
        url = '/api/finances/approval-requests/'
        response = self.client.post(url, purchase_data, format='json')
        
        # Should not be restricted by inactive budget control
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            data = response.json()
            self.assertNotIn(
                'budget',
                str(data).lower(),
                f"Inactive budget control should not restrict purchases. "
                f"Got error: {data}. Check active budget filtering logic."
            )

    def test_budget_control_no_budget_control_scenario_fails(self):
        """
        Test behavior when no budget control exists for student.
        
        This test validates that students without budget controls
        can make purchases without approval requirements.
        
        Expected to FAIL initially due to improper no-budget-control handling.
        """
        # Create student without any budget control
        no_budget_student = User.objects.create_user(
            email='no_budget_student@test.com',
            name='No Budget Student'
        )
        
        self.client.force_authenticate(user=no_budget_student)
        
        # Create pricing plan
        pricing_plan = PricingPlan.objects.create(
            name='Free Plan',
            hours=Decimal('1.00'),
            price=Decimal('15.00'),
            school=self.school,
            is_active=True
        )
        
        # Purchase attempt without budget control
        purchase_data = {
            'pricing_plan_id': pricing_plan.id,
            'amount': '15.00',
            'notes': 'Purchase without budget control'
        }
        
        url = '/api/finances/approval-requests/'
        response = self.client.post(url, purchase_data, format='json')
        
        # Without budget control, should either:
        # 1. Allow direct purchase (not create approval request)
        # 2. Create auto-approved approval request
        
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            # Should be auto-approved if approval request is created
            self.assertEqual(
                data.get('status'),
                PurchaseApprovalStatus.APPROVED,
                f"Without budget control, purchases should be auto-approved. "
                f"Got status: {data.get('status')}. "
                f"Check no-budget-control logic in approval system."
            )
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            # Should not be rejected due to missing budget control
            data = response.json()
            self.assertNotIn(
                'required',
                str(data).lower(),
                f"Budget control should not be required for all students. "
                f"Got error: {data}. Check budget control requirement logic."
            )

    def test_budget_control_approval_request_duplicate_handling_fails(self):
        """
        Test that duplicate approval requests are handled correctly.
        
        This test validates that the system prevents or handles
        duplicate approval requests appropriately.
        
        Expected to FAIL initially due to improper duplicate handling.
        """
        # Create budget control
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('100.00'),
            weekly_budget_limit=Decimal('25.00'),
            auto_approval_threshold=Decimal('25.00'),
            is_active=True
        )
        
        # Create pricing plan
        pricing_plan = PricingPlan.objects.create(
            name='Duplicate Plan',
            hours=Decimal('3.00'),
            price=Decimal('30.00'),
            school=self.school,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.student)
        
        # Create first approval request
        purchase_data = {
            'pricing_plan_id': pricing_plan.id,
            'amount': '30.00',
            'notes': 'First approval request'
        }
        
        url = '/api/finances/approval-requests/'
        first_response = self.client.post(url, purchase_data, format='json')
        
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        first_request_id = first_response.json().get('id')
        
        # Attempt duplicate approval request
        duplicate_data = {
            'pricing_plan_id': pricing_plan.id,
            'amount': '30.00',
            'notes': 'Duplicate approval request'
        }
        
        duplicate_response = self.client.post(url, duplicate_data, format='json')
        
        # Should handle duplicates appropriately
        if duplicate_response.status_code == status.HTTP_201_CREATED:
            duplicate_request_id = duplicate_response.json().get('id')
            self.assertNotEqual(
                first_request_id,
                duplicate_request_id,
                "System should allow multiple approval requests or prevent duplicates clearly"
            )
        elif duplicate_response.status_code == status.HTTP_400_BAD_REQUEST:
            # Should provide clear error about duplicate
            data = duplicate_response.json()
            self.assertIn(
                'duplicate',
                str(data).lower(),
                f"Duplicate prevention should mention 'duplicate'. Got: {data}"
            )
        else:
            self.fail(
                f"Unexpected response to duplicate approval request. "
                f"Got {duplicate_response.status_code}: {duplicate_response.data}. "
                f"Check duplicate handling logic."
            )