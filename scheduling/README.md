# Scheduling App

The scheduling app integrates with Google Calendar to import and manage class sessions for the AprendeComigo platform.

## Features

- Models for managing subjects, class types, and class sessions
- Integration with Google Calendar API using django-allauth authentication
- Automated parsing of calendar events to extract class information
- Management command for syncing calendar events

## Models

- **Subject**: Represents the subject taught in a class
- **ClassType**: Defines types of classes (e.g., individual, group) with pricing
- **ClassSession**: Represents a scheduled class session with teacher, students, and metadata

## Google Calendar Integration

The app uses Google's OAuth2 tokens from django-allauth to access the Calendar API. It parses event details based on these conventions:

- **Event Title**: Contains student name (e.g., "Tom Steadman")
- **Event Location**: Contains teacher name with "Prof." prefix (e.g., "Prof. Carla Almeida")
- **Event Description**: Contains subject name and class type indicators (e.g., "Explicação_Uni")
- **Attendance**: Events with "FALTOU" in the title are marked as not attended (e.g., "FALTOU - Tom Steadman")

See the [Calendar Format Documentation](docs/calendar_format.md) for detailed format guidelines.

## Setup

1. Ensure admin users connect their Google accounts via the social login feature
2. Make sure the Google Calendar API is enabled in your Google Project
3. Add the Calendar API scope in settings.py (should already be configured)
4. Run migrations:
   ```
   python manage.py migrate
   ```

## Usage

To sync events from Google Calendar:

```
python manage.py sync_calendar --admin-email admin@example.com [--calendar_id CALENDAR_ID] [--days DAYS] [--warn-placeholder]
```

Options:
- `--admin-email`: Email of admin user whose Google credentials to use (required)
- `--calendar_id`: ID of the calendar to sync (default: specified classroom calendar)
- `--days`: Number of days to fetch events for (default: 30)
- `--warn-placeholder`: Show warnings about placeholder users created during sync

## Important Notes

When syncing calendar events, the system will:
1. Create placeholder users for students and teachers that don't exist in the database
2. Set appropriate user types (teacher/student) for these placeholder users
3. Create email addresses in the format `username@placeholder.aprendecomigo.com`

These placeholder users will need profile completion later.
