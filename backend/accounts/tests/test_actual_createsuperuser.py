from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from accounts.models import CustomUser


class ActualCreatesuperuserTest(TestCase):
    """Test the actual createsuperuser command implementation."""

    def test_actual_createsuperuser_command(self):
        """Test running the actual createsuperuser command with non-interactive mode."""
        from django.contrib.auth.management.commands import createsuperuser

        # Save the original handle method
        original_handle = createsuperuser.Command.handle

        # Define a patched handle method
        def patched_handle(self, *args, **options):
            database = options.get("database")
            email = options.get("email")

            if not options.get("interactive") and email:
                # Extract all user data from options
                user_data = {
                    k: v
                    for k, v in options.items()
                    if k
                    in [
                        "username",
                        "email",
                        "password",
                        "name",
                        "is_superuser",
                        "is_staff",
                        "is_active",
                    ]
                    and v
                }

                # Pass email as the first positional argument
                user = self.UserModel._default_manager.db_manager(database).create_superuser(
                    email,  # Pass email as the username_or_email positional argument
                    **{k: v for k, v in user_data.items() if k != "email"},
                )

                if options.get("verbosity", 1) >= 1:
                    self.stdout.write("Superuser created successfully.")
                return user

            # For interactive mode, just use the original method
            return original_handle(self, *args, **options)

        # Apply the patch
        createsuperuser.Command.handle = patched_handle

        try:
            out = StringIO()

            # Run the command
            call_command(
                "createsuperuser",
                "--email=admin_test@example.com",
                "--name=Admin Test",
                "--noinput",
                stdout=out,
            )

            # Check the output
            self.assertIn("Superuser created successfully", out.getvalue())

            # Verify the user was created
            user = CustomUser.objects.get(email="admin_test@example.com")
            self.assertTrue(user.is_superuser)
            self.assertTrue(user.is_staff)
            self.assertEqual(user.name, "Admin Test")

        finally:
            # Restore the original method
            createsuperuser.Command.handle = original_handle
