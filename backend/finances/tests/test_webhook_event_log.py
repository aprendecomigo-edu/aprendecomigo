"""
Tests for WebhookEventLog model and related functionality.

This test suite covers webhook event logging, status tracking, and monitoring
functionality for administrative payment system oversight.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from finances.models import WebhookEventLog, WebhookEventStatus


class WebhookEventLogModelTest(TestCase):
    """Test cases for WebhookEventLog model."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_event_data = {
            'stripe_event_id': 'evt_test_12345',
            'event_type': 'payment_intent.succeeded',
            'status': WebhookEventStatus.RECEIVED,
            'payload': {
                'id': 'evt_test_12345',
                'type': 'payment_intent.succeeded',
                'data': {
                    'object': {
                        'id': 'pi_test_12345',
                        'amount': 2000,
                        'currency': 'eur'
                    }
                }
            }
        }
    
    def test_create_webhook_event_log(self):
        """Test creating a webhook event log entry."""
        log = WebhookEventLog.objects.create(**self.sample_event_data)
        
        self.assertEqual(log.stripe_event_id, 'evt_test_12345')
        self.assertEqual(log.event_type, 'payment_intent.succeeded')
        self.assertEqual(log.status, WebhookEventStatus.RECEIVED)
        self.assertEqual(log.retry_count, 0)
        self.assertIsNone(log.processed_at)
        self.assertEqual(log.error_message, '')
        self.assertIsNotNone(log.created_at)
    
    
    def test_mark_as_processing(self):
        """Test marking a webhook event as processing."""
        log = WebhookEventLog.objects.create(**self.sample_event_data)
        
        log.mark_as_processing()
        
        self.assertEqual(log.status, WebhookEventStatus.PROCESSING)
        self.assertIsNotNone(log.processed_at)
    
    def test_mark_as_processed(self):
        """Test marking a webhook event as successfully processed."""
        log = WebhookEventLog.objects.create(**self.sample_event_data)
        
        log.mark_as_processed()
        
        self.assertEqual(log.status, WebhookEventStatus.PROCESSED)
        self.assertIsNotNone(log.processed_at)
    
    def test_mark_as_failed(self):
        """Test marking a webhook event as failed."""
        log = WebhookEventLog.objects.create(**self.sample_event_data)
        error_message = "Payment processing failed"
        
        log.mark_as_failed(error_message)
        
        self.assertEqual(log.status, WebhookEventStatus.FAILED)
        self.assertEqual(log.error_message, error_message)
        self.assertIsNotNone(log.processed_at)
    
    def test_increment_retry_count(self):
        """Test incrementing retry count."""
        log = WebhookEventLog.objects.create(**self.sample_event_data)
        
        log.increment_retry_count()
        
        self.assertEqual(log.retry_count, 1)
        self.assertEqual(log.status, WebhookEventStatus.RETRYING)
    
    def test_is_retryable(self):
        """Test checking if a webhook event is retryable."""
        log = WebhookEventLog.objects.create(**self.sample_event_data)
        
        # New event should be retryable
        self.assertTrue(log.is_retryable())
        
        # Failed event with low retry count should be retryable
        log.mark_as_failed("Test error")
        self.assertTrue(log.is_retryable())
        
        # Event with high retry count should not be retryable
        log.retry_count = 5
        log.save()
        self.assertFalse(log.is_retryable())
        
        # Processed event should not be retryable
        log.retry_count = 0
        log.mark_as_processed()
        self.assertFalse(log.is_retryable())
    
    def test_get_processing_duration(self):
        """Test calculating processing duration."""
        log = WebhookEventLog.objects.create(**self.sample_event_data)
        
        # Event not yet processed should return None
        self.assertIsNone(log.get_processing_duration())
        
        # Mark as processed and check duration
        log.mark_as_processed()
        duration = log.get_processing_duration()
        self.assertIsNotNone(duration)
        self.assertGreaterEqual(duration.total_seconds(), 0)
    
    def test_string_representation(self):
        """Test string representation of webhook event log."""
        log = WebhookEventLog.objects.create(**self.sample_event_data)
        
        expected_str = f"Webhook Event: evt_test_12345 (payment_intent.succeeded) - Received"
        self.assertEqual(str(log), expected_str)
    
    def test_failed_events_manager(self):
        """Test custom manager for failed events."""
        # Create events with different statuses
        WebhookEventLog.objects.create(
            stripe_event_id='evt_success',
            event_type='payment_intent.succeeded',
            status=WebhookEventStatus.PROCESSED,
            payload={}
        )
        
        WebhookEventLog.objects.create(
            stripe_event_id='evt_failed',
            event_type='payment_intent.payment_failed',
            status=WebhookEventStatus.FAILED,
            payload={}
        )
        
        WebhookEventLog.objects.create(
            stripe_event_id='evt_pending',
            event_type='payment_intent.created',
            status=WebhookEventStatus.RECEIVED,
            payload={}
        )
        
        # Test failed events manager
        failed_events = WebhookEventLog.failed.all()
        self.assertEqual(failed_events.count(), 1)
        self.assertEqual(failed_events.first().stripe_event_id, 'evt_failed')
    
    def test_retryable_events_manager(self):
        """Test custom manager for retryable events."""
        # Create events with different retry counts
        WebhookEventLog.objects.create(
            stripe_event_id='evt_retryable_1',
            event_type='payment_intent.succeeded',
            status=WebhookEventStatus.FAILED,
            retry_count=2,
            payload={}
        )
        
        WebhookEventLog.objects.create(
            stripe_event_id='evt_not_retryable',
            event_type='payment_intent.succeeded',
            status=WebhookEventStatus.FAILED,
            retry_count=6,  # Over max retry limit
            payload={}
        )
        
        WebhookEventLog.objects.create(
            stripe_event_id='evt_processed',
            event_type='payment_intent.succeeded',
            status=WebhookEventStatus.PROCESSED,
            retry_count=1,
            payload={}
        )
        
        # Test retryable events manager
        retryable_events = WebhookEventLog.retryable.all()
        self.assertEqual(retryable_events.count(), 1)
        self.assertEqual(retryable_events.first().stripe_event_id, 'evt_retryable_1')
    
    def test_recent_events_manager(self):
        """Test custom manager for recent events."""
        from datetime import timedelta
        
        # Create an old event
        old_log = WebhookEventLog.objects.create(
            stripe_event_id='evt_old',
            event_type='payment_intent.succeeded',
            status=WebhookEventStatus.PROCESSED,
            payload={}
        )
        
        # Manually set created_at to be older than 24 hours
        old_time = timezone.now() - timedelta(hours=25)
        WebhookEventLog.objects.filter(id=old_log.id).update(created_at=old_time)
        
        # Create a recent event
        WebhookEventLog.objects.create(
            stripe_event_id='evt_recent',
            event_type='payment_intent.succeeded',
            status=WebhookEventStatus.PROCESSED,
            payload={}
        )
        
        # Test recent events manager
        recent_events = WebhookEventLog.recent.all()
        self.assertEqual(recent_events.count(), 1)
        self.assertEqual(recent_events.first().stripe_event_id, 'evt_recent')


class WebhookEventLogIntegrationTest(TestCase):
    """Integration tests for webhook event logging with webhook handler."""
    
    def test_log_webhook_event_processing(self):
        """Test logging webhook event processing lifecycle."""
        # Create initial log entry
        log = WebhookEventLog.objects.create(
            stripe_event_id='evt_integration_test',
            event_type='payment_intent.succeeded',
            status=WebhookEventStatus.RECEIVED,
            payload={
                'id': 'evt_integration_test',
                'type': 'payment_intent.succeeded',
                'data': {'object': {'id': 'pi_test_123'}}
            }
        )
        
        # Simulate processing workflow
        self.assertEqual(log.status, WebhookEventStatus.RECEIVED)
        
        # Mark as processing
        log.mark_as_processing()
        self.assertEqual(log.status, WebhookEventStatus.PROCESSING)
        
        # Simulate successful processing
        log.mark_as_processed()
        self.assertEqual(log.status, WebhookEventStatus.PROCESSED)
        self.assertIsNotNone(log.processed_at)
        
        # Verify processing time is reasonable
        duration = log.get_processing_duration()
        self.assertIsNotNone(duration)
        self.assertLess(duration.total_seconds(), 1)  # Should be very fast in test
    
    def test_retry_logic_workflow(self):
        """Test retry logic workflow for failed webhook events."""
        log = WebhookEventLog.objects.create(
            stripe_event_id='evt_retry_test',
            event_type='payment_intent.payment_failed',
            status=WebhookEventStatus.RECEIVED,
            payload={}
        )
        
        # Simulate failure and retry cycle
        for retry_attempt in range(3):
            self.assertTrue(log.is_retryable())
            
            # Increment retry count
            log.increment_retry_count()
            self.assertEqual(log.retry_count, retry_attempt + 1)
            self.assertEqual(log.status, WebhookEventStatus.RETRYING)
            
            # Mark as failed
            log.mark_as_failed(f"Retry attempt {retry_attempt + 1} failed")
        
        # After max retries, should not be retryable
        log.retry_count = 5
        log.save()
        self.assertFalse(log.is_retryable())