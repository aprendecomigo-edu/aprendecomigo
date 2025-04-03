import sys

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from scheduling.google_calendar import sync_calendar_events

User = get_user_model()

# The specific calendar ID provided by the user
DEFAULT_CALENDAR_ID = "dc309a9a476f57f957195db9973a541536145780250442dd3aa8c1ff9010f47b@group.calendar.google.com"


class Command(BaseCommand):
    help = "Synchronize events from Google Calendar to the database using admin Google account"

    def add_arguments(self, parser):
        parser.add_argument(
            "--calendar_id",
            default=DEFAULT_CALENDAR_ID,
            help="ID of the calendar to sync from",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help=(
                "Number of days to fetch events for "
                "(ignored if both start-date and end-date are provided)"
            ),
        )
        parser.add_argument(
            "--warn-placeholder",
            action="store_true",
            help="Show warnings about placeholder users created during sync",
        )
        parser.add_argument(
            "--admin-email",
            required=True,
            help="Email of admin user whose Google credentials should be used",
        )
        parser.add_argument(
            "--start-date", help="Start date for fetching events (format: YYYY-MM-DD)"
        )
        parser.add_argument(
            "--end-date", help="End date for fetching events (format: YYYY-MM-DD)"
        )

    def handle(self, **options):
        calendar_id = options["calendar_id"]
        days = options["days"]
        warn_placeholder = options["warn_placeholder"]
        admin_email = options["admin_email"]
        start_date = options.get("start_date")
        end_date = options.get("end_date")

        # Check if admin has Google account connected
        try:
            SocialAccount.objects.get(user__email=admin_email, provider="google")
            self.stdout.write(
                self.style.SUCCESS(f"Found Google account for admin: {admin_email}")
            )
        except ObjectDoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    f"Admin user {admin_email} does not have a connected Google account. "
                    "Please connect one via the social login feature first."
                )
            )
            return

        # Capture standard output to track placeholder users
        original_stdout = sys.stdout
        placeholder_messages = []

        class PlaceholderCapturer:
            def write(self, message):
                if "placeholder" in message.lower():
                    placeholder_messages.append(message)
                original_stdout.write(message)

            def flush(self):
                original_stdout.flush()

        # Redirect stdout to capture placeholder messages
        if warn_placeholder:
            sys.stdout = PlaceholderCapturer()

        try:
            # Determine message based on date parameters
            if start_date and end_date:
                date_message = f"from {start_date} to {end_date}"
            elif start_date:
                date_message = f"from {start_date} for {days} days"
            elif end_date:
                date_message = f"until {end_date}"
            else:
                date_message = f"for the next {days} days"

            self.stdout.write(
                self.style.SUCCESS(
                    f"Syncing events from calendar '{calendar_id}' {date_message} "
                    f"using {admin_email}'s Google account..."
                )
            )

            created, updated, total = sync_calendar_events(
                calendar_id, days, admin_email, start_date, end_date
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Calendar sync completed: {created} created, {updated} updated, "
                    f"{total} total events processed"
                )
            )

            # Show summary of placeholder users if any were created
            if warn_placeholder and placeholder_messages:
                self.stdout.write(self.style.WARNING("\nPlaceholder users created:"))
                for msg in placeholder_messages:
                    self.stdout.write(self.style.WARNING(f"  - {msg.strip()}"))

                self.stdout.write(
                    self.style.WARNING(
                        "\nPlease note: These users need to complete their profiles. "
                        "They have been assigned temporary email addresses and minimal information."
                    )
                )
        finally:
            # Restore stdout
            if warn_placeholder:
                sys.stdout = original_stdout
