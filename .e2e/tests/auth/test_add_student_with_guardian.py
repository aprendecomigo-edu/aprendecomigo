"""
E2E tests for adding Student with Guardian account type.

This test validates the complete workflow for creating a student account
where both the student and guardian get separate login accounts.
"""

from fixtures.test_data import VALIDATION_RULES, StudentTestData, TestSelectors
from playwright.sync_api import Page, expect
import pytest
from utils.base_test import BaseE2ETest


class TestAddStudentWithGuardian(BaseE2ETest):
    """Test suite for Student with Guardian account creation"""

    def test_successful_student_with_guardian_creation(self, page: Page):
        """
        Test successful creation of student with guardian account.

        Requirements:
        - Student gets their own login account with access to classes
        - Guardian gets their own login account with payment permissions
        - Both accounts should be created successfully
        """
        # Arrange
        test_data = StudentTestData.student_with_guardian_data()
        student_data = test_data["student"]
        guardian_data = test_data["guardian"]

        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Act - Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Verify correct form sections are visible
        self.assert_field_exists(page, TestSelectors.STUDENT_NAME)
        self.assert_field_exists(page, TestSelectors.STUDENT_EMAIL)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_NAME)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_EMAIL)

        # Fill student information
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, student_data["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, student_data["email"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, student_data["birth_date"])
        self.fill_form_field(page, TestSelectors.STUDENT_SCHOOL_YEAR, student_data["school_year"], "select")
        self.fill_form_field(page, TestSelectors.STUDENT_NOTES, student_data["notes"])

        # Fill guardian information
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, guardian_data["name"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, guardian_data["email"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_PHONE, guardian_data["phone"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_TAX_NR, guardian_data["tax_nr"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_ADDRESS, guardian_data["address"])

        # Set preferences
        self.fill_form_field(page, TestSelectors.GUARDIAN_INVOICE, guardian_data["invoice"], "checkbox")
        self.fill_form_field(
            page,
            TestSelectors.GUARDIAN_EMAIL_NOTIFICATIONS,
            guardian_data["email_notifications"],
            "checkbox",
        )
        self.fill_form_field(
            page,
            TestSelectors.GUARDIAN_SMS_NOTIFICATIONS,
            guardian_data["sms_notifications"],
            "checkbox",
        )

        # Submit form
        self.submit_form(page)

        # Assert - Verify success
        self.wait_for_success(page)

        # Verify student appears in the list
        self.verify_student_appears_in_list(page, student_data["name"])

    def test_required_field_validation_separate_accounts(self, page: Page):
        """
        Test that required fields are validated for separate accounts.

        Requirements validation:
        - Student name is required
        - Student email is required
        - Student birth date is required
        - Guardian name is required
        - Guardian email is required
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Try to submit without filling required fields
        self.submit_form(page)

        # Verify validation errors for required fields
        required_fields = VALIDATION_RULES["separate"]["required_fields"]

        selector_map = {
            "student_name": TestSelectors.STUDENT_NAME,
            "student_email": TestSelectors.STUDENT_EMAIL,
            "student_birth_date": TestSelectors.STUDENT_BIRTH_DATE,
            "guardian_name": TestSelectors.GUARDIAN_NAME,
            "guardian_email": TestSelectors.GUARDIAN_EMAIL,
        }

        for field_name in required_fields:
            if field_name in selector_map:
                self.verify_form_validation_error(page, selector_map[field_name])

    def test_invalid_email_validation(self, page: Page):
        """Test validation of invalid email addresses."""
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select account type
        self.select_account_type(page, "separate")

        # Fill invalid email addresses
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, "invalid-email")
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, "also-invalid")

        # Fill other required fields to isolate email validation
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Test Student")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2010-01-01")
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, "Test Guardian")

        # Try to submit
        self.submit_form(page)

        # Verify email validation errors
        self.verify_form_validation_error(page, TestSelectors.STUDENT_EMAIL)
        self.verify_form_validation_error(page, TestSelectors.GUARDIAN_EMAIL)

    def test_duplicate_email_handling(self, page: Page):
        """Test handling of duplicate email addresses."""
        # First, create a student successfully
        test_data = StudentTestData.student_with_guardian_data()

        # Navigate and create first student
        self.navigate_to_people_page(page)
        self.open_add_student_modal(page)
        self.select_account_type(page, "separate")

        # Fill and submit first student
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, test_data["student"]["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, test_data["student"]["email"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, test_data["student"]["birth_date"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, test_data["guardian"]["name"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, test_data["guardian"]["email"])

        self.submit_form(page)
        self.wait_for_success(page)

        # Now try to create another student with the same email
        self.open_add_student_modal(page)
        self.select_account_type(page, "separate")

        # Use same emails
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Different Student")
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, test_data["student"]["email"])  # Duplicate
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2011-01-01")
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, "Different Guardian")
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, test_data["guardian"]["email"])  # Duplicate

        self.submit_form(page)

        # Should show error for duplicate emails
        self.wait_for_error(page)

    def test_cancel_modal(self, page: Page):
        """Test canceling the add student modal."""
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Fill some data
        self.select_account_type(page, "separate")
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Test Student")

        # Cancel modal
        self.close_modal(page)

        # Verify modal is closed and form is reset
        modal = page.locator(TestSelectors.MODAL_TITLE)
        expect(modal).not_to_be_visible()

    def test_form_field_visibility_separate_accounts(self, page: Page):
        """Test that correct form fields are visible for separate accounts."""
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Verify student section fields are visible
        self.assert_field_exists(page, TestSelectors.STUDENT_NAME)
        self.assert_field_exists(page, TestSelectors.STUDENT_EMAIL)
        self.assert_field_exists(page, TestSelectors.STUDENT_BIRTH_DATE)
        self.assert_field_exists(page, TestSelectors.STUDENT_SCHOOL_YEAR)
        self.assert_field_exists(page, TestSelectors.STUDENT_NOTES)

        # Verify guardian section fields are visible
        self.assert_field_exists(page, TestSelectors.GUARDIAN_NAME)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_EMAIL)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_PHONE)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_TAX_NR)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_ADDRESS)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_INVOICE)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_EMAIL_NOTIFICATIONS)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_SMS_NOTIFICATIONS)

        # Verify other account type specific fields are NOT visible
        self.assert_field_not_exists(page, TestSelectors.SELF_PHONE)
        self.assert_field_not_exists(page, TestSelectors.GUARDIAN_ONLY_PHONE)
