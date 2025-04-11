from io import StringIO
from unittest.mock import MagicMock, patch

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

User = get_user_model()

# Use a simple fake calendar ID for testing
TEST_CALENDAR_ID = "test-calendar-id@example.com"


class SyncCalendarCommandTest(TestCase):
    """Test the sync_calendar management command"""

    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass",
            name="Admin User",
            is_admin=True,
        )

        # Mock SocialAccount for admin user
        self.social_account = MagicMock(spec=SocialAccount)
        self.social_account.user = self.admin_user

    @patch("scheduling.management.commands.sync_calendar.sync_calendar_events")
    @patch("scheduling.management.commands.sync_calendar.SocialAccount")
    @patch(
        "scheduling.management.commands.sync_calendar.DEFAULT_CALENDAR_ID",
        TEST_CALENDAR_ID,
    )
    def test_sync_calendar_command(self, mock_social_account, mock_sync_events):
        """Test the sync_calendar command basics"""
        # Setup mocks
        mock_social_account.objects.get.return_value = self.social_account
        mock_sync_events.return_value = (10, 5, 15)  # created, updated, total

        # Call the command
        out = StringIO()
        call_command(
            "sync_calendar", "--admin-email=admin@test.com", "--days=7", stdout=out
        )

        # Check output messages
        output = out.getvalue()
        self.assertIn("Found Google account for admin: admin@test.com", output)
        self.assertIn(
            "Calendar sync completed: 10 created, 5 updated, 15 total events processed",
            output,
        )

        # Verify sync_calendar_events was called with correct arguments
        mock_sync_events.assert_called_once_with(
            TEST_CALENDAR_ID,
            7,
            "admin@test.com",
            None,
            None,  # Use test calendar ID
        )

    @patch("scheduling.management.commands.sync_calendar.sync_calendar_events")
    @patch("scheduling.management.commands.sync_calendar.SocialAccount")
    @patch(
        "scheduling.management.commands.sync_calendar.DEFAULT_CALENDAR_ID",
        TEST_CALENDAR_ID,
    )
    def test_sync_calendar_with_date_range(self, mock_social_account, mock_sync_events):
        """Test the sync_calendar command with date range parameters"""
        # Setup mocks
        mock_social_account.objects.get.return_value = self.social_account
        mock_sync_events.return_value = (5, 0, 5)  # created, updated, total

        # Call the command with date range
        out = StringIO()
        call_command(
            "sync_calendar",
            "--admin-email=admin@test.com",
            "--start-date=2023-04-01",
            "--end-date=2023-04-30",
            stdout=out,
        )

        # Check output messages
        output = out.getvalue()
        self.assertIn("Found Google account for admin: admin@test.com", output)
        self.assertIn("from 2023-04-01 to 2023-04-30", output)
        self.assertIn(
            "Calendar sync completed: 5 created, 0 updated, 5 total events processed",
            output,
        )

        # Verify sync_calendar_events was called with correct arguments including dates
        mock_sync_events.assert_called_once_with(
            TEST_CALENDAR_ID,  # Use test calendar ID
            30,  # default days value
            "admin@test.com",
            "2023-04-01",
            "2023-04-30",
        )

    @patch("scheduling.management.commands.sync_calendar.SocialAccount")
    def test_sync_calendar_missing_google_account(self, mock_social_account):
        """Test command behavior when admin doesn't have a Google account"""
        # Setup mock to raise exception
        mock_social_account.objects.get.side_effect = SocialAccount.DoesNotExist

        # Call command
        out = StringIO()
        err = StringIO()
        call_command(
            "sync_calendar", "--admin-email=admin@test.com", stdout=out, stderr=err
        )

        # Check error output
        error_output = err.getvalue()
        self.assertIn("does not have a connected Google account", error_output)

    @patch("scheduling.management.commands.sync_calendar.sync_calendar_events")
    @patch("scheduling.management.commands.sync_calendar.SocialAccount")
    @patch(
        "scheduling.management.commands.sync_calendar.DEFAULT_CALENDAR_ID",
        TEST_CALENDAR_ID,
    )
    def test_sync_calendar_with_placeholder_warnings(
        self, mock_social_account, mock_sync_events
    ):
        """Test sync_calendar command with placeholder warnings"""
        # Setup mocks
        mock_social_account.objects.get.return_value = self.social_account

        # Make sync_events create a side effect that prints placeholder messages
        def side_effect():
            print(
                "Created placeholder teacher: teacher@placeholder.com "
                "(needs profile completion)"
            )
            print(
                "Created placeholder student: student@placeholder.com "
                "(needs profile completion)"
            )
            return (2, 0, 2)

        mock_sync_events.side_effect = side_effect

        # Call the command with placeholder warnings
        out = StringIO()
        call_command(
            "sync_calendar",
            "--admin-email=admin@test.com",
            "--warn-placeholder",
            stdout=out,
        )

        # Check output for placeholder warnings
        output = out.getvalue()
        self.assertIn("Placeholder users created:", output)
        self.assertIn("teacher@placeholder.com", output)
        self.assertIn("student@placeholder.com", output)
        self.assertIn("These users need to complete their profiles", output)
