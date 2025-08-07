"""
Test cases for purchase approval and spending control API endpoints.

This module tests the ViewSets and API endpoints for the parent-child
purchase approval workflow.
"""

import json
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from knox.models import AuthToken

from accounts.models import CustomUser, School, ParentChildRelationship, RelationshipType, TeacherProfile
from finances.models import (
    FamilyBudgetControl,
    PurchaseApprovalRequest,
    PurchaseTransaction,
    PricingPlan,
    ClassSession,
    TransactionPaymentStatus,
    PurchaseRequestType,
    PurchaseApprovalStatus,
    SessionType,
    PlanType,
)


class FamilyBudgetControlViewSetTest(TestCase):
    """Test cases for the FamilyBudgetControlViewSet."""

    def setUp(self):
        """Set up test data."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )

        # Create parent and child users
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )

        # Create parent-child relationship
        self.parent_child_relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

        # Create API client and authenticate as parent
        self.client = APIClient()
        self.parent_token = AuthToken.objects.create(self.parent)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.parent_token}')

        # Create API client for child
        self.child_client = APIClient()
        self.child_token = AuthToken.objects.create(self.child)[1]

    def test_create_budget_control(self):
        """Test creating a new budget control."""
        url = reverse('familybudgetcontrol-list')
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
        self.assertEqual(budget_control.weekly_budget_limit, Decimal('50.00'))
        self.assertEqual(budget_control.auto_approval_threshold, Decimal('20.00'))

    def test_list_budget_controls_as_parent(self):
        """Test listing budget controls as a parent."""
        # Create budget control
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('200.00'),
            auto_approval_threshold=Decimal('20.00')
        )

        url = reverse('familybudgetcontrol-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], budget_control.id)
        self.assertEqual(response.data[0]['parent_name'], 'Parent User')
        self.assertEqual(response.data[0]['child_name'], 'Child User')

    def test_update_budget_control(self):
        """Test updating a budget control."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('200.00'),
            auto_approval_threshold=Decimal('20.00')
        )

        url = reverse('familybudgetcontrol-detail', kwargs={'pk': budget_control.id})
        data = {
            'monthly_budget_limit': '300.00',
            'auto_approval_threshold': '25.00'
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        budget_control.refresh_from_db()
        self.assertEqual(budget_control.monthly_budget_limit, Decimal('300.00'))
        self.assertEqual(budget_control.auto_approval_threshold, Decimal('25.00'))

    def test_check_budget_limits_action(self):
        """Test the check_budget_limits custom action."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('200.00'),
            auto_approval_threshold=Decimal('20.00')
        )

        url = reverse('familybudgetcontrol-check-budget-limits', kwargs={'pk': budget_control.id})
        data = {'amount': '15.00'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['allowed'])
        self.assertTrue(response.data['can_auto_approve'])
        self.assertEqual(len(response.data['reasons']), 0)

    def test_child_cannot_access_budget_control(self):
        """Test that child users cannot access budget controls."""
        self.child_client.credentials(HTTP_AUTHORIZATION=f'Token {self.child_token}')
        
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('200.00')
        )

        url = reverse('familybudgetcontrol-list')
        response = self.child_client.get(url)

        # Should return empty list or 403, depending on permission implementation
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(len(response.data), 0)


class PurchaseApprovalRequestViewSetTest(TestCase):
    """Test cases for the PurchaseApprovalRequestViewSet."""

    def setUp(self):
        """Set up test data."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )

        # Create parent and child users
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )

        # Create parent-child relationship
        self.parent_child_relationship = ParentChildRelationship.objects.create(
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

        # Create API clients
        self.parent_client = APIClient()
        self.parent_token = AuthToken.objects.create(self.parent)[1] 

        self.child_client = APIClient()
        self.child_token = AuthToken.objects.create(self.child)[1]

    def test_create_approval_request_as_child(self):
        """Test creating a purchase approval request as a child."""
        self.child_client.credentials(HTTP_AUTHORIZATION=f'Token {self.child_token}')

        url = reverse('purchaseapprovalrequest-list')
        data = {
            'student': self.child.id,
            'parent': self.parent.id,
            'parent_child_relationship': self.parent_child_relationship.id,
            'amount': '100.00',
            'description': 'Request for 10-hour package',
            'request_type': PurchaseRequestType.HOURS,
            'pricing_plan': self.pricing_plan.id
        }

        response = self.child_client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PurchaseApprovalRequest.objects.count(), 1)
        
        approval_request = PurchaseApprovalRequest.objects.first()
        self.assertEqual(approval_request.student, self.child)
        self.assertEqual(approval_request.parent, self.parent)
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.PENDING)

    def test_list_approval_requests_as_parent(self):
        """Test listing approval requests as a parent."""
        self.parent_client.credentials(HTTP_AUTHORIZATION=f'Token {self.parent_token}')

        # Create approval request
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Request for 10-hour package',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        url = reverse('purchaseapprovalrequest-list')
        response = self.parent_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], approval_request.id)
        self.assertEqual(response.data[0]['student_name'], 'Child User')

    def test_approve_request_action(self):
        """Test approving a purchase request."""
        self.parent_client.credentials(HTTP_AUTHORIZATION=f'Token {self.parent_token}')

        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Request for 10-hour package',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        url = reverse('purchaseapprovalrequest-approve', kwargs={'pk': approval_request.id})
        data = {
            'action': 'approve',
            'parent_notes': 'Approved for educational purposes'
        }

        response = self.parent_client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.APPROVED)
        self.assertEqual(approval_request.parent_notes, 'Approved for educational purposes')

    def test_deny_request_action(self):
        """Test denying a purchase request."""
        self.parent_client.credentials(HTTP_AUTHORIZATION=f'Token {self.parent_token}')

        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Request for 10-hour package',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        url = reverse('purchaseapprovalrequest-approve', kwargs={'pk': approval_request.id})
        data = {
            'action': 'deny',
            'parent_notes': 'Too expensive this month'
        }

        response = self.parent_client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.DENIED)
        self.assertEqual(approval_request.parent_notes, 'Too expensive this month')

    def test_cancel_request_as_child(self):
        """Test cancelling a request as a child."""
        self.child_client.credentials(HTTP_AUTHORIZATION=f'Token {self.child_token}')

        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description='Request for 10-hour package',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        url = reverse('purchaseapprovalrequest-cancel', kwargs={'pk': approval_request.id})
        response = self.child_client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.CANCELLED)

    def test_filter_by_status(self):
        """Test filtering approval requests by status."""
        self.parent_client.credentials(HTTP_AUTHORIZATION=f'Token {self.parent_token}')

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

        # Test filtering by pending status
        url = reverse('purchaseapprovalrequest-list')
        response = self.parent_client.get(url, {'status': 'pending'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], pending_request.id)

        # Test filtering by approved status
        response = self.parent_client.get(url, {'status': 'approved'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], approved_request.id)


class StudentPurchaseRequestViewTest(TestCase):
    """Test cases for the StudentPurchaseRequestView."""

    def setUp(self):
        """Set up test data."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )

        # Create parent and child users
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )

        # Create parent-child relationship
        self.parent_child_relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

        # Create budget control with auto approval
        self.budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('200.00'),
            auto_approval_threshold=Decimal('50.00')
        )

        # Create pricing plan
        self.pricing_plan = PricingPlan.objects.create(
            name="Small Package",
            description="A small hour package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('5.00'),
            price_eur=Decimal('40.00'),
            validity_days=30
        )

        # Create API client for child
        self.client = APIClient()
        self.child_token = AuthToken.objects.create(self.child)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.child_token}')

    def test_create_purchase_request_auto_approved(self):
        """Test creating a purchase request that gets auto-approved."""
        url = reverse('student-purchase-request')
        data = {
            'amount': '40.00',
            'description': 'Request for small hour package',
            'request_type': 'hours',
            'pricing_plan_id': self.pricing_plan.id,
            'parent_id': self.parent.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['auto_approved'])
        
        # Should create a purchase request that's already approved
        approval_request = PurchaseApprovalRequest.objects.first()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.APPROVED)

    def test_create_purchase_request_needs_approval(self):
        """Test creating a purchase request that needs parent approval."""
        # Create a more expensive pricing plan
        expensive_plan = PricingPlan.objects.create(
            name="Large Package",
            description="A large hour package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('20.00'),
            price_eur=Decimal('150.00'),
            validity_days=30
        )

        url = reverse('student-purchase-request')
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
        
        # Should create a pending purchase request
        approval_request = PurchaseApprovalRequest.objects.first()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.PENDING)

    def test_create_purchase_request_exceeds_budget(self):
        """Test creating a purchase request that exceeds budget limits."""
        # Create spending this month to approach limit
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type='package',
            amount=Decimal('150.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        # Try to create a request that would exceed monthly limit
        url = reverse('student-purchase-request')
        data = {
            'amount': '100.00',
            'description': 'Request that exceeds budget',
            'request_type': 'hours',
            'pricing_plan_id': self.pricing_plan.id,
            'parent_id': self.parent.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('budget limit', response.data['message'].lower())

    def test_create_purchase_request_invalid_parent(self):
        """Test creating purchase request with invalid parent."""
        # Create another user who is not the parent
        other_user = CustomUser.objects.create_user(
            email="other@test.com",
            name="Other User"
        )

        url = reverse('student-purchase-request')
        data = {
            'amount': '40.00',
            'description': 'Request with invalid parent',
            'request_type': 'hours',
            'pricing_plan_id': self.pricing_plan.id,
            'parent_id': other_user.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data['message'].lower())


class ParentApprovalDashboardViewTest(TestCase):
    """Test cases for the ParentApprovalDashboardView."""

    def setUp(self):
        """Set up test data."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )

        # Create parent and children users
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        self.child1 = CustomUser.objects.create_user(
            email="child1@test.com",
            name="Child One"
        )
        self.child2 = CustomUser.objects.create_user(
            email="child2@test.com",
            name="Child Two"
        )

        # Create parent-child relationships
        self.relationship1 = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child1,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )
        self.relationship2 = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child2,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

        # Create budget controls
        FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship1,
            monthly_budget_limit=Decimal('200.00'),
            auto_approval_threshold=Decimal('50.00')
        )
        FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship2,
            monthly_budget_limit=Decimal('150.00'),
            auto_approval_threshold=Decimal('30.00')
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

        # Create API client
        self.client = APIClient()
        self.parent_token = AuthToken.objects.create(self.parent)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.parent_token}')

    def test_parent_dashboard_data(self):
        """Test getting comprehensive parent dashboard data."""
        # Create pending requests
        pending_request1 = PurchaseApprovalRequest.objects.create(
            student=self.child1,
            parent=self.parent,
            parent_child_relationship=self.relationship1,
            amount=Decimal('100.00'),
            description='Request from child 1',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )
        pending_request2 = PurchaseApprovalRequest.objects.create(
            student=self.child2,
            parent=self.parent,
            parent_child_relationship=self.relationship2,
            amount=Decimal('80.00'),
            description='Request from child 2',
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        # Create some completed transactions
        PurchaseTransaction.objects.create(
            student=self.child1,
            transaction_type='package',
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        PurchaseTransaction.objects.create(
            student=self.child2,
            transaction_type='package',
            amount=Decimal('75.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        url = reverse('parent-approval-dashboard')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check pending requests
        self.assertEqual(len(response.data['pending_requests']), 2)
        request_ids = [req['id'] for req in response.data['pending_requests']]
        self.assertIn(pending_request1.id, request_ids)
        self.assertIn(pending_request2.id, request_ids)

        # Check children summary
        self.assertEqual(len(response.data['children_summary']), 2)
        children_names = [child['name'] for child in response.data['children_summary']]
        self.assertIn('Child One', children_names)
        self.assertIn('Child Two', children_names)

        # Check monthly spending total
        self.assertEqual(response.data['monthly_spending_total'], Decimal('125.00'))

    def test_dashboard_budget_alerts(self):
        """Test budget alerts in dashboard."""
        # Create spending that approaches limits
        PurchaseTransaction.objects.create(
            student=self.child1,
            transaction_type='package',
            amount=Decimal('180.00'),  # Close to 200 limit
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        url = reverse('parent-approval-dashboard')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have budget alerts
        self.assertGreater(len(response.data['budget_alerts']), 0)
        
        # Check alert content
        alert_found = False
        for alert in response.data['budget_alerts']:
            if 'Child One' in alert.get('message', '') and 'budget' in alert.get('message', '').lower():
                alert_found = True
                break
        self.assertTrue(alert_found)

    def test_dashboard_recent_transactions(self):
        """Test recent transactions in dashboard."""
        # Create some recent transactions
        transaction1 = PurchaseTransaction.objects.create(
            student=self.child1,
            transaction_type='package',
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        transaction2 = PurchaseTransaction.objects.create(
            student=self.child2,
            transaction_type='package',
            amount=Decimal('75.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        url = reverse('parent-approval-dashboard')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check recent transactions
        self.assertGreater(len(response.data['recent_transactions']), 0)
        
        # Transactions should be ordered by most recent first
        transactions = response.data['recent_transactions']
        self.assertEqual(transactions[0]['amount'], '75.00')  # Most recent
        self.assertEqual(transactions[1]['amount'], '50.00')

    def test_dashboard_permission_check(self):
        """Test that only the parent can access their dashboard."""
        # Create another parent
        other_parent = CustomUser.objects.create_user(
            email="other_parent@test.com",
            name="Other Parent"
        )

        # Try to access dashboard as other parent
        other_client = APIClient()
        other_token = AuthToken.objects.create(other_parent)[1]
        other_client.credentials(HTTP_AUTHORIZATION=f'Token {other_token}')

        url = reverse('parent-approval-dashboard')
        response = other_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return empty data for other parent
        self.assertEqual(len(response.data['pending_requests']), 0)
        self.assertEqual(len(response.data['children_summary']), 0)
        self.assertEqual(response.data['monthly_spending_total'], Decimal('0.00'))