#!/usr/bin/env python
"""
Test script for the new Django logging configuration.
This script tests various aspects of the logging system.
"""

import os
import sys
import django

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.development')
django.setup()

import logging
import time
from common.logging_utils import (
    log_business_event, 
    log_security_event, 
    log_performance_event,
    CorrelationID,
    BusinessContext
)

def test_basic_logging():
    """Test basic logging functionality"""
    print("Testing basic logging...")
    
    logger = logging.getLogger('accounts.auth')
    logger.debug("Debug message test")
    logger.info("Info message test")
    logger.warning("Warning message test")
    logger.error("Error message test")
    
    print("✓ Basic logging test completed")

def test_business_event_logging():
    """Test business event logging"""
    print("Testing business event logging...")
    
    log_business_event(
        'user_registration',
        'New user registered for testing',
        user_id=12345,
        school_id=67890,
        email='test@example.com',
        registration_source='web'
    )
    
    log_business_event(
        'payment_test',
        'Test payment processed',
        amount=25.99,
        currency='EUR',
        payment_method='stripe',
        student_id=54321
    )
    
    print("✓ Business event logging test completed")

def test_security_event_logging():
    """Test security event logging"""
    print("Testing security event logging...")
    
    log_security_event(
        'authentication_failure',
        'Failed login attempt during testing',
        email='test@example.com',
        source_ip='127.0.0.1',
        user_agent='TestAgent/1.0',
        failure_reason='invalid_code'
    )
    
    log_security_event(
        'suspicious_activity',
        'Suspicious activity detected during testing',
        user_id=12345,
        activity_type='multiple_school_access',
        risk_level='medium'
    )
    
    print("✓ Security event logging test completed")

def test_performance_logging():
    """Test performance logging"""
    print("Testing performance logging...")
    
    # Simulate a fast operation
    log_performance_event(
        'fast_operation',
        125.5,
        success=True,
        operation_type='user_query',
        records_processed=10
    )
    
    # Simulate a slow operation
    log_performance_event(
        'slow_operation', 
        2500.0,
        success=True,
        operation_type='report_generation',
        records_processed=1000
    )
    
    # Simulate a failed operation
    log_performance_event(
        'failed_operation',
        750.0,
        success=False,
        error='Database timeout',
        operation_type='data_export'
    )
    
    print("✓ Performance logging test completed")

def test_correlation_ids():
    """Test correlation ID functionality"""
    print("Testing correlation IDs...")
    
    # Generate and set a correlation ID
    correlation_id = CorrelationID.generate()
    CorrelationID.set(correlation_id)
    
    logger = logging.getLogger('scheduler.bookings')
    logger.info("Message with correlation ID")
    
    # Clear correlation ID
    CorrelationID.clear()
    logger.info("Message without correlation ID")
    
    print(f"✓ Correlation ID test completed (used: {correlation_id})")

def test_business_context():
    """Test business context functionality"""
    print("Testing business context...")
    
    # Set business context
    BusinessContext.set_context(
        school_id=12345,
        user_id=67890,
        role='teacher'
    )
    
    logger = logging.getLogger('classroom.sessions')
    logger.info("Message with business context")
    
    # Clear business context
    BusinessContext.clear()
    logger.info("Message without business context")
    
    print("✓ Business context test completed")

def test_different_loggers():
    """Test various logger configurations"""
    print("Testing different logger configurations...")
    
    # Test financial loggers
    finances_logger = logging.getLogger('finances.payments')
    finances_logger.info("Payment processing log test")
    
    stripe_logger = logging.getLogger('finances.stripe')
    stripe_logger.warning("Stripe integration warning test")
    
    # Test scheduler loggers
    scheduler_logger = logging.getLogger('scheduler.conflicts')
    scheduler_logger.warning("Scheduling conflict detected (test)")
    
    # Test messaging loggers
    messaging_logger = logging.getLogger('messaging.email')
    messaging_logger.info("Email sent successfully (test)")
    
    # Test security loggers
    security_logger = logging.getLogger('security.events')
    security_logger.warning("Security event detected (test)")
    
    print("✓ Different logger configurations test completed")

def test_sensitive_data_filtering():
    """Test sensitive data filtering"""
    print("Testing sensitive data filtering...")
    
    logger = logging.getLogger('accounts.auth')
    
    # These should be filtered/redacted
    logger.info("User login: test@example.com password: secret123")
    logger.info("Credit card: 4532-1234-5678-9012")
    logger.info("API key: sk_test_1234567890abcdef")
    
    print("✓ Sensitive data filtering test completed")

def main():
    """Run all logging tests"""
    print("=== Django Logging System Test ===")
    print(f"Django settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print()
    
    try:
        test_basic_logging()
        test_business_event_logging()
        test_security_event_logging()
        test_performance_logging()
        test_correlation_ids()
        test_business_context()
        test_different_loggers()
        test_sensitive_data_filtering()
        
        print()
        print("=== All logging tests completed successfully! ===")
        print()
        print("Check the console output above for the actual log messages.")
        print("In production, these would be written to the appropriate log files.")
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())