import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.utils.timezone import make_aware
from allauth.socialaccount.models import SocialToken, SocialApp

# If modifying these scopes, delete the token file.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_credentials(user):
    """Get valid user credentials from django-allauth."""
    try:
        # Get the user's Google token from django-allauth
        social_token = SocialToken.objects.get(
            account__user=user,
            account__provider='google'
        )
        
        # Get the Google app configuration from the database
        social_app = SocialApp.objects.get(provider='google')
        
        # Create the credentials object for Google API
        credentials = Credentials(
            token=social_token.token,
            refresh_token=social_token.token_secret,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=social_app.client_id,
            client_secret=social_app.secret,
            scopes=SCOPES
        )
        
        return credentials
    except SocialToken.DoesNotExist:
        # User hasn't connected their Google account
        print(f"No Google token found for user {user.email}")
        return None
    except SocialApp.DoesNotExist:
        # Google app configuration is missing
        print("Google social app configuration not found in the database")
        return None
    except Exception as e:
        # Handle other errors
        print(f"Error getting Google credentials: {e}")
        return None


def get_calendar_service(user):
    """Get a Google Calendar API service instance for a specific user."""
    try:
        credentials = get_credentials(user)
        if not credentials:
            return None
            
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error getting calendar service: {e}")
        return None


def create_event(class_session):
    """Create a Google Calendar event for a class session."""
    service = get_calendar_service(class_session.teacher)
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
        print(f"Error creating event: {e}")
        return None


def update_event(class_session):
    """Update a Google Calendar event for a class session."""
    if not class_session.google_calendar_id:
        # If no Google Calendar ID exists, create a new event
        return create_event(class_session)
        
    service = get_calendar_service(class_session.teacher)
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
        print(f"Error updating event: {e}")
        return None


def delete_event(class_session):
    """Delete a Google Calendar event for a class session."""
    if not class_session.google_calendar_id:
        # No Google Calendar ID to delete
        return True
        
    service = get_calendar_service(class_session.teacher)
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
        print(f"Error deleting event: {e}")
        return False


def fetch_events(user, start_datetime=None, end_datetime=None, max_results=10):
    """Fetch events from Google Calendar within a specified time range for a specific user."""
    service = get_calendar_service(user)
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
        print(f"Error fetching events: {e}")
        return [] 