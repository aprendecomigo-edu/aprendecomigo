"""
E2E tests for Multiple Guardians functionality.

This test suite focuses specifically on testing the new multiple guardians
features across both Student+Guardian and Guardian-Only account types.
"""

from fixtures.test_data import VALIDATION_RULES, StudentTestData, TestSelectors
from playwright.sync_api import Page, expect
import pytest
from utils.base_test import BaseE2ETest


class TestMultipleGuardiansFunctionality(BaseE2ETest):
    """Test suite for Multiple Guardians functionality"""

    def test_maximum_guardians_limit(self, page: Page):
        """
        Test that there's a reasonable limit to how many guardians can be added.

        Requirements:
        - Should allow adding multiple guardians
        - Should have some reasonable limit (e.g., 5-10 guardians max)
        - UI should handle many guardians gracefully
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Fill minimal required student data
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Test Student")
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, "student@test.com")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2010-01-01")

        # Fill primary guardian
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, "Primary Guardian")
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, "primary@test.com")

        # Try to add multiple guardians (reasonable limit testing)
        add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)

        # Add up to 5 additional guardians
        for i in range(1, 6):
            # Check if button is still available
            if add_guardian_btn.is_visible():
                add_guardian_btn.click()

                # Fill basic info for each guardian
                self.fill_form_field(page, TestSelectors.guardian_field(i, "name"), f"Guardian {i + 1}")
                self.fill_form_field(page, TestSelectors.guardian_field(i, "email"), f"guardian{i + 1}@test.com")
            else:
                # If button disappeared, we hit the limit
                break

        # Submit form - should work with multiple guardians
        self.submit_form(page)
        self.wait_for_success(page)

    def test_guardian_email_uniqueness_across_forms(self, page: Page):
        """
        Test that guardian emails must be unique within the same form.

        Requirements:
        - Cannot have duplicate emails within same student form
        - Should show validation error for duplicate emails
        - Primary and additional guardians must have unique emails
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Fill minimal required student data
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, "Test Student")
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, "student@test.com")
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2010-01-01")

        # Fill primary guardian
        duplicate_email = "same@test.com"
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, "Primary Guardian")
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, duplicate_email)

        # Add additional guardian with same email
        add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)
        add_guardian_btn.click()

        self.fill_form_field(page, TestSelectors.guardian_field(1, "name"), "Additional Guardian")
        self.fill_form_field(page, TestSelectors.guardian_field(1, "email"), duplicate_email)  # Same email

        # Submit form
        self.submit_form(page)

        # Should show validation error for duplicate email
        self.wait_for_error(page)

    def test_guardian_permissions_inheritance(self, page: Page):
        """
        Test that guardian permissions are properly managed.

        Requirements:
        - Primary guardian has full permissions by default
        - Additional guardians start with limited permissions
        - Permissions can be customized independently
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

        # Check primary guardian permissions are checked by default
        bookings_checkbox = page.locator('input[name="guardian_0_can_manage_bookings"]')
        financial_checkbox = page.locator('input[name="guardian_0_can_view_financial_info"]')
        communication_checkbox = page.locator('input[name="guardian_0_can_communicate_with_teachers"]')

        expect(bookings_checkbox).to_be_checked()
        expect(financial_checkbox).to_be_checked()
        expect(communication_checkbox).to_be_checked()

        # Add additional guardian
        add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)
        add_guardian_btn.click()

        self.fill_form_field(page, TestSelectors.guardian_field(1, "name"), "Additional Guardian")
        self.fill_form_field(page, TestSelectors.guardian_field(1, "email"), "additional@test.com")

        # Additional guardian permissions should be unchecked by default (more restrictive)
        additional_bookings = page.locator('input[name="guardian_1_can_manage_bookings"]')
        additional_financial = page.locator('input[name="guardian_1_can_view_financial_info"]')
        additional_communication = page.locator('input[name="guardian_1_can_communicate_with_teachers"]')

        expect(additional_bookings).not_to_be_checked()
        expect(additional_financial).not_to_be_checked()
        expect(additional_communication).not_to_be_checked()

        # Customize additional guardian permissions
        additional_bookings.check()
        additional_communication.check()
        # Leave financial unchecked

        # Submit form
        self.submit_form(page)
        self.wait_for_success(page)

    def test_form_state_preservation_on_guardian_removal(self, page: Page):
        """
        Test that form state is preserved when removing guardians.

        Requirements:
        - Adding/removing guardians doesn't clear other form data
        - Guardian data in remaining fields is preserved
        - Form submission still works after guardian removal
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Fill student data first
        student_name = "Persistent Student"
        student_email = "persistent@test.com"
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, student_name)
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, student_email)
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, "2010-01-01")

        # Fill primary guardian
        primary_name = "Primary Guardian"
        primary_email = "primary@test.com"
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, primary_name)
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, primary_email)

        # Add two additional guardians
        add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)

        # Add first additional guardian
        add_guardian_btn.click()
        self.fill_form_field(page, TestSelectors.guardian_field(1, "name"), "Guardian 2")
        self.fill_form_field(page, TestSelectors.guardian_field(1, "email"), "guardian2@test.com")

        # Add second additional guardian
        add_guardian_btn.click()
        self.fill_form_field(page, TestSelectors.guardian_field(2, "name"), "Guardian 3")
        self.fill_form_field(page, TestSelectors.guardian_field(2, "email"), "guardian3@test.com")

        # Remove the first additional guardian (Guardian 2)
        remove_buttons = page.locator(TestSelectors.REMOVE_GUARDIAN_BUTTON)
        remove_buttons.first.click()

        # Verify student data is still there
        student_name_field = page.locator(TestSelectors.STUDENT_NAME)
        student_email_field = page.locator(TestSelectors.STUDENT_EMAIL)
        expect(student_name_field).to_have_value(student_name)
        expect(student_email_field).to_have_value(student_email)

        # Verify primary guardian data is still there
        primary_name_field = page.locator(TestSelectors.GUARDIAN_NAME)
        primary_email_field = page.locator(TestSelectors.GUARDIAN_EMAIL)
        expect(primary_name_field).to_have_value(primary_name)
        expect(primary_email_field).to_have_value(primary_email)

        # Verify one additional guardian remains (what was Guardian 3)
        # After removal, the remaining guardian should now be guardian_1
        remaining_guardian_name = page.locator(TestSelectors.guardian_field(1, "name"))
        remaining_guardian_email = page.locator(TestSelectors.guardian_field(1, "email"))
        expect(remaining_guardian_name).to_have_value("Guardian 3")
        expect(remaining_guardian_email).to_have_value("guardian3@test.com")

        # Submit form - should still work
        self.submit_form(page)
        self.wait_for_success(page)

    def test_guardian_section_visual_hierarchy(self, page: Page):
        """
        Test visual hierarchy and labeling of guardian sections.

        Requirements:
        - Primary guardian clearly labeled as "Primary"
        - Additional guardians numbered appropriately
        - Visual distinction between primary and additional
        - Remove buttons only on additional guardians
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Check primary guardian section has proper label
        primary_label = page.locator('text="Primary Guardian"')
        expect(primary_label).to_be_visible()

        # Primary guardian section should NOT have remove button
        primary_section = page.locator('[data-test="guardian-name-input"]').locator("../..")
        primary_remove_buttons = primary_section.locator(TestSelectors.REMOVE_GUARDIAN_BUTTON)
        expect(primary_remove_buttons).to_have_count(0)

        # Add additional guardian
        add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)
        add_guardian_btn.click()

        # Additional guardian should be labeled as "Additional Guardian 2"
        additional_label = page.locator('text="Additional Guardian"')
        expect(additional_label).to_be_visible()

        # Additional guardian should have remove button
        remove_btn = page.locator(TestSelectors.REMOVE_GUARDIAN_BUTTON)
        expect(remove_btn).to_be_visible()
        expect(remove_btn).to_have_count(1)

        # Add another guardian
        add_guardian_btn.click()

        # Should now have 2 remove buttons (one for each additional guardian)
        remove_buttons = page.locator(TestSelectors.REMOVE_GUARDIAN_BUTTON)
        expect(remove_buttons).to_have_count(2)

    def test_complex_family_scenario_mixed_permissions(self, page: Page):
        """
        Test a complex family scenario with mixed permissions.

        Scenario: Child with mother (primary), father, and grandmother
        - Mother: Full access (primary guardian)
        - Father: Bookings and communication, no financial
        - Grandmother: Communication only (emergency contact)
        """
        # Arrange
        test_data = {
            "student": {
                "name": "Sofia Complex",
                "email": "sofia.complex@test.com",
                "birth_date": "2012-05-15",
                "school_year": "6",
            },
            "guardians": [
                {
                    "name": "Ana Silva",
                    "email": "ana.silva@test.com",
                    "phone": "+351911000001",
                    "role": "Mother - Primary",
                    "permissions": {
                        "can_manage_bookings": True,
                        "can_view_financial_info": True,
                        "can_communicate_with_teachers": True,
                        "invoice": True,
                    },
                },
                {
                    "name": "João Silva",
                    "email": "joao.silva@test.com",
                    "phone": "+351911000002",
                    "role": "Father",
                    "permissions": {
                        "can_manage_bookings": True,
                        "can_view_financial_info": False,
                        "can_communicate_with_teachers": True,
                        "invoice": False,
                    },
                },
                {
                    "name": "Maria Santos",
                    "email": "maria.santos@test.com",
                    "phone": "+351911000003",
                    "role": "Grandmother - Emergency Contact",
                    "permissions": {
                        "can_manage_bookings": False,
                        "can_view_financial_info": False,
                        "can_communicate_with_teachers": True,
                        "invoice": False,
                    },
                },
            ],
        }

        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Fill student information
        self.fill_form_field(page, TestSelectors.STUDENT_NAME, test_data["student"]["name"])
        self.fill_form_field(page, TestSelectors.STUDENT_EMAIL, test_data["student"]["email"])
        self.fill_form_field(page, TestSelectors.STUDENT_BIRTH_DATE, test_data["student"]["birth_date"])
        self.fill_form_field(page, TestSelectors.STUDENT_SCHOOL_YEAR, test_data["student"]["school_year"], "select")

        # Fill primary guardian (mother)
        mother = test_data["guardians"][0]
        self.fill_form_field(page, TestSelectors.GUARDIAN_NAME, mother["name"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_EMAIL, mother["email"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_PHONE, mother["phone"])
        self.fill_form_field(page, TestSelectors.GUARDIAN_INVOICE, mother["permissions"]["invoice"], "checkbox")

        # Add and configure father
        add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)
        add_guardian_btn.click()

        father = test_data["guardians"][1]
        self.fill_form_field(page, TestSelectors.guardian_field(1, "name"), father["name"])
        self.fill_form_field(page, TestSelectors.guardian_field(1, "email"), father["email"])
        self.fill_form_field(page, TestSelectors.guardian_field(1, "phone"), father["phone"])

        # Set father's permissions
        self.fill_form_field(
            page,
            TestSelectors.guardian_field(1, "can_manage_bookings"),
            father["permissions"]["can_manage_bookings"],
            "checkbox",
        )
        self.fill_form_field(
            page,
            TestSelectors.guardian_field(1, "can_view_financial_info"),
            father["permissions"]["can_view_financial_info"],
            "checkbox",
        )
        self.fill_form_field(
            page,
            TestSelectors.guardian_field(1, "can_communicate_with_teachers"),
            father["permissions"]["can_communicate_with_teachers"],
            "checkbox",
        )

        # Add and configure grandmother
        add_guardian_btn.click()

        grandmother = test_data["guardians"][2]
        self.fill_form_field(page, TestSelectors.guardian_field(2, "name"), grandmother["name"])
        self.fill_form_field(page, TestSelectors.guardian_field(2, "email"), grandmother["email"])
        self.fill_form_field(page, TestSelectors.guardian_field(2, "phone"), grandmother["phone"])

        # Set grandmother's permissions (communication only)
        self.fill_form_field(
            page,
            TestSelectors.guardian_field(2, "can_manage_bookings"),
            grandmother["permissions"]["can_manage_bookings"],
            "checkbox",
        )
        self.fill_form_field(
            page,
            TestSelectors.guardian_field(2, "can_view_financial_info"),
            grandmother["permissions"]["can_view_financial_info"],
            "checkbox",
        )
        self.fill_form_field(
            page,
            TestSelectors.guardian_field(2, "can_communicate_with_teachers"),
            grandmother["permissions"]["can_communicate_with_teachers"],
            "checkbox",
        )

        # Submit form
        self.submit_form(page)

        # Assert success
        self.wait_for_success(page)

        # Verify student appears in the list
        self.verify_student_appears_in_list(page, test_data["student"]["name"])

    def test_guardian_form_accessibility_keyboard_navigation(self, page: Page):
        """
        Test basic keyboard accessibility for guardian forms.

        Requirements:
        - Tab navigation works through guardian fields
        - Add/remove buttons are keyboard accessible
        - Form submission works with keyboard
        """
        # Navigate to people page
        self.navigate_to_people_page(page)

        # Open add student modal
        self.open_add_student_modal(page)

        # Select Student with Guardian account type
        self.select_account_type(page, "separate")

        # Focus on student name field and tab through
        student_name_field = page.locator(TestSelectors.STUDENT_NAME)
        student_name_field.focus()

        # Fill student name using keyboard
        student_name_field.type("Keyboard Student")

        # Tab to next field (student email)
        student_name_field.press("Tab")
        student_email_field = page.locator(TestSelectors.STUDENT_EMAIL)
        expect(student_email_field).to_be_focused()

        # Continue filling required fields
        student_email_field.type("keyboard@test.com")
        student_email_field.press("Tab")

        birth_date_field = page.locator(TestSelectors.STUDENT_BIRTH_DATE)
        birth_date_field.type("2010-01-01")

        # Tab to guardian section
        guardian_name_field = page.locator(TestSelectors.GUARDIAN_NAME)
        guardian_name_field.focus()
        guardian_name_field.type("Keyboard Guardian")

        guardian_name_field.press("Tab")
        guardian_email_field = page.locator(TestSelectors.GUARDIAN_EMAIL)
        guardian_email_field.type("guardian@test.com")

        # Use keyboard to activate "Add Another Guardian" button
        add_guardian_btn = page.locator(TestSelectors.ADD_GUARDIAN_BUTTON)
        add_guardian_btn.focus()
        add_guardian_btn.press("Enter")  # Activate with keyboard

        # Verify additional guardian fields appeared
        additional_name_field = page.locator(TestSelectors.guardian_field(1, "name"))
        expect(additional_name_field).to_be_visible()

        # Submit form using keyboard
        submit_btn = page.locator(TestSelectors.SUBMIT_BUTTON)
        submit_btn.focus()
        submit_btn.press("Enter")

        # Should succeed
        self.wait_for_success(page)
