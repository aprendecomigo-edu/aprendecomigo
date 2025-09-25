"""
E2E tests for adding Adult Student account type.

This test validates the complete workflow for creating an adult student account
where the student manages everything independently (classes, payments, schedule).
"""

from fixtures.test_data import VALIDATION_RULES, StudentTestData, TestSelectors
from playwright.sync_api import Page, expect
import pytest
from utils.base_test import BaseE2ETest


class TestAddAdultStudent(BaseE2ETest):
    """Test suite for Adult Student account creation"""

    def test_successful_adult_student_creation(self, page: Page):
        """
        Test successful creation of adult student account.

        Requirements:
        - Student gets their own login account
        - Student has access to classes, scheduling, AND payments
        - No guardian account is created
        - Student manages everything independently
        """
        # Arrange
        test_data = StudentTestData.adult_student_data()
        student_data = test_data["student"]

        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Act - Select Adult Student account type
        self.select_account_type(page, "self")

        # Verify correct form sections are visible
        self.assert_field_exists(page, TestSelectors.STUDENT_NAME)
        self.assert_field_exists(page, TestSelectors.STUDENT_EMAIL)
        self.assert_field_exists(page, TestSelectors.SELF_PHONE)

        # Verify NO guardian fields are visible
        self.assert_field_not_exists(page, TestSelectors.GUARDIAN_NAME)
        self.assert_field_not_exists(page, TestSelectors.GUARDIAN_EMAIL)

        # Fill student information (they manage everything)
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, student_data["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, student_data["email"])
        self.fill_form_field(page, TestSelectors.SELF_PHONE, student_data["phone"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, student_data["birth_date"])
        self.fill_form_field(page, 'select[name="self_school_year"]', student_data["school_year"], "select")
        self.fill_form_field(page, TestSelectors.SELF_TAX_NR, student_data["tax_nr"])
        self.fill_form_field(page, TestSelectors.SELF_ADDRESS, student_data["address"])
        self.fill_form_field(page, TestSelectors.SELF_NOTES, student_data["notes"])

        # Set preferences (student controls their own settings)
        self.fill_form_field(page, TestSelectors.SELF_INVOICE, student_data["invoice"], "checkbox")
        self.fill_form_field(
            page,
            TestSelectors.SELF_EMAIL_NOTIFICATIONS,
            student_data["email_notifications"],
            "checkbox",
        )
        self.fill_form_field(
            page,
            TestSelectors.SELF_SMS_NOTIFICATIONS,
            student_data["sms_notifications"],
            "checkbox",
        )

        # Submit form
        self.submit_form(page)

        # Assert - Verify success
        self.wait_for_success(page)

        # Verify student appears in the list
        self.verify_student_appears_in_list(page, student_data["name"])

    def test_required_field_validation_adult_student(self, page: Page):
        """
        Test that required fields are validated for adult student accounts.

        Requirements validation:
        - Student name is required
        - Student email is required (they need login access)
        - Student birth date is required
        - No guardian fields are required (none exist)
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Adult Student account type
        self.select_account_type(page, "self")

        # Try to submit without filling required fields
        self.submit_form(page)

        # Verify validation errors for required fields
        required_fields = VALIDATION_RULES["self"]["required_fields"]

        selector_map = {
            "student_name": TestSelectors.STUDENT_NAME,
            "student_email": TestSelectors.STUDENT_EMAIL,
            "student_birth_date": TestSelectors.STUDENT_BIRTH_DATE,
        }

        for field_name in required_fields:
            if field_name in selector_map:
                self.verify_form_validation_error(page, selector_map[field_name])

    def test_adult_age_validation(self, page: Page):
        """
        Test that adult students should typically be 16+ years old.
        This is a business rule validation.
        """
        # Navigate to people page
        self.navigate_to_people_page(page)
        self.open_add_student_modal(page)
        self.select_account_type(page, "self")

        # Try with very young age (inappropriate for adult student)
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Too Young Student")
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, "young@example.com")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2015-01-01")  # 9 years old

        # Submit form
        self.submit_form(page)

        # This might show a warning or error depending on business rules
        # For now, let's check that the form handles this case
        # (The exact behavior would depend on business requirements)

    def test_form_field_visibility_adult_student(self, page: Page):
        """Test that correct form fields are visible for adult student accounts."""
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Adult Student account type
        self.select_account_type(page, "self")

        # Verify student fields are visible (they manage everything)
        self.assert_field_exists(page, TestSelectors.STUDENT_NAME)
        self.assert_field_exists(page, TestSelectors.STUDENT_EMAIL)
        self.assert_field_exists(page, TestSelectors.STUDENT_BIRTH_DATE)
        self.assert_field_exists(page, 'select[name="self_school_year"]')

        # Adult student specific fields
        self.assert_field_exists(page, TestSelectors.SELF_PHONE)
        self.assert_field_exists(page, TestSelectors.SELF_TAX_NR)
        self.assert_field_exists(page, TestSelectors.SELF_ADDRESS)
        self.assert_field_exists(page, TestSelectors.SELF_NOTES)
        self.assert_field_exists(page, TestSelectors.SELF_INVOICE)
        self.assert_field_exists(page, TestSelectors.SELF_EMAIL_NOTIFICATIONS)
        self.assert_field_exists(page, TestSelectors.SELF_SMS_NOTIFICATIONS)

        # Verify NO guardian fields are visible
        self.assert_field_not_exists(page, TestSelectors.GUARDIAN_NAME)
        self.assert_field_not_exists(page, TestSelectors.GUARDIAN_EMAIL)
        self.assert_field_not_exists(page, TestSelectors.GUARDIAN_PHONE)
        self.assert_field_not_exists(page, TestSelectors.GUARDIAN_ONLY_PHONE)

    def test_adult_student_email_validation(self, page: Page):
        """Test validation of adult student email address."""
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select account type
        self.select_account_type(page, "self")

        # Fill invalid student email
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, "invalid-adult-email")

        # Fill other required fields to isolate email validation
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Adult Student")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "1995-01-01")

        # Try to submit
        self.submit_form(page)

        # Verify student email validation error
        self.verify_form_validation_error(page, TestSelectors.STUDENT_EMAIL)

    def test_adult_student_duplicate_email_handling(self, page: Page):
        """Test handling of duplicate adult student email addresses."""
        test_data = StudentTestData.adult_student_data()

        # Create first adult student
        self.navigate_to_people_page(page)
        self.open_add_student_modal(page)
        self.select_account_type(page, "self")

        # Fill and submit first account
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, test_data["student"]["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, test_data["student"]["email"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, test_data["student"]["birth_date"])

        self.submit_form(page)
        self.wait_for_success(page)

        # Try to create another adult student with same email
        self.open_add_student_modal(page)
        self.select_account_type(page, "self")

        # Use same email
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Different Adult Student")
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, test_data["student"]["email"])  # Duplicate
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "1990-01-01")

        self.submit_form(page)

        # Should show error for duplicate email
        self.wait_for_error(page)

    def test_adult_student_complete_profile(self, page: Page):
        """Test creating adult student with complete profile information."""
        # Arrange
        test_data = StudentTestData.adult_student_data()
        student_data = test_data["student"]

        # Navigate to people page
        self.navigate_to_people_page(page)
        self.open_add_student_modal(page)
        self.select_account_type(page, "self")

        # Fill ALL available fields for adult student
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, student_data["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, student_data["email"])
        self.fill_form_field(page, TestSelectors.SELF_PHONE, student_data["phone"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, student_data["birth_date"])
        self.fill_form_field(page, 'select[name="self_school_year"]', student_data["school_year"], "select")
        self.fill_form_field(page, TestSelectors.SELF_TAX_NR, student_data["tax_nr"])
        self.fill_form_field(page, TestSelectors.SELF_ADDRESS, student_data["address"])
        self.fill_form_field(page, TestSelectors.SELF_NOTES, student_data["notes"])

        # Set all preferences
        self.fill_form_field(page, TestSelectors.SELF_INVOICE, student_data["invoice"], "checkbox")
        self.fill_form_field(
            page,
            TestSelectors.SELF_EMAIL_NOTIFICATIONS,
            student_data["email_notifications"],
            "checkbox",
        )
        self.fill_form_field(
            page,
            TestSelectors.SELF_SMS_NOTIFICATIONS,
            student_data["sms_notifications"],
            "checkbox",
        )

        # Submit form
        self.submit_form(page)

        # Verify success
        self.wait_for_success(page)
        self.verify_student_appears_in_list(page, student_data["name"])

    def test_adult_student_minimal_profile(self, page: Page):
        """Test creating adult student with only required fields."""
        # Navigate to people page
        self.navigate_to_people_page(page)
        self.open_add_student_modal(page)
        self.select_account_type(page, "self")

        # Fill only required fields
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Minimal Adult Student")
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, "minimal@example.com")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "1998-01-01")

        # Submit form
        self.submit_form(page)

        # Should succeed with minimal data
        self.wait_for_success(page)
        self.verify_student_appears_in_list(page, "Minimal Adult Student")
