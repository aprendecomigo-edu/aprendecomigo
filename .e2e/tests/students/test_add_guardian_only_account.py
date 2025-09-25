"""
E2E tests for adding Guardian-Only account type.

This test validates the complete workflow for creating a guardian-only account
where only the guardian gets a login account and manages everything for the child.
"""

from fixtures.test_data import VALIDATION_RULES, StudentTestData, TestSelectors
from playwright.sync_api import Page, expect
import pytest
from utils.base_test import BaseE2ETest


class TestAddGuardianOnlyAccount(BaseE2ETest):
    """Test suite for Guardian-Only account creation"""

    def test_successful_guardian_only_creation(self, page: Page):
        """
        Test successful creation of guardian-only account.

        Requirements:
        - Student profile is created but NO login account
        - Guardian gets login account with full access to manage child
        - Guardian can access classes, schedule, AND financial information
        """
        # Arrange
        test_data = StudentTestData.guardian_only_data()
        student_data = test_data["student"]
        guardian_data = test_data["guardian"]

        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Act - Select Guardian-Only account type
        self.select_account_type(page, "guardian_only")

        # Verify correct form sections are visible
        self.assert_field_exists(page, TestSelectors.STUDENT_NAME)
        self.assert_field_not_exists(page, TestSelectors.STUDENT_EMAIL)  # Student doesn't get email
        self.assert_field_exists(page, TestSelectors.GUARDIAN_NAME)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_EMAIL)

        # Fill student basic information (no email/login)
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, student_data["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, student_data["birth_date"])
        self.fill_form_field(
            page, 'select[name="guardian_only_student_school_year"]', student_data["school_year"], "select"
        )
        self.fill_form_field(page, 'textarea[name="guardian_only_student_notes"]', student_data["notes"])

        # Fill guardian information (they get the login account)
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, guardian_data["name"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, guardian_data["email"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_ONLY_PHONE, guardian_data["phone"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_ONLY_TAX_NR, guardian_data["tax_nr"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_ONLY_ADDRESS, guardian_data["address"])

        # Set preferences
        self.fill_form_field(page, TestSelectors.GUARDIAN_ONLY_INVOICE, guardian_data["invoice"], "checkbox")
        self.fill_form_field(
            page,
            TestSelectors.GUARDIAN_ONLY_EMAIL_NOTIFICATIONS,
            guardian_data["email_notifications"],
            "checkbox",
        )
        self.fill_form_field(
            page,
            TestSelectors.GUARDIAN_ONLY_SMS_NOTIFICATIONS,
            guardian_data["sms_notifications"],
            "checkbox",
        )

        # Submit form
        self.submit_form(page)

        # Assert - Verify success
        self.wait_for_success(page)

        # Verify student appears in the list (managed by guardian)
        self.verify_student_appears_in_list(page, student_data["name"])

    def test_required_field_validation_guardian_only(self, page: Page):
        """
        Test that required fields are validated for guardian-only accounts.

        Requirements validation:
        - Student name is required
        - Student birth date is required (no email needed)
        - Guardian name is required
        - Guardian email is required
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Guardian-Only account type
        self.select_account_type(page, "guardian_only")

        # Try to submit without filling required fields
        self.submit_form(page)

        # Verify validation errors for required fields
        required_fields = VALIDATION_RULES["guardian_only"]["required_fields"]

        selector_map = {
            "student_name": TestSelectors.STUDENT_NAME,
            "student_birth_date": TestSelectors.STUDENT_BIRTH_DATE,
            "guardian_name": TestSelectors.GUARDIAN_NAME,
            "guardian_email": TestSelectors.GUARDIAN_EMAIL,
        }

        for field_name in required_fields:
            if field_name in selector_map:
                self.verify_form_validation_error(page, selector_map[field_name])

    def test_student_email_not_required_guardian_only(self, page: Page):
        """
        Test that student email is NOT required for guardian-only accounts.
        Only guardian email is required since they manage everything.
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Guardian-Only account type
        self.select_account_type(page, "guardian_only")

        # Fill only required fields (no student email)
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Young Student")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2015-01-01")
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, "Parent Guardian")
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, "parent@example.com")

        # Submit form
        self.submit_form(page)

        # Should succeed without student email
        self.wait_for_success(page)

    def test_form_field_visibility_guardian_only(self, page: Page):
        """Test that correct form fields are visible for guardian-only accounts."""
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Guardian-Only account type
        self.select_account_type(page, "guardian_only")

        # Verify student basic info fields are visible (no login fields)
        self.assert_field_exists(page, TestSelectors.STUDENT_NAME)
        self.assert_field_exists(page, TestSelectors.STUDENT_BIRTH_DATE)
        self.assert_field_exists(page, 'select[name="guardian_only_student_school_year"]')
        self.assert_field_exists(page, 'textarea[name="guardian_only_student_notes"]')

        # Student should NOT have email field (no login account)
        self.assert_field_not_exists(page, TestSelectors.STUDENT_EMAIL)

        # Verify guardian fields are visible (they get login account)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_NAME)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_EMAIL)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_ONLY_PHONE)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_ONLY_TAX_NR)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_ONLY_ADDRESS)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_ONLY_INVOICE)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_ONLY_EMAIL_NOTIFICATIONS)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_ONLY_SMS_NOTIFICATIONS)

        # Verify other account type specific fields are NOT visible
        self.assert_field_not_exists(page, TestSelectors.SELF_PHONE)
        self.assert_field_not_exists(page, TestSelectors.GUARDIAN_PHONE)  # Different naming convention

    def test_guardian_email_validation(self, page: Page):
        """Test validation of guardian email address."""
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select account type
        self.select_account_type(page, "guardian_only")

        # Fill invalid guardian email
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, "invalid-guardian-email")

        # Fill other required fields to isolate email validation
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Young Student")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2015-01-01")
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, "Test Guardian")

        # Try to submit
        self.submit_form(page)

        # Verify guardian email validation error
        self.verify_form_validation_error(page, TestSelectors.GUARDIAN_EMAIL)

    def test_young_student_age_handling(self, page: Page):
        """Test handling of very young student (under 13) - typical guardian-only case."""
        # Arrange
        test_data = StudentTestData.guardian_only_data()
        # Make student very young (6 years old)
        test_data["student"]["birth_date"] = "2018-01-01"
        test_data["student"]["school_year"] = "1"  # 1st grade

        # Navigate to people page
        self.navigate_to_people_page(page)
        self.open_add_student_modal(page)
        self.select_account_type(page, "guardian_only")

        # Fill form with young student data
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, test_data["student"]["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, test_data["student"]["birth_date"])
        self.fill_form_field(
            page, 'select[name="guardian_only_student_school_year"]', test_data["student"]["school_year"], "select"
        )

        # Fill guardian info
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, test_data["guardian"]["name"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, test_data["guardian"]["email"])

        # Submit form
        self.submit_form(page)

        # Should succeed - young students are perfect for guardian-only accounts
        self.wait_for_success(page)

    def test_guardian_duplicate_email_handling(self, page: Page):
        """Test handling of duplicate guardian email addresses."""
        test_data = StudentTestData.guardian_only_data()

        # Create first guardian-only account
        self.navigate_to_people_page(page)
        self.open_add_student_modal(page)
        self.select_account_type(page, "guardian_only")

        # Fill and submit first account
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, test_data["student"]["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, test_data["student"]["birth_date"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, test_data["guardian"]["name"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, test_data["guardian"]["email"])

        self.submit_form(page)
        self.wait_for_success(page)

        # Try to create another account with same guardian email
        self.open_add_student_modal(page)
        self.select_account_type(page, "guardian_only")

        # Use different student but same guardian email
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Different Child")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2016-01-01")
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, "Same Guardian")
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, test_data["guardian"]["email"])  # Duplicate

        self.submit_form(page)

        # Should show error for duplicate guardian email
        self.wait_for_error(page)
