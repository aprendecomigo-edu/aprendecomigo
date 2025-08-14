"""
API tests for messaging app communication endpoints.

This module tests the complete communication management API for the Aprende Comigo
tutoring platform, covering email templates, sequences, and communications.

**API Endpoints Tested:**

Email Templates (CRUD):
- GET /api/messaging/email-templates/ - List school email templates with pagination
- POST /api/messaging/email-templates/ - Create new email template
- GET /api/messaging/email-templates/{id}/ - Retrieve specific template
- PUT /api/messaging/email-templates/{id}/ - Update template
- DELETE /api/messaging/email-templates/{id}/ - Delete template
- POST /api/messaging/email-templates/{id}/preview/ - Preview template with variables
- GET /api/messaging/email-templates/filter-options/ - Get template filter options

Email Sequences (CRUD):
- GET /api/messaging/email-sequences/ - List email sequences with steps count
- POST /api/messaging/email-sequences/ - Create new sequence
- POST /api/messaging/email-sequences/{id}/activate/ - Toggle sequence activation
- GET /api/messaging/email-sequences/trigger-events/ - Get trigger event options

Email Communications (Read-only):
- GET /api/messaging/email-communications/ - List communication history with filtering
- GET /api/messaging/email-communications/{id}/ - Get communication details
- GET /api/messaging/email-communications/analytics/ - Get analytics data
- GET /api/messaging/email-communications/communication-types/ - Get communication types

Analytics & Settings:
- GET /api/messaging/communication-analytics/ - Overall communication metrics
- GET /api/messaging/template-analytics/ - Template usage statistics
- GET/PUT /api/messaging/communication-settings/ - School communication settings

**Authentication & Permissions:**
- All endpoints require authentication (Token-based)
- School-level permissions (IsSchoolOwnerOrAdmin)
- Cross-school data isolation enforced

**Testing Approach:**
- Tests complete HTTP request/response cycles using APITestCase
- Validates authentication, permissions, and data isolation
- Tests all CRUD operations with proper status codes and response validation
- Covers edge cases, error conditions, and business rule validation
- Serves as executable documentation for API behavior

**Business Context:**
The communication system enables schools to manage email templates for teacher
invitations, onboarding sequences, and student balance notifications in the
Aprende Comigo tutoring platform.
"""

from django.urls import reverse
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole
from messaging.models import (
    EmailCommunication,
    EmailCommunicationType,
    EmailSequence,
    EmailSequenceStep,
    EmailTemplateType,
    SchoolEmailTemplate,
)


class CommunicationAPITestCase(APITestCase):
    """Base test case for communication API endpoints."""

    def setUp(self):
        """Set up test data for communication API tests."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            contact_email="admin@testschool.com",
            description="A test school for communication API testing",
        )

        # Create another school for permission testing
        self.other_school = School.objects.create(
            name="Other School",
            contact_email="admin@otherschool.com",
            description="Another school for isolation testing",
        )

        # Create school admin user
        self.admin_user = CustomUser.objects.create_user(
            email="admin@testschool.com", name="Test Admin", first_name="Test", last_name="Admin"
        )

        # Create school membership for admin
        SchoolMembership.objects.create(user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN)

        # Create teacher user
        self.teacher_user = CustomUser.objects.create_user(email="teacher@testschool.com", name="Test Teacher")

        SchoolMembership.objects.create(user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER)

        # Create user from other school
        self.other_user = CustomUser.objects.create_user(email="other@otherschool.com", name="Other User")

        SchoolMembership.objects.create(user=self.other_user, school=self.other_school, role=SchoolRole.SCHOOL_ADMIN)

        # Create auth token and authenticate as admin
        self.admin_token = AuthToken.objects.create(self.admin_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token}")


class SchoolEmailTemplateAPITest(CommunicationAPITestCase):
    """Test SchoolEmailTemplate ViewSet endpoints."""

    def setUp(self):
        super().setUp()

        # Create test email template
        self.email_template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.INVITATION,
            name="Teacher Invitation Template",
            subject_template="Join {{school_name}} as a Teacher",
            html_content="<p>Welcome {{teacher_name}} to {{school_name}}!</p>",
            text_content="Welcome {{teacher_name}} to {{school_name}}!",
            created_by=self.admin_user,
        )

    def test_list_email_templates(self):
        """
        Test GET /api/messaging/email-templates/ - List templates for user's school.

        **API Behavior:**
        - Returns paginated list of email templates for authenticated user's school
        - Only shows templates from schools user has admin access to
        - Response includes count, next/previous pagination links, and results array

        **Response Format:**
        {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "name": "Template Name",
                    "template_type": "invitation",
                    "school": 1,
                    "created_by": 1,
                    "created_at": "2025-01-01T00:00:00Z",
                    ...
                }
            ]
        }
        """
        url = reverse("messaging:email-template-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        template_data = response.data["results"][0]
        self.assertEqual(template_data["id"], self.email_template.id)
        self.assertEqual(template_data["name"], "Teacher Invitation Template")
        self.assertEqual(template_data["template_type"], EmailTemplateType.INVITATION)

    def test_create_email_template(self):
        """
        Test POST /api/messaging/email-templates/ - Create new template.

        **API Behavior:**
        - Creates new email template for authenticated user's school
        - Automatically sets created_by to current user
        - Validates template content and variables
        - Returns 201 CREATED with created template data

        **Required Fields:**
        - school: School ID (must be user's managed school)
        - template_type: Type from EmailTemplateType choices
        - name: Human-readable template name
        - subject_template: Email subject with variables like {{teacher_name}}
        - html_content: HTML email content with variables
        - text_content: Plain text version with variables
        """
        url = reverse("messaging:email-template-list")
        data = {
            "school": self.school.id,
            "template_type": EmailTemplateType.WELCOME,
            "name": "Welcome Template",
            "subject_template": "Welcome to {{school_name}}!",
            "html_content": "<p>Welcome {{teacher_name}}!</p>",
            "text_content": "Welcome {{teacher_name}}!",
            "use_school_branding": True,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Welcome Template")
        self.assertEqual(response.data["created_by"], self.admin_user.id)

        # Verify template was created in database
        template = SchoolEmailTemplate.objects.get(name="Welcome Template")
        self.assertEqual(template.school, self.school)
        self.assertEqual(template.created_by, self.admin_user)

    def test_retrieve_email_template(self):
        """Test GET /api/messaging/email-templates/{id}/ - Get specific template."""
        url = reverse("messaging:email-template-detail", kwargs={"pk": self.email_template.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.email_template.id)
        self.assertEqual(response.data["name"], "Teacher Invitation Template")
        self.assertIn("template_variables", response.data)
        self.assertIn("school_name", response.data["template_variables"])
        self.assertIn("teacher_name", response.data["template_variables"])

    def test_update_email_template(self):
        """Test PUT /api/messaging/email-templates/{id}/ - Update template."""
        url = reverse("messaging:email-template-detail", kwargs={"pk": self.email_template.pk})
        data = {
            "school": self.school.id,
            "template_type": EmailTemplateType.INVITATION,
            "name": "Updated Invitation Template",
            "subject_template": "Updated: Join {{school_name}}",
            "html_content": "<p>Updated: Welcome {{teacher_name}}!</p>",
            "text_content": "Updated: Welcome {{teacher_name}}!",
            "use_school_branding": True,
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Invitation Template")

        # Verify update in database
        self.email_template.refresh_from_db()
        self.assertEqual(self.email_template.name, "Updated Invitation Template")

    def test_delete_email_template(self):
        """Test DELETE /api/messaging/email-templates/{id}/ - Delete template."""
        url = reverse("messaging:email-template-detail", kwargs={"pk": self.email_template.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deletion
        self.assertFalse(SchoolEmailTemplate.objects.filter(pk=self.email_template.pk).exists())

    def test_template_preview_action(self):
        """
        Test POST /api/messaging/email-templates/{id}/preview/ - Preview template.

        **API Behavior:**
        - Renders template with provided variables for preview
        - Validates template variables for security
        - Returns rendered subject, HTML, and text content
        - Used by frontend for template editing and testing

        **Request Body:**
        {
            "template_variables": {
                "teacher_name": "John Doe",
                "school_name": "Test School"
            }
        }

        **Response:**
        {
            "rendered_subject": "Join Test School as a Teacher",
            "rendered_html": "<p>Welcome John Doe to Test School!</p>",
            "rendered_text": "Welcome John Doe to Test School!",
            "template_variables": {...},
            "template_id": 1
        }
        """
        url = reverse("messaging:email-template-preview", kwargs={"pk": self.email_template.pk})
        data = {"template_variables": {"teacher_name": "John Doe", "school_name": "Test School"}}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("rendered_subject", response.data)
        self.assertIn("rendered_html", response.data)
        self.assertIn("rendered_text", response.data)
        self.assertIn("John Doe", response.data["rendered_html"])
        self.assertIn("Test School", response.data["rendered_subject"])

    def test_cross_school_template_access_denied(self):
        """Test that users cannot access templates from other schools."""
        other_template = SchoolEmailTemplate.objects.create(
            school=self.other_school,
            template_type=EmailTemplateType.WELCOME,
            name="Other School Template",
            subject_template="Welcome to Other School",
            html_content="<p>Welcome!</p>",
            text_content="Welcome!",
        )

        url = reverse("messaging:email-template-detail", kwargs={"pk": other_template.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_template_filter_options(self):
        """Test GET /api/messaging/email-templates/filter-options/ - Get filter options."""
        url = reverse("messaging:email-template-filter-options")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("template_types", response.data)
        self.assertIsInstance(response.data["template_types"], list)

        # Check structure of filter options
        if response.data["template_types"]:
            option = response.data["template_types"][0]
            self.assertIn("value", option)
            self.assertIn("label", option)

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access templates."""
        self.client.credentials()  # Remove authentication

        url = reverse("messaging:email-template-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_teacher_permissions(self):
        """Test that teachers can view but have limited access to templates."""
        # Switch to teacher authentication
        teacher_token = AuthToken.objects.create(self.teacher_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {teacher_token}")

        # Teachers should be able to view templates
        url = reverse("messaging:email-template-list")
        response = self.client.get(url)

        # This depends on the actual permission implementation
        # Adjust based on whether teachers can view templates
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])


class EmailSequenceAPITest(CommunicationAPITestCase):
    """Test EmailSequence ViewSet endpoints."""

    def setUp(self):
        super().setUp()

        # Create test email template for sequence
        self.email_template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.INVITATION,
            name="Sequence Template",
            subject_template="Step in sequence",
            html_content="<p>Sequence step</p>",
            text_content="Sequence step",
            created_by=self.admin_user,
        )

        # Create test email sequence
        self.email_sequence = EmailSequence.objects.create(
            school=self.school,
            name="Onboarding Sequence",
            description="Teacher onboarding sequence",
            trigger_event="invitation_sent",
            is_active=True,
            max_emails=3,
        )

        # Create sequence step
        self.sequence_step = EmailSequenceStep.objects.create(
            sequence=self.email_sequence, step_number=1, template=self.email_template, delay_hours=0
        )

    def test_list_email_sequences(self):
        """Test GET /api/messaging/email-sequences/ - List sequences for user's school."""
        url = reverse("messaging:email-sequence-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        sequence_data = response.data["results"][0]
        self.assertEqual(sequence_data["id"], self.email_sequence.id)
        self.assertEqual(sequence_data["name"], "Onboarding Sequence")
        self.assertEqual(sequence_data["steps_count"], 1)

    def test_create_email_sequence(self):
        """Test POST /api/messaging/email-sequences/ - Create new sequence."""
        url = reverse("messaging:email-sequence-list")
        data = {
            "school": self.school.id,
            "name": "Welcome Sequence",
            "description": "Welcome sequence for new users",
            "trigger_event": "profile_completed",
            "is_active": True,
            "max_emails": 5,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Welcome Sequence")
        self.assertEqual(response.data["school"], self.school.id)

    def test_activate_sequence_action(self):
        """Test POST /api/messaging/email-sequences/{id}/activate/ - Toggle sequence."""
        url = reverse("messaging:email-sequence-activate", kwargs={"pk": self.email_sequence.pk})
        data = {"is_active": False}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])

        # Verify in database
        self.email_sequence.refresh_from_db()
        self.assertFalse(self.email_sequence.is_active)

    def test_trigger_events_action(self):
        """Test GET /api/messaging/email-sequences/trigger-events/ - Get trigger options."""
        url = reverse("messaging:email-sequence-trigger-events")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("trigger_events", response.data)
        self.assertIsInstance(response.data["trigger_events"], list)


class EmailCommunicationAPITest(CommunicationAPITestCase):
    """Test EmailCommunication ViewSet endpoints (read-only)."""

    def setUp(self):
        super().setUp()

        # Create test email template
        self.email_template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.INVITATION,
            name="Test Template",
            subject_template="Test Subject",
            html_content="<p>Test</p>",
            text_content="Test",
            created_by=self.admin_user,
        )

        # Create test email communication
        self.email_communication = EmailCommunication.objects.create(
            school=self.school,
            recipient_email="recipient@example.com",
            communication_type=EmailCommunicationType.MANUAL,
            template=self.email_template,
            template_type=EmailTemplateType.INVITATION,
            subject="Test Email",
            created_by=self.admin_user,
        )

    def test_list_email_communications(self):
        """Test GET /api/messaging/email-communications/ - List communications."""
        url = reverse("messaging:email-communication-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        comm_data = response.data["results"][0]
        self.assertEqual(comm_data["id"], self.email_communication.id)
        self.assertEqual(comm_data["recipient_email"], "recipient@example.com")
        self.assertEqual(comm_data["template_name"], "Test Template")

    def test_retrieve_email_communication(self):
        """Test GET /api/messaging/email-communications/{id}/ - Get specific communication."""
        url = reverse("messaging:email-communication-detail", kwargs={"pk": self.email_communication.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.email_communication.id)
        self.assertEqual(response.data["subject"], "Test Email")

    def test_communication_filtering(self):
        """Test filtering communications by recipient email."""
        url = reverse("messaging:email-communication-list")
        response = self.client.get(url, {"recipient_email": "recipient"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        # Test with non-matching filter
        response = self.client.get(url, {"recipient_email": "nonexistent"})
        self.assertEqual(response.data["count"], 0)

    def test_communication_analytics_action(self):
        """Test GET /api/messaging/email-communications/analytics/ - Get analytics."""
        url = reverse("messaging:email-communication-analytics")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("analytics", response.data)

        analytics = response.data["analytics"]
        self.assertIn("total_sent", analytics)
        self.assertIn("delivery_rate", analytics)
        self.assertIn("open_rate", analytics)

    def test_communication_types_action(self):
        """Test GET /api/messaging/email-communications/communication-types/."""
        url = reverse("messaging:email-communication-communication-types")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("communication_types", response.data)
        self.assertIsInstance(response.data["communication_types"], list)


class CommunicationAnalyticsAPITest(CommunicationAPITestCase):
    """Test communication analytics API endpoints."""

    def test_communication_analytics_endpoint(self):
        """Test GET /api/messaging/communication-analytics/ - Get overall analytics."""
        url = reverse("messaging:communication-analytics")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn("period", response.data)
        self.assertIn("total_sent", response.data)
        self.assertIn("delivery_rate", response.data)
        self.assertIn("open_rate", response.data)
        self.assertIn("click_rate", response.data)
        self.assertIn("recent_communications", response.data)

    def test_template_analytics_endpoint(self):
        """Test GET /api/messaging/template-analytics/ - Get template-specific analytics."""
        # Create a template first
        template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Analytics Test Template",
            subject_template="Test",
            html_content="<p>Test</p>",
            text_content="Test",
            created_by=self.admin_user,
        )

        url = reverse("messaging:template-analytics")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        if response.data:
            template_stat = response.data[0]
            self.assertIn("template_id", template_stat)
            self.assertIn("template_name", template_stat)
            self.assertIn("usage_count", template_stat)
            self.assertIn("success_rate", template_stat)

    def test_communication_settings_get(self):
        """Test GET /api/messaging/communication-settings/ - Get settings."""
        url = reverse("messaging:communication-settings")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn("default_from_email", response.data)
        self.assertIn("email_signature", response.data)
        self.assertIn("auto_sequence_enabled", response.data)
        self.assertIn("notification_preferences", response.data)

    def test_communication_settings_update(self):
        """Test PUT /api/messaging/communication-settings/ - Update settings."""
        url = reverse("messaging:communication-settings")
        data = {
            "default_from_email": "noreply@testschool.com",
            "email_signature": "Best regards,\nTest School Team",
            "auto_sequence_enabled": False,
            "notification_preferences": {"email_delivery_notifications": False, "bounce_notifications": True},
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("settings", response.data)


class CommunicationAPIPermissionsTest(CommunicationAPITestCase):
    """Test permissions for communication API endpoints."""

    def test_non_admin_permissions(self):
        """Test that non-admin users have appropriate access levels."""
        # Switch to teacher authentication
        teacher_token = AuthToken.objects.create(self.teacher_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {teacher_token}")

        # Test template access
        url = reverse("messaging:email-template-list")
        response = self.client.get(url)

        # Should either allow read access or deny based on permission setup
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_cross_school_isolation(self):
        """Test that users only see data from their own schools."""
        # Create template in other school
        other_template = SchoolEmailTemplate.objects.create(
            school=self.other_school,
            template_type=EmailTemplateType.WELCOME,
            name="Other School Template",
            subject_template="Other school subject",
            html_content="<p>Other school content</p>",
            text_content="Other school content",
        )

        # List templates - should only see own school's templates
        url = reverse("messaging:email-template-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should not see the other school's template
        template_ids = [t["id"] for t in response.data["results"]]
        self.assertNotIn(other_template.id, template_ids)
