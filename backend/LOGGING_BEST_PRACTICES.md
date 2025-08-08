# Django Logging Best Practices for Aprende Comigo Platform

## Overview

This guide provides comprehensive logging best practices for the Aprende Comigo multi-tenant tutoring platform. Our logging architecture is designed to support business intelligence, security monitoring, performance optimization, and compliance requirements.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Logging Levels and When to Use Them](#logging-levels-and-when-to-use-them)
3. [Logger Namespaces](#logger-namespaces)
4. [Business Event Logging](#business-event-logging)
5. [Security Event Logging](#security-event-logging)
6. [Performance Logging](#performance-logging)
7. [Error Handling and Logging](#error-handling-and-logging)
8. [Sensitive Data Protection](#sensitive-data-protection)
9. [Context and Correlation IDs](#context-and-correlation-ids)
10. [Environment-Specific Considerations](#environment-specific-considerations)
11. [Testing Logging](#testing-logging)
12. [Monitoring and Alerting](#monitoring-and-alerting)

## Getting Started

### Basic Logger Setup

Always use `logging.getLogger(__name__)` for automatic namespacing:

```python
import logging
from common.logging_utils import log_business_event, log_security_event, log_performance_event

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        logger.info("PaymentService initialized successfully")
    
    def process_payment(self, amount, student_id, school_id):
        start_time = time.time()
        
        try:
            # Log business event
            log_business_event(
                'payment_initiated',
                f"Payment of €{amount} initiated for student {student_id}",
                amount=amount,
                student_id=student_id,
                school_id=school_id,
                payment_method='stripe'
            )
            
            # Process payment logic here
            result = self.stripe_service.create_payment_intent(amount)
            
            # Log successful completion
            duration_ms = (time.time() - start_time) * 1000
            log_performance_event('payment_processing', duration_ms, 
                                amount=amount, success=True)
            
            logger.info(f"Payment processed successfully: {result.id}")
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_performance_event('payment_processing', duration_ms, 
                                amount=amount, success=False, error=str(e))
            
            logger.error(f"Payment processing failed: {e}", exc_info=True)
            raise
```

## Logging Levels and When to Use Them

### DEBUG Level
Use for detailed diagnostic information that's only of interest when diagnosing problems.

```python
logger.debug(f"Processing {len(students)} students for school {school_id}")
logger.debug(f"Query params: {request.query_params}")
logger.debug(f"Calculated availability slots: {available_slots}")
```

**When to use:**
- Variable values during complex calculations
- Query parameters and intermediate results
- Detailed workflow steps
- Development troubleshooting

### INFO Level
Use for general information that confirms things are working as expected.

```python
logger.info(f"New student registered: {student.email} in school {school.name}")
logger.info(f"Session scheduled: {session.id} for {session.scheduled_start}")
logger.info(f"Teacher invitation sent to {email}")
```

**When to use:**
- Major workflow milestones
- User actions and state changes
- System initialization and configuration
- Business process completions

### WARNING Level
Use when something unexpected happened, or anticipating a problem (e.g., 'disk space low'), but the software is still working as expected.

```python
logger.warning(f"Payment attempt failed due to insufficient funds: student {student_id}")
logger.warning(f"Teacher {teacher_id} has low availability for next week")
logger.warning(f"Email delivery failed, will retry: {email}")
```

**When to use:**
- Recoverable errors
- Business rule violations
- Resource constraints
- Retry scenarios

### ERROR Level
Use for more serious problems where the software has not been able to perform some function.

```python
logger.error(f"Failed to charge customer {customer_id}: {stripe_error}", exc_info=True)
logger.error(f"Database connection failed while processing session {session_id}")
logger.error(f"Unable to send critical notification: {error}")
```

**When to use:**
- Unrecoverable errors
- External service failures
- Data integrity issues
- Critical functionality failures

### CRITICAL Level
Use for very serious errors where the program itself may be unable to continue running.

```python
logger.critical(f"Database connection pool exhausted - system unstable")
logger.critical(f"Security breach detected: unauthorized access to school {school_id}")
logger.critical(f"Payment system completely unavailable")
```

**When to use:**
- System-wide failures
- Security breaches
- Data corruption
- Infrastructure failures

## Logger Namespaces

Our platform uses hierarchical logger names for organized logging:

### Application Areas
```python
# Authentication and user management
logger = logging.getLogger('accounts.auth')           # Authentication events
logger = logging.getLogger('accounts.security')      # Security violations
logger = logging.getLogger('accounts.throttles')     # Rate limiting events

# Financial operations  
logger = logging.getLogger('finances.payments')      # Payment processing
logger = logging.getLogger('finances.stripe')        # Stripe integration
logger = logging.getLogger('finances.fraud')         # Fraud detection
logger = logging.getLogger('finances.audit')         # Financial audit trail

# Scheduling system
logger = logging.getLogger('scheduler.bookings')     # Session booking events
logger = logging.getLogger('scheduler.conflicts')    # Scheduling conflicts
logger = logging.getLogger('scheduler.reminders')    # Reminder system

# Communication
logger = logging.getLogger('messaging.email')        # Email sending events
logger = logging.getLogger('messaging.invitations')  # Invitation flows
```

### Business Events
```python
# Use business event loggers for analytics and reporting
from common.logging_utils import get_business_event_logger

payment_logger = get_business_event_logger('payments')
session_logger = get_business_event_logger('sessions') 
auth_logger = get_business_event_logger('authentication')
```

## Business Event Logging

Business events are logged in structured JSON format for analytics and business intelligence.

### Payment Events
```python
from common.logging_utils import log_business_event

def process_payment(self, payment_data):
    log_business_event(
        'payment_initiated',
        f"Payment initiated for student {payment_data['student_id']}",
        amount=payment_data['amount'],
        currency=payment_data['currency'],
        payment_method=payment_data['method'],
        school_id=payment_data['school_id'],
        student_id=payment_data['student_id'],
        package_type=payment_data.get('package_type')
    )
    
def on_payment_success(self, payment_intent):
    log_business_event(
        'payment_completed',
        f"Payment successful: {payment_intent.id}",
        payment_intent_id=payment_intent.id,
        amount_received=payment_intent.amount_received,
        fees=payment_intent.application_fee_amount,
        processing_time_ms=self.calculate_processing_time()
    )
```

### Session Events
```python
def book_session(self, session_data):
    log_business_event(
        'session_booked',
        f"Session booked: {session_data['subject']} with {session_data['teacher_name']}",
        session_id=session_data['session_id'],
        teacher_id=session_data['teacher_id'],
        student_id=session_data['student_id'],
        school_id=session_data['school_id'],
        subject=session_data['subject'],
        duration_minutes=session_data['duration'],
        scheduled_start=session_data['start_time'].isoformat(),
        booking_lead_time_hours=self.calculate_lead_time(session_data['start_time'])
    )

def complete_session(self, session):
    log_business_event(
        'session_completed',
        f"Session completed: {session.id}",
        session_id=session.id,
        actual_duration_minutes=session.actual_duration_minutes,
        hours_consumed=session.hours_consumed,
        teacher_rating=session.teacher_rating,
        student_attendance=session.student_attended
    )
```

### User Events
```python
def create_teacher_profile(self, teacher_data):
    log_business_event(
        'teacher_registered',
        f"New teacher registered: {teacher_data['email']}",
        teacher_id=teacher_data['teacher_id'],
        school_id=teacher_data['school_id'],
        subjects=teacher_data['subjects'],
        experience_level=teacher_data['experience_level'],
        registration_source=teacher_data.get('source', 'direct')
    )
```

## Security Event Logging

Security events require special handling and are logged to dedicated security logs.

### Authentication Events
```python
from common.logging_utils import log_security_event

def handle_failed_login(self, email, ip_address, user_agent):
    log_security_event(
        'authentication_failure',
        f"Failed login attempt for {email}",
        email=email,
        source_ip=ip_address,
        user_agent=user_agent,
        failure_reason='invalid_credentials'
    )

def handle_suspicious_activity(self, user_id, activity_type, details):
    log_security_event(
        'suspicious_activity',
        f"Suspicious activity detected for user {user_id}: {activity_type}",
        user_id=user_id,
        activity_type=activity_type,
        details=details,
        risk_level='high'
    )
```

### Permission Violations
```python
def log_permission_violation(self, user, action, resource):
    logger = logging.getLogger('accounts.security')
    
    extra = {
        'event_type': 'permission_violation',
        'user_id': user.id,
        'action': action,
        'resource': resource,
        'user_role': user.get_role_for_school(self.school_id),
        'security_context': {
            'source_ip': self.get_client_ip(),
            'user_agent': self.get_user_agent(),
            'session_id': self.request.session.session_key
        }
    }
    
    logger.warning(
        f"User {user.id} attempted unauthorized action '{action}' on '{resource}'",
        extra=extra
    )
```

## Performance Logging

Track performance metrics for optimization and monitoring.

### Response Time Monitoring
```python
from common.logging_utils import log_performance_event
import time

class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log slow requests
        if duration_ms > 1000:  # Log requests slower than 1 second
            log_performance_event(
                'slow_request',
                duration_ms,
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                user_id=getattr(request.user, 'id', None)
            )
        
        return response
```

### Database Query Performance
```python
def get_student_dashboard_data(self, student_id):
    start_time = time.time()
    
    # Complex database operations
    dashboard_data = self.build_dashboard_data(student_id)
    
    query_time_ms = (time.time() - start_time) * 1000
    
    log_performance_event(
        'dashboard_query',
        query_time_ms,
        student_id=student_id,
        data_points=len(dashboard_data),
        cache_hit=self.was_cache_hit
    )
    
    return dashboard_data
```

## Error Handling and Logging

### Exception Handling with Context
```python
def process_webhook(self, webhook_data):
    logger = logging.getLogger('finances.webhooks')
    
    try:
        # Process webhook
        result = self.handle_webhook_event(webhook_data)
        logger.info(f"Webhook processed successfully: {webhook_data['id']}")
        return result
        
    except ValidationError as e:
        logger.warning(
            f"Invalid webhook data received: {webhook_data['id']}",
            extra={
                'webhook_id': webhook_data['id'],
                'validation_errors': e.message_dict,
                'webhook_type': webhook_data.get('type')
            }
        )
        raise
        
    except ExternalServiceError as e:
        logger.error(
            f"External service error processing webhook {webhook_data['id']}: {e}",
            extra={
                'webhook_id': webhook_data['id'],
                'service_name': e.service_name,
                'error_code': e.error_code
            },
            exc_info=True
        )
        raise
        
    except Exception as e:
        logger.critical(
            f"Unexpected error processing webhook {webhook_data['id']}: {e}",
            extra={
                'webhook_id': webhook_data['id'],
                'webhook_data': webhook_data  # Be careful with sensitive data
            },
            exc_info=True
        )
        raise
```

### Retry Logic with Logging
```python
def send_email_with_retry(self, email_data, max_attempts=3):
    logger = logging.getLogger('messaging.email')
    
    for attempt in range(1, max_attempts + 1):
        try:
            result = self.send_email(email_data)
            
            logger.info(
                f"Email sent successfully on attempt {attempt}",
                extra={
                    'email_to': email_data['to'],
                    'email_type': email_data['type'],
                    'attempt': attempt
                }
            )
            
            return result
            
        except TemporaryEmailError as e:
            if attempt == max_attempts:
                logger.error(
                    f"Email sending failed after {max_attempts} attempts",
                    extra={
                        'email_to': email_data['to'],
                        'email_type': email_data['type'],
                        'final_error': str(e)
                    },
                    exc_info=True
                )
                raise
            else:
                logger.warning(
                    f"Email sending failed on attempt {attempt}, retrying",
                    extra={
                        'email_to': email_data['to'],
                        'email_type': email_data['type'],
                        'attempt': attempt,
                        'error': str(e)
                    }
                )
                time.sleep(2 ** attempt)  # Exponential backoff
```

## Sensitive Data Protection

### What NOT to Log
- Passwords or password hashes
- JWT tokens or API keys
- Full credit card numbers
- Personal identification numbers
- Bank account details
- Full email addresses in some contexts

### Safe Logging Patterns
```python
# Bad - logs sensitive data
logger.info(f"User login: {user.email} with password {password}")

# Good - redacts sensitive data
logger.info(f"User login: {user.email[:3]}***@{user.email.split('@')[1]}")

# Use the SensitiveDataFilter (automatically applied)
logger.info(f"Processing payment for card ending in {card_number[-4:]}")

# For debugging, use structured logging with explicit redaction
logger.debug(
    "Payment processing details",
    extra={
        'payment_method_id': payment_method.id,
        'customer_id': customer.id,
        'amount': amount,
        'card_last_four': card_number[-4:],
        # Don't include full card number
    }
)
```

### User Data Logging
```python
def log_user_action(self, user, action, resource):
    # Safe user context logging
    logger.info(
        f"User action: {action} on {resource}",
        extra={
            'user_id': user.id,
            'user_role': user.get_role_display(),
            'school_id': self.get_current_school_id(),
            'action': action,
            'resource_type': type(resource).__name__,
            'resource_id': getattr(resource, 'id', None)
        }
    )
```

## Context and Correlation IDs

Our logging system automatically adds correlation IDs and business context to log entries.

### Correlation IDs
Correlation IDs are automatically generated for each request and propagated through all log entries. You can also manually set them:

```python
from common.logging_utils import CorrelationID

# In a background task or worker
correlation_id = CorrelationID.generate()
CorrelationID.set(correlation_id)

try:
    # All logging within this block will include the correlation ID
    logger.info("Processing background task")
    process_reminders()
finally:
    CorrelationID.clear()
```

### Business Context
Business context (school_id, user_id, role) is automatically added when available:

```python
from common.logging_utils import BusinessContext

# Manually set business context for background tasks
BusinessContext.set_context(
    school_id=school.id,
    user_id=user.id,
    role='teacher'
)

try:
    logger.info("Processing teacher analytics")
    # All logs will include the business context
    generate_teacher_report(teacher)
finally:
    BusinessContext.clear()
```

## Environment-Specific Considerations

### Development Environment
- Use DEBUG level for detailed troubleshooting
- Console output with colors for easy reading
- Optional file logging for debugging specific issues
- All loggers enabled for comprehensive visibility

### Production Environment
- INFO level for business events, WARNING+ for issues
- JSON format for monitoring tool integration
- Multiple handlers (files, syslog) for redundancy
- Performance-optimized configuration
- Long retention for audit logs

### Testing Environment
- WARNING+ level to reduce test noise
- Memory handlers for log verification in tests
- Null handlers for performance-heavy operations
- Captured logs can be asserted in tests

## Testing Logging

### Verifying Log Output in Tests
```python
import logging
from django.test import TestCase

class PaymentServiceTestCase(TestCase):
    def test_payment_logging(self):
        with self.assertLogs('finances.payments', level='INFO') as log:
            payment_service = PaymentService()
            payment_service.process_payment(25.00, student_id=1, school_id=1)
            
            # Verify log messages
            self.assertIn('Payment of €25.0 initiated', log.output[0])
            self.assertIn('Payment processed successfully', log.output[1])

    def test_security_event_logging(self):
        with self.assertLogs('security.events', level='WARNING') as log:
            # Trigger a security event
            self.client.post('/api/auth/verify/', {
                'email': 'test@example.com',
                'code': 'invalid_code'
            })
            
            # Verify security event was logged
            self.assertIn('authentication_failure', log.output[0])
```

### Testing Custom Filters
```python
class LoggingFilterTestCase(TestCase):
    def test_sensitive_data_filter(self):
        from common.logging_utils import SensitiveDataFilter
        
        filter = SensitiveDataFilter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='User email: user@example.com password: secret123',
            args=(),
            exc_info=None
        )
        
        filter.filter(record)
        
        # Verify email was redacted
        self.assertIn('***@example.com', record.getMessage())
        self.assertIn('[REDACTED]', record.getMessage())
        self.assertNotIn('secret123', record.getMessage())
```

## Monitoring and Alerting

### Key Metrics to Monitor
1. **Error Rates**: Increase in ERROR/CRITICAL level logs
2. **Security Events**: Authentication failures, permission violations
3. **Performance Degradation**: Slow response times, database queries
4. **Business Metrics**: Payment failures, session cancellations
5. **System Health**: Infrastructure issues, external service failures

### Alerting Rules Examples
```yaml
# Example alerting rules (for systems like Prometheus + AlertManager)
- alert: HighErrorRate
  expr: rate(django_log_messages{level="ERROR"}[5m]) > 0.1
  for: 2m
  annotations:
    summary: "High error rate detected"
    
- alert: AuthenticationFailures
  expr: rate(django_log_messages{logger="security.auth_failures"}[1m]) > 10
  for: 1m
  annotations:
    summary: "Multiple authentication failures detected"
    
- alert: PaymentSystemDown
  expr: rate(django_log_messages{logger="finances.stripe", level="CRITICAL"}[1m]) > 0
  for: 0m
  annotations:
    summary: "Payment system critical error"
```

### Log Analysis Queries
```json
// Example queries for log analysis systems like Elasticsearch

// Payment success rate over time
{
  "query": {
    "bool": {
      "must": [
        {"term": {"logger": "business.payments"}},
        {"range": {"timestamp": {"gte": "now-24h"}}}
      ]
    }
  },
  "aggs": {
    "success_rate": {
      "terms": {"field": "event_type"},
      "aggs": {
        "hourly": {
          "date_histogram": {
            "field": "timestamp",
            "interval": "1h"
          }
        }
      }
    }
  }
}

// Security events by school
{
  "query": {
    "bool": {
      "must": [
        {"term": {"logger": "security.events"}},
        {"range": {"timestamp": {"gte": "now-7d"}}}
      ]
    }
  },
  "aggs": {
    "by_school": {
      "terms": {"field": "school_id"},
      "aggs": {
        "event_types": {
          "terms": {"field": "event_type"}
        }
      }
    }
  }
}
```

## Performance Best Practices

### Lazy Evaluation
```python
# Bad - expensive operation always executed
logger.debug(f"Processing data: {expensive_calculation()}")

# Good - expensive operation only if DEBUG level is enabled
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Processing data: {expensive_calculation()}")

# Even better - use lazy evaluation
logger.debug("Processing data: %s", lambda: expensive_calculation())
```

### Efficient String Formatting
```python
# Use % formatting or .format() for better performance
logger.info("User %s performed action %s", user.id, action)
logger.info("User {user_id} performed action {action}", 
           user_id=user.id, action=action)

# Avoid f-strings in log messages if you're not sure about log level
# f-strings are always evaluated, even if the log level is disabled
```

### Bulk Operations
```python
def process_bulk_notifications(self, notifications):
    logger.info(f"Processing {len(notifications)} notifications")
    
    # Log summary instead of each individual item
    success_count = 0
    error_count = 0
    
    for notification in notifications:
        try:
            self.send_notification(notification)
            success_count += 1
        except Exception as e:
            error_count += 1
            # Only log individual errors, not successes
            logger.warning(f"Failed to send notification {notification.id}: {e}")
    
    # Log final summary
    logger.info(
        f"Bulk notification processing complete: {success_count} successful, {error_count} failed"
    )
```

## Conclusion

Effective logging is crucial for maintaining, debugging, and monitoring the Aprende Comigo platform. By following these best practices:

1. **Use appropriate log levels** for different types of information
2. **Structure your logs** with consistent formatting and context
3. **Protect sensitive data** while maintaining useful debugging information
4. **Monitor and alert** on key metrics and patterns
5. **Test your logging** to ensure it works as expected
6. **Consider performance** impact of logging operations

Remember: Good logging is an investment in the long-term maintainability and reliability of our platform. It helps us understand user behavior, detect issues early, and provide better support to our schools, teachers, and families.