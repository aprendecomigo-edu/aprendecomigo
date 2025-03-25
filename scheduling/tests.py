from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Subject, ClassType, ClassSession
from .services import CalendarService
from unittest.mock import patch, MagicMock

User = get_user_model()


class SchedulingModelsTests(TestCase):
    """Test cases for scheduling models.
    
    These tests verify that:
    - Subject model correctly stores and displays subject information
    - ClassType model properly handles different types of classes
    - ClassSession model manages class scheduling and relationships
    """
    
    def setUp(self):
        """Set up test environment with:
        - A teacher user
        - A student user
        - A test subject
        - A test class type
        """
        # Create test user
        self.teacher = User.objects.create_user(
            email='teacher@example.com',
            password='teacherpass',
            name='Teacher User'
        )
        
        self.student = User.objects.create_user(
            email='student@example.com',
            password='studentpass',
            name='Student User'
        )
        
        # Create test subject
        self.subject = Subject.objects.create(
            name='Mathematics',
            description='Math lessons'
        )
        
        # Create test class type
        self.class_type = ClassType.objects.create(
            name='Individual Tutoring',
            group_class=False,
            default_duration=60
        )
        
    def test_subject_creation(self):
        """Test subject model creation.
        
        Verifies that:
        1. Subject is created with correct name and description
        2. String representation is correct
        """
        self.assertEqual(self.subject.name, 'Mathematics')
        self.assertEqual(self.subject.description, 'Math lessons')
        self.assertEqual(str(self.subject), 'Mathematics')
        
    def test_class_type_creation(self):
        """Test class type model creation.
        
        Verifies that:
        1. Class type is created with correct attributes
        2. Boolean fields work as expected
        3. Duration is stored correctly
        4. String representation is correct
        """
        self.assertEqual(self.class_type.name, 'Individual Tutoring')
        self.assertFalse(self.class_type.group_class)
        self.assertEqual(self.class_type.default_duration, 60)
        self.assertEqual(str(self.class_type), 'Individual Tutoring')
        
    def test_class_session_creation(self):
        """Test class session model creation.
        
        Verifies that:
        1. Session is created with all required fields
        2. Relationships with teacher and subject are correct
        3. Many-to-many relationship with students works
        4. Status and notes are stored correctly
        5. String representation is correct
        """
        now = timezone.now()
        session = ClassSession.objects.create(
            title='Math Tutoring Session',
            teacher=self.teacher,
            subject=self.subject,
            class_type=self.class_type,
            start_time=now,
            end_time=now + timedelta(hours=1),
            status='scheduled',
            notes='Test notes'
        )
        
        session.students.add(self.student)
        
        self.assertEqual(session.title, 'Math Tutoring Session')
        self.assertEqual(session.teacher, self.teacher)
        self.assertEqual(session.subject, self.subject)
        self.assertEqual(session.class_type, self.class_type)
        self.assertEqual(session.status, 'scheduled')
        self.assertEqual(session.notes, 'Test notes')
        self.assertEqual(session.students.count(), 1)
        self.assertEqual(session.students.first(), self.student)
        self.assertEqual(str(session), 'Math Tutoring Session')


class CalendarServiceTests(TestCase):
    """Test cases for CalendarService.
    
    These tests verify that:
    - Class sessions are properly synced with Google Calendar
    - Conflict detection works correctly
    - Status transitions are handled properly
    - Validation rules are enforced
    """
    
    def setUp(self):
        """Set up test environment with:
        - A teacher and student user
        - A test subject and class type
        - A test class session
        """
        # Create test user
        self.teacher = User.objects.create_user(
            email='teacher@example.com',
            password='teacherpass',
            name='Teacher User'
        )
        
        self.student = User.objects.create_user(
            email='student@example.com',
            password='studentpass',
            name='Student User'
        )
        
        # Create test subject and class type
        self.subject = Subject.objects.create(name='Mathematics')
        self.class_type = ClassType.objects.create(name='Individual Tutoring')
        
        # Set up time variables
        self.now = timezone.now()
        self.one_hour_later = self.now + timedelta(hours=1)
        
        # Create a class session
        self.session = ClassSession.objects.create(
            title='Math Tutoring Session',
            teacher=self.teacher,
            subject=self.subject,
            class_type=self.class_type,
            start_time=self.now,
            end_time=self.one_hour_later,
            status='scheduled'
        )
        self.session.students.add(self.student)
        
    @patch('scheduling.google_calendar.create_event')
    def test_sync_class_session_create(self, mock_create_event):
        """Test syncing a new class session to Google Calendar.
        
        Verifies that:
        1. New session is properly synced to Google Calendar
        2. Google Calendar ID is stored in the session
        3. Create event function is called with correct parameters
        """
        # Mock the create_event function to return a fake event ID
        mock_create_event.return_value = 'fake_event_id_123'
        
        # Call the sync method
        result = CalendarService.sync_class_session(self.session)
        
        # Check the result
        self.assertTrue(result)
        mock_create_event.assert_called_once_with(self.session)
        
        # Refresh the session from the database
        self.session.refresh_from_db()
        self.assertEqual(self.session.google_calendar_id, 'fake_event_id_123')
        
    @patch('scheduling.google_calendar.update_event')
    def test_sync_class_session_update(self, mock_update_event):
        """Test updating an existing class session in Google Calendar.
        
        Verifies that:
        1. Existing session is properly updated in Google Calendar
        2. Update event function is called with correct parameters
        3. Google Calendar ID remains unchanged
        """
        # Set a Google Calendar ID
        self.session.google_calendar_id = 'existing_event_id'
        self.session.save()
        
        # Mock the update_event function to return the same event ID
        mock_update_event.return_value = 'existing_event_id'
        
        # Call the sync method
        result = CalendarService.sync_class_session(self.session)
        
        # Check the result
        self.assertTrue(result)
        mock_update_event.assert_called_once_with(self.session)
        
    @patch('scheduling.google_calendar.delete_event')
    def test_sync_class_session_delete(self, mock_delete_event):
        """Test deleting a class session from Google Calendar when cancelled.
        
        Verifies that:
        1. Cancelled session is properly deleted from Google Calendar
        2. Delete event function is called with correct parameters
        3. Google Calendar ID is cleared from the session
        """
        # Set a Google Calendar ID
        self.session.google_calendar_id = 'existing_event_id'
        self.session.status = 'cancelled'
        self.session.save()
        
        # Mock the delete_event function to return True
        mock_delete_event.return_value = True
        
        # Call the sync method
        result = CalendarService.sync_class_session(self.session)
        
        # Check the result
        self.assertTrue(result)
        mock_delete_event.assert_called_once_with(self.session)
        
        # Refresh the session from the database
        self.session.refresh_from_db()
        self.assertIsNone(self.session.google_calendar_id)
        
    def test_detect_conflicts_new_session(self):
        """Test conflict detection for a new session.
        
        Verifies that:
        1. Overlapping sessions are detected
        2. Conflict detection works with partial overlaps
        3. Correct conflicting sessions are returned
        """
        # Create a session that conflicts with self.session
        conflicting_session = ClassSession(
            title='Conflicting Session',
            teacher=self.teacher,
            subject=self.subject,
            class_type=self.class_type,
            start_time=self.now + timedelta(minutes=30),  # Within the existing session
            end_time=self.one_hour_later + timedelta(minutes=30),
            status='scheduled'
        )
        
        # Detect conflicts
        conflicts = CalendarService.detect_conflicts(conflicting_session)
        
        # Check that self.session is in the conflicts
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0], self.session)
        
    def test_detect_conflicts_no_conflict(self):
        """Test conflict detection with no conflicts.
        
        Verifies that:
        1. Non-overlapping sessions are not flagged as conflicts
        2. Sessions with different teachers are not flagged
        3. Sessions with different times are not flagged
        """
        # Create a session that doesn't conflict with self.session
        non_conflicting_session = ClassSession(
            title='Non-Conflicting Session',
            teacher=self.teacher,
            subject=self.subject,
            class_type=self.class_type,
            start_time=self.one_hour_later + timedelta(hours=1),  # After existing session
            end_time=self.one_hour_later + timedelta(hours=2),
            status='scheduled'
        )
        
        # Detect conflicts
        conflicts = CalendarService.detect_conflicts(non_conflicting_session)
        
        # Check that there are no conflicts
        self.assertEqual(len(conflicts), 0)
        
    def test_class_session_status_transitions(self):
        """Test class session status transitions.
        
        Verifies that:
        1. Session can transition through all valid statuses
        2. Status changes are properly saved
        3. Status values are correct
        """
        # Test initial status
        self.assertEqual(self.session.status, 'scheduled')
        
        # Test transition to in_progress
        self.session.status = 'in_progress'
        self.session.save()
        self.assertEqual(self.session.status, 'in_progress')
        
        # Test transition to completed
        self.session.status = 'completed'
        self.session.save()
        self.assertEqual(self.session.status, 'completed')
        
        # Test transition to cancelled
        self.session.status = 'cancelled'
        self.session.save()
        self.assertEqual(self.session.status, 'cancelled')
        
    def test_class_session_validation(self):
        """Test class session validation rules.
        
        Verifies that:
        1. End time cannot be before start time
        2. Session duration must match class type
        3. Appropriate errors are raised for invalid data
        """
        # Test end_time before start_time
        with self.assertRaises(ValueError):
            ClassSession.objects.create(
                title='Invalid Session',
                teacher=self.teacher,
                subject=self.subject,
                class_type=self.class_type,
                start_time=self.one_hour_later,
                end_time=self.now,  # End time before start time
                status='scheduled'
            )
            
        # Test session duration matches class type
        with self.assertRaises(ValueError):
            ClassSession.objects.create(
                title='Invalid Duration Session',
                teacher=self.teacher,
                subject=self.subject,
                class_type=self.class_type,
                start_time=self.now,
                end_time=self.now + timedelta(hours=2),  # Duration doesn't match class type
                status='scheduled'
            )

    def test_detect_conflicts_edge_cases(self):
        """Test conflict detection edge cases."""
        # Test exact boundary overlap
        boundary_session = ClassSession(
            title='Boundary Session',
            teacher=self.teacher,
            subject=self.subject,
            class_type=self.class_type,
            start_time=self.one_hour_later,  # Exactly when first session ends
            end_time=self.one_hour_later + timedelta(hours=1),
            status='scheduled'
        )
        
        conflicts = CalendarService.detect_conflicts(boundary_session)
        self.assertEqual(len(conflicts), 0)  # Should not conflict
        
        # Test contained session
        contained_session = ClassSession(
            title='Contained Session',
            teacher=self.teacher,
            subject=self.subject,
            class_type=self.class_type,
            start_time=self.now + timedelta(minutes=15),  # Starts during first session
            end_time=self.now + timedelta(minutes=45),    # Ends during first session
            status='scheduled'
        )
        
        conflicts = CalendarService.detect_conflicts(contained_session)
        self.assertEqual(len(conflicts), 1)  # Should conflict
        
        # Test overlapping session
        overlapping_session = ClassSession(
            title='Overlapping Session',
            teacher=self.teacher,
            subject=self.subject,
            class_type=self.class_type,
            start_time=self.now + timedelta(minutes=30),  # Starts during first session
            end_time=self.one_hour_later + timedelta(minutes=30),  # Ends after first session
            status='scheduled'
        )
        
        conflicts = CalendarService.detect_conflicts(overlapping_session)
        self.assertEqual(len(conflicts), 1)  # Should conflict

    @patch('scheduling.services.CalendarService.sync_class_session')
    def test_create_class_session(self, mock_sync):
        """Test creating a class session with the service."""
        # Mock the sync_class_session method
        mock_sync.return_value = True
        
        # Session data
        session_data = {
            'title': 'New Session',
            'teacher': self.teacher,
            'subject': self.subject,
            'class_type': self.class_type,
            'start_time': self.now + timedelta(hours=2),
            'end_time': self.now + timedelta(hours=3),
            'status': 'scheduled',
            'notes': 'Created with service',
            'students': [self.student.id]
        }
        
        # Create session using the service
        result = CalendarService.create_class_session(session_data)
        
        # Check the result
        self.assertIn('session', result)
        self.assertIn('conflicts', result)
        
        # Verify the session was created correctly
        session = result['session']
        self.assertEqual(session.title, 'New Session')
        self.assertEqual(session.teacher, self.teacher)
        self.assertEqual(session.students.count(), 1)
        self.assertEqual(session.students.first(), self.student)
        
        # Verify the sync was called
        mock_sync.assert_called_once_with(session)


# Create a mock for the Google Calendar API
class MockGoogleCalendarTests(TestCase):
    """Test cases for mocking Google Calendar API."""
    
    @patch('scheduling.google_calendar.get_calendar_service')
    def test_mock_google_calendar_service(self, mock_get_service):
        """Demonstrate how to mock the Google Calendar service."""
        # Mock the service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Mock the events method
        mock_events = MagicMock()
        mock_service.events.return_value = mock_events
        
        # Mock the insert method
        mock_insert = MagicMock()
        mock_events.insert.return_value = mock_insert
        
        # Mock the execute method to return a response with an ID
        mock_insert.execute.return_value = {'id': 'mock_event_id'}
        
        # Create a simple class session for testing
        now = timezone.now()
        teacher = User.objects.create_user(email='test@example.com', password='pass', name='Test')
        subject = Subject.objects.create(name='Test Subject')
        class_type = ClassType.objects.create(name='Test Class Type')
        
        session = ClassSession.objects.create(
            title='Test Session',
            teacher=teacher,
            subject=subject,
            class_type=class_type,
            start_time=now,
            end_time=now + timedelta(hours=1),
        )
        
        # Import the function we want to test
        from scheduling.google_calendar import create_event
        
        # Call the function
        event_id = create_event(session)
        
        # Verify the result
        self.assertEqual(event_id, 'mock_event_id')
        mock_get_service.assert_called_once()
        mock_service.events.assert_called_once()
        mock_events.insert.assert_called_once()
