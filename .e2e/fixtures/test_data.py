"""
Test data fixtures for E2E tests.
"""

from datetime import datetime
import random
from typing import Any


class StudentTestData:
    """Test data generator for student account creation tests"""

    @staticmethod
    def generate_unique_email(base: str) -> str:
        """Generate a unique email for testing"""
        timestamp = int(datetime.now().timestamp())
        random_num = random.randint(1000, 9999)  # nosec B311 - test data only
        return f"{base}.{timestamp}.{random_num}@e2e.test"

    @staticmethod
    def generate_phone() -> str:
        """Generate a test phone number"""
        return f"+351 9{random.randint(10000000, 99999999)}"  # nosec B311 - test data only

    @classmethod
    def student_with_guardian_data(cls) -> dict[str, Any]:
        """Test data for Student with Guardian account type (single guardian for backward compatibility)"""
        return {
            "account_type": "separate",
            "student": {
                "name": "João Silva E2E",
                "email": cls.generate_unique_email("student"),
                "birth_date": "2010-03-15",
                "school_year": "8",
                "notes": "Test student with separate guardian account",
            },
            "guardian": {
                "name": "Maria Silva E2E",
                "email": cls.generate_unique_email("guardian"),
                "phone": cls.generate_phone(),
                "tax_nr": "123456789",
                "address": "Rua da Escola, 123\n1000-001 Lisboa\nPortugal",
                "invoice": True,
                "email_notifications": True,
                "sms_notifications": False,
            },
        }

    @classmethod
    def guardian_only_data(cls) -> dict[str, Any]:
        """Test data for Guardian-Only account type (young student)"""
        return {
            "account_type": "guardian_only",
            "student": {
                "name": "Ana Costa E2E",
                "birth_date": "2015-07-22",
                "school_year": "3",
                "notes": "Young student - guardian manages everything",
            },
            "guardian": {
                "name": "Pedro Costa E2E",
                "email": cls.generate_unique_email("guardian-only"),
                "phone": cls.generate_phone(),
                "tax_nr": "987654321",
                "address": "Av. da República, 456\n4000-001 Porto\nPortugal",
                "invoice": False,
                "email_notifications": True,
                "sms_notifications": True,
            },
        }

    @classmethod
    def guardian_only_multiple_data(cls) -> dict[str, Any]:
        """Test data for Guardian-Only with Multiple Guardians"""
        return {
            "account_type": "guardian_only",
            "student": {
                "name": "Miguel Santos E2E",
                "birth_date": "2016-04-15",
                "school_year": "2",
                "notes": "Young student with divorced parents",
            },
            "primary_guardian": {
                "name": "Rita Santos E2E",
                "email": cls.generate_unique_email("primary-guardian-only"),
                "phone": cls.generate_phone(),
                "tax_nr": "123987456",
                "address": "Rua das Flores, 50\n1200-001 Lisboa\nPortugal",
                "invoice": True,
                "email_notifications": True,
                "sms_notifications": False,
            },
            "additional_guardians": [
                {
                    "name": "Carlos Santos E2E",
                    "email": cls.generate_unique_email("father-guardian-only"),
                    "phone": cls.generate_phone(),
                    "tax_nr": "654321987",
                    "address": "Rua dos Pinheiros, 75\n1300-001 Lisboa\nPortugal",
                    "can_manage_bookings": True,
                    "can_view_financial_info": False,
                    "can_communicate_with_teachers": True,
                    "invoice": False,
                    "email_notifications": True,
                    "sms_notifications": True,
                }
            ],
        }

    @classmethod
    def adult_student_data(cls) -> dict[str, Any]:
        """Test data for Adult Student account type"""
        return {
            "account_type": "self",
            "student": {
                "name": "Carlos Santos E2E",
                "email": cls.generate_unique_email("adult-student"),
                "phone": cls.generate_phone(),
                "birth_date": "1995-12-05",
                "school_year": "12",
                "tax_nr": "456789123",
                "address": "Rua dos Estudantes, 789\n3000-001 Coimbra\nPortugal",
                "notes": "Adult student managing own account",
                "invoice": True,
                "email_notifications": True,
                "sms_notifications": False,
            },
        }

    @classmethod
    def multiple_guardians_data(cls) -> dict[str, Any]:
        """Test data for Student with Multiple Guardians"""
        return {
            "account_type": "separate",
            "student": {
                "name": "Sofia Martins E2E",
                "email": cls.generate_unique_email("multi-student"),
                "birth_date": "2012-06-10",
                "school_year": "6",
                "notes": "Student with multiple guardians",
            },
            "primary_guardian": {
                "name": "Ana Martins E2E",
                "email": cls.generate_unique_email("primary-guardian"),
                "phone": cls.generate_phone(),
                "tax_nr": "111222333",
                "address": "Rua Principal, 100\n2000-001 Santarém\nPortugal",
                "invoice": True,
                "email_notifications": True,
                "sms_notifications": False,
            },
            "additional_guardians": [
                {
                    "name": "João Martins E2E",
                    "email": cls.generate_unique_email("father-guardian"),
                    "phone": cls.generate_phone(),
                    "tax_nr": "444555666",
                    "address": "Rua Secundária, 200\n2000-002 Santarém\nPortugal",
                    "can_manage_bookings": True,
                    "can_view_financial_info": False,
                    "can_communicate_with_teachers": True,
                    "invoice": False,
                    "email_notifications": True,
                    "sms_notifications": True,
                },
                {
                    "name": "Carla Silva E2E",
                    "email": cls.generate_unique_email("stepmother-guardian"),
                    "phone": cls.generate_phone(),
                    "tax_nr": "777888999",
                    "address": "Rua Terciária, 300\n2000-003 Santarém\nPortugal",
                    "can_manage_bookings": False,
                    "can_view_financial_info": False,
                    "can_communicate_with_teachers": True,
                    "invoice": False,
                    "email_notifications": False,
                    "sms_notifications": False,
                },
            ],
        }


class AdminTestData:
    """Test data for school admin login"""

    @staticmethod
    def get_school_admin_data() -> dict[str, str]:
        """Get school admin data for registration/login"""
        return {
            "school_name": "Test School E2E",
            "admin_name": "Test Admin E2E",
            "admin_email": "schooladmin.e2e@test.com",
            "admin_phone": "+351911223344",
        }

    @staticmethod
    def get_admin_credentials() -> dict[str, str]:
        """Get admin credentials for login"""
        return {"email": "schooladmin.e2e@test.com", "password": "TestPass123!"}


class TestSelectors:
    """CSS selectors and data-test attributes for E2E tests"""

    # Navigation and page elements
    ADD_STUDENT_BUTTON = '[data-test="add-student-button"]'
    MODAL_TITLE = '[role="dialog"] h3:has-text("Add New Student")'
    SUBMIT_BUTTON = '[data-test="submit-student-form"]'
    CANCEL_BUTTON = 'button:has-text("Cancel")'
    SUCCESS_MESSAGE = '[role="alert"].bg-green-100'
    ERROR_MESSAGE = '[role="alert"].bg-red-100'

    # Account type selection
    ACCOUNT_TYPE_SEPARATE = '[data-test="account-type-separate"]'
    ACCOUNT_TYPE_GUARDIAN_ONLY = '[data-test="account-type-guardian-only"]'
    ACCOUNT_TYPE_SELF = '[data-test="account-type-self"]'

    # Student fields
    STUDENT_NAME = '[data-test="student-name-input"]'
    STUDENT_EMAIL = '[data-test="student-email-input"]'
    STUDENT_BIRTH_DATE = '[data-test="student-birth-date-input"]'
    STUDENT_SCHOOL_YEAR = 'select[name="student_school_year"]'
    STUDENT_NOTES = 'textarea[name="student_notes"]'

    # Primary Guardian fields (guardian_0_*)
    GUARDIAN_NAME = '[data-test="guardian-name-input"]'  # Primary guardian name
    GUARDIAN_EMAIL = '[data-test="guardian-email-input"]'  # Primary guardian email
    GUARDIAN_PHONE = 'input[name="guardian_0_phone"]'
    GUARDIAN_TAX_NR = 'input[name="guardian_0_tax_nr"]'
    GUARDIAN_ADDRESS = 'textarea[name="guardian_0_address"]'
    GUARDIAN_INVOICE = 'input[name="guardian_0_invoice"]'
    GUARDIAN_EMAIL_NOTIFICATIONS = 'input[name="guardian_0_email_notifications"]'
    GUARDIAN_SMS_NOTIFICATIONS = 'input[name="guardian_0_sms_notifications"]'

    # Additional Guardian Management
    ADD_GUARDIAN_BUTTON = 'button:has-text("Add Another Guardian")'
    REMOVE_GUARDIAN_BUTTON = "button.text-red-600"  # Remove button styling

    # Guardian-only specific fields
    GUARDIAN_ONLY_PHONE = 'input[name="guardian_only_guardian_phone"]'
    GUARDIAN_ONLY_TAX_NR = 'input[name="guardian_only_guardian_tax_nr"]'
    GUARDIAN_ONLY_ADDRESS = 'textarea[name="guardian_only_guardian_address"]'
    GUARDIAN_ONLY_INVOICE = 'input[name="guardian_only_guardian_invoice"]'
    GUARDIAN_ONLY_EMAIL_NOTIFICATIONS = 'input[name="guardian_only_guardian_email_notifications"]'
    GUARDIAN_ONLY_SMS_NOTIFICATIONS = 'input[name="guardian_only_guardian_sms_notifications"]'

    # Adult student fields
    SELF_PHONE = 'input[name="self_phone"]'
    SELF_TAX_NR = 'input[name="self_tax_nr"]'
    SELF_ADDRESS = 'textarea[name="self_address"]'
    SELF_NOTES = 'textarea[name="self_notes"]'
    SELF_INVOICE = 'input[name="self_invoice"]'
    SELF_EMAIL_NOTIFICATIONS = 'input[name="self_email_notifications"]'
    SELF_SMS_NOTIFICATIONS = 'input[name="self_sms_notifications"]'

    # Dynamic Guardian Field Generators
    @staticmethod
    def guardian_field(guardian_index: int, field_name: str) -> str:
        """Generate dynamic guardian field selector"""
        return f'input[name="guardian_{guardian_index}_{field_name}"]'

    @staticmethod
    def guardian_textarea_field(guardian_index: int, field_name: str) -> str:
        """Generate dynamic guardian textarea field selector"""
        return f'textarea[name="guardian_{guardian_index}_{field_name}"]'


# Expected form validation requirements by account type
VALIDATION_RULES = {
    "separate": {
        "required_fields": [
            "student_name",
            "student_email",
            "student_birth_date",
            "guardian_0_name",
            "guardian_0_email",
        ],
        "creates_accounts": ["student", "guardian"],
        "description": "Both student and guardian get separate login accounts",
        "supports_multiple_guardians": True,
    },
    "guardian_only": {
        "required_fields": ["student_name", "student_birth_date", "guardian_0_name", "guardian_0_email"],
        "creates_accounts": ["guardian"],
        "description": "Only guardian gets login account, manages student profile",
        "supports_multiple_guardians": True,
    },
    "self": {
        "required_fields": ["student_name", "student_email", "student_birth_date"],
        "creates_accounts": ["student"],
        "description": "Adult student manages everything independently",
        "supports_multiple_guardians": False,
    },
}
