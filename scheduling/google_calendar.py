import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from scheduling.db_utils import get_google_credentials, get_google_token, get_or_create_class_type, get_or_create_student, get_or_create_teacher
from google.oauth2.credentials import Credentials
from django.conf import settings



# Scope required for Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_google_credentials(admin_email):
        """
    Get Google API credentials from a user's django-allauth social account

    Args:
        admin_email: Email of admin user whose Google credentials to use

    Returns:
        Google OAuth2 Credentials object or None if not available
    """
        token, refresh_token = get_google_token(admin_email)
        token_data = {
            "token": token,
            "refresh_token": refresh_token,
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



def get_calendar_service(admin_email):
    """Build and return a Google Calendar service object using admin credentials."""
    creds = get_google_credentials(admin_email)
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


def fetch_calendar_events(calendar_id, admin_email):
    """
    Fetch events from Google Calendar and return parsed data.

    Args:
        calendar_id: ID of the calendar to fetch events from
        admin_email: Email of admin whose Google credentials to use

    Returns:
        List of parsed events
    """
    try:
        service = get_calendar_service(admin_email)
        page_token = None
        events = []
        while True:
            events_result = service.events().list(calendarId=calendar_id, 
                                           singleEvents=True, 
                                           pageToken=page_token).execute()
            for event in events_result.get("items", []):
                events.append(event)
            page_token = events_result.get('nextPageToken')
            if not page_token:
                break
  
        parsed_events = []

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            start_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))

            end = event["end"].get("dateTime", event["end"].get("date"))
            end_time = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
            
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
                    "start_time": start_time,
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



def sync_calendar_events(calendar_id, admin_email):
    """
    Sync events from Google Calendar to the database.

    Args:
        calendar_id: ID of the calendar to fetch events from
        admin_email: Email of admin whose Google credentials to use

    Returns:
        Tuple (created, updated, total) count of events
    """
    events = fetch_calendar_events(calendar_id, admin_email)
    created = 0
    updated = 0

    for event_data in events:
        # Get or create each required object
        class_type = get_or_create_class_type(event_data["class_type_code"])
        teacher = get_or_create_teacher(event_data["teacher_name"])
        student = get_or_create_student(event_data["student_name"])
        
        # Create or update the class session
        session, created_new = create_or_update_class_session(
            event_data, teacher, class_type, student
        )
        
        if created_new:
            created += 1
        else:
            updated += 1

    return created, updated, len(events)
