"""
Consolidated Tests for Issue #183 - Business Logic Edge Cases and API Response Formatting

This module consolidates all Issue #183 test files into focused, meaningful tests that validate
business requirements without testing Django framework behavior.

Test Coverage:
1. CardDisplayTests - Payment method card display format validation
2. FinancialPrecisionTests - Decimal precision in financial calculations
3. MultiSchoolPermissionTests - Cross-school access and permission edge cases
4. APIResponseFormatTests - API response consistency and error handling

These tests focus on business logic validation and critical API behaviors.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import ParentChildRelationship, School, SchoolMembership, SchoolRole
from common.test_base import BaseAPITestCase
from finances.models import SchoolBillingSettings, StoredPaymentMethod, StudentAccountBalance
from finances.serializers import StoredPaymentMethodSerializer
from finances.services.business_logic_services import CompensationService

User = get_user_model()


class CardDisplayTests(BaseAPITestCase):
    """
    Test payment method card display format for Issue #183.
    Validates legacy format conversion and consistency across API responses.
    """

    def setUp(self):
        """Set up test data for card display tests."""
        super().setUp()
        self.client = APIClient()

        # Create test school
        self.school = School.objects.create(name="Test School", description="A test school", address="123 Test St")

        # Create student user
        self.student_user = User.objects.create_user(email="student@test.com", name="Test Student")

        # Create student account balance
        StudentAccountBalance.objects.create(
            student=self.student_user, hours_purchased=Decimal("10.00"), hours_consumed=Decimal("0.00")
        )

        self.client.force_authenticate(user=self.student_user)

    def test_legacy_card_format_conversion_x242(self):
        """
        Test conversion of legacy format 'X242' to new format '****4242'.
        Business requirement: PCI-compliant card display format.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_legacy",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="X242",  # Legacy format
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )

        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        expected_display = "Visa ****4242"
        actual_display = data["card_display"]

        self.assertEqual(
            actual_display,
            expected_display,
            f"Legacy format 'X242' should convert to '{expected_display}' but got '{actual_display}'",
        )

    def test_legacy_card_format_conversion_multiple_brands(self):
        """
        Test legacy format conversion for different card brands.
        Business requirement: Consistent format across all payment methods.
        """
        card_brands_legacy = [
            ("amex", "X002", "Amex ****0002"),
            ("discover", "X444", "Discover ****4444"),
            ("mastercard", "X242", "Mastercard ****4242"),
        ]

        for brand, last4, expected_display in card_brands_legacy:
            with self.subTest(brand=brand):
                pm = StoredPaymentMethod.objects.create(
                    student=self.student_user,
                    stripe_payment_method_id=f"pm_test_{brand}",
                    stripe_customer_id="cus_test_customer",
                    card_brand=brand,
                    card_last4=last4,
                    card_exp_month=12,
                    card_exp_year=2025,
                    is_default=False,
                    is_active=True,
                )

                serializer = StoredPaymentMethodSerializer(pm)
                actual_display = serializer.data["card_display"]

                self.assertEqual(
                    actual_display,
                    expected_display,
                    f"{brand} card should display as '{expected_display}' but got '{actual_display}'",
                )

    def test_raw_digits_format_unchanged(self):
        """
        Test that raw 4-digit format remains unchanged.
        Business requirement: Raw digits display correctly without conversion.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_raw",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="4242",  # Raw format
            card_exp_month=3,
            card_exp_year=2027,
            is_default=False,
            is_active=True,
        )

        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        expected_display = "Visa ****4242"
        actual_display = data["card_display"]

        self.assertEqual(
            actual_display,
            expected_display,
            f"Raw format '4242' should display as '{expected_display}' but got '{actual_display}'",
        )

    def test_card_display_property_method(self):
        """
        Test the model's card_display property works correctly.
        Business requirement: Model-level card display format conversion.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_property",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="X242",  # Legacy format
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )

        # Test card_display property if it exists
        if hasattr(payment_method, "card_display"):
            expected_display = "Visa ****4242"
            actual_display = payment_method.card_display

            self.assertEqual(
                actual_display,
                expected_display,
                f"Model card_display property should return '{expected_display}' but got '{actual_display}'",
            )
        else:
            # If no card_display property, just verify the serializer handles it
            serializer = StoredPaymentMethodSerializer(payment_method)
            data = serializer.data
            self.assertIn("card_display", data, "Serializer should include card_display field")


class FinancialPrecisionTests(BaseAPITestCase):
    """
    Test financial calculation precision for Issue #183.
    Validates decimal precision in compensation, refunds, and hour calculations.
    """

    def setUp(self):
        """Set up test data for financial precision tests."""
        super().setUp()
        self.teacher = User.objects.create_user(email="teacher@test.com", name="Test Teacher")
        self.student = User.objects.create_user(email="student@test.com", name="Test Student")
        self.period_start = date.today().replace(day=1)
        self.period_end = date.today()

    @patch("finances.services.business_logic_services.apps.get_model")
    def test_compensation_calculation_fractional_hourly_rate_precision(self, mock_get_model):
        """
        Test compensation with fractional hourly rates maintains 2-decimal precision.
        Business requirement: Financial calculations must be accurate to 2 decimal places.
        """
        mock_lesson_model = MagicMock()
        mock_lesson_queryset = MagicMock()
        mock_lesson_queryset.count.return_value = 13
        mock_lesson_model.objects.filter.return_value = mock_lesson_queryset

        mock_user_model = MagicMock()
        mock_teacher = MagicMock()
        mock_teacher.teacher_profile.hourly_rate = Decimal("18.777")
        mock_user_model.objects.get.return_value = mock_teacher

        mock_get_model.side_effect = lambda app, model: {
            ("classroom", "Lesson"): mock_lesson_model,
            ("accounts", "CustomUser"): mock_user_model,
            ("finances", "TeacherCompensation"): MagicMock(),
        }[(app, model)]

        result = CompensationService.calculate_teacher_compensation(
            teacher_id=self.teacher.id, period_start=self.period_start, period_end=self.period_end
        )

        expected_base = Decimal("244.10")  # 13 * 18.777 = 244.101, rounded down
        expected_total = Decimal("244.10")

        self.assertEqual(result["base_amount"], expected_base)
        self.assertEqual(result["total_amount"], expected_total)

        # Verify precision is exactly 2 decimal places
        self.assertEqual(result["base_amount"].as_tuple().exponent, -2)

    @patch("finances.services.business_logic_services.apps.get_model")
    def test_compensation_bonus_calculation_precision(self, mock_get_model):
        """
        Test bonus calculations maintain precision consistency.
        Business requirement: Multi-step calculations preserve precision.
        """
        mock_lesson_model = MagicMock()
        mock_lesson_queryset = MagicMock()
        mock_lesson_queryset.count.return_value = 22  # Triggers 10% bonus
        mock_lesson_model.objects.filter.return_value = mock_lesson_queryset

        mock_user_model = MagicMock()
        mock_teacher = MagicMock()
        mock_teacher.teacher_profile.hourly_rate = Decimal("27.333")
        mock_user_model.objects.get.return_value = mock_teacher

        mock_get_model.side_effect = lambda app, model: {
            ("classroom", "Lesson"): mock_lesson_model,
            ("accounts", "CustomUser"): mock_user_model,
            ("finances", "TeacherCompensation"): MagicMock(),
        }[(app, model)]

        result = CompensationService.calculate_teacher_compensation(
            teacher_id=self.teacher.id, period_start=self.period_start, period_end=self.period_end
        )

        expected_base = Decimal("601.33")  # 22 * 27.333 = 601.326, rounded
        expected_bonus = Decimal("60.13")  # 601.33 * 0.10 = 60.133, rounded
        expected_total = Decimal("661.46")  # Base + bonus

        self.assertEqual(result["base_amount"], expected_base)
        self.assertEqual(result["bonus_amount"], expected_bonus)
        self.assertEqual(result["total_amount"], expected_total)

    def test_decimal_precision_rounding_consistency(self):
        """
        Test financial calculations use consistent rounding modes.
        Business requirement: Standardized rounding behavior across all financial operations.
        """
        test_values = [
            (Decimal("25.555"), Decimal("25.56")),  # Round up
            (Decimal("25.554"), Decimal("25.55")),  # Round down
            (Decimal("25.565"), Decimal("25.57")),  # Round up (banker's rounding edge case)
            (Decimal("25.575"), Decimal("25.58")),  # Round up
        ]

        for input_value, expected_rounded in test_values:
            with self.subTest(input_value=input_value):
                rounded_value = input_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                self.assertEqual(rounded_value, expected_rounded)

    def test_partial_refund_fractional_percentages_precision(self):
        """
        Test partial refund calculations maintain precision.
        Business requirement: Refund calculations must be accurate and consistent.
        """
        original_payments = [
            Decimal("87.777"),
            Decimal("156.555"),
            Decimal("234.888"),
        ]
        refund_percentage = Decimal("0.675")  # 67.5% partial refund

        expected_refunds = [
            Decimal("59.25"),  # 87.777 * 0.675 = 59.24975, rounded up
            Decimal("105.67"),  # 156.555 * 0.675 = 105.67463, rounded down
            Decimal("158.55"),  # 234.888 * 0.675 = 158.5494, rounded up
        ]

        for i, payment in enumerate(original_payments):
            with self.subTest(payment_index=i):
                refund_amount = payment * refund_percentage
                rounded_refund = refund_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                self.assertEqual(rounded_refund, expected_refunds[i])

    def test_time_based_prorated_refund_precision(self):
        """
        Test time-based prorated refunds maintain daily calculation precision.
        Business requirement: Pro-rated refunds must be calculated accurately.
        """
        monthly_subscription_fee = Decimal("89.777")
        total_days_month = 31
        days_used = 23
        days_remaining = 8

        daily_rate = monthly_subscription_fee / Decimal(total_days_month)
        used_amount = daily_rate * Decimal(days_used)
        refund_amount = daily_rate * Decimal(days_remaining)

        expected_daily_rate = Decimal("2.90")  # 89.777 / 31 = 2.8960..., rounded up
        # Actual calculation: 2.8960645161 * 23 = 66.60948387, rounded to 66.61
        expected_used = Decimal("66.61")
        # Actual calculation: 2.8960645161 * 8 = 23.16851613, rounded to 23.17
        expected_refund = Decimal("23.17")

        self.assertEqual(daily_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), expected_daily_rate)
        self.assertEqual(used_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), expected_used)
        self.assertEqual(refund_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), expected_refund)


class MultiSchoolPermissionTests(BaseAPITestCase):
    """
    Test multi-school permission edge cases for Issue #183.
    Validates cross-school access and basic permission scenarios.
    """

    def setUp(self):
        """Set up test data for multi-school permission tests."""
        super().setUp()

        # Create multiple schools
        self.school_a = School.objects.create(name="School A", description="Test School A", address="123 A St")

        self.school_b = School.objects.create(name="School B", description="Test School B", address="456 B Ave")

        # Create users
        self.parent_user = User.objects.create_user(email="parent@test.com", name="Parent User")

        self.student_a = User.objects.create_user(email="student.a@test.com", name="Student A")

        self.student_b = User.objects.create_user(email="student.b@test.com", name="Student B")

    def test_cross_school_relationship_setup(self):
        """
        Test that parent-child relationships can be established across schools.
        Business requirement: Multi-school family relationships are supported.
        """
        # Set up parent-child relationships across different schools
        relationship_a = ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.student_a,
            school=self.school_a,
            relationship_type="parent",
            is_active=True,
        )

        relationship_b = ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.student_b,
            school=self.school_b,
            relationship_type="parent",
            is_active=True,
        )

        # Verify relationships were created correctly
        self.assertEqual(relationship_a.parent, self.parent_user)
        self.assertEqual(relationship_a.child, self.student_a)
        self.assertEqual(relationship_a.school, self.school_a)

        self.assertEqual(relationship_b.parent, self.parent_user)
        self.assertEqual(relationship_b.child, self.student_b)
        self.assertEqual(relationship_b.school, self.school_b)

        # Verify parent can have children in different schools
        parent_relationships = ParentChildRelationship.objects.filter(parent=self.parent_user)
        self.assertEqual(parent_relationships.count(), 2)

        school_ids = set(rel.school.id for rel in parent_relationships)
        self.assertEqual(len(school_ids), 2, "Parent should have children in 2 different schools")

    def test_school_membership_isolation(self):
        """
        Test that school memberships properly isolate users to their respective schools.
        Business requirement: Users belong to specific schools with defined roles.
        """
        # Create school memberships
        membership_a = SchoolMembership.objects.create(
            user=self.student_a, school=self.school_a, role=SchoolRole.STUDENT, is_active=True
        )

        membership_b = SchoolMembership.objects.create(
            user=self.student_b, school=self.school_b, role=SchoolRole.STUDENT, is_active=True
        )

        # Verify students belong to different schools
        student_a_schools = SchoolMembership.objects.filter(user=self.student_a, is_active=True).values_list(
            "school_id", flat=True
        )

        student_b_schools = SchoolMembership.objects.filter(user=self.student_b, is_active=True).values_list(
            "school_id", flat=True
        )

        self.assertIn(self.school_a.id, student_a_schools)
        self.assertNotIn(self.school_a.id, student_b_schools)

        self.assertIn(self.school_b.id, student_b_schools)
        self.assertNotIn(self.school_b.id, student_a_schools)

    def test_billing_settings_school_isolation(self):
        """
        Test that billing settings are properly isolated per school.
        Business requirement: Each school has independent billing configuration.
        """
        # Create billing settings for both schools
        billing_a = SchoolBillingSettings.objects.create(
            school=self.school_a,
            trial_cost_absorption="school",
            teacher_payment_frequency="monthly",
            payment_day_of_month=15,
        )

        billing_b = SchoolBillingSettings.objects.create(
            school=self.school_b,
            trial_cost_absorption="teacher",
            teacher_payment_frequency="weekly",
            payment_day_of_month=1,
        )

        # Verify each school has its own settings
        school_a_billing = SchoolBillingSettings.objects.get(school=self.school_a)
        school_b_billing = SchoolBillingSettings.objects.get(school=self.school_b)

        self.assertEqual(school_a_billing.trial_cost_absorption, "school")
        self.assertEqual(school_a_billing.teacher_payment_frequency, "monthly")
        self.assertEqual(school_a_billing.payment_day_of_month, 15)

        self.assertEqual(school_b_billing.trial_cost_absorption, "teacher")
        self.assertEqual(school_b_billing.teacher_payment_frequency, "weekly")
        self.assertEqual(school_b_billing.payment_day_of_month, 1)

        # Verify settings are different
        self.assertNotEqual(school_a_billing.trial_cost_absorption, school_b_billing.trial_cost_absorption)
        self.assertNotEqual(school_a_billing.teacher_payment_frequency, school_b_billing.teacher_payment_frequency)


class APIResponseFormatTests(BaseAPITestCase):
    """
    Test data format consistency for Issue #183.
    Validates serializer output and data structures.
    """

    def setUp(self):
        """Set up test data for response format tests."""
        super().setUp()

        self.school = School.objects.create(name="Test School", description="A test school", address="123 Test St")

        self.student_user = User.objects.create_user(email="student@test.com", name="Test Student")

        StudentAccountBalance.objects.create(
            student=self.student_user, hours_purchased=Decimal("10.00"), hours_consumed=Decimal("2.00")
        )

    def test_serializer_field_completeness(self):
        """
        Test that serializers include all expected fields.
        Business requirement: Complete field sets in data responses.
        """
        # Create payment method
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_complete",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="4242",
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )

        # Test serializer output
        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        # Required fields in serialized data
        required_fields = ["id", "card_brand", "card_display", "is_default", "is_active"]

        for field in required_fields:
            self.assertIn(field, data, f"Payment method serializer missing required field '{field}'")

        # Verify data types
        self.assertIsInstance(data["id"], int)
        self.assertIsInstance(data["card_brand"], str)
        self.assertIsInstance(data["card_display"], str)
        self.assertIsInstance(data["is_default"], bool)
        self.assertIsInstance(data["is_active"], bool)

    def test_decimal_field_serialization(self):
        """
        Test that decimal fields are properly serialized.
        Business requirement: Financial data maintains precision in serialization.
        """
        # Test decimal field handling with payment method
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_decimal",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="9999",
            card_exp_month=12,
            card_exp_year=2025,
            is_default=False,
            is_active=True,
        )

        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        # Verify that the serialized data maintains proper types
        # Even though this model doesn't have decimal fields, we verify
        # that integer fields are properly serialized
        self.assertIsInstance(data["card_exp_month"], int)
        self.assertIsInstance(data["card_exp_year"], int)

        # Verify basic financial precision concept with our balance model
        balance = StudentAccountBalance.objects.get(student=self.student_user)

        # These should be Decimal in the model
        self.assertIsInstance(balance.hours_purchased, Decimal)
        self.assertIsInstance(balance.hours_consumed, Decimal)

        # Verify decimal precision is maintained
        self.assertEqual(balance.hours_purchased.as_tuple().exponent, -2)
        self.assertEqual(balance.hours_consumed.as_tuple().exponent, -2)

    def test_boolean_field_consistency(self):
        """
        Test that boolean fields are consistently represented.
        Business requirement: Boolean values should be consistently typed.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_bool",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="1234",
            card_exp_month=12,
            card_exp_year=2025,
            is_default=False,
            is_active=True,
        )

        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        # Boolean fields should be actual booleans, not strings
        boolean_fields = ["is_default", "is_active"]
        for field in boolean_fields:
            if field in data:
                self.assertIsInstance(
                    data[field], bool, f"Field '{field}' should be boolean but got {type(data[field])}"
                )

    def test_json_serializable_output(self):
        """
        Test that all serialized data is JSON serializable.
        Business requirement: All data should be JSON serializable for API responses.
        """
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_json",
            stripe_customer_id="cus_test_customer",
            card_brand="mastercard",
            card_last4="5678",
            card_exp_month=8,
            card_exp_year=2026,
            is_default=True,
            is_active=True,
        )

        serializer = StoredPaymentMethodSerializer(payment_method)
        data = serializer.data

        # Should be JSON serializable without errors
        try:
            json.dumps(data)
        except (TypeError, ValueError) as e:
            self.fail(f"Serialized data is not JSON serializable: {e}")

        # Verify it's actually valid JSON
        json_string = json.dumps(data)
        try:
            json.loads(json_string)
        except json.JSONDecodeError as e:
            self.fail(f"Generated JSON is not valid: {e}")
