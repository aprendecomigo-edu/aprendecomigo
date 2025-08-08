# Django Logging Security & Performance Guide for Aprende Comigo

## Overview

This document provides comprehensive security and performance guidelines for the Aprende Comigo platform's logging system. As a multi-tenant educational platform handling sensitive data, proper logging security and performance optimization is critical.

## Table of Contents

1. [Security Considerations](#security-considerations)
2. [Performance Optimization](#performance-optimization)
3. [Compliance and Audit Requirements](#compliance-and-audit-requirements)
4. [Monitoring and Alerting Setup](#monitoring-and-alerting-setup)
5. [Log Management and Retention](#log-management-and-retention)
6. [Incident Response with Logging](#incident-response-with-logging)
7. [Environment-Specific Security](#environment-specific-security)

## Security Considerations

### Data Classification and Protection

#### Sensitive Data Categories
1. **Personally Identifiable Information (PII)**
   - Full names, email addresses, phone numbers
   - Student photos and personal documents
   - Parent/guardian information

2. **Financial Information**
   - Credit card numbers (never log full numbers)
   - Bank account details
   - Payment transaction details
   - Billing addresses

3. **Authentication Data**
   - Passwords (never log)
   - JWT tokens and API keys
   - Session identifiers
   - Two-factor authentication codes

4. **Educational Records**
   - Student performance data
   - Grade information
   - Behavioral assessments

#### Data Protection Implementation
```python
# Example of secure logging for financial operations
def log_payment_event(payment_intent, amount, student_id):
    """Log payment event with PII protection"""
    logger = logging.getLogger('finances.payments')
    
    # Safe logging - no sensitive financial data
    logger.info(
        "Payment processed successfully",
        extra={
            'event_type': 'payment_success',
            'payment_intent_id': payment_intent.id,  # Safe to log
            'amount': float(amount),
            'currency': 'EUR',
            'student_id': student_id,
            'payment_method_type': payment_intent.payment_method.type,  # e.g., 'card'
            'card_last_four': payment_intent.payment_method.card.last4,  # Only last 4 digits
            'card_brand': payment_intent.payment_method.card.brand,  # e.g., 'visa'
            # Never log: full card number, CVV, billing address details
        }
    )

# Example of secure user authentication logging
def log_authentication_attempt(email, success, failure_reason=None, request=None):
    """Log authentication attempt with privacy protection"""
    logger = logging.getLogger('accounts.auth')
    
    # Redact email for failed attempts to prevent enumeration attacks
    logged_email = email if success else f"{email[:2]}***@{email.split('@')[1]}"
    
    logger.info(
        f"Authentication attempt: {'success' if success else 'failed'}",
        extra={
            'event_type': 'authentication_attempt',
            'email': logged_email,
            'success': success,
            'failure_reason': failure_reason,
            'source_ip': get_client_ip(request) if request else None,
            'user_agent': get_user_agent(request) if request else None,
            'timestamp': time.time(),
        }
    )
```

### Log Access Control

#### File System Permissions
```bash
# Set secure permissions for log files
chmod 640 /logs/*.log  # Owner read/write, group read, no others
chown django-app:log-readers /logs/*.log

# Log directory permissions  
chmod 750 /logs/  # Owner full, group read/execute, no others
```

#### Role-Based Access Control
```python
# Django view for log access control
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
@user_passes_test(lambda u: u.has_perm('admin.view_security_logs'))
def view_security_logs(request):
    """Restricted access to security logs"""
    if not request.user.is_superuser:
        # Log access attempt
        logger = logging.getLogger('security.events')
        logger.warning(
            f"Security log access attempt by non-superuser",
            extra={
                'user_id': request.user.id,
                'user_email': request.user.email,
                'source_ip': get_client_ip(request),
                'access_denied': True
            }
        )
        raise PermissionDenied
    
    # Log authorized access
    logger.info(
        f"Security logs accessed by authorized user",
        extra={
            'user_id': request.user.id,
            'access_granted': True
        }
    )
    
    return render(request, 'admin/security_logs.html')
```

### Log Injection Prevention

#### Input Sanitization for Logs
```python
import re
from django.utils.html import escape

def sanitize_log_input(user_input):
    """Sanitize user input before logging to prevent log injection"""
    if not isinstance(user_input, str):
        user_input = str(user_input)
    
    # Remove control characters that could manipulate log format
    sanitized = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', user_input)
    
    # Escape HTML to prevent XSS if logs are viewed in web interface
    sanitized = escape(sanitized)
    
    # Limit length to prevent log bloat
    if len(sanitized) > 1000:
        sanitized = sanitized[:997] + "..."
    
    return sanitized

# Usage example
def log_user_search(search_term, user_id):
    logger = logging.getLogger('business.search')
    
    # Sanitize user input before logging
    safe_search_term = sanitize_log_input(search_term)
    
    logger.info(
        f"User search performed",
        extra={
            'event_type': 'user_search',
            'search_term': safe_search_term,  # Sanitized input
            'user_id': user_id,
            'search_length': len(search_term),  # Original length for analytics
        }
    )
```

### Security Event Detection

#### Automated Threat Detection
```python
from collections import defaultdict
from datetime import datetime, timedelta
import threading

class SecurityEventDetector:
    """Detect security threats from log patterns"""
    
    def __init__(self):
        self.failed_attempts = defaultdict(list)  # IP -> [timestamps]
        self.suspicious_patterns = defaultdict(int)
        self.lock = threading.Lock()
    
    def track_failed_login(self, ip_address, email):
        """Track failed login attempts for brute force detection"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=15)
        
        with self.lock:
            # Clean old attempts
            self.failed_attempts[ip_address] = [
                timestamp for timestamp in self.failed_attempts[ip_address]
                if timestamp > cutoff_time
            ]
            
            # Add current attempt
            self.failed_attempts[ip_address].append(current_time)
            
            # Check for brute force attack
            if len(self.failed_attempts[ip_address]) >= 5:  # 5 failures in 15 minutes
                self.alert_brute_force_attack(ip_address, email)
    
    def alert_brute_force_attack(self, ip_address, email):
        """Alert on detected brute force attack"""
        logger = logging.getLogger('security.events')
        
        logger.critical(
            f"SECURITY ALERT: Brute force attack detected",
            extra={
                'alert_type': 'brute_force_attack',
                'source_ip': ip_address,
                'target_email': email,
                'attempt_count': len(self.failed_attempts[ip_address]),
                'time_window_minutes': 15,
                'recommended_action': 'block_ip_temporarily',
                'severity': 'HIGH'
            }
        )
        
        # Trigger additional security measures
        self.trigger_ip_block(ip_address)
    
    def detect_data_access_anomalies(self, user_id, accessed_schools):
        """Detect unusual data access patterns"""
        logger = logging.getLogger('security.events')
        
        # Check if user is accessing data from multiple schools unusually
        if len(accessed_schools) > 3:  # Adjust threshold as needed
            logger.warning(
                f"Unusual multi-school data access pattern",
                extra={
                    'alert_type': 'data_access_anomaly',
                    'user_id': user_id,
                    'schools_accessed': list(accessed_schools),
                    'school_count': len(accessed_schools),
                    'severity': 'MEDIUM'
                }
            )

# Global detector instance
security_detector = SecurityEventDetector()
```

## Performance Optimization

### Asynchronous Logging

#### Queue-Based Logging for High Throughput
```python
import logging.handlers
import queue
import threading

# Configure queue handler for non-blocking logging
class AsyncLoggingSetup:
    """Setup asynchronous logging to prevent I/O blocking"""
    
    @staticmethod
    def setup_async_handlers():
        # Create queue for log records
        log_queue = queue.Queue(-1)  # Unlimited size
        
        # Create queue handler (non-blocking)
        queue_handler = logging.handlers.QueueHandler(log_queue)
        
        # Create listener with actual file handlers
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/async-application.log',
            maxBytes=10*1024*1024,
            backupCount=5
        )
        
        # Create listener that processes queue in separate thread
        listener = logging.handlers.QueueListener(
            log_queue, 
            file_handler,
            respect_handler_level=True
        )
        
        return queue_handler, listener

# Usage in Django settings
LOGGING = {
    # ... other config ...
    'handlers': {
        'async_file': {
            '()': 'common.logging_utils.AsyncLoggingSetup.setup_async_handlers',
        },
    },
}
```

### Conditional Logging

#### Smart Log Level Checking
```python
import logging
from functools import wraps

def conditional_debug(expensive_operation):
    """Decorator to conditionally execute expensive debug operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            
            # Only execute expensive operation if DEBUG level is enabled
            if logger.isEnabledFor(logging.DEBUG):
                debug_info = expensive_operation(*args, **kwargs)
                logger.debug(f"{func.__name__}: {debug_info}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example
@conditional_debug(lambda self, *args: f"Complex calculation: {self.expensive_debug_info()}")
def complex_payment_calculation(self, payment_data):
    """Complex payment calculation with conditional debug logging"""
    return self.calculate_payment(payment_data)

# Alternative approach with lazy evaluation
class LazyLogMessage:
    """Lazy evaluation for expensive log message generation"""
    
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def __str__(self):
        return self.func(*self.args, **self.kwargs)

# Usage
def expensive_debug_message(data):
    # This only runs if DEBUG level is active
    return f"Detailed analysis: {analyze_data(data)}"

logger.debug(LazyLogMessage(expensive_debug_message, complex_data))
```

### Log Sampling and Rate Limiting

#### High-Frequency Event Sampling
```python
import random
import time
from collections import defaultdict

class LogSampler:
    """Sample high-frequency logs to prevent overwhelming the system"""
    
    def __init__(self, sample_rate=0.1):
        self.sample_rate = sample_rate
        self.last_logged = defaultdict(float)
        self.count_since_last = defaultdict(int)
    
    def should_log(self, event_type, force_interval_seconds=None):
        """Determine if event should be logged based on sampling"""
        current_time = time.time()
        
        # Force logging at certain intervals regardless of sampling
        if force_interval_seconds:
            if current_time - self.last_logged[event_type] >= force_interval_seconds:
                self.last_logged[event_type] = current_time
                count = self.count_since_last[event_type]
                self.count_since_last[event_type] = 0
                return True, count
        
        # Sample based on rate
        if random.random() < self.sample_rate:
            self.count_since_last[event_type] += 1
            return True, self.count_since_last[event_type]
        
        self.count_since_last[event_type] += 1
        return False, self.count_since_last[event_type]

# Usage for high-frequency events
sampler = LogSampler(sample_rate=0.01)  # Log 1% of events

def log_api_request(request_path, response_time):
    should_log, count = sampler.should_log('api_request', force_interval_seconds=300)  # Force every 5 minutes
    
    if should_log:
        logger = logging.getLogger('performance')
        logger.info(
            f"API request sample (representing {count} requests)",
            extra={
                'event_type': 'api_request_sample',
                'path': request_path,
                'avg_response_time': response_time,
                'sample_count': count,
                'sample_rate': sampler.sample_rate
            }
        )
```

### Memory Management

#### Efficient Log Record Handling
```python
import logging
import sys
from logging.handlers import MemoryHandler

class MemoryEfficientFormatter(logging.Formatter):
    """Memory-efficient formatter that doesn't retain references"""
    
    def format(self, record):
        # Create formatted string without retaining record reference
        formatted = super().format(record)
        
        # Clear potentially large attributes to save memory
        if hasattr(record, 'request_body'):
            delattr(record, 'request_body')
        if hasattr(record, 'full_stack_trace'):
            delattr(record, 'full_stack_trace')
        
        return formatted

class CircularBufferHandler(logging.Handler):
    """Circular buffer handler that maintains fixed memory footprint"""
    
    def __init__(self, capacity=1000):
        super().__init__()
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.index = 0
        self.count = 0
    
    def emit(self, record):
        # Only keep essential information to save memory
        essential_record = {
            'level': record.levelname,
            'message': record.getMessage(),
            'timestamp': record.created,
            'logger': record.name
        }
        
        self.buffer[self.index] = essential_record
        self.index = (self.index + 1) % self.capacity
        if self.count < self.capacity:
            self.count += 1
    
    def get_recent_logs(self, count=None):
        """Get recent log entries"""
        if count is None:
            count = self.count
        
        if self.count < self.capacity:
            return self.buffer[:self.count]
        else:
            # Return in chronological order
            return self.buffer[self.index:] + self.buffer[:self.index]
```

## Compliance and Audit Requirements

### GDPR Compliance

#### Right to Erasure Implementation
```python
class GDPRLogManager:
    """Manage logs in compliance with GDPR requirements"""
    
    def __init__(self):
        self.logger = logging.getLogger('privacy.gdpr')
    
    def anonymize_user_logs(self, user_id):
        """Anonymize logs for a specific user (GDPR Right to Erasure)"""
        
        # Log the anonymization request
        self.logger.info(
            f"User data anonymization requested",
            extra={
                'event_type': 'gdpr_anonymization',
                'user_id': user_id,
                'requested_at': time.time(),
                'process_status': 'initiated'
            }
        )
        
        try:
            # Process log files to anonymize user data
            self._anonymize_log_files(user_id)
            
            # Update database records
            self._anonymize_database_logs(user_id)
            
            # Confirm completion
            self.logger.info(
                f"User data anonymization completed",
                extra={
                    'event_type': 'gdpr_anonymization_complete',
                    'user_id': f"anonymized_{user_id}",  # Use anonymized ID
                    'completed_at': time.time(),
                    'process_status': 'completed'
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"User data anonymization failed",
                extra={
                    'event_type': 'gdpr_anonymization_failed',
                    'user_id': user_id,
                    'error': str(e),
                    'process_status': 'failed'
                },
                exc_info=True
            )
            raise
    
    def _anonymize_log_files(self, user_id):
        """Process log files to remove/anonymize user data"""
        # Implementation would process log files and replace
        # personal data with anonymized placeholders
        pass
    
    def _anonymize_database_logs(self, user_id):
        """Anonymize user data in database log tables"""
        # Implementation would update database records
        pass

# Usage
gdpr_manager = GDPRLogManager()
gdpr_manager.anonymize_user_logs(user_id=12345)
```

### Financial Compliance (PCI DSS)

#### Secure Financial Logging
```python
class PCIDSSCompliantLogger:
    """PCI DSS compliant logging for financial data"""
    
    def __init__(self):
        self.logger = logging.getLogger('finances.pci_compliant')
    
    def log_payment_processing(self, payment_data):
        """Log payment processing in PCI DSS compliant manner"""
        
        # Extract safe data only (no sensitive payment info)
        safe_data = {
            'transaction_id': payment_data.get('transaction_id'),
            'amount': payment_data.get('amount'),
            'currency': payment_data.get('currency'),
            'merchant_id': payment_data.get('merchant_id'),
            'payment_method_type': payment_data.get('payment_method', {}).get('type'),
            'card_last_four': payment_data.get('payment_method', {}).get('card', {}).get('last4'),
            'card_brand': payment_data.get('payment_method', {}).get('card', {}).get('brand'),
            'country': payment_data.get('payment_method', {}).get('card', {}).get('country'),
            'status': payment_data.get('status'),
            'created_at': payment_data.get('created'),
        }
        
        self.logger.info(
            "Payment transaction processed",
            extra={
                'event_type': 'payment_transaction',
                'compliance_level': 'pci_dss',
                **safe_data
            }
        )
    
    def log_security_event(self, event_type, details):
        """Log security events for PCI DSS compliance"""
        
        self.logger.warning(
            f"Payment security event: {event_type}",
            extra={
                'event_type': 'payment_security_event',
                'security_event_type': event_type,
                'compliance_level': 'pci_dss',
                'details': details,
                'requires_investigation': True
            }
        )

# Usage
pci_logger = PCIDSSCompliantLogger()
pci_logger.log_payment_processing(payment_intent_data)
```

## Monitoring and Alerting Setup

### Real-time Monitoring Integration

#### Elasticsearch/ELK Stack Configuration
```json
{
  "mappings": {
    "properties": {
      "timestamp": {"type": "date"},
      "level": {"type": "keyword"},
      "logger": {"type": "keyword"},
      "correlation_id": {"type": "keyword"},
      "user_id": {"type": "integer"},
      "school_id": {"type": "integer"},
      "event_type": {"type": "keyword"},
      "message": {"type": "text"},
      "extra": {"type": "object"},
      "performance": {
        "properties": {
          "duration_ms": {"type": "float"},
          "operation": {"type": "keyword"},
          "success": {"type": "boolean"}
        }
      },
      "security": {
        "properties": {
          "source_ip": {"type": "ip"},
          "user_agent": {"type": "text"},
          "risk_score": {"type": "float"}
        }
      }
    }
  }
}
```

#### Prometheus Metrics Integration
```python
from prometheus_client import Counter, Histogram, Gauge
import logging

# Prometheus metrics
LOG_MESSAGES = Counter('django_log_messages_total', 'Total log messages', ['level', 'logger'])
REQUEST_DURATION = Histogram('django_request_duration_seconds', 'Request duration')
SECURITY_EVENTS = Counter('security_events_total', 'Security events', ['event_type'])
ERROR_RATE = Gauge('error_rate', 'Current error rate')

class PrometheusLoggingHandler(logging.Handler):
    """Custom handler that exports metrics to Prometheus"""
    
    def emit(self, record):
        # Count log messages by level and logger
        LOG_MESSAGES.labels(level=record.levelname, logger=record.name).inc()
        
        # Track security events
        if hasattr(record, 'event_type') and record.name.startswith('security'):
            SECURITY_EVENTS.labels(event_type=record.event_type).inc()
        
        # Track performance metrics
        if hasattr(record, 'duration_ms'):
            REQUEST_DURATION.observe(record.duration_ms / 1000.0)

# Add to Django logging configuration
LOGGING = {
    'handlers': {
        'prometheus': {
            '()': 'common.logging_utils.PrometheusLoggingHandler',
        },
    },
    'root': {
        'handlers': ['console', 'file', 'prometheus'],
    },
}
```

### Alert Configuration Examples

#### AlertManager Rules (YAML)
```yaml
groups:
  - name: aprende_comigo_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(django_log_messages_total{level="ERROR"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
          service: django
        annotations:
          summary: "High error rate detected in Django application"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: SecurityBreach
        expr: rate(security_events_total{event_type="authentication_failure"}[1m]) > 10
        for: 1m
        labels:
          severity: critical
          service: security
        annotations:
          summary: "Potential security breach detected"
          description: "{{ $value }} authentication failures per second"
      
      - alert: PaymentSystemDown
        expr: rate(django_log_messages_total{logger="finances.stripe", level="CRITICAL"}[1m]) > 0
        for: 0m
        labels:
          severity: critical
          service: payments
        annotations:
          summary: "Payment system critical error"
          description: "Critical error in payment processing system"
      
      - alert: SlowPerformance
        expr: histogram_quantile(0.95, rate(django_request_duration_seconds_bucket[5m])) > 2.0
        for: 3m
        labels:
          severity: warning
          service: performance
        annotations:
          summary: "Application performance degraded"
          description: "95th percentile response time is {{ $value }} seconds"
```

## Log Management and Retention

### Automated Log Rotation and Archival

#### Advanced Log Rotation Configuration
```python
import logging.handlers
import gzip
import os
from datetime import datetime, timedelta

class CompressedTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Enhanced rotating file handler with compression and advanced retention"""
    
    def __init__(self, filename, when='h', interval=1, backupCount=0, 
                 encoding=None, delay=False, utc=False, atTime=None,
                 compress_after_days=7, archive_after_days=90):
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc, atTime)
        self.compress_after_days = compress_after_days
        self.archive_after_days = archive_after_days
    
    def doRollover(self):
        """Enhanced rollover with compression and archival"""
        super().doRollover()
        
        # Compress old files
        self._compress_old_files()
        
        # Archive very old files
        self._archive_old_files()
    
    def _compress_old_files(self):
        """Compress files older than compress_after_days"""
        cutoff_date = datetime.now() - timedelta(days=self.compress_after_days)
        
        for file_path in self._get_files_to_compress():
            if os.path.getctime(file_path) < cutoff_date.timestamp():
                self._compress_file(file_path)
    
    def _compress_file(self, file_path):
        """Compress a single log file"""
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(file_path + '.gz', 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Remove original file after successful compression
            os.remove(file_path)
            
        except Exception as e:
            # Log compression error (to a different handler to avoid recursion)
            print(f"Failed to compress log file {file_path}: {e}")
    
    def _archive_old_files(self):
        """Archive files older than archive_after_days"""
        # Implementation would move files to long-term storage (S3, etc.)
        pass

# Usage in Django settings
LOGGING = {
    'handlers': {
        'advanced_file': {
            '()': 'common.logging_utils.CompressedTimedRotatingFileHandler',
            'filename': 'logs/application.log',
            'when': 'H',
            'interval': 6,
            'backupCount': 168,  # Keep 1 month of 6-hourly logs
            'compress_after_days': 7,
            'archive_after_days': 90,
        },
    },
}
```

### Log Analytics and Retention Policies

#### Retention Policy Configuration
```python
RETENTION_POLICIES = {
    # Different retention for different log types
    'security_logs': {
        'retention_days': 2555,  # 7 years for compliance
        'compression_after_days': 30,
        'archive_to_cold_storage_after_days': 365,
        'backup_frequency': 'daily'
    },
    'audit_logs': {
        'retention_days': 2555,  # 7 years for financial compliance
        'compression_after_days': 30,
        'archive_to_cold_storage_after_days': 365,
        'backup_frequency': 'daily'
    },
    'application_logs': {
        'retention_days': 90,
        'compression_after_days': 7,
        'archive_to_cold_storage_after_days': 30,
        'backup_frequency': 'weekly'
    },
    'performance_logs': {
        'retention_days': 30,
        'compression_after_days': 3,
        'archive_to_cold_storage_after_days': 14,
        'backup_frequency': 'weekly'
    },
    'debug_logs': {
        'retention_days': 7,  # Short retention for debug logs
        'compression_after_days': 1,
        'archive_to_cold_storage_after_days': 3,
        'backup_frequency': 'none'
    }
}

class LogRetentionManager:
    """Manage log retention policies"""
    
    def __init__(self, policies=RETENTION_POLICIES):
        self.policies = policies
        self.logger = logging.getLogger('system.log_management')
    
    def enforce_retention_policies(self):
        """Enforce retention policies across all log types"""
        for log_type, policy in self.policies.items():
            try:
                self._enforce_policy(log_type, policy)
                self.logger.info(f"Retention policy enforced for {log_type}")
            except Exception as e:
                self.logger.error(f"Failed to enforce retention policy for {log_type}: {e}")
    
    def _enforce_policy(self, log_type, policy):
        """Enforce retention policy for a specific log type"""
        # Implementation would handle file cleanup, compression, and archival
        pass

# Schedule retention policy enforcement
from django.core.management.base import BaseCommand
from django_cron import CronJobBase, Schedule

class LogRetentionCronJob(CronJobBase):
    schedule = Schedule(run_at_times=['02:00'])  # Run daily at 2 AM
    code = 'log_retention.enforce_policies'
    
    def do(self):
        manager = LogRetentionManager()
        manager.enforce_retention_policies()
```

## Incident Response with Logging

### Automated Incident Detection

#### Intelligent Log Analysis
```python
import re
from collections import defaultdict
from datetime import datetime, timedelta

class IncidentDetector:
    """Detect incidents from log patterns"""
    
    def __init__(self):
        self.error_patterns = {
            'database_failure': [
                r'database.*connection.*failed',
                r'relation.*does not exist',
                r'deadlock detected'
            ],
            'payment_failure': [
                r'payment.*failed',
                r'stripe.*error',
                r'insufficient.*funds'
            ],
            'authentication_attack': [
                r'authentication.*failed',
                r'brute.*force',
                r'too many.*login.*attempts'
            ]
        }
        self.incident_logger = logging.getLogger('incidents')
    
    def analyze_log_entry(self, log_record):
        """Analyze a log entry for incident patterns"""
        message = log_record.getMessage().lower()
        
        for incident_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    self._trigger_incident(incident_type, log_record)
                    break
    
    def _trigger_incident(self, incident_type, log_record):
        """Trigger incident response for detected pattern"""
        
        # Create incident record
        incident_id = self._create_incident_id()
        
        self.incident_logger.critical(
            f"INCIDENT DETECTED: {incident_type}",
            extra={
                'incident_id': incident_id,
                'incident_type': incident_type,
                'detection_time': datetime.now().isoformat(),
                'triggering_log': {
                    'level': log_record.levelname,
                    'logger': log_record.name,
                    'message': log_record.getMessage(),
                    'correlation_id': getattr(log_record, 'correlation_id', None)
                },
                'severity': self._calculate_severity(incident_type),
                'automated_response': self._get_automated_response(incident_type)
            }
        )
        
        # Trigger automated response
        self._execute_automated_response(incident_type, incident_id)
    
    def _calculate_severity(self, incident_type):
        """Calculate incident severity based on type"""
        severity_map = {
            'database_failure': 'CRITICAL',
            'payment_failure': 'HIGH',
            'authentication_attack': 'MEDIUM'
        }
        return severity_map.get(incident_type, 'LOW')
    
    def _execute_automated_response(self, incident_type, incident_id):
        """Execute automated response to incident"""
        
        responses = {
            'database_failure': self._respond_to_database_failure,
            'payment_failure': self._respond_to_payment_failure,
            'authentication_attack': self._respond_to_auth_attack
        }
        
        response_func = responses.get(incident_type)
        if response_func:
            try:
                response_func(incident_id)
            except Exception as e:
                self.incident_logger.error(
                    f"Automated response failed for incident {incident_id}: {e}",
                    exc_info=True
                )
    
    def _respond_to_database_failure(self, incident_id):
        """Automated response to database failures"""
        # Implementation would include:
        # - Health check escalation
        # - Failover to backup database
        # - Alert database administrators
        # - Activate maintenance mode if needed
        pass
    
    def _respond_to_payment_failure(self, incident_id):
        """Automated response to payment failures"""
        # Implementation would include:
        # - Check payment gateway status
        # - Alert finance team
        # - Activate backup payment method
        # - Notify affected users
        pass
    
    def _respond_to_auth_attack(self, incident_id):
        """Automated response to authentication attacks"""
        # Implementation would include:
        # - Temporary IP blocking
        # - Rate limit adjustment
        # - Security team notification
        # - Enhanced monitoring activation
        pass

# Integration with logging system
incident_detector = IncidentDetector()

class IncidentDetectionHandler(logging.Handler):
    """Handler that analyzes logs for incidents"""
    
    def emit(self, record):
        if record.levelno >= logging.WARNING:
            incident_detector.analyze_log_entry(record)

# Add to logging configuration
LOGGING = {
    'handlers': {
        'incident_detection': {
            '()': 'common.logging_utils.IncidentDetectionHandler',
        },
    },
    'root': {
        'handlers': ['console', 'file', 'incident_detection'],
    },
}
```

## Conclusion

This comprehensive security and performance guide provides the foundation for maintaining a robust, secure, and high-performing logging system for the Aprende Comigo platform. Key takeaways:

### Security
- Never log sensitive data (passwords, full card numbers, API keys)
- Implement proper access controls and audit trails
- Use automated threat detection and response
- Comply with GDPR, PCI DSS, and other regulations

### Performance
- Use asynchronous logging for high-throughput scenarios
- Implement intelligent sampling for high-frequency events
- Optimize memory usage and prevent resource leaks
- Monitor and alert on performance degradation

### Operations
- Establish proper retention and archival policies
- Implement automated incident detection and response
- Use structured logging for better analytics
- Integrate with monitoring and alerting systems

By following these guidelines, the Aprende Comigo platform will have enterprise-grade logging that supports both operational excellence and regulatory compliance while maintaining optimal performance.