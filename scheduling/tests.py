from datetime import datetime, timedelta
from unittest.mock import ANY, MagicMock, patch

import pytz
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .google_calendar import (
    fetch_calendar_events,
    get_calendar_service,
    get_google_credentials,
    parse_event_description,
    parse_event_location,
    parse_event_title,
    sync_calendar_events,
)
from .models import ClassSession, ClassType

User = get_user_model()


# Mock calendar response data
def create_mock_event(
    event_id="event123",
    title="Student Name",
    location="Prof. Teacher Name",
    description="Math_Uni",
    start_time=None,
    end_time=None,
    is_absent=False,
):
    """Helper function to create mock Google Calendar event data"""
    if is_absent:
        title = f"{title} - FALTOU"

    if start_time is None:
        # Default to current time
        start_time = datetime.now(pytz.UTC)

    if end_time is None:
        # Default to 1 hour after start
        end_time = start_time + timedelta(hours=1)

    # Format times in RFC3339 format
    start_str = start_time.isoformat()
    end_str = end_time.isoformat()

    return {
        "id": event_id,
        "summary": title,
        "location": location,
        "description": description,
        "start": {"dateTime": start_str},
        "end": {"dateTime": end_str},
    }


class EventParsingTests(TestCase):
    """Test the event parsing functions"""

    def test_parse_event_title_regular(self):
        """Test parsing a regular event title"""
        result = parse_event_title("John Doe")
        self.assertEqual(result["student_name"], "John Doe")
        self.assertTrue(result["attended"])

    def test_parse_event_title_absent(self):
        """Test parsing a title with FALTOU suffix"""
        result = parse_event_title("Jane Smith - FALTOU")
        self.assertEqual(result["student_name"], "Jane Smith")
        self.assertFalse(result["attended"])

    def test_parse_event_location(self):
        """Test parsing the location field"""
        result = parse_event_location("Prof. Maria Silva")
        self.assertEqual(result, "Maria Silva")

        # Test without Prof. prefix
        result = parse_event_location("João Marques")
        self.assertEqual(result, "João Marques")

    def test_parse_event_description(self):
        """Test parsing the description field"""
        # Test regular description
        class_type_code = parse_event_description("MATH101")
        self.assertEqual(class_type_code, "MATH101")

        # Test another code
        class_type_code = parse_event_description("CHEMISTRY_ADV")
        self.assertEqual(class_type_code, "CHEMISTRY_ADV")

        # Test empty description
        class_type_code = parse_event_description("")
        self.assertEqual(class_type_code, "DEFAULT")


class GoogleCalendarServiceTests(TestCase):
    """Test the Google Calendar service functions with mocks"""

    def setUp(self):
        # Create a test admin user with a mock Google account
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass",
            name="Admin User",
            is_admin=True,
        )

    @patch("scheduling.google_calendar.SocialAccount")
    @patch("scheduling.google_calendar.SocialToken")
    @patch("scheduling.google_calendar.Credentials")
    def test_get_credentials(
        self, mock_credentials, mock_social_token, mock_social_account
    ):
        """Test retrieving Google API credentials"""
        # Setup the mocks
        mock_social_account.objects.get.return_value = MagicMock()
        mock_social_token.objects.get.return_value = MagicMock(
            token="fake_token", token_secret="fake_refresh_token"
        )
        mock_credentials.return_value = "fake_credentials"

        # Call the function
        result = get_google_credentials("admin@test.com")

        # Assert results
        self.assertEqual(result, "fake_credentials")
        mock_social_account.objects.get.assert_called_once_with(
            user__email="admin@test.com", provider="google"
        )

    @patch("scheduling.google_calendar.get_credentials")
    @patch("scheduling.google_calendar.build")
    def test_get_calendar_service(self, mock_build, mock_get_credentials):
        """Test getting the calendar service"""
        mock_get_credentials.return_value = "fake_credentials"
        mock_build.return_value = "calendar_service"

        result = get_calendar_service("admin@test.com")

        self.assertEqual(result, "calendar_service")
        mock_get_credentials.assert_called_once_with("admin@test.com")
        mock_build.assert_called_once_with(
            "calendar", "v3", credentials="fake_credentials"
        )


class FetchCalendarEventsTests(TestCase):
    """Test fetching and parsing calendar events"""

    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass",
            name="Admin User",
            is_admin=True,
        )

        # Sample calendar ID - using a fake ID for testing
        self.calendar_id = "test-calendar-id@example.com"

        # Sample events for testing
        self.mock_events = {
            "items": [
                create_mock_event(
                    event_id="event1",
                    title="Ana Silva",
                    location="Prof. Maria Carvalho",
                    description="Portuguese_Uni",
                ),
                create_mock_event(
                    event_id="event2",
                    title="João Pereira",
                    location="Prof. Pedro Santos",
                    description="Math_Group",
                    is_absent=True,
                ),
                create_mock_event(
                    event_id="event3",
                    title="Sofia Martins",
                    location="Carlos Mendes",
                    description="Physics_Uni",
                ),
            ]
        }

    @patch("scheduling.google_calendar.get_calendar_service")
    def test_fetch_calendar_events(self, mock_get_service):
        """Test fetching Google Calendar events with mocked service"""
        # Setup mocks
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # Mock the events.list().execute() chain
        mock_service.events.return_value.list.return_value.execute.return_value = (
            self.mock_events
        )

        # Call the function
        events = fetch_calendar_events(self.calendar_id, admin_email="admin@test.com")

        # Assert results
        self.assertEqual(len(events), 3)

        # Check event 1 (attended)
        self.assertEqual(events[0]["google_calendar_id"], "event1")
        self.assertEqual(events[0]["student_name"], "Ana Silva")
        self.assertEqual(events[0]["teacher_name"], "Maria Carvalho")
        self.assertEqual(events[0]["subject_name"], "Portuguese_Uni")
        self.assertEqual(events[0]["price_code"], "Portuguese_Uni")
        self.assertTrue(events[0]["attended"])

        # Check event 2 (absent)
        self.assertEqual(events[1]["google_calendar_id"], "event2")
        self.assertEqual(events[1]["student_name"], "João Pereira")
        self.assertEqual(events[1]["teacher_name"], "Pedro Santos")
        self.assertEqual(events[1]["subject_name"], "Math_Group")
        self.assertEqual(events[1]["price_code"], "Math_Group")
        self.assertFalse(events[1]["attended"])

        # Verify service was called with correct parameters
        mock_service.events.return_value.list.assert_called_once_with(
            calendarId=self.calendar_id,
            timeMin=ANY,
            timeMax=ANY,
            singleEvents=True,
            orderBy="startTime",
        )

    @patch("scheduling.google_calendar.get_calendar_service")
    def test_fetch_calendar_events_with_date_range(self, mock_get_service):
        """Test fetching events with specific date range"""
        # Setup mocks
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.events.return_value.list.return_value.execute.return_value = (
            self.mock_events
        )

        # Define date range
        start_date = "2023-04-01"
        end_date = "2023-04-30"

        # Call the function
        events = fetch_calendar_events(
            self.calendar_id,
            admin_email="admin@test.com",
            start_date=start_date,
            end_date=end_date,
        )

        # Verify date parsing and service call
        mock_service.events.return_value.list.assert_called_once()
        # We can't check the exact time strings because they include the current date/time
        # But we can make sure the service was called


class SyncCalendarEventsTests(TestCase):
    """Test syncing calendar events to the database"""

    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass",
            name="Admin User",
            is_admin=True,
        )

        # Create a sample teacher
        self.teacher = User.objects.create_user(
            username="mariateacher",
            email="maria@teacher.com",
            password="teacherpass",
            name="Maria Teacher",
            user_type="teacher",
        )

        # Create a sample student
        self.student = User.objects.create_user(
            username="anastudent",
            email="ana@student.com",
            password="studentpass",
            name="Ana Student",
            user_type="student",
        )

        # Sample calendar ID - using a fake ID for testing
        self.calendar_id = "test-calendar-id@example.com"

        # Create a mock event list
        self.start_time = timezone.now()
        self.end_time = self.start_time + timedelta(hours=1)

        self.mock_parsed_events = [
            {
                "google_calendar_id": "event1",
                "title": "Ana Student",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "teacher_name": "Maria Teacher",
                "student_name": "Ana Student",
                "subject_name": "PORTUGUESE_ADV",
                "price_code": "PORTUGUESE_ADV",
                "attended": True,
            },
            {
                "google_calendar_id": "event2",
                "title": "New Student - FALTOU",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "teacher_name": "New Teacher",
                "student_name": "New Student",
                "subject_name": "MATH_GROUP",
                "price_code": "MATH_GROUP",
                "attended": False,
            },
        ]

    @patch("scheduling.google_calendar.fetch_calendar_events")
    def test_sync_calendar_events(self, mock_fetch_events):
        """Test syncing calendar events to database"""
        # Setup mock
        mock_fetch_events.return_value = self.mock_parsed_events

        # Initial counts
        initial_class_type_count = ClassType.objects.count()
        initial_user_count = User.objects.count()
        initial_session_count = ClassSession.objects.count()

        # Call the function
        created, updated, total = sync_calendar_events(
            self.calendar_id, admin_email="admin@test.com"
        )

        # Assert results
        self.assertEqual(created, 2)  # 2 new sessions should be created
        self.assertEqual(updated, 0)  # No updates
        self.assertEqual(total, 2)  # 2 total events processed

        # Verify database objects were created
        self.assertEqual(ClassType.objects.count(), initial_class_type_count + 2)
        self.assertEqual(
            User.objects.count(), initial_user_count + 2
        )  # New teacher and student
        self.assertEqual(ClassSession.objects.count(), initial_session_count + 2)

        # Verify session 1 (existing users)
        session1 = ClassSession.objects.get(google_calendar_id="event1")
        self.assertEqual(session1.title, "Ana Student")
        self.assertEqual(session1.teacher, self.teacher)
        self.assertTrue(self.student in session1.students.all())
        self.assertTrue(session1.attended)

        # Verify session 2 (new users)
        session2 = ClassSession.objects.get(google_calendar_id="event2")
        self.assertEqual(session2.title, "New Student - FALTOU")
        self.assertFalse(session2.attended)

        # Verify placeholder users were created with correct user_type
        new_teacher = User.objects.get(username="newteacher")
        self.assertEqual(new_teacher.user_type, "teacher")
        self.assertEqual(new_teacher.email, "newteacher@placeholder.aprendecomigo.com")

        new_student = User.objects.get(username="newstudent")
        self.assertEqual(new_student.user_type, "student")
        self.assertEqual(new_student.email, "newstudent@placeholder.aprendecomigo.com")

    @patch("scheduling.google_calendar.fetch_calendar_events")
    def test_sync_calendar_events_update_existing(self, mock_fetch_events):
        """Test updating existing calendar events"""
        # Create a pre-existing session
        class_type = ClassType.objects.create(
            name="PORTUGUESE_ADV", default_duration=60, hourly_rate=25.0
        )
        ClassSession.objects.create(
            google_calendar_id="event1",
            title="Ana Student",
            teacher=self.teacher,
            class_type=class_type,
            start_time=self.start_time,
            end_time=self.end_time,
            attended=True,
        )

        # Setup mock with changed data
        mock_fetch_events.return_value = [
            {
                "google_calendar_id": "event1",
                "title": "Ana Student - FALTOU",  # changed to absent
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "teacher_name": "Maria Teacher",
                "student_name": "Ana Student",
                "subject_name": "PORTUGUESE_ADV",
                "price_code": "PORTUGUESE_ADV",
                "attended": False,  # changed to absent
            }
        ]

        # Initial counts
        initial_class_type_count = ClassType.objects.count()
        initial_user_count = User.objects.count()
        initial_session_count = ClassSession.objects.count()

        # Call the function
        created, updated, total = sync_calendar_events(
            self.calendar_id, admin_email="admin@test.com"
        )

        # Assert results
        self.assertEqual(created, 0)  # No new sessions
        self.assertEqual(updated, 1)  # 1 updated session
        self.assertEqual(total, 1)  # 1 total event processed

        # Verify counts remain the same
        self.assertEqual(ClassType.objects.count(), initial_class_type_count)
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertEqual(ClassSession.objects.count(), initial_session_count)

        # Verify session was updated
        updated_session = ClassSession.objects.get(google_calendar_id="event1")
        self.assertEqual(updated_session.title, "Ana Student - FALTOU")
        self.assertFalse(updated_session.attended)
