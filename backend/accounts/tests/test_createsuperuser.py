from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from accounts.models import CustomUser


class CreatesuperuserTest(TestCase):
    """Test the createsuperuser command."""

    @patch("accounts.models.CustomUserManager.create_superuser")
    def test_createsuperuser_command(self, mock_create_superuser):
        """Test the createsuperuser command with non-interactive mode."""
        # Set up the mock to handle the call correctly
        mock_create_superuser.return_value = CustomUser(
            email="admin@example.com", name="Admin", is_staff=True, is_superuser=True
        )

        out = StringIO()
        call_command(
            "createsuperuser", "--email=admin@example.com", "--name=Admin", "--noinput", stdout=out
        )

        # Verify the command output
        self.assertIn("Superuser created successfully", out.getvalue())

        # Verify that create_superuser was called correctly
        mock_create_superuser.assert_called()

        # Check the arguments that were passed to create_superuser
        args, kwargs = mock_create_superuser.call_args

        # In the real implementation, Django will pass everything as kwargs
        self.assertTrue("name" in kwargs)
        self.assertEqual(kwargs.get("name"), "Admin")

        # There might be an email in positional args or in kwargs, but it should be present
        email_in_args = len(args) > 0 and args[0] == "admin@example.com"
        email_in_kwargs = "email" in kwargs and kwargs["email"] == "admin@example.com"

        self.assertTrue(
            email_in_args or email_in_kwargs, "Email should be present either in args or kwargs"
        )
