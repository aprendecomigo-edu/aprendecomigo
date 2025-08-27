"""
Push Notification Service for Education App
Handles push notifications for course updates, lesson reminders, and educational events
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from webpush import send_user_notification
from webpush.models import SubscriptionInfo

from .models import Course, Enrollment, Lesson, Assignment

logger = logging.getLogger('education.push_notifications')
User = get_user_model()


class EducationPushNotificationService:
    """
    Service for sending educational push notifications.
    Handles notifications for course updates, lesson reminders, assignments, and more.
    """
    
    def __init__(self):
        self.default_icon = '/static/images/icon-192x192.png'
        self.default_badge = '/static/images/badge-72x72.png'
    
    def send_course_enrollment_notification(self, enrollment: Enrollment) -> bool:
        """
        Send notification when a student enrolls in a course.
        """
        try:
            payload = {
                'head': f'Welcome to {enrollment.course.title}!',
                'body': f'You have successfully enrolled in {enrollment.course.title}. Get ready to learn!',
                'icon': self.default_icon,
                'badge': self.default_badge,
                'tag': f'enrollment_{enrollment.id}',
                'data': {
                    'type': 'course_enrollment',
                    'course_id': enrollment.course.id,
                    'enrollment_id': enrollment.id,
                    'url': f'/education/student/courses/{enrollment.course.id}/',
                    'timestamp': timezone.now().isoformat(),
                },
                'actions': [
                    {
                        'action': 'view_course',
                        'title': 'View Course',
                        'icon': '/static/images/view-icon.png'
                    },
                    {
                        'action': 'view_schedule',
                        'title': 'View Schedule',
                        'icon': '/static/images/calendar-icon.png'
                    }
                ],
                'requireInteraction': True,
                'vibrate': [200, 100, 200]
            }
            
            # Send to student
            result = send_user_notification(
                user=enrollment.student.user,
                payload=payload,
                ttl=86400  # 24 hours
            )
            
            # Also notify the teacher
            teacher_payload = {
                'head': 'New Student Enrollment',
                'body': f'{enrollment.student.user.get_full_name()} enrolled in {enrollment.course.title}',
                'icon': self.default_icon,
                'badge': self.default_badge,
                'tag': f'teacher_enrollment_{enrollment.id}',
                'data': {
                    'type': 'teacher_enrollment_notification',
                    'course_id': enrollment.course.id,
                    'enrollment_id': enrollment.id,
                    'student_id': enrollment.student.id,
                    'url': f'/education/teacher/courses/{enrollment.course.id}/',
                    'timestamp': timezone.now().isoformat(),
                },
                'actions': [
                    {
                        'action': 'view_student',
                        'title': 'View Student',
                        'icon': '/static/images/student-icon.png'
                    }
                ]
            }
            
            send_user_notification(
                user=enrollment.course.teacher.user,
                payload=teacher_payload,
                ttl=86400
            )
            
            logger.info(f'Sent enrollment notification for enrollment {enrollment.id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send enrollment notification: {e}')
            return False
    
    def send_lesson_reminder(self, lesson: Lesson, minutes_before: int = 30) -> bool:
        """
        Send lesson reminder notifications to students and teacher.
        """
        try:
            # Get enrolled students
            enrollments = Enrollment.objects.filter(
                course=lesson.course,
                status='active',
                is_active=True
            ).select_related('student__user')
            
            reminder_time = lesson.scheduled_date - timedelta(minutes=minutes_before)
            now = timezone.now()
            
            # Only send if reminder time is in the future
            if reminder_time <= now:
                return False
            
            # Prepare notification payload
            lesson_time = lesson.scheduled_date.strftime('%H:%M')
            lesson_date = lesson.scheduled_date.strftime('%A, %B %d')
            
            payload = {
                'head': f'Lesson Reminder: {lesson.title}',
                'body': f'Your lesson "{lesson.title}" starts in {minutes_before} minutes at {lesson_time}',
                'icon': self.default_icon,
                'badge': self.default_badge,
                'tag': f'lesson_reminder_{lesson.id}',
                'data': {
                    'type': 'lesson_reminder',
                    'lesson_id': lesson.id,
                    'course_id': lesson.course.id,
                    'scheduled_date': lesson.scheduled_date.isoformat(),
                    'url': f'/education/lessons/{lesson.id}/',
                    'timestamp': timezone.now().isoformat(),
                },
                'actions': [
                    {
                        'action': 'join_lesson',
                        'title': 'Join Lesson',
                        'icon': '/static/images/join-icon.png'
                    },
                    {
                        'action': 'view_materials',
                        'title': 'View Materials',
                        'icon': '/static/images/materials-icon.png'
                    }
                ],
                'requireInteraction': True,
                'vibrate': [300, 100, 300, 100, 300]
            }
            
            # Send to all enrolled students
            success_count = 0
            for enrollment in enrollments:
                try:
                    send_user_notification(
                        user=enrollment.student.user,
                        payload=payload,
                        ttl=3600  # 1 hour
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f'Failed to send lesson reminder to student {enrollment.student.id}: {e}')
            
            # Send to teacher
            teacher_payload = {
                'head': f'Teaching Reminder: {lesson.title}',
                'body': f'Your lesson "{lesson.title}" starts in {minutes_before} minutes',
                'icon': self.default_icon,
                'badge': self.default_badge,
                'tag': f'teacher_lesson_reminder_{lesson.id}',
                'data': {
                    'type': 'teacher_lesson_reminder',
                    'lesson_id': lesson.id,
                    'course_id': lesson.course.id,
                    'url': f'/education/teacher/lessons/{lesson.id}/',
                    'timestamp': timezone.now().isoformat(),
                },
                'actions': [
                    {
                        'action': 'start_lesson',
                        'title': 'Start Lesson',
                        'icon': '/static/images/start-icon.png'
                    }
                ]
            }
            
            try:
                send_user_notification(
                    user=lesson.course.teacher.user,
                    payload=teacher_payload,
                    ttl=3600
                )
                success_count += 1
            except Exception as e:
                logger.error(f'Failed to send lesson reminder to teacher {lesson.course.teacher.id}: {e}')
            
            logger.info(f'Sent lesson reminder for lesson {lesson.id} to {success_count} users')
            return success_count > 0
            
        except Exception as e:
            logger.error(f'Failed to send lesson reminder: {e}')
            return False
    
    def send_assignment_notification(self, assignment: Assignment, notification_type: str = 'new') -> bool:
        """
        Send assignment-related notifications.
        Types: 'new', 'due_soon', 'overdue', 'graded'
        """
        try:
            # Get enrolled students
            enrollments = Enrollment.objects.filter(
                course=assignment.course,
                status='active',
                is_active=True
            ).select_related('student__user')
            
            # Prepare notification based on type
            if notification_type == 'new':
                head = f'New Assignment: {assignment.title}'
                body = f'A new assignment has been posted for {assignment.course.title}'
                action_text = 'View Assignment'
                tag = f'assignment_new_{assignment.id}'
                
            elif notification_type == 'due_soon':
                days_until_due = (assignment.due_date.date() - timezone.now().date()).days
                head = f'Assignment Due Soon: {assignment.title}'
                body = f'Assignment "{assignment.title}" is due in {days_until_due} days'
                action_text = 'Complete Assignment'
                tag = f'assignment_due_{assignment.id}'
                
            elif notification_type == 'overdue':
                head = f'Overdue Assignment: {assignment.title}'
                body = f'Assignment "{assignment.title}" is now overdue'
                action_text = 'Submit Late'
                tag = f'assignment_overdue_{assignment.id}'
                
            elif notification_type == 'graded':
                head = f'Assignment Graded: {assignment.title}'
                body = f'Your assignment "{assignment.title}" has been graded'
                action_text = 'View Grade'
                tag = f'assignment_graded_{assignment.id}'
            
            else:
                logger.error(f'Unknown assignment notification type: {notification_type}')
                return False
            
            payload = {
                'head': head,
                'body': body,
                'icon': self.default_icon,
                'badge': self.default_badge,
                'tag': tag,
                'data': {
                    'type': f'assignment_{notification_type}',
                    'assignment_id': assignment.id,
                    'course_id': assignment.course.id,
                    'due_date': assignment.due_date.isoformat(),
                    'url': f'/education/assignments/{assignment.id}/',
                    'timestamp': timezone.now().isoformat(),
                },
                'actions': [
                    {
                        'action': 'view_assignment',
                        'title': action_text,
                        'icon': '/static/images/assignment-icon.png'
                    }
                ],
                'vibrate': [200, 100, 200]
            }
            
            # Send to all enrolled students
            success_count = 0
            for enrollment in enrollments:
                try:
                    send_user_notification(
                        user=enrollment.student.user,
                        payload=payload,
                        ttl=86400  # 24 hours
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f'Failed to send assignment notification to student {enrollment.student.id}: {e}')
            
            logger.info(f'Sent {notification_type} assignment notification for assignment {assignment.id} to {success_count} students')
            return success_count > 0
            
        except Exception as e:
            logger.error(f'Failed to send assignment notification: {e}')
            return False
    
    def send_course_update_notification(self, course: Course, update_message: str) -> bool:
        """
        Send course update notifications to all enrolled students.
        """
        try:
            enrollments = Enrollment.objects.filter(
                course=course,
                status='active',
                is_active=True
            ).select_related('student__user')
            
            payload = {
                'head': f'Course Update: {course.title}',
                'body': update_message,
                'icon': self.default_icon,
                'badge': self.default_badge,
                'tag': f'course_update_{course.id}_{timezone.now().timestamp()}',
                'data': {
                    'type': 'course_update',
                    'course_id': course.id,
                    'url': f'/education/courses/{course.id}/',
                    'timestamp': timezone.now().isoformat(),
                },
                'actions': [
                    {
                        'action': 'view_course',
                        'title': 'View Course',
                        'icon': '/static/images/view-icon.png'
                    }
                ]
            }
            
            success_count = 0
            for enrollment in enrollments:
                try:
                    send_user_notification(
                        user=enrollment.student.user,
                        payload=payload,
                        ttl=86400
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f'Failed to send course update to student {enrollment.student.id}: {e}')
            
            logger.info(f'Sent course update notification for course {course.id} to {success_count} students')
            return success_count > 0
            
        except Exception as e:
            logger.error(f'Failed to send course update notification: {e}')
            return False
    
    def send_payment_notification(self, user: User, payment_type: str, amount: str, success: bool = True) -> bool:
        """
        Send payment-related notifications.
        """
        try:
            if success:
                head = 'Payment Successful'
                body = f'Your {payment_type} payment of €{amount} has been processed successfully'
                icon = '/static/images/success-icon.png'
                tag = f'payment_success_{timezone.now().timestamp()}'
            else:
                head = 'Payment Failed'
                body = f'Your {payment_type} payment of €{amount} could not be processed'
                icon = '/static/images/error-icon.png'
                tag = f'payment_failed_{timezone.now().timestamp()}'
            
            payload = {
                'head': head,
                'body': body,
                'icon': icon,
                'badge': self.default_badge,
                'tag': tag,
                'data': {
                    'type': 'payment_notification',
                    'payment_type': payment_type,
                    'amount': amount,
                    'success': success,
                    'url': '/education/payments/history/',
                    'timestamp': timezone.now().isoformat(),
                },
                'actions': [
                    {
                        'action': 'view_payments',
                        'title': 'View Payments',
                        'icon': '/static/images/payment-icon.png'
                    }
                ],
                'requireInteraction': not success,  # Require interaction for failed payments
                'vibrate': [200, 100, 200] if success else [500, 200, 500, 200, 500]
            }
            
            send_user_notification(
                user=user,
                payload=payload,
                ttl=86400
            )
            
            logger.info(f'Sent payment notification to user {user.id}: {payment_type} - Success: {success}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send payment notification: {e}')
            return False
    
    def schedule_lesson_reminders(self, lesson: Lesson) -> bool:
        """
        Schedule multiple reminders for a lesson (24h, 1h, 30min before).
        This would typically be called by a background task scheduler.
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            lesson_time = lesson.scheduled_date
            
            # Schedule reminders at different intervals
            reminder_intervals = [
                (24 * 60, '24 hours'),  # 24 hours before
                (60, '1 hour'),         # 1 hour before
                (30, '30 minutes'),     # 30 minutes before
                (10, '10 minutes'),     # 10 minutes before
            ]
            
            for minutes_before, description in reminder_intervals:
                reminder_time = lesson_time - timedelta(minutes=minutes_before)
                
                # Only schedule if reminder time is in the future
                if reminder_time > now:
                    # In a real application, you would use Celery or similar
                    # to schedule these notifications
                    logger.info(f'Would schedule {description} reminder for lesson {lesson.id} at {reminder_time}')
            
            return True
            
        except Exception as e:
            logger.error(f'Failed to schedule lesson reminders: {e}')
            return False
    
    def get_user_subscription_status(self, user: User) -> Dict[str, Any]:
        """
        Get push notification subscription status for a user.
        """
        try:
            subscriptions = SubscriptionInfo.objects.filter(user=user)
            
            return {
                'has_subscriptions': subscriptions.exists(),
                'subscription_count': subscriptions.count(),
                'subscriptions': [
                    {
                        'id': sub.id,
                        'browser': sub.browser,
                        'endpoint': sub.endpoint[:50] + '...' if len(sub.endpoint) > 50 else sub.endpoint,
                        'created_at': sub.auth.isoformat() if hasattr(sub, 'auth') else None
                    }
                    for sub in subscriptions
                ]
            }
            
        except Exception as e:
            logger.error(f'Failed to get subscription status for user {user.id}: {e}')
            return {
                'has_subscriptions': False,
                'subscription_count': 0,
                'subscriptions': [],
                'error': str(e)
            }


# Singleton instance
push_service = EducationPushNotificationService()