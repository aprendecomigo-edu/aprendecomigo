"""
API Tests for Issue #183 - Permission Edge Cases in API (8-10 failures expected)

These tests validate multi-school access scenarios, parent permissions across schools,
teacher role combinations, and administrative access edge cases via API endpoints.

These tests will FAIL initially (TDD red state) and should pass after implementing
the permission edge case fixes.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock

from accounts.models import School, SchoolMembership, SchoolRole, ParentChildRelationship
from finances.models import (
    StoredPaymentMethod, StudentAccountBalance, PricingPlan, 
    SchoolBillingSettings, TeacherCompensationRule
)
from common.test_base import BaseAPITestCase

User = get_user_model()


class MultiSchoolPermissionEdgeCaseTests(BaseAPITestCase):
    """
    Test multi-school permission edge cases for Issue #183.
    
    These tests validate complex permission scenarios across multiple schools
    and role combinations that may cause API access issues.
    """
    
    def setUp(self):
        """Set up test data for multi-school permission tests."""
        super().setUp()
        self.client = APIClient()
        
        # Create multiple test schools
        self.school_a = School.objects.create(
            name="School A",
            description="Test School A",
            address="123 A St"
        )
        
        self.school_b = School.objects.create(
            name="School B", 
            description="Test School B",
            address="456 B Ave"
        )
        
        self.school_c = School.objects.create(
            name="School C",
            description="Test School C", 
            address="789 C Blvd"
        )
        
        # Create users for different multi-school scenarios
        self.multi_school_teacher = User.objects.create_user(
            email="multiteacher@test.com",
            name="Multi School Teacher"
        )
        
        self.parent_user = User.objects.create_user(
            email="parent@test.com", 
            name="Parent User"
        )
        
        self.student_a = User.objects.create_user(
            email="student.a@test.com",
            name="Student A"
        )
        
        self.student_b = User.objects.create_user(
            email="student.b@test.com", 
            name="Student B"
        )
        
        self.school_admin = User.objects.create_user(
            email="admin@test.com",
            name="School Admin"
        )
        
        # Set up multi-school teacher memberships
        SchoolMembership.objects.create(
            user=self.multi_school_teacher,
            school=self.school_a,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.multi_school_teacher, 
            school=self.school_b,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Set up student memberships
        SchoolMembership.objects.create(
            user=self.student_a,
            school=self.school_a, 
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.student_b,
            school=self.school_b,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Set up parent-child relationships across schools
        ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.student_a,
            relationship_type="parent",
            is_active=True
        )
        
        ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.student_b,
            relationship_type="parent", 
            is_active=True
        )
        
        # Set up school admin with access to School A only
        SchoolMembership.objects.create(
            user=self.school_admin,
            school=self.school_a,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        # Create student balances
        StudentAccountBalance.objects.create(
            student=self.student_a,
            school=self.school_a,
            balance=Decimal('50.00')
        )
        
        StudentAccountBalance.objects.create(
            student=self.student_b,
            school=self.school_b,
            balance=Decimal('30.00')
        )
        
        # Create school billing settings
        SchoolBillingSettings.objects.create(
            school=self.school_a,
            trial_cost_absorption=50,
            teacher_payment_frequency="monthly",
            payment_day_of_month=15
        )
        
        SchoolBillingSettings.objects.create(
            school=self.school_b,
            trial_cost_absorption=75,
            teacher_payment_frequency="monthly", 
            payment_day_of_month=1
        )

    def test_multi_school_teacher_billing_settings_access_edge_case(self):
        """
        Test multi-school teacher access to billing settings API.
        
        A teacher with memberships in multiple schools should only see billing
        settings for schools they belong to, not all schools.
        This test will FAIL initially if permission filtering is incorrect.
        """
        self.client.force_authenticate(user=self.multi_school_teacher)
        
        url = "/api/school-billing-settings/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        response_data = response.json()
        
        # Should have access to both School A and B settings, but not School C
        self.assertEqual(len(response_data), 2, "Multi-school teacher should see 2 billing settings")
        
        school_ids = [item['school'] for item in response_data]
        
        # CRITICAL: This will FAIL if permission filtering is broken
        self.assertIn(self.school_a.id, school_ids, "Should have access to School A billing")
        self.assertIn(self.school_b.id, school_ids, "Should have access to School B billing")
        self.assertNotIn(self.school_c.id, school_ids, "Should NOT have access to School C billing")

    def test_parent_cross_school_student_balance_access_edge_case(self):
        """
        Test parent access to children's balances across different schools.
        
        A parent with children in different schools should be able to access
        all their children's financial information via API.
        This test will FAIL initially if cross-school parent permissions are broken.
        """
        self.client.force_authenticate(user=self.parent_user)
        
        # Test accessing Student A's balance (School A)
        url = f"/api/student-balance/?student_id={self.student_a.id}"
        response = self.client.get(url)
        
        # CRITICAL: This will FAIL if parent cross-school permissions are broken
        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK,
            "Parent should have access to child's balance in School A"
        )
        
        # Test accessing Student B's balance (School B) 
        url = f"/api/student-balance/?student_id={self.student_b.id}"
        response = self.client.get(url)
        
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK, 
            "Parent should have access to child's balance in School B"
        )
        
        # Verify response contains correct school information
        response_data = response.json()
        self.assertIn('school_name', response_data, "Response should include school name")

    def test_school_admin_limited_cross_school_access_edge_case(self):
        """
        Test school admin access limitations across schools.
        
        A school admin should only access billing settings for their own school,
        not other schools, even if they try to access via API.
        This test will FAIL initially if admin permissions leak across schools.
        """
        self.client.force_authenticate(user=self.school_admin)
        
        # Should be able to access School A billing settings
        url = "/api/school-billing-settings/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # CRITICAL: Should only see School A, not School B or C
        self.assertEqual(len(response_data), 1, "School admin should only see 1 billing setting")
        
        billing_setting = response_data[0]
        self.assertEqual(
            billing_setting['school'], 
            self.school_a.id,
            "School admin should only see School A billing settings"
        )
        
        # Try to directly access School B billing settings (should be forbidden)
        school_b_billing = SchoolBillingSettings.objects.get(school=self.school_b)
        url = f"/api/school-billing-settings/{school_b_billing.id}/"
        response = self.client.get(url)
        
        # CRITICAL: This will FAIL if cross-school access control is broken
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "School admin should not access other school's billing settings"
        )

    def test_teacher_compensation_multi_school_edge_case(self):
        """
        Test teacher compensation rule access across multiple schools.
        
        A teacher with roles in multiple schools should see compensation rules
        for all their schools, properly filtered by API.
        This test will FAIL initially if filtering is incorrect.
        """
        # Create compensation rules for both schools
        rule_a = TeacherCompensationRule.objects.create(
            teacher=self.multi_school_teacher,
            school=self.school_a,
            rule_type="grade_specific",
            grade_level="5",
            rate_per_hour=Decimal('25.00'),
            is_active=True
        )
        
        rule_b = TeacherCompensationRule.objects.create(
            teacher=self.multi_school_teacher,
            school=self.school_b,
            rule_type="group_class",
            rate_per_hour=Decimal('30.00'), 
            is_active=True
        )
        
        # Create rule for different teacher (should not be visible)
        other_teacher = User.objects.create_user(
            email="other.teacher@test.com",
            name="Other Teacher"
        )
        
        SchoolMembership.objects.create(
            user=other_teacher,
            school=self.school_a,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        other_rule = TeacherCompensationRule.objects.create(
            teacher=other_teacher,
            school=self.school_a,
            rule_type="fixed_salary",
            fixed_amount=Decimal('1500.00'),
            is_active=True
        )
        
        self.client.force_authenticate(user=self.multi_school_teacher)
        
        url = "/api/teacher-compensation-rules/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # CRITICAL: Should see exactly 2 rules (both schools), not other teacher's rules
        self.assertEqual(
            len(response_data), 
            2,
            "Multi-school teacher should see compensation rules for both schools"
        )
        
        rule_ids = [rule['id'] for rule in response_data]
        self.assertIn(rule_a.id, rule_ids, "Should see School A compensation rule")
        self.assertIn(rule_b.id, rule_ids, "Should see School B compensation rule")
        self.assertNotIn(other_rule.id, rule_ids, "Should NOT see other teacher's rule")

    def test_parent_payment_method_access_across_children_edge_case(self):
        """
        Test parent access to payment methods for children in different schools.
        
        Parent should be able to manage payment methods for all their children
        regardless of which school each child attends.
        This test will FAIL initially if parent payment method permissions are broken.
        """
        # Create payment methods for both students
        payment_method_a = StoredPaymentMethod.objects.create(
            student=self.student_a,
            stripe_payment_method_id="pm_test_student_a",
            stripe_customer_id="cus_test_a",
            card_brand="visa",
            card_last4="4242",
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True
        )
        
        payment_method_b = StoredPaymentMethod.objects.create(
            student=self.student_b,
            stripe_payment_method_id="pm_test_student_b", 
            stripe_customer_id="cus_test_b",
            card_brand="mastercard",
            card_last4="5555", 
            card_exp_month=6,
            card_exp_year=2026,
            is_default=True,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.parent_user)
        
        # Test accessing Student A's payment methods (School A)
        url = f"/api/student-balance/payment-methods/?student_id={self.student_a.id}"
        response = self.client.get(url)
        
        # CRITICAL: This will FAIL if parent cross-school access is broken
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "Parent should access child's payment methods in School A"
        )
        
        response_data = response.json()
        self.assertIn('payment_methods', response_data)
        self.assertEqual(len(response_data['payment_methods']), 1)
        
        # Test accessing Student B's payment methods (School B)
        url = f"/api/student-balance/payment-methods/?student_id={self.student_b.id}"
        response = self.client.get(url)
        
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "Parent should access child's payment methods in School B"
        )

    def test_inactive_membership_permission_denial_edge_case(self):
        """
        Test that inactive school memberships don't grant API access.
        
        Users with inactive memberships should be denied access to school resources
        even if they previously had access.
        This test will FAIL initially if inactive membership filtering is broken.
        """
        # Create user with initially active membership
        temp_teacher = User.objects.create_user(
            email="temp.teacher@test.com",
            name="Temporary Teacher"
        )
        
        membership = SchoolMembership.objects.create(
            user=temp_teacher,
            school=self.school_a,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Create compensation rule while active
        compensation_rule = TeacherCompensationRule.objects.create(
            teacher=temp_teacher,
            school=self.school_a,
            rule_type="grade_specific",
            grade_level="3",
            rate_per_hour=Decimal('20.00'),
            is_active=True
        )
        
        self.client.force_authenticate(user=temp_teacher)
        
        # Should have access while membership is active
        url = "/api/teacher-compensation-rules/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Deactivate membership
        membership.is_active = False
        membership.save()
        
        # CRITICAL: Should now be denied access
        response = self.client.get(url)
        
        # This will FAIL if inactive membership filtering is broken
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            "Inactive membership should deny API access"
        )

    def test_role_combination_permission_edge_case(self):
        """
        Test complex role combinations in the same school via API.
        
        A user who is both school owner and teacher should have appropriate
        access levels for both roles via API endpoints.
        This test will FAIL initially if role combination handling is incorrect.
        """
        # Create user with dual roles in School A
        dual_role_user = User.objects.create_user(
            email="dualrole@test.com",
            name="Dual Role User"  
        )
        
        # Add as school owner
        SchoolMembership.objects.create(
            user=dual_role_user,
            school=self.school_a,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
        # Add as teacher in same school
        SchoolMembership.objects.create(
            user=dual_role_user, 
            school=self.school_a,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Create teacher compensation rule
        teacher_rule = TeacherCompensationRule.objects.create(
            teacher=dual_role_user,
            school=self.school_a,
            rule_type="grade_specific",
            grade_level="4",
            rate_per_hour=Decimal('35.00'),
            is_active=True
        )
        
        self.client.force_authenticate(user=dual_role_user)
        
        # Should have teacher-level access
        url = "/api/teacher-compensation-rules/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have owner-level access to billing settings
        url = "/api/school-billing-settings/"
        response = self.client.get(url)
        
        # CRITICAL: Should have access as school owner
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "Dual role user should have owner-level access to billing settings"
        )
        
        response_data = response.json()
        self.assertGreater(len(response_data), 0, "Should see billing settings as owner")

    def test_cross_school_data_isolation_edge_case(self):
        """
        Test that data from one school doesn't leak into another school's API responses.
        
        Users should only see data for schools they have access to, with strict isolation.
        This test will FAIL initially if data isolation is broken.
        """
        # Create user with access only to School A
        single_school_user = User.objects.create_user(
            email="singleschool@test.com",
            name="Single School User"
        )
        
        SchoolMembership.objects.create(
            user=single_school_user,
            school=self.school_a, 
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        self.client.force_authenticate(user=single_school_user)
        
        # Test billing settings - should only see School A
        url = "/api/school-billing-settings/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # CRITICAL: Should only see 1 school's data, not others
        self.assertEqual(len(response_data), 1, "Should only see one school's billing settings")
        
        billing_setting = response_data[0]
        self.assertEqual(
            billing_setting['school'],
            self.school_a.id,
            "Should only see School A's billing settings"
        )
        
        # Verify school name is correct (no data leakage)
        self.assertEqual(
            billing_setting['school_name'],
            "School A",
            "School name should match accessible school"
        )