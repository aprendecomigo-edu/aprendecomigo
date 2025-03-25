import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.utils.timezone import make_aware


# If modifying these scopes, delete the token file.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_credentials():
    """Get valid user credentials from storage or create new ones."""
    # This is a placeholder for actual OAuth 2.0 flow
    # In a real implementation, you'd handle token storage and refresh
    # For now, this is just a skeleton to show the structure
    
    # TODO: Implement the actual OAuth flow with proper storage
    # This would involve:
    # 1. Check if token file exists
    # 2. If it exists, load credentials
    # 3. If not, or if credentials are invalid, run the OAuth flow
    # 4. Save the credentials for future use
    
    # For testing purposes, you can use a service account
    # or manually authenticate once and save the token
    
    return None  # Replace with actual credentials


def get_calendar_service():
    """Get a Google Calendar API service instance."""
    try:
        credentials = get_credentials()
        if not credentials:
            # TODO: Implement proper error handling
            return None
            
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        # TODO: Implement proper logging
        print(f"Error getting calendar service: {e}")
        return None


def create_event(class_session):
    """Create a Google Calendar event for a class session."""
    service = get_calendar_service()
    if not service:
        return None
        
    # Format the event
    attendees = []
    
    # Add teacher
    attendees.append({
        'email': class_session.teacher.email,
        'responseStatus': 'accepted',
    })
    
    # Add students
    for student in class_session.students.all():
        attendees.append({
            'email': student.email,
            'responseStatus': 'needsAction',
        })
    
    event = {
        'summary': class_session.title,
        'location': 'Online or School Location',  # TODO: Add location field to ClassSession
        'description': class_session.notes,
        'start': {
            'dateTime': class_session.start_time.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'end': {
            'dateTime': class_session.end_time.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'attendees': attendees,
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 30},
            ],
        },
    }
    
    try:
        # TODO: Use the appropriate calendar ID
        # For now, we'll use 'primary'
        calendar_id = 'primary'
        
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return event['id']
    except Exception as e:
        # TODO: Implement proper logging
        print(f"Error creating event: {e}")
        return None


def update_event(class_session):
    """Update a Google Calendar event for a class session."""
    if not class_session.google_calendar_id:
        # If no Google Calendar ID exists, create a new event
        return create_event(class_session)
        
    service = get_calendar_service()
    if not service:
        return None
        
    # Format the event (similar to create_event)
    attendees = []
    
    # Add teacher
    attendees.append({
        'email': class_session.teacher.email,
        'responseStatus': 'accepted',
    })
    
    # Add students
    for student in class_session.students.all():
        attendees.append({
            'email': student.email,
            'responseStatus': 'needsAction',
        })
    
    event = {
        'summary': class_session.title,
        'location': 'Online or School Location',  # TODO: Add location field to ClassSession
        'description': class_session.notes,
        'start': {
            'dateTime': class_session.start_time.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'end': {
            'dateTime': class_session.end_time.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'attendees': attendees,
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 30},
            ],
        },
    }
    
    try:
        # TODO: Use the appropriate calendar ID
        # For now, we'll use 'primary'
        calendar_id = 'primary'
        
        event = service.events().update(
            calendarId=calendar_id, 
            eventId=class_session.google_calendar_id, 
            body=event
        ).execute()
        return event['id']
    except Exception as e:
        # TODO: Implement proper logging
        print(f"Error updating event: {e}")
        return None


def delete_event(class_session):
    """Delete a Google Calendar event for a class session."""
    if not class_session.google_calendar_id:
        # No Google Calendar ID to delete
        return True
        
    service = get_calendar_service()
    if not service:
        return False
        
    try:
        # TODO: Use the appropriate calendar ID
        # For now, we'll use 'primary'
        calendar_id = 'primary'
        
        service.events().delete(
            calendarId=calendar_id, 
            eventId=class_session.google_calendar_id
        ).execute()
        return True
    except Exception as e:
        # TODO: Implement proper logging
        print(f"Error deleting event: {e}")
        return False


def fetch_events(start_datetime=None, end_datetime=None, max_results=10):
    """Fetch events from Google Calendar within a specified time range."""
    service = get_calendar_service()
    if not service:
        return []
        
    # Default to next 7 days if no dates provided
    if not start_datetime:
        start_datetime = datetime.utcnow()
    if not end_datetime:
        end_datetime = start_datetime + timedelta(days=7)
        
    start_str = start_datetime.isoformat() + 'Z'  # 'Z' indicates UTC time
    end_str = end_datetime.isoformat() + 'Z'
    
    try:
        # TODO: Use the appropriate calendar ID
        # For now, we'll use 'primary'
        calendar_id = 'primary'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_str,
            timeMax=end_str,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
    except Exception as e:
        # TODO: Implement proper logging
        print(f"Error fetching events: {e}")
        return [] 