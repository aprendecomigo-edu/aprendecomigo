"""
Consolidated test suite for Approval and Budget Control API endpoints.

This module contains focused tests for:
- Family budget control management
- Purchase approval request workflows
- Parent-child relationship validation
- Budget limit enforcement
- Approval status transitions

Focuses on approval business logic and budget constraint validation.
"""

import json
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from knox.models import AuthToken

from accounts.models import School, ParentChildRelationship, RelationshipType
from finances.models import (
    FamilyBudgetControl,
    PurchaseApprovalRequest,
    PurchaseTransaction,
    PricingPlan,
    TransactionPaymentStatus,
    TransactionType,
    PurchaseRequestType,
    PurchaseApprovalStatus,
    PlanType,
)
from finances.tests.base import FinanceBaseTestCase
from finances.tests.stripe_test_utils import comprehensive_stripe_mocks_decorator

User = get_user_model()


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class ApprovalAPITestCase(FinanceBaseTestCase, APITestCase):
    """Base test case with common setup for approval API tests."""

    def setUp(self):
        """Set up test data common to all approval API tests."""
        super().setUp()
        
        # Use existing fixtures from base class
        # parent_user, student_user, and parent_child_relationship are already available
        self.parent = self.parent_user
        self.child = self.student_user
        
        self.other_parent = User.objects.create_user(
            email="other_parent@test.com",
            name="Other Parent"
        )

        # Use existing parent-child relationship from base class
        self.parent_child_relationship = self.parent_child_relationship

        # Use existing pricing plan from base class
        # self.pricing_plan already exists from base class

        # Create API tokens
        self.parent_token = AuthToken.objects.create(self.parent)[1]
        self.child_token = AuthToken.objects.create(self.child)[1]
        self.other_parent_token = AuthToken.objects.create(self.other_parent)[1]

    def authenticate_as_parent(self):
        """Authenticate client as parent."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.parent_token}')

    def authenticate_as_child(self):
        """Authenticate client as child."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.child_token}')

    def authenticate_as_other_parent(self):
        """Authenticate client as other parent."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_parent_token}')


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class FamilyBudgetControlAPITests(ApprovalAPITestCase):
    """Test cases for Family Budget Control management."""

    def test_create_budget_control_as_parent(self):
        """Test parent can create budget control with proper validation."""
        # First, delete any existing budget control from fixtures
        FamilyBudgetControl.objects.filter(
            parent_child_relationship=self.parent_child_relationship
        ).delete()
        
        self.authenticate_as_parent()
        url = reverse('finances:familybudgetcontrol-list')
        
        data = {
            'parent_child_relationship': self.parent_child_relationship.id,
            'monthly_budget_limit': '200.00',
            'weekly_budget_limit': '50.00',
            'auto_approval_threshold': '20.00',
            'require_approval_for_sessions': True,
            'require_approval_for_packages': True,
            'is_active': True
        }

        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FamilyBudgetControl.objects.count(), 1)
        
        budget_control = FamilyBudgetControl.objects.first()
        self.assertEqual(budget_control.monthly_budget_limit, Decimal('200.00'))
        self.assertEqual(budget_control.auto_approval_threshold, Decimal('20.00'))
        self.assertTrue(budget_control.require_approval_for_packages)

    def test_list_budget_controls_filtered_by_parent(self):
        """Test parent only sees their own budget controls."""
        # Use or create budget control for this parent
        budget_control, created = FamilyBudgetControl.objects.get_or_create(
            parent_child_relationship=self.parent_child_relationship,
            defaults={
                'monthly_budget_limit': Decimal('200.00'),
                'auto_approval_threshold': Decimal('20.00')
            }
        )
        
        # Create another parent-child relationship with budget control
        other_relationship = ParentChildRelationship.objects.create(
            parent=self.other_parent,
            child=User.objects.create_user(email="other_child@test.com", name="Other Child"),
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        FamilyBudgetControl.objects.create(
            parent_child_relationship=other_relationship,
            monthly_budget_limit=Decimal('150.00')
        )

        self.authenticate_as_parent()
        url = reverse('finances:familybudgetcontrol-list')
        
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], budget_control.id)
        self.assertEqual(response.data[0]['child_name'], 'Test Student')

    def test_update_budget_control_limits(self):
        """Test updating budget control limits and thresholds."""
        budget_control, created = FamilyBudgetControl.objects.get_or_create(
            parent_child_relationship=self.parent_child_relationship,
            defaults={
                'monthly_budget_limit': Decimal('200.00'),
                'auto_approval_threshold': Decimal('20.00')
            }
        )

        self.authenticate_as_parent()
        url = reverse('finances:familybudgetcontrol-detail', kwargs={'pk': budget_control.id})
        
        data = {
            'monthly_budget_limit': '300.00',
            'auto_approval_threshold': '25.00',
            'require_approval_for_sessions': False
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        budget_control.refresh_from_db()
        self.assertEqual(budget_control.monthly_budget_limit, Decimal('300.00'))
        self.assertEqual(budget_control.auto_approval_threshold, Decimal('25.00'))
        self.assertFalse(budget_control.require_approval_for_sessions)

    def test_budget_limit_validation_logic(self):
        """Test budget limit checking with existing spending."""
        # Use or update the existing budget control from fixtures
        try:
            budget_control = FamilyBudgetControl.objects.get(
                parent_child_relationship=self.parent_child_relationship
            )
            # Update it with test values
            budget_control.monthly_budget_limit = Decimal('200.00')
            budget_control.weekly_budget_limit = None  # Remove weekly limit for this test
            budget_control.auto_approval_threshold = Decimal('20.00')
            budget_control.save()
        except FamilyBudgetControl.DoesNotExist:
            budget_control = FamilyBudgetControl.objects.create(
                parent_child_relationship=self.parent_child_relationship,
                monthly_budget_limit=Decimal('200.00'),
                weekly_budget_limit=None,  # No weekly limit for this test
                auto_approval_threshold=Decimal('20.00')
            )
        
        # Clear any existing transactions and create specific test spending
        PurchaseTransaction.objects.filter(student=self.child).delete()
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('150.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=timezone.now()
        )

        self.authenticate_as_parent()
        url = reverse('finances:familybudgetcontrol-check-budget-limits', 
                     kwargs={'pk': budget_control.id})
        
        # Test amount within remaining budget
        response = self.client.post(url, {'amount': '40.00'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['allowed'])
        self.assertFalse(response.data['can_auto_approve'])  # Exceeds auto approval threshold
        
        # Test amount exceeding budget
        response = self.client.post(url, {'amount': '100.00'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['allowed'])
        self.assertIn('budget limit', ' '.join(response.data['reasons']).lower())

    def test_child_cannot_modify_budget_controls(self):
        """Test child users cannot create or modify budget controls."""
        self.authenticate_as_child()
        url = reverse('finances:familybudgetcontrol-list')
        
        data = {
            'parent_child_relationship': self.parent_child_relationship.id,
            'monthly_budget_limit': '100.00'
        }

        response = self.client.post(url, data, format='json')
        
        # Should be forbidden, bad request (validation), or return empty list
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(len(response.data), 0)


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PurchaseApprovalRequestAPITests(ApprovalAPITestCase):
    """Test cases for Purchase Approval Request workflows."""

    def test_create_approval_request_as_child(self):
        """Test child can create purchase approval request."""
        self.authenticate_as_child()
        url = reverse('finances:purchaseapprovalrequest-list')
        
        data = {
            'student': self.child.id,
            'parent': self.parent.id,
            'parent_child_relationship': self.parent_child_relationship.id,
            'amount': '100.00',
            'description': 'Request for 10-hour package',
            'request_type': PurchaseRequestType.HOURS,
            'pricing_plan': self.pricing_plan.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        approval_request = PurchaseApprovalRequest.objects.first()
        self.assertEqual(approval_request.student, self.child)
        self.assertEqual(approval_request.parent, self.parent)
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.PENDING)
        self.assertEqual(approval_request.amount, Decimal('100.00'))

    def test_parent_list_pending_approval_requests(self):
        """Test parent can list their pending approval requests."""
        # Clear existing requests and create specific test requests
        PurchaseApprovalRequest.objects.all().delete()
        
        # Create approval requests
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Request for tutoring hours',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )
        
        # Create request for other parent (should not appear)
        other_child = User.objects.create_user(email="other_child@test.com", name="Other Child")
        other_relationship = ParentChildRelationship.objects.create(
            parent=self.other_parent,
            child=other_child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        PurchaseApprovalRequest.objects.create(
            student=other_child,
            parent=self.other_parent,
            parent_child_relationship=other_relationship,
            amount=Decimal('50.00'),
            description='Other request',
            request_type=PurchaseRequestType.HOURS
        )

        self.authenticate_as_parent()
        url = reverse('finances:purchaseapprovalrequest-list')
        
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data_to_check = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data_to_check), 1)
        self.assertEqual(data_to_check[0]['id'], approval_request.id)
        self.assertEqual(data_to_check[0]['student_name'], 'Test Student')

    def test_approve_purchase_request(self):
        """Test parent can approve purchase request with validation."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Request for 10-hour package',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        self.authenticate_as_parent()
        url = reverse('finances:purchaseapprovalrequest-approve', 
                     kwargs={'pk': approval_request.id})
        
        data = {
            'action': 'approve',
            'parent_notes': 'Approved for educational purposes'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.APPROVED)
        self.assertEqual(approval_request.parent_notes, 'Approved for educational purposes')
        self.assertIsNotNone(approval_request.responded_at)

    def test_deny_purchase_request_with_reason(self):
        """Test parent can deny purchase request with reason."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Request for 10-hour package',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        self.authenticate_as_parent()
        url = reverse('finances:purchaseapprovalrequest-approve', 
                     kwargs={'pk': approval_request.id})
        
        data = {
            'action': 'deny',
            'parent_notes': 'Too expensive this month, try again next month'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.DENIED)
        self.assertIn('too expensive', approval_request.parent_notes.lower())

    def test_child_cancel_own_request(self):
        """Test child can cancel their own pending request."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Request for 10-hour package',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        self.authenticate_as_child()
        url = reverse('finances:purchaseapprovalrequest-cancel', 
                     kwargs={'pk': approval_request.id})
        
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.CANCELLED)

    def test_filter_approval_requests_by_status(self):
        """Test filtering approval requests by status."""
        # Clear existing requests and create specific test requests
        PurchaseApprovalRequest.objects.all().delete()
        
        # Create requests with different statuses
        pending_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Pending request',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        approved_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('50.00'),
            description='Approved request',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )
        approved_request.approve()

        self.authenticate_as_parent()
        url = reverse('finances:purchaseapprovalrequest-list')
        
        # Test filtering by pending status
        response = self.client.get(url, {'status': 'pending'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Use correct data structure for assertion
        data_to_check = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data_to_check), 1)
        self.assertEqual(data_to_check[0]['id'], pending_request.id)
        
        # Test filtering by approved status
        response = self.client.get(url, {'status': 'approved'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data_to_check_approved = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data_to_check_approved), 1)
        self.assertEqual(data_to_check_approved[0]['id'], approved_request.id)


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class StudentPurchaseRequestAPITests(ApprovalAPITestCase):
    """Test cases for Student Purchase Request workflow."""

    def setUp(self):
        """Set up budget control for auto-approval testing."""
        super().setUp()
        
        # Use or create budget control with auto approval threshold
        self.budget_control, created = FamilyBudgetControl.objects.get_or_create(
            parent_child_relationship=self.parent_child_relationship,
            defaults={
                'monthly_budget_limit': Decimal('200.00'),
                'auto_approval_threshold': Decimal('50.00'),
                'require_approval_for_packages': True
            }
        )
        
        # Create small pricing plan for auto approval
        self.small_plan = PricingPlan.objects.create(
            name="Small Package",
            description="A small hour package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('5.00'),
            price_eur=Decimal('40.00'),
            validity_days=30,
            is_active=True
        )

    def test_auto_approved_purchase_request(self):
        """Test purchase request gets auto-approved when below threshold."""
        # Clear existing approval requests and transactions from fixtures
        PurchaseApprovalRequest.objects.all().delete()
        PurchaseTransaction.objects.filter(student=self.child).delete()
        
        # Ensure budget control allows the test amount
        self.budget_control.monthly_budget_limit = Decimal('200.00')
        self.budget_control.weekly_budget_limit = Decimal('100.00')  # Higher than test amount
        self.budget_control.auto_approval_threshold = Decimal('50.00')  # Higher than test amount
        self.budget_control.save()
        
        self.authenticate_as_child()
        url = reverse('finances:student-purchase-request')
        
        data = {
            'amount': '40.00',
            'description': 'Request for small hour package',
            'request_type': 'hours',
            'pricing_plan_id': self.small_plan.id,
            'parent_id': self.parent.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['auto_approved'])
        
        # Verify request was automatically approved
        approval_request = PurchaseApprovalRequest.objects.first()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.APPROVED)

    def test_manual_approval_required_for_large_amount(self):
        """Test large purchase request requires manual approval."""
        # Clear existing approval requests and transactions from fixtures
        PurchaseApprovalRequest.objects.all().delete()
        PurchaseTransaction.objects.filter(student=self.child).delete()
        
        # Ensure budget control allows the large amount but requires manual approval
        self.budget_control.monthly_budget_limit = Decimal('300.00')  # Allow the purchase
        self.budget_control.weekly_budget_limit = Decimal('200.00')   # Allow the purchase
        self.budget_control.auto_approval_threshold = Decimal('50.00')  # Below the test amount so manual approval needed
        self.budget_control.save()
        
        # Create expensive plan
        expensive_plan = PricingPlan.objects.create(
            name="Large Package",
            description="A large hour package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('20.00'),
            price_eur=Decimal('150.00'),
            validity_days=30,
            is_active=True
        )

        self.authenticate_as_child()
        url = reverse('finances:student-purchase-request')
        
        data = {
            'amount': '150.00',
            'description': 'Request for large hour package',
            'request_type': 'hours',
            'pricing_plan_id': expensive_plan.id,
            'parent_id': self.parent.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['auto_approved'])
        
        # Verify request is pending approval
        approval_request = PurchaseApprovalRequest.objects.first()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.PENDING)

    def test_budget_limit_enforcement(self):
        """Test purchase request rejected when exceeding budget limits."""
        # Create spending this month approaching limit
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('150.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=timezone.now()
        )

        self.authenticate_as_child()
        url = reverse('finances:student-purchase-request')
        
        data = {
            'amount': '100.00',  # Would exceed 200 limit
            'description': 'Request that exceeds budget',
            'request_type': 'hours',
            'pricing_plan_id': self.pricing_plan.id,
            'parent_id': self.parent.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('budget limit', response.data['message'].lower())

    def test_invalid_parent_relationship_validation(self):
        """Test validation of parent-child relationship."""
        # Try to create request with unrelated parent
        unrelated_parent = User.objects.create_user(
            email="unrelated@test.com",
            name="Unrelated Parent"
        )

        self.authenticate_as_child()
        url = reverse('finances:student-purchase-request')
        
        data = {
            'amount': '40.00',
            'description': 'Request with invalid parent',
            'request_type': 'hours',
            'pricing_plan_id': self.small_plan.id,
            'parent_id': unrelated_parent.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data['error'].lower())


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class ParentApprovalDashboardAPITests(ApprovalAPITestCase):
    """Test cases for Parent Approval Dashboard."""

    def setUp(self):
        """Set up dashboard test data."""
        super().setUp()
        
        # Create additional child for comprehensive testing
        self.child2 = User.objects.create_user(
            email="child2@test.com",
            name="Child Two"
        )
        
        self.relationship2 = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child2,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        
        # Create or update budget controls
        FamilyBudgetControl.objects.update_or_create(
            parent_child_relationship=self.parent_child_relationship,
            defaults={
                'monthly_budget_limit': Decimal('200.00'),
                'auto_approval_threshold': Decimal('50.00')
            }
        )
        FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship2,
            monthly_budget_limit=Decimal('150.00'),
            auto_approval_threshold=Decimal('30.00')
        )

    def test_comprehensive_dashboard_data(self):
        """Test parent dashboard returns comprehensive data for all children."""
        # Clear existing approval requests from fixtures
        PurchaseApprovalRequest.objects.all().delete()
        
        # Create pending requests
        PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Request from child 1',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )
        PurchaseApprovalRequest.objects.create(
            student=self.child2,
            parent=self.parent,
            parent_child_relationship=self.relationship2,
            amount=Decimal('80.00'),
            description='Request from child 2',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )
        
        # Create recent transactions
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        self.authenticate_as_parent()
        url = reverse('finances:parent-approval-dashboard')
        
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify comprehensive data structure
        data = response.data
        self.assertIn('pending_requests', data)
        self.assertIn('children_summary', data)
        self.assertIn('recent_transactions', data)
        self.assertIn('monthly_spending_total', data)
        
        # Verify pending requests for both children
        self.assertEqual(len(data['pending_requests']), 2)
        
        # Verify children summary
        self.assertEqual(len(data['children_summary']), 2)
        children_names = [child['name'] for child in data['children_summary']]
        self.assertIn('Test Student', children_names)
        self.assertIn('Child Two', children_names)

    def test_budget_alert_generation(self):
        """Test dashboard generates appropriate budget alerts."""
        # Create spending approaching budget limits
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('180.00'),  # Close to 200 limit
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at=timezone.now()
        )

        self.authenticate_as_parent()
        url = reverse('finances:parent-approval-dashboard')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should generate budget alerts
        budget_alerts = response.data.get('budget_alerts', [])
        self.assertGreater(len(budget_alerts), 0)
        
        # Verify alert contains relevant information
        alert_found = any(
            'budget' in alert.get('message', '').lower() and 'Test Student' in alert.get('message', '')
            for alert in budget_alerts
        )
        self.assertTrue(alert_found)

    def test_dashboard_permission_isolation(self):
        """Test parent only sees data for their own children."""
        # Create data for other parent
        other_child = User.objects.create_user(email="other_child@test.com", name="Other Child")
        other_relationship = ParentChildRelationship.objects.create(
            parent=self.other_parent,
            child=other_child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        PurchaseApprovalRequest.objects.create(
            student=other_child,
            parent=self.other_parent,
            parent_child_relationship=other_relationship,
            amount=Decimal('75.00'),
            description='Other parent request',
            request_type=PurchaseRequestType.HOURS
        )

        self.authenticate_as_parent()
        url = reverse('finances:parent-approval-dashboard')
        
        response = self.client.get(url)
        
        # Should not see other parent's data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending_requests = response.data['pending_requests']
        
        # Verify no requests from other parent's children
        for request in pending_requests:
            self.assertNotEqual(request.get('student_name'), 'Other Child')
