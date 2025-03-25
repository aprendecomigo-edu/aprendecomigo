from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from datetime import datetime, timedelta

from .models import ClassSession
from . import google_calendar


class CalendarService:
    """Service class for handling calendar operations."""
    
    @staticmethod
    def sync_class_session(class_session):
        """
        Synchronize a class session with Google Calendar.
        Creates, updates, or deletes the corresponding event.
        """
        if class_session.status == 'cancelled':
            # Delete the event if the class is cancelled
            if class_session.google_calendar_id:
                result = google_calendar.delete_event(class_session)
                if result:
                    class_session.google_calendar_id = None
                    class_session.save(update_fields=['google_calendar_id'])
                return result
            return True
            
        if class_session.google_calendar_id:
            # Update existing event
            event_id = google_calendar.update_event(class_session)
        else:
            # Create new event
            event_id = google_calendar.create_event(class_session)
            
        if event_id and event_id != class_session.google_calendar_id:
            class_session.google_calendar_id = event_id
            class_session.save(update_fields=['google_calendar_id'])
            
        return bool(event_id)
    
    @staticmethod
    def sync_all_upcoming_sessions():
        """Synchronize all upcoming class sessions with Google Calendar."""
        now = timezone.now()
        upcoming_sessions = ClassSession.objects.filter(
            start_time__gte=now
        ).exclude(
            status='cancelled'
        )
        
        success_count = 0
        for session in upcoming_sessions:
            if CalendarService.sync_class_session(session):
                success_count += 1
                
        return {
            'total': upcoming_sessions.count(),
            'success': success_count,
            'failed': upcoming_sessions.count() - success_count
        }
    
    @staticmethod
    def fetch_calendar_events(start_date=None, end_date=None, teacher=None):
        """
        Fetch events from Google Calendar and match with class sessions.
        Returns a merged list of events from both sources.
        """
        # Default to upcoming week if no dates provided
        if not start_date:
            start_date = timezone.now().date()
        if not end_date:
            end_date = start_date + timedelta(days=7)
            
        # Convert dates to datetime for Google Calendar API
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Fetch class sessions from database
        sessions_query = ClassSession.objects.filter(
            start_time__date__gte=start_date,
            start_time__date__lte=end_date
        )
        
        if teacher:
            sessions_query = sessions_query.filter(teacher=teacher)
            
        sessions = list(sessions_query)
        
        # Fetch events from Google Calendar
        # This is commented out for now since we don't have credentials set up
        # In a real implementation, you'd uncomment this
        # google_events = google_calendar.fetch_events(
        #     start_datetime=start_datetime, 
        #     end_datetime=end_datetime
        # )
        
        # For now, we'll just return the database sessions
        return sessions
    
    @staticmethod
    def detect_conflicts(class_session, margin_minutes=15):
        """
        Detect conflicts with other class sessions.
        Returns a list of conflicting sessions.
        """
        if not class_session.id:
            # For new sessions, just check time conflicts
            conflicts = ClassSession.objects.filter(
                Q(teacher=class_session.teacher) & 
                (
                    # Session starts during another session
                    Q(start_time__lte=class_session.start_time, 
                      end_time__gte=class_session.start_time) |
                    # Session ends during another session
                    Q(start_time__lte=class_session.end_time,
                      end_time__gte=class_session.end_time) |
                    # Session completely contains another session
                    Q(start_time__gte=class_session.start_time,
                      end_time__lte=class_session.end_time)
                )
            ).exclude(status='cancelled')
        else:
            # For existing sessions, exclude self from conflict check
            conflicts = ClassSession.objects.filter(
                Q(teacher=class_session.teacher) & 
                (
                    # Session starts during another session
                    Q(start_time__lte=class_session.start_time, 
                      end_time__gte=class_session.start_time) |
                    # Session ends during another session
                    Q(start_time__lte=class_session.end_time,
                      end_time__gte=class_session.end_time) |
                    # Session completely contains another session
                    Q(start_time__gte=class_session.start_time,
                      end_time__lte=class_session.end_time)
                )
            ).exclude(id=class_session.id).exclude(status='cancelled')
            
        return list(conflicts)
        
    @staticmethod
    @transaction.atomic
    def create_class_session(session_data, sync_calendar=True):
        """
        Create a new class session and optionally sync with Google Calendar.
        Returns the created session and any conflicts.
        """
        class_session = ClassSession(**session_data)
        
        # Check for conflicts before saving
        conflicts = CalendarService.detect_conflicts(class_session)
        
        # Save the session
        class_session.save()
        
        # Add students if provided
        if 'students' in session_data:
            class_session.students.set(session_data['students'])
        
        # Sync with Google Calendar if requested
        if sync_calendar:
            CalendarService.sync_class_session(class_session)
            
        return {
            'session': class_session,
            'conflicts': conflicts
        }
        
    @staticmethod
    @transaction.atomic
    def update_class_session(class_session, session_data, sync_calendar=True):
        """
        Update an existing class session and optionally sync with Google Calendar.
        Returns the updated session and any conflicts.
        """
        # Update fields
        for key, value in session_data.items():
            if key != 'students':
                setattr(class_session, key, value)
        
        # Check for conflicts before saving
        conflicts = CalendarService.detect_conflicts(class_session)
        
        # Save the session
        class_session.save()
        
        # Update students if provided
        if 'students' in session_data:
            class_session.students.set(session_data['students'])
        
        # Sync with Google Calendar if requested
        if sync_calendar:
            CalendarService.sync_class_session(class_session)
            
        return {
            'session': class_session,
            'conflicts': conflicts
        } 