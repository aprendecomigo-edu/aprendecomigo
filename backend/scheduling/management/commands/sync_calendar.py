import sys

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from scheduling.google_calendar import get_calendar_service, sync_calendar_events

User = get_user_model()

# https://developers.google.com/workspace/calendar/api/guides/overview
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
            "--warn-placeholder",
            action="store_true",
            help="Show warnings about placeholder users created during sync",
        )
        parser.add_argument(
            "--admin-email",
            required=True,
            help="Email of admin user whose Google credentials should be used",
        )

    def test_handle(self, **options) -> str | None:
        calendar_id = options["calendar_id"]
        admin_email = options["admin_email"]
        service = get_calendar_service(admin_email)
        page_token = None
        while True:
            events = (
                service.events()
                .list(calendarId=calendar_id, pageToken=page_token)
                .execute()
            )
            for event in events["items"]:
                print(event)
            page_token = events.get("nextPageToken")
            if not page_token:
                break
        print("LEN EVENTS", len(events["items"]))

    def handle(self, **options):
        calendar_id = options["calendar_id"]
        warn_placeholder = options["warn_placeholder"]
        admin_email = options["admin_email"]

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
            self.stdout.write(
                self.style.SUCCESS(
                    f"Syncing events from calendar '{calendar_id}"
                    f"using {admin_email}'s Google account..."
                )
            )

            created, updated, total = sync_calendar_events(calendar_id, admin_email)

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
