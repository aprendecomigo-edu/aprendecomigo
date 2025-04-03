import datetime

from allauth.socialaccount.models import SocialAccount, SocialToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from accounts.models import Student, Teacher

from .models import ClassSession, ClassType, Subject

# Scope required for Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

User = get_user_model()


def get_credentials(admin_email):
    """
    Get Google API credentials from a user's django-allauth social account

    Args:
        admin_email: Email of admin user whose Google credentials to use

    Returns:
        Google OAuth2 Credentials object or None if not available
    """
    if not admin_email:
        raise ValueError("Admin email is required for authentication")

    try:
        # Find the admin's social account
        social_account = SocialAccount.objects.get(
            user__email=admin_email, provider="google"
        )
        # Get their Google token
        social_token = SocialToken.objects.get(account=social_account)

        # Convert socialtoken to Google's Credentials format
        token_data = {
            "token": social_token.token,
            "refresh_token": social_token.token_secret,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"],
            "client_secret": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"][
                "secret"
            ],
            "scopes": SCOPES,
        }

        creds = Credentials(**token_data)
        print(f"Using Google credentials from admin account: {admin_email}")
        return creds

    except (ObjectDoesNotExist, KeyError) as e:
        raise ValueError(f"Could not get Google credentials for {admin_email}: {e}")


def get_calendar_service(admin_email):
    """Build and return a Google Calendar service object using admin credentials."""
    creds = get_credentials(admin_email)
    service = build("calendar", "v3", credentials=creds)
    return service


def parse_event_title(title):
    """
    Parse the event title to extract student name and attended status.
    Format example: "Tom Steadman" or "Tom Steadman - FALTOU"
    """
    # Default values
    student_name = title.strip()
    attended = True

    # Check if title contains absence marker
    if "FALTOU" in title:
        student_name = title.split(" - ")[0].strip()
        attended = False

    return {"student_name": student_name, "attended": attended}


def parse_event_location(location):
    """
    Parse the event location to extract teacher name.
    Format example: "Prof. Carla Almeida"
    """
    teacher_name = location.strip()

    # Remove "Prof. " prefix if it exists
    if teacher_name.startswith("Prof. "):
        teacher_name = teacher_name[6:]

    return teacher_name


def parse_event_description(description):
    """
    Parse the event description to get the class type code.
    The description itself is the class type code, which corresponds to a specific hourly rate.
    Example: "MATH101" or "CHEM_GROUP" or any other code defined in the system.

    Returns:
        class_type_code: The code representing the class type and its pricing
    """
    if not description or description.strip() == "":
        description = "DEFAULT"

    # The description is the class type code
    return description.strip()


def fetch_calendar_events(
    calendar_id, days=30, admin_email=None, start_date=None, end_date=None
):
    """
    Fetch events from Google Calendar and return parsed data.

    Args:
        calendar_id: ID of the calendar to fetch events from
        days: Number of days to fetch events for (forward)
        admin_email: Email of admin whose Google credentials to use
        start_date: Start date for fetching events (format: YYYY-MM-DD)
        end_date: End date for fetching events (format: YYYY-MM-DD)

    Returns:
        List of parsed events
    """
    try:
        service = get_calendar_service(admin_email)

        # Get time range based on parameters
        now = datetime.datetime.utcnow()

        # If start_date is provided, use it
        if start_date:
            try:
                # Parse the provided start date
                time_min = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                # Set to beginning of day in UTC
                time_min = time_min.replace(hour=0, minute=0, second=0, microsecond=0)
                time_min = time_min.isoformat() + "Z"
            except ValueError:
                print(f"Invalid start_date format: {start_date}. Using current date.")
                time_min = now.isoformat() + "Z"
        else:
            # Use current time as default
            time_min = now.isoformat() + "Z"  # 'Z' indicates UTC time

        # If end_date is provided, use it
        if end_date:
            try:
                # Parse the provided end date
                time_max = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                # Set to end of day in UTC
                time_max = time_max.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                time_max = time_max.isoformat() + "Z"
            except ValueError:
                print(f"Invalid end_date format: {end_date}. Using days parameter.")
                time_max = (now + datetime.timedelta(days=days)).isoformat() + "Z"
        else:
            # Use days parameter as default
            time_max = (now + datetime.timedelta(days=days)).isoformat() + "Z"

        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        parsed_events = []

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            title = event.get("summary", "")
            description = event.get("description", "")
            location = event.get("location", "")  # Teacher name is in location

            # Parse event data
            parsed_title = parse_event_title(title)
            parsed_location = parse_event_location(location)
            class_type_code = parse_event_description(description)

            parsed_events.append(
                {
                    "google_calendar_id": event["id"],
                    "title": title,
                    "start_time": start,
                    "end_time": end,
                    "teacher_name": parsed_location,
                    "student_name": parsed_title["student_name"],
                    "class_type_code": class_type_code,
                    "attended": parsed_title["attended"],
                }
            )

        return parsed_events

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def sync_calendar_events(
    calendar_id, days=30, admin_email=None, start_date=None, end_date=None
):
    """
    Sync events from Google Calendar to the database.

    Args:
        calendar_id: ID of the calendar to fetch events from
        days: Number of days to fetch events for
        admin_email: Email of admin whose Google credentials to use
        start_date: Start date for fetching events (format: YYYY-MM-DD)
        end_date: End date for fetching events (format: YYYY-MM-DD)

    Returns:
        Tuple (created, updated, total) count of events
    """
    events = fetch_calendar_events(calendar_id, days, admin_email, start_date, end_date)
    created = 0
    updated = 0

    for event_data in events:
        # Get or create the subject
        subject, _ = Subject.objects.get_or_create(name=event_data["subject_name"])

        # Get or create the class type based on price code
        class_type_code = event_data["class_type_code"]
        try:
            class_type = ClassType.objects.get(name=class_type_code)
        except ClassType.DoesNotExist:
            print(
                f"WARNING: Class type code '{class_type_code}' not found in database. "
                f"Creating with default values."
            )
            class_type = ClassType.objects.create(
                name=class_type_code,
                hourly_rate=0,  # Default rate that should be updated by admin
            )

        # Get or create the teacher - search more thoroughly
        teacher_name = event_data["teacher_name"]
        teacher_username = teacher_name.replace(" ", "").lower()
        teacher_first_name = (
            teacher_name.split()[0] if " " in teacher_name else teacher_name
        )
        teacher_last_name = teacher_name.split()[-1] if " " in teacher_name else ""

        # Try different ways to find the teacher
        try:
            # Try by username first
            teacher = User.objects.get(username=teacher_username)
        except User.DoesNotExist:
            try:
                # Try by first and last name
                teacher = User.objects.filter(
                    first_name=teacher_first_name, last_name=teacher_last_name
                ).first()

                if not teacher:
                    raise User.DoesNotExist
            except User.DoesNotExist:
                # Create a placeholder teacher
                placeholder_email = f"{teacher_username}@placeholder.aprendecomigo.com"
                teacher = User.objects.create(
                    username=teacher_username,
                    email=placeholder_email,
                    name=teacher_name,  # Set the name field (required)
                    first_name=teacher_first_name,
                    last_name=teacher_last_name,
                    user_type="teacher",  # Set user type to teacher
                )

                # Create a basic Teacher profile for the placeholder user
                try:
                    # Use empty values for optional fields
                    Teacher.objects.create(
                        user=teacher,
                        bio="",
                        specialty="",
                        education="",
                        availability="",
                        address="",
                    )
                    print(f"Created placeholder teacher profile for: {teacher.email}")
                except Exception as e:
                    print(f"Failed to create teacher profile: {e}")

                print(
                    f"Created placeholder teacher: {teacher.email} (needs profile completion)"
                )

        # Get or create the student - search more thoroughly
        student_name = event_data["student_name"]
        student_username = student_name.replace(" ", "").lower()
        student_first_name = (
            student_name.split()[0] if " " in student_name else student_name
        )
        student_last_name = student_name.split()[-1] if " " in student_name else ""

        # Try different ways to find the student
        try:
            # Try by username first
            student = User.objects.get(username=student_username)
        except User.DoesNotExist:
            try:
                # Try by first and last name
                student = User.objects.filter(
                    first_name=student_first_name, last_name=student_last_name
                ).first()

                if not student:
                    raise User.DoesNotExist
            except User.DoesNotExist:
                # Create a placeholder student
                placeholder_email = f"{student_username}@placeholder.aprendecomigo.com"
                student = User.objects.create(
                    username=student_username,
                    email=placeholder_email,
                    name=student_name,  # Set the name field (required)
                    first_name=student_first_name,
                    last_name=student_last_name,
                    user_type="student",  # Set user type to student
                )

                # Create a basic Student profile for the placeholder user
                try:
                    # Use default values for required fields
                    Student.objects.create(
                        user=student,
                        school_year="(Pending)",
                        birth_date=timezone.now().date(),  # Today as placeholder
                        address="(Pending)",
                    )
                    print(f"Created placeholder student profile for: {student.email}")
                except Exception as e:
                    print(f"Failed to create student profile: {e}")

                print(
                    f"Created placeholder student: {student.email} (needs profile completion)"
                )

        # Get or create the class session
        session, created_new = ClassSession.objects.update_or_create(
            google_calendar_id=event_data["google_calendar_id"],
            defaults={
                "title": event_data["title"],
                "teacher": teacher,
                "subject": subject,
                "class_type": class_type,
                "start_time": event_data["start_time"],
                "end_time": event_data["end_time"],
                "attended": event_data["attended"],
            },
        )

        # Add student to the session
        session.students.add(student)

        if created_new:
            created += 1
        else:
            updated += 1

    return created, updated, len(events)
