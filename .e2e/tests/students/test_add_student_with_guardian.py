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

        # Fill primary guardian information (guardian_0_*)
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
            "guardian_0_name": TestSelectors.GUARDIAN_NAME,
            "guardian_0_email": TestSelectors.GUARDIAN_EMAIL,
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

    def test_multiple_guardians_creation(self, page: Page):
        """
        Test successful creation of student with multiple guardians.

        Requirements:
        - Primary guardian is always present and required
        - Additional guardians can be added dynamically
        - Each guardian has customizable permissions
        - All guardians are created successfully
        """
        # Arrange
        test_data = StudentTestData.multiple_guardians_data()
        student_data = test_data["student"]
        primary_guardian = test_data["primary_guardian"]
        additional_guardians = test_data["additional_guardians"]

        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Act - Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Fill student information
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, student_data["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, student_data["email"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, student_data["birth_date"])
        self.fill_form_field(page, TestSelectors.STUDENT_SCHOOL_YEAR, student_data["school_year"], "select")
        self.fill_form_field(page, TestSelectors.STUDENT_NOTES, student_data["notes"])

        # Fill primary guardian information
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, primary_guardian["name"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, primary_guardian["email"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_PHONE, primary_guardian["phone"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_TAX_NR, primary_guardian["tax_nr"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_ADDRESS, primary_guardian["address"])

        # Add additional guardians
        for i, guardian in enumerate(additional_guardians, 1):
            # Click "Add Another Guardian" button
            add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)
            add_guardian_btn.click()

            # Fill additional guardian information
            self.fill_form_field(page, TestSelectors.guardian_field(i, "name"), guardian["name"])
            self.fill_form_field(page, TestSelectors.guardian_field(i, "email"), guardian["email"])
            self.fill_form_field(page, TestSelectors.guardian_field(i, "phone"), guardian["phone"])
            self.fill_form_field(page, TestSelectors.guardian_field(i, "tax_nr"), guardian["tax_nr"])
            self.fill_form_field(page, TestSelectors.guardian_textarea_field(i, "address"), guardian["address"])

            # Set permissions for additional guardian
            if guardian.get("can_manage_bookings", False):
                self.fill_form_field(page, TestSelectors.guardian_field(i, "can_manage_bookings"), True, "checkbox")
            if guardian.get("can_view_financial_info", False):
                self.fill_form_field(page, TestSelectors.guardian_field(i, "can_view_financial_info"), True, "checkbox")
            if guardian.get("can_communicate_with_teachers", False):
                self.fill_form_field(
                    page, TestSelectors.guardian_field(i, "can_communicate_with_teachers"), True, "checkbox"
                )
            if guardian.get("email_notifications", False):
                self.fill_form_field(page, TestSelectors.guardian_field(i, "email_notifications"), True, "checkbox")
            if guardian.get("sms_notifications", False):
                self.fill_form_field(page, TestSelectors.guardian_field(i, "sms_notifications"), True, "checkbox")

        # Submit form
        self.submit_form(page)

        # Assert - Verify success
        self.wait_for_success(page)

        # Verify student appears in the list
        self.verify_student_appears_in_list(page, student_data["name"])

    def test_add_and_remove_guardian_buttons(self, page: Page):
        """
        Test the functionality of adding and removing guardians.

        Requirements:
        - "Add Another Guardian" button works
        - Remove buttons appear for additional guardians
        - Primary guardian cannot be removed
        - Form fields appear/disappear correctly
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Initially, only primary guardian should be visible
        self.assert_field_exists(page, TestSelectors.GUARDIAN_NAME)
        self.assert_field_exists(page, TestSelectors.GUARDIAN_EMAIL)

        # No additional guardian fields should exist
        self.assert_field_not_exists(page, TestSelectors.guardian_field(1, "name"))

        # Click "Add Another Guardian" button
        add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)
        add_guardian_btn.click()

        # Additional guardian fields should now exist
        self.assert_field_exists(page, TestSelectors.guardian_field(1, "name"))
        self.assert_field_exists(page, TestSelectors.guardian_field(1, "email"))

        # Remove button should be visible for additional guardian
        remove_btn = page.locator(TestSelectors.REMOVE_GUARDIAN_BUTTON).first
        expect(remove_btn).to_be_visible()

        # Click remove button
        remove_btn.click()

        # Additional guardian fields should be gone
        self.assert_field_not_exists(page, TestSelectors.guardian_field(1, "name"))

        # Primary guardian should still be there
        self.assert_field_exists(page, TestSelectors.GUARDIAN_NAME)

    def test_primary_guardian_cannot_be_removed(self, page: Page):
        """
        Test that the primary guardian section has no remove button.

        Requirements:
        - Primary guardian section should not have a remove button
        - Primary guardian fields should always be visible
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Primary guardian should be visible
        self.assert_field_exists(page, TestSelectors.GUARDIAN_NAME)

        # There should be no remove button in the primary guardian section
        # We look for remove buttons that would be near the primary guardian fields
        primary_guardian_section = page.locator('[data-test="guardian-name-input"]').locator("..").locator("..")
        remove_buttons_in_primary = primary_guardian_section.locator(TestSelectors.REMOVE_GUARDIAN_BUTTON)
        expect(remove_buttons_in_primary).to_have_count(0)

    def test_guardian_permissions_customization(self, page: Page):
        """
        Test that guardian permissions can be customized independently.

        Requirements:
        - Primary guardian has full permissions by default
        - Additional guardians can have custom permissions
        - Permission checkboxes work correctly
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Fill minimal required data
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Test Student")
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, "student@test.com")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2010-01-01")
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, "Primary Guardian")
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, "primary@test.com")

        # Add an additional guardian
        add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)
        add_guardian_btn.click()

        # Fill additional guardian basic info
        self.fill_form_field(page, TestSelectors.guardian_field(1, "name"), "Additional Guardian")
        self.fill_form_field(page, TestSelectors.guardian_field(1, "email"), "additional@test.com")

        # Customize permissions for additional guardian
        # Give limited permissions (not all like primary guardian)
        bookings_checkbox = page.locator(TestSelectors.guardian_field(1, "can_manage_bookings"))
        financial_checkbox = page.locator(TestSelectors.guardian_field(1, "can_view_financial_info"))
        communication_checkbox = page.locator(TestSelectors.guardian_field(1, "can_communicate_with_teachers"))

        # Check can_manage_bookings but not financial info
        bookings_checkbox.check()
        financial_checkbox.uncheck()  # Explicitly uncheck
        communication_checkbox.check()

        # Submit form
        self.submit_form(page)

        # Should succeed with custom permissions
        self.wait_for_success(page)
