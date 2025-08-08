# Logging Implementation Examples

This document provides practical examples of how to implement the new logging system across different parts of the Aprende Comigo platform.

## Example 1: Authentication Service with Security Logging

```python
# accounts/services/authentication_service.py
import logging
import time
from typing import Dict, Any, Optional
from django.contrib.auth import authenticate
from common.logging_utils import log_security_event, log_business_event, log_performance_event

logger = logging.getLogger('accounts.auth')
security_logger = logging.getLogger('security.auth_failures')

class AuthenticationService:
    def __init__(self):
        logger.info("AuthenticationService initialized")
    
    def authenticate_user(self, email: str, code: str, request) -> Dict[str, Any]:
        start_time = time.time()
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        try:
            # Attempt authentication
            user = self.verify_code(email, code)
            
            if user:
                # Log successful authentication
                log_business_event(
                    'user_login_success',
                    f"User {email} authenticated successfully",
                    user_id=user.id,
                    email=email,
                    source_ip=client_ip,
                    user_agent=user_agent
                )
                
                # Log performance
                duration_ms = (time.time() - start_time) * 1000
                log_performance_event('user_authentication', duration_ms, 
                                    success=True, method='email_code')
                
                logger.info(f"Authentication successful for user {user.id}")
                return {'success': True, 'user': user}
            
            else:
                # Log failed authentication
                log_security_event(
                    'authentication_failure',
                    f"Failed authentication attempt for {email}",
                    email=email,
                    source_ip=client_ip,
                    user_agent=user_agent,
                    failure_reason='invalid_code',
                    security_context={
                        'attempt_time': time.time(),
                        'session_id': request.session.session_key
                    }
                )
                
                security_logger.warning(
                    f"Authentication failed for {email} from {client_ip}",
                    extra={
                        'event_type': 'auth_failure',
                        'source_ip': client_ip,
                        'user_agent': user_agent,
                        'email': email
                    }
                )
                
                return {'success': False, 'error': 'Invalid code'}
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_performance_event('user_authentication', duration_ms, 
                                success=False, error=str(e))
            
            logger.error(f"Authentication error for {email}: {e}", exc_info=True)
            raise
    
    def handle_rate_limit_exceeded(self, email: str, request) -> None:
        """Handle rate limiting events"""
        client_ip = self.get_client_ip(request)
        
        log_security_event(
            'rate_limit_exceeded',
            f"Rate limit exceeded for authentication attempts: {email}",
            email=email,
            source_ip=client_ip,
            security_context={
                'rate_limit_type': 'auth_attempts',
                'limit_window': '1 hour',
                'max_attempts': 5
            }
        )
        
        security_logger.warning(
            f"Rate limit exceeded for {email} from {client_ip}",
            extra={
                'event_type': 'rate_limit_auth',
                'source_ip': client_ip,
                'email': email
            }
        )
    
    def get_client_ip(self, request) -> str:
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'unknown')
```

## Example 2: Payment Service with Business and Audit Logging

```python
# finances/services/payment_service.py
import logging
import time
from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction
from common.logging_utils import log_business_event, log_performance_event

logger = logging.getLogger('finances.payments')
audit_logger = logging.getLogger('finances.audit')
stripe_logger = logging.getLogger('finances.stripe')

class PaymentService:
    def __init__(self):
        logger.info("PaymentService initialized with Stripe integration")
    
    def create_payment_intent(self, amount: Decimal, student_id: int, 
                            school_id: int, metadata: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        correlation_id = self.generate_correlation_id()
        
        logger.info(f"Creating payment intent for €{amount} - student {student_id}")
        
        # Log business event - payment initiation
        log_business_event(
            'payment_intent_created',
            f"Payment intent created for €{amount}",
            amount=float(amount),
            currency='EUR',
            student_id=student_id,
            school_id=school_id,
            payment_method='stripe',
            metadata=metadata
        )
        
        # Audit log for financial compliance
        audit_logger.info(
            f"Financial transaction initiated: {correlation_id}",
            extra={
                'transaction_type': 'payment_intent_creation',
                'amount': float(amount),
                'currency': 'EUR',
                'student_id': student_id,
                'school_id': school_id,
                'correlation_id': correlation_id,
                'metadata': metadata
            }
        )
        
        try:
            # Create Stripe payment intent
            payment_intent = self.stripe_service.create_payment_intent(
                amount=amount,
                metadata={
                    'student_id': student_id,
                    'school_id': school_id,
                    'correlation_id': correlation_id,
                    **metadata
                }
            )
            
            # Log successful creation
            duration_ms = (time.time() - start_time) * 1000
            log_performance_event('payment_intent_creation', duration_ms, 
                                success=True, amount=float(amount))
            
            logger.info(f"Payment intent created successfully: {payment_intent.id}")
            
            return {
                'payment_intent_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'correlation_id': correlation_id
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_performance_event('payment_intent_creation', duration_ms, 
                                success=False, error=str(e), amount=float(amount))
            
            # Log error with context
            logger.error(
                f"Failed to create payment intent for student {student_id}: {e}",
                extra={
                    'amount': float(amount),
                    'student_id': student_id,
                    'school_id': school_id,
                    'correlation_id': correlation_id,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            
            # Audit log for failed transaction
            audit_logger.error(
                f"Financial transaction failed: {correlation_id}",
                extra={
                    'transaction_type': 'payment_intent_creation_failed',
                    'amount': float(amount),
                    'student_id': student_id,
                    'school_id': school_id,
                    'correlation_id': correlation_id,
                    'error': str(e)
                }
            )
            
            raise
    
    def handle_payment_success(self, payment_intent_id: str, webhook_data: Dict[str, Any]) -> None:
        """Handle successful payment webhook"""
        logger.info(f"Processing successful payment: {payment_intent_id}")
        
        try:
            with transaction.atomic():
                # Update local records
                self.update_payment_records(payment_intent_id, webhook_data)
                
                # Extract metadata
                metadata = webhook_data.get('metadata', {})
                student_id = metadata.get('student_id')
                school_id = metadata.get('school_id')
                amount = webhook_data.get('amount_received', 0) / 100  # Convert from cents
                
                # Log business event
                log_business_event(
                    'payment_completed',
                    f"Payment completed successfully: €{amount}",
                    payment_intent_id=payment_intent_id,
                    amount=amount,
                    currency='EUR',
                    student_id=student_id,
                    school_id=school_id,
                    fees_paid=webhook_data.get('application_fee_amount', 0) / 100,
                    processing_time=self.calculate_processing_time(webhook_data)
                )
                
                # Audit log
                audit_logger.info(
                    f"Financial transaction completed: {payment_intent_id}",
                    extra={
                        'transaction_type': 'payment_completion',
                        'payment_intent_id': payment_intent_id,
                        'amount': amount,
                        'student_id': student_id,
                        'school_id': school_id,
                        'stripe_data': {
                            'charge_id': webhook_data.get('latest_charge'),
                            'receipt_url': webhook_data.get('receipt_url')
                        }
                    }
                )
                
                logger.info(f"Payment processing completed for {payment_intent_id}")
                
        except Exception as e:
            logger.error(
                f"Error processing payment success webhook {payment_intent_id}: {e}",
                extra={
                    'payment_intent_id': payment_intent_id,
                    'webhook_data': webhook_data,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            
            # Log audit trail for failed processing
            audit_logger.error(
                f"Payment success processing failed: {payment_intent_id}",
                extra={
                    'transaction_type': 'payment_success_processing_failed',
                    'payment_intent_id': payment_intent_id,
                    'error': str(e)
                }
            )
            raise
    
    def detect_potential_fraud(self, payment_data: Dict[str, Any]) -> bool:
        """Fraud detection with security logging"""
        fraud_logger = logging.getLogger('finances.fraud')
        
        risk_score = self.calculate_risk_score(payment_data)
        
        if risk_score > 0.7:  # High risk threshold
            fraud_logger.warning(
                f"High-risk payment detected: {payment_data.get('payment_intent_id')}",
                extra={
                    'event_type': 'fraud_alert',
                    'risk_score': risk_score,
                    'payment_intent_id': payment_data.get('payment_intent_id'),
                    'student_id': payment_data.get('student_id'),
                    'amount': payment_data.get('amount'),
                    'risk_factors': self.get_risk_factors(payment_data),
                    'security_context': {
                        'ip_address': payment_data.get('client_ip'),
                        'user_agent': payment_data.get('user_agent'),
                        'payment_method': payment_data.get('payment_method_type')
                    }
                }
            )
            return True
            
        elif risk_score > 0.4:  # Medium risk
            fraud_logger.info(
                f"Medium-risk payment flagged: {payment_data.get('payment_intent_id')}",
                extra={
                    'event_type': 'fraud_review',
                    'risk_score': risk_score,
                    'payment_intent_id': payment_data.get('payment_intent_id'),
                    'requires_manual_review': True
                }
            )
            
        return False
```

## Example 3: Scheduler Service with Conflict Detection

```python
# scheduler/services/booking_service.py
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.db.models import Q
from common.logging_utils import log_business_event, log_performance_event

logger = logging.getLogger('scheduler.bookings')
conflict_logger = logging.getLogger('scheduler.conflicts')

class SessionBookingService:
    def __init__(self):
        logger.info("SessionBookingService initialized")
    
    def book_session(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        logger.info(
            f"Booking session request: {booking_data['subject']} "
            f"for student {booking_data['student_id']} with teacher {booking_data['teacher_id']}"
        )
        
        try:
            # Check for conflicts
            conflicts = self.check_scheduling_conflicts(booking_data)
            if conflicts:
                return self.handle_scheduling_conflicts(booking_data, conflicts)
            
            # Validate availability
            if not self.validate_teacher_availability(booking_data):
                logger.warning(
                    f"Teacher {booking_data['teacher_id']} not available at requested time",
                    extra={
                        'teacher_id': booking_data['teacher_id'],
                        'requested_time': booking_data['scheduled_start'],
                        'duration': booking_data['duration_minutes']
                    }
                )
                return {'success': False, 'error': 'Teacher not available'}
            
            # Create booking
            session = self.create_session_booking(booking_data)
            
            # Log successful booking
            duration_ms = (time.time() - start_time) * 1000
            log_performance_event('session_booking', duration_ms, success=True)
            
            log_business_event(
                'session_booked',
                f"Session successfully booked: {session.id}",
                session_id=session.id,
                teacher_id=booking_data['teacher_id'],
                student_id=booking_data['student_id'],
                school_id=booking_data['school_id'],
                subject=booking_data['subject'],
                duration_minutes=booking_data['duration_minutes'],
                scheduled_start=booking_data['scheduled_start'].isoformat(),
                booking_lead_time_hours=self.calculate_lead_time(booking_data['scheduled_start']),
                booking_source=booking_data.get('source', 'web')
            )
            
            logger.info(f"Session booked successfully: {session.id}")
            return {'success': True, 'session_id': session.id}
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_performance_event('session_booking', duration_ms, success=False, error=str(e))
            
            logger.error(
                f"Failed to book session for student {booking_data['student_id']}: {e}",
                extra={
                    'booking_data': booking_data,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            raise
    
    def check_scheduling_conflicts(self, booking_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for scheduling conflicts and log them"""
        teacher_id = booking_data['teacher_id']
        student_id = booking_data['student_id']
        start_time = booking_data['scheduled_start']
        end_time = start_time + timedelta(minutes=booking_data['duration_minutes'])
        
        conflicts = []
        
        # Check teacher conflicts
        teacher_conflicts = self.get_teacher_conflicts(teacher_id, start_time, end_time)
        if teacher_conflicts:
            conflicts.extend(teacher_conflicts)
            
            conflict_logger.warning(
                f"Teacher scheduling conflict detected: teacher {teacher_id}",
                extra={
                    'conflict_type': 'teacher_double_booking',
                    'teacher_id': teacher_id,
                    'requested_start': start_time.isoformat(),
                    'requested_end': end_time.isoformat(),
                    'conflicting_sessions': [s['id'] for s in teacher_conflicts],
                    'conflict_count': len(teacher_conflicts)
                }
            )
        
        # Check student conflicts  
        student_conflicts = self.get_student_conflicts(student_id, start_time, end_time)
        if student_conflicts:
            conflicts.extend(student_conflicts)
            
            conflict_logger.warning(
                f"Student scheduling conflict detected: student {student_id}",
                extra={
                    'conflict_type': 'student_double_booking',
                    'student_id': student_id,
                    'requested_start': start_time.isoformat(),
                    'requested_end': end_time.isoformat(),
                    'conflicting_sessions': [s['id'] for s in student_conflicts]
                }
            )
        
        return conflicts
    
    def handle_scheduling_conflicts(self, booking_data: Dict[str, Any], 
                                  conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle scheduling conflicts with detailed logging"""
        
        conflict_logger.error(
            f"Cannot book session due to {len(conflicts)} conflicts",
            extra={
                'booking_request': {
                    'teacher_id': booking_data['teacher_id'],
                    'student_id': booking_data['student_id'],
                    'scheduled_start': booking_data['scheduled_start'].isoformat(),
                    'duration': booking_data['duration_minutes']
                },
                'conflicts': conflicts,
                'resolution_suggestions': self.generate_alternative_slots(booking_data)
            }
        )
        
        return {
            'success': False,
            'error': 'Scheduling conflicts detected',
            'conflicts': conflicts,
            'alternative_slots': self.generate_alternative_slots(booking_data)
        }
    
    def cancel_session(self, session_id: int, cancellation_reason: str, 
                      cancelled_by_user_id: int) -> Dict[str, Any]:
        """Cancel session with comprehensive logging"""
        
        logger.info(f"Session cancellation requested: {session_id}")
        
        try:
            session = self.get_session(session_id)
            
            # Log business event
            log_business_event(
                'session_cancelled',
                f"Session cancelled: {session_id}",
                session_id=session_id,
                teacher_id=session.teacher_id,
                student_id=session.student_id,
                school_id=session.school_id,
                cancellation_reason=cancellation_reason,
                cancelled_by_user_id=cancelled_by_user_id,
                cancelled_by_role=self.get_user_role(cancelled_by_user_id, session.school_id),
                advance_notice_hours=self.calculate_advance_notice(session),
                refund_eligible=self.is_refund_eligible(session)
            )
            
            # Update session status
            session.status = 'cancelled'
            session.cancellation_reason = cancellation_reason
            session.cancelled_by_id = cancelled_by_user_id
            session.cancelled_at = datetime.now()
            session.save()
            
            # Handle refunds if applicable
            if self.is_refund_eligible(session):
                self.process_cancellation_refund(session)
            
            logger.info(f"Session cancelled successfully: {session_id}")
            return {'success': True}
            
        except Exception as e:
            logger.error(
                f"Failed to cancel session {session_id}: {e}",
                extra={
                    'session_id': session_id,
                    'cancellation_reason': cancellation_reason,
                    'cancelled_by_user_id': cancelled_by_user_id,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            raise
```

## Example 4: WebSocket Connection Logging

```python
# classroom/consumers.py
import logging
import json
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from common.logging_utils import log_business_event, log_performance_event

logger = logging.getLogger('channels.websocket')
session_logger = logging.getLogger('classroom.sessions')

class ClassroomConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.session_id = None
        self.user_id = None
        self.connection_start_time = None
    
    async def connect(self):
        self.connection_start_time = time.time()
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.user_id = self.scope.get('user', {}).get('id')
        self.room_group_name = f'classroom_{self.session_id}'
        
        logger.info(
            f"WebSocket connection requested for session {self.session_id}",
            extra={
                'session_id': self.session_id,
                'user_id': self.user_id,
                'client_ip': self.get_client_ip(),
                'user_agent': self.get_user_agent()
            }
        )
        
        try:
            # Validate session access
            if not await self.validate_session_access():
                logger.warning(
                    f"Unauthorized WebSocket connection attempt",
                    extra={
                        'session_id': self.session_id,
                        'user_id': self.user_id,
                        'reason': 'insufficient_permissions'
                    }
                )
                await self.close()
                return
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Log successful connection
            connection_time_ms = (time.time() - self.connection_start_time) * 1000
            log_performance_event('websocket_connection', connection_time_ms, success=True)
            
            log_business_event(
                'classroom_connection_established',
                f"User connected to classroom session {self.session_id}",
                session_id=self.session_id,
                user_id=self.user_id,
                connection_type='websocket',
                client_info={
                    'ip_address': self.get_client_ip(),
                    'user_agent': self.get_user_agent()
                }
            )
            
            logger.info(f"WebSocket connection established for session {self.session_id}")
            
        except Exception as e:
            connection_time_ms = (time.time() - self.connection_start_time) * 1000
            log_performance_event('websocket_connection', connection_time_ms, 
                                success=False, error=str(e))
            
            logger.error(
                f"Failed to establish WebSocket connection: {e}",
                extra={
                    'session_id': self.session_id,
                    'user_id': self.user_id,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            await self.close()
    
    async def disconnect(self, close_code):
        connection_duration = time.time() - self.connection_start_time if self.connection_start_time else 0
        
        # Leave room group
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        # Log disconnection
        log_business_event(
            'classroom_connection_closed',
            f"User disconnected from classroom session {self.session_id}",
            session_id=self.session_id,
            user_id=self.user_id,
            connection_duration_seconds=connection_duration,
            close_code=close_code,
            close_reason=self.get_close_reason(close_code)
        )
        
        logger.info(
            f"WebSocket connection closed for session {self.session_id}",
            extra={
                'session_id': self.session_id,
                'user_id': self.user_id,
                'connection_duration': connection_duration,
                'close_code': close_code
            }
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            logger.debug(
                f"WebSocket message received: {message_type}",
                extra={
                    'session_id': self.session_id,
                    'user_id': self.user_id,
                    'message_type': message_type,
                    'message_size': len(text_data)
                }
            )
            
            # Route message based on type
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'screen_share':
                await self.handle_screen_share(data)
            elif message_type == 'session_update':
                await self.handle_session_update(data)
            else:
                logger.warning(
                    f"Unknown WebSocket message type: {message_type}",
                    extra={
                        'session_id': self.session_id,
                        'user_id': self.user_id,
                        'message_type': message_type
                    }
                )
                
        except json.JSONDecodeError as e:
            logger.warning(
                f"Invalid JSON in WebSocket message: {e}",
                extra={
                    'session_id': self.session_id,
                    'user_id': self.user_id,
                    'raw_message': text_data[:100]  # First 100 chars only
                }
            )
        except Exception as e:
            logger.error(
                f"Error processing WebSocket message: {e}",
                extra={
                    'session_id': self.session_id,
                    'user_id': self.user_id,
                    'message_data': data if 'data' in locals() else None,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
    
    async def handle_chat_message(self, data):
        """Handle chat messages with moderation logging"""
        message_content = data.get('message', '')
        
        # Log chat message (without content for privacy)
        session_logger.info(
            f"Chat message sent in session {self.session_id}",
            extra={
                'event_type': 'chat_message',
                'session_id': self.session_id,
                'sender_id': self.user_id,
                'message_length': len(message_content),
                'timestamp': time.time()
            }
        )
        
        # Check for inappropriate content (if moderation is enabled)
        if self.requires_moderation(message_content):
            logger.warning(
                f"Chat message flagged for moderation in session {self.session_id}",
                extra={
                    'session_id': self.session_id,
                    'sender_id': self.user_id,
                    'moderation_flags': self.get_moderation_flags(message_content)
                }
            )
        
        # Broadcast message to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender_id': self.user_id,
                'timestamp': time.time()
            }
        )
    
    def get_client_ip(self):
        """Extract client IP from WebSocket headers"""
        headers = dict(self.scope.get('headers', []))
        x_forwarded_for = headers.get(b'x-forwarded-for')
        if x_forwarded_for:
            return x_forwarded_for.decode().split(',')[0]
        return self.scope.get('client', ['unknown'])[0]
    
    def get_user_agent(self):
        """Extract user agent from WebSocket headers"""
        headers = dict(self.scope.get('headers', []))
        user_agent = headers.get(b'user-agent')
        return user_agent.decode() if user_agent else 'Unknown'
```

## Example 5: Middleware for Request/Response Logging

```python
# common/middleware/request_logging_middleware.py
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from common.logging_utils import CorrelationID, BusinessContext, log_performance_event

logger = logging.getLogger('django.request')
security_logger = logging.getLogger('security.events')

class RequestLoggingMiddleware(MiddlewareMixin):
    """Enhanced request logging with security and performance monitoring"""
    
    def process_request(self, request):
        # Generate correlation ID
        correlation_id = request.headers.get('X-Correlation-ID', CorrelationID.generate())
        CorrelationID.set(correlation_id)
        
        # Store request start time
        request._logging_start_time = time.time()
        request._correlation_id = correlation_id
        
        # Set business context if available
        if hasattr(request, 'user') and request.user.is_authenticated:
            school_id = getattr(request, 'school_id', None)
            if hasattr(request, 'resolver_match') and request.resolver_match:
                school_id = request.resolver_match.kwargs.get('school_id', school_id)
            
            BusinessContext.set_context(
                school_id=school_id,
                user_id=request.user.id,
                role=getattr(request.user, 'current_role', None)
            )
        
        # Log request details (for debug level)
        logger.debug(
            f"Request started: {request.method} {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'query_string': request.META.get('QUERY_STRING', ''),
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'correlation_id': correlation_id,
                'client_ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
            }
        )
        
        return None
    
    def process_response(self, request, response):
        # Calculate request duration
        if hasattr(request, '_logging_start_time'):
            duration_ms = (time.time() - request._logging_start_time) * 1000
            
            # Log performance metrics
            if duration_ms > 1000:  # Log slow requests (>1s)
                log_performance_event(
                    'slow_request',
                    duration_ms,
                    path=request.path,
                    method=request.method,
                    status_code=response.status_code,
                    user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None
                )
                
                logger.warning(
                    f"Slow request detected: {request.method} {request.path} took {duration_ms:.2f}ms",
                    extra={
                        'method': request.method,
                        'path': request.path,
                        'duration_ms': duration_ms,
                        'status_code': response.status_code,
                        'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None
                    }
                )
            
            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.path} [{response.status_code}] in {duration_ms:.2f}ms",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                    'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                    'response_size': len(response.content) if hasattr(response, 'content') else 0
                }
            )
        
        # Add correlation ID to response
        if hasattr(request, '_correlation_id'):
            response['X-Correlation-ID'] = request._correlation_id
        
        # Log security events for certain status codes
        if response.status_code in [401, 403, 429]:
            self.log_security_event(request, response)
        
        return response
    
    def process_exception(self, request, exception):
        """Log unhandled exceptions"""
        duration_ms = (time.time() - request._logging_start_time) * 1000 if hasattr(request, '_logging_start_time') else 0
        
        logger.error(
            f"Unhandled exception in {request.method} {request.path}: {exception}",
            extra={
                'method': request.method,
                'path': request.path,
                'duration_ms': duration_ms,
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'exception_type': type(exception).__name__,
                'client_ip': self.get_client_ip(request)
            },
            exc_info=True
        )
        
        return None
    
    def log_security_event(self, request, response):
        """Log security-related events"""
        event_type_map = {
            401: 'unauthorized_access',
            403: 'permission_denied', 
            429: 'rate_limit_exceeded'
        }
        
        event_type = event_type_map.get(response.status_code, 'security_event')
        
        security_logger.warning(
            f"Security event: {event_type} for {request.path}",
            extra={
                'event_type': event_type,
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'source_ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'security_context': {
                    'referer': request.META.get('HTTP_REFERER'),
                    'query_string': request.META.get('QUERY_STRING')
                }
            }
        )
    
    def get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'unknown')
```

These examples demonstrate how to integrate the new logging system across different components of the Aprende Comigo platform, providing comprehensive observability for business events, security monitoring, and performance optimization.