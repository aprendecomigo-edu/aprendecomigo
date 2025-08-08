"""
Django Signals for Scheduling Reminders & Communications Integration - Issue #154

This module defines signals that are emitted when class status changes occur,
allowing the reminder system to react to these events.
"""

from django.dispatch import Signal, receiver
import logging

logger = logging.getLogger(__name__)

# Define the class status change signal
class_status_changed = Signal()


@receiver(class_status_changed)
def handle_class_status_change(sender, instance, old_status, new_status, changed_by=None, **kwargs):
    """
    Handle class status changes by delegating to the ReminderService.
    This avoids circular imports by handling the signal here.
    """
    try:
        # Import here to avoid circular imports
        from .reminder_services import ReminderService
        
        if changed_by:
            ReminderService.handle_class_status_change(
                instance, old_status, new_status, changed_by
            )
        else:
            logger.warning(f"Class status changed from {old_status} to {new_status} for {instance} but no changed_by user provided")
            
    except Exception as e:
        logger.error(f"Error handling class status change signal: {e}", exc_info=True)